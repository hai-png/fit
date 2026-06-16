# Critical Analysis of `hai-png/fit` Repository
## Cross-Referenced Against the Fitness App Reference Guide

---

## 1. ARCHITECTURE & DESIGN ASSESSMENT

### ✅ What They Do Well

| Aspect | Evaluation | Notes |
|--------|-----------|-------|
| **Modular structure** | Strong | Clean separation: calculators, decision trees, exercise plans, meal plans, adjustments |
| **Evidence-based** | Strong | Every formula traces to a cited source (RippedBody, Helms, Hodgdon & Beckett) |
| **Determinism** | Strong | Same inputs → same outputs (essential for reproducibility) |
| **Explainability** | Strong | Every recommendation carries a rationale string |
| **Hard filters** | Strong | Equipment is never silently relaxed — critical safety feature |
| **Safety floors** | Present | 1200 kcal minimum enforced; contraindications tracked per exercise |
| **Typing** | Strong | Dataclasses, enums, type hints throughout |

### ⚠️ Design Concerns

| Issue | Severity | Detail |
|-------|----------|--------|
| **Somatotype reliance** | Medium | Uses ectomorph/mesomorph/endomorph — a discredited taxonomy with no scientific basis. The reference guide does NOT include somatotype as a valid framework. Modern sports science rejects this classification. |
| **9-dimensional signature** | Low-Medium | 25,920 combinations is combinatorial overkill. Most dimensions are irrelevant to actual plan generation (e.g., session length only affects rest periods, not exercise selection). |
| **Age buckets too coarse** | Low | 18-30 / 31-45 / 46+ misses important physiological transitions (e.g., sarcopenia onset at 50+, menopausal changes). |

---

## 2. CALORIE & METABOLISM CALCULATIONS

### 2.1 BMR Formula Choice

| Implementation | Reference Guide Alignment | Verdict |
|---------------|--------------------------|---------|
| **Primary: Harris-Benedict** | ❌ **MISALIGNED** | The reference guide states Mifflin-St Jeor is "the most reliable, often predicting REE within 10% of measured values and having the narrowest margin of error" (Frankenfield et al. review). Harris-Benedict was published in 1919 and systematically overestimates BMR by ~5-10% in modern populations. |
| **Alternative: Mifflin-St Jeor** | ✅ Correct but secondary | Present in code but not used as the primary. Should be inverted. |
| **Katch-McArdle** | ✅ Present | Good for lean individuals with known BF%. Correctly implemented. |

**Recommendation:** Make Mifflin-St Jeor the default. Harris-Benedict should be the fallback, not the primary.

### 2.2 Metabolic Adaptation

| Feature | Implementation | Reference Guide Alignment |
|---------|---------------|--------------------------|
| Deficit adaptation (-5%) | ✅ `energy_expenditure()` | Matches guide: "BMR drops ~5% during calorie deficit" |
| Post-diet adaptation (-3%) | ✅ `if >10% below all-time highest` | Matches guide |
| NEAT buffer (+50% on surplus) | ✅ Bulk surplus calculation | Matches guide |
| BMR selection based on deficit state | ✅ | Good design |

### 2.3 TDEE Activity Multipliers

| Level | Fit Implementation | Guide Recommended | Alignment |
|-------|-------------------|-------------------|-----------|
| Sedentary | ×1.15 | ×1.25 | ❌ **Too low** |
| Mostly sedentary + lifting | ×1.35 | ×1.45 | ❌ **Too low** |
| Lightly active + lifting | ×1.55 | ×1.55-1.65 | ⚠️ Low end of range |
| Highly active + lifting | ×1.75 | ×1.75-1.85 | ⚠️ Low end of range |

**Critical Finding:** The fit repository's TDEE multipliers are systematically lower than RippedBody's published values. RippedBody's article explicitly states:
- Sedentary (<5k steps): ×1.25
- Mostly Sedentary + lifting: ×1.45

Fit uses ×1.15 and ×1.35 respectively — these are ~8% lower, which means calorie targets will be systematically underestimated. For a 2000 kcal TDEE person, this is a 160 kcal/day error.

**Missing:** The `ActivityLevel` enum has only 4 tiers, but the reference guide shows RippedBody uses 5 tiers (adding "Moderately Active" between lightly and highly active).

### 2.4 Calorie Target Logic

**Cutting (0.75% BW/week):**
```python
deficit = bodyweight_kg * 0.0075 * 1100  # 1100 kcal per kg of deficit
```

| Aspect | Implementation | Guide | Alignment |
|--------|---------------|-------|-----------|
| Rate | 0.75% BW/week | 0.25-1.0% BW/week (sweet spot 0.5-0.7%) | ⚠️ Slightly aggressive for most people |
| Alpert's max fat loss | ❌ Not implemented | 22 kcal/lb of fat per day | **MISSING** — critical safety check |
| Calorie floor | ✅ 1200 kcal | 1200 (women) / 1500 (men) | ⚠️ Men's floor is 1500, not enforced |

