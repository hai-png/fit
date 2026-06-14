# 07 — Exercise Plans Library

## 7.1 Data model

```python
@dataclass
class Exercise:
    name: str
    pattern: str              # horizontal_push, vertical_pull, hinge, ...
    primary_muscle: str
    secondary_muscles: List[str]
    equipment: List[str]
    difficulty: int           # 1 (easy) – 5 (hard)
    regression: Optional[str]    # name of easier variant
    progression: Optional[str]    # name of harder variant
    cues: List[str]               # form cues
    contraindications: List[str]  # health conditions to flag
    tags: List[str]
```

## 7.2 Movement patterns

The library is organised around eight movement patterns:

| Pattern | Examples |
|---|---|
| **horizontal_push** | Bench press, push-up, dumbbell bench, incline press |
| **vertical_push** | Overhead press, dumbbell press, pike push-up |
| **horizontal_pull** | Bent-over row, dumbbell row, machine row |
| **vertical_pull** | Pull-up, band pull-up, lat pulldown |
| **hinge** | Deadlift, RDL, kettlebell swing, hip thrust |
| **squat** | Back squat, goblet squat, leg press, split squat |
| **hamstring** | Lying leg curl, Nordic curl |
| **isolation** | Barbell curl, lateral raise, triceps pushdown |
| **core** | Plank, Pallof press |
| **carry** | Farmer carry |
| **cardio** | Zone-2 walk, intervals, rower |

Every session ensures **at least one push, one pull, one leg, one
hinge, and one core/carry** movement.

## 7.3 Difficulty rating

`difficulty` is an integer 1–5 that captures the technical demand
of an exercise:

| Difficulty | Examples |
|---|---|
| 1 | Bodyweight squat, plank, farmer carry |
| 2 | Goblet squat, dumbbell RDL, push-up, dumbbell bench |
| 3 | Back squat, conventional deadlift, barbell row |
| 4 | Front squat, deficit deadlift, weighted pull-up |
| 5 | Handstand push-up, snatch, clean & jerk |

The recommender uses `difficulty_max` (default 4) to filter the
library when selecting exercises.

## 7.4 Regressions & progressions

Each compound lift has a chain:

```
bodyweight_squat → goblet_squat → back_squat → front_squat
push_up → incline_push_up → diamond_push_up → archer_push_up
band_pullup → pullup → weighted_pullup
bodyweight_rdl → dumbbell_rdl → barbell_rdl → deficit_rdl
```

Clients move **down the chain** when regressing (injury, deload,
intensity cap) and **up the chain** when progressing (PR, milestone).

The recommender currently uses `difficulty` directly; future
versions could surface explicit chains.

## 7.5 Equipment filter

`pick_exercise()` filters by equipment:

1. Find all exercises for the pattern with `difficulty ≤ max`.
2. Keep those whose `equipment` is a subset of available equipment.
3. Sort by `(-difficulty, len(equipment))` — pick the **hardest**
   exercise the equipment supports.

This means:
* Full gym → barbell compounds
* Home + dumbbells → dumbbell variants
* Bodyweight only → bodyweight patterns

If no exercise in the pattern matches, the equipment filter is
dropped (still respecting difficulty cap).

## 7.6 Weekly split builder

`weekly_split()` produces a per-day list of exercises. The split
depends on `days_per_week`:

| Days | Split |
|---|---|
| 1–3 | Full body (Mon / Wed / Fri) |
| 4 | Upper / Lower (Mon / Tue / Thu / Fri) |
| 5 | Push / Pull / Legs (Mon–Fri) |
| 6 | Push / Pull / Legs x2 (Mon–Sat) |

Each session contains 4–7 exercises covering all major patterns,
with no duplicates within a session.

## 7.7 Periodisation presets

The recommender picks one of:

| Profile | Scheme |
|---|---|
| Novice / Beginner | Linear Progression — add reps/session, add load when top of rep range |
| Strength goal | 5/3/1 (Wendler) — 3-week wave + deload |
| Muscle gain goal | Daily Undulating Periodisation (DUP) — rep target rotates day-to-day |
| Endurance goal | Block Periodisation — base / build / peak |
| Default | Linear with RPE cap — load +2.5 kg when RPE < cap |

