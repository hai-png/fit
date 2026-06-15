# 07 — Exercise Plans

## Library

47 exercises organised by movement pattern, each with:
- Equipment requirements
- Primary + secondary muscles
- Difficulty (1-5)
- Regression / progression variants
- Form cues
- Contraindications (safety)

## Movement patterns

`horizontal_push`, `vertical_push`, `horizontal_pull`, `vertical_pull`,
`squat`, `hinge`, `hamstring`, `isolation`, `core`, `carry`, `cardio`.

## Environment → equipment mapping

| Environment | Equipment available |
|---|---|
| `home_bodyweight` | (none — bodyweight only) |
| `home_gym` | dumbbells, bands, bench, pullup_bar, kettlebells |
| `gym_full` | barbell, bench, dumbbells, machine, cardio_machine, kettlebells, pullup_bar, trap_bar |

## Equipment filtering (hard filter)

`pick_exercise()` enforces:
- Pattern match
- Difficulty ≤ max
- **Required equipment is a subset of available** (never silently relaxed)
- Not in exclude set

If no feasible candidate exists, the `ExerciseRule.substitute_map` is
consulted before giving up.

## A/B session variation

Consecutive sessions with the same structure use a `variant` parameter
to select alternate exercises, preventing identical day-to-day plans.

3-day split: A/B/A. 4-day: Upper-A/Lower-A/Upper-B/Lower-B. 5-6 day:
Push/Pull/Legs with B variants.
