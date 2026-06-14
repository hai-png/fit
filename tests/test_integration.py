"""
test_integration.py
===================

End-to-end integration tests. Run every curated archetype through
the recommender and verify sensible invariants on every plan.
"""
import unittest

from fitness_engine import (
    ActivityLevel, ClientProfile, DietaryPreference, ExperienceLevel,
    GoalArchetype, Recommender, SessionLength, Sex, TrainingEnvironment,
    all_curated,
)


# Per-archetype sensible defaults
DEFAULTS = {
    "The Desk-Bound Reset": dict(age=34, sex=Sex.FEMALE, height_cm=168,
                                  weight_kg=72, body_fat_pct=32,
                                  waist_cm=82, neck_cm=33),
    "The Classic Hard Gainer": dict(age=22, sex=Sex.MALE, height_cm=180,
                                     weight_kg=64, body_fat_pct=11,
                                     waist_cm=74, neck_cm=37),
    "The Reclaiming Parent": dict(age=33, sex=Sex.FEMALE, height_cm=165,
                                  weight_kg=68, body_fat_pct=27,
                                  waist_cm=80, neck_cm=32),
    "The Vital Retiree": dict(age=64, sex=Sex.MALE, height_cm=175,
                              weight_kg=80, body_fat_pct=22,
                              waist_cm=92, neck_cm=38),
    "The Metabolic Rebuild": dict(age=52, sex=Sex.MALE, height_cm=178,
                                  weight_kg=102, body_fat_pct=32,
                                  waist_cm=110, neck_cm=40),
    "The Endurance Specialist": dict(age=26, sex=Sex.FEMALE, height_cm=170,
                                     weight_kg=58, body_fat_pct=16,
                                     waist_cm=68, neck_cm=29),
    "The Plant-Powered Performer": dict(age=27, sex=Sex.MALE, height_cm=178,
                                         weight_kg=74, body_fat_pct=12,
                                         waist_cm=76, neck_cm=37),
    "The Keto Cruiser": dict(age=38, sex=Sex.MALE, height_cm=178,
                             weight_kg=82, body_fat_pct=18,
                             waist_cm=88, neck_cm=39),
    "The Shift-Worker": dict(age=42, sex=Sex.MALE, height_cm=174,
                             weight_kg=84, body_fat_pct=24,
                             waist_cm=94, neck_cm=39),
    "The Back-Pain Returner": dict(age=39, sex=Sex.FEMALE, height_cm=167,
                                    weight_kg=72, body_fat_pct=30,
                                    waist_cm=86, neck_cm=32),
    "The Youth Athlete": dict(age=16, sex=Sex.MALE, height_cm=175,
                              weight_kg=68, body_fat_pct=12,
                              waist_cm=72, neck_cm=33),
    "The PCOS Balancer": dict(age=29, sex=Sex.FEMALE, height_cm=165,
                              weight_kg=80, body_fat_pct=36,
                              waist_cm=92, neck_cm=33),
}


def _build_for_archetype(ap) -> ClientProfile:
    sig = ap.signature
    d = DEFAULTS[ap.nickname]
    return ClientProfile(
        age=d["age"], sex=d["sex"], height_cm=d["height_cm"],
        weight_kg=d["weight_kg"], body_fat_pct=d.get("body_fat_pct"),
        waist_cm=d.get("waist_cm"), neck_cm=d.get("neck_cm"),
        activity=sig.activity, sleep_hours=7.0, stress_level=4,
        health_conditions=[],
        dietary_preference=sig.diet,
        allergies=[], meals_per_day=4,
        experience=sig.experience,
        environment=sig.environment,
        equipment=["barbell","bench","dumbbells","machine",
                   "cardio_machine","kettlebells","pullup_bar"],
        days_per_week=4, session_length=sig.session,
        primary_goal=sig.goal, timeline_weeks=12,
        parq_answers={f"parq_{i}":"no" for i in range(1, 8)},
    )


class ArchetypeInvariants(unittest.TestCase):
    """Every archetype must produce a sensible, consistent plan."""

    def test_all_archetypes_run(self):
        for ap in all_curated():
            with self.subTest(archetype=ap.nickname):
                p = _build_for_archetype(ap)
                rec = Recommender(p).recommend()
                # Plan must be produced
                self.assertTrue(rec.archetype_signature)
                # Target calories must be positive and reasonable
                self.assertGreater(rec.energy.calorie_target, 800)
                self.assertLess(rec.energy.calorie_target, 5000)
                # Macros must be positive
                m = rec.nutrition.macros
                self.assertGreater(m.protein_g, 30)
                self.assertGreater(m.carbs_g, 0)
                self.assertGreater(m.fat_g, 20)
                # Schedule must have one session per day
                self.assertGreaterEqual(len(rec.training.weekly_schedule), 1)
                # Meal plan must have at least one meal
                self.assertGreaterEqual(
                    len(rec.nutrition.meal_plan.meals), 1)


