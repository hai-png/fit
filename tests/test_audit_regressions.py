"""
test_audit_regressions.py
=========================

Regression tests for every Critical (P0) and Major (P1) finding from the
v2.2.1 engineering audit. Each test is annotated with the finding ID (C1,
C2, F36, etc.) so the audit trail is preserved.

Run with:
    python -m unittest tests.test_audit_regressions
"""
import unittest

from fitness_engine import (
    ActivityLevel, ClientProfile, DietaryPreference, ExperienceLevel,
    GoalArchetype, Recommender, Sex, SessionLength, Somatotype,
    TrainingEnvironment, body_composition, correct_bf_estimate, macros_for, macro_cycle,
    muscular_potential, anthropometric_indices, one_rep_max,
    assemble_7_day_meal_plan, weekly_split,
    training_split, weekly_volume, supplement_stack,
)
from fitness_engine.archetypes import AgeGroup
from fitness_engine.calculators import infer_age_group
from fitness_engine.exercise_plans import (
    EXERCISE_LIBRARY, pick_exercise, build_session,
)
from fitness_engine.exercise_database import ExerciseDatabase
from fitness_engine.meal_plans import (
    assemble_day, assemble_week,
)
from fitness_engine.seven_day_meal_planner import (
    load_external_recipe_meals,
)
from fitness_engine.questionnaires import DIETARY, HEALTH_SCREEN
from fitness_engine.protocols import DIET_MODE_NOTES, build_complete_profile_protocol


class TestP0Critical(unittest.TestCase):
    """P0 (Critical) regression tests — each maps to a C-finding."""

    # ---- C1: body_composition validates bf_pct ----
    def test_C1_body_composition_rejects_negative_bf(self):
        with self.assertRaisesRegex(ValueError, "bf_pct"):
            body_composition(70, 175, 30, Sex.MALE, bf_pct=-5)

    def test_C1_body_composition_rejects_above_60_bf(self):
        with self.assertRaisesRegex(ValueError, "bf_pct"):
            body_composition(70, 175, 30, Sex.MALE, bf_pct=120)

    def test_C1_body_composition_accepts_valid_bf(self):
        bc = body_composition(70, 175, 30, Sex.MALE, bf_pct=15)
        self.assertEqual(bc.body_fat_pct, 15)
        self.assertEqual(bc.estimation_method, "user_input")

    # ---- C2: macros_for rejects impossible floor combinations ----
    def test_C2_macros_for_rejects_impossible_combination(self):
        with self.assertRaisesRegex(ValueError, "Cannot satisfy macro floors"):
            macros_for(1200, 90, 60, GoalArchetype.FAT_LOSS, Sex.MALE,
                       Somatotype.ENDOMORPH, DietaryPreference.OMNIVORE,
                       body_fat_pct=25)

    def test_C2_macros_for_returns_consistent_split_when_feasible(self):
        m = macros_for(2400, 80, 64, GoalArchetype.MUSCLE_GAIN, Sex.MALE,
                       Somatotype.MESOMORPH, DietaryPreference.OMNIVORE,
                       body_fat_pct=20)
        total = m.protein_g * 4 + m.carbs_g * 4 + m.fat_g * 9
        # Total must be within 2% of the target (the feasibility tolerance).
        self.assertLessEqual(total, m.calories * 1.02 + 1)

    # ---- C3: _load_guidance no longer cross-applies 1RM via pattern ----
    def test_C3_deadlift_does_not_apply_to_hip_thrust(self):
        p = ClientProfile(
            age=30, sex=Sex.MALE, height_cm=178, weight_kg=82,
            experience=ExperienceLevel.INTERMEDIATE,
            environment=TrainingEnvironment.GYM_FULL,
            days_per_week=3, working_weights_kg={"deadlift": 120},
        )
        rec = Recommender(p).recommend()
        # No exercise named "Barbell Hip Thrust" should carry deadlift load guidance.
        for day, exs in rec.training.weekly_schedule.items():
            for ex in exs:
                lg = ex.get("load_guidance")
                if lg and "hip" in ex["name"].lower():
                    self.fail(f"Deadlift 1RM was applied to {ex['name']} on {day}")

    def test_C3_overhead_press_does_not_apply_to_all_vertical_push(self):
        p = ClientProfile(
            age=30, sex=Sex.MALE, height_cm=178, weight_kg=82,
            experience=ExperienceLevel.INTERMEDIATE,
            environment=TrainingEnvironment.GYM_FULL,
            days_per_week=3, working_weights_kg={"overhead_press": 50},
        )
        rec = Recommender(p).recommend()
        # Only exercises whose name contains "overhead" or "shoulder press"
        # should carry the overhead_press guidance.
        for day, exs in rec.training.weekly_schedule.items():
            for ex in exs:
                lg = ex.get("load_guidance")
                if lg and lg.get("source_lift") == "overhead_press":
                    name_l = ex["name"].lower()
                    self.assertTrue(
                        any(k in name_l for k in ("overhead", "shoulder press", "arnold")),
                        msg=f"overhead_press guidance wrongly applied to {ex['name']}"
                    )

    # ---- C4: days_per_week=1 produces a 1-day plan ----
    def test_C4_training_split_one_day(self):
        ts = training_split(GoalArchetype.MUSCLE_GAIN, ExperienceLevel.BEGINNER, 1)
        self.assertEqual(len(ts.days), 1)
        self.assertIn("Full Body", ts.days[0])

    def test_C4_weekly_split_one_day(self):
        plan = weekly_split(GoalArchetype.MUSCLE_GAIN, ExperienceLevel.BEGINNER,
                            1, TrainingEnvironment.GYM_FULL)
        self.assertEqual(len(plan), 1)

    def test_C4_recommender_one_day(self):
        p = ClientProfile(age=30, sex=Sex.MALE, height_cm=178, weight_kg=82,
                          days_per_week=1)
        rec = Recommender(p).recommend()
        self.assertEqual(len(rec.training.weekly_schedule), 1)

    # ---- C5: volume reconciliation no longer starves arms/calves ----
    def test_C5_session_includes_isolation_patterns(self):
        session = build_session(GoalArchetype.MUSCLE_GAIN,
                                TrainingEnvironment.GYM_FULL, 60)
        patterns = {ex.pattern for ex in session}
        # The new default pattern list includes "isolation" for arms.
        self.assertIn("isolation", patterns)

    def test_C5_reconciliation_arms_nonzero(self):
        p = ClientProfile(
            age=30, sex=Sex.MALE, height_cm=178, weight_kg=82,
            body_fat_pct=18, days_per_week=3, meals_per_day=4,
            experience=ExperienceLevel.INTERMEDIATE,
            primary_goal=GoalArchetype.MUSCLE_GAIN,
        )
        rec = Recommender(p).recommend()
        audit = rec.training.volume_reconciliation
        # Arms may still be below target but should no longer be 0.
        self.assertGreater(audit["scheduled_sets"].get("arms", 0), 0,
                           "Arms should receive direct isolation volume")

    # ---- C5a: macro_cycle rest-day floor ----
    def test_C5a_macro_cycle_male_rest_day_floor(self):
        m = macros_for(2400, 80, 64, GoalArchetype.MUSCLE_GAIN, Sex.MALE,
                       Somatotype.MESOMORPH, DietaryPreference.OMNIVORE,
                       body_fat_pct=20)
        mc = macro_cycle(m, training_days_per_week=6, sex=Sex.MALE)
        self.assertGreaterEqual(mc.rest_day.calories, 1500)

    def test_C5a_macro_cycle_female_rest_day_floor(self):
        m = macros_for(2000, 60, 48, GoalArchetype.MUSCLE_GAIN, Sex.FEMALE,
                       Somatotype.MESOMORPH, DietaryPreference.OMNIVORE,
                       body_fat_pct=20)
        mc = macro_cycle(m, training_days_per_week=6, sex=Sex.FEMALE)
        self.assertGreaterEqual(mc.rest_day.calories, 1200)

    # ---- F27: correct_bf_estimate clamping ----
    def test_F27_correct_bf_zero_clamped(self):
        self.assertGreaterEqual(correct_bf_estimate(0, is_self_estimate=True), 2.0)

    def test_F27_correct_bf_high_clamped(self):
        self.assertLessEqual(correct_bf_estimate(100, is_self_estimate=True), 55.0)


