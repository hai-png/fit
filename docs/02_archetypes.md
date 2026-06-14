# 02 — The Archetype System

## 2.1 What is an archetype?

An **archetype** is a deterministic label for a client that captures
all of the dimensions on which their plan should differ. We use
**nine orthogonal dimensions** so that the plan can be fully
differentiated by archetype combination alone.

## 2.2 The nine dimensions

| # | Dimension | Enum | Cardinality | Coded as |
|---|---|---|---|---|
| 1 | Goal | `GoalArchetype` | 8 | FAT / MUS / REC / STR / END / GEN / ATH / REH |
| 2 | Somatotype | `Somatotype` | 4 | ECTO / MESO / ENDO / MIXED |
| 3 | Experience | `ExperienceLevel` | 5 | NOV / BEG / INT / ADV / ELI |
| 4 | Age group | `AgeGroup` | 6 | YOU / YOUN / ADUL / MIDD / SENI / ELDE |
| 5 | Sex | `Sex` | 2 | M / F |
| 6 | Activity | `ActivityLevel` | 5 | SED / LIG / MOD / VER / ATH |
| 7 | Diet | `DietaryPreference` | 11 | OMNI / PESC / POLL / VEG / VGN / KETO / MEDI / FODM / HAL / KOS / FLEX |
| 8 | Environment | `TrainingEnvironment` | 7 | HOM_BW / HOM_MIN / HOM_FULL / GYM_C / GYM_F / HYB / OUT |
| 9 | Session length | `SessionLength` | 4 | 30 / 45 / 60 / 90 |

**Total combinatorial space**: 8 × 4 × 5 × 6 × 2 × 5 × 11 × 7 × 4
= **1,178,880** unique archetype signatures.

Not every combination is biologically sensible (e.g. elite + youth)
but every combination is **representable** — useful for QA, regression
testing, and exploring edge cases.

## 2.3 The archetype signature

```python
@dataclass(frozen=True)
class ArchetypeSignature:
    goal: GoalArchetype
    somatotype: Somatotype
    experience: ExperienceLevel
    age_group: AgeGroup
    sex: Sex
    activity: ActivityLevel
    diet: DietaryPreference
    environment: TrainingEnvironment
    session: SessionLength
```

`ArchetypeSignature.code()` produces a deterministic, human-readable
identifier — the **archetype code**. For example:

```
FAT-MESO-BEG-ADUL-F-SED-MEDI-GYM-60
│   │    │   │   │ │   │    │   │
│   │    │   │   │ │   │    │   └─ session length (minutes)
│   │    │   │   │ │   │    └───── environment
│   │    │   │   │ │   └────────── diet
│   │    │   │   │ └────────────── activity
│   │    │   │   └──────────────── sex
│   │    │   └──────────────────── age group
│   │    └──────────────────────── experience
│   └───────────────────────────── somatotype
└──────────────────────────────── goal
```

## 2.4 Enumeration helpers

```python
from fitness_engine import total_combinations, enumerate_signatures
print(total_combinations())                # 1178880
sigs = enumerate_signatures()              # all 1.18M signatures
```

Use these for:
* Regression testing
* QA dashboards
* Cohort analytics

## 2.5 Curated profiles

Twelve hand-curated archetypes capture the most common real-world
scenarios. Each is stored as an `ArchetypeProfile` with a nickname,
summary, strengths, risks, and emphasis points.

| Code | Nickname | Goal × Profile |
|---|---|---|
| `office_worker_fat_loss` | The Desk-Bound Reset | Fat loss · sedentary beginner |
| `ectomorph_lean_gain` | The Classic Hard Gainer | Muscle gain · ectomorph intermediate |
| `postpartum_recomp` | The Reclaiming Parent | Recomp · postpartum home setup |
| `senior_strength_health` | The Vital Retiree | Strength · 60+ novice |
| `diabetes_reversal` | The Metabolic Rebuild | Health · T2 diabetes |
| `athlete_endurance` | The Endurance Specialist | Endurance · advanced female |
| `vegan_athlete` | The Plant-Powered Performer | Athletic · vegan male |
| `keto_cruiser` | The Keto Cruiser | Health · ketogenic |
| `shift_worker` | The Shift-Worker | Health · rotating shifts |
| `back_pain_returner` | The Back-Pain Returner | Rehab · chronic LBP |
| `youth_athlete` | The Youth Athlete | Athletic · 16-year-old |
| `pcos_balancer` | The PCOS Balancer | Fat loss · PCOS |

```python
from fitness_engine import all_curated, get_curated
for ap in all_curated():
    print(ap.nickname, "->", ap.signature.code())
print(get_curated("diabetes_reversal").summary)
print(get_curated("keto_cruiser").emphasis)
```

## 2.6 How dimensions drive the plan

Each dimension influences specific decisions:

| Dimension | Drives |
|---|---|
| Goal | Calorie target, training split, volume, intensity, periodisation |
| Somatotype | Macro split (fat vs carbs), exercise selection (compounds vs isolations) |
| Experience | Volume (sets/wk), progression rule, periodisation scheme |
| Age group | Volume cap, intensity cap, hydration, bone-loading emphasis |
| Sex | BMR coefficient, fat floor, iron recommendation, calorie floor |
| Activity | TDEE multiplier |
| Diet | Meal library filter, cuisine picker, fat/carb split |
| Environment | Equipment filter on exercise selection |
| Session length | Density (work:rest), superset usage |

## 2.7 Somatotype inference

If `body_fat_pct` is supplied, `infer_somatotype()` uses BMI + body
fat % + sex to classify the client. The heuristic:

```
Male:   BF ≤ 14 & BMI ≤ 23  →  ECTOMORPH
        BF ≥ 22 OR BMI ≥ 28  →  ENDOMORPH
        else                 →  MESOMORPH

Female: BF ≤ 20 & BMI ≤ 22  →  ECTOMORPH
        BF ≥ 30 OR BMI ≥ 28  →  ENDOMORPH
        else                 →  MESOMORPH
```

This is a coarse heuristic. For finer classification, use the Heath-
Carter method (out of scope for v1.0).

## 2.8 Why not fewer dimensions?

Reducing dimensionality would merge clients who need very different
plans. For example:

* `fat_loss` + `endomorph` + `beginner` → high-protein, low-volume, frequent cardio
* `fat_loss` + `ectomorph` + `beginner` → moderate deficit, hypertrophy-leaning

Both are "fat loss beginners" but the plans diverge substantially.

The 9 dimensions let every meaningful client combination have its
own traceable plan signature.

## 2.9 Why not more?

Every additional dimension:
* Multiplies the combinatorial space
* Adds cognitive load for the coach filling in the intake
* Must have an evidence-based effect on the plan

We deliberately stop at 9 — additional dimensions would either be
redundant (already captured by age / experience) or unsupported by
the evidence base.

## 2.10 Future extensions

Candidates for a future 2.0:

* **Hormonal status** — menstrual-cycle phase, menopause, TRT
* **Chronotype** — morning vs evening preference
* **Travel intensity** — currently lumped into lifestyle
* **Injury severity** — currently a single flag
* **Mental health** — anxiety, depression, ADHD

Each would need a clear evidence base for impact on plan design.
