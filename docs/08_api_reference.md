# 08 — API Reference

## Core classes

```python
from fitness_engine import (
    ClientProfile, Recommender, PlanRecommendation,
    TrainingPlan, NutritionPlan,
)
```

### ClientProfile

| Field | Type | Default |
|---|---|---|
| age | int | required |
| sex | Sex | required |
| height_cm | float | required |
| weight_kg | float | required |
| body_fat_pct | float \| None | None |
| waist_cm | float \| None | None |
| neck_cm | float \| None | None |
| hip_cm | float \| None | None |
| visual_bf_label | str \| None | None |
| wrist_cm | float \| None | None |
| resting_hr | int | 60 |
| activity | ActivityLevel | MOSTLY_SEDENTARY |
| dietary_preference | DietaryPreference | OMNIVORE |
| allergies | list[str] | [] |
| dislikes | list[str] | [] |
| meals_per_day | int | 4 |
| preferred_cuisines | list[str] | [] |
| experience | ExperienceLevel | BEGINNER |
| environment | TrainingEnvironment | GYM_FULL |
| days_per_week | int | 3 |
| session_length | SessionLength | STANDARD_60 |
| primary_goal | GoalArchetype | GENERAL_HEALTH |
| target_weight_kg | float \| None | None |
| timeline_weeks | int | 12 |
| motivation | str | "" |

### PlanRecommendation

| Field | Type |
|---|---|
| profile | dict |
| archetype_signature | str |
| trainee_category | TraineeProfile |
| body_composition | BodyComposition |
| energy | EnergyExpenditure |
| training | TrainingPlan |
| nutrition | NutritionPlan |
| muscular_potential | MuscularPotential \| None |
| intake_report | IntakeReport |
| warnings | list[str] |
| notes | list[str] |

## Quickstart

```python
from fitness_engine import *

profile = ClientProfile(
    age=22, sex=Sex.MALE, height_cm=180, weight_kg=64, body_fat_pct=11,
    activity=ActivityLevel.LIGHTLY_ACTIVE,
    experience=ExperienceLevel.BEGINNER,
    environment=TrainingEnvironment.GYM_FULL,
    days_per_week=4, session_length=SessionLength.STANDARD_60,
    primary_goal=GoalArchetype.MUSCLE_GAIN,
    dietary_preference=DietaryPreference.OMNIVORE,
    meals_per_day=4,
)
rec = Recommender(profile).recommend()
```

## Standalone calculators

All are importable directly:

```python
from fitness_engine import (
    bmi, body_fat_navy, body_fat_from_visual,
    bmr_harris_benedict, tdee, calorie_target,
    macros_for, micronutrient_targets, muscular_potential,
    one_rep_max, cardio_zones, hydration,
    classify_trainee, infer_somatotype,
)
```

## Adjustment tools

```python
from fitness_engine import (
    cut_adjustment_checklist, bulk_adjustment_checklist,
    training_plateau_checklist, progress_tracking_guide,
    metabolic_adaptation_info,
)
```
