# Fitness Engine v2.0 — Personalised Exercise & Meal Plan Generator

A streamlined, evidence-based engine grounded in the **RippedBody**
methodology and the **Muscle & Strength** body-type framework. It takes
a simple client profile and produces a fully-customised **training
program**, **nutrition plan**, and **coaching notes**.

> Goal: turn a 90-second intake into a defensible, executable, and
> traceable plan grounded in real coaching methodology.

---

## What changed in v2.0

This is a ground-up redesign based on the RippedBody and M&S sources:

| Aspect | v1.0 | v2.0 |
|---|---|---|
| **Goals** | 8 (incl. endurance, athletic, rehab) | **5** — fat_loss, muscle_gain, recomp, strength, general_health |
| **Somatotype** | 4 (incl. mixed) | **3** — ectomorph, mesomorph, endomorph (M&S framework) |
| **Experience** | 5 tiers | **3** — beginner, intermediate, advanced |
| **Age groups** | 6 | **3** — young (18-30), adult (31-45), middle (46+) |
| **Activity** | 5 levels | **4** — RippedBody TDEE multipliers |
| **Diet** | 11 options | **2** — omnivore, vegan |
| **Environment** | 7 | **3** — home_bodyweight, home_gym, gym_full |
| **Calorie method** | Flat % of TDEE | **RippedBody**: 0.75%/wk cut, experience-tiered bulk |
| **Macro method** | g/kg fixed | **RippedBody**: protein by lean mass, fat 15-30%, carbs remainder |
| **Body fat** | Navy + Deurenberg | + **Visual estimation** (rippedbody.com/body-fat-guide) |
| **Questionnaires** | 6 forms incl. PAR-Q | **3 lean forms** + auto-generated health recommendations |
| **Trainee profiling** | None | **9 RippedBody categories** with strategy + pitfalls |
| **Decision trees** | Generic | **RippedBody Training Pyramid** (adherence → VIF → progression) |

---

## Methodology sources

- **Calories**: [rippedbody.com/calories](https://rippedbody.com/calories/) — Harris-Benedict BMR, 4-tier TDEE, 0.75%/wk fat loss
- **Macros**: [rippedbody.com/macros](https://rippedbody.com/macros/) — protein by lean mass, fat/carb bands
- **Body fat visual**: [rippedbody.com/body-fat-guide](https://rippedbody.com/body-fat-guide/)
- **9 trainee categories**: [goal-setting 1](https://rippedbody.com/goal-setting-1/), [2](https://rippedbody.com/goal-setting-2/), [3](https://rippedbody.com/goal-setting-3/)
- **Training programs**: [rippedbody.com/how-to-build-training-programs](https://rippedbody.com/how-to-build-training-programs/)
- **Somatotype**: [muscleandstrength.com](https://www.muscleandstrength.com/articles/body-types-ectomorph-mesomorph-endomorph.html)

---

## Highlights

- **9-dimensional archetype system** — deterministic signature like
  `MUS-ECTO-BEG-YOUN-M-LIG-OMNI-GYM-60`. Combinatorial space: **25,920**.
- **5 curated archetypes** covering the most common real-world scenarios.
- **RippedBody trainee categories** — classifies clients into 1 of 9
  physique states with tailored strategy, pitfalls, and recommendations.
- **Visual body-fat estimation** — when tape measurements aren't available,
  users self-classify against the RippedBody photo guide (7 bands).
- **Experience-tiered calorie targets** — beginners bulk faster, cut at
  0.75% BW/week; metabolic adaptation is accounted for.
- **47 exercises** with equipment-aware selection (hard filter) and A/B variation.
- **51 meals** across 8 cuisines, portion-scaled to hit calorie targets (≤0.4% error).
- **Streamlined intake** — 3 short forms instead of 6; health screening
  replaced by auto-generated recommendations.

---

## Quickstart

```bash
# Run all demos, generate HTML, run tests
bash examples/run_all.sh

# CLI - generate a plan from a sample client
python -m fitness_engine.cli profile examples/sample_client.json
python -m fitness_engine.cli profile examples/sample_client.json --format html --out output/plan.html

# CLI - archetype cohort showcase
python -m fitness_engine.cli showcase

# Run the tests
PYTHONPATH=. python3 tests/test_calculators.py
PYTHONPATH=. python3 tests/test_integration.py
```

---

## Five-second tour

```python
from fitness_engine import (
    ClientProfile, Recommender,
    Sex, ActivityLevel, GoalArchetype,
    ExperienceLevel, DietaryPreference,
    TrainingEnvironment, SessionLength,
)

profile = ClientProfile(
    age=22, sex=Sex.MALE,
    height_cm=180, weight_kg=64,
    body_fat_pct=11,
    activity=ActivityLevel.LIGHTLY_ACTIVE,
    experience=ExperienceLevel.BEGINNER,
    environment=TrainingEnvironment.GYM_FULL,
    days_per_week=4,
    session_length=SessionLength.STANDARD_60,
    primary_goal=GoalArchetype.MUSCLE_GAIN,
    dietary_preference=DietaryPreference.OMNIVORE,
    meals_per_day=4,
)

rec = Recommender(profile).recommend()

print(rec.archetype_signature)                 # MUS-ECTO-BEG-YOUN-M-LIG-OMNI-GYM-60
print(rec.trainee_category.category.value)     # skinny
print(rec.trainee_category.strategy)           # bulk
print(rec.energy.calorie_target)               # 3258.1
print(rec.nutrition.macros.protein_g)          # 125.3 g
print(rec.training.weekly_volume.total_sets)   # 70 sets/wk
```

---

## Project layout

```
fitness_engine/         core Python package
├── archetypes.py       9-dimensional archetype framework + 9 trainee categories
├── calculators.py      BMR, TDEE, calorie target, macros, visual BF, somatotype
├── questionnaires.py   3 streamlined intake forms + auto-recommendations
├── decision_trees.py   RippedBody Training Pyramid decision logic
├── meal_plans.py       51 meals + cuisine/diet filters + portion scaling
├── exercise_plans.py   47 exercises with equipment-aware selection
├── recommender.py      Orchestrator: profile -> PlanRecommendation
└── cli.py              Command-line interface

examples/
├── sample_*.json       6 pre-built client profiles
├── render_html.py      Standalone HTML renderer
└── run_all.sh          One-shot verification script

tests/
├── test_calculators.py    41 calculator unit tests
└── test_integration.py    14 integration tests (all archetypes)
```

---

## License & disclaimer

This software is intended for **educational and coaching** use. It is
not a substitute for medical advice. Clients with diagnosed conditions
must obtain physician clearance before vigorous training.
