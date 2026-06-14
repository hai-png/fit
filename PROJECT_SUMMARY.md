# Project Summary

## At a glance

| Metric | Value |
|---|---|
| Python LOC (core) | **4,137** |
| Test LOC | **412** (41 tests, all passing) |
| Documentation LOC | **2,654** (10 markdown files) |
| Example/demo LOC | **646** (Python + shell) |
| Sample clients | **6** with rendered HTML plans |
| Curated archetypes | **12** |
| Combinatorial space | **2,956,800** unique signatures |
| Meal library | **40+ items** × 8 cuisines |
| Exercise library | **38 items** with progressions |

## What's included

### Core Python package — `fitness_engine/`

| Module | LOC | Purpose |
|---|---|---|
| `archetypes.py` | 530+ | 9-dimensional archetype framework + 12 curated profiles |
| `calculators.py` | 465 | 14 numerical engines (BMI, BMR, TDEE, BF%, macros, hydration, 1RM, cardio zones) |
| `questionnaires.py` | 607 | 6 validated intake forms (PAR-Q+, health, lifestyle, diet, fitness, goals) |
| `decision_trees.py` | 490 | 10 decision-tree modules (split, volume, intensity, exercise selection, periodisation, density, progression, macro overrides, cuisine pick, supplement stack) |
| `meal_plans.py` | 690+ | 40+ meals, cuisine/diet filters, daily + weekly rotation |
| `exercise_plans.py` | 436 | 38 exercises with progressions/regressions, weekly splits |
| `recommender.py` | 453+ | Orchestrator: ClientProfile → PlanRecommendation |
| `cli.py` | 280+ | Command-line interface |
| `__init__.py` | 90+ | Public API surface |

### Tests — `tests/`

| File | Tests | Coverage |
|---|---|---|
| `test_calculators.py` | 28 | BMI, BMR, TDEE, calorie target, 1RM, cardio zones, hydration, macros, age groups, somatotype, end-to-end |
| `test_integration.py` | 13 | All 12 archetypes run, sanity invariants per archetype, profile JSON round-trip, archetype cardinality |

### Documentation — `docs/`

| File | LOC | Purpose |
|---|---|---|
| `01_overview.md` | 110 | System architecture, design principles |
| `02_archetypes.md` | 174 | 9 dimensions, 12 curated profiles |
| `03_calculators.md` | 229 | All 14 numerical calculators with formulae |
| `04_questionnaires.md` | 190 | PAR-Q+, all 6 intake forms |
| `05_decision_trees.md` | 292 | All 10 decision trees with execution order |
| `06_meal_plans.md` | 200+ | Meal library + daily/weekly rotation |
| `07_exercise_plans.md` | 238 | Exercise library + splits + periodisation |
| `08_api_reference.md` | 502 | Python API: every public symbol |
| `09_methodology.md` | 256 | Evidence base + references |
| `10_cli_and_intake.md` | 188 | CLI, intake form, customisation, deployment |

### Examples — `examples/`

| File | Type | Purpose |
|---|---|---|
| `intake_form.html` | Self-contained HTML | Interactive 7-section intake form, archetype cards, JSON download |
| `sample_*.json` (6 files) | JSON | Pre-built client profiles for every major archetype |
| `demo_basic.py` | Python | Pretty-print a full plan |
| `demo_arthur.py` | Python | Senior archetype demo |
| `demo_archetypes.py` | Python | Cohort comparison of all archetypes |
| `render_html.py` | Python | Standalone HTML renderer |
| `run_all.sh` | Bash | One-shot verification pipeline |

### Generated outputs — `output/`

7 HTML plans, one per sample client:
- `sara_plan.html` (fat loss, beginner)
- `arthur_plan.html` (senior strength + HTN)
- `lena_plan.html` (endurance athlete)
- `maya_plan.html` (vegan athletic)
- `derek_plan.html` (shift-worker beginner)
- `emma_plan.html` (PCOS fat loss)
- `client_plan.html` (from run_all.sh scaffold)

## How to run

### Quickstart

```bash
bash examples/run_all.sh       # full verification + HTML generation
python3 examples/demo_basic.py # pretty-print a full plan
```

### CLI

```bash
python -m fitness_engine.cli profile examples/sample_client.json
python -m fitness_engine.cli profile examples/sample_client.json --format html --out plan.html
python -m fitness_engine.cli showcase
python -m fitness_engine.cli archetypes
python -m fitness_engine.cli new /tmp/new.json
python -m fitness_engine.cli meals
```

### Python

```python
from fitness_engine import (
    ClientProfile, Recommender,
    Sex, ActivityLevel, GoalArchetype,
    ExperienceLevel, DietaryPreference,
    TrainingEnvironment, SessionLength,
)
profile = ClientProfile(
    age=34, sex=Sex.FEMALE, height_cm=168, weight_kg=72,
    body_fat_pct=28,
    activity=ActivityLevel.SEDENTARY,
    experience=ExperienceLevel.BEGINNER,
    environment=TrainingEnvironment.GYM_COMMERCIAL,
    equipment=["barbell","bench","dumbbells"],
    days_per_week=4,
    session_length=SessionLength.STANDARD_60,
    primary_goal=GoalArchetype.FAT_LOSS,
    dietary_preference=DietaryPreference.MEDITERRANEAN,
    parq_answers={f"parq_{i}": "no" for i in range(1, 8)},
)
rec = Recommender(profile).recommend()
print(rec.archetype_signature, rec.energy.calorie_target,
      rec.nutrition.macros.protein_g)
```

### Tests

```bash
PYTHONPATH=. python3 tests/test_calculators.py
PYTHONPATH=. python3 tests/test_integration.py
```

## Architecture

```
            ClientProfile
                 │
                 ▼
        ArchetypeSignature  ──► unique 9-axis code (2,956,800 possible)
                 │
   ┌─────────────┼─────────────┐
   ▼             ▼             ▼
Calculators   Decision Trees  Protocol Libraries
 (math)        (logic)        (meals, exercises)
   │             │             │
   └─────────────┴─────────────┘
                 │
                 ▼
       PlanRecommendation
       (training + nutrition + notes)
```

Every output traces back to a specific combination of inputs — so
any coach can audit, adjust, or override at any level.

## License & disclaimer

Educational and coaching use only. Not a substitute for medical
advice. PAR-Q responses must be reviewed by a qualified professional.
