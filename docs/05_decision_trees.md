# 05 — Decision Trees

Each tree is a small named function that maps one or two inputs
into a structured output. They are pure, auditable, and easily
overridden. The order of evaluation matters; this document
explains the trees in execution order.

## 5.1 Training split

**Inputs**: `goal`, `experience`, `health_conditions`
**Output**: `TrainingSplit(strength_pct, hypertrophy_pct, cardio_pct, mobility_pct)`

Base splits by goal:

| Goal | Strength | Hypertrophy | Cardio | Mobility |
|---|---|---|---|---|
| Fat loss | 0.20 | 0.40 | 0.35 | 0.05 |
| Muscle gain | 0.40 | 0.45 | 0.10 | 0.05 |
| Recomposition | 0.35 | 0.45 | 0.15 | 0.05 |
| Strength | 0.70 | 0.20 | 0.05 | 0.05 |
| Endurance | 0.15 | 0.15 | 0.65 | 0.05 |
| Athletic | 0.40 | 0.25 | 0.30 | 0.05 |
| General health | 0.25 | 0.30 | 0.35 | 0.10 |
| Rehabilitation | 0.20 | 0.30 | 0.20 | 0.30 |

**Modifiers**:
* Beginner/novice → +5 % cardio (lower CNS stress)
* Cardio-limited → cardio −20 %, hypertrophy +15 %
* Knee issue → strength −10 %, mobility +5 %

After modifications, the four values are **renormalised to 1.0**.

## 5.2 Weekly volume

**Inputs**: `goal`, `experience`, `days_per_week`, `age_group`
**Output**: `WeeklyVolume(total_sets, per_muscle_group, rationale)`

Base sets per muscle group per week:

| Goal | Sets/group |
|---|---|---|
| Fat loss | 10 |
| Muscle gain | 14 |
| Recomposition | 12 |
| Strength | 8 |
| Endurance | 5 |
| Athletic | 10 |
| General health | 7 |
| Rehabilitation | 5 |

Experience factor:
* Novice 0.60 × Beginner 0.80 × Intermediate 1.00 × Advanced 1.15 × Elite 1.25

Age factor (older clients need less volume per session):
* Youth 1.00 × Young adult 1.05 × Adult 1.00 × Middle 0.95 × Senior 0.85 × Elder 0.75

Distribution across groups:
* 7 major groups (chest, back, shoulders, quads, hams, glutes) get full sets
* Calves get max(4, sets−4)
* Arms get max(6, sets−4)
* Core is fixed at 6 sets/wk

## 5.3 Intensity scheme

**Inputs**: `goal`, `experience`, `health_conditions`
**Output**: `IntensityScheme(primary_reps, primary_rpe, accessory_reps, accessory_rpe)`

Base rep ranges and RPE caps:

| Goal | Primary | RPE | Accessory | RPE |
|---|---|---|---|---|
| Fat loss | 10–15 | 7.5 | 12–20 | 8.0 |
| Muscle gain | 6–12 | 8.0 | 10–15 | 8.5 |
| Recomposition | 6–12 | 8.0 | 10–15 | 8.0 |
| Strength | 3–6 | 8.5 | 6–10 | 8.0 |
| Endurance | 12–20 | 7.0 | 15–25 | 7.5 |
| Athletic | 4–8 | 8.0 | 8–12 | 8.0 |
| General health | 8–12 | 7.5 | 10–15 | 7.5 |
| Rehabilitation | 8–12 | 6.5 | 10–15 | 7.0 |

Novices capped at RPE 7.0 / 7.5. Hypertension capped at RPE 7.0 / 7.5.

## 5.4 Exercise selection

**Inputs**: `goal`, `environment`, `equipment`, `health`, `age_group`
**Output**: `ExerciseRule(include, exclude, substitute_map)`

Starts with universal movement patterns:
```
horizontal_push, vertical_pull, hinge, squat, carry, core
```

