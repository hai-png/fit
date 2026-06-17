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
    ActivityLevel, AgeGroup, ArchetypeProfile, ArchetypeSignature,
    DietaryPreference, ExperienceLevel, GoalArchetype,
    SessionLength, Sex, Somatotype, TrainingEnvironment,
    TraineeCategory, TraineeProfile,
    CURATED_PROFILES, all_curated, get_curated, signature_from_dict,
    enumerate_signatures, iter_signatures, total_combinations,
)
from .calculators import (
    BodyComposition, CardioZones, EnergyExpenditure, Hydration, Macros,
    StrengthEstimate, MicronutrientTargets, MuscularPotential,
    AnthropometricIndices, MacroAdjustment, DailyLog, AdaptiveTDEEEstimate,
    ReverseDietStep, ReverseDietProtocol,
    body_composition, body_fat_navy, body_fat_bmi_method,
    body_fat_from_visual, visual_bf_description, VISUAL_BF_BANDS,
    correct_bf_estimate,
    bmi, bmi_category, bmr_harris_benedict, bmr_mifflin, bmr_katch,
    tdee, calorie_target, energy_expenditure, hydration,
    macros_for, cardio_zones, one_rep_max, weekly_tonnage,
    micronutrient_targets, muscular_potential,
    anthropometric_indices, ideal_body_weight_devine,
    adjust_macros_for_calorie_change, adaptive_tdee, reverse_diet_protocol,
    infer_age_group, infer_somatotype, classify_trainee, recommend_phase_strategy,
    ACTIVITY_MULTIPLIERS, BULK_MONTHLY_RATE, FAT_LOSS_WEEKLY_RATE,
    fat_loss_rate_for_bodyfat, macro_cycle, MacroCycle,
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
from .seven_day_meal_planner import (
    DayPlanQuality, MealAlternativeSet, SevenDayMealPlan, load_external_recipe_meals, recipe_pool,
    assemble_7_day_meal_plan,
)
from .meal_plan_auditor import MealPlanAudit, audit_7_day_meal_plan
from .exercise_plans import (
    EXERCISE_LIBRARY, Exercise, weekly_split, build_session,
    ENVIRONMENT_EQUIPMENT,
)
from .questionnaires import (
    DIETARY, FITNESS_HISTORY, GOALS, HEALTH_SCREEN, FULL_INTAKE,
    intake_report, IntakeReport,
)
from .protocols import (
    ExercisePlanProtocol, MealPlanProtocol, CompleteProfileProtocol,
    build_exercise_plan_protocol, build_meal_plan_protocol,
    build_complete_profile_protocol,
)
from .recommender import (
    ClientProfile, PlanRecommendation, TrainingPlan, NutritionPlan,
    Recommender,
)
from .persistence import (
    init_db, store_client, add_weight, add_adherence, client_summary,
    delete_client, schema_version,
)
from .exercise_database import ExerciseDatabase, ScrapedExercise

__all__ = [
    # archetypes
    "ActivityLevel", "AgeGroup", "ArchetypeProfile", "ArchetypeSignature",
    "DietaryPreference", "ExperienceLevel", "GoalArchetype",
    "SessionLength", "Sex", "Somatotype", "TrainingEnvironment",
    "TraineeCategory", "TraineeProfile", "classify_trainee",
    "CURATED_PROFILES", "all_curated", "get_curated", "signature_from_dict",
    "enumerate_signatures", "iter_signatures", "total_combinations",
    # calculators
    "BodyComposition", "CardioZones", "EnergyExpenditure", "Hydration",
    "Macros", "StrengthEstimate", "MicronutrientTargets", "MuscularPotential",
    "AnthropometricIndices", "MacroAdjustment", "DailyLog",
    "AdaptiveTDEEEstimate", "ReverseDietStep", "ReverseDietProtocol",
    "body_composition", "body_fat_navy", "body_fat_bmi_method",
    "body_fat_from_visual", "visual_bf_description", "VISUAL_BF_BANDS",
    "correct_bf_estimate",
    "bmi", "bmi_category", "bmr_harris_benedict", "bmr_mifflin", "bmr_katch",
    "tdee", "calorie_target", "energy_expenditure", "hydration", "macros_for",
    "cardio_zones", "one_rep_max", "weekly_tonnage",
    "micronutrient_targets", "muscular_potential",
    "anthropometric_indices", "ideal_body_weight_devine",
    "adjust_macros_for_calorie_change", "adaptive_tdee", "reverse_diet_protocol",
    "infer_age_group", "infer_somatotype", "classify_trainee",
    "recommend_phase_strategy",
    "ACTIVITY_MULTIPLIERS", "BULK_MONTHLY_RATE", "FAT_LOSS_WEEKLY_RATE",
    "fat_loss_rate_for_bodyfat", "macro_cycle", "MacroCycle",
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
    "DayPlanQuality", "MealAlternativeSet", "SevenDayMealPlan", "load_external_recipe_meals",
    "recipe_pool", "assemble_7_day_meal_plan",
    "MealPlanAudit", "audit_7_day_meal_plan",
    # exercise plans
    "EXERCISE_LIBRARY", "Exercise", "weekly_split", "build_session",
    "ENVIRONMENT_EQUIPMENT",
    # questionnaires
    "DIETARY", "FITNESS_HISTORY", "GOALS", "HEALTH_SCREEN", "FULL_INTAKE",
    "intake_report", "IntakeReport",
    # protocols
    "ExercisePlanProtocol", "MealPlanProtocol", "CompleteProfileProtocol",
    "build_exercise_plan_protocol", "build_meal_plan_protocol",
    "build_complete_profile_protocol",
    # main
    "ClientProfile", "PlanRecommendation", "TrainingPlan", "NutritionPlan",
    "Recommender",
    # persistence
    "init_db", "store_client", "add_weight", "add_adherence", "client_summary",
    "delete_client", "schema_version",
    # exercise database
    "ExerciseDatabase", "ScrapedExercise",
]

__version__ = "2.4.0"
