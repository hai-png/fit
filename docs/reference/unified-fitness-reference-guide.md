# Unified Fitness Reference Guide
## Evidence-Based Nutrition, Training & Body Composition

> **Sources Synthesized:** RippedBody.com (25 articles), MacroFactor.com (3 articles), FatCalc.com (5 calculators), GymGeek.com (4 calculators), ZoltHealth.com (1 article), UltimatePerformance.com (1 article), BuiltWithScience.com (1 quiz)
>
> **Compiled:** June 2026
> **Purpose:** Single-source-of-truth reference for the Fitness Engine v2.4.0

---

## Table of Contents

1. [The Nutrition Hierarchy of Importance](#1-the-nutrition-hierarchy-of-importance)
2. [Calories & Energy Balance](#2-calories--energy-balance)
3. [Macronutrients: Protein, Fat, Carbs](#3-macronutrients-protein-fat-carbs)
4. [Body Fat Assessment](#4-body-fat-assessment)
5. [Micronutrients & Hydration](#5-micronutrients--hydration)
6. [Goal Setting & Trainee Classification](#6-goal-setting--trainee-classification)
7. [Cutting (Fat Loss) Protocol](#7-cutting-fat-loss-protocol)
8. [Bulking (Muscle Gain) Protocol](#8-bulking-muscle-gain-protocol)
9. [Body Recomposition](#9-body-recomposition)
10. [Adaptive TDEE & Metabolic Adaptation](#10-adaptive-tdee--metabolic-adaptation)
11. [Weight Fluctuations & Progress Tracking](#11-weight-fluctuations--progress-tracking)
12. [Training Plateaus](#12-training-plateaus)
13. [Adjustment Protocols](#13-adjustment-protocols)
14. [Special Diets: Keto & Vegan](#14-special-diets-keto--vegan)
15. [Maximum Muscular Potential](#15-maximum-muscular-potential)
16. [Calculator Reference](#16-calculator-reference)
17. [Anthropometric Health Indices](#17-anthropometric-health-indices)

---

## 1. The Nutrition Hierarchy of Importance

*Source: RippedBody.com — "How To Set Up Your Diet: The Nutrition Hierarchy of Importance"*

The fitness industry inverts the true hierarchy of nutritional importance, selling supplements (the least impactful layer) while ignoring calories (the most impactful). The correct hierarchy, adapted from Dr. Eric Helms' model, is:

### Order of Priority (Most → Least Important)

1. **Calories** — Energy balance (calories in vs. calories out) is the primary driver of weight change. A deficit causes weight loss; a surplus causes weight gain. This is immutable physics.

2. **Macronutrients** — Protein, carbohydrates, and fat distribution. Protein is the most critical macro for body composition — it preserves muscle during cuts and drives growth during bulks.

3. **Micronutrients** — Vitamins, minerals, and fiber. Deficiency impairs performance and health but excess provides no benefit above sufficiency.

4. **Nutrient Timing** — Meal timing, pre/post-workout nutrition. Timing matters far less than total daily intake. The "anabolic window" is wider than commonly believed (24-48 hours, not 30 minutes).

5. **Supplements** — The least impactful layer. Most supplements do nothing; a few (creatine, caffeine, vitamin D) have modest evidence. Supplements cannot compensate for poor calorie or macro compliance.

### Key Design Principles

- **Simplicity over complexity** — Follow the simplest path that works before adding tracking complexity.
- **Evidence-based** — All recommendations backed by peer-reviewed research, not marketing.
- **Anti-scam stance** — Actively debunk industry myths (carb-phobia, magic supplements, "anabolic windows").
- **Sustainable habits** — Focus on long-term adherence, not short-term extremes. The best diet is the one you can stick to for 12+ weeks.

---

## 2. Calories & Energy Balance

*Sources: RippedBody.com ("How To Set Your Calorie Intake"), MacroFactor.com, GymGeek.com, FatCalc.com, ZoltHealth.com*

### The CICO Equation

**Fundamental Law:** Calories In vs. Calories Out (CICO) is the primary driver of weight change.

| State | Calories In vs. TDEE | Result |
|-------|---------------------|--------|
| Deficit | In < Out | Weight loss |
| Maintenance | In = Out | Weight stability |
| Surplus | In > Out | Weight gain |

### Components of TDEE

- **Basal Metabolic Rate (BMR)** — Calories burned at complete rest. Accounts for 60-70% of TDEE.
- **Thermic Effect of Food (TEF)** — Energy to digest food. ~10% of TDEE. Protein has the highest TEF (~20-30% of its calories).
- **Non-Exercise Activity Thermogenesis (NEAT)** — Fidgeting, walking, daily movement. Highly variable (100-800 kcal/day between individuals). **Critical insight:** NEAT drops during dieting (adaptive thermogenesis), which is a major cause of fat-loss plateaus.
- **Exercise Activity Thermogenesis (EAT)** — Structured exercise. Typically 200-600 kcal/session.

### BMR Formulas (Ranked by Accuracy)

1. **Mifflin-St Jeor** (engine default) — Best general-purpose formula. ~10-15% error range.
   - Men: `BMR = 10×kg + 6.25×cm - 5×age + 5`
   - Women: `BMR = 10×kg + 6.25×cm - 5×age - 161`

2. **Katch-McArdle** — Requires lean body mass. Best for lean individuals.
   - `BMR = 370 + 21.6 × lean_mass_kg`

3. **Harris-Benedict** (original, 1919) — Oldest, least accurate for modern populations. Retained for comparison only.

### Activity Multipliers

| Level | Multiplier | Description |
|-------|-----------|-------------|
| Sedentary | 1.25 | <5k steps, desk job |
| Mostly Sedentary | 1.45 | <5k steps + lifting |
| Lightly Active | 1.55 | 5-10k steps + training |
| Moderately Active | 1.60 | 5-10k steps + training (midpoint) |
| Highly Active | 1.80 | 10k+ steps + training |
| Very Active | 1.90 | Physical job + training |

### Calorie Target Calculation

**Fat Loss (Cut):**
- Target deficit: 0.25-1.0% body weight/week (body-fat-dependent)
- Default rate: 0.75% BW/week
- Formula: `TDCI = TDEE - (BW × rate × 1100)` where 1100 ≈ kcal per kg fat
- **Alpert safeguard:** Maximum daily deficit = fat_mass_lb × 22 kcal. Prevents excessive lean-mass loss in very lean individuals.

**Muscle Gain (Bulk):**
- Target surplus: 0.5-2% body weight/month (experience-dependent)
- Beginner: 2% BW/month; Intermediate: 1%; Advanced: 0.5%
- Formula: `TDCI = TDEE + (BW × monthly_rate × 330)` where 330 ≈ kcal per kg gain/month
- NEAT buffer: 50% added to compensate for NEAT rise during surplus

**Recomposition:** TDCI = TDEE (maintenance)

**Strength:** TDCI = TDEE × 1.02 (very slight surplus)

### Safety Floor
- Women: ≥1200 kcal/day
- Men: ≥1500 kcal/day
- Below these floors, medical supervision is required.

---

## 3. Macronutrients: Protein, Fat, Carbs

*Sources: RippedBody.com ("Best Macro Ratio", "How to Count Macros"), FatCalc.com*

### Why the "Best" Macro Ratio Does Not Exist

There is no universally optimal macronutrient ratio. The "best" ratio depends on:
- Individual preferences and adherence
- Training demands
- Body composition goals
- Diet mode (keto, Mediterranean, etc.)

The RippedBody approach sets macros **in order of priority**, not by ratio:

### 1. Protein (Set First)

Protein is the most critical macro for body composition. It preserves muscle during cuts and drives growth during bulks.

| Scenario | Multiplier | Basis |
|----------|-----------|-------|
| Cutting, BF% known, omnivore (lean, BF≤12%) | 2.8 g/kg | Lean mass |
| Cutting, BF% known, omnivore (BF>12%) | 2.5 g/kg | Lean mass |
| Cutting, BF% known, vegan | 2.6 g/kg | Lean mass |
| Cutting, BF% unknown, omnivore | 2.2 g/kg | Target BW |
| Cutting, BF% unknown, vegan | 2.6 g/kg | Target BW |
| Bulk/Recomp, BF% known, omnivore | 2.2 g/kg | Lean mass |
| Bulk/Recomp, BF% known, vegan | 2.6 g/kg | Lean mass |
| Bulk/Recomp, BF% unknown, omnivore | 1.6 g/kg | Body weight |
| Bulk/Recomp, BF% unknown, vegan | 2.2 g/kg | Body weight |

**Vegan note:** Plant protein is less well absorbed and has lower BCAA/leucine content. Vegan targets are set higher to compensate.

**High-protein preset:** Floor of 2.2 g/kg BW, applied after the initial calculation.

### 2. Fat (Set Second)

Fat is set as a percentage of total calories, with minimums:

| Scenario | Fat % of Calories |
|----------|------------------|
| Cutting | 20% (range: 15-25%) |
| Bulking | 25% (range: 20-30%) |
| Low-carb diet | 40% |
| Mediterranean diet | 35% |
| Paleo diet | 35% |
| Keto diet | Fat fills remaining calories |

**Minimum fat floor:** 0.5 g/kg body weight. Below this, hormonal function may be impaired.

### 3. Carbohydrates (Fill the Remainder)

Carbs fill the remaining calorie budget after protein and fat are set.

**Minimum carb floor:** 1.0 g/kg body weight (unless explicitly low-carb/keto). Below this, training performance suffers.

### Keto Exception

For keto, carbs are capped at <50 g/day (generally ~8% of calories), protein is set first, and fat fills the remainder.

### Macro Adjustment Rules

When adjusting calories:
- **Preserve protein** — never reduce protein to cut calories.
- **Split the change across carbs and fat** at approximately 2:1 (carbs:fats) by calories.
- **Round to practical 5 g increments** for manual adjustments; 1 g for macro cycling.

---

## 4. Body Fat Assessment

*Sources: RippedBody.com ("Body-Fat Guide", "How to Calculate Body Fat"), UltimatePerformance.com, FatCalc.com*

### Visual Body-Fat Estimation

When tape measurements aren't available, visual comparison is the most practical method.

#### Male Body-Fat Bands

| Label | Range | Midpoint | Description |
|-------|-------|----------|-------------|
| Shredded | 7-10% | 8.5% | Competition-ready; striations visible |
| Very Lean | 10-12% | 11.0% | Cover-model lean; clear abs |
| Lean | 12-15% | 13.5% | Athletic; blurry six-pack |
| Average Fit | 15-18% | 16.5% | Some definition; abs not clearly visible |
| Soft | 18-21% | 19.5% | Average; no visible abs |
| Overweight | 21-25% | 23.0% | Significant fat layer |
| Obese | 25-40%+ | 30.0% | Heavy fat accumulation; health risk |

#### Female Body-Fat Bands

| Label | Range | Midpoint | Description |
|-------|-------|----------|-------------|
| Shredded | 14-17% | 15.5% | Competition-ready (very lean for women) |
| Very Lean | 17-20% | 18.5% | Fitness-model lean |
| Lean | 20-23% | 21.5% | Athletic; clear shape |
| Average Fit | 23-27% | 25.0% | Fit/average; some definition |
| Soft | 27-32% | 29.5% | Average; softer appearance |
| Overweight | 32-37% | 34.5% | Substantial fat accumulation |
| Obese | 37-50%+ | 40.0% | Health risk rises |

### Self-Estimate Correction

> "Most people underestimate their body-fat percentage. If you haven't cut down to see your abs before and you are trying to estimate how much fat you have to lose, add 50% to your estimate." — RippedBody

Formula: `corrected_bf = bf_estimate × 1.5` (clamped to [2, 55]%)

### Navy Body-Fat Formula (Hodgdon & Beckett, 1984)

**Male:** `BF% = 495 / (1.0324 - 0.19077 × log10(waist - neck) + 0.15456 × log10(height)) - 450`

**Female:** `BF% = 495 / (1.29579 - 0.35004 × log10(waist + hip - neck) + 0.22100 × log10(height)) - 450`

- Male: waist > neck required
- Female: hip required; waist + hip > neck required
- Results clamped to [2, 60]%

### Deurenberg BMI Method (Fallback)

`BF% = 1.20 × BMI + 0.23 × age - 10.8 × sex_coef - 5.4`

Where sex_coef = 1 for male, 0 for female. Clamped to [2, 60]%.

### Priority Order for Body-Fat Estimation

1. User-supplied BF% (most trusted, if from DEXA/hydrostatic)
2. Navy formula (if waist + neck measurements available)
3. Visual estimation (if visual_bf_label provided)
4. Deurenberg BMI method (automatic fallback)

---

## 5. Micronutrients & Hydration

*Source: RippedBody.com ("How To Cover Your Micronutrient Needs")*

### Fruit and Vegetable Targets

| Daily Calories | Fruit (cups) | Vegetables (cups) |
|----------------|-------------|-------------------|
| 1200-2000 | 2 | 2 |
| 2000-3000 | 3 | 3 |
| 3000-4000 | 4 | 4 |

### Fiber Target

**14 g per 1000 kcal** — based on USDA Dietary Guidelines.

| Calories | Fiber Target |
|----------|-------------|
| 1500 | 21 g |
| 2000 | 28 g |
| 2500 | 35 g |
| 3000 | 42 g |
| 3500 | 49 g |

### Hydration

- **Base:** 30 ml/kg body weight
- **Sex adjustment:** +300 ml for men (higher average lean mass)
- **Exercise bonus:** 350 ml per 30 minutes of exercise
- **Practical guidance:**
  - Aim to be peeing clear by noon
  - Have five clear urinations a day
  - Don't begin training dehydrated
  - Taper water toward evening to avoid sleep disruption

### Multivitamin Stance

> "Do not treat multivitamins as a substitute for fruit, vegetables, and varied whole foods." — RippedBody

Multivitamins are insurance, not a replacement. Whole foods provide fiber, phytonutrients, and satiety that pills cannot.

---

## 6. Goal Setting & Trainee Classification

*Sources: RippedBody.com ("9 Categories of Trainee", "Should I Bulk vs Cut"), MacroFactor.com ("Bulk or Cut?")*

### The 9 Categories of Trainee

RippedBody classifies trainees into 9 categories based on body-fat percentage and training experience:

| Category | Description | Strategy |
|----------|-------------|----------|
| **Skinny** | Low muscle, low BF | Bulk |
| **Fat But Muscled** | Muscular + high BF | Cut |
| **Muscled Lean** | Muscled, few lbs to lose | Cut |
| **Shredded** | Defined abs | Maintenance / Slow bulk |
| **Fat and Weak** | High BF, new to training | Cut + newbie gains |
| **Obese** | Very high BF | Habit change + cut |
| **Skinny-Fat** | Low muscle + moderate-high BF | Recomp or gentle bulk |
| **Purgatory** | Stuck spinning wheels | Commit to one phase |
| **New Trainee Healthy** | Healthy BW, new to training | Recomp |

### Cut/Bulk Decision Boundaries

| Sex | End Cut (BF%) | End Bulk (BF%) |
|-----|-------------|-------------|
| Male | 10% | 20% |
| Female | 18% | 28% |

**Decision tree:**
1. If BF% > upper boundary → **Cut** first while lifting.
2. If BMI < 18.5 or (BF% < lower threshold and BMI < 22) → **Bulk** with controlled surplus.
3. If beginner with healthy BW → **Recomp** is realistic.
4. Otherwise → Follow user preference, but flag mismatches.

### Body-Fat-Aware Fat-Loss Rates

| Male-Equiv BF% | Weekly Loss Rate | Rationale |
|----------------|-----------------|-----------|
| ≤12% | 0.4% BW/wk | Leaner trainees must cut slower to preserve muscle |
| 13-18% | 0.6% BW/wk | Moderate rate |
| 19-28% | 0.75% BW/wk | Default RippedBody rate |
| >28% | 1.0% BW/wk | Higher BF tolerates faster cuts |

*(Female BF% adjusted by subtracting 8% for male-equivalent comparison.)*

---

## 7. Cutting (Fat Loss) Protocol

*Sources: RippedBody.com ("How to Adjust Macros"), MacroFactor.com ("Cutting Calculator")*

### Setup

1. Set calories at TDEE minus the calculated deficit
2. Set protein first (2.2-2.8 g/kg lean mass, diet-dependent)
3. Set fat at ~20% of calories (15-25% range)
4. Carbs fill the remainder
5. Cap cardio at <50% of weekly lifting time
6. Diet drives the deficit; resistance training preserves muscle

### Expected Results

- **Weekly loss:** 0.5-1.0% body weight (body-fat-dependent)
- **First week:** Ignore — water/glycogen shifts dominate
- **Assessment window:** 3-4 weeks before adjusting

### Alpert Maximum Fat-Loss Safeguard

Maximum daily deficit (kcal) = fat_mass_lb × 22

This prevents the engine from prescribing a deficit so large it forces lean-mass loss. For very lean trainees, the Alpert cap will reduce the deficit below the target rate — this is correct and safe.

---

## 8. Bulking (Muscle Gain) Protocol

*Sources: RippedBody.com ("How to Bulk", "Updated Bulking Guidelines", "How to Adjust Macros — Bulk"), MacroFactor.com ("Bulking Calculator")*

### Experience-Tiered Gain Rates

| Experience | Monthly Gain Rate | Daily Surplus (approx.) |
|------------|------------------|------------------------|
| Beginner | 2% BW/month | ~300-500 kcal |
| Intermediate | 1% BW/month | ~150-250 kcal |
| Advanced | 0.5% BW/month | ~75-125 kcal |

### Key Principles

1. **Train hard and often enough** — The body needs a stimulus to grow. 3-4 sessions/week of progressive compound lifting.
2. **Eat a sufficient surplus** — Enough to grow, but not so much you gain excess fat.
3. **Track weight** — Weekly average. Gain rate should match the tier above.
4. **Expect initial jump** — Week 1 will show 1-3 kg of water/glycogen weight. This is not fat. Judge the trend after 2-3 weeks.
5. **NEAT rises during a bulk** — The body subconsciously moves more when fed more. The 50% buffer compensates for this.

### What to Do If Gaining Too Fast

1. Are you tracking accurately?
2. Are you feeling too full? (Swap whole food for liquid calories)
3. Is your food environment set up?
4. Have you revisited your "why"?
5. Is stress under control?
6. Are you sleeping 7+ hours?
7. Has NEAT increased? (Don't restrict — just eat more)
8. Have you waited 5 weeks?
9. **Last resort:** Decrease by ~5% calories (150-200 kcal). Add mostly carbs. Wait 5 weeks.

### What to Do If Not Gaining

1. Are you tracking accurately? (Under-eating is common)
2. Are you feeling too full?
3. Is your food environment set up?
4. Have you revisited your "why"?
5. Is stress under control?
6. Are you sleeping 7+ hours?
7. Has NEAT increased?
8. Have you waited 5 weeks?
9. **Last resort:** Increase by ~5% calories (150-200 kcal). Add mostly carbs. Wait 5 weeks.

---

## 9. Body Recomposition

*Source: RippedBody.com ("Cut or Bulk", Goal Setting series)*

### Who Can Recomp

Recomposition (simultaneous fat loss + muscle gain) is realistic for:
- **Beginners** with healthy body weight
- **Overweight beginners** (newbie gains + fat loss)
- **Returning trainees** (muscle memory)
- **Detrained individuals** (after a break)

### Who Cannot Recomp Effectively

- **Intermediate/Advanced trainees** — Need dedicated cut/bulk phases
- **Very lean individuals** — Little fat to mobilize
- **Very muscular individuals** — Near genetic ceiling

### Calorie Target for Recomp

- Start at **maintenance** (TDEE)
- High protein (2.0-2.2 g/kg lean mass)
- Track photos, measurements, and strength — **not just scale weight**
- Expect slow changes: 0.5-1% BW/month recomp
- Be patient — recomp takes 8-16 weeks to show visible results

---

## 10. Adaptive TDEE & Metabolic Adaptation

*Sources: ZoltHealth.com ("What is Adaptive TDEE"), GymGeek.com, GymCreek.com, FatCalc.com*

### What Is Metabolic Adaptation?

When you diet, your metabolism slows to fight the calorie deficit. This is called **metabolic adaptation** (or adaptive thermogenesis). It reduces TDEE by **15-25%** during prolonged calorie restriction.

### Causes

1. **NEAT reduction** — The body subconsciously reduces fidgeting, movement, and posture
2. **BMR reduction** — Thyroid hormones decrease; lean mass may decrease
3. **TEF reduction** — Less food eaten = less thermic effect
4. **Hormonal adaptation** — Leptin drops, ghrelin rises, cortisol rises

### Mitigation Strategies

1. The 0.75% BW/week fat-loss rate **pre-accounts** for adaptation (slower than many apps prescribe)
2. **Diet breaks** every 6-8 weeks (eat at maintenance for 1-2 weeks)
3. **Don't reduce calories proactively** — wait until weight-loss rate actually slows
4. **Track steps/NEAT** — it drops during a cut; maintain a daily minimum (5,000-8,000)
5. **Use adaptive TDEE** when 14+ days of intake + weight logs exist
6. **Reverse diet** after extended cuts to restore metabolic rate

### Adaptive TDEE Calculation

**Formula:** `observed_TDEE = avg_intake - (weight_change × kcal_per_kg / days)`

Where `kcal_per_kg` = 7700 (traditional) or 7200-7500 (Hall 2008, more accurate for fat loss).

**Blending:** `adaptive_TDEE = formula_TDEE × (1 - weight) + observed_TDEE × weight`

Where `weight` increases with data sufficiency:
- <14 days: use formula only (confidence: low)
- 14-27 days: 25% observed (confidence: low)
- 28-41 days: 50% observed (confidence: medium)
- 42+ days: 80% observed (confidence: high)

### Reverse Dieting

After an extended cut, gradually increase calories back to maintenance:
- **Conservative:** +50 kcal/week
- **Moderate:** +100 kcal/week (default)
- **Aggressive:** +150 kcal/week

**Monitoring:**
- Track daily weight, compare weekly averages
- Some water/glycogen weight gain is normal
- If weekly average rises >0.5% BW/week, pause or halve increases
- Maintain training intensity and protein

---

## 11. Weight Fluctuations & Progress Tracking

*Sources: RippedBody.com ("Why is My Weight Going Up and Down", "Diet Progress Tracking", "Initial Adjustment")*

### Why Weight Fluctuates

Weight loss is **never linear**. Expect stalls and "whooshes":

1. **Water retention** — Stress, poor sleep, high sodium, and hormonal changes can mask fat loss for 1-2 weeks
2. **Glycogen** — Carbohydrate restriction drops glycogen (and its bound water) rapidly in week 1
3. **The "whoosh" effect** — Fat cells empty of fat but fill with water temporarily, then release suddenly
4. **Bowel content** — Food residue and fiber can add 0.5-1.5 kg
5. **Menstrual cycle** — Women may see 1-3 kg water retention in the luteal phase

### How to Track Progress

#### Weight Tracking
- Weigh yourself **every morning**, after bathroom, before eating/drinking
- Use the **weekly average** — never individual days
- **Ignore the first week** after starting/changing a diet (water shifts dominate)
- Don't change calories until 3-4 weeks of trend data exist

#### Measurement Tracking
- Measure **9 points** weekly: chest at nipple line; L/R upper arm; L/R thigh; stomach at navel, 3 fingers above, and 3 fingers below
- Use a non-stretch tape, same time of day (morning is best)
- Measurements confirm tissue change when scale is stable (especially during recomp)

#### Photo Tracking
- Monthly photos in **same lighting, distance, poses, and time of day**
- Use photos as a recomp indicator, not day-to-day mirror checks

#### Strength Tracking
- Log exercises, sets, reps, load, and RIR/RPE
- Strength trends over weeks; short-term dips are common during cuts
- If strength holds during a cut, you're preserving muscle

### Initial Assessment (First 3-4 Weeks)

1. Wait 3-4 weeks before assessing — ignore week 1
2. If weight changes **faster** than expected:
   - Cut: losing >1% BW/wk → increase calories by 200-250
   - Cut: losing <0.5% BW/wk (after wk 2) → decrease by 200-250
   - Bulk: gaining >2% BW/month → decrease by 150 kcal
   - Bulk: gaining <0.5% BW/month (after wk 3) → increase by 150 kcal
3. If on track → continue for another 4-6 weeks before re-assessing

---

## 12. Training Plateaus

*Source: RippedBody.com ("How to Break Training Plateaus")*

### Decision Tree Checklist

| Step | Check | Action |
|------|-------|--------|
| 1 | Sleeping 7+ hours? | Sleep deprivation impairs recovery, reduces strength, blunts hypertrophy |
| 2 | Eating enough? | Can't build from nothing; leaner + more experienced = harder at maintenance |
| 3 | Enough protein? | Minimum 1.6 g/kg; more if dieting (2.2+ g/kg) |
| 4 | Training hard/too hard? | Overestimating RPE = not close enough to failure; underestimating = too much fatigue |
| 5 | Hitting each muscle 2×/wk? | Frequency ≥2×/wk optimizes hypertrophy |
| 6 | Technique sound? | Poor form cheats progress; film yourself, get coaching |
| 7 | Joint/tendon pain? | Increase reps to 12-20 on painful movements; consider BFR |
| 8 | Volume appropriate? | Stalled → try +1-2 sets per exercise; fatigued → reduce 20-30% or deload |

---

## 13. Adjustment Protocols

*Sources: RippedBody.com ("How to Adjust Macros" for cut and bulk), FatCalc.com*

### Cut Adjustment Checklist (In Order)

**Reduce calories as the LAST resort.** Work through these first:

1. Are you tracking accurately? (Weigh food, log everything)
2. Are you managing hunger? (Swap liquid calories, cut palatable foods, eat more veg/fruit/salad/soup)
3. Is your food environment managed? (Clear junk from house, stock good foods)
4. Have you revisited your "why"? (Emotional connection sustains motivation)
5. Is stress under control? (Stress causes water retention, impairs recovery)
6. Are you sleeping 7+ hours? (Poor sleep mimics stress effects)
7. Has daily activity (steps) decreased? (NEAT drops during a cut — check step count)
8. Have you waited long enough? (3-4 weeks of data; stalls can last 1-2 weeks)
9. Can you add cardio instead of cutting food? (Zone-2 before reducing calories)
10. **Last resort: reduce calories by ~200-250 kcal.** Reduce from carbs first (and fat if already low). Never reduce protein. Wait 3-4 weeks.

### Bulk Adjustment Checklist

1. Are you tracking accurately? (Under-eating is common for hard gainers)
2. Are you feeling too full? (Swap to liquid calories, eat faster, add breakfast)
3. Is your food environment set up? (Stock calorie-dense foods: nuts, dried fruit, oils)
4. Have you revisited your "why"? (Bulking is a chore)
5. Is stress under control? (Stress causes more fat, less muscle from surplus)
6. Are you sleeping 7+ hours? (Poor sleep kills gains)
7. Has NEAT increased? (Don't restrict — just eat more)
8. Have you waited 5 weeks? (Initial jump is water, then it slows)
9. **Last resort: increase by ~5% (150-200 kcal).** Add mostly carbs. Wait 5 weeks.

---

## 14. Special Diets

### Keto

*Source: RippedBody.com ("How to Systematically Test if Keto is Right for You")*

**Key principles:**
- Carbs generally <50 g/day
- Protein set first (same as non-keto)
- Fat fills remaining calories
- Use as a **preference/tolerance mode**, not because ketosis is superior for fat loss when calories are matched
- Run a **4-week trial** and rate mood, energy, hunger, and training performance daily
- **Supplement:** sodium (3000-5000 mg/day in early keto), magnesium (200-400 mg/day), potassium (1000-3500 mg/day) to prevent "keto flu"

### Vegan

*Source: RippedBody.com ("Optimizing Vegan Diets for Performance and Muscle Growth")*

**Key adjustments:**
- Protein targets set **higher** (2.6 g/kg lean mass for cutting, 2.6 g/kg for bulk/recomp)
- Combine plant proteins (rice + pea, soy + legumes) for complete amino acid profiles
- Consider pea/rice protein blends
- **Mandatory supplements:** Vitamin B12 (1000 mcg, 2-3×/week)
- **Recommended supplements:** Vitamin D3 (1000-2000 IU/day), algae omega-3 EPA/DHA (250-500 mg/day), creatine monohydrate (5 g/day — not found in plant foods)
- **Conditional:** Iron (if ferritin low), zinc (8-11 mg/day — phytates reduce absorption), calcium (1000 mg/day if not met by food)
- Iron from plant sources is less well absorbed — pair with vitamin C-rich foods, avoid coffee/tea around meals

---

## 15. Maximum Muscular Potential

*Source: RippedBody.com ("Maximum Muscular Potential")*

### Berkhan Model

Stage-shredded maximum bodyweight (kg) = height_cm - 100

This is the maximum bodyweight at ~5-6% body fat for a drug-free male.

### FFMI (Fat-Free Mass Index)

`FFMI = lean_mass_kg / height_m²`

**Normalized FFMI** (adjusted to 1.8 m): `FFMI + 6.3 × (1.8 - height_m)`

| Normalized FFMI | Category |
|----------------|----------|
| <18 | Below average |
| 18-20 | Average |
| 20-22 | Above average |
| 22-23 | Excellent |
| 23-25 | Superior |
| 25-26 | Suspicious (possible PED use) |
| >26 | Highly suspicious (likely PED use) |

**Natural ceiling:** ~25 FFMI

---

## 16. Calculator Reference

### MacroFactor

- **Bulk or Cut?** — Decision tree based on body fat, experience, and preference
- **Cutting Calculator** — Maximum safe fat-loss rate based on body fat percentage
- **Bulking Calculator** — Experience-tiered weight gain rates (2%/1%/0.5% per month)

### FatCalc.com Calculators

| Calculator | Purpose | Key Formula |
|-----------|---------|-------------|
| Macro | Macro calculator with 11 diet types | Mifflin BMR × activity × goal modifier |
| MFL (Max Fat Loss) | Maximum fat loss rate | Alpert formula: fat_mass_lb × 22 kcal/day max deficit |
| ABSI | Body shape health risk | ABSI = WC(m) × weight(kg)^(-2/3) × height(m)^(5/6) |
| Reverse Diet | Post-diet calorie restoration | Weekly increments of 50/100/150 kcal |
| BF | Body fat calculator | Navy formula with multiple methods |
| WHtR | Waist-to-height ratio | WC / height; <0.5 = healthy |
| WHR | Waist-to-hip ratio | WHO thresholds: 0.90 (M) / 0.85 (F) |
| Hydration | Daily water target | Weight-based + exercise bonus |
| Protein | Protein target calculator | 0.8-2.2+ g/kg depending on goal |
| RMR | Resting metabolic rate | Mifflin-St Jeor |
| TDEE | Total daily energy expenditure | RMR × activity multiplier |
| IBW | Ideal body weight (Devine) | 50 + 2.3 × (height_in - 60) for males |
| BWP | Body weight planner | Energy balance modeling |
| RWL | Rapid weight loss | Time-limited aggressive deficit |
| MM | Macronutrient mass | Gram-to-calorie conversion |
| BFB | Body fat % from BMI | Deurenberg formula |
| Body Recomp | Recomposition calculator | Maintenance ± small adjustment |

### GymGeek.com Calculators

- **Maintenance Calories** — TDEE calculator
- **Calorie Calculator** — Goal-adjusted calorie targets
- **Adaptive TDEE** — Trend-based TDEE from weight/intake logs
- **Bulking Calculator** — Surplus calculator

### ZoltHealth.com

- **Adaptive TDEE Guide** — Explains metabolic adaptation, 15-25% TDEE reduction during dieting, and the importance of trend-based calculation over formula-based

---

## 17. Anthropometric Health Indices

*Sources: FatCalc.com (ABSI, WHtR, WHR, IBW), WHO standards*

### Waist-to-Height Ratio (WHtR)

`WHtR = waist_cm / height_cm`

| WHtR | Category |
|------|----------|
| <0.5 | Healthy |
| 0.5-0.6 | Increased risk |
| >0.6 | Substantially increased risk |

**Rule of thumb:** Keep your waist less than half your height.

### Waist-to-Hip Ratio (WHR)

`WHR = waist_cm / hip_cm`

| WHR | Male | Female |
|-----|------|--------|
| Healthy | <0.90 | <0.85 |
| Elevated risk | 0.90-1.0 | 0.85-1.0 |
| High risk | >1.0 | >1.0 |

*Source: WHO 2008, "Waist Circumference and Waist-Hip Ratio"*

### ABSI (A Body Shape Index)

`ABSI = WC(m) × weight(kg)^(-2/3) × height(m)^(5/6)`

**ABSI z-score** (vs. population reference, Krakauer & Krakauer 2012):

| z-score | Category |
|---------|----------|
| <-0.5 | Below average risk |
| -0.5 to +0.5 | Average risk |
| +0.5 to +1.5 | Elevated risk |
| >+1.5 | High risk |

### Devine Ideal Body Weight

`IBW = base + 2.3 × max(0, height_inches - 60)`

Where base = 50 kg (male) or 45.5 kg (female).

---

## Appendix A: Source Attribution

| Source | Articles | Primary Topics |
|--------|----------|---------------|
| RippedBody.com | 25 | Nutrition pyramid, calories, macros, body fat, micros, keto, vegan, goal setting, cut/bulk, adjustments, plateaus, progress tracking, muscular potential |
| MacroFactor.com | 3 | Bulk-or-cut decision, cutting rate, bulking rate |
| FatCalc.com | 17 | Macro, fat loss, ABSI, reverse diet, body fat, WHtR, WHR, hydration, protein, RMR, TDEE, IBW, recomp |
| GymGeek.com | 4 | Maintenance calories, calorie calculator, adaptive TDEE, bulking |
| ZoltHealth.com | 1 | Adaptive TDEE explanation |
| UltimatePerformance.com | 1 | Male body fat comparison |
| BuiltWithScience.com | 1 | Fitness quiz reference |

---

## Appendix B: Key Formulas Summary

```
BMR (Mifflin-St Jeor):
  Men:   10×kg + 6.25×cm - 5×age + 5
  Women: 10×kg + 6.25×cm - 5×age - 161

BMR (Katch-McArdle):
  370 + 21.6 × lean_mass_kg

TDEE:
  BMR × activity_multiplier

Calorie Target (Fat Loss):
  TDEE - (BW × rate × 1100)
  Alpert cap: fat_mass_lb × 22

Calorie Target (Muscle Gain):
  TDEE + (BW × monthly_rate × 330 × 1.5)

Protein (cutting, lean mass known):
  Omnivore: 2.5 g/kg lean (2.8 if BF≤12%)
  Vegan:    2.6 g/kg lean

Fat: 15-30% of calories (diet-mode aware)
Carbs: Remainder of calorie budget

Navy BF% (Male):
  495 / (1.0324 - 0.19077×log10(waist-neck) + 0.15456×log10(height)) - 450

FFMI:
  lean_mass_kg / height_m²

ABSI:
  WC(m) × weight(kg)^(-2/3) × height(m)^(5/6)

WHtR:
  waist_cm / height_cm

WHR:
  waist_cm / hip_cm

Adaptive TDEE:
  observed = avg_intake - (Δweight × 7700 / days)
  adaptive = formula × (1-w) + observed × w
  where w = min(0.8, max(0.25, days/42))

1RM Estimates:
  Epley:   weight × (1 + reps/30)
  Brzycki: weight × 36 / (37 - reps)
  Lander:  100×weight / (101.3 - 2.67123×reps)
```

---

*This unified reference guide synthesizes the content of 37+ web articles from 7 sources. It is intended as a living document to be maintained alongside the Fitness Engine codebase. All claims are traceable to the cited sources.*