Then adds goal-specific patterns:
* Strength / Athletic → barbell compounds
* Muscle gain / Recomp → accessories
* Fat loss / Health → circuits + swings
* Endurance / Athletic → intervals

**Environment substitutions**:
* Home bodyweight only → swap barbell for bodyweight
* Home minimal → swap barbell for dumbbell variants
* Missing equipment → trigger substitute map

**Health substitutions**:
* Knee issue → box squat, leg press, split squat
* Shoulder issue → landmine press, neutral grip
* Lower back → trap bar DL, light RDL
* Cardio-limited → walk only
* Pregnancy → no supine / Valsalva / impact
* Postpartum → pelvic-floor first

## 5.5 Periodisation

**Inputs**: `goal`, `experience`
**Output**: `Periodisation(scheme, cycle_weeks, deload_every, description)`

| Experience | Goal | Scheme | Cycle | Deload |
|---|---|---|---|---|
| Novice/Beginner | any | Linear Progression | 8w | every 4w |
| any | Strength | 5/3/1 (Wendler) | 4w | every 4w |
| any | Muscle gain | DUP | 6w | every 6w |
| any | Endurance | Block | 12w | every 4w |
| any | other | Linear with RPE cap | 6w | every 6w |

## 5.6 Session density

**Inputs**: `goal`, `session_length`
**Output**: `SessionDensity(work_seconds, rest_seconds, density)`

Base work:rest by goal:

| Goal | Work (s) | Rest (s) |
|---|---|---|
| Fat loss | 30 | 15 |
| Muscle gain | 45 | 90 |
| Recomposition | 45 | 75 |
| Strength | 60 | 180 |
| Endurance | 180 | 60 |
| Athletic | 45 | 90 |
| General health | 40 | 60 |
| Rehabilitation | 30 | 60 |

Session-length modifiers:
* Express (30 min) → rest −30 s, supersets recommended
* Short (45 min) → rest −15 s
* Extended (90 min) → rest +30 s

## 5.7 Progression rule

**Inputs**: `goal`, `experience`, `health`
**Output**: `ProgressionRule(primary, accessory, rule)`

| Profile | Primary progression |
|---|---|
| Novice / Beginner | Add reps each session; add load when top of rep range |
| Strength | Wave-load: 3×5 → 3×3 → 1×5, deload |
| Hypertension | Slow RPE climb, never above 7 |
| Default | Double-progression: hit top of rep range, then add load |

## 5.8 Macro overrides

**Inputs**: `health_conditions`
**Output**: `dict[str, str]` of override notes

| Condition | Override |
|---|---|
| T2 diabetes / pre-diabetes | Carbs moderate low-GI; fibre 30-40 g; meal frequency 3+1 |
| Hypertension | Sodium < 2300 mg; potassium 3500+ mg |
| High cholesterol | Saturated fat < 7 % kcal; fibre ≥ 30 g |
| PCOS | Protein ≥ 1.8 g/kg; low-GI, anti-inflammatory |
| IBS / Celiac | Low-FODMAP / GF substitutions |
| Pregnancy | Folate ≥ 600 mcg; iron 27 mg with vit C |
| Postpartum | Protein ≥ 1.8 g/kg; omega-3 ≥ 250 mg |

## 5.9 Cuisine pick

**Inputs**: `preferred_cuisines`, `dietary_preference`
**Output**: `list[str]` of 2–3 cuisines

Algorithm:
1. If no preferences, default by diet (Mediterranean → "mediterranean"; Keto → "mediterranean", "american"; else → "american", "mediterranean").
2. Otherwise, return the user's selections, intersected with diet-compatible cuisines (e.g. vegan + american works fine).
3. Cap at 3 cuisines for variety.

## 5.10 Supplement stack

**Inputs**: `goal`, `sex`, `health_conditions`
**Output**: `SupplementStack(foundational, goal_specific, conditional)`

