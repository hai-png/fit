"""
test_remediation_regressions.py
================================

Regression tests for the P0/P1 fixes applied in the second-pass audit.
Each test name encodes the issue ID so failures point directly at the
finding being protected.

Run with:
    python -m pytest tests/test_remediation_regressions.py -v
"""
from __future__ import annotations

import json
import os
import random
import subprocess
import tempfile
import unittest
from pathlib import Path

from fitness_engine import (
    GoalArchetype, Sex, ExperienceLevel,
    DietaryPreference, TrainingEnvironment, Macros, DailyLog, adaptive_tdee, macro_cycle,
    bmr_mifflin, bmi, hydration, muscular_potential, micronutrient_targets,
    one_rep_max, cardio_zones, weekly_tonnage, ideal_body_weight_devine,
    MAX_1RM_REPS,
)
# _protein_target and _validate_positive are private; import explicitly.
from fitness_engine.calculators import _protein_target, _validate_positive
from fitness_engine.recommender import ClientProfile, Recommender
from fitness_engine.exercise_plans import EXERCISE_LIBRARY
from fitness_engine.meal_plans import MealItem, MealPlan
from fitness_engine.seven_day_meal_planner import (
    _allergen_ok, DayPlanQuality, SevenDayMealPlan,
)
from fitness_engine.meal_plan_auditor import audit_7_day_meal_plan
from fitness_engine.questionnaires import intake_report, FULL_INTAKE, CORE_DEMOGRAPHICS

REPO = Path(__file__).resolve().parents[1]


def _make_macros(cal=2000, p=150, c=220, f=65):
    return Macros(
        calories=cal, protein_g=p, carbs_g=c, fat_g=f,
        protein_pct=p*4/cal*100, carbs_pct=c*4/cal*100, fat_pct=f*9/cal*100,
        rationale="test",
    )


# =========================================================================== #
# P0-1: adaptive_tdee must sort logs by day before slicing
# =========================================================================== #
class TestP01_AdaptiveTDEESortsLogs(unittest.TestCase):
    def test_unsorted_logs_produce_same_result_as_sorted(self):
        """adaptive_tdee must be order-independent on input logs."""
        weights = [80.0 - 0.1 * i for i in range(28)]
        cals = [2500 if i % 2 == 0 else 2400 for i in range(28)]
        logs_sorted = [
            DailyLog(day=i + 1, calories=cals[i], weight_kg=weights[i], complete=True)
            for i in range(28)
        ]
        logs_shuffled = logs_sorted[:]
        random.seed(42)
        random.shuffle(logs_shuffled)
        res_sorted = adaptive_tdee(logs_sorted, formula_tdee=2450.0)
        res_shuffled = adaptive_tdee(logs_shuffled, formula_tdee=2450.0)
        # After the P0-1 fix, both should be identical (no error from unsorted input).
        self.assertAlmostEqual(
            res_sorted.observed_tdee, res_shuffled.observed_tdee, delta=0.5,
            msg="adaptive_tdee must produce identical results for sorted vs shuffled logs",
        )
        self.assertAlmostEqual(
            res_sorted.weight_change_kg, res_shuffled.weight_change_kg, delta=0.05,
        )


# =========================================================================== #
# P0-2: macro_cycle rest-day floor enforced after rounding
# =========================================================================== #
class TestP02_MacroCycleFloorEnforced(unittest.TestCase):
    def test_male_floor_1500_enforced_at_low_base(self):
        """At base=1600 kcal, male, the rest day must not drop below 1500."""
        base = _make_macros(cal=1600, p=130, c=130, f=50)
        cycle = macro_cycle(base, training_days_per_week=6, calorie_swing_pct=0.20, sex=Sex.MALE)
        self.assertGreaterEqual(
            cycle.rest_day.calories, 1500,
            f"male rest-day floor of 1500 violated: got {cycle.rest_day.calories}",
        )

    def test_female_floor_1200_enforced_at_low_base(self):
        base = _make_macros(cal=1400, p=120, c=110, f=45)
        cycle = macro_cycle(base, training_days_per_week=6, calorie_swing_pct=0.20, sex=Sex.FEMALE)
        self.assertGreaterEqual(
            cycle.rest_day.calories, 1200,
            f"female rest-day floor of 1200 violated: got {cycle.rest_day.calories}",
        )

    def test_no_violations_across_parameter_scan(self):
        """Scan 112 parameter combinations — none should violate the floor."""
        base_protos = [(1500, 130, 130, 50), (1600, 130, 140, 55), (1800, 140, 170, 60),
                       (2000, 150, 220, 65), (2200, 165, 240, 73), (2500, 180, 280, 80)]
        violations = []
        for cal, p, c, f in base_protos:
            base = _make_macros(cal=cal, p=p, c=c, f=f)
            for swing in [0.05, 0.10, 0.15, 0.20]:
                for td in [3, 4, 5, 6]:
                    for sex in [Sex.MALE, Sex.FEMALE]:
                        cycle = macro_cycle(base, training_days_per_week=td,
                                            calorie_swing_pct=swing, sex=sex)
                        floor = 1500 if sex == Sex.MALE else 1200
                        if cycle.rest_day.calories < floor:
                            violations.append((cal, swing, td, sex.value, cycle.rest_day.calories))
        self.assertEqual(violations, [], f"{len(violations)} floor violations: {violations[:5]}")


