# 09 — Methodology & Evidence Base

This document lists the evidence and reasoning behind every
default in the engine. All numbers are conservative; when evidence
is mixed, the more conservative value is used.

## 9.1 Body composition

### BMI
* **Source**: World Health Organization (WHO), 1995.
* **Rationale**: International standard, well-validated for
  population-level screening.
* **Limitations**: Does not differentiate lean vs fat mass; can
  mis-classify athletic clients (high BMI + low BF %).

### Body-fat — Navy method
* **Source**: Hodgdon & Beckett, 1984 (US Navy).
* **Formula**:
  * Men: 495/(1.0324 − 0.19077·log10(waist − neck) + 0.15456·log10(height)) − 450
  * Women: 495/(1.29579 − 0.35004·log10(waist + hip − neck) + 0.22100·log10(height)) − 450
* **Accuracy**: ±3 % vs DEXA in validation studies.
* **Use case**: when tape measurements are available.

### Body-fat — Deuremberg
* **Source**: Deurenberg et al., 1991.
* **Use case**: when only BMI is available.

### Lean body mass
* Computed as `weight × (1 − bf/100)`.
* Used by Katch-McArdle BMR formula.

## 9.2 Energy expenditure

### BMR — Mifflin-St Jeor (default)
* **Source**: Mifflin et al., 1990 (J Am Diet Assoc).
* **Accuracy**: ±10 % vs indirect calorimetry.
* **Rationale**: Most accurate of the standard equations for
  modern, non-athlete populations (Frankenfield et al., 2005).

### BMR — Harris-Benedict (revised)
* **Source**: Roza & Shizgal, 1984.
* **Accuracy**: ±15 %. Provided for comparison only.

### BMR — Katch-McArdle
* **Source**: Katch & McArdle, 1973.
* **Use case**: when lean body mass is known; preferred for
  athletic populations.

### TDEE multipliers
* **Source**: Harris & Benedict (1919) and updated literature.
* **Conservative bias**: engine uses the lower end of the
  multiplier when self-reported activity is borderline
  (e.g. "moderate" defaults to 1.55, not 1.6+).

### Calorie target adjustments

| Goal | Adjustment | Source / rationale |
|---|---|---|
| Fat loss | −20 % | Meta-analysis of RCTs shows ~20 % deficit maximises fat loss while preserving lean mass (Helms et al., 2014) |
| Muscle gain | +12 % | Lean bulk: surplus of 200-300 kcal supports ~0.25-0.5 kg/mo gain without excessive fat storage |
| Recomposition | 0 % | Maintenance calories + high protein + progressive overload |
| Strength | +5 % | Strength gains on maintenance are possible; small surplus adds recovery buffer |
| Endurance | +10 % | Endurance training increases energy needs by ~5-15 % |
| Athletic | +12 % | High overall energy demand from multi-modal training |
| Rehabilitation | +5 % | Small surplus supports tissue repair |

## 9.3 Macronutrients

### Protein
| Goal | g/kg | Source |
|---|---|---|
| Fat loss | 2.0 | Helms et al. (2014): 2.3 g/kg in a 20 % deficit preserved lean mass |
| Muscle gain | 1.9 | Schoenfeld & Aragon (2018): ≥1.6 g/kg is sufficient; we use 1.9 for safety |
| Recomposition | 1.9 | Same as muscle gain |
| Strength | 1.8 | Lower volume tolerance; protein still high |
| Endurance | 1.6 | Burke et al. (2011): 1.6 g/kg for endurance athletes |
| Athletic | 1.8 | Multi-modal; lean toward higher end |
| General health | 1.4 | General-population target |
| Rehabilitation | 1.6 | Tissue-repair needs |

### Fat floor
| Sex | g/kg | Source |
|---|---|---|
| Male | 0.8 | Volek et al.: minimum fat for testosterone production |
| Female | 0.9 | Same; higher floor for hormonal health |

### Carbs
* Remainder of calories after protein and fat.
* Keto override: hard ceiling at 50 g carbs, fat raised to 70 %.

## 9.4 Hydration

