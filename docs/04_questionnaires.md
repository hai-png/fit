# 04 — Questionnaires

The intake is deliberately lean: **3 short forms** that capture only
the inputs that drive the plan. PAR-Q, health history, and lifestyle
forms have been removed in favour of **auto-generated recommendations**
derived from body composition and trainee category.

## 1. Diet & Preferences

| Question | Type | Notes |
|---|---|---|
| Dietary pattern | single | omnivore / vegan |
| Food allergies | multi (optional) | dairy, gluten, nuts, etc. |
| Foods you dislike | text (optional) | Free text |
| Traditional cuisine | single (optional) | Optional add, defaults to none |

**No cooking skill question.** Cuisine is optional/traditional only.

## 2. Fitness History

| Question | Type | Notes |
|---|---|---|
| Training experience | single | beginner / intermediate / advanced |
| Training environment | single | home_bodyweight / home_gym / gym_full |
| Days per week | int | 2-6 |
| Session length | single | 30 / 45 / 60 / 90 min |

**No equipment list** (derived from environment). **No cardio
preference or current lifts question.**

## 3. Goals

| Question | Type | Notes |
|---|---|---|
| Primary goal | single | fat_loss / muscle_gain / recomp / strength / general_health |
| Target weight | float (optional) | kg |
| Timeline | int | weeks |
| Motivation | single | health_event / appearance / performance / longevity / mental_health |

**No secondary goals, no past attempts, no support system question.**
Endurance, athletic performance, and rehabilitation are excluded from
goal choices.

## Auto-generated health recommendations

Instead of a screening questionnaire, the system generates targeted
advice from the client's actual data:

- Calorie-floor warnings (if target < 1200 kcal)
- BMI-based notes (underweight / obese range)
- Body-fat-based notes (higher fat → deficit + resistance training)
- Trainee-category-specific recommendations (pitfalls + action items)
- Universal daily habits (sleep, weight tracking, waist measurements,
  physician consult for conditions)