**Problem:** The 0.75% rate doesn't scale with body fat percentage. Per the reference guide, fatter individuals can safely lose faster (up to 1.5 lbs/week), while leaner individuals need slower rates (0.25-0.5%/week). The current implementation applies 0.75% universally.

**Bulking:**
```python
# Experience-tiered rates: Beginner 2%, Intermediate 1%, Advanced 0.5%
surplus = bodyweight_kg * rate * 330 * 1.5  # 50% NEAT buffer
```

| Aspect | Implementation | Guide | Alignment |
|--------|---------------|-------|-----------|
| Beginner rate | 2%/month | 2%/month | ✅ |
| Intermediate rate | 1%/month | 1%/month | ✅ |
| Advanced rate | 0.5%/month | 0.5%/month | ✅ |
| NEAT buffer | 50% | 50% | ✅ |
| Energy cost of muscle | 330 kcal/kg | 5500 kcal/kg (~2500/lb) | ✅ Consistent |
| Research alignment | — | Helms et al.: faster gains ≠ more muscle | ⚠️ Should warn users about excess fat gain at high rates |

---

## 3. MACRONUTRIENT CALCULATIONS

### 3.1 Protein

| Scenario | Fit Implementation | Guide Recommendation | Alignment |
|----------|-------------------|---------------------|-----------|
| Cutting, known BF% | 2.5 g/kg lean mass | 2.0-2.7 g/kg body weight (Helms: 2.3-3.1 g/kg lean) | ✅ Within range |
| Cutting, unknown BF% | 2.2 g/kg target body weight | 2.0-2.7 g/kg | ✅ |
| Bulking, known BF% | 2.2 g/kg lean mass | 1.6-2.2 g/kg body weight | ⚠️ Slightly high for bulking |
| Bulking, unknown BF% | 1.6 g/kg body weight | 1.6-2.2 g/kg | ✅ |
| Vegan cutting | 2.6 g/kg lean mass | 2.6 g/kg body weight (vegan, dieting) | ✅ |
| Vegan bulking (unknown BF%) | 2.2 g/kg body weight | 2.2 g/kg body weight | ✅ |
| Recomposition | 2.2 g/kg lean | 1.8-2.4 g/kg body weight | ✅ |
| Strength | 2.2 g/kg lean | 1.6-2.2 g/kg | ✅ |

**Good:** Protein is set by lean mass when BF% is known, and by body weight when unknown. This correctly implements the "no best ratio" principle — protein doesn't scale proportionally with calories.

**Issue:** The protein for cutting with known BF% (2.5 g/kg lean) is lower than Helms' recommendation of 2.3-3.1 g/kg lean for athletes in energy restriction. For very lean individuals cutting, 2.5 may be insufficient.

### 3.2 Fat

| Scenario | Fit Implementation | Guide | Alignment |
|----------|-------------------|-------|-----------|
| Cutting | 15-25% of calories | 15-30% | ✅ (within range) |
| Bulking | 20-30% of calories | 15-30% | ✅ |
| Minimum floor | 0.5 g/kg body weight | 0.5 g/kg (0.25 g/lb) | ✅ |
| Somatotype adjustment | Ectomorph: -2%, Endomorph: +2% | Not in reference guide | ⚠️ Arbitrary |

**Issue:** The somatotype-based fat adjustments (-2% for ectomorph, +2% for endomorph) have no basis in the reference guide or scientific literature. This introduces noise without benefit.

### 3.3 Carbohydrates

| Aspect | Implementation | Guide | Alignment |
|--------|---------------|-------|-----------|
| Method | Remainder of calorie budget | Remainder after protein and fat | ✅ |
| Minimum floor | 1.0 g/kg body weight | Not specified as minimum | ✅ Reasonable |

**Good:** Carbs are correctly set as the remainder — this is the proper approach per the reference guide.

### 3.4 Missing: Macro Adjustment Logic

The reference guide specifies HOW to adjust macros when calories change:

| Feature | Fit | Guide | Gap |
|---------|-----|-------|-----|
| Reduce carbs:fats at 1:1 to 2:1 ratio | ❌ | ✅ | **MISSING** |
| Maintain protein during cuts | ✅ (implicitly) | ✅ | Present |
| Round macros to nearest 5g | ❌ | ✅ | Minor |
| Macro cycling support | ❌ | ✅ | Missing |

---

## 4. BODY COMPOSITION ASSESSMENT

### 4.1 Body Fat Estimation

| Method | Fit Implementation | Guide Accuracy | Alignment |
|--------|-------------------|----------------|-----------|
| User input (priority 1) | ✅ | Most trusted | ✅ |
| Navy formula (priority 2) | ✅ Hodgdon & Beckett 1984 | ±3-4% | ✅ |
| Visual estimation (priority 3) | ✅ 7-band system | Subjective | ✅ |
| Deurenberg BMI fallback (priority 4) | ✅ | Variable accuracy | ✅ |

**Visual BF bands comparison:**