# =========================================================================== #
# P0-3: meal_plan_auditor flags zero-fibre days
# =========================================================================== #
class TestP03_AuditorFlagsZeroFibre(unittest.TestCase):
    def _build_plan_with_fibre(self, fibre_g):
        meal = MealItem(
            name="test_meal", cuisine="american", slot="dinner",
            calories=600, protein_g=40, carbs_g=40, fat_g=20, fibre_g=fibre_g,
            tags=["dinner", "source:internal", "confidence:verified",
                  "diet:omnivore"],
            ingredients=["chicken", "rice", "broccoli"],
        )
        return MealPlan(name="d1", cuisine="american",
                        diet=DietaryPreference.OMNIVORE, meals=[meal])

    def test_zero_fibre_day_is_flagged(self):
        days = [self._build_plan_with_fibre(0 if i == 1 else 25) for i in range(7)]
        from fitness_engine.calculators import MicronutrientTargets
        qualities = [
            DayPlanQuality(calorie_error_pct=0.0, protein_error_g=0.0,
                           fibre_g=(0 if i == 1 else 25),
                           macro_confidence="verified")
            for i in range(7)
        ]
        plan = SevenDayMealPlan(
            name="t", diet=DietaryPreference.OMNIVORE,
            days=days, target_calories=2000,
            target_macros=_make_macros(),
            micronutrients=MicronutrientTargets(
                fibre_g=28.0, fruit_cups=2, veg_cups=3, water_guidance=["2-3 L/day"]),
            quality_by_day=qualities, shopping_list={}, protocol_notes=[],
            source_summary={"internal": 7},
        )
        audit = audit_7_day_meal_plan(plan)
        # The fix ensures zero-fibre days are flagged — either in the
        # "Known fibre is low" list or the "Days with zero fibre data" list.
        fibre_issues = [i for i in audit.issues if "fibre" in i.lower()]
        self.assertTrue(
            fibre_issues,
            f"zero-fibre day not flagged; audit issues: {audit.issues}",
        )


# =========================================================================== #
# P0-4: exercise DB loads pull-up, chin-up, dips, hanging leg raises
# =========================================================================== #
class TestP04_ExerciseLibraryContainsExpectedExercises(unittest.TestCase):
    def test_pullup_bar_exercises_present(self):
        for ex_id in ("pull_up", "chin_up", "wide_grip_pull_up",
                      "chest_dip", "tricep_dip", "bench_dip",
                      "hanging_leg_raise", "hanging_knee_raise"):
            self.assertIn(
                ex_id, EXERCISE_LIBRARY,
                msg=f"Expected exercise '{ex_id}' missing — check equipment mapping",
            )


# =========================================================================== #
# P0-5: allergen matching uses word-boundary regex
# =========================================================================== #
class TestP05_AllergenWordBoundary(unittest.TestCase):
    def test_pea_does_not_match_peanut(self):
        recipe = MealItem(
            name="Peanut Butter Toast", cuisine="american", slot="breakfast",
            calories=350, protein_g=12, carbs_g=40, fat_g=15, fibre_g=4,
            tags=["breakfast", "vegetarian"],
            ingredients=["peanut butter", "bread"],
        )
        self.assertTrue(
            _allergen_ok(recipe, ["pea"]),
            "allergen 'pea' must NOT match 'peanut' (word-boundary regex)",
        )

    def test_peanut_matches_peanut(self):
        recipe = MealItem(
            name="Peanut Butter Toast", cuisine="american", slot="breakfast",
            calories=350, protein_g=12, carbs_g=40, fat_g=15, fibre_g=4,
            tags=["breakfast"],
            ingredients=["peanut butter", "bread"],
        )
        self.assertFalse(
            _allergen_ok(recipe, ["peanut"]),
            "allergen 'peanut' must match 'peanut'",
        )

    def test_plural_egg_matches_eggs(self):
        recipe = MealItem(
            name="Omelette", cuisine="american", slot="breakfast",
            calories=250, protein_g=18, carbs_g=2, fat_g=18, fibre_g=0,
            tags=["breakfast"], ingredients=["eggs", "butter"],
        )
        self.assertFalse(
            _allergen_ok(recipe, ["egg"]),
            "allergen 'egg' must match ingredient 'eggs' (plural form)",
        )


# =========================================================================== #
# P0-6: CLI --format html works from any directory
# =========================================================================== #
class TestP06_CLIHtmlFormatWorks(unittest.TestCase):
    def test_html_render_from_non_project_dir(self):
        sample = REPO / "examples" / "sample_client.json"
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                ["python", "-m", "fitness_engine.cli", "profile", str(sample),
                 "--format", "html", "--out", os.path.join(tmp, "out.html")],
                cwd="/home/z/my-project",  # NOT the repo root
                capture_output=True, text=True, timeout=60,
            )
            self.assertEqual(
                result.returncode, 0,
                f"CLI --format html failed outside project root: {result.stderr[:500]}",
            )
            self.assertTrue(
                os.path.exists(os.path.join(tmp, "out.html")),
                "HTML output file was not created",
            )


# =========================================================================== #
# P0-7: female with waist+neck, no hip does not crash recommend()
# =========================================================================== #
class TestP07_FemaleNoHipFallback(unittest.TestCase):
    def test_recommend_succeeds_without_hip(self):
        p = ClientProfile(
            age=30, sex=Sex.FEMALE, height_cm=165, weight_kg=70,
            waist_cm=78, neck_cm=32, hip_cm=None,
            primary_goal=GoalArchetype.FAT_LOSS,
            experience=ExperienceLevel.INTERMEDIATE,
            days_per_week=4, environment=TrainingEnvironment.HOME_GYM,
            dietary_preference=DietaryPreference.OMNIVORE,
        )
        rec = Recommender(p).recommend()
        self.assertIsNotNone(rec.archetype_signature)


