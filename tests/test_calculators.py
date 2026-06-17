"""
test_calculators.py
===================

Unit tests for the numerical calculators, grounded in the RippedBody
methodology. Run with:
    python3 -m unittest tests.test_calculators
"""
import unittest

from fitness_engine import (
    ActivityLevel, GoalArchetype, Sex, ExperienceLevel,
    bmi, bmi_category, bmr_harris_benedict, bmr_mifflin, bmr_katch,
    body_fat_from_visual,
    body_composition, correct_bf_estimate,
    tdee, calorie_target, energy_expenditure,
    one_rep_max, cardio_zones, hydration, macros_for,
    micronutrient_targets, muscular_potential,
    anthropometric_indices, adjust_macros_for_calorie_change,
    adaptive_tdee, DailyLog, reverse_diet_protocol,
    infer_age_group, infer_somatotype, classify_trainee,
    weekly_tonnage, MAX_1RM_REPS,
)
from fitness_engine.archetypes import Somatotype, DietaryPreference


class TestBMI(unittest.TestCase):
    def test_normal(self):
        self.assertAlmostEqual(bmi(70, 175), 22.86, places=1)

    def test_categories(self):
        self.assertEqual(bmi_category(17), "underweight")
        self.assertEqual(bmi_category(22), "normal")
        self.assertEqual(bmi_category(27), "overweight")
        self.assertEqual(bmi_category(32), "obese_class_i")
        self.assertEqual(bmi_category(42), "obese_class_iii")

    def test_invalid_height(self):
        with self.assertRaises(ValueError):
            bmi(70, 0)


class TestBMR(unittest.TestCase):
    def test_harris_benedict_male(self):
        # 30y male, 80kg, 180cm
        # 66 + (13.7*80) + (5*180) - (6.8*30) = 66+1096+900-204 = 1858
        self.assertEqual(bmr_harris_benedict(80, 180, 30, Sex.MALE), 1858.0)

    def test_harris_benedict_female(self):
        # 30y female, 60kg, 165cm
        # 655 + (9.6*60) + (1.8*165) - (4.7*30) = 655+576+297-141 = 1387
        self.assertEqual(bmr_harris_benedict(60, 165, 30, Sex.FEMALE), 1387.0)

    def test_katch_single_arg(self):
        self.assertEqual(bmr_katch(60), 370 + 21.6 * 60)

    def test_katch_invalid(self):
        with self.assertRaises(ValueError):
            bmr_katch(0)


class TestTDEE(unittest.TestCase):
    def test_sedentary(self):
        self.assertAlmostEqual(tdee(1500, ActivityLevel.SEDENTARY), 1875.0)

    def test_highly_active(self):
        self.assertEqual(tdee(1500, ActivityLevel.HIGHLY_ACTIVE), 2700.0)


class TestCalorieTarget(unittest.TestCase):
    def test_fat_loss_deficit(self):
        target, bd = calorie_target(2500, GoalArchetype.FAT_LOSS,
                                     bodyweight_kg=80,
                                     experience=ExperienceLevel.INTERMEDIATE)
        self.assertLess(target, 2500)
        self.assertEqual(bd["mode"], "fat_loss (cut)")

    def test_muscle_gain_surplus(self):
        target, bd = calorie_target(2500, GoalArchetype.MUSCLE_GAIN,
                                     bodyweight_kg=70,
                                     experience=ExperienceLevel.BEGINNER)
        self.assertGreater(target, 2500)
        self.assertEqual(bd["mode"], "muscle_gain (bulk)")

    def test_recomp_maintenance(self):
        target, _ = calorie_target(2500, GoalArchetype.RECOMPOSITION,
                                    bodyweight_kg=70,
                                    experience=ExperienceLevel.INTERMEDIATE)
        self.assertEqual(target, 2500.0)

    def test_minimum_floor(self):
        target, bd = calorie_target(800, GoalArchetype.FAT_LOSS,
                                     bodyweight_kg=50,
                                     experience=ExperienceLevel.ADVANCED)
        self.assertGreaterEqual(target, 1200)
        self.assertIn("warning", bd)

    def test_bulk_experience_tiers(self):
        """Beginners get a bigger surplus than advanced."""
        beg, _ = calorie_target(2500, GoalArchetype.MUSCLE_GAIN, 70,
                                ExperienceLevel.BEGINNER)
        adv, _ = calorie_target(2500, GoalArchetype.MUSCLE_GAIN, 70,
                                ExperienceLevel.ADVANCED)
        self.assertGreater(beg, adv)


