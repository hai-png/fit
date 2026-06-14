# 04 — Questionnaires

Six intake forms, each a list of `Question` objects that can be
presented to clients sequentially, scored algorithmically, and
persisted to JSON.

```
PAR_Q → HEALTH_HISTORY → LIFESTYLE → DIETARY → FITNESS_HISTORY → GOALS
```

## 4.1 PAR-Q+ (Physical Activity Readiness Questionnaire)

The standard 7-question screening tool endorsed by the ACSM. Any
"yes" raises a flag — **recommend physician clearance** before
vigorous training.

| Q | Prompt |
|---|---|
| 1 | Has your doctor ever said you have a heart condition…? |
| 2 | Do you feel pain in your chest when you do physical activity? |
| 3 | In the past month, have you had chest pain when not doing physical activity? |
| 4 | Do you lose your balance because of dizziness? |
| 5 | Do you have a bone or joint problem that could be made worse by a change in your physical activity? |
| 6 | Is your doctor currently prescribing drugs for your blood pressure or heart condition? |
| 7 | Do you know of any other reason why you should not do physical activity? |

```python
from fitness_engine import PAR_Q, parq_score
answers = {f"parq_{i}": "no" for i in range(1, 8)}
score = parq_score(answers)         # 0.0
# score >= 4 → flag for physician clearance
```

Each "yes" carries a severity weight (1.5–4.0). Heart-related
items (1-3) are weighted higher than joint or balance items.

## 4.2 Health history

| Field | Type | Notes |
|---|---|---|
| Age | int | 14-100 |
| Biological sex | single | Male / Female |
| Height | float | cm |
| Weight | float | kg |
| Diagnosed conditions | multi | 14 options |
| Medications | text | Free text, "none" if N/A |
| Injuries | text | Free text |
| Family history | text | Cardiac < 55y, diabetes, etc. |

Condition options:
```
none, t2_diabetes, pre_diabetes, hypertension,
high_cholesterol, pcos, hypothyroidism,
joint_knee, joint_shoulder, lower_back,
cardio_limited, celiac, ibs, pregnancy, postpartum
```

## 4.3 Lifestyle

| Field | Type | Range |
|---|---|---|
| Sleep hours | float | 0–14 |
| Sleep quality | single | poor / fair / good / excellent |
| Stress | int | 1 (calm) – 10 (overwhelmed) |
| Work type | single | desk / mixed / active / physical |
| Travel frequency | single | rare / monthly / weekly |
| Smoking | single | never / former / occasional / daily |
| Alcohol | single | none / moderate / regular / heavy |

Sleep and stress automatically bias the training prescription:
* Sleep < 6 h → warn + refer to sleep hygiene module
* Stress ≥ 8 → emphasise Zone-2 cardio, lower intensity cap

## 4.4 Dietary preferences

| Field | Type | Options |
|---|---|---|
| Diet pattern | single | omnivore / pescatarian / pollo_pescatarian / vegetarian / vegan / keto / mediterranean / low_fodmap / halal / kosher / flexible |
| Allergies / intolerances | multi | dairy / gluten / nuts / peanuts / soy / eggs / shellfish / fish |
| Dislikes | text | Free text — "liver, olives" |
| Meals per day | single | 3 / 4 / 5 / OMAD |
| Cooking skill | single | basic / intermediate / advanced |
| Preferred cuisines | multi | american / mediterranean / asian / indian / mexican / middle_eastern / african / nordic |

Cuisine preferences feed `cuisine_pick()` in the decision tree.

## 4.5 Fitness history

| Field | Type | Range |
|---|---|---|
| Experience | single | novice / beginner / intermediate / advanced / elite |
| Environment | single | home_bodyweight / home_minimal / home_full / gym_commercial / gym_full / hybrid / outdoor |
| Equipment | multi | barbell / dumbbells / kettlebells / bands / machine / cardio_machine / box / pullup_bar |
| Days per week | int | 1–7 |
| Session length | single | express_30 / short_45 / standard_60 / extended_90 |
| Cardio preference | single | walking / running / cycling / rowing / swimming / mixed |
| Current lifts | text | Free text — "squat 100kg x5, bench 80kg x5" |

Equipment filter is the **primary driver** of which exercises the
recommender can suggest. Missing equipment automatically triggers
substitutions via the exercise-selection decision tree.

## 4.6 Goals & motivation

| Field | Type | Notes |
|---|---|---|
| Primary goal | single | fat_loss / muscle_gain / recomposition / strength / endurance / general_health / athletic_performance / rehabilitation |
| Secondary goals | multi | Same options as primary |
| Target weight | float | Optional, kg |
| Timeline | int | 4–104 weeks |
| Motivation driver | single | health_event / appearance / performance / longevity / mental_health / life_event |
| Past attempts | text | Free text |
| Support system | single | solo / partner / trainer / group |

Timeline × goal combinations are sanity-checked by the recommender:
* < 8 weeks + muscle_gain → note about realistic rate of gain
* > 52 weeks + fat_loss → suggest intermediate check-ins

## 4.7 Intake report

```python
from fitness_engine import intake_report, IntakeReport
report = intake_report({
    "parq_1": "no", "parq_2": "no", ...,
    "ls_sleep_hours": 7.5,
    "ls_stress": 4,
    "hh_conditions": ["t2_diabetes"],
})
report.parq_score          # 0.0
report.parq_clear          # True
report.warnings            # []
report.notes               # ["Type 2 diabetes — schedule training post-meal ..."]
```

`intake_report()` runs cross-cutting checks:

| Trigger | Action |
|---|---|
| PAR-Q score ≥ 4 | Add physician-clearance warning |
| Sleep < 6 h | Add sleep-hygiene warning |
| Stress ≥ 8 | Note: bias to lower-intensity work |
| Pregnancy | Warning: avoid supine / Valsalva / impact |
| Postpartum | Note: pelvic-floor screen recommended |
| T2 diabetes | Note: schedule post-meal training |
| Hypertension | Note: sub-maximal loads, no Valsalva |
| Lower-back issue | Note: limit axial loading without physio clearance |
| Knee issue | Note: substitute knee-dominant patterns |
| Shoulder issue | Note: substitute overhead patterns |

## 4.8 Intake data flow

```
ClientProfile.parq_answers ──┐
                              ├──► intake_report() ──► IntakeReport
ClientProfile.health_conditions ──┤                   - parq_score
ClientProfile.sleep_hours ──────┤                    - parq_clear
ClientProfile.stress_level ─────┘                    - warnings
                                                       - notes
                                                          │
                                                          ▼
                                          Annotations appear on every plan
```

## 4.9 Extending questionnaires

To add a new question:

```python
from fitness_engine.questionnaires import Question, QuestionType, Choice

HEALTH_HISTORY.append(Question(
    id="hh_smoking_status",
    prompt="Do you currently smoke?",
    qtype=QuestionType.SINGLE,
    choices=[Choice("yes", "Yes"), Choice("no", "No")],
))
```

Then update `intake_report()` with any cross-cutting logic that
depends on the new question.

## 4.10 Validation rules

| Rule | Source |
|---|---|
| PAR-Q score ≥ 4 → physician clearance | ACSM |
| Sleep < 6 h impairs recovery | Multiple sleep & performance studies |
| Hypertension + heavy Valsalva = risk | AHA position stand |
| Postpartum + heavy core work = pelvic-floor risk | Pelvic-health PT consensus |
| Pregnancy + supine position = aortocaval compression | ACOG |