# =========================================================================== #
# P1-3: calorie_target default floor is conservative (1500 for sex=None)
# =========================================================================== #
class TestP01Fix3_CalorieTargetFloor(unittest.TestCase):
    def test_unknown_sex_uses_male_floor(self):
        from fitness_engine import calorie_target, FAT_LOSS_WEEKLY_RATE
        # calorie_target returns (target, breakdown_dict).
        target, breakdown = calorie_target(
            tdee_value=800,
            goal=GoalArchetype.FAT_LOSS,
            bodyweight_kg=80,
            experience=ExperienceLevel.ADVANCED,
            fat_loss_rate=FAT_LOSS_WEEKLY_RATE,
            sex=None,
        )
        # With sex=None, the floor should be 1500 (conservative male floor),
        # not 1200 (female floor) which would under-protect male users.
        self.assertGreaterEqual(target, 1500)


# =========================================================================== #
# P1-4: protein lean-cut threshold is sex-aware
# =========================================================================== #
class TestP01Fix4_SexAwareProteinThreshold(unittest.TestCase):
    def test_female_at_13pct_bf_gets_lean_cut_multiplier(self):
        # 13% BF female is clinically very lean (essential fat ~10-13%).
        # Previously she would have been denied the 2.8 g/kg lean-cut
        # multiplier because the threshold was a flat 12%.
        lean_mass = 50.0
        protein_g, _ = _protein_target(
            goal=GoalArchetype.FAT_LOSS, weight_kg=60,
            lean_mass_kg=lean_mass, body_fat_pct=13.0,
            target_weight_kg=None, is_vegan=False,
            sex=Sex.FEMALE,
        )
        # 2.8 g/kg lean mass → 50 * 2.8 = 140 g protein.
        self.assertAlmostEqual(protein_g, 140.0, delta=0.5,
                               msg="female at 13% BF should get 2.8 g/kg lean-cut multiplier")

    def test_male_at_13pct_bf_does_not_get_lean_cut(self):
        # Male at 13% BF is NOT in the lean-cut range (threshold 12% for men).
        lean_mass = 70.0
        protein_g, _ = _protein_target(
            goal=GoalArchetype.FAT_LOSS, weight_kg=80,
            lean_mass_kg=lean_mass, body_fat_pct=13.0,
            target_weight_kg=None, is_vegan=False,
            sex=Sex.MALE,
        )
        # 2.5 g/kg lean mass → 70 * 2.5 = 175 g protein (not 2.8 = 196).
        self.assertAlmostEqual(protein_g, 175.0, delta=0.5)


# =========================================================================== #
# P1-6: StrengthEstimate.rationale field populated on clamp
# =========================================================================== #
class TestP01Fix6_StrengthEstimateRationale(unittest.TestCase):
    def test_rationale_populated_when_reps_clamped(self):
        # reps > MAX_1RM_REPS triggers clamping; rationale should be non-empty.
        est = one_rep_max(weight=100, reps=MAX_1RM_REPS + 5)
        self.assertTrue(
            est.rationale,
            "rationale should be populated when reps are clamped; got empty string",
        )
        self.assertIn("clamped", est.rationale.lower())

    def test_rationale_empty_when_no_clamp(self):
        est = one_rep_max(weight=100, reps=5)
        self.assertEqual(est.rationale, "",
                         "rationale should be empty when no clamping occurred")


# =========================================================================== #
# P1-7: _validate_positive rejects bad inputs
# =========================================================================== #
class TestP01Fix7_ValidatePositive(unittest.TestCase):
    def test_rejects_negative(self):
        with self.assertRaises(ValueError):
            _validate_positive("x", -5)

    def test_rejects_zero_by_default(self):
        with self.assertRaises(ValueError):
            _validate_positive("x", 0)

    def test_allows_zero_when_flagged(self):
        _validate_positive("x", 0, allow_zero=True)  # should not raise

    def test_rejects_nan(self):
        with self.assertRaises(ValueError):
            _validate_positive("x", float("nan"))

    def test_rejects_inf(self):
        with self.assertRaises(ValueError):
            _validate_positive("x", float("inf"))

    def test_rejects_string(self):
        with self.assertRaises(ValueError):
            _validate_positive("x", "5")

    def test_rejects_bool(self):
        with self.assertRaises(ValueError):
            _validate_positive("x", True)

    def test_rejects_none(self):
        with self.assertRaises(ValueError):
            _validate_positive("x", None)

    def test_bmi_rejects_negative_weight(self):
        with self.assertRaises(ValueError):
            bmi(-5, 178)

    def test_bmr_mifflin_rejects_negative_age(self):
        with self.assertRaises(ValueError):
            bmr_mifflin(70, 178, -10, Sex.MALE)

    def test_hydration_rejects_negative_weight(self):
        with self.assertRaises(ValueError):
            hydration(-80, 30, Sex.MALE)

    def test_muscular_potential_rejects_impossible_bf(self):
        with self.assertRaises(ValueError):
            muscular_potential(178, 80, 200)

    def test_micronutrient_targets_rejects_zero_calories(self):
        with self.assertRaises(ValueError):
            micronutrient_targets(0)


# =========================================================================== #
# P1-8: cardio_zones no integer overlap
# =========================================================================== #
class TestP01Fix8_CardioZonesNoOverlap(unittest.TestCase):
    def test_no_zone_overlap_at_integer_boundaries(self):
        zones = cardio_zones(40, 60).zones
        # Z1.high must be < Z2.low (after the fix that adds +1 to non-first lows).
        z1_high = zones["Z1_recovery"][1]
        z2_low = zones["Z2_aerobic_base"][0]
        self.assertLess(
            z1_high, z2_low,
            f"Z1.high ({z1_high}) must be < Z2.low ({z2_low}) — no overlap",
        )
        z2_high = zones["Z2_aerobic_base"][1]
        z3_low = zones["Z3_tempo"][0]
        self.assertLess(z2_high, z3_low)
        z3_high = zones["Z3_tempo"][1]
        z4_low = zones["Z4_threshold"][0]
        self.assertLess(z3_high, z4_low)
        z4_high = zones["Z4_threshold"][1]
        z5_low = zones["Z5_vo2max"][0]
        self.assertLess(z4_high, z5_low)