| Label | Fit Range | Guide (RippedBody) Range | Alignment |
|-------|-----------|-------------------------|-----------|
| shredded | 6-9% (mid 8.0) | 7-9% | ⚠️ Slightly off at bottom |
| very_lean | 10-12% (mid 11.0) | 10-11% | ⚠️ Slightly wider |
| lean | 13-15% (mid 14.0) | 12-14% | ⚠️ Slightly shifted |
| average_fit | 16-19% (mid 17.5) | 15-17% | ⚠️ Slightly shifted |
| soft | 20-24% (mid 22.0) | 18-20% | ❌ Gap: 18-20% not mapped |
| overweight | 25-29% (mid 27.0) | 21-24% | ❌ Different mapping |
| obese | 30-40% (mid 33.0) | 25-29%, 30%+ | ⚠️ Compressed |

**Critical Gap:** The fit repository's visual bands don't align well with RippedBody's photo guide. For example, "soft" in fit is 20-24% but RippedBody shows 18-20%. "Overweight" in fit is 25-29% but RippedBody shows 21-24%. This could lead to misclassification.

### 4.2 Self-Estimate Correction

```python
def correct_bf_estimate(bf_pct, is_self_estimate=True):
    if is_self_estimate:
        return round(bf_pct * 1.5, 1)
    return bf_pct
```

**✅ Correctly implements** RippedBody's guidance: "Most people underestimate their body-fat percentage... add 50% to your estimate."

### 4.3 Navy Formula Implementation

**✅ Correctly implements** both male and female equations from Hodgdon & Beckett 1984. Proper validation (waist > neck, hip required for females, bounds 2-60%).

### 4.4 FFMI & Muscular Potential

| Feature | Fit | Guide | Alignment |
|---------|-----|-------|-----------|
| Berkhan model | `height_cm - 100` | `height_cm - 98~102` | ✅ (uses midpoint) |
| FFMI calculation | `lean_kg / height_m²` | Same | ✅ |
| Natural ceiling | 25 | ~25 | ✅ |
| Normalized FFMI | `FFMI + 6.1 × (1.8 - height)` | `FFMI + 6.3 × (1.8 - height)` | ⚠️ Minor coefficient difference |
| Categorization | 6 tiers | Different tiers | ⚠️ Different thresholds |

**Issue:** The normalized FFMI coefficient is 6.1 in fit but 6.3 in the reference guide. This is a minor discrepancy but should be aligned.

### 4.5 MISSING Anthropometric Indices

The reference guide covers several health risk indicators that fit does NOT implement:

| Metric | In Fit? | Importance |
|--------|---------|-----------|
| Waist-to-Height Ratio (WHtR) | ❌ | Better predictor of CVD than BMI |
| Waist-to-Hip Ratio (WHR) | ❌ | Visceral fat indicator |
| A Body Shape Index (ABSI) | ❌ | Mortality risk predictor |
| Ideal Body Weight (IBW) | ❌ | Clinical reference |

---

## 5. GOAL-SETTING & TRAINEE CATEGORIZATION

### 5.1 The 9 Trainee Categories

| Category | Fit Implementation | Guide Alignment | Verdict |
|----------|-------------------|-----------------|---------|
| Skinny | ✅ BF < 10%, no muscle | ✅ | Correct |
| Fat but Muscled | ✅ BF 22-30%, has muscle | ✅ (guide says 20-30%) | Correct |
| Muscled Lean | ✅ BF 15-22%, has muscle | ✅ | Correct |
| Shredded | ✅ BF < 10%, has muscle | ✅ | Correct |
| Fat & Weak | ✅ BF 23-30%, no muscle | ✅ (guide says 23-30%) | Correct |
| Obese | ✅ BF > 30% | ✅ | Correct |
| Skinny-Fat | ✅ BF 15-22%, no muscle | ✅ | Correct |
| Purgatory | ❌ Not classified in code | ✅ Guide includes it | **MISSING** |
| New Trainee Healthy | ✅ | ✅ | Correct |

### 5.2 Cut/Bulk Decision Boundaries

| Sex | Fit | Guide | Alignment |
|-----|-----|-------|-----------|
| Male end cut | 10% | 10% | ✅ |
| Male end bulk | 20% | 20% | ✅ |
| Female end cut | 18% | 18-20% | ✅ |
| Female end bulk | 28% | 28-30% | ✅ |

### 5.3 Strategy Recommendations

| Category | Fit Strategy | Guide Strategy | Alignment |
|----------|-------------|----------------|-----------|
| Skinny | Bulk | Bulk | ✅ |
| Fat but Muscled | Cut | Cut | ✅ |
| Muscled Lean | Cut | Cut | ✅ |
| Shredded | Maintenance | Maintenance/Slow Bulk | ✅ |
| Fat & Weak | Cut | Cut | ✅ |
| Obese | Cut (habit change) | Habit change + Cut | ✅ |
| Skinny-Fat | Recomp | Recomp/Gentle Bulk | ✅ |
| New Trainee Healthy | Recomp | Recomp | ✅ |

