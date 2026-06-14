"""
test_calculators.py
===================

Unit tests for the numerical calculators. Run with:
    python3 -m unittest tests.test_calculators
"""
import unittest

from fitness_engine import (
    ActivityLevel, GoalArchetype, Sex,
    bmi, bmi_category, bmr_mifflin, bmr_harris, bmr_katch,
    body_fat_navy, body_fat_bmi_method, body_composition,
    tdee, calorie_target, energy_expenditure,
    one_rep_max, cardio_zones, hydration, macros_for,
    infer_age_group, infer_somatotype,
)
from fitness_engine.archetypes import DietaryPreference, Somatotype


class TestBMI(unittest.TestCase):
    def test_normal(self):
        self.assertAlmostEqual(bmi(70, 175), 22.86, places=1)

    def test_underweight(self):
        self.assertEqual(bmi_category(17), "underweight")

    def test_normal2(self):
        self.assertEqual(bmi_category(22), "normal")

    def test_overweight(self):
        self.assertEqual(bmi_category(27), "overweight")

    def test_obese_i(self):
        self.assertEqual(bmi_category(32), "obese_class_i")

    def test_obese_iii(self):
        self.assertEqual(bmi_category(42), "obese_class_iii")

    def test_invalid_height(self):
        with self.assertRaises(ValueError):
            bmi(70, 0)


class TestBMR(unittest.TestCase):
    def test_mifflin_male(self):
        # Reference: 30y male, 80kg, 180cm
        # 10*80 + 6.25*180 - 5*30 + 5 = 800 + 1125 - 150 + 5 = 1780
        self.assertEqual(bmr_mifflin(80, 180, 30, Sex.MALE), 1780.0)

    def test_mifflin_female(self):
        # 30y female, 60kg, 165cm
        # 10*60 + 6.25*165 - 5*30 - 161 = 600 + 1031.25 - 150 - 161 = 1320.25
        self.assertAlmostEqual(bmr_mifflin(60, 165, 30, Sex.FEMALE),
                               1320.25, places=2)

    def test_harris_male_close_to_mifflin(self):
        self.assertAlmostEqual(
            bmr_harris(80, 180, 30, Sex.MALE),
            bmr_mifflin(80, 180, 30, Sex.MALE),
            delta=100
        )

    def test_katch(self):
        # BMR = 370 + 21.6 * lean_kg
        self.assertEqual(bmr_katch(80, 60), 370 + 21.6 * 60)


class TestTDEE(unittest.TestCase):
    def test_sedentary(self):
        self.assertEqual(tdee(1500, ActivityLevel.SEDENTARY), 1800.0)
    def test_athlete(self):
        self.assertEqual(tdee(1500, ActivityLevel.ATHLETE), 2850.0)


class TestCalorieTarget(unittest.TestCase):
    def test_fat_loss(self):
        target, bd = calorie_target(2000, GoalArchetype.FAT_LOSS)
        self.assertEqual(target, 1600.0)
        self.assertEqual(bd["mode"], "fat_loss")

    def test_muscle_gain(self):
        target, bd = calorie_target(2000, GoalArchetype.MUSCLE_GAIN)
        self.assertEqual(target, 2240.0)

    def test_recomp(self):
        target, _ = calorie_target(2000, GoalArchetype.RECOMPOSITION)
        self.assertEqual(target, 2000.0)


class TestOneRepMax(unittest.TestCase):
    def test_epley(self):
        r = one_rep_max(100, 5)
        # Epley: 100 * (1 + 5/30) = 116.67
        self.assertAlmostEqual(r.epley_1rm, 116.7, places=1)

    def test_invalid_reps(self):
        with self.assertRaises(ValueError):
            one_rep_max(100, 0)

    def test_percentages(self):
        r = one_rep_max(100, 5)
        self.assertIn("80%", r.pct_of_1rm)


