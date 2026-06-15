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
from typing import Any, Dict

from . import (
    ClientProfile, Recommender,
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
    tc = rec.trainee_category
    out.append(f"Trainee Category: {tc.category.value} ({tc.strategy})")
    out.append(f"  -> {tc.summary}")
    e = rec.energy
    out.append(f"Energy: BMR {e.bmr} | TDEE {e.tdee} | "
               f"Target {e.calorie_target} kcal")
    m = rec.nutrition.macros
    out.append(f"Macros: {m.protein_g}P / {m.carbs_g}C / {m.fat_g}F "
               f"({m.calories} kcal)")
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
    def default(o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        if hasattr(o, "value"):
            return o.value
        return str(o)
    return json.dumps(dataclasses.asdict(rec), default=default, indent=2)


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

    from . import Sex
    DEFAULTS = {
        "The Classic Hard Gainer":  (22, Sex.MALE,   180, 64, 11),
        "The Muscled Cutter":       (35, Sex.MALE,   178, 92, 25),
        "The Skinny-Fat Recomper":  (30, Sex.MALE,   175, 78, 22),
        "The Home-Gym Beginner":    (45, Sex.FEMALE, 165, 68, 28),
        "The Plant-Powered Builder":(27, Sex.MALE,   178, 74, 12),
    }
    for ap in all_curated():
        sig = ap.signature
        age, sex, ht, wt, bf = DEFAULTS[ap.nickname]
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
    }
    with open(args.output, "w") as fh:
        json.dump(template, fh, indent=2)
    print(f"Scaffolded {args.output}")
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

    sp = sub.add_parser("meals", help="List meal library")
    sp.set_defaults(func=cmd_meal_library)

    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