### 5.4 MISSING: Decision Tree Logic

The reference guide provides a formal decision tree:
```
Overweight? → Cut
└── Not overweight → Underweight? → Bulk
    └── Not underweight → Beginner/returning? → Recomp
        └── Not beginner → Preference-based
```

The fit repository implements the classification but does NOT provide the decision tree as executable logic. The `classify_trainee()` function only categorizes — it doesn't recommend a path when the user's stated goal conflicts with their body composition.

---

## 6. TRAINING PROGRAM GENERATION

### 6.1 Training Splits

| Days | Fit Split | Guide Alignment | Verdict |
|------|-----------|-----------------|---------|
| 2 | Full Body A/B | ✅ Full Body recommended for beginners | Correct |
| 3 | Full Body A/B/C | ✅ RippedBody default | Correct |
| 4 | Upper/Lower A/B | ✅ Standard hypertrophy split | Correct |
| 5 | Push/Pull/Legs + Push/Pull | ⚠️ Unconventional | Unusual but workable |
| 6 | PPL × 2 | ✅ Standard high-volume split | Correct |

### 6.2 Volume Guidelines

| Goal | Beginner | Intermediate | Advanced | Guide Range | Alignment |
|------|----------|-------------|----------|-------------|-----------|
| Strength | 8 sets | 12 sets | 16 sets | — | Reasonable |
| Fat Loss | 8 sets | 10 sets | 12 sets | Reduce 20-30% from maintenance | ✅ Reduced |
| Muscle Gain/Recomp | 10 sets | 14 sets | 18 sets | 10-20 sets/muscle/week | ✅ Within range |
| General Health | 10 sets | 14 sets | 18 sets | — | Reasonable |

**Good:** Volume is appropriately reduced during fat loss (preserving intensity while cutting volume). This aligns with the reference guide.

### 6.3 Intensity (RIR) Guidelines

| Aspect | Fit | Guide | Alignment |
|--------|-----|-------|-----------|
| Beginner RIR floor | 3.0 | "stay further from failure" | ✅ |
| Fat loss RIR | Primary: 2.0, Accessory: 1.0 | Maintain training intensity | ✅ |
| Strength RIR | Primary: 2.0 | Lower reps, closer to failure | ✅ |
| Hypertrophy RIR | Primary: 2.0, Accessory: 1.0 | 1-3 RIR | ✅ |

### 6.4 Progression Schemes

| Level | Fit | Guide | Alignment |
|-------|-----|-------|-----------|
| Beginner | Linear (+2.5kg when range hit) | Add weight/reps each session | ✅ |
| Intermediate | Double progression | Add reps, then load | ✅ |
| Advanced | Wave loading / RPE-based | Periodised, deload 4-6 weeks | ✅ |

### 6.5 Exercise Library

| Aspect | Fit | Assessment |
|--------|-----|-----------|
| Total exercises | 47 | Good coverage |
| Equipment filtering | HARD filter | ✅ Never prescribes infeasible exercises |
| Regression/Progression chains | ✅ | Each exercise has regression and progression |
| Form cues | ✅ | 2-4 cues per exercise |
| Contraindications | ✅ | Tracked (e.g., lower_back for deadlift) |
| Movement patterns | 8 patterns | Covers all major patterns |

**Missing patterns from guide:**
- The guide specifically emphasizes squat, bench press, and deadlift as the "big three"
- Fit includes these but doesn't prioritize them for beginners as strongly as the guide recommends

### 6.6 Rest Periods

| Goal | Fit | Guide | Alignment |
|------|-----|-------|-----------|
| Strength | 3-5 min (180-300s) | 3-5 min | ✅ |
| Hypertrophy | 1.5-3 min (90-180s) | 1.5-3 min | ✅ |
| Fat Loss | 60-90s | — | ✅ Reasonable |

### 6.7 Cardio Prescription

| Aspect | Fit | Guide | Alignment |
|--------|-----|-------|-----------|
| Fat loss cardio | 60+ min/week Zone-2 | Cardio supplementary to diet | ✅ |
| Muscle gain cardio | 0-60 min optional | Excessive cardio interferes with gains | ✅ |
| Step target | 7,000-10,000 | Track steps for NEAT | ✅ |
| Cardio limit | Implicitly capped | < 50% of lifting time | ⚠️ Not explicitly enforced |

**Issue:** The guide states "your cardio for the week should be less than half the time you spend lifting weights." This constraint is not enforced in the fit code. A user doing 3×60 min lifting could theoretically be prescribed 150+ min of cardio.

---

## 7. ADJUSTMENTS & PLATEAU MANAGEMENT

### 7.1 Cut Adjustment Checklist