* **Source**: EFSA (2010), ACSM position stand.
* **Base**: 35 ml/kg body weight (covers NEAT and basic needs).
* **Workout bonus**: +350 ml per 30 min training (covers sweat losses).

## 9.5 One-rep max estimates

* **Epley (1985)**: weight × (1 + reps/30). Most cited.
* **Brzycki (1993)**: weight × 36/(37 − reps). Most accurate in 1-10 rep range.
* **Lander (1985)**: 100·weight/(101.3 − 2.67123·reps).
* **Average**: defensive default when test data is sparse.

We do **not** recommend testing 1RM directly. Use percent-of-1RM
from `one_rep_max()` and RPE to drive prescription.

## 9.6 Cardio zones (Karvonen)

* **HR_max formula**: Tanaka et al. (2001) — `208 − 0.7 × age`.
  More accurate than the older 220−age.
* **HRR**: HR_max_Tanaka − resting_HR.
* **Zones**: standard 5-zone model based on %HRR.

## 9.7 Training volume

| Goal | Sets / group / wk | Source |
|---|---|---|
| Maintenance | 6-8 | Renaissance Periodisation (RP) volume landmarks |
| Hypertrophy | 10-14 | RP, Mike Israetel meta-analyses |
| Strength | 6-10 | Low-volume strength prescription |
| Fat loss | 8-12 | Higher volume + cardio to drive deficit |
| Recomp | 10-12 | Mid-range |
| Endurance | 4-6 | Low strength volume + high cardio |
| General health | 6-8 | Maintenance-level |
| Rehab | 4-6 | Conservative |

Experience modifiers and age modifiers are documented in
`decision_trees.py`.

## 9.8 Intensity (reps & RPE)

| Goal | Primary reps | RPE | Source |
|---|---|---|---|
| Strength | 3-6 | 8.5 | Schoenfeld (2010); RPE = "2 reps in reserve" |
| Hypertrophy | 6-12 | 8.0 | Standard hypertrophy range |
| Endurance | 12-20 | 7.0 | Higher reps, lower load |
| Fat loss | 10-15 | 7.5 | Combines metabolic + mechanical stimulus |
| General health | 8-12 | 7.5 | Middle of the road |
| Rehab | 8-12 | 6.5 | Conservative |

## 9.9 Periodisation

| Profile | Scheme | Source |
|---|---|---|
| Beginner | Linear Progression | Starting Strength, StrongLifts 5×5 |
| Strength | 5/3/1 | Wendler (2009) |
| Muscle gain | DUP | Multiple studies showing DUP ≈ block for hypertrophy |
| Endurance | Block | Seiler & Kjerland (2006) |
| Default | Linear with RPE cap | Conservative default |

Deload frequency: every 4-6 weeks. Empirical evidence (Coleman
et al., 2016) suggests deload every 4-6 weeks optimises recovery
without detraining.

## 9.10 Progression rules

* **Beginner linear**: add reps/session, then add load when top
  of rep range. Reset after 3 stalls.
* **Strength wave-load**: 5/3/1 waves (Wendler).
* **Hypertension**: rep-range progression only, RPE ≤ 7.
  Avoids excessive BP spikes from heavy Valsalva.
* **Default double-progression**: hit top of rep range with good
  form, then add 2.5-5 kg.

## 9.11 Meal library

* Calorie and macro estimates are conservative — we list the
  upper end of the realistic range.
* Recipes are simple and short — the engine is a starting point,
  not a recipe app.
* Cuisine coverage aims for ≥ 4 meals per major cuisine × major
  diet combination. Falls back gracefully when combinations are
  missing.

## 9.12 Supplements

| Supplement | Evidence level | Source |
|---|---|---|
| Vitamin D | Strong | Many deficiency studies; D₃ 1000-2000 IU/d |
| Omega-3 | Strong | Meta-analyses show CV benefit at 1-2 g EPA+DHA |
| Magnesium | Moderate | Helpful for sleep, glycaemic control, BP |
| Creatine | Strong | Most studied performance aid; 5 g/d |
| Protein powder | Strong | Convenience to hit protein targets |
| Iron (female) | Strong | Pre-menopausal deficiency common |
| Collagen (joint) | Moderate | 10-15 g/d may support connective tissue |
| Berberine (T2D) | Moderate | Adjunct to lifestyle; 500 mg 2-3x/d |
| Potassium citrate (HTN) | Moderate | Counter sodium load |

