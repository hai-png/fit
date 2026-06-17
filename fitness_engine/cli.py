"""
cli.py
======

Command-line interface for the Fitness Engine.

Usage:
    python -m fitness_engine.cli profile <input.json> [--out plan.html] [--format html|json|text]
    python -m fitness_engine.cli showcase        # run all curated archetypes
    python -m fitness_engine.cli archetypes      # list all curated archetypes
    python -m fitness_engine.cli new <output.json>  # scaffold an empty profile
    python -m fitness_engine.cli --help
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import sys

from . import (
    ClientProfile, Recommender,
    DailyLog, adaptive_tdee, reverse_diet_protocol,
    init_db, store_client, add_weight, add_adherence, client_summary,
    all_curated, __version__,
)
from .meal_plans import MEAL_LIBRARY


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #
def _print_section(title: str) -> None:
    bar = "=" * 70
    print(f"\n{bar}\n{title}\n{bar}")


def _format_plan_text(rec) -> str:
    out = []
    out.append(f"Personalised Plan  -  signature {rec.archetype_signature}")
    out.append("")
    bc = rec.body_composition
    out.append(f"Body Composition: BMI {bc.bmi} ({bc.bmi_category}), "
               f"BF {bc.body_fat_pct}% [{bc.estimation_method}]")
    ai = rec.anthropometrics
    if ai.waist_to_height_ratio is not None:
        out.append(f"Anthropometrics: WHtR {ai.waist_to_height_ratio} "
                   f"({ai.waist_to_height_category}), "
                   f"WHR {ai.waist_to_hip_ratio}, ABSI {ai.absi}")
    tc = rec.trainee_category
    out.append(f"Trainee Category: {tc.category.value} ({tc.strategy})")
    out.append(f"  -> {tc.summary}")
    e = rec.energy
    out.append(f"Energy: BMR {e.bmr} | TDEE {e.tdee} | "
               f"Target {e.calorie_target} kcal")
    m = rec.nutrition.macros
    out.append(f"Macros: {m.protein_g}P / {m.carbs_g}C / {m.fat_g}F "
               f"({m.calories} kcal)")
    mc = rec.nutrition.macro_cycle
    out.append(f"Macro cycle option: training day {mc.training_day.calories:.0f} kcal, "
               f"rest day {mc.rest_day.calories:.0f} kcal "
               f"(weekly avg {mc.weekly_average_calories:.0f})")
    t = rec.training
    out.append(f"Training: {t.weekly_volume.total_sets} sets/wk, "
               f"{t.split.name}, {t.periodisation.scheme}")
    out.append(f"Cardio: {t.cardio_prescription.get('weekly_cardio_minutes')} min/wk")
    out.append("")
    for day, exs in t.weekly_schedule.items():
        out.append(f"{day}:")
        for e_ in exs:
            out.append(f"  - {e_['name']} ({e_['sets_reps']} RIR {e_['rir']})")
    out.append("")
    out.append("Meal plan:")
    for m_ in rec.nutrition.meal_plan.meals:
        out.append(f"  {m_.slot}: {m_.name} ({m_.calories:.0f} kcal)")
    if rec.trainee_category.recommendations:
        out.append("\nRecommendations:")
        for r in rec.trainee_category.recommendations:
            out.append(f"  i {r}")
    if rec.warnings:
        out.append("\nWarnings:")
        for w in rec.warnings:
            out.append(f"  ! {w}")
    return "\n".join(out)


def _format_plan_json(rec) -> str:
    """Serialize a PlanRecommendation to a JSON string.

    Uses the unified ``_to_json_safe`` helper from recommender.py so that
    enums (top-level and nested) are converted to their string values
    uniformly — the same path used by ``ClientProfile.to_dict``. See audit
    finding F76.
    """
    from .recommender import _to_json_safe
    return json.dumps(_to_json_safe(rec), indent=2)


def _json_default(o):
    """Fallback JSON default for objects ``_to_json_safe`` does not handle
    (e.g., datetime, set). Used by ``cmd_review`` and ``cmd_store_client``.
    """
    import dataclasses as _dc
    from datetime import datetime as _dt
    if _dc.is_dataclass(o):
        return _dc.asdict(o)
    if hasattr(o, "value"):
        return o.value
    if isinstance(o, _dt):
        return o.isoformat()
    if isinstance(o, set):
        return sorted(o)
    return str(o)


# --------------------------------------------------------------------------- #
# Sub-commands                                                                #
# --------------------------------------------------------------------------- #
def cmd_profile(args) -> int:
    with open(args.input) as fh:
        data = json.load(fh)
    profile = ClientProfile.from_dict(data)
    rec = Recommender(profile).recommend()

    if args.format == "json":
        out = _format_plan_json(rec)
    elif args.format == "html":
        from examples.render_html import render
        out = render(rec, data.get("name", "Client"))
    else:
        out = _format_plan_text(rec)

    if args.out:
        with open(args.out, "w") as fh:
            fh.write(out)
        print(f"Wrote {args.out}", file=sys.stderr)
    else:
        print(out)
    return 0


def cmd_showcase(args) -> int:
    print(f"Fitness Engine v{__version__} - archetype showcase")
    print()
    fmt = "{:28s} {:>6s} {:>5s} {:>5s} {:>5s} {:>5s} {:18s} {:14s}"
    print(fmt.format("Archetype", "kcal", "P", "C", "F", "sets",
                     "strategy", "split"))
    print("-" * 95)

    # Showcase defaults are now co-located with each ArchetypeProfile
    # (ap.showcase_defaults) so the dict no longer needs to be maintained
    # separately. See audit finding F75.
    for ap in all_curated():
        sig = ap.signature
        if ap.showcase_defaults is None:
            # Skip archetypes without showcase defaults rather than crashing.
            continue
        age, sex, ht, wt, bf = ap.showcase_defaults
        p = ClientProfile(
            age=age, sex=sex, height_cm=ht, weight_kg=wt, body_fat_pct=bf,
            activity=sig.activity,
            dietary_preference=sig.diet,
            experience=sig.experience, environment=sig.environment,
            days_per_week=4, session_length=sig.session,
            primary_goal=sig.goal, timeline_weeks=12,
            meals_per_day=4,
        )
        rec = Recommender(p).recommend()
        m = rec.nutrition.macros
        v = rec.training.weekly_volume.total_sets
        strat = rec.trainee_category.strategy
        split = rec.training.split.name[:18]
        print(fmt.format(ap.nickname[:28],
                         f"{rec.energy.calorie_target:.0f}",
                         f"{m.protein_g:.0f}", f"{m.carbs_g:.0f}",
                         f"{m.fat_g:.0f}", str(v), strat, split))
    return 0


def cmd_archetypes(args) -> int:
    print(f"Fitness Engine v{__version__} - curated archetypes\n")
    for ap in all_curated():
        print(f"  {ap.nickname}")
        print(f"    signature: {ap.signature.code()}")
        print(f"    summary  : {ap.summary}")
        print(f"    strengths: {', '.join(ap.strengths)}")
        print(f"    risks    : {', '.join(ap.risks)}")
        print(f"    emphasis : {', '.join(ap.emphasis)}")
        print()
    return 0


def cmd_new(args) -> int:
    """Scaffold an empty profile JSON pre-filled with sensible defaults."""
    template = {
        "name": "New Client",
        "age": 30,
        "sex": "male",
        "height_cm": 178,
        "weight_kg": 80,
        "body_fat_pct": None,
        "waist_cm": None,
        "neck_cm": None,
        "hip_cm": None,
        "visual_bf_label": None,
        "wrist_cm": None,
        "resting_hr": 60,
        "measured_max_hr": None,
        "activity": "mostly_sedentary",
        "dietary_preference": "omnivore",
        "allergies": [],
        "dislikes": [],
        "meals_per_day": 4,
        "preferred_cuisines": [],
        "experience": "beginner",
        "environment": "gym_full",
        "days_per_week": 3,
        "session_length": "standard_60",
        "primary_goal": "general_health",
        "target_weight_kg": None,
        "timeline_weeks": 12,
        "motivation": "appearance",
        "medical_flags": {
            "pregnant_or_recent_postpartum": False,
            "recent_surgery": False,
            "diagnosed_eating_disorder": False,
            "cardiac_condition": False,
            "unexplained_chest_pain_or_fainting": False,
        },
        "working_weights_kg": {
            "squat": None,
            "bench_press": None,
            "deadlift": None,
            "overhead_press": None,
            "row": None,
            "pullup": None,
        },
        "plan_week": 1,
        "meal_plan_seed": None,
    }
    with open(args.output, "w") as fh:
        json.dump(template, fh, indent=2)
    print(f"Scaffolded {args.output}")
    return 0


def _client_id_from_name(name: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "-" for ch in name).strip("-") or "client"


def cmd_review(args) -> int:
    """Review weight/intake logs and optional reverse-diet targets."""
    with open(args.input) as fh:
        data = json.load(fh)
    logs = [DailyLog(**row) for row in data.get("logs", [])]
    result = {"adaptive_tdee": None, "reverse_diet": None}
    if "formula_tdee" in data:
        result["adaptive_tdee"] = dataclasses.asdict(
            adaptive_tdee(logs, float(data["formula_tdee"]), data.get("smoothing_days", 7))
        )
    reverse = data.get("reverse_diet")
    if reverse:
        # Resolve estimated_maintenance with explicit guards to avoid
        # subscripting None. See audit finding F74.
        est_maintenance = reverse.get("estimated_maintenance")
        if est_maintenance is None:
            # Fall back to adaptive_tdee's observed value if available.
            adaptive = result.get("adaptive_tdee") or {}
            est_maintenance = adaptive.get("adaptive_tdee")
        if est_maintenance is None:
            # Fall back to formula_tdee if provided.
            est_maintenance = data.get("formula_tdee")
        if est_maintenance is None:
            # Last resort: use current_calories (no surplus) so we don't crash.
            est_maintenance = float(reverse["current_calories"])
        result["reverse_diet"] = dataclasses.asdict(reverse_diet_protocol(
            current_calories=float(reverse["current_calories"]),
            estimated_maintenance=float(est_maintenance),
            bodyweight_kg=float(reverse["bodyweight_kg"]),
            approach=reverse.get("approach", "moderate"),
            build_muscle=bool(reverse.get("build_muscle", False)),
        ))
    out = json.dumps(result, indent=2)
    if args.out:
        with open(args.out, "w") as fh:
            fh.write(out)
        print(f"Wrote {args.out}", file=sys.stderr)
    else:
        print(out)
    return 0


def cmd_db_init(args) -> int:
    init_db(args.db)
    print(f"Initialised {args.db}")
    return 0


def cmd_store_client(args) -> int:
    with open(args.profile) as fh:
        data = json.load(fh)
    profile = ClientProfile.from_dict(data)
    rec = Recommender(profile).recommend() if args.with_plan else None
    name = data.get("name", "Client")
    client_id = args.client_id or _client_id_from_name(name)
    # Use _to_json_safe for the plan snapshot so nested enums are converted
    # uniformly. See audit finding F76.
    from .recommender import _to_json_safe
    plan_snapshot = _to_json_safe(rec) if rec else None
    store_client(client_id, name, profile.to_dict(), plan_snapshot, args.db)
    print(f"Stored client {client_id} in {args.db}")
    return 0


def cmd_update_weight(args) -> int:
    add_weight(args.client_id, args.weight_kg, args.day, args.db)
    print(f"Added weight for {args.client_id}: {args.weight_kg:g} kg")
    return 0


def cmd_log_adherence(args) -> int:
    add_adherence(args.client_id, args.nutrition_pct, args.training_pct, args.day, args.notes or "", args.db)
    print(f"Added adherence log for {args.client_id}")
    return 0


def cmd_client_summary(args) -> int:
    print(json.dumps(client_summary(args.client_id, args.db), indent=2))
    return 0


def cmd_meal_library(args) -> int:
    print(f"Meal library: {len(MEAL_LIBRARY)} items across "
          f"{len(set(m.cuisine for m in MEAL_LIBRARY))} cuisines")
    by_cuisine = {}
    for m in MEAL_LIBRARY:
        by_cuisine.setdefault(m.cuisine, []).append(m)
    for cuisine, meals in sorted(by_cuisine.items()):
        print(f"\n  {cuisine.title()} ({len(meals)} meals)")
        for m in meals:
            print(f"    [{m.slot:10s}] {m.name} - "
                  f"{m.calories:.0f} kcal, P{m.protein_g:.0f} "
                  f"C{m.carbs_g:.0f} F{m.fat_g:.0f}")
    return 0


# --------------------------------------------------------------------------- #
# Parser                                                                      #
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="fitness_engine",
        description="Personalised exercise and meal plan generator.",
    )
    p.add_argument("--version", action="version",
                   version=f"fitness_engine {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("profile", help="Generate a plan from a client JSON")
    sp.add_argument("input", help="path to client JSON profile")
    sp.add_argument("--out", help="write output to file instead of stdout")
    sp.add_argument("--format", choices=["text", "json", "html"],
                     default="text")
    sp.set_defaults(func=cmd_profile)

    sp = sub.add_parser("showcase", help="Run all curated archetypes")
    sp.set_defaults(func=cmd_showcase)

    sp = sub.add_parser("archetypes", help="List curated archetypes")
    sp.set_defaults(func=cmd_archetypes)

    sp = sub.add_parser("new", help="Scaffold a new client JSON profile")
    sp.add_argument("output", help="output JSON path")
    sp.set_defaults(func=cmd_new)

    sp = sub.add_parser("review", help="Review intake/weight logs for adaptive TDEE and reverse dieting")
    sp.add_argument("input", help="review JSON with formula_tdee/logs and optional reverse_diet block")
    sp.add_argument("--out", help="write JSON output to file instead of stdout")
    sp.set_defaults(func=cmd_review)

    sp = sub.add_parser("db-init", help="Initialise a local SQLite coaching database")
    sp.add_argument("--db", default="clients.db", help="SQLite database path")
    sp.set_defaults(func=cmd_db_init)

    sp = sub.add_parser("store-client", help="Store a profile and optional generated plan snapshot")
    sp.add_argument("profile", help="profile JSON to store")
    sp.add_argument("--client-id", help="stable client identifier; defaults to slugified name")
    sp.add_argument("--with-plan", action="store_true", help="also generate and store a plan snapshot")
    sp.add_argument("--db", default="clients.db", help="SQLite database path")
    sp.set_defaults(func=cmd_store_client)

    sp = sub.add_parser("update-weight", help="Append a client weight log")
    sp.add_argument("client_id")
    sp.add_argument("weight_kg", type=float)
    sp.add_argument("--day", type=int)
    sp.add_argument("--db", default="clients.db", help="SQLite database path")
    sp.set_defaults(func=cmd_update_weight)

    sp = sub.add_parser("log-adherence", help="Append nutrition/training adherence percentages")
    sp.add_argument("client_id")
    sp.add_argument("--nutrition-pct", type=float)
    sp.add_argument("--training-pct", type=float)
    sp.add_argument("--day", type=int)
    sp.add_argument("--notes")
    sp.add_argument("--db", default="clients.db", help="SQLite database path")
    sp.set_defaults(func=cmd_log_adherence)

    sp = sub.add_parser("client-summary", help="Print stored client logs and plan snapshots")
    sp.add_argument("client_id")
    sp.add_argument("--db", default="clients.db", help="SQLite database path")
    sp.set_defaults(func=cmd_client_summary)

    sp = sub.add_parser("meals", help="List meal library")
    sp.set_defaults(func=cmd_meal_library)

    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
