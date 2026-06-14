"""
fitness_engine
==============

A comprehensive, systematic engine for generating customised exercise
and meal plans from detailed client profiles.

Modules
-------
archetypes       — multi-dimensional archetype framework
calculators      — health & fitness numerical engines
questionnaires   — validated intake forms (PAR-Q+, health, lifestyle, ...)
decision_trees   — decision logic from archetype → recommendations
meal_plans       — structured meal library
exercise_plans   — exercise library and weekly splits
recommender      — main orchestrator

Quickstart
---------
>>> from fitness_engine import ClientProfile, Recommender
>>> p = ClientProfile(age=34, sex="female", height_cm=168, weight_kg=72, ...)
>>> rec = Recommender(p).recommend()
>>> print(rec.archetype_signature, rec.nutrition.macros.protein_g)
"""
from .archetypes import (
    ActivityLevel, AgeGroup, ArchetypeSignature, CookingSkill,
    DietaryPreference, ExperienceLevel, GoalArchetype, HealthCondition,
    SessionLength, Sex, Somatotype, TrainingEnvironment,
    CURATED_PROFILES, all_curated, get_curated, signature_from_dict,
    enumerate_signatures, total_combinations,
)
from .calculators import (
    BodyComposition, CardioZones, EnergyExpenditure, Hydration, Macros,
    StrengthEstimate, body_composition, body_fat_navy, body_fat_bmi_method,
    bmi, bmi_category, bmr_mifflin, bmr_harris, bmr_katch, tdee,
    calorie_target, energy_expenditure, hydration, macros_for,
    cardio_zones, one_rep_max, weekly_tonnage, infer_age_group,
    infer_somatotype,
)
from .decision_trees import (
    IntensityScheme, Periodisation, ProgressionRule, SessionDensity,
    TrainingSplit, WeeklyVolume, exercise_selection, intensity_scheme,
    macro_overrides, periodisation, cuisine_pick, progression_rule,
    session_density, supplement_stack, training_split, weekly_volume,
)
from .meal_plans import MealItem, MealPlan, MEAL_LIBRARY, assemble_day, assemble_week
from .exercise_plans import EXERCISE_LIBRARY, Exercise, weekly_split, build_session
from .questionnaires import (
    PAR_Q, HEALTH_HISTORY, LIFESTYLE, DIETARY, FITNESS_HISTORY, GOALS,
    FULL_INTAKE, parq_score, intake_report, IntakeReport,
)
from .recommender import (
    ClientProfile, PlanRecommendation, TrainingPlan, NutritionPlan,
    Recommender,
)

__all__ = [
    # archetypes
    "ActivityLevel", "AgeGroup", "ArchetypeSignature", "CookingSkill",
    "DietaryPreference", "ExperienceLevel", "GoalArchetype", "HealthCondition",
    "SessionLength", "Sex", "Somatotype", "TrainingEnvironment",
    "CURATED_PROFILES", "all_curated", "get_curated", "signature_from_dict",
    "enumerate_signatures", "total_combinations",
    # calculators
    "BodyComposition", "CardioZones", "EnergyExpenditure", "Hydration",
    "Macros", "StrengthEstimate", "body_composition", "body_fat_navy",
    "body_fat_bmi_method", "bmi", "bmi_category", "bmr_mifflin", "bmr_harris",
    "bmr_katch", "tdee", "calorie_target", "energy_expenditure", "hydration",
    "macros_for", "cardio_zones", "one_rep_max", "weekly_tonnage",
    "infer_age_group", "infer_somatotype",
    # decision trees
    "IntensityScheme", "Periodisation", "ProgressionRule", "SessionDensity",
    "TrainingSplit", "WeeklyVolume", "exercise_selection", "intensity_scheme",
    "macro_overrides", "periodisation", "cuisine_pick", "progression_rule",
    "session_density", "supplement_stack", "training_split", "weekly_volume",
    # meal plans
    "MealItem", "MealPlan", "MEAL_LIBRARY", "assemble_day", "assemble_week",
    # exercise plans
    "EXERCISE_LIBRARY", "Exercise", "weekly_split", "build_session",
    # questionnaires
    "PAR_Q", "HEALTH_HISTORY", "LIFESTYLE", "DIETARY", "FITNESS_HISTORY",
    "GOALS", "FULL_INTAKE", "parq_score", "intake_report", "IntakeReport",
    # main
    "ClientProfile", "PlanRecommendation", "TrainingPlan", "NutritionPlan",
    "Recommender",
]

__version__ = "1.0.0"
