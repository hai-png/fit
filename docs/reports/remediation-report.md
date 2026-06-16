# Remediation Report — `hai-png/fit`

This report records the issues found by cross-referencing the repository against `../reference/fitness-app-reference-guide.md`, and the fixes implemented in this workspace.

## Verification

```bash
python3 -m unittest tests.test_calculators tests.test_integration
# Ran 80 tests — OK

bash examples/run_all.sh
# All checks complete
```

## Issues addressed

| Area | Reference-guide requirement | Previous state | Remediation |
|---|---|---|---|
| BMR default | Mifflin-St Jeor is the preferred general-purpose estimate; Harris-Benedict is lower priority | `energy_expenditure()` used Harris-Benedict by default | Switched default to Mifflin-St Jeor; kept Harris-Benedict exposed for comparison/fallback |
| Activity multipliers | Sedentary 1.25, light + lifting 1.45, moderate 1.55–1.65, active 1.75–1.85 | Used 1.15, 1.35, 1.55, 1.75 | Updated to 1.25, 1.45, 1.60, 1.80 while keeping the existing 4-tier enum for backwards compatibility |
| Calorie safety floor | Women ≥1200 kcal/day, men ≥1500 kcal/day | Universal 1200 kcal floor | `calorie_target()` now accepts `sex`; male floor is 1500, otherwise 1200 |
| Maximum safe fat-loss rate | Alpert max deficit: fat mass in lb × 22 kcal/day | Not implemented | Added Alpert safeguard when BF%/lean mass is known; recommender surfaces warning when applied |
| Visual body-fat bands | Sex-specific visual ranges from the guide | Male ranges were shifted and compressed; no female-specific mapping | Rebuilt visual bands as sex-specific maps aligned to guide tables |
| Somatotype macro tweaks | Guide rejects body-type macro manipulation; adjust from outcomes/adherence | Fat % changed based on somatotype | Removed somatotype macro adjustment; rationale now states no somatotype tweak |
| FFMI coefficient | Normalized FFMI = FFMI + 6.3 × (1.8 − height) | Used 6.1 | Updated to 6.3 |
| Hydration | 30 ml/kg baseline; +300 ml for men; exercise adjustment | 35 ml/kg baseline | Updated formula; backwards-compatible optional `sex` argument |
| Macro adjustment logic | Maintain protein; adjust carbs/fats at 1:1–2:1 calorie split; round to 5 g | Missing | Added `adjust_macros_for_calorie_change()` |
| Anthropometric indices | WHtR, WHR, ABSI, IBW | Missing | Added `anthropometric_indices()` and `ideal_body_weight_devine()` |
| Adaptive TDEE | Formula estimate blended with trend data, outlier handling, confidence | Missing | Added `DailyLog`, `adaptive_tdee()`, and `AdaptiveTDEEEstimate` |
| Reverse dieting | Conservative/moderate/aggressive calorie increases after cuts | Missing | Added `reverse_diet_protocol()` with weekly steps and monitoring rules |
| Cardio interference cap | Weekly cardio should be less than half weekly lifting time | Text guidance existed, prescription could exceed cap | Fat-loss cardio prescription now includes and respects a cap based on lifting time |
| Goal conflict decision tree | Body-composition strategy should be flagged when selected goal conflicts | Classification existed, mismatch not surfaced | Recommender notes when selected goal conflicts with trainee-category strategy |
| Test coverage | New reference-guide behaviours should be regression tested | Tests covered old values only | Added tests for Mifflin default, new multipliers, male floor, Alpert cap, anthropometrics, macro adjustment, adaptive TDEE, reverse diet |

## Important remaining product-level gaps

The repository is now materially better aligned with the reference guide, but several guide items are larger product features rather than calculator-library fixes:

1. **Full food-tracking product layer** — barcode scanning, verified food database, recipe builder, favorites, quick-add.
2. **Progress-photo storage and visualization** — requires UI/storage beyond the current engine.
3. **Full 9-point measurement log** — guidance can be added easily, but longitudinal storage/visualization needs an app layer.
4. **Diet-type expansion** — keto, Mediterranean, vegetarian, gluten-free, paleo, low-carb presets require enum/API changes and a larger tagged meal database.
5. **Wearable / step-count integration** — needs external device integrations.
6. **Keto tolerance trial workflow** — needs daily subjective ratings and comparison reports.
7. **Female cycle-aware trend interpretation** — requires menstrual-cycle inputs and UX decisions.

## Files changed

- `fitness_engine/calculators.py`
- `fitness_engine/recommender.py`
- `fitness_engine/__init__.py`
- `tests/test_calculators.py`
- regenerated `output/*_plan.html` via `examples/run_all.sh`

## Second-pass completion against `../analysis/fit-analysis.md`

Additional items from the analysis have now been addressed:

