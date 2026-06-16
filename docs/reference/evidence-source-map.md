# Evidence Source Map

This map records the user-supplied reference corpus and how the engine currently uses each cluster. It is a traceability document, not a claim that every external calculator agrees exactly with the implementation.

## Body-fat estimation and physique comparison

| Source | Engine mapping |
|---|---|
| https://rippedbody.com/body-fat-guide/ | Visual body-fat labels and self-estimate correction concepts in `calculators.py`; `ClientProfile.visual_bf_label` fallback. |
| https://ultimateperformance.com/your-goal/fat-loss/male-fat-loss/male-body-fat-comparison | Reference context for male visual body-fat comparison; not copied directly. |
| https://rippedbody.com/how-calculate-body-fat-percentage/ | Navy/body-fat-estimation context; engine supports Navy tape, BMI fallback and visual fallback. |
| https://www.fatcalc.com/bfb | Body-fat/BMI comparison reference; not a primary formula source. |
| https://www.fatcalc.com/bf | Body-fat calculator comparison reference; not a primary formula source. |

## Intake / quiz / before-counting workflow

| Source | Engine mapping |
|---|---|
| https://quiz.builtwithscience.com/page/1 | Product-style intake inspiration; not scraped or copied. |
| https://rippedbody.com/before-you-count/ | Reflected through validation, medical flags and coaching warnings; not a full behavioural questionnaire. |
| https://rippedbody.com/how-to-count-macros/ | Counting/adherence guidance is represented in adjustment checklists and plan notes. |

## Nutrition pyramid, micros, calories and macros

| Source | Engine mapping |
|---|---|
| https://rippedbody.com/nutrition-pyramid-overview/ | Overall hierarchy reflected in calorie/protein-first design and supplement priority. |
| https://rippedbody.com/micros/ | `micronutrient_targets()` and meal-plan fibre/fruit/veg notes. |
| https://rippedbody.com/calories/ | Calorie target logic and goal-specific energy balance. |
| https://rippedbody.com/calories/#loss-rate | Body-fat-aware fat-loss rate and Alpert cap. |
| https://rippedbody.com/best-macro-ratio/ | `macros_for()` protein/fat/carbohydrate partitioning; no magic ratio claim. |
| https://rippedbody.com/macro-calculator/ | Macro-calculator methodology reference. |
| https://rippedbody.com/keto/ | Keto branch caps carbs and shifts calories to fat. |
| https://rippedbody.com/advice-for-vegans/ | Vegan protein adjustment and vegan supplement stack. |
| https://www.fatcalc.com/macro | Macro calculator comparison reference. |
| https://www.fatcalc.com/protein-calculator | Protein calculator comparison reference. |

## Diet adjustment, progress tracking and plateaus

| Source | Engine mapping |
|---|---|
| https://rippedbody.com/how-to-adjust-macros/ | `cut_adjustment_checklist()` and calorie-adjustment utilities. |
| https://rippedbody.com/how-to-adjust-macros/#checklist | Cut checklist source. |
| https://rippedbody.com/how-to-adjust-macros-bulk/#checklist | Bulk checklist source. |
| https://rippedbody.com/training-plateaus/#checklist | Training plateau checklist source. |
| https://rippedbody.com/diet-progress-tracking/ | `adaptive_tdee()`, `cli review`, persistence weight logs, and coaching notes. |
| https://rippedbody.com/why-my-weight-going-up-and-down-while-dieting/ | Water-weight/noise concept in adjustment notes. |
| https://rippedbody.com/initial-adjustment/ | Initial-adjustment caution in `adjustments.py`. |

## Cutting, bulking, recomposition and phase choice

