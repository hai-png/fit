"""
test_integration.py
===================

End-to-end integration tests. Run every curated archetype through the
recommender and verify sensible invariants.
"""
import unittest

from fitness_engine import (
    ActivityLevel, ClientProfile, DietaryPreference, ExperienceLevel,
    GoalArchetype, Recommender, SessionLength, Sex, TrainingEnvironment,
    all_curated, total_combinations, iter_signatures,
    build_complete_profile_protocol, macros_for, Somatotype,
    assemble_7_day_meal_plan, audit_7_day_meal_plan,
)


# Per-archetype sensible defaults
DEFAULTS = {
    "The Classic Hard Gainer": dict(age=22, sex=Sex.MALE, height_cm=180,
                                     weight_kg=64, body_fat_pct=11),
    "The Muscled Cutter":      dict(age=35, sex=Sex.MALE, height_cm=178,
                                     weight_kg=92, body_fat_pct=25),
    "The Skinny-Fat Recomper": dict(age=30, sex=Sex.MALE, height_cm=175,
                                     weight_kg=78, body_fat_pct=22),
    "The Home-Gym Beginner":   dict(age=45, sex=Sex.FEMALE, height_cm=165,
                                     weight_kg=68, body_fat_pct=28),
    "The Plant-Powered Builder": dict(age=27, sex=Sex.MALE, height_cm=178,
                                       weight_kg=74, body_fat_pct=12),
}


def _build_for_archetype(ap) -> ClientProfile:
    sig = ap.signature
    d = DEFAULTS[ap.nickname]
    return ClientProfile(
        age=d["age"], sex=d["sex"], height_cm=d["height_cm"],
        weight_kg=d["weight_kg"], body_fat_pct=d.get("body_fat_pct"),
        activity=sig.activity,
        dietary_preference=sig.diet,
        meals_per_day=4,
        experience=sig.experience,
        environment=sig.environment,
        days_per_week=4, session_length=sig.session,
        primary_goal=sig.goal, timeline_weeks=12,
    )


class ArchetypeInvariants(unittest.TestCase):
    """Every archetype must produce a sensible, consistent plan."""

    def test_all_archetypes_run(self):
        for ap in all_curated():
            with self.subTest(archetype=ap.nickname):
                p = _build_for_archetype(ap)
                rec = Recommender(p).recommend()
                self.assertTrue(rec.archetype_signature)
                self.assertGreater(rec.energy.calorie_target, 800)
                self.assertLess(rec.energy.calorie_target, 5000)
                m = rec.nutrition.macros
                self.assertGreater(m.protein_g, 30)
                self.assertGreater(m.carbs_g, 0)
                self.assertGreater(m.fat_g, 15)
                self.assertGreaterEqual(len(rec.training.weekly_schedule), 1)
                self.assertGreaterEqual(
                    len(rec.nutrition.meal_plan.meals), 1)

    def test_all_meal_plans_within_5pct(self):
        """Every plan's meal total must be within 5% of the target."""
        for ap in all_curated():
            with self.subTest(archetype=ap.nickname):
                rec = Recommender(_build_for_archetype(ap)).recommend()
                tgt = rec.energy.calorie_target
                actual = sum(m.calories for m in rec.nutrition.meal_plan.meals)
                err = abs(actual - tgt) / tgt
                self.assertLess(err, 0.05)


class PlanSanity(unittest.TestCase):

    def _profile(self, **kw):
        defaults = dict(
            age=30, sex=Sex.MALE, height_cm=178, weight_kg=82,
            body_fat_pct=18, activity=ActivityLevel.MOSTLY_SEDENTARY,
            experience=ExperienceLevel.INTERMEDIATE,
            environment=TrainingEnvironment.GYM_FULL,
            days_per_week=3, session_length=SessionLength.STANDARD_60,
            dietary_preference=DietaryPreference.OMNIVORE, meals_per_day=4,
        )
        defaults.update(kw)
        return ClientProfile(**defaults)

    def test_fat_loss_is_deficit(self):
        rec = Recommender(self._profile(primary_goal=GoalArchetype.FAT_LOSS)).recommend()
        self.assertLess(rec.energy.calorie_target, rec.energy.tdee)

    def test_muscle_gain_is_surplus(self):
        rec = Recommender(self._profile(primary_goal=GoalArchetype.MUSCLE_GAIN)).recommend()
        self.assertGreater(rec.energy.calorie_target, rec.energy.tdee)

    def test_recomp_is_maintenance(self):
        rec = Recommender(self._profile(primary_goal=GoalArchetype.RECOMPOSITION)).recommend()
        self.assertAlmostEqual(rec.energy.calorie_target, rec.energy.tdee, delta=1)

    def test_beginner_fewer_sets_than_advanced(self):
        beg = Recommender(self._profile(
            experience=ExperienceLevel.BEGINNER,
            primary_goal=GoalArchetype.MUSCLE_GAIN)).recommend()
        adv = Recommender(self._profile(
            experience=ExperienceLevel.ADVANCED,
            primary_goal=GoalArchetype.MUSCLE_GAIN)).recommend()
        self.assertLessEqual(beg.training.weekly_volume.total_sets,
                             adv.training.weekly_volume.total_sets)

    def test_home_bodyweight_all_bodyweight(self):
        """A no-equipment plan must only prescribe bodyweight exercises."""
        p = self._profile(environment=TrainingEnvironment.HOME_BODYWEIGHT)
        rec = Recommender(p).recommend()
        for day, exs in rec.training.weekly_schedule.items():
            for ex in exs:
                for eq in ex["equipment"]:
                    self.assertEqual(eq, "bodyweight",
                        msg=f"{day}: {ex['name']} requires '{eq}'")

    def test_day_variation(self):
        """Consecutive full-body days must differ."""
        p = self._profile(days_per_week=3)
        rec = Recommender(p).recommend()
        days = list(rec.training.weekly_schedule.values())
        if len(days) >= 2:
            d1 = [e["name"] for e in days[0]]
            d2 = [e["name"] for e in days[1]]
            self.assertNotEqual(d1, d2)

    def test_vegan_supplements_include_b12(self):
        p = self._profile(dietary_preference=DietaryPreference.VEGAN)
        rec = Recommender(p).recommend()
        names = [s[0] for s in rec.nutrition.supplements["foundational"]]
        self.assertIn("Vitamin B12", names)

    def test_trainee_category_assigned(self):
        rec = Recommender(self._profile()).recommend()
        self.assertIsNotNone(rec.trainee_category)
        self.assertTrue(rec.trainee_category.recommendations)