| `../analysis/fit-analysis.md` item | Resolution |
|---|---|
| Activity enum missing the full guide model | Added `MODERATELY_ACTIVE` and `VERY_ACTIVE`, preserving legacy values. Multipliers now cover 1.25 / 1.45 / 1.55 / 1.60 / 1.80 / 1.90. |
| Fat-loss rate did not scale with body fat | Added `fat_loss_rate_for_bodyfat()` and wired it into `energy_expenditure()` so leaner clients cut slower and higher-BF clients can cut faster, still capped by Alpert. |
| Lean cutting protein may be low | Lean cutting profiles now receive a higher omnivore lean-mass protein multiplier. |
| Formal bulk/cut/recomp decision tree missing | Added `recommend_phase_strategy()` and use it in the recommender to flag selected-goal conflicts. |
| Macro cycling missing | Added optional `macro_cycle()` that keeps weekly calories matched, preserves protein, and shifts mostly carbs. |
| Diet types too limited | Expanded `DietaryPreference` to balanced, omnivore, vegan, vegetarian, pescatarian, pollo-pescatarian, keto, low-carb, Mediterranean, paleo, gluten-free, and high-protein. |
| Keto / low-carb / Mediterranean presets missing | `macros_for()` now has diet-mode-aware macro constraints/presets for keto, low-carb, Mediterranean, paleo, and high-protein. |
| Meal filtering only supported omnivore/vegan | `meal_plans.py` now has a full compatibility matrix and additional meals/tags so every diet mode can assemble a calorie-accurate day. |
| Purgatory and new-trainee-healthy categories not practically classified | `classify_trainee()` now supports purgatory via `diet_history_confused=True` and classifies healthy-range beginners as `new_trainee_healthy` where appropriate. |
| Progress tracking only partially covered measurements and omitted photos | `progress_tracking_guide()` now includes 9-point measurements, monthly photos, and strength log guidance. |
| Complete plan-building protocols not explicit | Added `fitness_engine/protocols.py` with comprehensive exercise and meal protocol builders covering every archetype/profile combination. Recommender now includes `rec.protocols`. |
| Coverage for every possible profile not tested | Added integration coverage proving the protocol builder handles every enumerated archetype signature, plus all diet modes can assemble day plans within ±5%. |

Current verification:

```bash
python3 -m unittest tests.test_calculators tests.test_integration
# Ran 80 tests — OK

bash examples/run_all.sh
# All checks complete
```

## Protocol documentation added

A human-readable protocol guide has also been added:

- `../protocols/comprehensive-plan-building-protocols.md`

This explains the rule system for exercise plan construction, meal plan construction, diet modes, adjustment protocols, and the coverage guarantee for all profile combinations.

## External recipe scrape + weekly planner added

Additional deliverables:

- `scripts/scrape_external_recipes.py`
- `data/recipes/normalized/trifecta_recipes.json`
- `fitness_engine/seven_day_meal_planner.py`
- `../protocols/recipe-scraping-and-7day-system.md`

Current scrape results in this environment:

- Trifecta scraped successfully: 256 normalized recipe/article entries.
- 43 entries have parsed macros and are eligible for automated planning.
- Muscle & Strength direct scraping is implemented, but the site returned Cloudflare/403 to headless HTTP in this environment; blocked URLs are recorded when the scraper is run without `--skip-mns`.

The recommender now creates `rec.nutrition.weekly_meal_plan` using the 7-day protocol planner.

Verification now passes:

```bash
python3 -m unittest tests.test_calculators tests.test_integration
# Ran 80 tests — OK
```

## User-attached Muscle & Strength recipes imported and audited

The attached `/home/user/uploads/recipes.json` export was normalized into:

- `data/recipes/normalized/muscleandstrength_recipes.json`

Import result:

- 149 recipes imported.
- 148 planner-eligible recipes.

Additional quality tooling added:

- `scripts/import_muscleandstrength_recipes.py`
- `fitness_engine/meal_plan_auditor.py`
- `../reports/meal-plan-quality-audit.md`
- `output/sample_7day_meal_plan_audit.json`

Audit after fixes:

```text
Sample weekly plan: A, 100/100
Cross-diet plans: all A-grade
```

## External-recipe-only cleanup and unified database

The meal planning system has been cleaned up again to address recipe field contamination and internal/external mixing.

New canonical recipe organization:

- `data/recipes/unified_external_recipes.json`
- `data/recipes/normalized/muscleandstrength_recipes.json`
- `data/recipes/normalized/trifecta_recipes.json`
- `data/recipes/status/muscleandstrength_scrape_status.json`

New/updated scripts:

- `scripts/import_muscleandstrength_recipes.py`
- `scripts/scrape_external_recipes.py`
- `scripts/build_unified_recipe_database.py`
- `scripts/generate_common_profile_meal_plans.py`

The 7-day planner now uses external recipes only (`include_internal=False` by default). `rec.nutrition.meal_plan` is now the first day of the same external-only weekly plan for backwards compatibility.

Canonical recipe DB result:

- 323 clean external recipes.
- 147 Muscle & Strength.
- 137 Trifecta.

Sample generated plan audit:

- A grade, 100/100.
- Source mix: Trifecta 9, Muscle & Strength 18, Daring Gourmet 1.

Common profile plans with alternatives are in `output/common_meal_plans/`.
