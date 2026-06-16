# Fitness Engine v2.2 — Evidence-Based Training & Meal Plan Generator

A deterministic Python engine that turns a client profile into a traceable training plan, nutrition target, weekly external-recipe meal plan, and coaching notes.

The engine is grounded in the RippedBody / Muscle & Strength Pyramid approach, with full alignment to the project reference guide.

## Current State (v2.2)

- Fully remediated against the comprehensive reference guide
- All major issues from the critical analysis have been fixed
- 80+ passing tests
- Clean, focused repository structure

## Quickstart

```bash
# Run tests
python3 -m unittest tests.test_calculators tests.test_integration

# Generate a text plan
python -m fitness_engine.cli profile examples/sample_client.json

# Generate HTML
python -m fitness_engine.cli profile examples/sample_client.json --format html --out output/plan.html
```

## Repository Structure

```
fitness_engine/          # Core engine
data/recipes/            # Unified external recipe database
docs/
├── reference/           # Fitness App Reference Guide
└── protocols/           # Plan-building protocols
examples/                # Sample profiles & runners
output/                  # Generated plans
scripts/                 # Maintenance & data tools
tests/                   # Comprehensive test suite
```

## License & Disclaimer

Educational and coaching use only. Not a substitute for medical advice.