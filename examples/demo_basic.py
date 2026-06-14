"""
demo_basic.py
=============

Demonstrates the most common workflow:

    1. Build a ClientProfile
    2. Run it through the Recommender
    3. Pretty-print every section of the plan

Run:
    python3 examples/demo_basic.py
"""
from __future__ import annotations

import json
import os
import sys

# Make the package importable when running from the repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fitness_engine import (
    ActivityLevel, ClientProfile, DietaryPreference, ExperienceLevel,
    GoalArchetype, Recommender, SessionLength, Sex, TrainingEnvironment,
)


def banner(s: str) -> None:
    print()
    print("=" * 78)
    print(s)
    print("=" * 78)


def pretty_plan(profile_path: str) -> None:
    with open(profile_path) as fh:
        data = json.load(fh)
    profile = ClientProfile.from_dict(data)

    banner(f"CLIENT  : {data.get('name', 'Unnamed')}")
    print(f"Profile  : {profile.age}y {profile.sex.value}, "
          f"{profile.height_cm}cm, {profile.weight_kg}kg, "
          f"{profile.body_fat_pct}% BF")
    print(f"Goal     : {profile.primary_goal.value}")
    print(f"Env      : {profile.environment.value}, "
          f"{profile.days_per_week}d/wk, {profile.session_length.value}")

    rec = Recommender(profile).recommend()

    banner("ARCHETYPE SIGNATURE")
    print(rec.archetype_signature)
    print(json.dumps(rec.archetype_summary, indent=2))

    banner("BODY COMPOSITION")
    bc = rec.body_composition
    print(f"BMI         : {bc.bmi}  ({bc.bmi_category})")
    print(f"Body Fat %  : {bc.body_fat_pct}")
    print(f"Lean mass   : {bc.lean_mass_kg} kg")
    print(f"Fat mass    : {bc.fat_mass_kg} kg")

    banner("ENERGY EXPENDITURE & TARGET")
    e = rec.energy
    print(f"BMR (Mifflin) : {e.bmr_mifflin} kcal/day")
    print(f"BMR (Harris)  : {e.bmr_harris} kcal/day")
    if e.bmr_katch:
        print(f"BMR (Katch)   : {e.bmr_katch} kcal/day")
    print(f"TDEE          : {e.tdee} kcal/day "
          f"(x {e.activity_multiplier})")
    print(f"Target        : {e.calorie_target} kcal/day")
    print(f"Breakdown     : {e.calorie_target_breakdown}")

    banner("MACROS")
    m = rec.nutrition.macros
    print(f"Calories : {m.calories} kcal")
    print(f"Protein  : {m.protein_g} g  ({m.protein_pct}%)")
    print(f"Carbs    : {m.carbs_g} g  ({m.carbs_pct}%)")
    print(f"Fat      : {m.fat_g} g  ({m.fat_pct}%)")
    print(f"Rationale: {m.rationale}")
    print(f"Hydration: {rec.nutrition.hydration.total_ml} ml/day "
          f"(base {rec.nutrition.hydration.base_ml} ml + "
          f"{rec.nutrition.hydration.workout_bonus_ml} ml workout bonus)")

    banner("TRAINING - split & volume")
    t = rec.training
    print(f"Split     : S {t.split.strength_pct*100:.0f}% / "
          f"H {t.split.hypertrophy_pct*100:.0f}% / "
          f"C {t.split.cardio_pct*100:.0f}% / "
          f"M {t.split.mobility_pct*100:.0f}%")
    print(f"Volume    : {t.weekly_volume.total_sets} sets/week")
    for grp, sets_ in t.weekly_volume.per_muscle_group.items():
        print(f"  - {grp:14s}: {sets_} sets")
    print(f"Intensity : primary {t.intensity.primary_reps} @ RPE "
          f"{t.intensity.primary_rpe} / accessory "
          f"{t.intensity.accessory_reps} @ RPE {t.intensity.accessory_rpe}")
    print(f"Period    : {t.periodisation.scheme} "
          f"(cycle {t.periodisation.cycle_weeks}w, "
          f"deload every {t.periodisation.deload_every}w)")
    print(f"Progression: {t.progression.rule}")

    banner("CARDIO PRESCRIPTION")
    for k, v in t.cardio_prescription.items():
        print(f"  {k:22s}: {v}")
    print("Zones:")
    for name, (lo, hi) in t.cardio_zones.zones.items():
        print(f"  {name:18s}: {lo:.0f}-{hi:.0f} bpm")

    banner("WEEKLY SCHEDULE")
    for day, exs in t.weekly_schedule.items():
        print(f"\n  {day}:")
        for e in exs:
            print(f"    - {e['name']:36s} {e['sets_reps']:10s} "
                  f"RPE {e['rpe']}  ({e['primary_muscle']})")

    banner("WARM-UP / COOL-DOWN")
    print("Warm-up:")
    for s in t.warmup_protocol:
        print(f"  * {s}")
    print("Cool-down:")
    for s in t.cooldown_protocol:
        print(f"  * {s}")

    banner("MEAL PLAN")
    print(f"Cuisines       : {rec.nutrition.cuisine}")
    print(f"Plan name      : {rec.nutrition.meal_plan.name}")
    print(f"Notes          : {rec.nutrition.meal_plan.notes}")
    for meal in rec.nutrition.meal_plan.meals:
        print(f"  {meal.slot:10s} | {meal.name}")
        print(f"               {meal.calories:.0f} kcal  "
              f"P {meal.protein_g:.0f}  C {meal.carbs_g:.0f}  "
              f"F {meal.fat_g:.0f}  Fibre {meal.fibre_g:.0f}")
        if meal.recipe:
            print(f"               recipe: {meal.recipe}")

    banner("SUPPLEMENTS")
    s = rec.nutrition.supplements
    print("Foundational:")
    for name, dose, why in s["foundational"]:
        print(f"  * {name:24s} {dose:24s} - {why}")
    print("Goal-specific:")
    for name, dose, why in s["goal_specific"]:
        print(f"  * {name:24s} {dose:24s} - {why}")
    print("Conditional:")
    for name, dose, why in s["conditional"]:
        print(f"  * {name:24s} {dose:24s} - {why}")

    banner("MEDICAL OVERRIDES")
    for k, v in rec.nutrition.overrides.items():
        print(f"  * {k:14s}: {v}")

    banner("WARNINGS & NOTES")
    print("Warnings:")
    if rec.warnings:
        for w in rec.warnings:
            print(f"  ! {w}")
    else:
        print("  (none)")
    print("Notes:")
    for n in rec.notes:
        print(f"  i {n}")


if __name__ == "__main__":
    pretty_plan("examples/sample_client.json")