class TestCardioZones(unittest.TestCase):
    def test_zones_present(self):
        z = cardio_zones(30, 60)
        self.assertIn("Z2_aerobic_base", z.zones)
        # Z2 should be lower than Z4
        self.assertLess(z.zones["Z2_aerobic_base"][0],
                        z.zones["Z4_threshold"][0])


class TestHydration(unittest.TestCase):
    def test_base(self):
        h = hydration(80, 0)
        self.assertEqual(h.base_ml, 2800.0)

    def test_workout_bonus(self):
        h = hydration(80, 60)
        self.assertEqual(h.workout_bonus_ml, 700.0)


class TestMacros(unittest.TestCase):
    def test_protein_floor(self):
        m = macros_for(2000, 80, 60, GoalArchetype.MUSCLE_GAIN,
                       Sex.MALE, Somatotype.MESOMORPH,
                       DietaryPreference.OMNIVORE)
        self.assertGreaterEqual(m.protein_g, 150)  # 1.9 g/kg
        self.assertLessEqual(m.fat_pct, 45)

    def test_keto_low_carb(self):
        m = macros_for(2000, 80, 60, GoalArchetype.FAT_LOSS,
                       Sex.MALE, Somatotype.MESOMORPH,
                       DietaryPreference.KETO)
        self.assertLessEqual(m.carbs_g, 60)

    def test_sum_equals_calories(self):
        m = macros_for(2200, 70, 55, GoalArchetype.RECOMPOSITION,
                       Sex.FEMALE, Somatotype.ENDOMORPH,
                       DietaryPreference.MEDITERRANEAN)
        # Allow rounding within 50 kcal
        self.assertLess(abs(m.protein_g*4 + m.carbs_g*4 + m.fat_g*9
                            - m.calories), 50)


class TestInferFunctions(unittest.TestCase):
    def test_age_groups(self):
        self.assertEqual(infer_age_group(15).value, "youth")
        self.assertEqual(infer_age_group(25).value, "young_adult")
        self.assertEqual(infer_age_group(35).value, "adult")
        self.assertEqual(infer_age_group(50).value, "middle")
        self.assertEqual(infer_age_group(65).value, "senior")
        self.assertEqual(infer_age_group(80).value, "elder")

    def test_somatotype_male(self):
        self.assertEqual(
            infer_somatotype(70, 175, 30, Sex.MALE, body_fat_pct=10).value,
            "ectomorph",
        )
        self.assertEqual(
            infer_somatotype(95, 175, 30, Sex.MALE, body_fat_pct=28).value,
            "endomorph",
        )
        self.assertEqual(
            infer_somatotype(80, 175, 30, Sex.MALE, body_fat_pct=18).value,
            "mesomorph",
        )


class TestEndToEnd(unittest.TestCase):
    def test_full_recommendation(self):
        from fitness_engine import (
            ClientProfile, Recommender, SessionLength, TrainingEnvironment,
            ExperienceLevel,
        )
        p = ClientProfile(
            age=30, sex=Sex.FEMALE, height_cm=165, weight_kg=65,
            body_fat_pct=25, waist_cm=75, neck_cm=32,
            activity=ActivityLevel.MODERATE, sleep_hours=7.5, stress_level=4,
            health_conditions=[], dietary_preference=DietaryPreference.OMNIVORE,
            allergies=[], meals_per_day=3,
            experience=ExperienceLevel.INTERMEDIATE,
            environment=TrainingEnvironment.GYM_COMMERCIAL,
            equipment=["barbell","bench","dumbbells","machine","cardio_machine"],
            days_per_week=4, session_length=SessionLength.STANDARD_60,
            primary_goal=GoalArchetype.FAT_LOSS, timeline_weeks=12,
            parq_answers={f"parq_{i}":"no" for i in range(1, 8)},
        )
        rec = Recommender(p).recommend()
        self.assertTrue(rec.archetype_signature.startswith("FAT"))
        self.assertGreater(rec.nutrition.macros.protein_g, 100)
        self.assertEqual(len(rec.training.weekly_schedule), 4)
        self.assertGreater(len(rec.nutrition.meal_plan.meals), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
