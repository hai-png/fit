#!/usr/bin/env python3
"""Generate 7-day external-recipe meal plans with alternatives for common profiles."""
from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fitness_engine import (
    ActivityLevel, ClientProfile, DietaryPreference, ExperienceLevel,
    GoalArchetype, Recommender, SessionLength, Sex, TrainingEnvironment,
    audit_7_day_meal_plan,
)

COMMON_PROFILES = {
    "male_fat_loss_omnivore": ClientProfile(
        age=35, sex=Sex.MALE, height_cm=178, weight_kg=92, body_fat_pct=25,
        activity=ActivityLevel.MODERATELY_ACTIVE, experience=ExperienceLevel.INTERMEDIATE,
        environment=TrainingEnvironment.GYM_FULL, days_per_week=4,
        session_length=SessionLength.STANDARD_60, primary_goal=GoalArchetype.FAT_LOSS,
        dietary_preference=DietaryPreference.OMNIVORE, meals_per_day=4,
        preferred_cuisines=["american", "mexican"],
    ),
    "female_fat_loss_gluten_free": ClientProfile(
        age=34, sex=Sex.FEMALE, height_cm=165, weight_kg=76, body_fat_pct=34,
        activity=ActivityLevel.LIGHTLY_ACTIVE, experience=ExperienceLevel.BEGINNER,
        environment=TrainingEnvironment.GYM_FULL, days_per_week=3,
        session_length=SessionLength.SHORT_45, primary_goal=GoalArchetype.FAT_LOSS,
        dietary_preference=DietaryPreference.GLUTEN_FREE, meals_per_day=4,
        preferred_cuisines=["american", "mediterranean"],
    ),
    "male_muscle_gain_omnivore": ClientProfile(
        age=24, sex=Sex.MALE, height_cm=180, weight_kg=72, body_fat_pct=13,
        activity=ActivityLevel.MODERATELY_ACTIVE, experience=ExperienceLevel.BEGINNER,
        environment=TrainingEnvironment.GYM_FULL, days_per_week=4,
        session_length=SessionLength.STANDARD_60, primary_goal=GoalArchetype.MUSCLE_GAIN,
        dietary_preference=DietaryPreference.OMNIVORE, meals_per_day=5,
        preferred_cuisines=["american", "mexican", "asian"],
    ),
    "female_recomp_vegetarian": ClientProfile(
        age=29, sex=Sex.FEMALE, height_cm=168, weight_kg=64, body_fat_pct=27,
        activity=ActivityLevel.MODERATELY_ACTIVE, experience=ExperienceLevel.BEGINNER,
        environment=TrainingEnvironment.HOME_GYM, days_per_week=3,
        session_length=SessionLength.STANDARD_60, primary_goal=GoalArchetype.RECOMPOSITION,
        dietary_preference=DietaryPreference.VEGETARIAN, meals_per_day=4,
        preferred_cuisines=["mediterranean", "american"],
    ),
    "female_vegan_general_health": ClientProfile(
        age=30, sex=Sex.FEMALE, height_cm=165, weight_kg=60, body_fat_pct=25,
        activity=ActivityLevel.SEDENTARY, experience=ExperienceLevel.BEGINNER,
        environment=TrainingEnvironment.HOME_GYM, days_per_week=3,
        session_length=SessionLength.SHORT_45, primary_goal=GoalArchetype.GENERAL_HEALTH,
        dietary_preference=DietaryPreference.VEGAN, meals_per_day=4,
        preferred_cuisines=["american", "asian", "indian"],
    ),
    "male_keto_fat_loss": ClientProfile(
        age=42, sex=Sex.MALE, height_cm=176, weight_kg=98, body_fat_pct=30,
        activity=ActivityLevel.LIGHTLY_ACTIVE, experience=ExperienceLevel.INTERMEDIATE,
        environment=TrainingEnvironment.GYM_FULL, days_per_week=3,
        session_length=SessionLength.STANDARD_60, primary_goal=GoalArchetype.FAT_LOSS,
        dietary_preference=DietaryPreference.KETO, meals_per_day=4,
        preferred_cuisines=["american"],
    ),

    "ethiopian_omnivore_fat_loss": ClientProfile(
        age=38, sex=Sex.MALE, height_cm=176, weight_kg=88, body_fat_pct=24,
        activity=ActivityLevel.MODERATELY_ACTIVE, experience=ExperienceLevel.INTERMEDIATE,
        environment=TrainingEnvironment.GYM_FULL, days_per_week=4,
        session_length=SessionLength.STANDARD_60, primary_goal=GoalArchetype.FAT_LOSS,
        dietary_preference=DietaryPreference.OMNIVORE, meals_per_day=4,
        preferred_cuisines=["ethiopian", "american"],
    ),
    "ethiopian_vegan_recomp": ClientProfile(
        age=31, sex=Sex.FEMALE, height_cm=165, weight_kg=62, body_fat_pct=27,
        activity=ActivityLevel.LIGHTLY_ACTIVE, experience=ExperienceLevel.BEGINNER,
        environment=TrainingEnvironment.HOME_GYM, days_per_week=3,
        session_length=SessionLength.STANDARD_60, primary_goal=GoalArchetype.RECOMPOSITION,
        dietary_preference=DietaryPreference.VEGAN, meals_per_day=4,
        preferred_cuisines=["ethiopian", "african"],
    ),
    "adult_general_health_mediterranean": ClientProfile(
        age=45, sex=Sex.FEMALE, height_cm=166, weight_kg=70, body_fat_pct=30,
        activity=ActivityLevel.LIGHTLY_ACTIVE, experience=ExperienceLevel.BEGINNER,
        environment=TrainingEnvironment.HOME_GYM, days_per_week=3,
        session_length=SessionLength.SHORT_45, primary_goal=GoalArchetype.GENERAL_HEALTH,
        dietary_preference=DietaryPreference.MEDITERRANEAN, meals_per_day=4,
        preferred_cuisines=["mediterranean"],
    ),
}