# =========================================================================== #
# P1-6 (Task 5): ClientProfile.from_dict lists missing fields
# =========================================================================== #
class TestP01Fix6_FromDictErrorMessages(unittest.TestCase):
    def test_missing_required_field_lists_all_missing(self):
        with self.assertRaises(ValueError) as ctx:
            ClientProfile.from_dict({"age": 30})
        # Error should mention the missing required fields.
        msg = str(ctx.exception)
        self.assertIn("sex", msg)
        self.assertIn("height_cm", msg)
        self.assertIn("weight_kg", msg)

    def test_non_dict_input_raises_typeerror(self):
        with self.assertRaises(TypeError):
            ClientProfile.from_dict([1, 2, 3])
        with self.assertRaises(TypeError):
            ClientProfile.from_dict("not a dict")


# =========================================================================== #
# P1-7 (Task 5): __post_init__ produces actionable type errors
# =========================================================================== #
class TestP01Fix7_PostInitTypeErrors(unittest.TestCase):
    def test_string_age_raises_valueerror_not_typeerror(self):
        with self.assertRaises(ValueError) as ctx:
            ClientProfile(
                age="thirty", sex="male", height_cm=178, weight_kg=75,
            )
        msg = str(ctx.exception)
        self.assertIn("age", msg)
        self.assertIn("number", msg.lower())


# =========================================================================== #
# P1-12: recommend() asserts 7-day meal plan
# =========================================================================== #
class TestP01Fix12_AssertSevenDayPlan(unittest.TestCase):
    def test_recommend_produces_seven_day_plan(self):
        p = ClientProfile(
            age=30, sex=Sex.MALE, height_cm=178, weight_kg=75,
            primary_goal=GoalArchetype.GENERAL_HEALTH,
            experience=ExperienceLevel.INTERMEDIATE,
            days_per_week=4, environment=TrainingEnvironment.GYM_FULL,
            dietary_preference=DietaryPreference.OMNIVORE,
        )
        rec = Recommender(p).recommend()
        self.assertEqual(
            len(rec.nutrition.weekly_meal_plan.days), 7,
            "weekly_meal_plan must have exactly 7 days",
        )


# =========================================================================== #
# P1-13: PURGATORY category reachable via diet_history_confused
# =========================================================================== #
class TestP01Fix13_PurgatoryReachable(unittest.TestCase):
    def test_diet_history_confused_can_reach_purgatory(self):
        from fitness_engine import classify_trainee
        # Iterate BF% to find a configuration where PURGATORY is returned.
        # The gate is diet_history_confused=True plus a non-shredded, non-obese
        # body composition that would otherwise route to a different category.
        found_purgatory = False
        for bf in [10, 15, 20, 25, 30]:
            for bmi_val in [20, 23, 26, 28]:
                for sex in [Sex.MALE, Sex.FEMALE]:
                    for exp in [ExperienceLevel.BEGINNER,
                                ExperienceLevel.INTERMEDIATE,
                                ExperienceLevel.ADVANCED]:
                        t = classify_trainee(
                            bf, exp, sex, bmi_val,
                            diet_history_confused=True,
                        )
                        if "PURGATORY" in t.category.name:
                            found_purgatory = True
                            break
        self.assertTrue(
            found_purgatory,
            "PURGATORY category was never returned even with diet_history_confused=True",
        )


# =========================================================================== #
# P1-14: FULL_INTAKE covers core demographics
# =========================================================================== #
class TestP01Fix14_FullIntakeCoversCoreDemographics(unittest.TestCase):
    def test_core_demographics_section_exists(self):
        section_names = [name for name, _ in FULL_INTAKE]
        self.assertIn("Core Demographics", section_names)

    def test_core_demographics_includes_required_fields(self):
        core_fields = {item[0] for item in CORE_DEMOGRAPHICS}
        for required in ("age", "sex", "height_cm", "weight_kg"):
            self.assertIn(required, core_fields)


# =========================================================================== #
# P1-5: intake_report is sex-aware
# =========================================================================== #
class TestP01Fix5_IntakeReportSexAware(unittest.TestCase):
    def test_female_26pct_bf_not_flagged_as_moderate(self):
        # Female at 26% BF is healthy; previously she got "Moderate body fat —
        # steady cut" advice identical to a male at 26% BF.
        rep = intake_report(
            bmi_val=22.0, body_fat_pct=26.0, calorie_target=2000,
            sex=Sex.FEMALE,
        )
        moderate_msgs = [r for r in rep.recommendations if "Moderate body fat" in r]
        self.assertEqual(
            moderate_msgs, [],
            "female at 26% BF should NOT get 'Moderate body fat — steady cut' advice",
        )

    def test_male_26pct_bf_flagged_as_moderate(self):
        rep = intake_report(
            bmi_val=26.0, body_fat_pct=26.0, calorie_target=2000,
            sex=Sex.MALE,
        )
        moderate_msgs = [r for r in rep.recommendations if "Moderate body fat" in r]
        self.assertTrue(moderate_msgs, "male at 26% BF SHOULD get 'Moderate body fat' advice")

    def test_calorie_floor_sex_aware(self):
        # Male at 1400 kcal should warn (below 1500 floor).
        rep_m = intake_report(bmi_val=22, body_fat_pct=15, calorie_target=1400, sex=Sex.MALE)
        self.assertTrue(any("1500" in w for w in rep_m.warnings))
        # Female at 1400 kcal should NOT warn (above 1200 floor).
        rep_f = intake_report(bmi_val=22, body_fat_pct=25, calorie_target=1400, sex=Sex.FEMALE)
        self.assertFalse(any("1500" in w for w in rep_f.warnings))


