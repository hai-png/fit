# 10 — CLI & Interactive Intake

## 10.1 Command-line interface

The engine ships with a CLI tool accessible via:

```bash
python -m fitness_engine.cli --help
```

### Sub-commands

| Command | Purpose |
|---|---|
| `profile <input.json>` | Generate a plan from a client JSON |
| `showcase` | Run every curated archetype and print one summary line |
| `archetypes` | List curated archetypes with full profile |
| `new <output.json>` | Scaffold an empty client JSON profile |
| `meals` | List the meal library by cuisine |

### `profile` options

```bash
python -m fitness_engine.cli profile examples/sample_client.json
python -m fitness_engine.cli profile examples/sample_client.json \
    --format text                          # default, prints to stdout
python -m fitness_engine.cli profile examples/sample_client.json \
    --format html --out plan.html          # HTML renderer
python -m fitness_engine.cli profile examples/sample_client.json \
    --format json --out plan.json          # full JSON dump
```

### Sample text output

```
Personalised Plan  -  signature FAT-MESO-BEG-ADUL-F-SED-MEDI-GYM-60

Body Composition: BMI 25.51 (overweight), BF 28%, lean 51.84 kg
Energy: BMR 1439.0 | TDEE 1726.8 | Target 1381.4 kcal
Macros: 144.0P / 55.6C / 64.8F (1381.4 kcal)
Training: 64 sets/wk, Linear Progression
Cardio: 132 min/wk

Monday:
  - Barbell bench press (3 x 10-15 RPE 7.5)
  - Bent-over barbell row (3 x 10-15 RPE 7.5)
  - ...
```

## 10.2 Interactive intake form

Open `examples/intake_form.html` in any browser. The form:

1. Shows **6 curated archetype cards** — click one to auto-fill the form
2. Walks through **7 sections**: Identity → PAR-Q+ → Lifestyle → Health → Diet → Training → Goals
3. Has full **client-side validation** for required fields
4. **Generates a JSON profile** in-browser
5. Lets the user **download the JSON** or **copy to clipboard**
6. Shows a **PAR-Q warning** if any "yes" responses

### Workflow

1. Open `examples/intake_form.html` in browser (or serve via any static server)
2. Fill in the form (or click an archetype card)
3. Click "Download JSON" — saves `client_name.json`
4. Run: `python -m fitness_engine.cli profile client_name.json --format html --out plan.html`
5. Open `plan.html` in browser

The form is a single self-contained HTML file (no external scripts or
stylesheets required) that works fully offline.

## 10.3 Programmatic flow

For backend integration (REST API, batch processing, etc.):

```python
from fitness_engine import ClientProfile, Recommender

# Build profile from form data
profile = ClientProfile.from_dict(request.json)

# Generate plan
rec = Recommender(profile).recommend()

# Return HTML or JSON
import json, dataclasses
return json.dumps(dataclasses.asdict(rec), default=str)
```

## 10.4 One-shot verification

`examples/run_all.sh` runs the full verification pipeline:

```bash
bash examples/run_all.sh
```

This:
1. Runs 28 calculator unit tests
2. Runs 13 integration tests (all archetypes)
3. Lists every curated archetype
4. Runs the cohort showcase
5. Generates HTML plans for every sample client
6. Prints sample CLI commands

Useful as a smoke test after changes.

## 10.5 Sample clients included

| File | Archetype | Notes |
|---|---|---|
| `sample_client.json` | Sara Martinez | Fat loss, beginner, Mediterranean |
| `sample_arthur.json` | Arthur Chen | Senior strength + HTN |
| `sample_lena.json` | Lena Volkov | Endurance athlete, advanced |
| `sample_maya.json` | Maya Park | Vegan athletic performance |
| `sample_derek.json` | Derek Thompson | Shift-worker, beginner |
| `sample_emma.json` | Emma Reyes | PCOS fat loss |

Each comes with a pre-rendered HTML plan in `output/`.

## 10.6 Customising the engine

### Override a single decision tree

```python
import fitness_engine.decision_trees as dt

def my_intensity(goal, experience, health):
    return dt.IntensityScheme("5-8", 8.0, "8-12", 8.0, "custom")

dt.intensity_scheme = my_intensity
```

The recommender picks up your override automatically.

### Add a new meal

```python
from fitness_engine.meal_plans import MealItem, MEAL_LIBRARY

MEAL_LIBRARY.append(MealItem(
    name="Beef and broccoli stir-fry",
    cuisine="asian",
    slot="dinner",
    calories=620, protein_g=38, carbs_g=62, fat_g=18, fibre_g=6,
    tags=["omnivore"],
    ingredients=["150g lean beef", "broccoli", "rice"],
    recipe="Stir-fry beef + broccoli; serve over jasmine rice.",
))
```

### Add a new archetype

```python
from fitness_engine import (
    ArchetypeProfile, ArchetypeSignature,
    GoalArchetype, Somatotype, ExperienceLevel, AgeGroup,
    Sex, ActivityLevel, DietaryPreference, TrainingEnvironment,
    SessionLength, CURATED_PROFILES,
)

CURATED_PROFILES["my_archetype"] = ArchetypeProfile(
    signature=ArchetypeSignature(
        goal=GoalArchetype.STRENGTH,
        somatotype=Somatotype.MESOMORPH,
        experience=ExperienceLevel.INTERMEDIATE,
        age_group=AgeGroup.ADULT,
        sex=Sex.MALE,
        activity=ActivityLevel.MODERATE,
        diet=DietaryPreference.OMNIVORE,
        environment=TrainingEnvironment.GYM_COMMERCIAL,
        session=SessionLength.STANDARD_60,
    ),
    nickname="My New Archetype",
    summary="...",
    strengths=["..."],
    risks=["..."],
    emphasis=["..."],
)
```

## 10.7 Production deployment notes

* The recommender is **stateless** — safe to run behind a load balancer
* All inputs are pure data — safe to log full profiles for QA
* Output is dataclasses that serialize cleanly via `dataclasses.asdict`
* For very large cohorts, use `enumerate_signatures()` to pre-warm
* For analytics, use the deterministic signature as a primary key