def main() -> int:
    out_dir = Path("output/common_meal_plans")
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_lines = ["# Common Profile 7-Day Meal Plans", "", "All plans use external recipes only, with alternatives per meal.", ""]
    for name, profile in COMMON_PROFILES.items():
        rec = Recommender(profile).recommend()
        week = rec.nutrition.weekly_meal_plan
        audit = audit_7_day_meal_plan(week)
        payload = {
            "profile_name": name,
            "profile": profile.to_dict(),
            "calories": rec.energy.calorie_target,
            "macros": dataclasses.asdict(rec.nutrition.macros),
            "audit": dataclasses.asdict(audit),
            "weekly_meal_plan": dataclasses.asdict(week),
        }
        (out_dir / f"{name}.json").write_text(json.dumps(payload, indent=2, default=str))
        summary_lines.extend([
            f"## {name}",
            "",
            f"- Calories: {rec.energy.calorie_target:.0f} kcal",
            f"- Macros: P{rec.nutrition.macros.protein_g:.0f} / C{rec.nutrition.macros.carbs_g:.0f} / F{rec.nutrition.macros.fat_g:.0f}",
            f"- Diet: {profile.dietary_preference.value}",
            f"- Audit: {audit.grade} ({audit.score}/100)",
            f"- Source mix: {week.source_summary}",
            "",
        ])
        alt_lookup = {(a.day, a.selected): a.alternatives for a in week.alternatives}
        for day in week.days:
            summary_lines.append(f"### {day.name}")
            for meal in day.meals:
                summary_lines.append(f"- **{meal.slot}**: {meal.name} — {meal.calories:.0f} kcal, P{meal.protein_g:.0f}/C{meal.carbs_g:.0f}/F{meal.fat_g:.0f}")
                alts = alt_lookup.get((day.name, meal.name), [])[:2]
                if alts:
                    summary_lines.append("  - Alternatives: " + "; ".join(f"{a.name} ({a.calories:.0f} kcal)" for a in alts))
            summary_lines.append("")
        summary_lines.append(f"JSON: `{name}.json`\n")
    (out_dir / "README.md").write_text("\n".join(summary_lines))
    print(f"Wrote {len(COMMON_PROFILES)} plans to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
