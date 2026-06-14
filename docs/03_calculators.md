# 03 — Calculators Reference

All calculators are **pure functions** returning typed dataclasses.
They have no side effects and can be called independently of the
recommender. Every result is a structured object, so downstream
code can introspect, log, and unit-test individual computations.

## 3.1 Body composition

### BMI
```
BMI = weight_kg / (height_m)^2
```
```python
from fitness_engine import bmi, bmi_category
bmi(70, 175)               # 22.86
bmi_category(22.86)        # BMICategory.NORMAL → "normal"
bmi_category(31.9)         # "obese_class_i"
```

Categories (WHO):
| BMI | Category |
|---|---|
| < 18.5 | underweight |
| 18.5–24.9 | normal |
| 25–29.9 | overweight |
| 30–34.9 | obese_class_i |
| 35–39.9 | obese_class_ii |
| ≥ 40 | obese_class_iii |

### Body fat (Navy method)
```
Men:   BF = 495 / (1.0324 − 0.19077·log10(waist − neck) + 0.15456·log10(height)) − 450
Women: BF = 495 / (1.29579 − 0.35004·log10(waist + hip − neck) + 0.22100·log10(height)) − 450
```
Requires waist, neck, height (all cm); hip required for females.

### Body fat (Deurenberg BMI method)
```
BF = 1.20·BMI + 0.23·age − 10.8·(sex==male) − 5.4
```
Fallback when waist/neck measurements are unavailable.

### Composite
```python
from fitness_engine import body_composition
body_composition(weight_kg=72, height_cm=168, age=34,
                 sex=Sex.FEMALE, body_fat_pct=28,
                 waist_cm=78, neck_cm=32)
# Returns BodyComposition(bmi=25.51, bmi_category="overweight",
#   body_fat_pct=28.0, lean_mass_kg=51.84, fat_mass_kg=20.16)
```

## 3.2 Energy expenditure

### BMR — Mifflin-St Jeor (default)
```
Men:   10·kg + 6.25·cm − 5·age + 5
Women: 10·kg + 6.25·cm − 5·age − 161
```
Most accurate for modern, non-athlete populations.

### BMR — Revised Harris-Benedict
```
Men:   88.362 + 13.397·kg + 4.799·cm − 5.677·age
Women: 447.593 + 9.247·kg + 3.098·cm − 4.330·age
```
Provided for parity / comparison.

### BMR — Katch-McArdle
```
BMR = 370 + 21.6 · lean_mass_kg
```
Requires lean body mass — preferred for lean / athletic clients.

### TDEE
```
TDEE = BMR × activity_multiplier
```

| Activity | Multiplier |
|---|---|
| Sedentary | 1.200 |
| Light | 1.375 |
| Moderate | 1.550 |
| Very active | 1.725 |
| Athlete | 1.900 |

### Calorie target by goal

| Goal | Adjustment |
|---|---|
| Fat loss | −20% TDEE |
| Muscle gain | +12% TDEE |
| Recomposition | 0% |
| Strength | +5% TDEE |
| Endurance | +10% TDEE |
| Athletic | +12% TDEE |
| General health | 0% |
| Rehabilitation | +5% TDEE |

### Composite
```python
energy_expenditure(weight_kg=72, height_cm=168, age=34, sex=Sex.FEMALE,
                   activity=ActivityLevel.SEDENTARY,
                   goal=GoalArchetype.FAT_LOSS, lean_mass_kg=51.84)
```

## 3.3 Macronutrient partitioning

### Protein floor (g/kg body weight)

| Goal | g/kg |
|---|---|
| Fat loss | 2.0 |
| Muscle gain | 1.9 |
| Recomposition | 1.9 |
| Strength | 1.8 |
| Endurance | 1.6 |
| Athletic performance | 1.8 |
| General health | 1.4 |
| Rehabilitation | 1.6 |

### Fat floor (g/kg)
| Sex | g/kg |
|---|---|
| Male | 0.8 |
| Female | 0.9 |

### Somatotype modifier
* Ectomorph → bias toward more fat (~27% kcal)
* Endomorph → floor only
* Mesomorph → ~25% kcal

### Diet modifier
* **Keto** → fat at 70% kcal, carbs ≤ 50 g
* **Mediterranean** → fat ≥ 30% kcal
* Other → remainder after protein + fat floor

## 3.4 Hydration

```
base     = weight_kg × 35       # ml
bonus    = (workout_min/30) × 350  # ml
total    = base + bonus
```

A 70 kg client training 60 min/day needs 2,450 + 700 = **3,150 ml**.

## 3.5 One-rep-max estimates

| Method | Formula |
|---|---|
| Epley | `weight × (1 + reps/30)` |
| Brzycki | `weight × 36/(37 − reps)` |
| Lander | `100·weight/(101.3 − 2.67123·reps)` |

The composite returns all three plus the average and a percent-of-1RM
table at 50/60/65/70/75/80/85/90/95/100%.

```python
from fitness_engine import one_rep_max
r = one_rep_max(100, 5)
r.epley_1rm        # 116.7
r.brzycki_1rm      # 112.5
r.average_1rm      # 114.1
r.pct_of_1rm       # {'50%': 57.0, '60%': 68.5, ...}
```

## 3.6 Cardiovascular zones

Karvonen method using resting HR:

```
HRR = HR_max_Tanaka − resting_HR
Zone = resting_HR + HRR × pct
```

Tanaka HR_max is preferred over the simpler 220-age because it is
more accurate across ages:

```
HR_max_Tanaka = 208 − 0.7 × age
```

### Zones
| Zone | % HRR | Purpose |
|---|---|---|
| Z1 recovery | 0.50–0.60 | Active recovery |
| Z2 aerobic base | 0.60–0.70 | Fat oxidation, mitochondrial density |
| Z3 tempo | 0.70–0.80 | Aerobic power |
| Z4 threshold | 0.80–0.90 | Lactate threshold |
| Z5 VO2max | 0.90–1.00 | Peak power, intervals |

## 3.7 Somatotype inference

Coarse heuristic from BMI + body fat %:

```python
infer_somatotype(weight_kg=80, height_cm=180, age=30,
                 sex=Sex.MALE, body_fat_pct=18)
# Somatotype.MESOMORPH
```

For research-grade classification, use Heath-Carter
(out of scope for v1.0).

## 3.8 Age group inference

```python
infer_age_group(15)   # AgeGroup.YOUTH
infer_age_group(25)   # AgeGroup.YOUNG_ADULT
infer_age_group(35)   # AgeGroup.ADULT
infer_age_group(50)   # AgeGroup.MIDDLE
infer_age_group(65)   # AgeGroup.SENIOR
infer_age_group(80)   # AgeGroup.ELDER
```

## 3.9 Weekly tonnage

```python
weekly_tonnage([
    {"sets": 4, "reps": 6, "load_kg": 100},   # squats
    {"sets": 3, "reps": 8, "load_kg": 80},    # bench
])
# WeeklyTonnage(sets=7, reps=48, load_kg=89.17, total_volume_kg=26400)
```

Useful for tracking progressive overload over time.