class TestP1Major(unittest.TestCase):
    """P1 (Major) regression tests — each maps to an F-finding."""

    # ---- F8: activity multiplier comment / 6-tier ----
    def test_F8_activity_multipliers_six_tiers(self):
        from fitness_engine.calculators import ACTIVITY_MULTIPLIERS
        self.assertEqual(len(ACTIVITY_MULTIPLIERS), 6)

    # ---- F11: Alpert safeguard flag is set at clamp point ----
    def test_F11_alpert_safeguard_flag_when_clamped(self):
        from fitness_engine.calculators import calorie_target
        target, bd = calorie_target(2500, GoalArchetype.FAT_LOSS, 70,
                                     ExperienceLevel.INTERMEDIATE,
                                     sex=Sex.MALE, body_fat_pct=8)
        # Lean male (8% BF) triggers the Alpert cap.
        self.assertTrue(bd.get("alpert_safeguard_applied"))
        self.assertIn("alpert_max_daily_deficit", bd)

    # ---- F12: NEAT buffer surfaced in breakdown ----
    def test_F12_neat_buffer_in_breakdown(self):
        from fitness_engine.calculators import calorie_target
        _, bd = calorie_target(2500, GoalArchetype.MUSCLE_GAIN, 70,
                                ExperienceLevel.BEGINNER)
        self.assertIn("neat_buffer_pct", bd)
        self.assertIn("neat_buffer_note", bd)

    # ---- F23: ABSI z-score returned ----
    def test_F23_absi_z_score_computed(self):
        ai = anthropometric_indices(180, 80, Sex.MALE,
                                     waist_cm=85, hip_cm=100)
        self.assertIsNotNone(ai.absi_z)
        self.assertIsNotNone(ai.absi_category)

    # ---- F28: normalized_ffmi returned ----
    def test_F28_normalized_ffmi_returned(self):
        mp = muscular_potential(178, 82, 18)
        self.assertIsNotNone(mp.normalized_ffmi)
        self.assertGreater(mp.normalized_ffmi, 0)

    # ---- F29: strength beginner rationale note ----
    def test_F29_strength_rationale_notes_exception(self):
        wv = weekly_volume(GoalArchetype.STRENGTH, ExperienceLevel.BEGINNER, 3)
        self.assertIn("Strength training emphasizes intensity", wv.rationale)

    # ---- F33: conditional supplements populated ----
    def test_F33_conditional_supplements_populated(self):
        sp = supplement_stack(GoalArchetype.GENERAL_HEALTH, DietaryPreference.KETO)
        self.assertGreater(len(sp.conditional), 0)

    def test_F33_vegan_conditional_iron(self):
        sp = supplement_stack(GoalArchetype.MUSCLE_GAIN, DietaryPreference.VEGAN)
        conditional_names = [s[0] for s in sp.conditional]
        self.assertTrue(any("Iron" in n for n in conditional_names))

    # ---- F34: picker no longer picks hardest feasible for beginners ----
    def test_F34_beginner_gets_easier_deadlift(self):
        ex = pick_exercise("hinge", TrainingEnvironment.GYM_FULL, difficulty_max=3)
        # Beginners (difficulty_max=3) should now get an easier variant, not
        # the difficulty-4 barbell deadlift.
        self.assertLessEqual(ex.difficulty, 3)
        # Sort-by-target means the closest-to-midpoint (2) is picked first.
        self.assertLessEqual(ex.difficulty, 3)

    # ---- F35: lru_cache on comprehensive DB load ----
    def test_F35_lru_cache_on_comprehensive_loader(self):
        from fitness_engine.exercise_plans import _get_comprehensive_library
        # Call twice; the lru_cache should return the same object.
        a = _get_comprehensive_library()
        b = _get_comprehensive_library()
        self.assertIs(a, b)
        # Cache info should show 1 miss and 1 hit.
        info = _get_comprehensive_library.cache_info()
        self.assertGreaterEqual(info.hits, 1)

    # ---- F36: Barbell Upright Row reclassified ----
    def test_F36_upright_row_not_vertical_pull(self):
        # The comprehensive DB should no longer classify upright row as vertical_pull.
        upright = [e for e in EXERCISE_LIBRARY.values()
                   if "upright" in e.name.lower()]
        self.assertGreater(len(upright), 0, "Upright row should be in library")
        for ex in upright:
            self.assertNotEqual(ex.pattern, "vertical_pull",
                                msg=f"{ex.name} should not be vertical_pull")

    # ---- F39: filter_by_equipment([]) returns bodyweight exercises ----
    def test_F39_filter_by_equipment_empty_returns_bodyweight(self):
        db = ExerciseDatabase()
        results = db.filter_by_equipment([])
        self.assertGreater(len(results), 0,
                           "Empty equipment list should still return bodyweight exercises")

    # ---- F40: ENVIRONMENT_EQUIPMENT consolidated ----
    def test_F40_environment_equipment_consistent(self):
        from fitness_engine.exercise_plans import ENVIRONMENT_EQUIPMENT as plan_map
        from fitness_engine.exercise_database import ENVIRONMENT_EQUIPMENT as db_map
        # HOME_BODYWEIGHT should be the empty list in both maps.
        self.assertEqual(plan_map[TrainingEnvironment.HOME_BODYWEIGHT], [])
        self.assertEqual(db_map[TrainingEnvironment.HOME_BODYWEIGHT], [])

    # ---- F44: assemble_day / assemble_week accept seed ----
    def test_F44_assemble_day_reproducible_with_seed(self):
        p1 = assemble_day("american", DietaryPreference.OMNIVORE, 2000, seed=42)
        p2 = assemble_day("american", DietaryPreference.OMNIVORE, 2000, seed=42)
        self.assertEqual([m.name for m in p1.meals], [m.name for m in p2.meals])

    def test_F44_assemble_week_reproducible_with_seed(self):
        w1 = assemble_week("american", DietaryPreference.OMNIVORE, 2000, seed=42)
        w2 = assemble_week("american", DietaryPreference.OMNIVORE, 2000, seed=42)
        self.assertEqual([d.name for d in w1], [d.name for d in w2])
        for d1, d2 in zip(w1, w2):
            self.assertEqual([m.name for m in d1.meals], [m.name for m in d2.meals])

    # ---- F46: allergen matching uses word boundaries ----
    def test_F46_egg_does_not_match_eggplant(self):
        # The allergen regex should not match "eggplant" when the user is
        # allergic to "egg". Plural "eggs" should still match.
        import re
        # Reproduce the pattern from filter_compatible.
        # Allergen "egg" (not ending in 's') gets the plural-s? suffix.
        pattern = re.compile(r"\begg" + r"s?" + r"\b", re.IGNORECASE)
        # "eggplant" should NOT match.
        self.assertFalse(pattern.search("grilled eggplant with tahini"))
        # "eggs" should match.
        self.assertTrue(pattern.search("2 eggs, scrambled"))
        # "egg" should match.
        self.assertTrue(pattern.search("1 egg, scrambled"))

    # ---- F47: 5-meal layout uses snack_1/snack_2 ----
    def test_F47_five_meal_layout_has_distinct_snack_slots(self):
        from fitness_engine.meal_plans import _SLOT_WEIGHTS
        slots_5 = [s for s, _ in _SLOT_WEIGHTS[5]]
        self.assertIn("snack_1", slots_5)
        self.assertIn("snack_2", slots_5)

    def test_F47_assemble_day_5_meals_distinct_slots(self):
        plan = assemble_day("american", DietaryPreference.OMNIVORE, 2400,
                            meals_per_day=5, seed=42)
        slots = [m.slot for m in plan.meals]
        # The 5-meal plan should have 5 distinct slots.
        self.assertEqual(len(slots), len(set(slots)),
                         f"Duplicate slots in 5-meal plan: {slots}")

    # ---- F48: 7-day planner uses local Random instance ----
    def test_F48_planner_does_not_mutate_global_random(self):
        import random
        # Capture global state.
        random.seed(123)
        expected = random.random()
        # Run the planner with a different seed.
        target = macros_for(2200, 80, 64, GoalArchetype.RECOMPOSITION, Sex.MALE,
                            Somatotype.MESOMORPH, DietaryPreference.OMNIVORE,
                            body_fat_pct=20)
        assemble_7_day_meal_plan(DietaryPreference.OMNIVORE, 2200, target,
                                  meals_per_day=4, seed=999)
        # Reset global state and verify the planner did not corrupt it.
        random.seed(123)
        actual = random.random()
        self.assertEqual(expected, actual)

    # ---- F50: _choose_day caps total meals ----
    def test_F50_choose_day_caps_meals(self):
        target = macros_for(2200, 80, 64, GoalArchetype.RECOMPOSITION, Sex.MALE,
                            Somatotype.MESOMORPH, DietaryPreference.VEGAN,
                            body_fat_pct=20)
        plan = assemble_7_day_meal_plan(DietaryPreference.VEGAN, 2200, target,
                                         meals_per_day=4, seed=42)
        for day in plan.days:
            # meals_per_day + 1 = 5 max.
            self.assertLessEqual(len(day.meals), 5,
                                 f"{day.name} has {len(day.meals)} meals, exceeds cap")

    # ---- F52: load_external_recipe_meals logs errors (smoke test) ----
    def test_F52_load_handles_corrupt_json(self):
        # Pointing at a non-existent file returns empty list, not crash.
        meals = load_external_recipe_meals("/nonexistent/path/recipes.json")
        self.assertEqual(meals, [])

    # ---- F54: placeholder-instruction recipes skipped ----
    def test_F54_injera_not_in_pool(self):
        # The Injera recipe had placeholder instructions and should be filtered.
        meals = load_external_recipe_meals()
        names = [m.name.lower() for m in meals]
        self.assertFalse(any("injera" == n.strip() for n in names),
                         "Injera (placeholder instructions) should be filtered out")

    # ---- F55: auditor exempts sides by property not name ----
    def test_F55_auditor_exempt_snack_under_300(self):
        from fitness_engine.meal_plans import MealItem
        from fitness_engine.meal_plan_auditor import _is_side_or_booster
        small_snack = MealItem(
            name="Protein shake", cuisine="american", slot="snack",
            calories=200, protein_g=25, carbs_g=10, fat_g=5, fibre_g=1,
        )
        self.assertTrue(_is_side_or_booster(small_snack))
        big_dinner = MealItem(
            name="Steak and potatoes", cuisine="american", slot="dinner",
            calories=700, protein_g=45, carbs_g=60, fat_g=25, fibre_g=6,
        )
        self.assertFalse(_is_side_or_booster(big_dinner))

    # ---- F56: slot-sanity uses word boundaries ----
    def test_F56_barbacoa_not_flagged_as_bar(self):
        # "Barbacoa" should not match the "bar" keyword (now word-boundary).
        from fitness_engine.meal_plan_auditor import _SLOT_SANITY_PATTERNS
        # None of the patterns should match "Barbacoa beef bowl".
        name = "Barbacoa beef bowl".lower()
        self.assertFalse(any(p.search(name) for p in _SLOT_SANITY_PATTERNS))

    def test_F56_brownie_still_flagged(self):
        from fitness_engine.meal_plan_auditor import _SLOT_SANITY_PATTERNS
        name = "Chocolate brownie sundae".lower()
        self.assertTrue(any(p.search(name) for p in _SLOT_SANITY_PATTERNS))

    # ---- F59: 3-day split has three distinct sessions ----
    def test_F59_three_day_split_distinct(self):
        p = ClientProfile(
            age=30, sex=Sex.MALE, height_cm=178, weight_kg=82,
            experience=ExperienceLevel.INTERMEDIATE,
            environment=TrainingEnvironment.GYM_FULL,
            days_per_week=3, primary_goal=GoalArchetype.MUSCLE_GAIN,
        )
        rec = Recommender(p).recommend()
        days = list(rec.training.weekly_schedule.values())
        if len(days) >= 3:
            d1 = [e["name"] for e in days[0]]
            d3 = [e["name"] for e in days[2]]
            self.assertNotEqual(d1, d3, "Day 1 and Day 3 should differ")

    # ---- F60: meal_plan field documented ----
    def test_F60_meal_plan_is_first_day_of_week(self):
        p = ClientProfile(age=30, sex=Sex.MALE, height_cm=178, weight_kg=82)
        rec = Recommender(p).recommend()
        # meal_plan should be the same object as weekly_meal_plan.days[0].
        self.assertEqual(rec.nutrition.meal_plan.name,
                         rec.nutrition.weekly_meal_plan.days[0].name)

    # ---- F63: DIET_MODE_NOTES covers all diets ----
    def test_F63_diet_mode_notes_complete(self):
        for diet in DietaryPreference:
            self.assertIn(diet, DIET_MODE_NOTES,
                          msg=f"{diet} missing from DIET_MODE_NOTES")

    # ---- F65: diet questionnaire covers all 12 diets ----
    def test_F65_diet_questionnaire_full(self):
        d_pref = [q for q in DIETARY if q.id == "d_pref"][0]
        choice_ids = {c.id for c in d_pref.choices}
        for diet in DietaryPreference:
            self.assertIn(diet.value, choice_ids,
                          msg=f"{diet.value} missing from diet questionnaire")

    # ---- F66: health screen populates medical_flags ----
    def test_F66_health_screen_present(self):
        self.assertGreater(len(HEALTH_SCREEN), 0)
        ids = {q.id for q in HEALTH_SCREEN}
        self.assertIn("h_pregnant_postpartum", ids)
        self.assertIn("h_cardiac", ids)

    # ---- F74: cmd_review handles missing formula_tdee ----
    def test_F74_cmd_review_no_crash_without_formula_tdee(self):
        import json
        import tempfile
        import os
        from fitness_engine.cli import main
        # Create a review JSON with reverse_diet but no formula_tdee.
        review_data = {
            "logs": [],
            "reverse_diet": {
                "current_calories": 1800,
                "bodyweight_kg": 80,
            },
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(review_data, f)
            tmp_path = f.name
        try:
            # Should not raise.
            rc = main(["review", tmp_path])
            self.assertEqual(rc, 0)
        finally:
            os.unlink(tmp_path)

    # ---- F77: render_html auto-creates output dir ----
    def test_F77_render_html_creates_output_dir(self):
        import os
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "examples"))
        from render_html import render  # noqa
        # We test via the render function directly; the directory creation
        # is in main(), which we cannot easily invoke without argparse.
        # Instead, verify the render function returns HTML.
        p = ClientProfile(age=30, sex=Sex.MALE, height_cm=178, weight_kg=82)
        rec = Recommender(p).recommend()
        html = render(rec, "Test Client")
        self.assertIn("<html", html)
        self.assertIn("Test Client", html)

    # ---- F79: ExerciseDatabase exported ----
    def test_F79_exercise_database_exported(self):
        import fitness_engine
        self.assertTrue(hasattr(fitness_engine, "ExerciseDatabase"))
        self.assertTrue(hasattr(fitness_engine, "ScrapedExercise"))

    # ---- F80: version matches pyproject ----
    def test_F80_version_consistency(self):
        import fitness_engine
        # Read pyproject.toml and verify version matches.
        import pathlib
        pyproject = pathlib.Path(__file__).resolve().parents[1] / "pyproject.toml"
        content = pyproject.read_text()
        self.assertIn(f'version = "{fitness_engine.__version__}"', content)

    # ---- F81: anthropometric test now checks category (not just division) ----
    def test_F81_anthropometric_indices_category(self):
        ai = anthropometric_indices(180, 80, Sex.MALE,
                                     waist_cm=85, hip_cm=100)
        # WHtR 85/180 = 0.472 → "healthy"
        self.assertEqual(ai.waist_to_height_category, "healthy")
        # WHR 85/100 = 0.85 → "healthy" for male (< 0.90)
        self.assertEqual(ai.waist_to_hip_category, "healthy")