# =========================================================================== #
# P1-17: motivation normalization handles empty string
# =========================================================================== #
class TestP01Fix17_MotivationNormalization(unittest.TestCase):
    def test_empty_string_normalized_to_appearance(self):
        p = ClientProfile(
            age=30, sex=Sex.MALE, height_cm=178, weight_kg=75,
            motivation="",
        )
        self.assertEqual(p.motivation, "appearance",
                         "empty string motivation must normalize to 'appearance'")

    def test_whitespace_normalized_to_appearance(self):
        p = ClientProfile(
            age=30, sex=Sex.MALE, height_cm=178, weight_kg=75,
            motivation="   ",
        )
        self.assertEqual(p.motivation, "appearance")


# =========================================================================== #
# P1-9: exercise_database.ScrapedExercise coerces string numerics
# =========================================================================== #
class TestP01Fix9_ScrapedExerciseTypeCoercion(unittest.TestCase):
    def test_string_difficulty_coerced_to_int(self):
        from fitness_engine.exercise_database import ScrapedExercise
        ex = ScrapedExercise(
            id="test", name="Test", pattern="push",
            primary_muscle="chest", difficulty="3",
            views="7400000", comments="42",
        )
        self.assertEqual(ex.difficulty, 3)
        self.assertEqual(ex.views, 7400000)
        self.assertEqual(ex.comments, 42)

    def test_mechanics_lowercased(self):
        from fitness_engine.exercise_database import ScrapedExercise
        ex = ScrapedExercise(
            id="test", name="Test", pattern="push",
            primary_muscle="chest", mechanics="Compound",
        )
        self.assertEqual(ex.mechanics, "compound")


# =========================================================================== #
# P1-7 (Task 4): exercise_database load handles non-dict records
# =========================================================================== #
class TestP01Fix7_NonDictExerciseRecord(unittest.TestCase):
    def test_load_skips_non_dict_records(self):
        from fitness_engine.exercise_database import ExerciseDatabase
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({
                "metadata": {},
                "movement_patterns": {},
                "exercises": [
                    "not_a_dict",
                    {"id": "x", "name": "X", "pattern": "p", "primary_muscle": "m"},
                ],
            }, f)
            path = f.name
        try:
            db = ExerciseDatabase()
            db._load_database(Path(path))
            # The non-dict record is skipped; the valid one is loaded.
            self.assertIn("x", db.exercises)
        finally:
            os.unlink(path)


# =========================================================================== #
# P1-7 (Task 4): cardio_zones rejects age=0
# =========================================================================== #
class TestP01Fix7_CardioZonesRejectsZeroAge(unittest.TestCase):
    def test_zero_age_raises(self):
        with self.assertRaises(ValueError):
            cardio_zones(0)


# =========================================================================== #
# P1-9 (Task 4): weekly_tonnage rejects negative values
# =========================================================================== #
class TestP01Fix9_WeeklyTonnageRejectsNegative(unittest.TestCase):
    def test_negative_load_raises(self):
        with self.assertRaises(ValueError):
            weekly_tonnage([{"sets": 3, "reps": 10, "load_kg": -80}])


# =========================================================================== #
# P1-10 (Task 4): ideal_body_weight_devine rejects negative height
# =========================================================================== #
class TestP01Fix10_DevineRejectsNegativeHeight(unittest.TestCase):
    def test_negative_height_raises(self):
        with self.assertRaises(ValueError):
            ideal_body_weight_devine(-178, Sex.MALE)


if __name__ == "__main__":
    unittest.main()


# =========================================================================== #
# P2 regression tests (added in third pass)
# =========================================================================== #
class TestP2_FrozenDataclasses(unittest.TestCase):
    """P2 #16 — result containers should be immutable."""

    def test_macros_is_frozen(self):
        m = _make_macros()
        with self.assertRaises((AttributeError, Exception)):
            m.calories = 999  # type: ignore[misc]

    def test_mealitem_is_frozen(self):
        from fitness_engine.meal_plans import MealItem
        m = MealItem(name="t", cuisine="a", slot="dinner",
                     calories=100, protein_g=10, carbs_g=10, fat_g=5, fibre_g=3)
        with self.assertRaises((AttributeError, Exception)):
            m.calories = 999  # type: ignore[misc]

    def test_exercise_is_frozen(self):
        from fitness_engine.exercise_plans import Exercise
        e = Exercise(name="t", pattern="p", primary_muscle="m")
        with self.assertRaises((AttributeError, Exception)):
            e.name = "modified"  # type: ignore[misc]


class TestP2_SexAwareProteinThreshold(unittest.TestCase):
    """P1 #4 follow-up — structured version is also sex-aware."""

    def test_female_lean_cut_uses_20pct_threshold(self):
        from fitness_engine.calculators import _protein_target_structured
        result = _protein_target_structured(
            goal=GoalArchetype.FAT_LOSS, weight_kg=60,
            lean_mass_kg=50, body_fat_pct=15.0,
            target_weight_kg=None, is_vegan=False,
            sex=Sex.FEMALE,
        )
        # 15% BF < 20% female threshold → lean_cut → mult=2.8.
        self.assertAlmostEqual(result["multiplier"], 2.8)


class TestP2_AgeGroupSenior(unittest.TestCase):
    """P2 #18 — SENIOR bucket exists for ages 65+."""

    def test_65_returns_senior(self):
        from fitness_engine import infer_age_group
        from fitness_engine.archetypes import AgeGroup
        self.assertEqual(infer_age_group(65), AgeGroup.SENIOR)
        self.assertEqual(infer_age_group(90), AgeGroup.SENIOR)

    def test_50_returns_middle(self):
        from fitness_engine import infer_age_group
        from fitness_engine.archetypes import AgeGroup
        self.assertEqual(infer_age_group(50), AgeGroup.MIDDLE)

    def test_negative_age_raises(self):
        from fitness_engine import infer_age_group
        with self.assertRaises(ValueError):
            infer_age_group(5)


