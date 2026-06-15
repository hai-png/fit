# 01 — System Overview

## Architecture

The Fitness Engine is a streamlined, evidence-based system that turns a
simple client profile into a fully-customised training program,
nutrition plan, and coaching notes.

```
            ClientProfile  (lean, ~20 fields)
                 │
        ┌────────┴────────┐
        ▼                 ▼
   Body Composition   Somatotype (M&S)
   (Navy / Visual /      │
    Deurenberg)           │
        │                 │
        ▼                 ▼
   Trainee Category (RippedBody 9 types)
        │
   ┌────┼─────────────┐
   ▼    ▼             ▼
Calories  Macros    Training
(RippedBody) (RippedBody) (Pyramid)
   │    │             │
   └────┼─────────────┘
        ▼
      PlanRecommendation
```

## Design principles

1. **Simplicity** — fewer dimensions, fewer options, faster intake (~90s).
2. **Evidence-based** — every formula and rule traces to a cited source.
3. **Determinism** — the same inputs always produce the same outputs.
4. **Explainability** — every recommendation carries a rationale string.
5. **Hard filters** — equipment, exclusions, and safety floors are never
   silently relaxed.

## Modules

| Module | Purpose |
|---|---|
| `archetypes.py` | 9-dimensional signature + 9 trainee categories + curated profiles |
| `calculators.py` | BMR, TDEE, calorie target, macros, body composition, somatotype, FFMI, micros |
| `questionnaires.py` | 3 lean intake forms + auto-generated health recommendations |
| `decision_trees.py` | RippedBody Training Pyramid: split, volume, intensity, progression |
| `exercise_plans.py` | 47 exercises with equipment-aware selection + A/B variation |
| `meal_plans.py` | 51 meals, cuisine filters, portion-scaled assembly |
| `adjustments.py` | Diet/training adjustment checklists, plateau trees, progress tracking |
| `recommender.py` | Orchestrator: profile → PlanRecommendation |
| `cli.py` | Command-line interface |

## Version

**v2.1.0** — grounded in the RippedBody Nutrition & Training Pyramids
and the Muscle & Strength body-type framework.
