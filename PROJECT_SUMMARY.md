# Project Summary — Fitness Engine v2.1

## At a glance

| Metric | Value |
|---|---|
| Core Python LOC | ~4,700 |
| Tests | 66 (52 calculator + 14 integration) |
| Curated archetypes | 5 |
| Combinatorial space | 25,920 signatures |
| Trainee categories | 9 (RippedBody) |
| Exercise library | 48 items |
| Meal library | 51 items × 8 cuisines |
| Visual BF bands | 7 |
| Total files | 48 |

## Methodology

Grounded in:
- **RippedBody** Nutrition & Training Pyramids
- **Muscle & Strength** body-type classification
- **Kouri et al. 1995** FFMI research

## Module breakdown

| Module | LOC | Purpose |
|---|---|---|
| `archetypes.py` | 430 | 9-dim signature, 9 trainee categories, 5 curated profiles |
| `calculators.py` | 620 | BMR, TDEE, calories, macros, body composition, FFMI, micros |
| `questionnaires.py` | 250 | 3 lean intake forms + auto-recommendations |
| `decision_trees.py` | 350 | RippedBody Training Pyramid decision logic |
| `exercise_plans.py` | 530 | 48 exercises, equipment-aware selection, A/B variation |
| `meal_plans.py` | 690 | 51 meals, cuisine filters, portion-scaled assembly |
| `adjustments.py` | 350 | Diet/training checklists, plateau trees, progress tracking |
| `recommender.py` | 280 | Orchestrator: profile → PlanRecommendation |
| `cli.py` | 250 | Command-line interface |

## How to run

```bash
bash examples/run_all.sh       # full verification + HTML generation
PYTHONPATH=. python3 tests/test_calculators.py
PYTHONPATH=. python3 tests/test_integration.py
python -m fitness_engine.cli showcase
```

## License

Educational and coaching use only. Not a substitute for medical advice.
