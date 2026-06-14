"""
cli.py
======

Command-line interface for the Fitness Engine.

Usage:
    python -m fitness_engine.cli profile <input.json> [--out plan.html] [--format html|json|text]
    python -m fitness_engine.cli showcase                       # run all curated archetypes
    python -m fitness_engine.cli archetypes                     # list all curated archetypes
    python -m fitness_engine.cli new <output.json>             # scaffold an empty profile JSON
    python -m fitness_engine.cli --help
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import os
import sys
from typing import Any, Dict

from . import (
    ClientProfile, Recommender,
    all_curated, get_curated, __version__,
)
from .meal_plans import MealItem, MEAL_LIBRARY


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
               f"BF {bc.body_fat_pct}%, lean {bc.lean_mass_kg} kg")
    e = rec.energy
    out.append(f"Energy: BMR {e.bmr_mifflin} | TDEE {e.tdee} | "
               f"Target {e.calorie_target} kcal")
    m = rec.nutrition.macros
    out.append(f"Macros: {m.protein_g}P / {m.carbs_g}C / {m.fat_g}F "
               f"({m.calories} kcal)")
    t = rec.training
    out.append(f"Training: {t.weekly_volume.total_sets} sets/wk, "
               f"{t.periodisation.scheme}")
    out.append(f"Cardio: {t.cardio_prescription.get('weekly_cardio_minutes')} min/wk")
    out.append("")
    for day, exs in t.weekly_schedule.items():
        out.append(f"{day}:")
        for e_ in exs:
            out.append(f"  - {e_['name']} ({e_['sets_reps']} RPE {e_['rpe']})")
    out.append("")
    out.append("Meal plan:")
    for m_ in rec.nutrition.meal_plan.meals:
        out.append(f"  {m_.slot}: {m_.name} ({m_.calories:.0f} kcal)")
    if rec.warnings:
        out.append("\nWarnings:")
        for w in rec.warnings:
            out.append(f"  ! {w}")
    if rec.notes:
        out.append("\nNotes:")
        for n in rec.notes:
            out.append(f"  i {n}")
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
        # Import lazily so non-HTML paths don't pull in the renderer
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
    fmt = "{:32s} {:32s} {:>6s} {:>5s} {:>5s} {:>5s} {:>5s} {:24s}"
    print(fmt.format("Archetype", "Signature", "kcal", "P", "C", "F",
                     "sets", "periodisation"))
    print("-" * 110)
    from . import (
        ActivityLevel, Sex,
        all_curated,
    )
    DEFAULTS = {
        "The Desk-Bound Reset":         (34, Sex.FEMALE, 168, 72, 32),
        "The Classic Hard Gainer":      (22, Sex.MALE,   180, 64, 11),
        "The Reclaiming Parent":        (33, Sex.FEMALE, 165, 68, 27),
        "The Vital Retiree":            (64, Sex.MALE,   175, 80, 22),
        "The Metabolic Rebuild":        (52, Sex.MALE,   178, 102, 32),
        "The Endurance Specialist":     (26, Sex.FEMALE, 170, 58, 16),
        "The Plant-Powered Performer":  (27, Sex.MALE,   178, 74, 12),
        "The Keto Cruiser":             (38, Sex.MALE,   178, 82, 18),
        "The Shift-Worker":             (42, Sex.MALE,   174, 84, 24),
        "The Back-Pain Returner":       (39, Sex.FEMALE, 167, 72, 30),
        "The Youth Athlete":            (16, Sex.MALE,   175, 68, 12),
        "The PCOS Balancer":            (29, Sex.FEMALE, 165, 80, 36),
    }
    for ap in all_curated():
        sig = ap.signature
        age, sex, ht, wt, bf = DEFAULTS[ap.nickname]
        p = ClientProfile(
            age=age, sex=sex, height_cm=ht, weight_kg=wt, body_fat_pct=bf,
            waist_cm=bf+50, neck_cm=35,
            activity=sig.activity, sleep_hours=7.0, stress_level=4,
            health_conditions=[], dietary_preference=sig.diet,
            allergies=[], meals_per_day=4,
            experience=sig.experience, environment=sig.environment,
            equipment=["barbell","bench","dumbbells","machine",
                       "cardio_machine","kettlebells","pullup_bar"],
            days_per_week=4, session_length=sig.session,
            primary_goal=sig.goal, timeline_weeks=12,
            parq_answers={f"parq_{i}":"no" for i in range(1,8)},
        )
        rec = Recommender(p).recommend()
        m = rec.nutrition.macros
        v = rec.training.weekly_volume.total_sets
        per = rec.training.periodisation.scheme[:24]
        print(fmt.format(ap.nickname[:32], rec.archetype_signature,
                         f"{rec.energy.calorie_target:.0f}",
                         f"{m.protein_g:.0f}", f"{m.carbs_g:.0f}",
                         f"{m.fat_g:.0f}", str(v), per))
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
        "sex": "female",
        "height_cm": 165,
        "weight_kg": 65,
        "body_fat_pct": None,
        "waist_cm": None,
        "neck_cm": None,
        "resting_hr": 60,
        "activity": "moderate",
        "sleep_hours": 7.5,
        "stress_level": 5,
        "health_conditions": [],
        "medications": "",
        "injuries": "",
        "parq_answers": {f"parq_{i}": "no" for i in range(1, 8)},
        "dietary_preference": "omnivore",
        "allergies": [],
        "dislikes": [],
        "meals_per_day": 3,
        "cooking_skill": "intermediate",
        "preferred_cuisines": [],
        "experience": "beginner",
        "environment": "gym_commercial",
        "equipment": [],
        "days_per_week": 4,
        "session_length": "standard_60",
        "primary_goal": "general_health",
        "secondary_goals": [],
        "target_weight_kg": None,
        "timeline_weeks": 12,
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