class TestMacros(unittest.TestCase):
    def test_protein_by_lean_mass(self):
        """Cutting with known BF% → 2.5 g/kg lean mass."""
        m = macros_for(2000, 80, 64, GoalArchetype.FAT_LOSS, Sex.MALE,
                       Somatotype.MESOMORPH, DietaryPreference.OMNIVORE,
                       body_fat_pct=20)
        self.assertAlmostEqual(m.protein_g, 64 * 2.5, places=1)

    def test_protein_by_body_weight(self):
        """Bulking with unknown BF% → 1.6 g/kg body weight."""
        m = macros_for(2500, 70, None, GoalArchetype.MUSCLE_GAIN, Sex.MALE,
                       Somatotype.MESOMORPH, DietaryPreference.OMNIVORE)
        self.assertAlmostEqual(m.protein_g, 70 * 1.6, places=1)

    def test_fat_within_band(self):
        m = macros_for(2000, 70, 55, GoalArchetype.GENERAL_HEALTH, Sex.MALE,
                       Somatotype.MESOMORPH, DietaryPreference.OMNIVORE)
        self.assertGreaterEqual(m.fat_pct, 15)
        self.assertLessEqual(m.fat_pct, 30)

    def test_macro_sum(self):
        m = macros_for(2200, 70, 55, GoalArchetype.RECOMPOSITION, Sex.FEMALE,
                       Somatotype.ENDOMORPH, DietaryPreference.OMNIVORE)
        total_kcal = m.protein_g*4 + m.carbs_g*4 + m.fat_g*9
        self.assertLess(abs(total_kcal - m.calories), 100)

    def test_fat_floor_enforced(self):
        # Fat floor of 0.5 g/kg = 45 g for a 90-kg male. At 2200 kcal
        # (rather than the old 1200 kcal), the floors fit and we can verify
        # the fat floor is honored.
        m = macros_for(2200, 90, 60, GoalArchetype.FAT_LOSS, Sex.MALE,
                       Somatotype.ENDOMORPH, DietaryPreference.OMNIVORE,
                       body_fat_pct=25)
        self.assertGreaterEqual(m.fat_g, 90 * 0.5)

    def test_impossible_macro_combination_raises(self):
        """When calorie target is too low to satisfy protein+fat+carb floors,
        macros_for must raise ValueError rather than silently returning
        a split whose caloric sum exceeds the target. See audit C2."""
        with self.assertRaisesRegex(ValueError, "Cannot satisfy macro floors"):
            macros_for(1200, 90, 60, GoalArchetype.FAT_LOSS, Sex.MALE,
                       Somatotype.ENDOMORPH, DietaryPreference.OMNIVORE,
                       body_fat_pct=25)

    def test_keto_caps_carbs(self):
        m = macros_for(2200, 80, 64, GoalArchetype.FAT_LOSS, Sex.MALE,
                       Somatotype.MESOMORPH, DietaryPreference.KETO,
                       body_fat_pct=20)
        self.assertLessEqual(m.carbs_g, 50)
        self.assertGreater(m.fat_pct, 50)

    def test_mediterranean_higher_fat_preset(self):
        m = macros_for(2400, 80, 64, GoalArchetype.GENERAL_HEALTH, Sex.MALE,
                       Somatotype.MESOMORPH, DietaryPreference.MEDITERRANEAN,
                       body_fat_pct=20)
        self.assertAlmostEqual(m.fat_pct, 35, delta=2)


class TestOneRepMax(unittest.TestCase):
    def test_epley(self):
        r = one_rep_max(100, 5)
        self.assertAlmostEqual(r.epley_1rm, 116.7, places=1)

    def test_high_reps_clamped(self):
        high = one_rep_max(100, 50)
        clamped = one_rep_max(100, MAX_1RM_REPS)
        self.assertAlmostEqual(high.average_1rm, clamped.average_1rm, places=1)

    def test_no_negative(self):
        for reps in range(1, 100):
            est = one_rep_max(100, reps)
            self.assertGreater(est.average_1rm, 0)

    def test_invalid_reps(self):
        with self.assertRaises(ValueError):
            one_rep_max(100, 0)

    def test_invalid_weight(self):
        with self.assertRaises(ValueError):
            one_rep_max(0, 5)