| Step | Fit Implementation | Guide Alignment | Verdict |
|------|-------------------|-----------------|---------|
| 1. Check tracking accuracy | ✅ | ✅ | Correct |
| 2. Manage hunger | ✅ Swap liquid calories, more veg | ✅ | Correct |
| 3. Food environment | ✅ | ✅ | Correct |
| 4. Revisit "why" | ✅ | ✅ | Correct |
| 5. Stress management | ✅ | ✅ | Correct |
| 6. Sleep | ✅ 7+ hours | ✅ | Correct |
| 7. NEAT/steps | ✅ Set minimum 5,000-8,000 | ✅ | Correct |
| 8. Wait period | ✅ 3-4 weeks | ✅ | Correct |
| 9. Add cardio | ✅ Before reducing calories | ✅ | Correct |
| 10. Reduce calories | ✅ Last resort, ~200-250 kcal | ✅ | Correct |

**✅ Excellent alignment.** This is one of the strongest implementations in the repository — correctly positions calorie reduction as the LAST resort.

### 7.2 Bulk Adjustment Checklist

| Step | Fit | Guide | Alignment |
|------|-----|-------|-----------|
| 1. Check tracking | ✅ | ✅ | Correct |
| 2. Fullness management | ✅ Liquid calories, more meals | ✅ | Correct |
| 3. Food environment | ✅ Calorie-dense foods | ✅ | Correct |
| 4. Revisit "why" | ✅ | ✅ | Correct |
| 5. Stress | ✅ | ✅ | Correct |
| 6. Sleep | ✅ | ✅ | Correct |
| 7. NEAT increase | ✅ Don't restrict, eat more | ✅ | Correct |
| 8. Wait 5 weeks | ✅ | ✅ | Correct |
| 9. Increase calories | ✅ Last resort, ~5% (+150-200 kcal) | ✅ | Correct |

**✅ Excellent alignment.**

### 7.3 Training Plateau Checklist

| Step | Fit | Guide | Alignment |
|------|-----|-------|-----------|
| 1. Sleep | ✅ 7+ hours | ✅ | Correct |
| 2. Eating enough | ✅ | ✅ | Correct |
| 3. Protein intake | ✅ 1.6 g/kg minimum | ✅ (0.7 g/lb = 1.54 g/kg) | ✅ |
| 4. Training intensity | ✅ RPE/RIR | ✅ | Correct |
| 5. Frequency | ✅ 2×/week per muscle | ✅ | Correct |
| 6. Technique | ✅ | ✅ | Correct |
| 7. Joint pain | ✅ Higher reps, BFR mentioned | ✅ BFR at 20-30% 1RM | ⚠️ BFR not implemented in exercise library |
| 8. Volume management | ✅ Increase or deload | ✅ | Correct |

### 7.4 Progress Tracking

| Feature | Fit | Guide | Alignment |
|---------|-----|-------|-----------|
| Daily weighing | ✅ | ✅ | Correct |
| Weekly averages | ✅ | ✅ | Correct |
| First week data ignored | ✅ | ✅ | Correct |
| 9-point measurements | ⚠️ Only waist mentioned | ✅ 9 points | **PARTIAL** |
| Progress photos | ❌ Not mentioned | ✅ Monthly | **MISSING** |
| Whoosh effect explained | ✅ | ✅ | Correct |
| Weight fluctuation causes | ✅ Water, glycogen, stress | ✅ | Correct |

### 7.5 Metabolic Adaptation

| Feature | Fit | Guide | Alignment |
|---------|-----|-------|-----------|
| Explanation provided | ✅ | ✅ | Correct |
| Impact range | ✅ 15-25% | ✅ 5-25% (adaptive thermogenesis) | ⚠️ Slightly high |
| Mitigation strategies | ✅ 5 strategies | ✅ | Good |
| Adaptive TDEE | ✅ Mentioned in text | ✅ Core methodology | ❌ **Not implemented as a calculator** |

**Major Gap:** The reference guide extensively covers Adaptive TDEE as a key differentiator for modern fitness apps. The fit repository mentions it in the adjustments module but does NOT implement an actual adaptive TDEE calculator that learns from user data over time. This is a significant missing feature.

### 7.6 Reverse Dieting

| Feature | Fit | Guide | Alignment |
|---------|-----|-------|-----------|
| Implementation | ❌ | ✅ 3 approaches | **MISSING** |

**Major Gap:** No reverse dieting calculator or protocol. After extended cuts, users need a structured plan to return to maintenance without rapid fat regain.

---

## 8. NUTRITION DETAILS

### 8.1 Micronutrients

| Feature | Fit | Guide | Alignment |
|---------|-----|-------|-----------|
| Fruit/veg targets by calorie | ✅ 2/3/4 cups | ✅ 2/3/4 cups | ✅ |
| Fiber: 14g/1000kcal | ✅ | ✅ | ✅ |
| Water guidance | ✅ 4 guidelines | ✅ 4 guidelines | ✅ |
| Water formula: 35ml/kg | ✅ | ✅ 30ml/kg | ⚠️ Slightly higher (35 vs 30) |

### 8.2 Supplement Recommendations

