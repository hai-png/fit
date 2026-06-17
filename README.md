# Fitness Engine v2.4.0 — Evidence-Based Training & Meal Plan Generator

A deterministic Python engine that turns a client profile into a traceable training plan, nutrition target, weekly external-recipe meal plan, and coaching notes.

The engine is grounded in the RippedBody / Muscle & Strength Pyramid approach. All formulas, thresholds, and decision rules are documented in the [Unified Fitness Reference Guide](docs/reference/unified-fitness-reference-guide.md), which synthesizes 37+ articles from RippedBody, MacroFactor, FatCalc, GymGeek, ZoltHealth, and UltimatePerformance.

## What it provides

- **Training plans**: split selection (1-6 days), movement-pattern exercise selection, RIR/repetition targets, warm-up/cool-down, cardio zones, progression and periodisation notes.
- **Volume audit**: the generated schedule is compared with prescribed weekly sets per muscle group, with differences surfaced in the output for coaching adjustment.
- **Optional load guidance**: provide current working weights for key lifts and the schedule will include estimated 1RM and conservative starting-load guidance.
- **Nutrition and health-reference targets**: Mifflin-St Jeor BMR/TDEE, body-fat-aware fat-loss rates, Alpert max-deficit safeguard, goal-specific calorie targets, diet-aware macros, and anthropometric indices (WHtR, WHR, ABSI with z-score, Devine IBW).
- **7-day recipe meal plans**: external recipe database with diet/allergen filters, calorie scaling, protein/fibre quality checks, shopping list, alternatives, and automated quality audit.
- **Trainee classification**: RippedBody-style 9-category physique/strategy classification with pitfalls and recommendations.
- **Safety signals**: medical red-flag fields can mark a plan as requiring medical review. A minimal health-screen questionnaire populates these flags from intake. This is not a medical screening substitute.
- **Review utilities**: calculators for adaptive TDEE, macro cycling, reverse dieting and macro adjustments are exposed for coaching workflows.
- **Persistence**: SQLite coaching log with schema versioning, client/plan/weight/adherence storage, and client deletion.

## Current State

- **204 tests passing** + 22 subtests.
- Static analysis clean with `ruff`.
- All Critical (P0), Major (P1), and Minor (P2) findings from two independent engineering audits have been addressed. See `CHANGELOG.md` for the full remediation history.
- MIT licensed.

## Quickstart

```bash
# Install dev dependencies
python -m pip install -e ".[dev]"

# Run tests
python -m pytest -q

# Run lint
ruff check .

# Generate a text plan
python -m fitness_engine.cli profile examples/sample_client.json

# Generate HTML
python -m fitness_engine.cli profile examples/sample_client.json --format html --out output/plan.html

# Scaffold a new profile
python -m fitness_engine.cli new my_client.json

# Review logs for adaptive TDEE / reverse dieting
python -m fitness_engine.cli review review.json

# Optional local SQLite coaching log
python -m fitness_engine.cli db-init --db clients.db
python -m fitness_engine.cli store-client examples/sample_client.json --with-plan --db clients.db
python -m fitness_engine.cli update-weight sara-martinez 72.4 --day 8 --db clients.db
python -m fitness_engine.cli client-summary sara-martinez --db clients.db

# Editable install
python -m pip install -e .
fitness-engine --help
```

## Profile additions worth knowing

```json
{
  "medical_flags": {
    "pregnant_or_recent_postpartum": false,
    "recent_surgery": false,
    "diagnosed_eating_disorder": false,
    "cardiac_condition": false
  },
  "working_weights_kg": {
    "squat": 100,
    "bench_press": 80,
    "deadlift": 120,
    "overhead_press": 50
  },
  "plan_week": 1,
  "meal_plan_seed": null
}
```

`plan_week` is used to derive a deterministic meal-plan seed, so week 2 can produce a different repeatable recipe rotation without abandoning reproducibility. When `meal_plan_seed` is supplied, it is XORed with `plan_week` so each week still differs.

## Repository Structure

```text
fitness_engine/          # Core engine (14 modules, ~7k LOC)
data/
├── exercises/           # 115-exercise database
└── recipes/             # 323-recipe unified external database
docs/
├── reference/           # Unified Fitness Reference Guide (37 sources)
├── protocols/           # Plan-building protocols
└── analysis/            # Exercise database analysis
examples/                # 6 sample profiles + HTML renderer + run_all.sh
scripts/                 # Recipe database builder
tests/                   # 204 tests (calculators, integration, audit regressions)
```

## License & Disclaimer

MIT License. See `LICENSE` for details.

Educational and coaching use only. Not a substitute for medical advice, diagnosis or treatment. People with medical conditions, pregnancy/post-partum status, eating-disorder history, recent surgery, chest pain/fainting, or injuries should obtain qualified medical clearance before starting a generated plan.
