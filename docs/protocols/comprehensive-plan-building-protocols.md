# Comprehensive Exercise and Meal Plan Building Protocols

This document explains the protocol layer in `fitness_engine/protocols.py`. The engine does **not** need a hand-authored plan for every one of the 233,280 enumerated archetype signatures. Instead, every profile is covered by deterministic protocol rules that combine:

- goal
- experience
- age/sex
- activity
- diet mode
- training environment
- training days/week
- session length
- calorie/macro target
- meal frequency and cuisine/allergen preferences

For the full evidence-based rationale behind each formula and threshold, see `docs/reference/unified-fitness-reference-guide.md`.

## Exercise plan protocol

### 1. Adherence first

The profile's realistic training days and session length come before theoretical optimization.

| Days/week | Default split |
|---:|---|
| 1 | Full Body (single session) |
| 2 | Full Body A/B |
| 3 | Full Body A/B/C (three distinct variants) |
| 4 | Upper / Lower |
| 5 | Push / Pull / Legs A / Upper / Legs B |
| 6+ | Push / Pull / Legs × 2 |

Advanced trainees receive notes that two days/week is mainly maintenance unless sessions are long and recovery is excellent.

### 2. Volume, intensity, frequency

The protocol sets weekly sets per muscle group from goal + experience:

- fat loss: reduced volume, preserve intensity
- muscle gain/recomp: hypertrophy range
- strength: more main-lift focus
- general health: moderate repeatable volume

It also enforces per-session caps so plans do not exceed the guide's practical limit of roughly 11 sets per muscle per session.

### 3. Rep ranges and RIR

| Goal | Primary lifts | Accessories | RIR logic |
|---|---|---|---|
| Strength | 3-6 reps | 6-10 reps | usually 2 RIR; beginners 3+ |
| Fat loss | 6-12 reps | 10-15 reps | preserve load, trim volume first |
| Muscle gain | 6-12 reps | 8-15 reps | 1-3 RIR depending exercise |
| Recomp/general | 8-12 reps | 10-15 reps | sustainable effort |

### 4. Progression

| Experience | Progression protocol |
|---|---|
| Beginner | Linear progression: add reps/load frequently; deload if stalls accumulate |
| Intermediate | Double progression: reach top of rep range across sets, then add load |
| Advanced | Periodized / auto-regulated: wave loading, readiness-based adjustments, planned deloads |

### 5. Exercise selection

Every plan covers movement patterns in priority order according to goal:

- squat / knee-dominant
- hinge / hip-dominant
- horizontal push
- vertical push
- horizontal pull
- vertical pull
- single-leg or unilateral work
- carry/core
- isolation as needed

Equipment is a hard filter:

- `home_bodyweight`: only bodyweight-compatible exercises
- `home_gym`: dumbbells, bands, bench, pull-up bar, kettlebells
- `gym_full`: barbell, bench, dumbbells, machines, trap bar, pull-up bar, cardio machines

### 6. Conditioning/cardio

- Fat loss: start with modest Zone-2 cardio and cap it at less than half weekly lifting time.
- Muscle gain/strength: optional easy cardio only; do not compromise progressive overload.
- General health: 90-150 min/week easy-to-moderate aerobic work if recovery allows.

### 7. Special modifiers

- Age 46+: longer warm-ups, slower load jumps, joint-friendly variation, conservative RIR.
- Female clients: scale trends should account for menstrual-cycle water changes where applicable.
- Cuts: maintain load/intensity and reduce volume before letting effort quality collapse.

## Meal plan protocol

### 1. Nutrition hierarchy

1. Calories
2. Protein and macros
3. Micronutrients/fiber/hydration
4. Timing
5. Supplements

### 2. Calories

- Uses Mifflin-St Jeor default BMR.
- Uses guide-aligned activity multipliers.
- Uses body-fat-aware cutting rates.
- Applies Alpert maximum deficit when body-fat data is available.
- Uses experience-tiered bulk rates.
- Enforces sex-specific calorie floors.
- Supports adaptive TDEE when enough log data exists.

### 3. Macros

- Protein is set first by lean mass/body weight and goal.
- Fat floor is preserved.
- Carbs fill the remainder unless diet mode constrains them.
- No somatotype macro tweaking.
- Macro adjustments preserve protein and change carbs/fats at a practical 1:1 to 2:1 calorie split.
- Optional macro cycling keeps weekly calories matched and shifts mostly carbs to training days.

### 4. Diet modes supported

The engine now supports:

- balanced
- omnivore
- vegan
- vegetarian
- pescatarian
- pollo-pescatarian
- keto
- low-carb
- Mediterranean
- paleo
- gluten-free
- high-protein

Keto and low-carb are treated as preference/tolerance modes, not as superior fat-loss mechanisms when calories and protein are equated.

### 5. Meal assembly

The meal builder:

1. filters by diet compatibility and allergens
2. filters by preferred cuisine if possible
3. allocates calories by meal slot
4. chooses meals closest to slot targets
5. portion-scales the day to hit target calories
6. falls back to compatible meals when cuisine-specific choices are insufficient

All diet modes are tested to assemble a day plan within ±5% of target calories.

### 6. Micronutrients and hydration

- Fruit and vegetables scale by calorie intake.
- Fiber target: 14 g / 1000 kcal.
- Hydration guidance follows practical urine/workout rules.
- Supplements are last, with vegan-specific essentials flagged.

### 7. Adjustments

Fat-loss stalls:

1. check tracking
2. manage hunger
3. fix food environment
4. revisit motivation
5. address stress
6. fix sleep
7. maintain steps/NEAT
8. wait for enough trend data
9. add cardio sparingly
10. reduce calories last

Bulk stalls:

1. check tracking
2. manage fullness
3. improve food environment
4. revisit motivation
5. address stress
6. fix sleep
7. account for NEAT increases
8. wait about 5 weeks
9. increase calories last

Post-cut transitions use the reverse-diet protocol: +50 / +100 / +150 kcal per week depending on diet length and regain risk.

## Coverage guarantee

The integration suite now includes:

```bash
python3 -m unittest tests.test_calculators tests.test_integration
# Ran 80 tests — OK
```

Coverage includes:

- every enumerated archetype signature at the protocol-builder level
- every diet mode at the meal-builder level
- end-to-end curated profile recommendations
- equipment hard-filter checks
- calorie/macro calculator regression tests

## 7-day meal-plan creation system

A dedicated weekly planner has been added in `fitness_engine/seven_day_meal_planner.py`.

It uses the clean unified external recipe database at `data/recipes/unified_external_recipes.json`, then generates seven daily plans using the same calorie/macro/micronutrient protocol described above. Internal curated meals are excluded by default for the 7-day planner.

Key API:

```python
from fitness_engine import assemble_7_day_meal_plan

week = assemble_7_day_meal_plan(
    diet=profile.dietary_preference,
    target_calories=rec.energy.calorie_target,
    target_macros=rec.nutrition.macros,
    meals_per_day=profile.meals_per_day,
    allergens=profile.allergies,
    preferred_cuisines=profile.preferred_cuisines,
    include_external=True,
)
```

The recommender now exposes this automatically:

```python
rec.nutrition.weekly_meal_plan
```

The weekly planner hard-filters by diet and allergens, soft-scores cuisine preference, rotates meals to reduce repeats, adds a protein booster if the day is too low in protein density, portion-scales each day to the calorie target, and returns daily quality diagnostics plus a shopping list.