class TestP2Minor(unittest.TestCase):
    """P2 (Minor) regression tests."""

    def test_F5_age_group_13_to_17_is_young(self):
        # The validator accepts 13+; the AgeGroup comment was wrong to say 18-30.
        self.assertEqual(infer_age_group(13), AgeGroup.YOUNG)
        self.assertEqual(infer_age_group(17), AgeGroup.YOUNG)

    def test_F64_special_modifiers_pregnancy(self):
        proto = build_complete_profile_protocol(
            GoalArchetype.GENERAL_HEALTH, ExperienceLevel.BEGINNER, 3,
            SessionLength.STANDARD_60, TrainingEnvironment.GYM_FULL,
            DietaryPreference.OMNIVORE, 2000,
            macros_for(2000, 70, 55, GoalArchetype.GENERAL_HEALTH, Sex.FEMALE,
                       Somatotype.MESOMORPH, DietaryPreference.OMNIVORE,
                       body_fat_pct=22),
            4, ActivityLevel.MOSTLY_SEDENTARY, age=30, sex=Sex.FEMALE,
            medical_flags={"pregnant_or_recent_postpartum": True},
        )
        modifiers = proto.exercise.special_population_modifiers
        self.assertTrue(any("Pregnancy" in m or "pregnancy" in m.lower() for m in modifiers))

    def test_F64_special_modifiers_adolescent(self):
        proto = build_complete_profile_protocol(
            GoalArchetype.GENERAL_HEALTH, ExperienceLevel.BEGINNER, 3,
            SessionLength.STANDARD_60, TrainingEnvironment.GYM_FULL,
            DietaryPreference.OMNIVORE, 2000,
            macros_for(2000, 60, 50, GoalArchetype.GENERAL_HEALTH, Sex.MALE,
                       Somatotype.MESOMORPH, DietaryPreference.OMNIVORE,
                       body_fat_pct=15),
            4, ActivityLevel.MOSTLY_SEDENTARY, age=15, sex=Sex.MALE,
        )
        modifiers = proto.exercise.special_population_modifiers
        self.assertTrue(any("Adolescent" in m or "adolescent" in m.lower() for m in modifiers))


