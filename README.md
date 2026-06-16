# Fitness Engine v2.1 — Evidence-Based Training & Meal Plan Generator

A deterministic Python engine that turns a client profile into a traceable training plan, nutrition target, weekly external-recipe meal plan, and coaching notes.

The engine is grounded in the RippedBody / Muscle & Strength Pyramid approach, with additional safeguards and app-level protocols from the project reference guide.

---

## Current capabilities

- **Training plans** by goal, experience, days/week, session length, and available equipment.
- **Nutrition calculations** using Mifflin-St Jeor by default, guide-aligned activity multipliers, body-fat-aware cut rates, Alpert deficit capping, sex-specific calorie floors, and experience-tiered bulking rates.
- **Macro targets** that set protein first, preserve fat floors, use carbs as the remainder, and support diet-mode constraints such as keto, low-carb, Mediterranean, paleo, and high-protein.
- **Body composition tools** including BMI, Navy body-fat estimate, visual body-fat bands, FFMI, WHtR, WHR, ABSI, and Devine IBW.
- **7-day external-recipe meal planner** using a clean unified recipe database with alternatives for every meal.
- **Recipe quality audit** for calories, protein, fiber, diet compatibility, source confidence, slot sanity, variety, and portion scaling.
- **Protocol layer** that explains how each exercise and meal plan was built.
- **Common profile meal plans** generated under `output/common_meal_plans/`.

---

## v2.1 changes

| Area | v2.0 | v2.1 |
|---|---|---|
| BMR default | Harris-Benedict | Mifflin-St Jeor |
| Activity levels | 4 | 6 guide-compatible levels |
| Diet modes | 2 | 12 diet modes |
| Recipe source | curated internal meals | 323 clean standardized external recipes + legacy internal library |
| Weekly planner | day plan only | 7-day external-recipe planner with alternatives |
| Recipe QA | basic filtering | unified schema, sanitization, macro/fiber quality checks |
| Adaptive features | limited | adaptive TDEE helper, reverse diet helper, macro adjustment/cycling |
| Protocol output | implicit | explicit `rec.protocols` and weekly meal protocol notes |
| Archetype space | 25,920 | 233,280 signatures |

---

## External recipe database

Canonical recipe file:

```text
data/recipes/unified_external_recipes.json
```

Current clean recipe count:

| Source group | Clean planner-ready recipes |
|---|---:|
| Muscle & Strength | 147 |
| Trifecta | 137 |
| Ethiopian/African sources | 39 |
| **Total** | **323** |

Intermediate normalized files:

```text
data/recipes/normalized/muscleandstrength_recipes.json
data/recipes/normalized/trifecta_recipes.json
data/recipes/normalized/ethiopian_recipes.json
data/recipes/status/muscleandstrength_scrape_status.json
```

---

## Quickstart

```bash
# Run tests, showcase archetypes, and regenerate demo HTML plans
bash examples/run_all.sh

# Generate a text plan from a sample profile
python -m fitness_engine.cli profile examples/sample_client.json

# Generate HTML
python -m fitness_engine.cli profile examples/sample_client.json --format html --out output/plan.html

# Generate JSON
python -m fitness_engine.cli profile examples/sample_client.json --format json

# Run tests directly
python3 -m unittest tests.test_calculators tests.test_integration
```

---

## Five-second tour

```python
from fitness_engine import (
    ClientProfile, Recommender,
    Sex, ActivityLevel, GoalArchetype,
    ExperienceLevel, DietaryPreference,
    TrainingEnvironment, SessionLength,
    audit_7_day_meal_plan,
)

profile = ClientProfile(
    age=22,
    sex=Sex.MALE,
    height_cm=180,
    weight_kg=64,
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

audit = audit_7_day_meal_plan(rec.nutrition.weekly_meal_plan)

print(rec.archetype_signature)
print(rec.energy.calorie_target)
print(rec.nutrition.macros)
print(rec.training.split.name)
print(rec.protocols.exercise.split)
print(len(rec.nutrition.weekly_meal_plan.days))     # 7
print(len(rec.nutrition.weekly_meal_plan.alternatives))
print(audit.summary)
```

---

## Repository layout

```text
fitness_engine/                     core Python package
├── archetypes.py                    profile dimensions, signatures, trainee categories
├── calculators.py                   body comp, calories, macros, adaptive helpers
├── decision_trees.py                training split/volume/intensity/progression logic
├── exercise_plans.py                exercise library and schedule builder
├── meal_plans.py                    legacy curated meal library and day assembler
├── seven_day_meal_planner.py        external-recipe 7-day planner + alternatives
├── meal_plan_auditor.py             weekly meal-plan quality audit
├── protocols.py                     comprehensive exercise/meal protocol builders
├── questionnaires.py                intake forms and report helpers
├── adjustments.py                   plateau/progress/reverse-diet guidance
├── recommender.py                   profile → PlanRecommendation orchestrator
└── cli.py                           command-line interface

data/recipes/                       recipe data pipeline outputs
├── unified_external_recipes.json    canonical planner database
├── normalized/                      normalized source-specific recipe files
└── status/                          scrape status/failure records

scripts/                            data and output generation tools
├── scrape_external_recipes.py       Trifecta + M&S direct scrape attempts
├── import_muscleandstrength_recipes.py
├── scrape_ethiopian_recipes.py
├── build_unified_recipe_database.py
└── generate_common_profile_meal_plans.py

docs/
├── analysis/                        critical analysis of the repo
├── protocols/                       plan-building and recipe-system docs
├── reference/                       project reference guide
└── reports/                         remediation and meal-plan audit reports

examples/                           sample profiles and HTML renderer
output/                             generated demo plans and common-profile plans
tests/                              unit and integration tests
```

---

## Useful maintenance commands

```bash
# Re-import attached Muscle & Strength export
python3 scripts/import_muscleandstrength_recipes.py /home/user/uploads/recipes.json \
  --out data/recipes/normalized/muscleandstrength_recipes.json

# Re-scrape Trifecta recipes
python3 scripts/scrape_external_recipes.py --skip-mns --trifecta-pages 30 \
  --out data/recipes/normalized/trifecta_recipes.json

# Re-scrape Ethiopian recipe sources
python3 scripts/scrape_ethiopian_recipes.py \
  --out data/recipes/normalized/ethiopian_recipes.json

# Rebuild unified external recipe database
python3 scripts/build_unified_recipe_database.py \
  --out data/recipes/unified_external_recipes.json

# Regenerate common profile meal plans
python3 scripts/generate_common_profile_meal_plans.py
```

---

## Documentation

- Critical analysis: `docs/analysis/fit-analysis.md`
- Reference guide: `docs/reference/fitness-app-reference-guide.md`
- Plan protocols: `docs/protocols/comprehensive-plan-building-protocols.md`
- Recipe and 7-day meal planning system: `docs/protocols/recipe-scraping-and-7day-system.md`
- Meal-plan audit report: `docs/reports/meal-plan-quality-audit.md`
- Remediation report: `docs/reports/remediation-report.md`

---

## License & disclaimer

This software is intended for educational and coaching use. It is not a substitute for medical advice. Clients with diagnosed conditions, symptoms, pregnancy, eating-disorder risk, or very low calorie targets should seek professional medical guidance before following generated plans.