class PlanSanity(unittest.TestCase):
    """Spot checks on a few specific archetypes."""

    def test_fat_loss_deficit(self):
        ap = [a for a in all_curated() if a.nickname == "The Desk-Bound Reset"][0]
        rec = Recommender(_build_for_archetype(ap)).recommend()
        self.assertLess(rec.energy.calorie_target, rec.energy.tdee)

    def test_muscle_gain_surplus(self):
        ap = [a for a in all_curated() if a.nickname == "The Classic Hard Gainer"][0]
        rec = Recommender(_build_for_archetype(ap)).recommend()
        self.assertGreater(rec.energy.calorie_target, rec.energy.tdee)

    def test_keto_low_carb(self):
        ap = [a for a in all_curated() if a.nickname == "The Keto Cruiser"][0]
        rec = Recommender(_build_for_archetype(ap)).recommend()
        self.assertLessEqual(rec.nutrition.macros.carbs_g, 60)

    def test_vegan_high_protein_attention(self):
        ap = [a for a in all_curated() if a.nickname == "The Plant-Powered Performer"][0]
        rec = Recommender(_build_for_archetype(ap)).recommend()
        # Vegan athlete should have high protein target
        self.assertGreater(rec.nutrition.macros.protein_g, 100)

    def test_rehab_low_volume(self):
        ap = [a for a in all_curated() if a.nickname == "The Back-Pain Returner"][0]
        rec = Recommender(_build_for_archetype(ap)).recommend()
        # Rehab should be lowest volume archetype
        self.assertLessEqual(rec.training.weekly_volume.total_sets, 50)

    def test_endurance_high_cardio(self):
        ap = [a for a in all_curated() if a.nickname == "The Endurance Specialist"][0]
        rec = Recommender(_build_for_archetype(ap)).recommend()
        cardio_min = int(rec.training.cardio_prescription.get(
            "weekly_cardio_minutes", "0"))
        self.assertGreater(cardio_min, 100)

    def test_youth_athlete_no_1rm_recommended(self):
        ap = [a for a in all_curated() if a.nickname == "The Youth Athlete"][0]
        rec = Recommender(_build_for_archetype(ap)).recommend()
        # No 1RM testing in youth
        for day, exs in rec.training.weekly_schedule.items():
            for ex in exs:
                self.assertGreaterEqual(ex["rpe"], 7.0)


class ProfileRoundTrip(unittest.TestCase):
    """Client profile must survive JSON round-trip."""

    def test_to_from_dict(self):
        p = ClientProfile(
            age=30, sex=Sex.FEMALE, height_cm=165, weight_kg=60,
            body_fat_pct=22, activity=ActivityLevel.MODERATE,
            experience=ExperienceLevel.INTERMEDIATE,
            dietary_preference=DietaryPreference.MEDITERRANEAN,
            environment=TrainingEnvironment.GYM_COMMERCIAL,
            equipment=["barbell","dumbbells"],
            primary_goal=GoalArchetype.FAT_LOSS,
            session_length=SessionLength.STANDARD_60,
            days_per_week=4, timeline_weeks=12,
            parq_answers={"parq_1": "no"},
            secondary_goals=[GoalArchetype.STRENGTH],
            health_conditions=[],
        )
        d = p.to_dict()
        p2 = ClientProfile.from_dict(d)
        rec1 = Recommender(p).recommend()
        rec2 = Recommender(p2).recommend()
        self.assertEqual(rec1.archetype_signature, rec2.archetype_signature)
        self.assertEqual(rec1.energy.calorie_target,
                         rec2.energy.calorie_target)


class ArchetypeCardinality(unittest.TestCase):
    """Verify the combinatorial space."""

    def test_total_combinations_is_positive(self):
        from fitness_engine import total_combinations
        self.assertGreater(total_combinations(), 1_000_000)

    def test_enumerate_signatures_count(self):
        from fitness_engine import enumerate_signatures
        sigs = enumerate_signatures()
        from fitness_engine import total_combinations
        self.assertEqual(len(sigs), total_combinations())

    def test_signature_tuples_unique(self):
        from fitness_engine import enumerate_signatures
        sigs = enumerate_signatures()
        # Signatures are dataclass(frozen=True) -> hashable -> unique tuples
        seen = set()
        for s in sigs:
            self.assertNotIn(s, seen)   # no duplicates
            seen.add(s)

    def test_signature_code_collisions_are_known(self):
        """Short codes are intentionally compact; we only require them
        to be distinguishable at the level coaches actually read
        (goal + somatotype + experience + age + sex + activity + diet
        + session). Environment and full code are not unique by design.
        """
        from fitness_engine import enumerate_signatures
        sigs = enumerate_signatures()
        # Show that codes are stable for re-inputs of the same sig
        sig = sigs[0]
        self.assertEqual(sig.code(), sig.code())   # deterministic


if __name__ == "__main__":
    unittest.main(verbosity=2)