| Layer | Examples |
|---|---|
| **Foundational** | Vitamin D, Omega-3, Magnesium, Protein powder |
| **Goal-specific** | Creatine (strength/muscle), Na-bicarb (endurance) |
| **Conditional** | Berberine (T2 diabetes), K-citrate (hypertension) |

Female clients get iron as foundational (pre-menopausal).

Joint issues (knee, lower back) get collagen peptides.

## 5.11 Cardio prescription

Built dynamically from `training_split.cardio_pct`:

```
weekly_minutes = 180 × cardio_pct + 60   # floor
```

Zone-2 vs HIIT proportion by goal:

| Goal | Zone-2 % | HIIT % |
|---|---|---|
| Fat loss | 60 | 40 |
| Muscle gain | 50 | 50 |
| Recomposition | 60 | 40 |
| Strength | 50 | 50 |
| Endurance | 30 | 70 |
| Athletic | 40 | 60 |
| General health | 70 | 30 |
| Rehabilitation | 80 | 20 |

Sessions spread across 2–4 days/week. Cardio-limited clients
default to walking only.

## 5.12 Putting it together — execution order

```python
# Inside Recommender.recommend():
sig            = _archetype_signature()
bc             = body_composition(...)                # 1. Calculator
ee             = energy_expenditure(...)              # 2. Calculator
m              = macros_for(...)                      # 3. Calculator
h              = hydration(...)                       # 4. Calculator

ts             = training_split(...)                  # 5. Decision tree
wv             = weekly_volume(...)                   # 6. Decision tree
ins            = intensity_scheme(...)                # 7. Decision tree
per            = periodisation(...)                   # 8. Decision tree
dty            = session_density(...)                 # 9. Decision tree
er             = exercise_selection(...)              # 10. Decision tree
prog           = progression_rule(...)                # 11. Decision tree
cz             = cardio_zones(...)                    # 12. Calculator
sched          = weekly_split(...)                    # 13. Protocol library

overrides      = macro_overrides(...)                 # 14. Decision tree
cuisines       = cuisine_pick(...)                    # 15. Decision tree
supps          = supplement_stack(...)                # 16. Decision tree

day_plan       = assemble_day(...)                    # 17. Protocol library
cardio_rx      = _cardio_prescription(...)            # 18. Custom
warmup         = _warmup_protocol()                   # 19. Custom
cooldown       = _cooldown_protocol()                 # 20. Custom

ir             = intake_report(...)                   # 21. Cross-cutting
```

## 5.13 Overriding a tree

To A/B test a different intensity scheme, for example, monkey-patch
in your own module:

```python
import fitness_engine.decision_trees as dt

def my_intensity_scheme(goal, experience, health):
    return dt.IntensityScheme(
        primary_reps="5-8", primary_rpe=8.0,
        accessory_reps="8-12", accessory_rpe=8.0,
        rationale="custom higher-intensity protocol"
    )

dt.intensity_scheme = my_intensity_scheme
```

The recommender will pick up your version automatically.

## 5.14 Decision-trace example

For a 34 y female, fat loss, beginner, sedentary, Mediterranean:

| Tree | Output |
|---|---|
| signature | `FAT-MESO-BEG-ADUL-F-SED-MEDI-GYM-60` |
| training_split | S 18 % / H 37 % / C 40 % / M 5 % |
| weekly_volume | 64 sets/wk (8 per major group) |
| intensity | primary 10–15 @ RPE 7.5 / acc 12–20 @ RPE 8.0 |
| periodisation | Linear Progression, 8 w cycle, deload every 4 w |
| density | work 30 s, rest 15 s (supersets) |
| exercise_rule | include 11 patterns, exclude 0, substitute 0 |
| progression | Linear, weekly; reset after 3 stalls |
| cardio | 132 min/wk, 4 Z2 sessions, 53 min HIIT |
| cuisine | mediterranean, asian |
| supplements | foundational (4 items), no goal-specific |
