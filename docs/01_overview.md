# 01 — System Overview

## 1.1 Mission

Turn a 90-second intake into a defensible, executable, and traceable
training + nutrition plan for any client profile, while making every
recommendation auditable.

## 1.2 Design principles

| Principle | Implementation |
|---|---|
| **Orthogonality** | Each archetype dimension is independent |
| **Enumerability** | All values are `Enum` members |
| **Determinism** | Same input → same plan, byte-for-byte |
| **Explainability** | Every output links back to specific inputs |
| **Composability** | Trees are small, named, independent |
| **Auditability** | PAR-Q, warnings, notes always surfaced |
| **Pure functions** | Calculators have no hidden state |

## 1.3 Layered architecture

```
            ┌──────────────────────────────────┐
            │       ClientProfile (input)      │
            └────────────────┬─────────────────┘
                             │
                  ┌──────────▼──────────┐
                  │   Archetype Engine  │   signature code
                  └──────────┬──────────┘
                             │
       ┌─────────────────────┼─────────────────────┐
       │                     │                     │
┌──────▼──────┐      ┌───────▼────────┐    ┌──────▼─────────┐
│ Calculators │      │ Decision Trees │    │   Protocol     │
│  (math)     │      │   (logic)      │    │  Libraries     │
└──────┬──────┘      └───────┬────────┘    └──────┬─────────┘
       │                     │                     │
       └─────────────────────┼─────────────────────┘
                             │
                  ┌──────────▼──────────┐
                  │   PlanRecommendation│
                  │   (output)          │
                  └─────────────────────┘
```

## 1.4 The three vertical pillars

### Calculators — *what is true about this body?*
14 pure functions: BMI, three BMR equations, TDEE, calorie target,
two body-fat estimators, lean mass, hydration, three 1RM equations,
cardio zones (Karvonen), somatotype inference.

### Decision Trees — *what should we do given that truth?*
Nine small named functions:
* `training_split` — strength/hypertrophy/cardio/mobility %
* `weekly_volume` — sets per muscle group
* `intensity_scheme` — rep range + RPE cap
* `exercise_selection` — include / exclude / substitute rules
* `periodisation` — linear / DUP / block / 5-3-1
* `session_density` — work:rest ratios
* `progression_rule` — how to add load
* `macro_overrides` — medical / dietary adjustments
* `cuisine_pick` — diet → cuisine mapping
* `supplement_stack` — goal + sex + condition stack

### Protocol Libraries — *what are the actual meals and exercises?*
70+ meal items across 8 cuisines × 7 diets. 40+ exercises with
progressions, regressions, equipment tags, contraindications, form cues.

## 1.5 Reproducibility

The recommender is **deterministic**: given the same `ClientProfile`,
the same `PlanRecommendation` is produced. No randomness, no clock,
no global state.

This means:
* Plans can be regenerated and diffed.
* Coach overrides are explicit (just edit the JSON profile).
* Quality assurance is straightforward (one input → one output).

## 1.6 Extending the engine

* **Add a new dimension**: drop a new `Enum` into `archetypes.py`,
  add a field to `ArchetypeSignature`, update the `code()` method,
  and reference it from any decision tree.
* **Add a new meal**: append a `MealItem` to `MEAL_LIBRARY` with
  cuisine + slot + diet tags.
* **Add a new exercise**: append an `Exercise` to `EXERCISE_LIBRARY`.
* **Override a tree**: monkey-patch the function in
  `decision_trees.py` for an A/B test.

## 1.7 Limitations

1. The recommender produces one day's meals, not a rotating 7-day
   rotation. Rotate manually or extend `assemble_day`.
2. Body-fat estimates are **estimates**; gold standard is DXA.
3. Somatotype inference is a heuristic from BMI + body-fat %.
4. Supplementation guidance is generic; do not prescribe
   pharmacologically active substances without medical sign-off.
5. PAR-Q scoring is a binary trigger — physician clearance is the
   appropriate follow-up for any positive response.

## 1.8 Intended users

* **Coaches** — generate first-draft plans, then refine.
* **Health-clinic intake staff** — consistent triage & outputs.
* **App developers** — embed as a Python service / REST API.
* **Researchers** — run cohort analyses on the deterministic
  archetype space.