class TestCardioZones(unittest.TestCase):
    def test_zones_present(self):
        z = cardio_zones(30, 60)
        self.assertIn("Z2_aerobic_base", z.zones)
        self.assertLess(z.zones["Z2_aerobic_base"][0],
                        z.zones["Z4_threshold"][0])


class TestHydration(unittest.TestCase):
    def test_base(self):
        self.assertEqual(hydration(80, 0).base_ml, 2400.0)

    def test_workout_bonus(self):
        self.assertEqual(hydration(80, 60).workout_bonus_ml, 700.0)


class TestVisualBodyFat(unittest.TestCase):
    def test_visual_label(self):
        # Updated midpoints after F6 (contiguous bands, no gaps).
        self.assertEqual(body_fat_from_visual("shredded"), 8.5)
        self.assertEqual(body_fat_from_visual("average_fit"), 16.5)
        self.assertEqual(body_fat_from_visual("obese"), 30.0)

    def test_invalid_label(self):
        with self.assertRaises(ValueError):
            body_fat_from_visual("nonexistent")

    def test_body_composition_uses_visual(self):
        bc = body_composition(80, 178, 30, Sex.MALE, visual_bf_label="lean")
        self.assertEqual(bc.estimation_method, "visual")
        # Updated midpoint after F6 (lean band now 12-15%, midpoint 13.5).
        self.assertEqual(bc.body_fat_pct, 13.5)

    def test_body_composition_priority(self):
        """User-supplied BF% takes priority over visual."""
        bc = body_composition(80, 178, 30, Sex.MALE,
                              bf_pct=18, visual_bf_label="lean")
        self.assertEqual(bc.estimation_method, "user_input")
        self.assertEqual(bc.body_fat_pct, 18)


class TestInferFunctions(unittest.TestCase):
    def test_age_groups(self):
        self.assertEqual(infer_age_group(25).value, "young")
        self.assertEqual(infer_age_group(35).value, "adult")
        self.assertEqual(infer_age_group(50).value, "middle")

    def test_somatotype(self):
        self.assertEqual(
            infer_somatotype(70, 175, 30, Sex.MALE, body_fat_pct=10).value,
            "ectomorph")
        self.assertEqual(
            infer_somatotype(95, 175, 30, Sex.MALE, body_fat_pct=28).value,
            "endomorph")
        self.assertEqual(
            infer_somatotype(80, 175, 30, Sex.MALE, body_fat_pct=16).value,
            "mesomorph")

    def test_somatotype_wrist_refinement(self):
        meso = infer_somatotype(76, 175, 30, Sex.MALE, body_fat_pct=16)
        self.assertEqual(meso, Somatotype.MESOMORPH)
        ecto = infer_somatotype(76, 175, 30, Sex.MALE,
                                body_fat_pct=16, wrist_cm=15.0)
        self.assertEqual(ecto, Somatotype.ECTOMORPH)


class TestClassifyTrainee(unittest.TestCase):
    def test_skinny(self):
        t = classify_trainee(8, ExperienceLevel.BEGINNER, Sex.MALE, 21)
        self.assertEqual(t.category.value, "skinny")
        self.assertEqual(t.strategy, "bulk")

    def test_fat_but_muscled(self):
        t = classify_trainee(25, ExperienceLevel.INTERMEDIATE, Sex.MALE, 28)
        self.assertEqual(t.strategy, "cut")

    def test_obese(self):
        t = classify_trainee(33, ExperienceLevel.BEGINNER, Sex.MALE, 32)
        self.assertEqual(t.category.value, "obese")
        self.assertEqual(t.strategy, "cut")

    def test_shredded(self):
        t = classify_trainee(9, ExperienceLevel.ADVANCED, Sex.MALE, 25)
        self.assertEqual(t.category.value, "shredded")

    def test_new_trainee_healthy(self):
        t = classify_trainee(12, ExperienceLevel.BEGINNER, Sex.MALE, 21)
        self.assertEqual(t.category.value, "new_trainee_healthy")
        self.assertEqual(t.strategy, "recomp")

    def test_purgatory_flag(self):
        t = classify_trainee(18, ExperienceLevel.INTERMEDIATE, Sex.MALE, 24,
                             diet_history_confused=True)
        self.assertEqual(t.category.value, "purgatory")
        self.assertEqual(t.strategy, "maintenance")


