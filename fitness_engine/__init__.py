"""
fitness_engine
==============

A streamlined engine for generating customised exercise and meal plans
from client profiles, grounded in the RippedBody methodology and the
Muscle & Strength body-type framework.

Quickstart
---------
>>> from fitness_engine import ClientProfile, Recommender
>>> p = ClientProfile(age=25, sex="male", height_cm=178, weight_kg=75, ...)
>>> rec = Recommender(p).recommend()
>>> print(rec.archetype_signature, rec.nutrition.macros.protein_g)
"""
from .archetypes import (
    ActivityLevel, AgeGroup, ArchetypeSignature,
    DietaryPreference, ExperienceLevel, GoalArchetype,
    SessionLength, Sex, Somatotype, TrainingEnvironment,
    TraineeCategory, TraineeProfile,
    CURATED_PROFILES, all_curated, get_curated, signature_from_dict,
    enumerate_signatures, iter_signatures, total_combinations,
)
from .calculators import (
    BodyComposition, CardioZones, EnergyExpenditure, Hydration, Macros,
    StrengthEstimate, MicronutrientTargets, MuscularPotential,
    body_composition, body_fat_navy, body_fat_bmi_method,
    body_fat_from_visual, visual_bf_description, VISUAL_BF_BANDS,
    correct_bf_estimate,
    bmi, bmi_category, bmr_harris_benedict, bmr_mifflin, bmr_katch,
    tdee, calorie_target, energy_expenditure, hydration,
    macros_for, cardio_zones, one_rep_max, weekly_tonnage,
    micronutrient_targets, muscular_potential,
    infer_age_group, infer_somatotype, classify_trainee,
    ACTIVITY_MULTIPLIERS, BULK_MONTHLY_RATE, FAT_LOSS_WEEKLY_RATE,
    MAX_1RM_REPS,
)
from .adjustments import (
    CUT_BULK_BOUNDARIES, PROGRESS_RATES,
    CutAdjustmentChecklist, BulkAdjustmentChecklist, PlateauChecklist,
    ProgressTrackingGuide, MetabolicAdaptationInfo,
    cut_adjustment_checklist, bulk_adjustment_checklist,
    training_plateau_checklist, progress_tracking_guide,
    metabolic_adaptation_info, initial_assessment_guidance,
)
from .decision_trees import (
    IntensityScheme, Periodisation, ProgressionRule, SessionDensity,
    TrainingSplit, WeeklyVolume, exercise_selection, intensity_scheme,
    cuisine_pick, progression_rule, session_density, supplement_stack,
    training_split, weekly_volume, periodisation,
)
from .meal_plans import MealItem, MealPlan, MEAL_LIBRARY, assemble_day, assemble_week
from .exercise_plans import (
    EXERCISE_LIBRARY, Exercise, weekly_split, build_session,
    ENVIRONMENT_EQUIPMENT,
)
from .questionnaires import (
    DIETARY, FITNESS_HISTORY, GOALS, FULL_INTAKE,
    intake_report, IntakeReport,
)
from .recommender import (
    ClientProfile, PlanRecommendation, TrainingPlan, NutritionPlan,
    Recommender,
)

__all__ = [
    # archetypes
    "ActivityLevel", "AgeGroup", "ArchetypeSignature",
    "DietaryPreference", "ExperienceLevel", "GoalArchetype",
    "SessionLength", "Sex", "Somatotype", "TrainingEnvironment",
    "TraineeCategory", "TraineeProfile", "classify_trainee",
    "CURATED_PROFILES", "all_curated", "get_curated", "signature_from_dict",
    "enumerate_signatures", "iter_signatures", "total_combinations",
    # calculators
    "BodyComposition", "CardioZones", "EnergyExpenditure", "Hydration",
    "Macros", "StrengthEstimate", "MicronutrientTargets", "MuscularPotential",
    "body_composition", "body_fat_navy", "body_fat_bmi_method",
    "body_fat_from_visual", "visual_bf_description", "VISUAL_BF_BANDS",
    "correct_bf_estimate",
    "bmi", "bmi_category", "bmr_harris_benedict", "bmr_mifflin", "bmr_katch",
    "tdee", "calorie_target", "energy_expenditure", "hydration", "macros_for",
    "cardio_zones", "one_rep_max", "weekly_tonnage",
    "micronutrient_targets", "muscular_potential",
    "infer_age_group", "infer_somatotype", "classify_trainee",
    "ACTIVITY_MULTIPLIERS", "BULK_MONTHLY_RATE", "FAT_LOSS_WEEKLY_RATE",
    "MAX_1RM_REPS",
    # adjustments
    "CUT_BULK_BOUNDARIES", "PROGRESS_RATES",
    "CutAdjustmentChecklist", "BulkAdjustmentChecklist", "PlateauChecklist",
    "ProgressTrackingGuide", "MetabolicAdaptationInfo",
    "cut_adjustment_checklist", "bulk_adjustment_checklist",
    "training_plateau_checklist", "progress_tracking_guide",
    "metabolic_adaptation_info", "initial_assessment_guidance",
    # decision trees
    "IntensityScheme", "Periodisation", "ProgressionRule", "SessionDensity",
    "TrainingSplit", "WeeklyVolume", "exercise_selection", "intensity_scheme",
    "cuisine_pick", "progression_rule", "session_density", "supplement_stack",
    "training_split", "weekly_volume", "periodisation",
    # meal plans
    "MealItem", "MealPlan", "MEAL_LIBRARY", "assemble_day", "assemble_week",
    # exercise plans
    "EXERCISE_LIBRARY", "Exercise", "weekly_split", "build_session",
    "ENVIRONMENT_EQUIPMENT",
    # questionnaires
    "DIETARY", "FITNESS_HISTORY", "GOALS", "FULL_INTAKE",
    "intake_report", "IntakeReport",
    # main
    "ClientProfile", "PlanRecommendation", "TrainingPlan", "NutritionPlan",
    "Recommender",
]

__version__ = "2.0.0"