## 9.13 Health overrides

Each medical override is based on a position stand or guideline:

| Condition | Override | Source |
|---|---|---|
| T2 diabetes | Low-GI carbs; 30-40 g fibre; 3+1 meals | ADA Standards of Care 2024 |
| Hypertension | Na < 2300 mg; K⁺ ≥ 3500 mg | DASH diet trial |
| High cholesterol | Saturated fat < 7 % kcal; ≥ 30 g fibre | AHA guidelines |
| PCOS | Protein ≥ 1.8 g/kg; low-GI | International PCOS guideline 2023 |
| Pregnancy | Folate ≥ 600 mcg; iron 27 mg + vit C | ACOG |
| Postpartum | Protein ≥ 1.8 g/kg; omega-3 250 mg | Lactation nutrition consensus |

## 9.14 PAR-Q

* **Source**: ACSM (2017) — standard 7-item screening.
* **Threshold**: ≥ 1 "yes" → physician clearance.
* Our engine uses weighted scoring (1.5-4.0 per item) and flags
  ≥ 4.0 as "needs clearance".

## 9.15 Known limitations

1. **Calorie targets**: BMR equations have ±10 % error. If
   weight is not changing as expected, recalculate after 2-4
   weeks.
2. **Macros**: protein and fat floors are well-supported; carb
   distribution is more art than science.
3. **Volume landmarks**: derived from a limited body of
   literature; individual response varies up to 3×.
4. **Supplements**: only evidenced supplements are listed; any
   pharmacological agent requires medical oversight.
5. **Meal library**: meals are templates; clients should adjust
   portion sizes to hit calorie and macro targets exactly.
6. **Exercise library**: 38 exercises covers most patterns but
   is not exhaustive.
7. **Archetype space**: 1.18M combinations is comprehensive but
   includes biologically implausible ones (e.g. youth + elite).

## 9.16 What we deliberately do *not* claim

* We do not prescribe medical treatment.
* We do not replace physiotherapy, dietitian, or psychologist input.
* We do not generate "personalised" advice for clients under
  18 or pregnant clients without medical sign-off.
* We do not promise specific outcomes.

## 9.17 Future research directions

* Individual volume response (genetic markers)
* Hormonal-cycle-aware programming for females
* Wearable-driven auto-progression
* HRV-driven recovery-modulated volume
* Microbiome-aware nutrition

## 9.18 Bibliography (key references)

1. ACSM (2017). *Guidelines for Exercise Testing and Prescription* (10e).
2. Deurenberg P, Weststrate JA, Seidell JC (1991). BMI as a measure of body fatness. *Int J Obes*.
3. Frankenfield D, Roth-Yousey L, Compher C (2005). Comparison of predictive equations for resting metabolic rate. *J Am Diet Assoc*.
4. Helms ER, Zinn C, Rowlands DS, Brown SR (2014). A systematic review of dietary protein during caloric restriction in resistance trained lean athletes. *IJKSS*.
5. Hodgdon JA, Beckett MB (1984). Prediction of percent body fat for US Navy men from body circumferences. *Technical Report*.
6. Mifflin MD et al. (1990). A new predictive equation for resting energy expenditure. *J Am Diet Assoc*.
7. Schoenfeld BJ, Aragon AA (2018). How much protein per day for muscle hypertrophy? *JISSN*.
8. Wendler J (2009). *5/3/1: The Simplest and Most Effective Training System*.
9. Tanaka H, Monahan KD, Seals DR (2001). Age-predicted maximal heart rate revisited. *JACC*.
10. WHO (1995). Physical status: the use and interpretation of anthropometry.
11. Seiler S, Kjerland G (2006). Quantifying training intensity distribution. *Int J Sports Physiol Perform*.
12. Coleman M et al. (2016). A systematic review of the effects of deload weeks. *Sports*.