class TestWeeklyTonnage(unittest.TestCase):
    def test_basic(self):
        sessions = [{"sets": 3, "reps": 10, "load_kg": 80},
                    {"sets": 4, "reps": 8, "load_kg": 60}]
        t = weekly_tonnage(sessions)
        self.assertEqual(t.sets, 7)
        self.assertEqual(t.total_volume_kg, 4320.0)

    def test_empty(self):
        t = weekly_tonnage([])
        self.assertEqual(t.sets, 0)


class TestMicronutrients(unittest.TestCase):
    """Micronutrient targets scale with calorie intake."""

    def test_low_calories(self):
        m = micronutrient_targets(1500)
        self.assertEqual(m.fruit_cups, 2)
        self.assertEqual(m.veg_cups, 2)
        self.assertAlmostEqual(m.fibre_g, 21.0, places=1)

    def test_mid_calories(self):
        m = micronutrient_targets(2500)
        self.assertEqual(m.fruit_cups, 3)
        self.assertEqual(m.veg_cups, 3)
        self.assertAlmostEqual(m.fibre_g, 35.0, places=1)

    def test_high_calories(self):
        m = micronutrient_targets(3500)
        self.assertEqual(m.fruit_cups, 4)
        self.assertEqual(m.veg_cups, 4)

    def test_water_guidance_present(self):
        m = micronutrient_targets(2000)
        self.assertGreater(len(m.water_guidance), 2)


class TestMuscularPotential(unittest.TestCase):
    """Berkhan model and FFMI calculations."""

    def test_berkhan_model(self):
        mp = muscular_potential(178, 82, 18)
        # Berkhan: 178 - 100 = 78
        self.assertEqual(mp.berkhan_stage_max_kg, 78.0)

    def test_ffmi_calculated(self):
        mp = muscular_potential(178, 82, 18)
        # lean = 82 * 0.82 = 67.24, height_m = 1.78
        # FFMI = 67.24 / (1.78^2) = 67.24 / 3.1684 = 21.2
        self.assertGreater(mp.ffmi, 18)
        self.assertLess(mp.ffmi, 26)

    def test_ceiling(self):
        mp = muscular_potential(180, 90, 10)
        self.assertEqual(mp.ceiling_ffmi, 25.0)


class TestBFEstimateCorrection(unittest.TestCase):
    """Self-estimates should be bumped by 50%."""

    def test_self_estimate_corrected(self):
        self.assertEqual(correct_bf_estimate(15, is_self_estimate=True), 22.5)

    def test_known_value_unchanged(self):
        self.assertEqual(correct_bf_estimate(20, is_self_estimate=False), 20)


class TestVeganProtein(unittest.TestCase):
    """Vegan protein targets should be higher than omnivore."""

    def test_vegan_cutting_higher(self):
        """Cutting with known BF%: vegan 2.6 vs omni 2.5 g/kg lean."""
        lean = 60
        m_v = macros_for(1800, 80, lean, GoalArchetype.FAT_LOSS, Sex.MALE,
                         Somatotype.MESOMORPH, DietaryPreference.VEGAN,
                         body_fat_pct=25)
        m_o = macros_for(1800, 80, lean, GoalArchetype.FAT_LOSS, Sex.MALE,
                         Somatotype.MESOMORPH, DietaryPreference.OMNIVORE,
                         body_fat_pct=25)
        self.assertGreater(m_v.protein_g, m_o.protein_g)

    def test_vegan_bulk_unknown_bf_higher(self):
        """Bulking with unknown BF%: vegan 2.2 vs omni 1.6 g/kg."""
        m_v = macros_for(2500, 70, None, GoalArchetype.MUSCLE_GAIN, Sex.MALE,
                         Somatotype.MESOMORPH, DietaryPreference.VEGAN,
                         body_fat_pct=None)
        m_o = macros_for(2500, 70, None, GoalArchetype.MUSCLE_GAIN, Sex.MALE,
                         Somatotype.MESOMORPH, DietaryPreference.OMNIVORE,
                         body_fat_pct=None)
        self.assertGreater(m_v.protein_g, m_o.protein_g)


