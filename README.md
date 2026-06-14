# Fitness Engine — Personalised Exercise & Meal Plan Generator

A systematic, archetype-driven engine that takes detailed client profiles
and produces fully-customised **training programs**, **nutrition
plans**, and **coaching notes** — all grounded in evidence-based
methodology and tunable at every layer.

> Goal: turn a 90-second intake into a defensible, executable, and
> traceable plan a coach can hand to a client on day one.

---

## Highlights

- **9-dimensional archetype system** — every client becomes a
  deterministic, reproducible signature like
  `FAT-MESO-BEG-ADUL-F-SED-MEDI-GYM-60`. Combinatorial space:
  **2,956,800** unique signatures.
- **12 curated archetypes** with full profiles, summaries,
  strengths, risks, and emphasis points.
- **14 health/fitness calculators** — BMI, BMR (3 formulae), TDEE,
  calorie target, body fat (Navy & BMI-method), macros, hydration,
  1RM (3 formulae), cardio zones (Karvonen), somatotype inference.
- **6 validated intake questionnaires** — PAR-Q+, health history,
  lifestyle, dietary preferences, fitness history, goals.
- **9 decision-tree modules** — split, volume, intensity, exercise
  selection, periodisation, density, progression, macro overrides,
  cuisine selection, supplement stack.
- **40+ meal items** across 8 cuisines × 11 dietary patterns.
- **38 exercise records** with progressions, regressions,
  equipment tags, contraindications, and form cues.
- **Weekly meal rotation generator** with cuisine cycling.
- **HTML plan renderer** + **interactive intake form**.
- **CLI tool** for end-to-end plan generation.

---

## Quickstart

```bash
# 1. One-shot: run every demo, generate every HTML plan, run every test
bash examples/run_all.sh

# 2. CLI - generate a plan from a sample client
python -m fitness_engine.cli profile examples/sample_client.json
python -m fitness_engine.cli profile examples/sample_client.json \
    --format html --out output/sara_plan.html

# 3. CLI - archetype cohort showcase
python -m fitness_engine.cli showcase

# 4. CLI - list curated archetypes with their full profile
python -m fitness_engine.cli archetypes

# 5. CLI - scaffold a new client JSON profile
python -m fitness_engine.cli new /tmp/new_client.json

# 6. CLI - inspect the meal library
python -m fitness_engine.cli meals

# 7. Run the tests
PYTHONPATH=. python3 tests/test_calculators.py
PYTHONPATH=. python3 tests/test_integration.py

# 8. Pretty-print a full plan for a client (text mode)
python3 examples/demo_basic.py
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
    age=34, sex=Sex.FEMALE,
    height_cm=168, weight_kg=72,
    body_fat_pct=28,
    activity=ActivityLevel.SEDENTARY,
    experience=ExperienceLevel.BEGINNER,
    environment=TrainingEnvironment.GYM_COMMERCIAL,
    equipment=["barbell","bench","dumbbells",
               "machine","cardio_machine"],
    days_per_week=4,
    session_length=SessionLength.STANDARD_60,
    primary_goal=GoalArchetype.FAT_LOSS,
    dietary_preference=DietaryPreference.MEDITERRANEAN,
    parq_answers={f"parq_{i}": "no" for i in range(1, 8)},
)

rec = Recommender(profile).recommend()

print(rec.archetype_signature)               # FAT-MESO-BEG-ADUL-F-SED-MEDI-GYM-60
print(rec.energy.calorie_target)             # 1381.4
print(rec.nutrition.macros.protein_g)        # 144.0 g
print(rec.training.weekly_volume.total_sets) # 64 sets/wk
```

---

## Project layout

```
fitness_engine/         core Python package (3,900 LOC)
├── archetypes.py       9-dimensional archetype framework
├── calculators.py      14 health / fitness numerical engines
├── questionnaires.py   6 intake forms + intake_report()
├── decision_trees.py   9+ decision-tree modules
├── meal_plans.py       40+ meal items + cuisine / diet filters + week rotation
├── exercise_plans.py   38 exercises with progressions
├── recommender.py      Orchestrator: profile -> PlanRecommendation
└── cli.py              Command-line interface

examples/
├── intake_form.html         Interactive intake form (browser-based)
├── sample_client.json       Sara Martinez (fat loss, beginner)
├── sample_arthur.json       Arthur Chen (senior strength + HTN)
├── sample_lena.json         Lena Volkov (endurance athlete)
├── sample_maya.json         Maya Park (vegan athletic)
├── sample_derek.json        Derek Thompson (shift-worker beginner)
├── sample_emma.json         Emma Reyes (PCOS fat loss)
├── demo_basic.py            Pretty-print full plan
├── demo_arthur.py           Senior archetype demo
├── demo_archetypes.py       Cohort comparison of all archetypes
├── render_html.py           Standalone HTML renderer
└── run_all.sh               One-shot verification script

tests/
├── test_calculators.py   28 calculator unit tests
└── test_integration.py   13 integration tests (all archetypes)

docs/
├── 01_overview.md       System architecture, design principles
├── 02_archetypes.md     9 dimensions, 12 curated profiles
├── 03_calculators.md    All 14 numerical calculators
├── 04_questionnaires.md Intake form documentation
├── 05_decision_trees.md Decision-tree logic
├── 06_meal_plans.md     Meal library structure
├── 07_exercise_plans.md Exercise library structure
├── 08_api_reference.md  Python API reference
└── 09_methodology.md    Evidence base, references, limitations

output/                  Generated sample HTML plans
└── {name}_plan.html     One per sample client
```