| Source | Engine mapping |
|---|---|
| https://macrofactor.com/cutting-calculator/ | Cutting-rate comparison reference. |
| https://macrofactor.com/bulk-or-cut/ | Phase-decision comparison reference; engine has RippedBody-style `recommend_phase_strategy()`. |
| https://macrofactor.com/bulking-calculator/ | Bulking-rate comparison reference. |
| https://rippedbody.com/goal-setting-1/ | Trainee category and goal-setting context. |
| https://rippedbody.com/goal-setting-2/ | Goal-setting context. |
| https://rippedbody.com/goal-setting-3/ | Goal-setting context. |
| https://rippedbody.com/cut-or-bulk/ | Cut/bulk boundaries and phase mismatch notes. |
| https://rippedbody.com/how-to-bulk/ | Bulking guidance and surplus cautions. |
| https://rippedbody.com/updated-bulking-guidelines/ | Experience-tiered bulking rates. |
| https://www.fatcalc.com/body-recomp-calculator | Recomposition comparison reference. |
| https://www.fatcalc.com/rwl | Rate-of-weight-loss comparison reference. |
| https://www.fatcalc.com/reverse-diet-calculator | Reverse-diet calculator comparison reference; engine exposes `reverse_diet_protocol()` and `cli review`. |

## Adaptive TDEE, maintenance, RMR/TDEE

| Source | Engine mapping |
|---|---|
| https://gymgeek.com/calculators/maintenance-calories-calculator/#explainer | Maintenance-calorie comparison reference. |
| https://gymgeek.com/calculators/calorie-calculator/ | Calorie calculator comparison reference. |
| https://gymgeek.com/calculators/adaptive-tdee-calculator/ | Adaptive TDEE comparison reference; engine has `adaptive_tdee()` and `cli review`. |
| https://www.zolthealth.com/learn/what-is-adaptive-tdee | Adaptive TDEE concept reference. |
| https://gymcreek.com/adaptive-tdee-calculator/ | Adaptive TDEE comparison reference. |
| https://gymgeek.com/calculators/bulking-calculator/ | Bulking calculator comparison reference. |
| https://www.fatcalc.com/rmr-calculator | RMR comparison reference. |
| https://www.fatcalc.com/tdee-calculator | TDEE comparison reference. |

## Anthropometrics and body composition calculators

| Source | Engine mapping |
|---|---|
| https://www.fatcalc.com/bwp | Body-weight planning comparison reference. |
| https://www.fatcalc.com/mfl | Maximum fat-loss comparison reference; engine uses Alpert-style cap. |
| https://www.fatcalc.com/whtr-calculator | `anthropometric_indices().waist_to_height_ratio`; surfaced in `PlanRecommendation`. |
| https://www.fatcalc.com/whr | `anthropometric_indices().waist_to_hip_ratio`; surfaced in `PlanRecommendation`. |
| https://www.fatcalc.com/absi | `anthropometric_indices().absi`; surfaced in `PlanRecommendation`. |
| https://www.fatcalc.com/hydration-calculator | Hydration comparison reference; engine has `hydration()`. |
| https://www.fatcalc.com/mm | Muscular-potential comparison reference. |
| https://www.fatcalc.com/ibw-calculator | `ideal_body_weight_devine()` surfaced via `anthropometric_indices()`. |

## Muscular potential

| Source | Engine mapping |
|---|---|
| https://rippedbody.com/maximum-muscular-potential/ | `muscular_potential()` Berkhan/FFMI reference. |

## Training programs

| Source | Engine mapping |
|---|---|
| https://rippedbody.com/how-to-build-training-programs/ | `training_split()`, `weekly_volume()`, `intensity_scheme()`, `progression_rule()`, `periodisation()`, `weekly_split()`, and volume reconciliation. |

## Notes for future audits

1. RippedBody sources are treated as the primary methodology contract for this repository.
2. MacroFactor, GymGeek, FatCalc and Zolt references are comparison/calibration sources unless explicitly wired into formulas.
3. External pages change. If strict formula parity is required, freeze dated excerpts in `docs/reference/` and add tests with expected examples.