class ProfileRoundTrip(unittest.TestCase):

    def test_to_from_dict(self):
        p = ClientProfile(
            age=30, sex=Sex.MALE, height_cm=178, weight_kg=82,
            body_fat_pct=18, activity=ActivityLevel.MOSTLY_SEDENTARY,
            experience=ExperienceLevel.INTERMEDIATE,
            dietary_preference=DietaryPreference.OMNIVORE,
            environment=TrainingEnvironment.GYM_FULL,
            days_per_week=4, session_length=SessionLength.STANDARD_60,
            primary_goal=GoalArchetype.FAT_LOSS, timeline_weeks=12,
            visual_bf_label=None, meals_per_day=4,
        )
        d = p.to_dict()
        p2 = ClientProfile.from_dict(d)
        rec1 = Recommender(p).recommend()
        rec2 = Recommender(p2).recommend()
        self.assertEqual(rec1.archetype_signature, rec2.archetype_signature)
        self.assertEqual(rec1.energy.calorie_target, rec2.energy.calorie_target)


class ProtocolCoverage(unittest.TestCase):
    def test_protocol_builder_covers_every_signature(self):
        from fitness_engine import DietaryPreference
        dummy_macros = macros_for(2400, 80, 64, GoalArchetype.RECOMPOSITION,
                                  Sex.MALE, Somatotype.MESOMORPH,
                                  DietaryPreference.OMNIVORE, body_fat_pct=20)
        count = 0
        for sig in iter_signatures():
            proto = build_complete_profile_protocol(
                sig.goal, sig.experience, 4, sig.session, sig.environment,
                sig.diet, 2400, dummy_macros, 4, sig.activity,
                age=35, sex=sig.sex,
            )
            self.assertTrue(proto.exercise.days)
            self.assertTrue(proto.exercise.movement_pattern_priority)
            self.assertTrue(proto.meal.macro_protocol)
            self.assertTrue(proto.conflict_resolution)
            count += 1
        self.assertEqual(count, total_combinations())

    def test_all_diet_modes_can_assemble_day(self):
        from fitness_engine.meal_plans import assemble_day
        for diet in DietaryPreference:
            with self.subTest(diet=diet.value):
                plan = assemble_day("american", diet, 2200, meals_per_day=4)
                self.assertGreater(len(plan.meals), 0)
                actual = sum(m.calories for m in plan.meals)
                self.assertLess(abs(actual - 2200) / 2200, 0.05)

    def test_7_day_protocol_meal_plan(self):
        target = macros_for(2200, 80, 64, GoalArchetype.RECOMPOSITION,
                            Sex.MALE, Somatotype.MESOMORPH,
                            DietaryPreference.OMNIVORE, body_fat_pct=20)
        week = assemble_7_day_meal_plan(DietaryPreference.OMNIVORE, 2200, target,
                                        meals_per_day=4, include_external=True)
        self.assertEqual(len(week.days), 7)
        self.assertGreater(len(week.shopping_list), 0)
        for day in week.days:
            actual = sum(m.calories for m in day.meals)
            self.assertLess(abs(actual - 2200) / 2200, 0.05)
        self.assertTrue(any(k in week.source_summary for k in ("muscleandstrength", "trifecta")))
        audit = audit_7_day_meal_plan(week)
        self.assertGreaterEqual(audit.score, 80)


class ArchetypeCardinality(unittest.TestCase):

    def test_total_combinations_positive(self):
        self.assertGreater(total_combinations(), 1000)

    def test_iter_count_matches(self):
        count = sum(1 for _ in iter_signatures())
        self.assertEqual(count, total_combinations())

    def test_sample_uniqueness(self):
        seen = set()
        for i, s in enumerate(iter_signatures()):
            if i >= 5000:
                break
            self.assertNotIn(s, seen)
            seen.add(s)


if __name__ == "__main__":
    unittest.main(verbosity=2)
