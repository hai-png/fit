# 03 — Calculators

All numerical engines grounded in the RippedBody Nutrition Pyramid and
Muscle & Strength framework.

## Body composition

| Calculator | Method | Source |
|---|---|---|
| `bmi()` | BMI (kg/m²) | WHO 1995 |
| `body_fat_navy()` | U.S. Navy tape (metric) | Hodgdon & Beckett 1984 |
| `body_fat_bmi_method()` | Deurenberg (BMI→BF%) | Deurenberg 1991 |
| `body_fat_from_visual()` | 7-band visual estimation | [rippedbody.com/body-fat-guide](https://rippedbody.com/body-fat-guide/) |
| `correct_bf_estimate()` | +50% for self-estimates | RippedBody |
| `muscular_potential()` | Berkhan model + FFMI | [maximum-muscular-potential](https://rippedbody.com/maximum-muscular-potential/) |

**Visual BF bands:**

| Label | BF% range | Midpoint |
|---|---|---|
| shredded | 6-9% | 8.0 |
| very_lean | 10-12% | 11.0 |
| lean | 13-15% | 14.0 |
| average_fit | 16-19% | 17.5 |
| soft | 20-24% | 22.0 |
| overweight | 25-29% | 27.0 |
| obese | 30-40% | 33.0 |

**Priority:** user_input → Navy → visual → Deurenberg.

## Energy expenditure

Source: [rippedbody.com/calories](https://rippedbody.com/calories/)

**BMR:** Harris-Benedict (metric).

**TDEE multipliers (4-tier):**

| Activity | Multiplier |
|---|---|
| Sedentary | ×1.15 |
| Mostly sedentary + lifting | ×1.35 |
| Lightly active + lifting | ×1.55 |
| Highly active + lifting | ×1.75 |

**Calorie target by goal:**

| Goal | Formula | Notes |
|---|---|---|
| Fat loss (cut) | TDEE − (BW × 0.0075 × 1100) | 0.75%/wk; accounts for metabolic adaptation |
| Muscle gain (bulk) | TDEE + (BW × rate × 330 × 1.5) | Rate tiered by experience; 50% NEAT buffer |
| Recomp | TDEE | Maintenance |
| Strength | TDEE × 1.02 | Slight surplus |

**Bulk monthly gain rates:** Beginner 2%, Intermediate 1%, Advanced 0.5%.

**Safety floor:** 1200 kcal minimum.

## Macronutrient partitioning

Source: [rippedbody.com/macros](https://rippedbody.com/macros/),
[best-macro-ratio](https://rippedbody.com/best-macro-ratio/)

| Macro | Rule | Source |
|---|---|---|
| Protein | BF% known: 2.5 g/kg lean (cut), 2.2 g/kg (bulk). BF% unknown: 2.2 g/kg target BW (cut), 1.6 g/kg (bulk). **Vegan: +0.1-0.6 g/kg** | RippedBody + [vegan advice](https://rippedbody.com/advice-for-vegans/) |
| Fat | 15-25% (cutting), 20-30% (bulking). Min 0.5 g/kg. Somatotype-adjusted. | RippedBody |
| Carbs | Remainder of calorie budget. Min 1 g/kg. | RippedBody |

## Micronutrients

Source: [rippedbody.com/micros](https://rippedbody.com/micros/)

| Calories | Fruit (cups) | Veg (cups) | Fibre |
|---|---|---|---|
| 1200-2000 | 2 | 2 | 14g/1000kcal |
| 2000-3000 | 3 | 3 | 14g/1000kcal |
| 3000-4000 | 4 | 4 | 14g/1000kcal |

## Hydration

35 ml/kg base + 350 ml per 30 min workout.
Also: 5 clear urinations/day, clear by noon.

## Strength estimation

1RM via Epley, Brzycki, Lander (clamped to ≤12 reps).

## Cardio zones

Karvonen method (Tanaka HRmax), 5 zones (Z1-Z5).