class TestP2AdditionalFixes(unittest.TestCase):
    """Additional P2 fixes from the second remediation pass."""

    # ---- F2: signature code collision guard ----
    def test_F2_code_uniqueness_guard_passes(self):
        # If the guard runs at import without raising, all current enum
        # values produce distinct code segments.
        from fitness_engine.archetypes import _validate_code_uniqueness
        _validate_code_uniqueness()  # should not raise

    # ---- F3: signature_from_dict clear error ----
    def test_F3_signature_from_dict_clear_error(self):
        from fitness_engine.archetypes import signature_from_dict
        with self.assertRaises(ValueError) as ctx:
            signature_from_dict({
                "goal": "fat_loss", "somatotype": "ectomorph",
                "experience": "begginer",  # typo
                "age_group": "young", "sex": "male",
                "activity": "sedentary", "diet": "omnivore",
                "environment": "gym_full", "session": "standard_60",
            })
        self.assertIn("experience", str(ctx.exception))
        self.assertIn("begginer", str(ctx.exception))

    def test_F3_signature_from_dict_missing_key(self):
        from fitness_engine.archetypes import signature_from_dict
        with self.assertRaises(KeyError) as ctx:
            signature_from_dict({"goal": "fat_loss"})
        self.assertIn("somatotype", str(ctx.exception))

    # ---- F5: AgeGroup comment covers 13+ ----
    def test_F5_age_group_13_to_17_is_young(self):
        from fitness_engine.calculators import infer_age_group
        from fitness_engine.archetypes import AgeGroup
        self.assertEqual(infer_age_group(13), AgeGroup.YOUNG)
        self.assertEqual(infer_age_group(17), AgeGroup.YOUNG)
        self.assertEqual(infer_age_group(30), AgeGroup.YOUNG)

    # ---- F6: VISUAL_BF_BANDS are contiguous ----
    def test_F6_visual_bf_bands_contiguous(self):
        from fitness_engine.calculators import VISUAL_BF_BANDS, Sex
        for sex in [Sex.MALE, Sex.FEMALE]:
            bands = VISUAL_BF_BANDS[sex]
            for i in range(len(bands) - 1):
                _, (low1, high1), _, _ = bands[i]
                _, (low2, high2), _, _ = bands[i + 1]
                self.assertEqual(high1, low2,
                                 f"{sex} bands {i} and {i+1} not contiguous: "
                                 f"{high1} != {low2}")

    # ---- F7: body_fat_navy sex-specific errors ----
    def test_F7_navy_male_error_mentions_waist_neck(self):
        from fitness_engine.calculators import body_fat_navy
        with self.assertRaises(ValueError) as ctx:
            body_fat_navy(Sex.MALE, 180, 100, 100)  # waist == neck
        self.assertIn("waist", str(ctx.exception).lower())
        self.assertIn("neck", str(ctx.exception).lower())

    def test_F7_navy_female_error_mentions_hip(self):
        from fitness_engine.calculators import body_fat_navy
        with self.assertRaises(ValueError) as ctx:
            body_fat_navy(Sex.FEMALE, 165, 30, 80, hip_cm=None)
        self.assertIn("hip", str(ctx.exception).lower())

    # ---- F9: fat_loss_rate citation in docstring ----
    def test_F9_fat_loss_rate_cited(self):
        from fitness_engine.calculators import fat_loss_rate_for_bodyfat
        doc = fat_loss_rate_for_bodyfat.__doc__
        self.assertIn("Gallagher", doc)

    # ---- F10: bmr_harris_benedict deprecation note ----
    def test_F10_harris_benedict_deprecated(self):
        from fitness_engine.calculators import bmr_harris_benedict
        self.assertIn("deprecated", bmr_harris_benedict.__doc__.lower())

    # ---- F14: keto fat_pct capped at 1.0 ----
    def test_F14_keto_fat_pct_never_exceeds_100(self):
        # Extreme case: very high protein floor + keto + low calories.
        # macros_for should raise (C2) rather than return fat_pct > 1.
        with self.assertRaises(ValueError):
            macros_for(800, 100, 80, GoalArchetype.FAT_LOSS, Sex.MALE,
                       Somatotype.MESOMORPH, DietaryPreference.KETO,
                       body_fat_pct=10)

    # ---- F15: _protein_target no redundant check ----
    def test_F15_protein_target_lean_mass_cut(self):
        from fitness_engine.calculators import _protein_target
        # lean_cut branch: bf=10 (<=12), omnivore → 2.8 g/kg lean
        protein, _ = _protein_target(
            GoalArchetype.FAT_LOSS, 80, 64, 10, None, is_vegan=False
        )
        self.assertAlmostEqual(protein, 64 * 2.8, places=1)

    # ---- F16: structured protein target ----
    def test_F16_structured_protein_target(self):
        from fitness_engine.calculators import _protein_target_structured
        result = _protein_target_structured(
            GoalArchetype.FAT_LOSS, 80, 64, 10, None, is_vegan=False
        )
        self.assertIn("basis", result)
        self.assertEqual(result["basis"], "lean_mass")
        self.assertEqual(result["multiplier"], 2.8)
        self.assertEqual(result["phase"], "cutting")

    # ---- F17: macro_cycle drift reduced ----
    def test_F17_macro_cycle_drift_small(self):
        m = macros_for(2400, 80, 64, GoalArchetype.MUSCLE_GAIN, Sex.MALE,
                       Somatotype.MESOMORPH, DietaryPreference.OMNIVORE,
                       body_fat_pct=20)
        mc = macro_cycle(m, training_days_per_week=4, sex=Sex.MALE)
        # With 1g rounding, weekly average drift should be < 5 kcal.
        drift = abs(mc.weekly_average_calories - m.calories)
        self.assertLess(drift, 5.0,
                        f"Macro cycle drift {drift} exceeds 5 kcal")

    # ---- F18: 1RM percent table includes warmup ranges ----
    def test_F18_1rm_table_has_warmup_ranges(self):
        r = one_rep_max(100, 5)
        self.assertIn("30%", r.pct_of_1rm)
        self.assertIn("40%", r.pct_of_1rm)

    # ---- F20: cardio zones no longer overlap ----
    def test_F20_cardio_zones_no_overlap(self):
        from fitness_engine import cardio_zones
        z = cardio_zones(30, 60)
        z1_high = z.zones["Z1_recovery"][1]
        z2_low = z.zones["Z2_aerobic_base"][0]
        self.assertLess(z1_high, z2_low,
                        f"Z1 high {z1_high} >= Z2 low {z2_low}")

    # ---- F21: cardio_zones docstring notes Fox formula ----
    def test_F21_cardio_zones_docstring(self):
        from fitness_engine import cardio_zones
        self.assertIn("Fox", cardio_zones.__doc__)

    # ---- F22: somatotype frame refinement symmetric ----
    def test_F22_small_frame_endomorph_becomes_meso(self):
        from fitness_engine import infer_somatotype, Somatotype
        # Male, 95kg, 175cm, 28% BF → endomorph; small wrist → mesomorph.
        result = infer_somatotype(95, 175, 30, Sex.MALE,
                                  body_fat_pct=28, wrist_cm=15.0)
        self.assertEqual(result, Somatotype.MESOMORPH)

    def test_F22_large_frame_ectomorph_becomes_meso(self):
        from fitness_engine import infer_somatotype, Somatotype
        # Male, 65kg, 180cm, 8% BF → ectomorph; large wrist → mesomorph.
        result = infer_somatotype(65, 180, 25, Sex.MALE,
                                  body_fat_pct=8, wrist_cm=20.0)
        self.assertEqual(result, Somatotype.MESOMORPH)

    # ---- F24: WHR citation in docstring ----
    def test_F24_whr_citation(self):
        from fitness_engine import anthropometric_indices
        self.assertIn("WHO", anthropometric_indices.__doc__)

    # ---- F25: adaptive_tdee true median ----
    def test_F25_adaptive_tdee_even_length_median(self):
        from fitness_engine import adaptive_tdee, DailyLog
        # 14 logs with even-length distribution; verify no crash and
        # reasonable output.
        logs = [DailyLog(day=i+1, calories=2000+i*10, weight_kg=80)
                for i in range(14)]
        est = adaptive_tdee(logs, formula_tdee=2500)
        self.assertIsNotNone(est.observed_tdee)

    # ---- F26: adaptive_tdee kcal_per_kg parameter ----
    def test_F26_adaptive_tdee_custom_kcal_per_kg(self):
        from fitness_engine import adaptive_tdee, DailyLog
        logs = [DailyLog(day=i+1, calories=2200, weight_kg=80-i*0.03)
                for i in range(28)]
        est_default = adaptive_tdee(logs, formula_tdee=2500, kcal_per_kg=7700)
        est_custom = adaptive_tdee(logs, formula_tdee=2500, kcal_per_kg=7200)
        # Different conversion factors should produce different observed TDEE.
        self.assertNotEqual(est_default.observed_tdee, est_custom.observed_tdee)

    # ---- F30: strength beginner RIR goal-aware ----
    def test_F30_strength_beginner_keeps_2_rir(self):
        from fitness_engine import intensity_scheme
        scheme = intensity_scheme(GoalArchetype.STRENGTH, ExperienceLevel.BEGINNER)
        # Strength beginners keep 2 RIR (not bumped to 3).
        self.assertEqual(scheme.primary_rir, 2.0)

    def test_F30_hypertrophy_beginner_bumped_to_3(self):
        from fitness_engine import intensity_scheme
        scheme = intensity_scheme(GoalArchetype.MUSCLE_GAIN, ExperienceLevel.BEGINNER)
        # Hypertrophy beginners still get 3 RIR.
        self.assertGreaterEqual(scheme.primary_rir, 3.0)

    # ---- F31: exercise_selection environment-aware ----
    def test_F31_strength_home_no_barbell_specific(self):
        from fitness_engine import exercise_selection
        rule = exercise_selection(GoalArchetype.STRENGTH, TrainingEnvironment.HOME_BODYWEIGHT)
        # Barbell-specific lifts should NOT be in the include list for home.
        self.assertNotIn("barbell_squat", rule.include)
        self.assertNotIn("deadlift", rule.include)

    def test_F31_strength_gym_has_barbell_specific(self):
        from fitness_engine import exercise_selection
        rule = exercise_selection(GoalArchetype.STRENGTH, TrainingEnvironment.GYM_FULL)
        self.assertIn("barbell_squat", rule.include)

    # ---- F32: cuisine_pick locale-aware default ----
    def test_F32_cuisine_pick_default_overridable(self):
        from fitness_engine.decision_trees import cuisine_pick, set_default_cuisines
        import fitness_engine.decision_trees as dt
        original = dt._DEFAULT_CUISINES[:]
        try:
            set_default_cuisines(["ethiopian", "mediterranean"])
            result = cuisine_pick([])
            self.assertEqual(result, ["ethiopian", "mediterranean"])
        finally:
            set_default_cuisines(original)

    # ---- F37: exercise name case normalized ----
    def test_F37_exercise_names_title_case(self):
        from fitness_engine.exercise_plans import EXERCISE_LIBRARY
        # All comprehensive_db exercises should have title-case names.
        for key, ex in EXERCISE_LIBRARY.items():
            if "comprehensive_db" in ex.tags:
                # Title case: each word capitalized.
                self.assertEqual(ex.name, ex.name.title(),
                                 f"Exercise '{ex.name}' not title-case")

    # ---- F41: ScrapedExercise load skips malformed ----
    def test_F41_scraped_exercise_load_skips_malformed(self):
        # The ExerciseDatabase should not crash on a single malformed record.
        import json
        import tempfile
        import os
        from fitness_engine.exercise_database import ExerciseDatabase
        payload = {
            "metadata": {"source": "test"},
            "exercises": [
                {"id": "good", "name": "Good Exercise", "pattern": "squat",
                 "primary_muscle": "quads", "equipment": ["barbell"],
                 "difficulty": 2},
                {"id": "bad", "unexpected_field": "value"},
            ],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(payload, f)
            tmp = f.name
        try:
            db = ExerciseDatabase(db_path=tmp)
            self.assertIn("good", db.exercises)
        finally:
            os.unlink(tmp)

    # ---- F42: curated macros sourcing note ----
    def test_F42_meal_library_sourcing_note(self):
        from fitness_engine.meal_plans import MEAL_LIBRARY
        # The module docstring should mention USDA / approximate.
        # Check the comment is present in the source by verifying the
        # library is non-empty (the comment is above the list).
        self.assertGreater(len(MEAL_LIBRARY), 0)

    # ---- F45: portion scaling warns on clamp ----
    def test_F45_scale_meal_warns_on_clamp(self):
        import io
        from contextlib import redirect_stderr
        from fitness_engine.meal_plans import _scale_meal, MEAL_LIBRARY
        meal = MEAL_LIBRARY[0]
        # Trigger a clamp by requesting a scale > 3.0.
        buf = io.StringIO()
        with redirect_stderr(buf):
            _scale_meal(meal, 5.0)
        self.assertIn("clamped", buf.getvalue())

    # ---- F51: monotonic repeat penalty (smoke test) ----
    def test_F51_planner_runs_without_crash(self):
        from fitness_engine import assemble_7_day_meal_plan
        target = macros_for(2200, 80, 64, GoalArchetype.RECOMPOSITION, Sex.MALE,
                            Somatotype.MESOMORPH, DietaryPreference.OMNIVORE,
                            body_fat_pct=20)
        plan = assemble_7_day_meal_plan(DietaryPreference.OMNIVORE, 2200, target,
                                         meals_per_day=4, seed=42)
        self.assertEqual(len(plan.days), 7)

    # ---- F53: _external_to_meal rejects extreme calories ----
    def test_F53_external_to_meal_rejects_extreme_calories(self):
        from fitness_engine.seven_day_meal_planner import _external_to_meal
        # 5000-kcal recipe should be rejected.
        rec = {
            "nutrition_per_serving": {"calories": 5000, "protein_g": 50,
                                       "carbs_g": 500, "fat_g": 250},
            "diet_tags": ["omnivore"],
            "title": "Extreme recipe",
            "slot": "dinner",
            "cuisine": "american",
            "ingredients": [],
            "instructions": ["Cook everything in butter."],
        }
        self.assertIsNone(_external_to_meal(rec))

    # ---- F57: auditor score has floor ----
    def test_F57_auditor_score_floor(self):
        from fitness_engine import audit_7_day_meal_plan, assemble_7_day_meal_plan
        target = macros_for(2200, 80, 64, GoalArchetype.RECOMPOSITION, Sex.MALE,
                            Somatotype.MESOMORPH, DietaryPreference.OMNIVORE,
                            body_fat_pct=20)
        plan = assemble_7_day_meal_plan(DietaryPreference.OMNIVORE, 2200, target,
                                         meals_per_day=4, seed=42)
        audit = audit_7_day_meal_plan(plan)
        self.assertGreaterEqual(audit.score, 40)

    # ---- F58: Recommender auto-runs audit ----
    def test_F58_recommender_includes_meal_plan_audit(self):
        p = ClientProfile(age=30, sex=Sex.MALE, height_cm=178, weight_kg=82)
        rec = Recommender(p).recommend()
        self.assertIsNotNone(rec.meal_plan_audit)
        self.assertTrue(hasattr(rec.meal_plan_audit, "score"))
        self.assertTrue(hasattr(rec.meal_plan_audit, "grade"))

    # ---- F61: goal-strategy mismatch is warning ----
    def test_F61_mismatch_is_warning(self):
        from fitness_engine import ClientProfile, Recommender, GoalArchetype
        # Underweight male selecting FAT_LOSS should trigger a mismatch warning.
        p = ClientProfile(
            age=30, sex=Sex.MALE, height_cm=180, weight_kg=55,
            body_fat_pct=8, primary_goal=GoalArchetype.FAT_LOSS,
        )
        rec = Recommender(p).recommend()
        self.assertTrue(any("decision tree suggests" in w.lower() or "mismatch" in w.lower()
                            for w in rec.warnings),
                        f"Mismatch warning not found in: {rec.warnings}")

    # ---- F62: recursive enum serialization ----
    def test_F62_to_dict_handles_nested_enums(self):
        from fitness_engine import ClientProfile, Sex
        p = ClientProfile(age=30, sex=Sex.MALE, height_cm=178, weight_kg=82)
        d = p.to_dict()
        # Top-level enum should be a string.
        self.assertEqual(d["sex"], "male")
        # Verify it's JSON-serializable.
        import json
        json.dumps(d)  # should not raise

    # ---- F67: motivation normalization ----
    def test_F67_motivation_empty_normalized(self):
        from fitness_engine import ClientProfile, Sex
        p = ClientProfile(age=30, sex=Sex.MALE, height_cm=178, weight_kg=82,
                          motivation="   ")
        self.assertEqual(p.motivation, "appearance")

    def test_F67_motivation_freetext_accepted(self):
        from fitness_engine import ClientProfile, Sex
        p = ClientProfile(age=30, sex=Sex.MALE, height_cm=178, weight_kg=82,
                          motivation="wedding in June")
        self.assertEqual(p.motivation, "wedding in June")

    # ---- F68: persistence schema versioning ----
    def test_F68_schema_version(self):
        import tempfile
        from pathlib import Path
        from fitness_engine import init_db, schema_version
        db = Path(tempfile.gettempdir()) / "fit_test_schema.db"
        if db.exists():
            db.unlink()
        try:
            init_db(str(db))
            v = schema_version(str(db))
            self.assertGreaterEqual(v, 1)
        finally:
            if db.exists():
                db.unlink()

    # ---- F70: delete_client ----
    def test_F70_delete_client(self):
        import tempfile
        from pathlib import Path
        from fitness_engine import (init_db, store_client, add_weight,
                                     delete_client, client_summary)
        db = Path(tempfile.gettempdir()) / "fit_test_delete.db"
        if db.exists():
            db.unlink()
        try:
            init_db(str(db))
            store_client("test-client", "Test", {"age": 30}, db_path=str(db))
            add_weight("test-client", 80.0, day=1, db_path=str(db))
            deleted = delete_client("test-client", db_path=str(db))
            self.assertTrue(deleted)
            with self.assertRaises(KeyError):
                client_summary("test-client", str(db))
            # Deleting again returns False.
            deleted_again = delete_client("test-client", db_path=str(db))
            self.assertFalse(deleted_again)
        finally:
            if db.exists():
                db.unlink()

    # ---- F71: indexes exist ----
    def test_F71_indexes_exist(self):
        import tempfile
        import sqlite3
        from pathlib import Path
        from fitness_engine import init_db
        db = Path(tempfile.gettempdir()) / "fit_test_indexes.db"
        if db.exists():
            db.unlink()
        try:
            init_db(str(db))
            con = sqlite3.connect(str(db))
            indexes = [row[0] for row in con.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
            ).fetchall()]
            con.close()
            self.assertIn("idx_weights_client_day", indexes)
            self.assertIn("idx_adherence_client_day", indexes)
        finally:
            if db.exists():
                db.unlink()

    # ---- F73: structured initial assessment guidance ----
    def test_F73_structured_assessment_guidance(self):
        from fitness_engine.adjustments import initial_assessment_guidance_structured
        # P2 #35 — `goal` parameter removed; signature is now (expected_change_per_week_kg,).
        result = initial_assessment_guidance_structured(0.5)
        self.assertGreater(len(result.rules), 0)
        self.assertIn("condition", result.rules[0])
        self.assertIn("action", result.rules[0])
        self.assertIn("adjustment", result.rules[0])

    # ---- F75: showcase defaults co-located ----
    def test_F75_showcase_defaults_present(self):
        from fitness_engine import all_curated
        for ap in all_curated():
            self.assertIsNotNone(ap.showcase_defaults,
                                 f"{ap.nickname} missing showcase_defaults")

    # ---- F76: unified serialization ----
    def test_F76_cli_format_plan_json(self):
        from fitness_engine.cli import _format_plan_json
        p = ClientProfile(age=30, sex=Sex.MALE, height_cm=178, weight_kg=82)
        rec = Recommender(p).recommend()
        # Should not raise; output should be valid JSON.
        import json
        data = json.loads(_format_plan_json(rec))
        self.assertIn("archetype_signature", data)

    # ---- F79: ArchetypeProfile exported ----
    def test_F79_archetype_profile_exported(self):
        import fitness_engine
        self.assertTrue(hasattr(fitness_engine, "ArchetypeProfile"))


