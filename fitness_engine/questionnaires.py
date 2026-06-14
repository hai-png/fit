"""
questionnaires.py
=================

Validated intake forms. Each form is a list of `Question` objects that can
be presented sequentially, scored algorithmically, and persisted to JSON.

Forms implemented
-----------------
1. PAR-Q+ (Physical Activity Readiness Questionnaire) — standard
   pre-exercise screening.
2. Health history — medical, surgical, family.
3. Lifestyle & behavioural — sleep, stress, work, travel.
4. Dietary preferences — allergies, restrictions, palate, habits.
5. Fitness history & experience — training background, current
   routine, milestones.
6. Goals & motivation — primary/secondary goals, timeline, identity.

The same `Question` primitive drives all forms so we get uniform UX,
storage, and analytics across the suite.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


# --------------------------------------------------------------------------- #
# Primitive                                                                   #
# --------------------------------------------------------------------------- #
class QuestionType(str, Enum):
    SINGLE = "single"
    MULTI = "multi"
    INT = "int"
    FLOAT = "float"
    TEXT = "text"
    BOOL = "bool"


@dataclass
class Choice:
    id: str
    label: str
    score: float = 0.0       # for risk/severity scoring


@dataclass
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
            "choices": [asdict(c) for c in self.choices],
            "help": self.help,
            "min": self.min_value,
            "max": self.max_value,
            "units": self.units,
        }


# --------------------------------------------------------------------------- #
# 1. PAR-Q+                                                                   #
# --------------------------------------------------------------------------- #
PAR_Q = [
    Question(
        id="parq_1",
        prompt=("Has your doctor ever said that you have a heart condition "
                "and that you should only do physical activity recommended "
                "by a doctor?"),
        qtype=QuestionType.BOOL,
        choices=[Choice("yes", "Yes", score=4.0), Choice("no", "No", 0)],
        help="Standard PAR-Q item 1.",
    ),
    Question(
        id="parq_2",
        prompt=("Do you feel pain in your chest when you do physical "
                "activity?"),
        qtype=QuestionType.BOOL,
        choices=[Choice("yes", "Yes", score=4.0), Choice("no", "No", 0)],
    ),
    Question(
        id="parq_3",
        prompt=("In the past month, have you had chest pain when not doing "
                "physical activity?"),
        qtype=QuestionType.BOOL,
        choices=[Choice("yes", "Yes", score=4.0), Choice("no", "No", 0)],
    ),
    Question(
        id="parq_4",
        prompt="Do you lose your balance because of dizziness?",
        qtype=QuestionType.BOOL,
        choices=[Choice("yes", "Yes", score=2.0), Choice("no", "No", 0)],
    ),
    Question(
        id="parq_5",
        prompt=("Do you have a bone or joint problem that could be made "
                "worse by a change in your physical activity?"),
        qtype=QuestionType.BOOL,
        choices=[Choice("yes", "Yes", score=2.0), Choice("no", "No", 0)],
    ),
    Question(
        id="parq_6",
        prompt=("Is your doctor currently prescribing drugs for your blood "
                "pressure or heart condition?"),
        qtype=QuestionType.BOOL,
        choices=[Choice("yes", "Yes", score=1.5), Choice("no", "No", 0)],
    ),
    Question(
        id="parq_7",
        prompt="Do you know of any other reason why you should not do physical activity?",
        qtype=QuestionType.BOOL,
        choices=[Choice("yes", "Yes", score=2.0), Choice("no", "No", 0)],
    ),
]


def parq_score(answers: Dict[str, str]) -> float:
    """Return aggregate PAR-Q score (0-15.5). > 4 → recommend physician clearance."""
    score = 0.0
    for q in PAR_Q:
        ans = answers.get(q.id)
        for c in q.choices:
            if c.id == ans:
                score += c.score
                break
    return score


# --------------------------------------------------------------------------- #
# 2. Health history                                                           #
# --------------------------------------------------------------------------- #
HEALTH_HISTORY = [
    Question(
        id="hh_age",
        prompt="Age (years)",
        qtype=QuestionType.INT,
        min_value=14, max_value=100,
    ),
    Question(
        id="hh_biological_sex",
        prompt="Biological sex (affects physiology calculations)",
        qtype=QuestionType.SINGLE,
        choices=[Choice("male", "Male"), Choice("female", "Female")],
    ),
    Question(
        id="hh_height",
        prompt="Height",
        qtype=QuestionType.FLOAT,
        min_value=120, max_value=220, units="cm",
    ),
    Question(
        id="hh_weight",
        prompt="Current weight",
        qtype=QuestionType.FLOAT,
        min_value=30, max_value=250, units="kg",
    ),
    Question(
        id="hh_conditions",
        prompt="Diagnosed medical conditions (select all that apply)",
        qtype=QuestionType.MULTI,
        required=False,
        choices=[
            Choice("none", "None"),
            Choice("t2_diabetes", "Type 2 diabetes"),
            Choice("pre_diabetes", "Pre-diabetes"),
            Choice("hypertension", "Hypertension"),
            Choice("high_cholesterol", "High cholesterol"),
            Choice("pcos", "PCOS"),
            Choice("hypothyroidism", "Hypothyroidism"),
            Choice("joint_knee", "Knee joint issue"),
            Choice("joint_shoulder", "Shoulder joint issue"),
            Choice("lower_back", "Lower back issue"),
            Choice("cardio_limited", "Cardiovascular limitation"),
            Choice("celiac", "Celiac disease"),
            Choice("ibs", "IBS"),
            Choice("pregnancy", "Currently pregnant"),
            Choice("postpartum", "Postpartum (< 12 months)"),
        ],
    ),
    Question(
        id="hh_medications",
        prompt="Medications (free text — write 'none' if none)",
        qtype=QuestionType.TEXT,
        required=False,
    ),
    Question(
        id="hh_injuries",
        prompt="Current or recent injuries (free text)",
        qtype=QuestionType.TEXT,
        required=False,
    ),
    Question(
        id="hh_family_history",
        prompt="Relevant family medical history (cardiac events < 55y, diabetes, etc.)",
        qtype=QuestionType.TEXT,
        required=False,
    ),
]


# --------------------------------------------------------------------------- #
# 3. Lifestyle                                                                #
# --------------------------------------------------------------------------- #
LIFESTYLE = [
    Question(
        id="ls_sleep_hours",
        prompt="Average sleep per night",
        qtype=QuestionType.FLOAT,
        min_value=0, max_value=14, units="hours",
    ),
    Question(
        id="ls_sleep_quality",
        prompt="Self-rated sleep quality",
        qtype=QuestionType.SINGLE,
        choices=[
            Choice("poor", "Poor — wake unrefreshed"),
            Choice("fair", "Fair"),
            Choice("good", "Good"),
            Choice("excellent", "Excellent"),
        ],
    ),
    Question(
        id="ls_stress",
        prompt="Self-rated stress (1=calm, 10=overwhelmed)",
        qtype=QuestionType.INT,
        min_value=1, max_value=10,
    ),
    Question(
        id="ls_work_type",
        prompt="Typical workday",
        qtype=QuestionType.SINGLE,
        choices=[
            Choice("desk", "Mostly seated (desk)"),
            Choice("mixed", "Mixed sitting / standing"),
            Choice("active", "On feet most of day"),
            Choice("physical", "Physically demanding"),
        ],
    ),
    Question(
        id="ls_travel",
        prompt="Travel frequency disrupting routine",
        qtype=QuestionType.SINGLE,
        choices=[
            Choice("rare", "Rarely"),
            Choice("monthly", "Monthly"),
            Choice("weekly", "Weekly"),
        ],
    ),
    Question(
        id="ls_smoking",
        prompt="Smoking status",
        qtype=QuestionType.SINGLE,
        choices=[
            Choice("never", "Never"),
            Choice("former", "Former"),
            Choice("occasional", "Occasional"),
            Choice("daily", "Daily"),
        ],
    ),
    Question(
        id="ls_alcohol",
        prompt="Alcohol frequency",
        qtype=QuestionType.SINGLE,
        choices=[
            Choice("none", "None"),
            Choice("moderate", "1-3 drinks/week"),
            Choice("regular", "4-7 drinks/week"),
            Choice("heavy", "8+ drinks/week"),
        ],
    ),
]


# --------------------------------------------------------------------------- #
# 4. Dietary preferences                                                      #
# --------------------------------------------------------------------------- #
DIETARY = [
    Question(
        id="d_pref",
        prompt="Dietary pattern",
        qtype=QuestionType.SINGLE,
        choices=[
            Choice("omnivore", "Omnivore"),
            Choice("pescatarian", "Pescatarian"),
            Choice("pollo_pescatarian", "Pollo-pescatarian"),
            Choice("vegetarian", "Vegetarian"),
            Choice("vegan", "Vegan"),
            Choice("keto", "Ketogenic"),
            Choice("mediterranean", "Mediterranean"),
            Choice("low_fodmap", "Low-FODMAP"),
            Choice("halal", "Halal"),
            Choice("kosher", "Kosher"),
            Choice("flexible", "Flexible / no rules"),
        ],
    ),
    Question(
        id="d_allergies",
        prompt="Food allergies / intolerances",
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
        prompt="Foods you strongly dislike (free text)",
        qtype=QuestionType.TEXT,
        required=False,
    ),
    Question(
        id="d_meals_per_day",
        prompt="Preferred meals per day",
        qtype=QuestionType.SINGLE,
        choices=[
            Choice("3", "3 (breakfast / lunch / dinner)"),
            Choice("4", "4 (3 + snack)"),
            Choice("5", "5 (3 + 2 snacks)"),
            Choice("omad", "1 (OMAD)"),
        ],
    ),
    Question(
        id="d_cooking",
        prompt="Cooking skill",
        qtype=QuestionType.SINGLE,
        choices=[
            Choice("basic", "Basic — boil, fry, assemble"),
            Choice("intermediate", "Intermediate — multi-step recipes"),
            Choice("advanced", "Advanced — long and complex"),
        ],
    ),
    Question(
        id="d_cuisine",
        prompt="Preferred cuisines (multi-select)",
        qtype=QuestionType.MULTI,
        required=False,
        choices=[
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
# 5. Fitness history                                                          #
# --------------------------------------------------------------------------- #
FITNESS_HISTORY = [
    Question(
        id="fh_experience",
        prompt="Resistance-training experience",
        qtype=QuestionType.SINGLE,
        choices=[
            Choice("novice", "< 3 months"),
            Choice("beginner", "3-12 months"),
            Choice("intermediate", "1-3 years"),
            Choice("advanced", "3-5 years"),
            Choice("elite", "5+ years competitive"),
        ],
    ),
    Question(
        id="fh_environment",
        prompt="Primary training environment",
        qtype=QuestionType.SINGLE,
        choices=[
            Choice("home_bodyweight", "Home (bodyweight only)"),
            Choice("home_minimal", "Home (bands + dumbbells)"),
            Choice("home_full", "Home (full home gym)"),
            Choice("gym_commercial", "Commercial gym"),
            Choice("gym_full", "Specialised gym (PL/SM)"),
            Choice("hybrid", "Hybrid"),
            Choice("outdoor", "Outdoor"),
        ],
    ),
    Question(
        id="fh_equipment",
        prompt="Available equipment (multi-select)",
        qtype=QuestionType.MULTI,
        required=False,
        choices=[
            Choice("barbell", "Barbell + plates"),
            Choice("dumbbells", "Dumbbells"),
            Choice("kettlebells", "Kettlebells"),
            Choice("bands", "Resistance bands"),
            Choice("machine", "Cable / machines"),
            Choice("cardio_machine", "Treadmill / bike / rower"),
            Choice("box", "Plyo box"),
            Choice("pullup_bar", "Pull-up bar"),
        ],
    ),
    Question(
        id="fh_days_per_week",
        prompt="Days per week available to train",
        qtype=QuestionType.INT,
        min_value=1, max_value=7,
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
    Question(
        id="fh_cardio_preference",
        prompt="Preferred cardio modality",
        qtype=QuestionType.SINGLE,
        choices=[
            Choice("walking", "Walking"),
            Choice("running", "Running"),
            Choice("cycling", "Cycling"),
            Choice("rowing", "Rowing"),
            Choice("swimming", "Swimming"),
            Choice("mixed", "Mixed / none preferred"),
        ],
    ),
    Question(
        id="fh_lifts",
        prompt="Current best lifts (free text, e.g. 'squat 100kg x5, bench 80kg x5')",
        qtype=QuestionType.TEXT,
        required=False,
    ),
]


# --------------------------------------------------------------------------- #
# 6. Goals & motivation                                                       #
# --------------------------------------------------------------------------- #
GOALS = [
    Question(
        id="g_primary",
        prompt="Primary goal",
        qtype=QuestionType.SINGLE,
        choices=[
            Choice("fat_loss", "Fat loss"),
            Choice("muscle_gain", "Build muscle"),
            Choice("recomposition", "Body recomposition"),
            Choice("strength", "Get stronger"),
            Choice("endurance", "Improve endurance"),
            Choice("general_health", "General health"),
            Choice("athletic_performance", "Athletic performance"),
            Choice("rehabilitation", "Rehabilitation"),
        ],
    ),
    Question(
        id="g_secondary",
        prompt="Secondary goals (multi)",
        qtype=QuestionType.MULTI,
        required=False,
        choices=[
            Choice("fat_loss", "Fat loss"),
            Choice("muscle_gain", "Build muscle"),
            Choice("strength", "Get stronger"),
            Choice("endurance", "Improve endurance"),
            Choice("flexibility", "Flexibility / mobility"),
            Choice("energy", "Energy / vitality"),
            Choice("stress", "Stress management"),
            Choice("sleep", "Better sleep"),
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
            Choice("performance", "Performance (sport, hobby)"),
            Choice("longevity", "Longevity"),
            Choice("mental_health", "Mental health"),
            Choice("life_event", "Major life event"),
        ],
    ),
    Question(
        id="g_past_attempts",
        prompt="Past attempts at changing diet / exercise",
        qtype=QuestionType.TEXT,
        required=False,
    ),
    Question(
        id="g_support",
        prompt="Support system",
        qtype=QuestionType.SINGLE,
        choices=[
            Choice("solo", "Mostly solo"),
            Choice("partner", "Partner / spouse"),
            Choice("trainer", "Working with a trainer"),
            Choice("group", "Group / community"),
        ],
    ),
]


# --------------------------------------------------------------------------- #
# Full intake sequence                                                        #
# --------------------------------------------------------------------------- #
FULL_INTAKE = [
    ("PAR-Q+ Pre-screening", PAR_Q),
    ("Health History", HEALTH_HISTORY),
    ("Lifestyle", LIFESTYLE),
    ("Dietary Preferences", DIETARY),
    ("Fitness History", FITNESS_HISTORY),
    ("Goals & Motivation", GOALS),
]


# --------------------------------------------------------------------------- #
# Scoring & validation                                                        #
# --------------------------------------------------------------------------- #
@dataclass
class IntakeReport:
    parq_score: float
    parq_clear: bool
    warnings: List[str]
    notes: List[str]


def intake_report(answers: Dict[str, Any]) -> IntakeReport:
    """Run sanity checks on a complete intake."""
    parq = parq_score({k: answers.get(k, "no") for k in
                       [q.id for q in PAR_Q]})
    warnings: List[str] = []
    notes: List[str] = []

    # PAR-Q threshold
    if parq >= 4:
        warnings.append(
            "PAR-Q score elevated — recommend physician clearance "
            "before vigorous training.")

    # Sleep
    sleep = float(answers.get("ls_sleep_hours", 0) or 0)
    if sleep < 6:
        warnings.append("Sleep < 6 h/night impairs recovery — refer to sleep hygiene module.")

    # Stress
    stress = int(answers.get("ls_stress", 5) or 5)
    if stress >= 8:
        notes.append("High stress — bias toward lower-intensity training and Zone-2 cardio.")

    # Conditions
    conds = answers.get("hh_conditions", []) or []
    if "pregnancy" in conds:
        warnings.append("Pregnancy — avoid supine, Valsalva, and high-impact work.")
    if "postpartum" in conds:
        notes.append("Postpartum — pelvic-floor screening recommended.")
    if "t2_diabetes" in conds:
        notes.append("Type 2 diabetes — schedule training post-meal for glycaemic control.")
    if "hypertension" in conds:
        notes.append("Hypertension — keep training loads sub-maximal, avoid Valsalva.")
    if "lower_back" in conds:
        notes.append("Lower-back issue — restrict axial loading without prior physio clearance.")
    if "joint_knee" in conds:
        notes.append("Knee issue — substitute knee-dominant patterns as needed.")
    if "joint_shoulder" in conds:
        notes.append("Shoulder issue — substitute overhead patterns as needed.")

    return IntakeReport(
        parq_score=parq,
        parq_clear=parq < 4,
        warnings=warnings,
        notes=notes,
    )
