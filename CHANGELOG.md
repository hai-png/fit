# Changelog

All notable changes to this project are documented in this file. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the
project adheres to [Semantic Versioning](https://semver.org/).

## [2.4.0] — 2026-06-17

### Summary

Third remediation pass: addresses true findings from a second (external)
engineering audit that were not already covered in v2.3.0–v2.3.1. Test suite
grows from 191 to 204 tests.

### Added
- `TestSecondAuditFixes` class with 13 regression tests covering all new fixes.

### Changed
- `cuisine_pick` normalizes all cuisine names to lowercase so `"Mediterranean"`
  matches the meal library's `"mediterranean"` tag. Previously, mixed-case
  preferences were silently ignored (second-audit: cuisine case).
- `meal_plan_seed` is now XORed with `plan_week` so each week produces a
  different deterministic plan — matching the README's claim. Previously,
  supplying `meal_plan_seed` produced the *same* plan every week (second-audit:
  meal_plan_seed overrides plan_week).
- 5-day split redesigned: Push / Pull / Legs A / Upper / Legs B (2 leg sessions
  instead of 1). Previously had 4 upper sessions and only 1 leg session
  (second-audit: 5-day split only 1 leg session).
- Protein/fibre boosters in `_choose_day` are now scaled along with main meals
  rather than being added before scaling. The previous implementation added
  boosters before the uniform scale, which meant the booster was also scaled
  down — defeating its purpose and *reducing* total protein (second-audit:
  protein booster added before scaling).
- `pull_up`, `chin_up`, `wide_grip_pull_up`, `chest_dip`, `tricep_dip`,
  `hanging_leg_raise`, `hanging_knee_raise` now have `equipment=["pullup_bar"]`
  in the exercise database. Previously these claimed `equipment=[]` (bodyweight)
  but actually require a pull-up bar or dip station. `inverted_row` (built-in)
  also updated. This prevents HOME_BODYWEIGHT plans from prescribing exercises
  the user cannot perform (second-audit: home bodyweight equipment filter
  broken).
- `leg_day` pattern list no longer has duplicate `"squat"` entry; replaced with
  `"hamstring"` for direct hamstring isolation (second-audit: leg_day duplicate
  squat pattern).
- `add_weight` validates `weight_kg` is positive and ≤ 500 (second-audit:
  add_weight no validation).
- `add_adherence` validates `nutrition_pct` and `training_pct` are in [0, 100]
  (second-audit: add_adherence no bounds check).
- `client_summary` now returns `plan_json` content in the plans list, not just
  `id` and `created_at` (second-audit: client_summary missing plan JSON).
- `tdee` raises `ValueError` if `bmr <= 0` (second-audit: tdee accepts bmr=0).
- `supplement_stack` no longer duplicates creatine for vegan muscle-gain
  trainees (it was in both `foundational` and `goal_specific`)
  (second-audit: supplement creatine duplicate).
- `_protein_target` bulk/recomp with BF% known now uses 2.6 g/kg for vegans
  (was 2.2 — same as omnivore, inconsistent with the "vegan targets are higher"
  rationale) (second-audit: vegan bulk protein same as omnivore).
- `render_html.py` no longer unconditionally mutates `sys.path` on import —
  only falls back to path insertion if `fitness_engine` is not already
  importable (second-audit: sys.path mutation).
- `render_html.py` escapes all warning/note strings with `escape(str(...))` to
  prevent XSS via user-supplied `medical_flags` keys (second-audit: XSS).
- `meal_plan_auditor` removed dead `"missing_or_incomplete"` from the confidence
  check set (second-audit: dead confidence check).
- `load_external_recipe_meals` is now cached via `functools.lru_cache` so
  repeated calls do not re-read the ~600 KB JSON file (second-audit: recipe_pool
  re-loads JSON on every call).

## [2.3.1] — 2026-06-17

### Summary

Second remediation pass: addresses the remaining P2 (Minor) findings from the
v2.2.1 engineering audit. All findings are now resolved. Test suite grows
from 146 to 191 tests.

### Added
- `ArchetypeProfile.showcase_defaults` field — co-locates the showcase CLI's
  per-archetype defaults with the profile definition (F75).
- `ArchetypeProfile` is now exported from `fitness_engine/__init__.py` (F4).
- `_validate_code_uniqueness()` guard in `archetypes.py` — runs at import and
  raises `AssertionError` if two enum values within a dimension produce the
  same truncated code segment (F2).
- `signature_from_dict` now produces clear error messages naming the
  offending key and valid values (F3).
- `_protein_target_structured()` — machine-readable protein-target breakdown
  with `basis`, `multiplier`, `reference_mass_kg`, `diet_mode`, `phase` (F16).
- `initial_assessment_guidance_structured()` and `InitialAssessmentGuidance`
  dataclass — structured alternative to the ASCII-art string list (F73).
- `delete_client()` and `schema_version()` in persistence layer (F70, F68).
- `set_default_cuisines()` — locale-aware override for the cuisine default (F32).
- `adaptive_tdee` accepts `kcal_per_kg` parameter for population-specific
  energy-density tuning (F26).
- `adjust_macros_for_calorie_change` accepts `round_to_g` parameter (F17).
- 45 new regression tests in `tests/test_audit_regressions.py`
  (`TestP2AdditionalFixes` class) covering every P2 fix.

### Changed
- `VISUAL_BF_BANDS` are now contiguous (no gaps between bands) with updated
  midpoints (F6).
- `body_fat_navy` raises sex-specific errors with clear messages and emits a
  `warnings.warn` when the result is clamped to [2, 60] (F7).
- `bmr_harris_benedict` docstring marks it as deprecated/comparison-only (F10).
- `fat_loss_rate_for_bodyfat` docstring cites Gallagher et al. 2000 for the
  8% female sex adjustment (F9).
- `_protein_target` removed redundant `body_fat_pct is not None` check (F15).
- Keto path in `macros_for` caps `fat_g` at `calories / 9` and `fat_pct` at
  1.0 to prevent impossible outputs (F14).
- `macro_cycle` uses 1 g rounding (instead of 5 g) to minimize weekly-average
  drift (F17).
- `one_rep_max` percent table now includes 30% and 40% warmup ranges (F18).
- `cardio_zones` uses ceil(low)/floor(high) so zones are half-open [low, high]
  and never overlap at integer bpm values (F20). Docstring notes the Fox
  formula is display-only (F21).
- `infer_somatotype` frame refinement is now symmetric across all three base
  classifications (F22).
- `anthropometric_indices` WHR docstring cites WHO 2008 (F24).
- `adaptive_tdee` computes a true median (average of two middle values for
  even-length lists) (F25).
- `intensity_scheme` beginner RIR override is goal-aware: strength beginners
  keep 2 RIR; hypertrophy/fat-loss beginners get 3 RIR (F30).
- `exercise_selection` include list is environment-aware: barbell-specific
  lifts only included for `GYM_FULL` (F31).
- Exercise DB loader normalizes names to title case and clamps difficulty to
  [1, 5] (F37).
- `ExerciseDatabase._load_database` skips malformed records with a stderr
  warning instead of crashing (F41).
- `MEAL_LIBRARY` header comment documents that macros are approximate USDA
  estimates (F42).
- `DIET_COMPATIBILITY` documentation explains the intentional asymmetry (F43).
- `_scale_meal` emits a stderr warning when the scale is clamped to [0.25, 3.0] (F45).
- `_external_to_meal` canonical-schema path now validates calories are in
  [50, 1500] (matching the legacy path) (F53).
- 7-day planner uses monotonic use-count decay instead of binary clear/reset
  for smoother variety (F51).
- `audit_7_day_meal_plan` score has a floor of 40 so a single catastrophic
  issue cannot drive the score into the 50s when all other checks pass (F57).
- `Recommender` auto-runs `audit_7_day_meal_plan` and includes the result in
  `PlanRecommendation.meal_plan_audit` (F58).
- Goal-strategy mismatch is now a WARNING (not a note) so it is visible in
  red in the HTML renderer (F61).
- `ClientProfile.to_dict` uses a recursive `_to_json_safe` helper that
  converts nested enums uniformly (F62).
- `ClientProfile.__post_init__` normalizes empty/whitespace motivation to
  "appearance" (F67).
- Persistence layer: schema versioning via `PRAGMA user_version` (F68),
  per-process init tracking to avoid redundant `init_db` calls (F69),
  `delete_client` cascade-deletes weights/adherence/plans (F70), indexes on
  `(client_id, day)` for weights and adherence (F71), foreign-key enforcement
  enabled per connection.
- `cmd_showcase` uses `ap.showcase_defaults` instead of a hardcoded dict (F75).
- `cmd_store_client` and `_format_plan_json` use the unified `_to_json_safe`
  serializer so enums are converted consistently (F76).
- `docs/analysis/exercise_database_analysis.md` updated to reflect v2.3.0
  remediation status (F88).

## [2.3.0] — 2026-06-17

### Summary

This release addresses every Critical (P0) and Major (P1) finding from the
v2.2.1 engineering audit, plus selected Minor (P2) polish. See the audit
report for the full finding-by-finding breakdown.

### Added
- `CHANGELOG.md`, `LICENSE` (MIT), `CONTRIBUTING.md`, `.gitignore`.
- GitHub Actions CI workflow (`.github/workflows/ci.yml`) running `ruff check` + `pytest -q`.
- `pytest-cov` configuration in `pyproject.toml` for coverage measurement.
- `HEALTH_SCREEN` questionnaire module that populates `ClientProfile.medical_flags` from intake.
- `assemble_day` / `assemble_week` now accept a `seed` parameter for reproducible plans (F44).
- `macro_cycle` accepts `sex` and applies the 1200/1500-kcal safety floor to rest-day calories (C5a).
- `MuscularPotential.normalized_ffmi` field — previously computed internally but never returned (F28).
- `AnthropometricIndices.absi_z` and `absi_category` fields — ABSI is now z-scored against Krakauer & Krakauer (2012) reference values (F23).
- `DietaryPreference` questionnaire now offers all 12 diet modes instead of only Omnivore/Vegan (F65).
- `DIET_MODE_NOTES` covers all 12 `DietaryPreference` values (F63).
- `SupplementStack.conditional` is now populated with diet- and goal-specific supplements (electrolytes for keto, iron for vegan women, caffeine for strength/fat-loss, etc.) (F33).
- `_special_modifiers` now handles adolescent (age < 18), pregnancy/post-partum, recent surgery, eating-disorder history, and cardiac flags (F64).
- `build_complete_profile_protocol` accepts `medical_flags` and threads it through to `_special_modifiers`.
- Exercise DB loader logs skipped records to stderr (F38) and the recipe loader logs placeholder-instruction rejections (F54) and JSON parse errors (F52).
- `ExerciseDatabase` and `ScrapedExercise` are now exported from `fitness_engine/__init__.py` (F79).
- `HEALTH_SCREEN` is exported from `fitness_engine/__init__.py`.
- New regression tests for every P0 and P1 fix (see `tests/`).

### Changed
- `body_composition` validates `bf_pct` to [2, 60]% and rejects pathological values (C1).
- `macros_for` raises `ValueError` when protein + fat + carb floors exceed the calorie target (C2).
- `_load_guidance` matches on exercise **name** only — pattern-name aliases (`"hinge"`, `"vertical_push"`, etc.) removed to eliminate cross-lift 1RM contamination (C3).
- `training_split` adds an explicit 1-day case (`Full Body 1-day`) so `days_per_week=1` no longer silently produces a 2-day plan (C4).
- `weekly_split` uses three distinct variants (`fb(0)`, `fb(1)`, `fb(2)`) for the 3-day split so Day 3 != Day 1 (F59).
- `build_session` default pattern list now includes `isolation` and `hamstring` so accessory muscles receive direct volume (C5).
- `pick_exercise` sorts candidates by difficulty closest to the experience-appropriate tier instead of always picking the hardest feasible option (F34).
- `_load_comprehensive_exercise_library` is wrapped in `functools.lru_cache` so the JSON is parsed at most once per process (F35).
- `correct_bf_estimate` clamps results to [2, 55]% (F27).
- `assemble_7_day_meal_plan` uses a local `random.Random(seed)` instance instead of seeding the global `random` module (F48).
- `_choose_day` caps total meals at `meals_per_day + 1` even when protein/fibre boosters want to add more (F50).
- `load_external_recipe_meals` skips recipes with placeholder instructions (<80 chars total) (F54).
- `filter_by_equipment` and `_equipment_feasible` in `exercise_database.py` handle the `["bodyweight"]` token (F39).
- `ENVIRONMENT_EQUIPMENT` in `exercise_database.py` is consolidated to match `exercise_plans.py` (F40).
- `Barbell Upright Row` reclassified from `vertical_pull` to `horizontal_pull` (F36).
- Comprehensive exercise DB metadata `total_exercises` corrected from 100 to 115.
- `DIET_COMPATIBILITY` documentation updated to note intentional asymmetry (F43).
- `filter_compatible` allergen matching uses word-boundary regex instead of substring (F46).
- 5-meal layout uses distinct `snack_1` / `snack_2` slot keys (F47).
- Meal auditor's `_is_side_or_booster` detects sides by tag/properties rather than hardcoded names (F55).
- Meal auditor's slot-sanity check uses word-boundary regex and a refined keyword list (F56).
- `_SLOT_WEIGHTS` comment documents the snack_1/snack_2 disambiguation.
- `cmd_review` guards against `None` subscripting when `formula_tdee` is missing (F74).
- `examples/render_html.py` auto-creates the output directory (F77) and renders `snack_1`/`snack_2` as "Morning Snack"/"Afternoon Snack" (F78).
- `examples/run_all.sh` runs `mkdir -p output/` before the render loop (F86).
- `calorie_target` Alpert safeguard uses a clean boolean flag set at the point of clamping (F11).
- `calorie_target` MUSCLE_GAIN surplus surfaces `neat_buffer_pct` and `neat_buffer_note` in the breakdown (F12).
- `archetypes.py` activity-multiplier comment corrected from "4-tier" to "6-tier" (F8).
- `weekly_volume` rationale notes the strength-training exception when base < 10 (F29).
- `ClientProfile.motivation` field documented as accepting enum values from the GOALS questionnaire.
- `recommender._load_guidance` rationale strings now include the source lift and rep assumption.
- `recommender.recommend()` passes `sex` to `macro_cycle` and `medical_flags` to `build_complete_profile_protocol`.

### Fixed
- **C1**: `body_composition(bf_pct=-5)` no longer returns `lean_mass_kg=73.5`; raises `ValueError`.
- **C2**: `macros_for(1200, 90, 60, FAT_LOSS, MALE, ENDOMORPH, OMNIVORE, body_fat_pct=25)` no longer returns 1365 kcal of macros at a 1200-kcal target; raises `ValueError`.
- **C3**: `working_weights_kg={"deadlift": 120}` no longer applies the deadlift 1RM to Barbell Hip Thrust.
- **C4**: `days_per_week=1` produces a 1-day plan, not a 2-day plan.
- **C5**: Weekly volume reconciliation no longer starves calves and arms (isolation patterns added to session builder).
- **C5a**: `macro_cycle(base=2400, training_days_per_week=6)` no longer produces 944-kcal rest days.
- **F27**: `correct_bf_estimate(0, True)` returns 2.0 instead of 0.0; `correct_bf_estimate(100, True)` returns 55.0 instead of 150.0.
- **F39**: `db.filter_by_equipment([])` returns bodyweight exercises instead of 0.
- **F54**: Recipes with placeholder instructions (e.g., "Injera" with `["Easy Yeast Method", "Quick Method", "Cooking"]`) are no longer surfaced in plans.
- **F59**: 3-day Full Body A/B/C split now has three distinct sessions.
- **F74**: `python -m fitness_engine.cli review review.json` no longer crashes when `formula_tdee` is missing.
- **F77**: `python examples/render_html.py examples/sample_arthur.json output/arthur_plan.html` no longer crashes when `output/` does not exist.

### Removed
- Dead `bmr_harris_benedict` is kept for backwards compatibility but explicitly documented as a comparison-only formula (F10).
- The hardcoded `side_names` exemption set in the meal auditor (replaced by tag/property detection).

## [2.2.1] — 2026-06-15

Initial audited release. See the engineering audit report for the full list
of findings addressed in 2.3.0.