class TestReferenceGuideAdditions(unittest.TestCase):
    def test_mifflin_default_energy(self):
        ee = energy_expenditure(80, 180, 30, Sex.MALE,
                                ActivityLevel.SEDENTARY,
                                GoalArchetype.GENERAL_HEALTH,
                                ExperienceLevel.INTERMEDIATE)
        self.assertEqual(ee.bmr, round(bmr_mifflin(80, 180, 30, Sex.MALE), 1))
        self.assertEqual(ee.activity_multiplier, 1.25)

    def test_male_calorie_floor(self):
        target, bd = calorie_target(1000, GoalArchetype.FAT_LOSS, 80,
                                    ExperienceLevel.INTERMEDIATE, sex=Sex.MALE)
        self.assertEqual(target, 1500)
        self.assertIn("warning", bd)

    def test_alpert_safeguard(self):
        target, bd = calorie_target(2500, GoalArchetype.FAT_LOSS, 70,
                                    ExperienceLevel.INTERMEDIATE, sex=Sex.MALE,
                                    body_fat_pct=8)
        self.assertIn("alpert_max_daily_deficit", bd)
        self.assertLessEqual(bd["daily_deficit"], bd["alpert_max_daily_deficit"])
        self.assertGreater(target, 1800)

    def test_anthropometric_indices(self):
        idx = anthropometric_indices(180, 80, Sex.MALE, waist_cm=85, hip_cm=100)
        self.assertEqual(idx.waist_to_height_category, "healthy")
        self.assertEqual(idx.waist_to_hip_category, "healthy")
        self.assertIsNotNone(idx.absi)

    def test_macro_adjustment_preserves_protein(self):
        m = macros_for(2200, 80, 64, GoalArchetype.FAT_LOSS, Sex.MALE,
                       Somatotype.MESOMORPH, DietaryPreference.OMNIVORE,
                       body_fat_pct=20)
        adj = adjust_macros_for_calorie_change(m, -200)
        self.assertEqual(adj.protein_g, m.protein_g)
        self.assertLess(adj.carbs_g, m.carbs_g)

    def test_adaptive_tdee(self):
        logs = [DailyLog(day=i+1, calories=2200, weight_kg=80 - i*0.03) for i in range(28)]
        est = adaptive_tdee(logs, formula_tdee=2500)
        self.assertIn(est.confidence, {"medium", "low"})
        self.assertIsNotNone(est.observed_tdee)
        self.assertGreater(est.adaptive_tdee, 2200)

    def test_reverse_diet(self):
        proto = reverse_diet_protocol(1800, 2400, 80, approach="moderate")
        self.assertEqual(proto.weekly_increase_kcal, 100)
        self.assertEqual(proto.duration_weeks, 6)
        self.assertEqual(proto.steps[-1].calories, 2400)


class TestEndToEnd(unittest.TestCase):
    def test_full_recommendation(self):
        from fitness_engine import (
            ClientProfile, Recommender, SessionLength, TrainingEnvironment,
        )
        p = ClientProfile(
            age=30, sex=Sex.MALE, height_cm=178, weight_kg=82, body_fat_pct=18,
            activity=ActivityLevel.MOSTLY_SEDENTARY,
            experience=ExperienceLevel.INTERMEDIATE,
            dietary_preference=DietaryPreference.OMNIVORE,
            environment=TrainingEnvironment.GYM_FULL,
            days_per_week=4, session_length=SessionLength.STANDARD_60,
            primary_goal=GoalArchetype.FAT_LOSS, timeline_weeks=12,
            meals_per_day=4,
        )
        rec = Recommender(p).recommend()
        self.assertTrue(rec.archetype_signature.startswith("FAT"))
        self.assertGreater(rec.nutrition.macros.protein_g, 50)
        self.assertGreaterEqual(len(rec.training.weekly_schedule), 2)
        self.assertGreater(len(rec.nutrition.meal_plan.meals), 0)
        self.assertIsNotNone(rec.trainee_category)


if __name__ == "__main__":
    unittest.main(verbosity=2)