| Feature | Fit | Guide Alignment | Verdict |
|---------|-----|-----------------|---------|
| Tiered system | ✅ Foundational, goal-specific, conditional | ✅ Evidence-based tiers | Correct |
| Vegan-specific | ✅ B12, D3, omega-3, creatine | ✅ | Correct |
| Creatine dosing | ✅ 5g/day | ✅ | Correct |
| Anti-supplement philosophy | ✅ Noted as least important layer | ✅ Bottom of pyramid | Correct |

### 8.3 Diet Types

| Feature | Fit | Guide | Gap |
|---------|-----|-------|-----|
| Omnivore | ✅ | ✅ | — |
| Vegan | ✅ | ✅ | — |
| Keto | ❌ Not in meal plan tags (only in comments) | ✅ Testing protocol | **MISSING** |
| Mediterranean | ❌ Not implemented as diet type | ✅ | **MISSING** |
| Vegetarian | ❌ Not implemented | ✅ | **MISSING** |
| Low-carb | ❌ | ✅ | **MISSING** |

**Note:** The meal library includes keto-tagged meals and Mediterranean cuisine, but the `DietaryPreference` enum only has `OMNIVORE` and `VEGAN`. The guide recommends supporting 11 diet types.

### 8.4 Meal Planning

| Aspect | Fit | Assessment |
|--------|-----|-----------|
| Total meals | 51 | Good variety |
| Cuisines | 8 | Good coverage |
| Portion scaling | ✅ Uniform scale factor | Good — ensures calorie accuracy |
| Proportional allocation | ✅ Per-slot weights | Fixes greedy allocation bug |
| Weekly rotation | ✅ With no-repeat logic | Good |
| Allergen filtering | ✅ Simple keyword matching | Basic but functional |
| Calorie accuracy | ≤0.4% error | Excellent |

