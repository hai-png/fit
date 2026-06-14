"""
demo_archetypes.py
==================

Run every curated archetype through the recommender and print a
one-line summary. Useful for cohort dashboards, QA, and ensuring
that every archetype signature produces a coherent plan.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fitness_engine import (
    ClientProfile, Recommender, Sex,
    all_curated, get_curated,
)


# Per-archetype sensible body-composition defaults.
DEFAULTS = {
    "The Desk-Bound Reset": dict(
        age=34, sex=Sex.FEMALE, height_cm=168, weight_kg=72,
        body_fat_pct=32, waist_cm=82, neck_cm=33,
    ),
    "The Classic Hard Gainer": dict(
        age=22, sex=Sex.MALE, height_cm=180, weight_kg=64,
        body_fat_pct=11, waist_cm=74, neck_cm=37,
    ),
    "The Reclaiming Parent": dict(
        age=33, sex=Sex.FEMALE, height_cm=165, weight_kg=68,
        body_fat_pct=27, waist_cm=80, neck_cm=32,
    ),
    "The Vital Retiree": dict(
        age=64, sex=Sex.MALE, height_cm=175, weight_kg=80,
        body_fat_pct=22, waist_cm=92, neck_cm=38,
    ),
    "The Metabolic Rebuild": dict(
        age=52, sex=Sex.MALE, height_cm=178, weight_kg=102,
        body_fat_pct=32, waist_cm=110, neck_cm=40,
    ),
    "The Endurance Specialist": dict(
        age=26, sex=Sex.FEMALE, height_cm=170, weight_kg=58,
        body_fat_pct=16, waist_cm=68, neck_cm=29,
    ),
    "The Plant-Powered Performer": dict(
        age=27, sex=Sex.MALE, height_cm=178, weight_kg=74,
        body_fat_pct=12, waist_cm=76, neck_cm=37,
    ),
    "The Keto Cruiser": dict(
        age=38, sex=Sex.MALE, height_cm=178, weight_kg=82,
        body_fat_pct=18, waist_cm=88, neck_cm=39,
    ),
    "The Shift-Worker": dict(
        age=42, sex=Sex.MALE, height_cm=174, weight_kg=84,
        body_fat_pct=24, waist_cm=94, neck_cm=39,
    ),
    "The Back-Pain Returner": dict(
        age=39, sex=Sex.FEMALE, height_cm=167, weight_kg=72,
        body_fat_pct=30, waist_cm=86, neck_cm=32,
    ),
    "The Youth Athlete": dict(
        age=16, sex=Sex.MALE, height_cm=175, weight_kg=68,
        body_fat_pct=12, waist_cm=72, neck_cm=33,
    ),
    "The PCOS Balancer": dict(
        age=29, sex=Sex.FEMALE, height_cm=165, weight_kg=80,
        body_fat_pct=36, waist_cm=92, neck_cm=33,
    ),
}


def build_profile(ap) -> ClientProfile:
    sig = ap.signature
    d = DEFAULTS[ap.nickname]
    return ClientProfile(
        age=d["age"], sex=d["sex"], height_cm=d["height_cm"],
        weight_kg=d["weight_kg"], body_fat_pct=d.get("body_fat_pct"),
        waist_cm=d.get("waist_cm"), neck_cm=d.get("neck_cm"),
        activity=sig.activity, sleep_hours=7.0, stress_level=4,
        health_conditions=[],
        dietary_preference=sig.diet,
        allergies=[], meals_per_day=4,
        experience=sig.experience,
        environment=sig.environment,
        equipment=["barbell","bench","dumbbells","machine",
                   "cardio_machine","kettlebells","pullup_bar"],
        days_per_week=4,
        session_length=sig.session,
        primary_goal=sig.goal,
        timeline_weeks=12,
        parq_answers={f"parq_{i}":"no" for i in range(1, 8)},
    )


def main():
    print("=" * 120)
    print(f"{'Archetype':32s} {'Signature':32s} "
          f"{'kcal':>6s} {'P':>4s} {'C':>4s} {'F':>4s} "
          f"{'sets':>5s} {'period':24s}")
    print("=" * 120)
    for ap in all_curated():
        try:
            p = build_profile(ap)
            rec = Recommender(p).recommend()
            m = rec.nutrition.macros
            v = rec.training.weekly_volume.total_sets
            per = rec.training.periodisation.scheme[:24]
            print(f"{ap.nickname[:32]:32s} {rec.archetype_signature:32s} "
                  f"{rec.energy.calorie_target:6.0f} "
                  f"{m.protein_g:4.0f} {m.carbs_g:4.0f} {m.fat_g:4.0f} "
                  f"{v:5d} {per:24s}")
        except Exception as e:
            print(f"{ap.nickname[:32]:32s} ERROR: {e}")


if __name__ == "__main__":
    main()