class TestP2_WeeklyTonnageRename(unittest.TestCase):
    """P2 #19 + NEW-V1-9 — load_kg renamed and CORRECTED to avg_load_per_rep_kg."""

    def test_avg_load_per_rep_kg_field(self):
        from fitness_engine import weekly_tonnage
        # NEW-V1-9: avg_load_per_rep_kg is now the mean of session load_kg
        # values, not total_volume/total_reps. For one session at 100 kg,
        # the average load per rep is 100 kg (the session's load).
        t = weekly_tonnage([{"sets": 3, "reps": 10, "load_kg": 100}])
        self.assertEqual(t.avg_load_per_rep_kg, 100.0)
        self.assertEqual(t.total_volume_kg, 3000.0)

    def test_load_kg_backwards_compat_property(self):
        from fitness_engine import weekly_tonnage
        t = weekly_tonnage([{"sets": 3, "reps": 10, "load_kg": 100}])
        # P2 #19 + NEW-V1-9 — backwards-compat property returns the legacy
        # (misleading) value: total_volume / total_reps = 3000/10 = 300.
        self.assertEqual(t.load_kg, 300.0)


class TestP2_SchemaNotNullMigration(unittest.TestCase):
    """P2 #35, NEW-P2 #17 — schema NOT NULL constraints + migration."""

    def test_init_db_creates_v3_schema(self):
        import tempfile
        from fitness_engine.persistence import init_db, connect, SCHEMA_VERSION
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            path = tmp.name
        try:
            init_db(path)
            with connect(path) as con:
                # Schema version should be 3 after init.
                row = con.execute("PRAGMA user_version").fetchone()
                self.assertEqual(row[0], SCHEMA_VERSION)
                # clients.name should be NOT NULL.
                schema = con.execute("PRAGMA table_info(clients)").fetchall()
                name_col = [c for c in schema if c["name"] == "name"][0]
                # notnull=1 means NOT NULL constraint.
                self.assertEqual(name_col["notnull"], 1,
                                 f"clients.name should be NOT NULL, got notnull={name_col['notnull']}")
        finally:
            os.unlink(path)


class TestP2_JsonDefaultRaises(unittest.TestCase):
    """P2 #36 — _json_default raises TypeError for unknown types."""

    def test_unknown_type_raises(self):
        from fitness_engine.persistence import _json_default
        class Foo:
            pass
        with self.assertRaises(TypeError):
            _json_default(Foo())


class TestP2_CutBulkBoundaryEnumKeyed(unittest.TestCase):
    """P2 #33 — CUT_BULK_BOUNDARIES keyed by Sex enum; helper accepts str too."""

    def test_sex_enum_lookup(self):
        from fitness_engine.adjustments import cut_bulk_boundary, CUT_BULK_BOUNDARIES
        from fitness_engine.archetypes import Sex
        self.assertEqual(cut_bulk_boundary(Sex.MALE), CUT_BULK_BOUNDARIES[Sex.MALE])

    def test_string_lookup_backwards_compat(self):
        from fitness_engine.adjustments import cut_bulk_boundary
        # "male" string should also work via the helper.
        result = cut_bulk_boundary("male")
        self.assertEqual(result["end_cut"], 10)

    def test_invalid_string_raises(self):
        from fitness_engine.adjustments import cut_bulk_boundary
        with self.assertRaises(ValueError):
            cut_bulk_boundary("klingon")


class TestP2_AllergenPluralSymmetry(unittest.TestCase):
    """P2 #24 — "peas" allergen matches both "pea" and "peas" ingredients."""

    def test_peas_matches_pea(self):
        # Build a fake recipe with "pea" (not "peas") in ingredients.
        # We can't easily inject into MEAL_LIBRARY, so just verify the
        # pattern-building logic via _allergen_ok (which shares the same
        # regex construction).
        from fitness_engine.seven_day_meal_planner import _allergen_ok
        from fitness_engine.meal_plans import MealItem
        recipe = MealItem(
            name="Pea Soup", cuisine="american", slot="lunch",
            calories=200, protein_g=8, carbs_g=30, fat_g=4, fibre_g=8,
            tags=["lunch"], ingredients=["split pea", "broth"],
        )
        # Allergen "peas" (plural) should match ingredient "pea" (singular).
        self.assertFalse(_allergen_ok(recipe, ["peas"]),
                         msg="allergen 'peas' should match ingredient 'pea'")


class TestP2_ArchetypeSignatureSessionCode(unittest.TestCase):
    """P2 #38 — explicit _SESSION_CODES mapping."""

    def test_all_session_lengths_have_codes(self):
        from fitness_engine.archetypes import _SESSION_CODES, SessionLength
        for sl in SessionLength:
            self.assertIn(sl, _SESSION_CODES,
                          msg=f"SessionLength.{sl.name} missing from _SESSION_CODES")


class TestP2_CardioZonesNoOverlap(unittest.TestCase):
    """P1 #8 follow-up — verify all 4 zone boundaries don't overlap."""

    def test_all_zone_boundaries_strictly_increasing(self):
        zones = cardio_zones(40, 60).zones
        # All zone lows should be strictly less than their highs.
        for name, (lo, hi) in zones.items():
            self.assertLessEqual(lo, hi, f"{name}: low {lo} > high {hi}")
        # And consecutive zones should not overlap.
        ordered = [zones["Z1_recovery"], zones["Z2_aerobic_base"],
                   zones["Z3_tempo"], zones["Z4_threshold"], zones["Z5_vo2max"]]
        for i in range(len(ordered) - 1):
            self.assertLess(ordered[i][1], ordered[i + 1][0],
                            f"Zone {i} high ({ordered[i][1]}) >= Zone {i+1} low ({ordered[i+1][0]})")