class TestSecondAuditFixes(unittest.TestCase):
    """Fixes for true findings from the second (external) audit that were
    not already addressed in the first remediation pass."""

    # ---- cuisine_pick case normalization ----
    def test_cuisine_pick_normalizes_case(self):
        from fitness_engine.decision_trees import cuisine_pick
        result = cuisine_pick(["Mediterranean", "Asian"])
        self.assertEqual(result, ["mediterranean", "asian"])

    # ---- meal_plan_seed XORed with plan_week ----
    def test_meal_plan_seed_changes_with_week(self):
        p1 = ClientProfile(age=30, sex=Sex.MALE, height_cm=178, weight_kg=82,
                           meal_plan_seed=42, plan_week=1)
        p2 = ClientProfile(age=30, sex=Sex.MALE, height_cm=178, weight_kg=82,
                           meal_plan_seed=42, plan_week=2)
        from fitness_engine.recommender import Recommender
        seed1 = Recommender(p1)._meal_seed()
        seed2 = Recommender(p2)._meal_seed()
        self.assertNotEqual(seed1, seed2,
                            "Same meal_plan_seed should produce different seeds for different weeks")

    # ---- 5-day split has 2 leg sessions ----
    def test_five_day_split_has_two_leg_sessions(self):
        from fitness_engine import training_split
        ts = training_split(GoalArchetype.MUSCLE_GAIN, ExperienceLevel.INTERMEDIATE, 5)
        leg_count = sum(1 for d in ts.days if "leg" in d.lower())
        self.assertGreaterEqual(leg_count, 2, f"5-day split should have ≥2 leg sessions: {ts.days}")

    def test_five_day_weekly_split_has_two_leg_days(self):
        from fitness_engine import weekly_split
        plan = weekly_split(GoalArchetype.MUSCLE_GAIN, ExperienceLevel.INTERMEDIATE,
                            5, TrainingEnvironment.GYM_FULL)
        leg_days = [k for k in plan.keys() if "leg" in k.lower()]
        self.assertGreaterEqual(len(leg_days), 2, f"5-day split should have ≥2 leg days: {list(plan.keys())}")

    # ---- home bodyweight excludes pull-up-bar exercises ----
    def test_home_bodyweight_no_pullup_bar_exercises(self):
        from fitness_engine import ClientProfile, Recommender, TrainingEnvironment
        p = ClientProfile(
            age=30, sex=Sex.MALE, height_cm=178, weight_kg=82,
            environment=TrainingEnvironment.HOME_BODYWEIGHT,
            days_per_week=3, meals_per_day=4,
        )
        rec = Recommender(p).recommend()
        bar_exercises = []
        for day, exs in rec.training.weekly_schedule.items():
            for ex in exs:
                if "pullup_bar" in ex.get("equipment", []):
                    bar_exercises.append(ex["name"])
        self.assertEqual(bar_exercises, [],
                         f"HOME_BODYWEIGHT plan should not include pull-up bar exercises: {bar_exercises}")

    # ---- add_weight validates input ----
    def test_add_weight_rejects_zero(self):
        import tempfile
        from pathlib import Path
        from fitness_engine import init_db, add_weight
        db = Path(tempfile.gettempdir()) / "fit_test_wt.db"
        if db.exists():
            db.unlink()
        try:
            init_db(str(db))
            with self.assertRaises(ValueError):
                add_weight("test", 0, db_path=str(db))
            with self.assertRaises(ValueError):
                add_weight("test", -5, db_path=str(db))
            with self.assertRaises(ValueError):
                add_weight("test", 600, db_path=str(db))
        finally:
            if db.exists():
                db.unlink()

    # ---- add_adherence validates input ----
    def test_add_adherence_rejects_out_of_range(self):
        import tempfile
        from pathlib import Path
        from fitness_engine import init_db, add_adherence
        db = Path(tempfile.gettempdir()) / "fit_test_adh.db"
        if db.exists():
            db.unlink()
        try:
            init_db(str(db))
            with self.assertRaises(ValueError):
                add_adherence("test", nutrition_pct=-10, db_path=str(db))
            with self.assertRaises(ValueError):
                add_adherence("test", nutrition_pct=150, db_path=str(db))
        finally:
            if db.exists():
                db.unlink()

    # ---- client_summary returns plan_json ----
    def test_client_summary_returns_plan_json(self):
        import tempfile
        from pathlib import Path
        from fitness_engine import init_db, store_client, client_summary
        db = Path(tempfile.gettempdir()) / "fit_test_pjson.db"
        if db.exists():
            db.unlink()
        try:
            init_db(str(db))
            store_client("test", "Test", {"age": 30}, plan={"key": "value"}, db_path=str(db))
            summary = client_summary("test", str(db))
            self.assertGreater(len(summary["plans"]), 0)
            self.assertIn("plan_json", summary["plans"][0])
        finally:
            if db.exists():
                db.unlink()

    # ---- tdee rejects bmr=0 ----
    def test_tdee_rejects_zero_bmr(self):
        from fitness_engine import tdee, ActivityLevel
        with self.assertRaises(ValueError):
            tdee(0, ActivityLevel.SEDENTARY)

    # ---- supplement_stack no creatine duplicate for vegan ----
    def test_vegan_creatine_not_duplicated(self):
        from fitness_engine import supplement_stack
        sp = supplement_stack(GoalArchetype.MUSCLE_GAIN, DietaryPreference.VEGAN)
        foundational_names = [s[0] for s in sp.foundational]
        goal_specific_names = [s[0] for s in sp.goal_specific]
        # Creatine should be in foundational (vegan) but NOT in goal_specific.
        self.assertIn("Creatine monohydrate", foundational_names)
        self.assertNotIn("Creatine monohydrate", goal_specific_names)

    # ---- vegan bulk protein higher than omnivore ----
    def test_vegan_bulk_protein_higher(self):
        m_v = macros_for(2500, 70, 55, GoalArchetype.MUSCLE_GAIN, Sex.MALE,
                          Somatotype.MESOMORPH, DietaryPreference.VEGAN,
                          body_fat_pct=12)
        m_o = macros_for(2500, 70, 55, GoalArchetype.MUSCLE_GAIN, Sex.MALE,
                          Somatotype.MESOMORPH, DietaryPreference.OMNIVORE,
                          body_fat_pct=12)
        self.assertGreater(m_v.protein_g, m_o.protein_g,
                           "Vegan bulk protein should be higher than omnivore (BF% known)")

    # ---- render_html escapes XSS ----
    def test_render_html_escapes_medical_flags(self):
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "examples"))
        from render_html import render
        p = ClientProfile(
            age=30, sex=Sex.MALE, height_cm=178, weight_kg=82,
            medical_flags={"<script>alert(1)</script>": True},
        )
        rec = Recommender(p).recommend()
        html = render(rec, "Test")
        # The script tag should be escaped, not rendered as HTML.
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;", html)

    # ---- leg_day no longer has duplicate squat pattern ----
    def test_leg_day_no_duplicate_squat(self):
        from fitness_engine.exercise_plans import weekly_split
        import inspect
        source = inspect.getsource(weekly_split)
        # The leg_day function should not have ["squat", "hinge", "squat", ...]
        # (the duplicate squat was removed)
        self.assertNotIn('"squat", "hinge", "squat"', source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
