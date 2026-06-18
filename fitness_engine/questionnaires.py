"""
questionnaires.py
=================

Streamlined intake forms. The old PAR-Q, lifestyle and health-history
questionnaires have been removed in favour of a lean profile. Common
health and lifestyle considerations are handled via *recommendations
and warnings* generated from the client's body composition and trainee
category, rather than a long screening form.

Forms implemented
-----------------
1. Diet & preferences — omnivore/vegan, allergies, optional traditional cuisine.
2. Fitness history    — experience level, training environment (3 options).
3. Goals              — single primary goal, target weight, timeline.

This keeps the intake fast (90 seconds) while still capturing the
inputs that actually drive the plan.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    # NEW-V1-4 — import Sex under TYPE_CHECKING so the type annotation
    # resolves for IDEs without introducing a runtime circular import.
    from .archetypes import Sex


# --------------------------------------------------------------------------- #
# Primitive                                                                   #
# --------------------------------------------------------------------------- #
class QuestionType(str, Enum):
    SINGLE = "single"
    MULTI = "multi"
    INT = "int"
    FLOAT = "float"
    TEXT = "text"


@dataclass(frozen=True)
class Choice:
    id: str
    label: str
    score: float = 0.0


@dataclass(frozen=True)
class Question:
    id: str
    prompt: str
    qtype: QuestionType
    required: bool = True
    choices: List[Choice] = field(default_factory=list)
    help: str = ""
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    units: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "prompt": self.prompt,
            "type": self.qtype.value,
            "required": self.required,
            "choices": [{"id": c.id, "label": c.label} for c in self.choices],
            "help": self.help,
            "min": self.min_value,
            "max": self.max_value,
            "units": self.units,
        }


# --------------------------------------------------------------------------- #
# 1. Diet & preferences                                                        #
# --------------------------------------------------------------------------- #
DIETARY = [
    Question(
        id="d_pref",
        prompt="Dietary pattern",
        qtype=QuestionType.SINGLE,
        choices=[
            Choice("omnivore", "Omnivore (eat everything)"),
            Choice("balanced", "Balanced (no exclusions, mixed macros)"),
            Choice("vegetarian", "Vegetarian (no meat, dairy + eggs OK)"),
            Choice("vegan", "Vegan (no animal products)"),
            Choice("pescatarian", "Pescatarian (fish + vegetarian)"),
            Choice("pollo_pescatarian", "Pollo-pescatarian (poultry + fish + veg)"),
            Choice("mediterranean", "Mediterranean (fish, veg, olive oil, whole grains)"),
            Choice("keto", "Keto (<50 g carbs/day)"),
            Choice("low_carb", "Low-carb (50-130 g carbs/day)"),
            Choice("paleo", "Paleo (meat, fish, veg, fruit, nuts; no grains/dairy)"),
            Choice("gluten_free", "Gluten-free (medical or preference)"),
            Choice("high_protein", "High-protein (≥2.0 g/kg body weight)"),
        ],
    ),
    Question(
        id="d_allergies",
        prompt="Food allergies / intolerances (optional)",
        qtype=QuestionType.MULTI,
        required=False,
        choices=[
            Choice("dairy", "Dairy"),
            Choice("gluten", "Gluten"),
            Choice("nuts", "Tree nuts"),
            Choice("peanuts", "Peanuts"),
            Choice("soy", "Soy"),
            Choice("eggs", "Eggs"),
            Choice("shellfish", "Shellfish"),
            Choice("fish", "Fish"),
        ],
    ),
    Question(
        id="d_dislikes",
        prompt="Foods you strongly dislike (optional, free text)",
        qtype=QuestionType.TEXT,
        required=False,
    ),
    Question(
        id="d_cuisine",
        prompt="Add a traditional cuisine preference? (optional)",
        qtype=QuestionType.SINGLE,
        required=False,
        choices=[
            Choice("none", "No preference"),
            Choice("american", "American"),
            Choice("mediterranean", "Mediterranean"),
            Choice("asian", "East / SE Asian"),
            Choice("indian", "Indian / South Asian"),
            Choice("mexican", "Mexican / Latin"),
            Choice("middle_eastern", "Middle Eastern"),
            Choice("african", "African"),
            Choice("nordic", "Nordic / European"),
        ],
    ),
]


# --------------------------------------------------------------------------- #
# 2. Fitness history                                                           #
# --------------------------------------------------------------------------- #
FITNESS_HISTORY = [
    Question(
        id="fh_experience",
        prompt="Training experience",
        qtype=QuestionType.SINGLE,
        choices=[
            Choice("beginner", "Beginner (new to training, < 1 year)"),
            Choice("intermediate", "Intermediate (1-3 years, monthly progress)"),
            Choice("advanced", "Advanced (3+ years, progress over months)"),
        ],
    ),
    Question(
        id="fh_environment",
        prompt="Training environment",
        qtype=QuestionType.SINGLE,
        choices=[
            Choice("home_bodyweight", "Home — bodyweight only"),
            Choice("home_gym", "Home gym / small gym (dumbbells, bands, bench)"),
            Choice("gym_full", "Full gym (barbells, racks, machines)"),
        ],
    ),
    Question(
        id="fh_days_per_week",
        prompt="Days per week available to train",
        qtype=QuestionType.INT,
        min_value=1, max_value=6,
    ),
    Question(
        id="fh_session_length",
        prompt="Typical session length",
        qtype=QuestionType.SINGLE,
        choices=[
            Choice("express_30", "~30 min"),
            Choice("short_45", "~45 min"),
            Choice("standard_60", "~60 min"),
            Choice("extended_90", "~90 min"),
        ],
    ),
]


# --------------------------------------------------------------------------- #
# 3. Goals                                                                     #
# --------------------------------------------------------------------------- #
GOALS = [
    Question(
        id="g_primary",
        prompt="Primary goal",
        qtype=QuestionType.SINGLE,
        choices=[
            Choice("fat_loss", "Fat loss (cut)"),
            Choice("muscle_gain", "Build muscle (bulk)"),
            Choice("recomposition", "Recomposition (fat loss + muscle gain)"),
            Choice("strength", "Get stronger"),
            Choice("general_health", "General health & fitness"),
        ],
    ),
    Question(
        id="g_target_weight",
        prompt="Target weight (optional)",
        qtype=QuestionType.FLOAT,
        required=False,
        units="kg",
    ),
    Question(
        id="g_timeline_weeks",
        prompt="Timeline to primary goal",
        qtype=QuestionType.INT,
        min_value=4, max_value=104,
        units="weeks",
    ),
    Question(
        id="g_motivation",
        prompt="What is driving this change?",
        qtype=QuestionType.SINGLE,
        choices=[
            Choice("health_event", "A health event or diagnosis"),
            Choice("appearance", "Appearance / self-image"),
            Choice("performance", "Performance"),
            Choice("longevity", "Longevity"),
            Choice("mental_health", "Mental health"),
        ],
    ),
]


# --------------------------------------------------------------------------- #
# 4. Health screening (minimal)                                                #
# --------------------------------------------------------------------------- #
# A minimal health screen that populates ``ClientProfile.medical_flags``.
# The engine's recommender surfaces these flags as warnings; the questionnaire
# must ask about them so the flags actually get set. See audit finding F66.
HEALTH_SCREEN = [
    Question(
        id="h_pregnant_postpartum",
        prompt="Are you pregnant or less than 6 weeks postpartum?",
        qtype=QuestionType.SINGLE,
        required=False,
        choices=[
            Choice("no", "No"),
            Choice("yes", "Yes"),
        ],
    ),
    Question(
        id="h_recent_surgery",
        prompt="Have you had surgery in the last 3 months?",
        qtype=QuestionType.SINGLE,
        required=False,
        choices=[
            Choice("no", "No"),
            Choice("yes", "Yes"),
        ],
    ),
    Question(
        id="h_eating_disorder",
        prompt="Have you been diagnosed with or are you recovering from an eating disorder?",
        qtype=QuestionType.SINGLE,
        required=False,
        choices=[
            Choice("no", "No"),
            Choice("yes", "Yes"),
        ],
    ),
    Question(
        id="h_cardiac",
        prompt="Have you been diagnosed with a cardiac condition (heart disease, arrhythmia, etc.)?",
        qtype=QuestionType.SINGLE,
        required=False,
        choices=[
            Choice("no", "No"),
            Choice("yes", "Yes"),
        ],
    ),
    Question(
        id="h_chest_pain",
        prompt="Have you experienced unexplained chest pain or fainting during exercise?",
        qtype=QuestionType.SINGLE,
        required=False,
        choices=[
            Choice("no", "No"),
            Choice("yes", "Yes"),
        ],
    ),
]


# --------------------------------------------------------------------------- #
# Full intake sequence                                                        #
# --------------------------------------------------------------------------- #
# P1 #14 — previously FULL_INTAKE covered only 15 of 30 ClientProfile fields.
# The "core demographics" section is now added so an intake form can populate
# the demographics the engine requires (age, sex, height_cm, weight_kg) plus
# the optional anthropometrics (body_fat_pct, waist/neck/hip/wrist_cm,
# visual_bf_label, resting_hr, measured_max_hr) and lifestyle (activity,
# meals_per_day, working_weights_kg). The original four sections are retained
# unchanged for backwards compatibility.
CORE_DEMOGRAPHICS = [
    ("age", "How old are you? (13-100)", "int"),
    ("sex", "Biological sex? (male / female) — needed for BMR & BF formulas", "choice:male,female"),
    ("height_cm", "Height in cm (50-250)", "float"),
    ("weight_kg", "Current weight in kg (20-350)", "float"),
    ("body_fat_pct", "Body fat %% if known (2-70), else leave blank", "float?"),
    ("waist_cm", "Waist circumference at navel in cm (optional)", "float?"),
    ("neck_cm", "Neck circumference at narrowest point in cm (optional)", "float?"),
    ("hip_cm", "Hip circumference at widest point in cm (optional, required for female Navy BF)", "float?"),
    ("wrist_cm", "Wrist circumference for frame-size estimation (optional)", "float?"),
    ("visual_bf_label", "Visual body-fat estimate if you have one (shredded/lean/average_fit/average/overweight/obese)", "str?"),
    ("resting_hr", "Resting heart rate in bpm (30-220, default 60)", "int"),
    ("measured_max_hr", "Measured max HR if known (80-240, optional)", "int?"),
    ("activity", "Activity level (sedentary/mostly_sedentary/lightly_active/moderately_active/very_active)", "choice"),
    ("meals_per_day", "Preferred meals per day (3-5, default 4)", "int"),
    ("working_weights_kg", "Current working weights as JSON: {squat: 100, bench_press: 80, ...}", "dict?"),
]

FULL_INTAKE = [
    ("Core Demographics", CORE_DEMOGRAPHICS),
    ("Diet & Preferences", DIETARY),
    ("Fitness History", FITNESS_HISTORY),
    ("Goals", GOALS),
    ("Health Screen", HEALTH_SCREEN),
]


# --------------------------------------------------------------------------- #
# Health & lifestyle recommendations                                          #
# --------------------------------------------------------------------------- #
# Instead of a PAR-Q questionnaire, we generate recommendations and warnings
# from the client's body composition, trainee category, and goals.

@dataclass(frozen=True)
class IntakeReport:
    warnings: List[str]
    notes: List[str]
    recommendations: List[str]


def intake_report(
    bmi_val: float,
    body_fat_pct: Optional[float],
    calorie_target: float,
    trainee_summary: str = "",
    trainee_recommendations: Optional[List[str]] = None,
    sex: Optional["Sex"] = None,
) -> IntakeReport:
    """Generate health/lifestyle recommendations based on body metrics.

    Replaces the old PAR-Q / health-history forms with targeted advice
    derived from the client's actual data.

    P1 #5 — sex parameter added so calorie floor and body-fat thresholds
    are sex-aware. Previously a female at 26% BF (healthy) and a male at
    26% BF (slightly elevated) got identical 'Moderate body fat — steady
    cut' advice — wrong for the female.
    """
    # Avoid circular import: import Sex lazily.
    from .archetypes import Sex as _Sex
    if sex is not None:
        sex = _Sex(sex)

    warnings: List[str] = []
    notes: List[str] = []
    recommendations: List[str] = []

    # Calorie floor warning — sex-aware (male 1500, female 1200).
    # Previously used a flat 1200 for everyone, under-warning male users
    # whose target should not drop below 1500.
    floor = 1200 if sex == _Sex.FEMALE else 1500
    # P2 #28 — use <= instead of < so a target exactly at the floor also
    # warns (defensive check for direct callers bypassing calorie_target's
    # upstream clamp).
    if calorie_target <= floor:
        warnings.append(
            f"Calorie target below {floor} kcal — consider medical supervision "
            "and prioritise nutrient-dense foods."
        )

    # BMI-based notes
    if bmi_val < 18.5:
        notes.append(
            "BMI in the underweight range — ensure adequate calorie and "
            "protein intake to support training recovery."
        )
    elif bmi_val >= 30:
        notes.append(
            "BMI in the obese range — gradual, sustainable weight loss with "
            "resistance training will protect lean mass and metabolic health."
        )

    # Body-fat-based notes — sex-aware thresholds.
    # Male: 25%+ elevated, 30%+ high. Female: 30%+ elevated, 36%+ high
    # (female essential fat is ~10-13% vs male ~3-5%, so the same absolute
    # BF% means very different things). Previously a female at 26% BF got
    # the same 'Moderate body fat — steady cut' advice as a male at 26%.
    if body_fat_pct is not None:
        high_threshold = 30 if sex != _Sex.FEMALE else 36
        moderate_threshold = 25 if sex != _Sex.FEMALE else 30
        if body_fat_pct >= high_threshold:
            recommendations.append(
                "Higher body fat — focus on a moderate deficit and resistance "
                "training. Cardio is supplementary, not the main driver."
            )
        elif body_fat_pct >= moderate_threshold:
            recommendations.append(
                "Moderate body fat — a steady cut with 3 days/week lifting "
                "will preserve muscle while shedding fat."
            )

    # General health recommendations (always present)
    recommendations.extend([
        "Prioritise 7-9 hours of sleep per night — recovery drives progress.",
        "Track your weight daily (morning, after bathroom) and use the weekly average.",
        "Take waist measurements weekly at the navel and 3 fingers above/below.",
        "If you have a diagnosed medical condition or are on medication, "
        "consult your physician before starting a new training and diet program.",
    ])

    # Add trainee-category-specific recommendations
    if trainee_recommendations:
        recommendations.extend(trainee_recommendations)

    return IntakeReport(
        warnings=warnings,
        notes=notes,
        recommendations=recommendations,
    )