**Issues:**
- Meal nutrition values appear to be manually estimated, not from a verified database (unlike MacroFactor's approach)
- No mechanism for users to add custom meals
- The meal library is small — 51 meals across 8 cuisines means ~6 meals per cuisine, which limits variety in weekly plans

---

## 9. QUESTIONNAIRES & INTAKE

### 9.1 Streamlined Intake (3 forms)

| Form | Fields | Assessment |
|------|--------|-----------|
| Diet & Preferences | 4 questions | ✅ Efficient |
| Fitness History | 4 questions | ✅ Efficient |
| Goals | 4 questions | ✅ Efficient |

**Total: 12 questions** — genuinely achieves the "~90 second intake" claim.

### 9.2 PAR-Q Replacement

| Approach | Fit | Guide | Assessment |
|----------|-----|-------|-----------|
| Auto-generated recommendations | ✅ Based on BMI, BF%, trainee category | ✅ Lifestyle-first approach | Correct — aligns with "before you count" philosophy |

### 9.3 Health Warnings

| Feature | Fit | Guide | Alignment |
|---------|-----|-------|-----------|
| Calorie floor warning (<1200) | ✅ | ✅ 1200 women / 1500 men | ⚠️ Missing men's 1500 floor |
| BMI underweight note | ✅ | ✅ | Correct |
| BMI obese note | ✅ | ✅ | Correct |
| Medical disclaimer | ✅ | ✅ | Correct |
| Sleep recommendation | ✅ 7-9 hours | ✅ | Correct |

---

## 10. MISSING FEATURES (vs Reference Guide)

### Critical Missing Features

| Feature | Importance | Implementation Complexity |
|---------|-----------|--------------------------|
| **Adaptive TDEE calculator** | HIGH | Medium — requires trend analysis over time |
| **Reverse dieting protocol** | HIGH | Low-Medium |
| **Alpert's maximum fat loss check** | HIGH | Low — simple formula |
| **WHtR / WHR / ABSI health indices** | MEDIUM | Low |
| **Progress photo tracking** | MEDIUM | Medium |
| **Full 9-point body measurement tracking** | MEDIUM | Low |
| **Men's 1500 kcal minimum floor** | MEDIUM | Low |
| **Keto tolerance testing protocol** | MEDIUM | Medium |
| **Macro cycling support** | LOW-MEDIUM | Medium |
| **Calorie deficit timeline (Hall's mathematical model)** | LOW | Medium |

### Nice-to-Have Missing Features

| Feature | Description |
|---------|------------|
| Outlier detection for log days | Filter incomplete/unusual days from adaptive TDEE |
| Data quality indicators | Show confidence levels for calculations |
| Body recomposition suitability assessment | Automated scoring based on BF%, experience, FFMI |
| Diet break recommendations | Scheduled maintenance breaks during long cuts |
| NEAT tracking integration | Step count monitoring with minimum targets |
| "Before You Count" assessment | Score the 10 big wins before recommending calorie counting |
| BFR training exercises | Blood flow restriction protocols for joint pain |
| Female-specific cycle tracking | Menstrual phase considerations for weight tracking |

---

## 11. CODE QUALITY & BUGS

### 11.1 Bugs Found

| Bug | Location | Severity | Description |
|-----|----------|----------|-------------|
| **TDEE multipliers too low** | `calculators.py:ACTIVITY_MULTIPLIERS` | HIGH | Sedentary ×1.15 vs RippedBody's ×1.25; Mostly sedentary ×1.35 vs ×1.45 |
| **Men's calorie floor missing** | `calculators.py:calorie_target()` | MEDIUM | Only 1200 kcal floor enforced, not 1500 for men |
| **Normalized FFMI coefficient** | `calculators.py:muscular_potential()` | LOW | Uses 6.1 instead of 6.3 |
| **Visual BF band misalignment** | `calculators.py:VISUAL_BF_BANDS` | MEDIUM | Bands don't match RippedBody's photo guide ranges |
| **Somatotype fat adjustment** | `calculators.py:macros_for()` | LOW | Ectomorph -2% fat, Endomorph +2% — no scientific basis |
| **`bmi_category()` return type mismatch** | `calculators.py` | LOW | Returns `BMICategory` enum but type annotation says `str` |

### 11.2 Code Quality

| Aspect | Rating | Notes |
|--------|--------|-------|
| Type hints | ⭐⭐⭐⭐ | Comprehensive, with dataclasses and enums |
| Documentation | ⭐⭐⭐⭐ | Excellent docstrings with source citations |
| Test coverage | ⭐⭐⭐⭐⭐ | 52 unit tests + integration tests — all pass |
| Modularity | ⭐⭐⭐⭐⭐ | Clean separation of concerns |
| Immutability | ⭐⭐⭐⭐ | `ArchetypeSignature` is frozen; other dataclasses are mutable |
| Error handling | ⭐⭐⭐ | `ValueError` for invalid inputs, but no graceful degradation |
| Performance | ⭐⭐⭐⭐⭐ | Pure functions, no I/O bottlenecks |

---

## 12. SUMMARY: ALIGNMENT SCORECARD

| Category | Score | Notes |
|----------|-------|-------|
| **Calorie Calculations** | 6.5/10 | Harris-Benedict as primary, TDEE multipliers too low, no Alpert check |
| **Macro Calculations** | 8/10 | Good protein logic, correct carb/fat approach, missing adjustment ratios |
| **Body Composition** | 7.5/10 | BF estimation methods good, visual bands misaligned, missing WHtR/WHR/ABSI |
| **Goal Setting** | 8.5/10 | 9 categories well-implemented, missing Purgatory, no decision tree |
| **Training Programs** | 8.5/10 | Splits, volume, intensity, progression all well-aligned |
| **Adjustments/Plateaus** | 9.5/10 | Excellent — calorie reduction correctly placed last |
| **Nutrition Details** | 7/10 | Good micros, supplements correct, limited diet types |
| **Progress Tracking** | 6/10 | Daily weighing and averages correct, missing photos and full measurements |
| **Adaptive Features** | 3/10 | No adaptive TDEE, no reverse dieting, no learning from user data |
| **Questionnaires** | 8/10 | Efficient intake, good PAR-Q replacement approach |
| **Code Quality** | 8.5/10 | Well-structured, typed, tested, documented |
| **Documentation** | 9/10 | Excellent — every module has source citations |

### **Overall: 7.3/10 — Good Foundation, Notable Gaps**

---

## 13. PRIORITY RECOMMENDATIONS

### 🔴 Critical (Fix Immediately)

1. **Replace Harris-Benedict with Mifflin-St Jeor as primary BMR formula** — This is the single most impactful change. Mifflin-St Jeor is more accurate for modern populations.
2. **Fix TDEE activity multipliers** — Increase from ×1.15/×1.35/×1.55/×1.75 to ×1.25/×1.45/×1.55-1.65/×1.75-1.85 to match RippedBody's published values.
3. **Add men's 1500 kcal minimum floor** — Currently only 1200 kcal is enforced.
4. **Implement Alpert's maximum fat loss check** — Prevent unsafe calorie deficits that cause excessive muscle loss.
5. **Fix visual BF band ranges** — Align with RippedBody's actual photo guide categories.

### 🟡 Important (Fix Soon)

6. **Implement Adaptive TDEE** — This is the biggest differentiator between static calculators and modern fitness apps. Use statistical modeling combining formula estimates with user weight/intake data over time.
7. **Add reverse dieting protocol** — Essential for post-cut transition.
8. **Implement WHtR as primary health screen** — Superior to BMI for health risk prediction.
9. **Add progress photo tracking** — Most reliable recomp indicator.
10. **Expand diet type support** — Add keto, Mediterranean, vegetarian, low-carb with proper macro presets.
11. **Add macro adjustment ratio logic** — When calories change, reduce carbs:fats at 1:1 to 2:1 ratio, maintain protein.
12. **Remove somatotype-based adjustments** — Replace with evidence-based individualization.

### 🟢 Nice-to-Have

13. Implement Hall's mathematical body model for calorie deficit timelines
14. Add BFR training exercises to the exercise library
15. Implement "Before You Count" assessment (10 big wins scoring)
16. Add female menstrual cycle tracking for weight interpretation
17. Implement keto tolerance testing protocol (4-week trial with mood/energy/training ratings)
18. Add NEAT tracking with step count monitoring
19. Implement outlier detection for adaptive TDEE
20. Add data quality indicators and confidence scoring

---

## 14. WHAT THE REPOSITORY GETS RIGHT (Strengths)

1. **The adjustment checklists are exceptional** — calorie reduction correctly positioned as the LAST resort for both cutting and bulking
2. **Protein set by lean mass, not ratio** — correctly implements the "no best macro ratio" principle
3. **Equipment as HARD filter** — never prescribes infeasible exercises
4. **Deterministic and explainable** — every output has a rationale
5. **Visual BF estimation as fallback** — practical and aligned with RippedBody's approach
6. **Self-estimate BF correction (+50%)** — correctly addresses the systematic underestimation bias
7. **Comprehensive exercise library with regression/progression chains** — practical and scalable
8. **Proper meal portion scaling** — avoids the greedy allocation bug
9. **Training volume reduction during cuts** — correctly preserves intensity while cutting volume
10. **Excellent test coverage** — 52 passing tests across all calculator modules
11. **Anti-supplement philosophy** — correctly positions supplements at the bottom of the hierarchy
12. **The 9 trainee categories** — practical, evidence-based classification system
13. **BFR mention for joint pain** — shows awareness of clinical training methods
14. **NEAT awareness** — recognizes that activity levels change during dieting
15. **Wait period before assessment** — correctly advises waiting 3-4 weeks before adjusting calories

---

## 15. REMEDIATION STATUS (Applied in this workspace)

The priority findings above have been acted on in the codebase. See `../reports/remediation-report.md` for the implementation matrix and verification commands.

### Fixed / implemented

1. **Mifflin-St Jeor is now the default BMR formula** in `energy_expenditure()`; Harris-Benedict remains available as a comparison/fallback function.
2. **Activity multipliers now match the reference guide** using the existing 4-tier enum: 1.25 / 1.45 / 1.60 / 1.80.
3. **Sex-specific calorie floors are enforced**: 1500 kcal for men and 1200 kcal otherwise when `sex` is supplied.
4. **Alpert's maximum fat-loss safeguard has been added** when body-fat or lean-mass data is available.
5. **Visual body-fat bands now use sex-specific guide-aligned ranges**.
6. **Somatotype-based fat macro adjustment has been removed**; macro defaults no longer vary by body-type taxonomy.
7. **Normalized FFMI coefficient has been corrected to 6.3**.
8. **Hydration now uses the guide formula**: 30 ml/kg, optional +300 ml for men, plus workout fluid.
9. **Anthropometric indices added**: WHtR, WHR, ABSI, and Devine IBW.
10. **Macro adjustment helper added**: protein preserved, carbs/fats changed at a practical 1:1–2:1 calorie split, rounded to 5 g.
11. **Adaptive TDEE helper added** with complete-day filtering, outlier exclusion, trend-weight comparison, formula blending, and confidence labels.
12. **Reverse dieting protocol added** with conservative/moderate/aggressive weekly calorie increases and monitoring rules.
13. **Cardio prescription now respects the reference-guide interference cap**: cardio remains below half of weekly lifting time.
14. **Goal/strategy conflicts are surfaced** by the recommender when the selected goal differs from the body-composition decision-tree recommendation.
15. **Regression tests added** for the corrected behaviours.

### Verification

```bash
python3 -m unittest tests.test_calculators tests.test_integration
# Ran 80 tests — OK

bash examples/run_all.sh
# All checks complete
```

### Not fully implemented because they require a broader product/app layer

- Verified food database, barcode scanning, recipe builder, custom food storage.
- Progress-photo storage and trend visualization.
- Full longitudinal 9-point body-measurement tracking.
- Wearable/step-count integrations.
- Keto trial workflow with daily mood/energy/training ratings.
- Female menstrual-cycle-aware trend interpretation.
- Full diet-mode expansion (keto, Mediterranean, vegetarian, gluten-free, paleo, low-carb) with matching meal-library coverage.

### Second-pass remediation update

The following additional analysis findings have now been addressed in code:

- Completed the activity model with `moderately_active` and `very_active`.
- Added body-fat-aware fat-loss rates plus Alpert deficit capping.
- Added executable bulk/cut/recomp phase decision tree.
- Added optional macro cycling.
- Expanded diet modes beyond omnivore/vegan and added diet-mode-aware macro presets.
- Added meal compatibility and extra tagged meals so every supported diet mode can assemble a plan.
- Added explicit comprehensive exercise and meal protocol builders for every archetype/profile combination in `fitness_engine/protocols.py`.
- Added protocol output to `PlanRecommendation` as `rec.protocols`.
- Added tests for every enumerated archetype signature at the protocol level and every diet mode at the meal-plan level.
- Upgraded progress tracking guidance to full 9-point measurements, monthly photos, and strength logging.

Verification now passes with `79` tests plus the full demo script.