Deload is hard-coded every 4–6 weeks depending on scheme.

## 7.8 Progression rules

| Profile | Rule |
|---|---|
| Novice/Beginner | Add reps/session; add load when top of rep range; reset after 3 stalls |
| Strength | Top-set + back-off volume; chase rep PRs |
| Hypertension | Rep-range progression only; never above RPE 7 |
| Default | Double-progression — hit top of rep range, then add load |

## 7.9 Intensity scheme

Per-exercise intensity is set by the recommender based on the
pattern:

* **Compound** (squat, hinge, push, pull) → primary rep range + RPE
* **Isolation** → accessory rep range + RPE

Example (fat-loss, beginner):
* Primary: 10–15 @ RPE 7.5
* Accessory: 12–20 @ RPE 8.0

Example (strength, intermediate):
* Primary: 3–6 @ RPE 8.5
* Accessory: 6–10 @ RPE 8.0

## 7.10 Warm-up & cool-down

**Warm-up** (every session):
1. 5 min easy cardio (bike / walk / row)
2. Dynamic mobility: hip openers, thoracic rotations, ankle circles
3. Activation: 2×15 band pull-aparts, 2×10 glute bridges
4. Specific warm-up: 2 sets of the first compound at 50 % then 70 %

**Cool-down** (every session):
1. 5 min walking / slow cycling
2. Static stretches, 30 s each: hip flexors, hamstrings, thoracic, pecs, lats
3. Box breathing 4-4-4-4 for 2 min

## 7.11 Cardio prescription

Output:
```python
{
    "weekly_cardio_minutes": "132",
    "modality": "mixed (rower / bike / walk / jog)",
    "zone_2": "20 min per session, 4 sessions/week",
    "hiit": "53 min total weekly (2-3 sessions, 20-30 min each)",
    "step_target": "8-10k steps/day outside sessions"
}
```

Cardio-limited clients get **walking only** as modality.

## 7.12 Heart-rate zones (Karvonen)

Using Tanaka HR_max and client resting HR:

| Zone | % HRR | Purpose |
|---|---|---|
| Z1 recovery | 0.50–0.60 | Active recovery |
| Z2 aerobic base | 0.60–0.70 | Fat oxidation, mitochondrial density |
| Z3 tempo | 0.70–0.80 | Aerobic power |
| Z4 threshold | 0.80–0.90 | Lactate threshold |
| Z5 VO2max | 0.90–1.00 | Peak power, intervals |

Sample (34 y, resting HR 62):
* HR_max (Tanaka) = 208 − 0.7 × 34 = 184
* HRR = 184 − 62 = 122
* Z2 = 62 + 122 × [0.60, 0.70] = [135, 148] bpm

## 7.13 Adding a new exercise

```python
from fitness_engine.exercise_plans import Exercise, EXERCISE_LIBRARY

EXERCISE_LIBRARY["zombie_squat"] = Exercise(
    name="Zombie squat",
    pattern="squat",
    primary_muscle="quads",
    secondary_muscles=["glutes", "core"],
    equipment=["bodyweight"],
    difficulty=2,
    regression="bodyweight_squat",
    progression="goblet_squat",
    cues=["Arms extended forward", "Sit back", "Knees track toes"],
)
```

The recommender will consider it the next time it builds a
squat-pattern session.

## 7.14 Library size & coverage

| Pattern | # Exercises |
|---|---|
| horizontal_push | 5 |
| vertical_push | 3 |
| horizontal_pull | 3 |
| vertical_pull | 3 |
| hinge | 5 |
| squat | 7 |
| hamstring | 1 |
| isolation | 4 |
| core | 3 |
| carry | 1 |
| cardio | 3 |
| **Total** | **38** |

Every muscle group has at least 3 exercise options across the
regression-progression chain.

## 7.15 Future extensions

* Explicit regression-progression chains surfaced in output
* Exercise video / GIF URLs
* Substitute-on-injury chains with full ROM comparison
* Auto-deload detection from RPE history
* 1RM-tracked progression calculator