class TestP2_IntakeReportOffByOne(unittest.TestCase):
    """P2 #28 — calorie_target <= floor triggers warning (was <)."""

    def test_exactly_at_floor_warns(self):
        # Male floor is 1500; calorie_target = 1500 should warn.
        rep = intake_report(bmi_val=22, body_fat_pct=15, calorie_target=1500, sex=Sex.MALE)
        self.assertTrue(any("1500" in w for w in rep.warnings),
                        msg="calorie_target=1500 (exactly at male floor) should warn")


class TestP2_InitialAssessmentNoGoalParam(unittest.TestCase):
    """P2 #35 — initial_assessment_guidance_structured no longer takes goal."""

    def test_signature_without_goal(self):
        from fitness_engine.adjustments import initial_assessment_guidance_structured
        import inspect
        sig = inspect.signature(initial_assessment_guidance_structured)
        self.assertNotIn("goal", sig.parameters,
                         msg="goal parameter should be removed")
        self.assertIn("expected_change_per_week_kg", sig.parameters)


# =========================================================================== #
# V1 verification follow-up tests
# =========================================================================== #
class TestV1_CalorieTargetActivityTiered(unittest.TestCase):
    """T3 P1 #5 — calorie_target NEAT buffer is now activity-tiered."""

    def test_highly_active_gets_no_buffer(self):
        from fitness_engine import calorie_target
        from fitness_engine.archetypes import ActivityLevel, ExperienceLevel, GoalArchetype, Sex
        # Very active bulk: NEAT buffer should be 1.0 (no buffer).
        target, breakdown = calorie_target(
            tdee_value=2500, goal=GoalArchetype.MUSCLE_GAIN,
            bodyweight_kg=80, experience=ExperienceLevel.BEGINNER,
            sex=Sex.MALE, activity=ActivityLevel.VERY_ACTIVE,
        )
        self.assertEqual(breakdown["neat_buffer_pct"], 0)

    def test_sedentary_gets_50pct_buffer(self):
        from fitness_engine import calorie_target
        from fitness_engine.archetypes import ActivityLevel, ExperienceLevel, GoalArchetype, Sex
        target, breakdown = calorie_target(
            tdee_value=2500, goal=GoalArchetype.MUSCLE_GAIN,
            bodyweight_kg=80, experience=ExperienceLevel.BEGINNER,
            sex=Sex.MALE, activity=ActivityLevel.SEDENTARY,
        )
        self.assertEqual(breakdown["neat_buffer_pct"], 50)

    def test_lightly_active_gets_25pct_buffer(self):
        from fitness_engine import calorie_target
        from fitness_engine.archetypes import ActivityLevel, ExperienceLevel, GoalArchetype, Sex
        target, breakdown = calorie_target(
            tdee_value=2500, goal=GoalArchetype.MUSCLE_GAIN,
            bodyweight_kg=80, experience=ExperienceLevel.BEGINNER,
            sex=Sex.MALE, activity=ActivityLevel.LIGHTLY_ACTIVE,
        )
        self.assertEqual(breakdown["neat_buffer_pct"], 25)


class TestV1_AnthropometricIndicesValidation(unittest.TestCase):
    """T3 P1 #9 — anthropometric_indices validates waist<hip."""

    def test_waist_ge_hip_adds_warning_note(self):
        from fitness_engine import anthropometric_indices
        from fitness_engine.archetypes import Sex
        result = anthropometric_indices(170, 70, Sex.FEMALE, waist_cm=100, hip_cm=80)
        # Should still compute, but include a warning note about the unusual ratio.
        self.assertTrue(any(">= hip_cm" in note or "unusual" in note.lower() for note in result.notes),
                        msg=f"Expected warning note about waist>=hip; got notes: {result.notes}")

    def test_negative_waist_raises(self):
        from fitness_engine import anthropometric_indices
        from fitness_engine.archetypes import Sex
        with self.assertRaises(ValueError):
            anthropometric_indices(170, 70, Sex.MALE, waist_cm=-10, hip_cm=90)


class TestV1_FatLossRateValidation(unittest.TestCase):
    """T3 P1 #7 — fat_loss_rate_for_bodyfat validates input range."""

    def test_negative_bf_raises(self):
        from fitness_engine import fat_loss_rate_for_bodyfat
        from fitness_engine.archetypes import Sex
        with self.assertRaises(ValueError):
            fat_loss_rate_for_bodyfat(-10, Sex.MALE)

    def test_excessive_bf_raises(self):
        from fitness_engine import fat_loss_rate_for_bodyfat
        from fitness_engine.archetypes import Sex
        with self.assertRaises(ValueError):
            fat_loss_rate_for_bodyfat(200, Sex.MALE)

    def test_none_bf_returns_default(self):
        from fitness_engine import fat_loss_rate_for_bodyfat, FAT_LOSS_WEEKLY_RATE
        from fitness_engine.archetypes import Sex
        self.assertEqual(fat_loss_rate_for_bodyfat(None, Sex.MALE), FAT_LOSS_WEEKLY_RATE)


class TestV1_BodyCompositionFemaleNoHipDirectCall(unittest.TestCase):
    """T3 P1 #10 — body_composition no longer crashes for female-no-hip direct call."""

    def test_female_waist_neck_no_hip_falls_through(self):
        from fitness_engine import body_composition
        from fitness_engine.archetypes import Sex
        # Direct call (not via Recommender) — should fall through to Deurenberg
        # instead of raising ValueError.
        bc = body_composition(
            weight_kg=70, height_cm=165, age=30, sex=Sex.FEMALE,
            waist_cm=78, neck_cm=32, hip_cm=None,
        )
        self.assertIsNotNone(bc.body_fat_pct)
        self.assertNotEqual(bc.estimation_method, "navy",
                            "Female with no hip should NOT use Navy method")


