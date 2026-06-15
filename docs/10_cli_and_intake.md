# 10 — CLI & Usage

## Commands

```bash
# Generate a plan from a client JSON profile
python -m fitness_engine.cli profile examples/sample_client.json

# Output as HTML
python -m fitness_engine.cli profile examples/sample_client.json --format html --out output/plan.html

# Output as JSON
python -m fitness_engine.cli profile examples/sample_client.json --format json

# Run all curated archetypes (cohort table)
python -m fitness_engine.cli showcase

# List curated archetypes with full profiles
python -m fitness_engine.cli archetypes

# Scaffold a new client JSON
python -m fitness_engine.cli new /tmp/new_client.json

# List the meal library
python -m fitness_engine.cli meals
```

## Client JSON format

Minimal example:

```json
{
  "name": "Jane Doe",
  "age": 30,
  "sex": "female",
  "height_cm": 165,
  "weight_kg": 62,
  "visual_bf_label": "average_fit",
  "activity": "mostly_sedentary",
  "dietary_preference": "omnivore",
  "experience": "beginner",
  "environment": "gym_full",
  "days_per_week": 3,
  "session_length": "standard_60",
  "primary_goal": "fat_loss",
  "target_weight_kg": 58,
  "timeline_weeks": 12,
  "meals_per_day": 4
}
```

All fields except `age`, `sex`, `height_cm`, and `weight_kg` have
sensible defaults. `body_fat_pct`, `visual_bf_label`, `waist_cm`,
and `neck_cm` are all optional — body fat is inferred if none are given.

## Running tests

```bash
PYTHONPATH=. python3 tests/test_calculators.py
PYTHONPATH=. python3 tests/test_integration.py
```

## Full pipeline

```bash
bash examples/run_all.sh
```

## HTML output

Plans render as self-contained HTML (inline CSS, no external resources).
Use `examples/render_html.py` standalone:

```bash
python3 examples/render_html.py examples/sample_client.json output/plan.html
```