---

## Curated archetypes

The engine ships with **12 hand-curated archetypes**, each capturing
a real-world clinical or coaching scenario:

| Code | Nickname | Goal × Profile |
|---|---|---|
| `office_worker_fat_loss` | The Desk-Bound Reset | Fat loss · sedentary beginner |
| `ectomorph_lean_gain` | The Classic Hard Gainer | Muscle gain · ectomorph intermediate |
| `postpartum_recomp` | The Reclaiming Parent | Recomp · postpartum home setup |
| `senior_strength_health` | The Vital Retiree | Strength · 60+ novice |
| `diabetes_reversal` | The Metabolic Rebuild | Health · T2 diabetes |
| `athlete_endurance` | The Endurance Specialist | Endurance · advanced female |
| `vegan_athlete` | The Plant-Powered Performer | Athletic · vegan male |
| `keto_cruiser` | The Keto Cruiser | Health · ketogenic |
| `shift_worker` | The Shift-Worker | Health · rotating shifts |
| `back_pain_returner` | The Back-Pain Returner | Rehab · chronic LBP |
| `youth_athlete` | The Youth Athlete | Athletic · 16-year-old |
| `pcos_balancer` | The PCOS Balancer | Fat loss · PCOS |

Each archetype has a nickname, summary, strengths, risks, and
emphasis points stored in the catalog.

---

## Sample cohort output

| Archetype | kcal | P | C | F | sets/wk | Periodisation |
|---|---|---|---|---|---|---|
| Desk-Bound Reset | 1381 | 144 | 56 | 65 | 64 | Linear Progression |
| Classic Hard Gainer | 2556 | 122 | 345 | 77 | 118 | Daily Undulating |
| Reclaiming Parent | 1905 | 129 | 209 | 61 | 78 | Linear Progression |
| Vital Retiree | 2279 | 144 | 255 | 76 | 40 | Linear Progression |
| Metabolic Rebuild | 2253 | 143 | 237 | 82 | 40 | Linear Progression |
| Endurance Specialist | 2825 | 93 | 423 | 85 | 52 | Block Periodisation |
| Plant-Powered Performer | 3328 | 133 | 491 | 92 | 78 | Linear w/ RPE Cap |
| Keto Cruiser | 2709 | 115 | 50 | 228 | 58 | Linear w/ RPE Cap |
| Shift-Worker | 2368 | 118 | 323 | 67 | 46 | Linear Progression |
| Back-Pain Returner | 1774 | 115 | 182 | 65 | 34 | Linear Progression |
| Youth Athlete | 3282 | 122 | 476 | 98 | 78 | Linear w/ RPE Cap |
| PCOS Balancer | 1464 | 160 | 44 | 72 | 64 | Linear Progression |

Note how:
- Fat loss / recomposition / rehab → maintenance calories or deficit
- Muscle gain / athletic / endurance → surplus (200-1000 kcal)
- Keto Cruiser → carbs collapsed to 50 g, fat at 70 % kcal
- PCOS Balancer → highest protein (160 g) for insulin sensitivity

---

## How it works

```
            ClientProfile
                 │
                 ▼
        ArchetypeSignature  ────► unique 9-axis code
                 │
   ┌─────────────┼─────────────┐
   ▼             ▼             ▼
Calculators   Decision Trees  Protocol Libraries
 (BMI, BMR,    (split,        (meals, exercises,
 TDEE, BF%,    volume,        cardio zones,
 macros,       intensity,     supplements)
 cardio        progression)
 zones)
   │             │             │
   └─────────────┴─────────────┘
                 │
                 ▼
       PlanRecommendation
       (training + nutrition + notes)
```

Every output traces back to a specific combination of inputs — so
any coach can audit, adjust, or override at any level.

---

## Documentation index

| Doc | Purpose |
|---|---|
| [docs/01_overview.md](docs/01_overview.md) | System architecture, design principles |
| [docs/02_archetypes.md](docs/02_archetypes.md) | The 9 archetype dimensions, 12 curated profiles |
| [docs/03_calculators.md](docs/03_calculators.md) | All 14 numerical calculators, formulae, examples |
| [docs/04_questionnaires.md](docs/04_questionnaires.md) | PAR-Q+, health, lifestyle, diet, fitness, goals |
| [docs/05_decision_trees.md](docs/05_decision_trees.md) | Decision logic from archetype to recommendation |
| [docs/06_meal_plans.md](docs/06_meal_plans.md) | Meal library structure, cuisine / diet filters, weekly rotation |
| [docs/07_exercise_plans.md](docs/07_exercise_plans.md) | Exercise library structure, splits, periodisation |
| [docs/08_api_reference.md](docs/08_api_reference.md) | Python API: every public symbol |
| [docs/09_methodology.md](docs/09_methodology.md) | Evidence base, references, limitations |

---

## License & disclaimer

This software is intended for **educational and coaching** use. It is
not a substitute for medical advice. Clients with diagnosed conditions
must obtain physician clearance before vigorous training, and PAR-Q
responses must be reviewed by a qualified professional.
# fit