class TestV1_PortionScaleThresholdsAligned(unittest.TestCase):
    """T4 P1 #10 — all three portion-scale sites use the same constants."""

    def test_scaler_clamp_range_consistent(self):
        from fitness_engine.meal_plans import _scale_meal, MealItem, PORTION_SCALE_MAX
        from fitness_engine.seven_day_meal_planner import _scale
        # Both scalers should clamp to [0.25, 3.0] now.
        meal = MealItem(name="t", cuisine="a", slot="dinner",
                        calories=100, protein_g=10, carbs_g=10, fat_g=5, fibre_g=3)
        # Try scale=10.0 — both should clamp to PORTION_SCALE_MAX.
        m1 = _scale_meal(meal, 10.0)
        m2 = _scale(meal, 10.0)
        self.assertAlmostEqual(m1.portion_scale, PORTION_SCALE_MAX)
        self.assertAlmostEqual(m2.portion_scale, PORTION_SCALE_MAX)

    def test_auditor_uses_centralised_constants(self):
        from fitness_engine.meal_plans import PORTION_SCALE_AUDIT_MIN, PORTION_SCALE_AUDIT_MAX
        # Just verify the constants are importable and have expected values.
        self.assertEqual(PORTION_SCALE_AUDIT_MIN, 0.35)
        self.assertEqual(PORTION_SCALE_AUDIT_MAX, 2.5)


class TestV1_LoadGuidanceWordBoundary(unittest.TestCase):
    """T5 P1 #3 — _load_guidance uses actual word-boundary regex."""

    def test_row_does_not_match_arrow(self):
        from fitness_engine.recommender import ClientProfile, Recommender
        from fitness_engine.archetypes import Sex, GoalArchetype, ExperienceLevel, TrainingEnvironment, DietaryPreference
        # Exercise named "Arrow Release Drill" should NOT match working_weights_kg['row'].
        p = ClientProfile(
            age=30, sex=Sex.MALE, height_cm=178, weight_kg=75,
            primary_goal=GoalArchetype.GENERAL_HEALTH,
            experience=ExperienceLevel.INTERMEDIATE,
            days_per_week=4, environment=TrainingEnvironment.GYM_FULL,
            dietary_preference=DietaryPreference.OMNIVORE,
            working_weights_kg={"row": 80.0},
        )
        rec = Recommender(p)
        # Construct a fake exercise-like object with name "Arrow Release Drill".
        class FakeEx:
            name = "Arrow Release Drill"
        result = rec._load_guidance(FakeEx(), "8-12")
        # Should NOT match because "row" is not a word boundary in "Arrow Release Drill"
        # (it's a substring of "Arrow"). Returns None.
        self.assertIsNone(result,
                          msg="'row' working weight should NOT match 'Arrow Release Drill'")


class TestV1_WeeklyTonnageCorrected(unittest.TestCase):
    """NEW-V1-9 — avg_load_per_rep_kg now correctly computes mean of session loads."""

    def test_single_session_load_returned(self):
        from fitness_engine import weekly_tonnage
        # Single session at 100 kg → avg_load_per_rep_kg should be 100.0
        # (the session's load), NOT 300.0 (the legacy total_volume/total_reps).
        t = weekly_tonnage([{"sets": 3, "reps": 10, "load_kg": 100}])
        self.assertEqual(t.avg_load_per_rep_kg, 100.0)

    def test_multi_session_mean(self):
        from fitness_engine import weekly_tonnage
        # Two sessions: 100 kg and 80 kg → mean = 90.
        t = weekly_tonnage([
            {"sets": 3, "reps": 10, "load_kg": 100},
            {"sets": 4, "reps": 8, "load_kg": 80},
        ])
        self.assertEqual(t.avg_load_per_rep_kg, 90.0)

    def test_legacy_load_kg_property_preserved(self):
        from fitness_engine import weekly_tonnage
        t = weekly_tonnage([{"sets": 3, "reps": 10, "load_kg": 100}])
        # Legacy property returns the OLD (misleading) value for backwards compat.
        # 3000 / 10 = 300.
        self.assertEqual(t.load_kg, 300.0)


class TestV1_AllOpenCallsHaveEncoding(unittest.TestCase):
    """NEW-V1-1, NEW-V1-2 — all open() calls use encoding='utf-8'."""

    def test_no_open_without_encoding_in_engine(self):
        import os
        engine_dir = "/home/z/my-project/fit/fitness_engine"
        offenders = []
        for root, _, files in os.walk(engine_dir):
            for fname in files:
                if not fname.endswith(".py"):
                    continue
                path = os.path.join(root, fname)
                with open(path, encoding="utf-8") as f:
                    for lineno, line in enumerate(f, 1):
                        # Find open( calls that don't specify encoding.
                        if "open(" in line and "encoding" not in line:
                            # Skip comments and docstrings (rough heuristic).
                            stripped = line.strip()
                            if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
                                continue
                            offenders.append(f"{path}:{lineno}: {stripped}")
        # Allow no offenders.
        self.assertEqual(offenders, [], msg=f"open() calls without encoding: {offenders}")


class TestV1_RecommenderDataclassesFrozen(unittest.TestCase):
    """NEW-V1-3 — TrainingPlan, NutritionPlan, PlanRecommendation are frozen."""

    def test_plan_recommendation_is_frozen(self):
        from fitness_engine.recommender import PlanRecommendation
        # Check that the dataclass has frozen=True in its params.
        params = PlanRecommendation.__dataclass_params__
        self.assertTrue(params.frozen,
                        msg="PlanRecommendation should be frozen=True")

    def test_training_plan_is_frozen(self):
        from fitness_engine.recommender import TrainingPlan
        params = TrainingPlan.__dataclass_params__
        self.assertTrue(params.frozen)
