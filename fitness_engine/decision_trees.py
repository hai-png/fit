"""
decision_trees.py
=================

All decision logic that maps a ClientProfile to concrete plan parameters.
Implemented as small, named functions so every rule is auditable,
testable, and traceable to the originating archetype dimensions.

The trees cover:
  * Training split (strength : hypertrophy : cardio)
  * Volume (sets per muscle group per week)
  * Intensity (RPE / %1RM)
  * Exercise selection rules (include / exclude / substitute)
  * Periodisation strategy (linear, undulating, block)
  * Session density (work : rest ratios)
  * Progression scheme
  * Deload frequency
  * Macro split overrides for medical conditions
  * Meal-plan cuisine selection
  * Hydration and supplement overrides
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from .archetypes import (
    ActivityLevel, AgeGroup, DietaryPreference, ExperienceLevel,
    GoalArchetype, HealthCondition, SessionLength, Sex,
    Somatotype, TrainingEnvironment,
)


# --------------------------------------------------------------------------- #
# Training split                                                              #
# --------------------------------------------------------------------------- #
@dataclass
class TrainingSplit:
    strength_pct: float
    hypertrophy_pct: float
    cardio_pct: float
    mobility_pct: float


def training_split(goal: GoalArchetype, experience: ExperienceLevel,
                   health: List[HealthCondition]) -> TrainingSplit:
    base = {
        GoalArchetype.FAT_LOSS:            (0.20, 0.40, 0.35, 0.05),
        GoalArchetype.MUSCLE_GAIN:         (0.40, 0.45, 0.10, 0.05),
        GoalArchetype.RECOMPOSITION:       (0.35, 0.45, 0.15, 0.05),
        GoalArchetype.STRENGTH:            (0.70, 0.20, 0.05, 0.05),
        GoalArchetype.ENDURANCE:           (0.15, 0.15, 0.65, 0.05),
        GoalArchetype.ATHLETIC_PERFORMANCE:(0.40, 0.25, 0.30, 0.05),
        GoalArchetype.GENERAL_HEALTH:      (0.25, 0.30, 0.35, 0.10),
        GoalArchetype.REHABILITATION:      (0.20, 0.30, 0.20, 0.30),
    }[goal]
    s, h, c, m = base
    # Experience modifier: beginners benefit from more conditioning
    if experience in (ExperienceLevel.NOVICE, ExperienceLevel.BEGINNER):
        c += 0.05; h -= 0.03; s -= 0.02
    # Health modifier
    if HealthCondition.CARDIO_LIMITED in health:
        c = max(0.10, c - 0.20); h += 0.15
    if HealthCondition.JOINT_ISSUES_KNEE in health:
        s = max(0.10, s - 0.10); h += 0.05; m += 0.05
    # Renormalise to 1.0
    tot = s + h + c + m
    return TrainingSplit(
        strength_pct=round(s/tot, 2),
        hypertrophy_pct=round(h/tot, 2),
        cardio_pct=round(c/tot, 2),
        mobility_pct=round(m/tot, 2),
    )


# --------------------------------------------------------------------------- #
# Volume                                                                      #
# --------------------------------------------------------------------------- #
@dataclass
class WeeklyVolume:
    total_sets: int
    per_muscle_group: Dict[str, int]
    rationale: str


def weekly_volume(
    goal: GoalArchetype, experience: ExperienceLevel,
    days_per_week: int, age_group: AgeGroup,
) -> WeeklyVolume:
    """Working sets per muscle group per week.

    Reference ranges (synthesised from Renaissance Periodisation,
    Mike Israetel, Stronger By Science):
        Maintenance : 6-8
        Hypertrophy : 10-14
        Strength    : 6-10
        Fat-loss    : 8-12
        Recomp      : 10-12
        Endurance   : 4-6
        General     : 6-8
        Rehab       : 4-6
    """
    # Base sets/muscle/week
    base_per_group = {
        GoalArchetype.FAT_LOSS: 10,
        GoalArchetype.MUSCLE_GAIN: 14,
        GoalArchetype.RECOMPOSITION: 12,
        GoalArchetype.STRENGTH: 8,
        GoalArchetype.ENDURANCE: 5,
        GoalArchetype.ATHLETIC_PERFORMANCE: 10,
        GoalArchetype.GENERAL_HEALTH: 7,
        GoalArchetype.REHABILITATION: 5,
    }[goal]

    # Experience modifier
    exp_factor = {
        ExperienceLevel.NOVICE: 0.6,
        ExperienceLevel.BEGINNER: 0.8,
        ExperienceLevel.INTERMEDIATE: 1.0,
        ExperienceLevel.ADVANCED: 1.15,
        ExperienceLevel.ELITE: 1.25,
    }[experience]

    # Age modifier — seniors need slightly less volume per session but
    # more frequency to manage recovery
    age_factor = {
        AgeGroup.YOUTH: 1.0,
        AgeGroup.YOUNG_ADULT: 1.05,
        AgeGroup.ADULT: 1.0,
        AgeGroup.MIDDLE: 0.95,
        AgeGroup.SENIOR: 0.85,
        AgeGroup.ELDER: 0.75,
    }[age_group]

    sets = round(base_per_group * exp_factor * age_factor)
    # 7 major muscle groups: chest, back, shoulders, quads, hams, glutes, calves
    groups = {
        "chest": sets, "back": sets, "shoulders": sets,
        "quads": sets, "hamstrings": sets, "glutes": sets,
        "calves": max(4, sets - 4),
        "arms": max(6, sets - 4),
        "core": 6,
    }
    total = sum(groups.values())
    return WeeklyVolume(
        total_sets=total,
        per_muscle_group=groups,
        rationale=(
            f"{sets} sets per major group based on goal={goal.value}, "
            f"experience={experience.value}, age={age_group.value}."
        ),
    )


# --------------------------------------------------------------------------- #
# Intensity                                                                   #
# --------------------------------------------------------------------------- #
@dataclass
class IntensityScheme:
    primary_reps: str
    primary_rpe: float
    accessory_reps: str
    accessory_rpe: float
    rationale: str


def intensity_scheme(goal: GoalArchetype, experience: ExperienceLevel,
                     health: List[HealthCondition]) -> IntensityScheme:
    base = {
        GoalArchetype.FAT_LOSS: ("10-15", 7.5, "12-20", 8.0),
        GoalArchetype.MUSCLE_GAIN: ("6-12", 8.0, "10-15", 8.5),
        GoalArchetype.RECOMPOSITION: ("6-12", 8.0, "10-15", 8.0),
        GoalArchetype.STRENGTH: ("3-6", 8.5, "6-10", 8.0),
        GoalArchetype.ENDURANCE: ("12-20", 7.0, "15-25", 7.5),
        GoalArchetype.ATHLETIC_PERFORMANCE: ("4-8", 8.0, "8-12", 8.0),
        GoalArchetype.GENERAL_HEALTH: ("8-12", 7.5, "10-15", 7.5),
        GoalArchetype.REHABILITATION: ("8-12", 6.5, "10-15", 7.0),
    }[goal]

    p_reps, p_rpe, a_reps, a_rpe = base
    if experience == ExperienceLevel.NOVICE:
        p_rpe = min(p_rpe, 7.0); a_rpe = min(a_rpe, 7.5)
    if HealthCondition.HYPERTENSION in health:
        p_rpe = min(p_rpe, 7.0); a_rpe = min(a_rpe, 7.5)
    return IntensityScheme(
        primary_reps=p_reps, primary_rpe=round(p_rpe, 1),
        accessory_reps=a_reps, accessory_rpe=round(a_rpe, 1),
        rationale=f"RPE scaled by goal={goal.value}, experience={experience.value}.",
    )


# --------------------------------------------------------------------------- #
# Exercise selection rules                                                    #
# --------------------------------------------------------------------------- #
@dataclass
class ExerciseRule:
    """A rule that include/exclude/substitute exercises."""
    include: List[str]
    exclude: List[str]
    substitute_map: Dict[str, List[str]]


def exercise_selection(
    goal: GoalArchetype,
    environment: TrainingEnvironment,
    equipment: List[str],
    health: List[HealthCondition],
    age_group: AgeGroup,
) -> ExerciseRule:
    """Output a rule-set that the exercise library can apply."""
    include: List[str] = []
    exclude: List[str] = []
    subs: Dict[str, List[str]] = {}

    # Universal pull / push / legs / core patterns
    include.extend(["horizontal_push", "vertical_pull", "hinge",
                    "squat", "carry", "core"])

    # Goal specifics
    if goal in (GoalArchetype.STRENGTH, GoalArchetype.ATHLETIC_PERFORMANCE):
        include.extend(["barbell_squat", "deadlift", "bench_press",
                        "overhead_press", "row"])
    if goal in (GoalArchetype.MUSCLE_GAIN, GoalArchetype.RECOMPOSITION):
        include.extend(["incline_press", "lat_pulldown", "leg_curl",
                        "lateral_raise", "triceps_extension"])
    if goal in (GoalArchetype.FAT_LOSS, GoalArchetype.GENERAL_HEALTH):
        include.extend(["kettlebell_swing", "row_machine", "circuit_pattern"])
    if goal in (GoalArchetype.ENDURANCE, GoalArchetype.ATHLETIC_PERFORMANCE):
        include.extend(["interval_pattern", "tempo_run"])

    # Environment restrictions
    if environment in (TrainingEnvironment.HOME_BODYWEIGHT,
                       TrainingEnvironment.OUTDOOR):
        for lift in ["barbell_squat", "deadlift", "bench_press", "overhead_press"]:
            subs[lift] = ["bodyweight_squat", "hinge_pattern",
                          "push_up", "pike_push_up"]
    if environment == TrainingEnvironment.HOME_MINIMAL:
        subs["barbell_squat"] = ["goblet_squat", "dumbbell_squat"]
        subs["deadlift"]      = ["dumbbell_rdl", "single_leg_rdl"]
        subs["bench_press"]   = ["dumbbell_bench", "floor_press"]
        subs["overhead_press"]= ["dumbbell_press", "landmine_press"]

    # Equipment gaps
    if "barbell" not in equipment:
        for lift in ["barbell_squat", "deadlift", "bench_press",
                     "overhead_press", "row"]:
            subs.setdefault(lift, [])

    # Health restrictions
    if HealthCondition.JOINT_ISSUES_KNEE in health:
        subs["squat"] = ["box_squat", "leg_press", "split_squat"]
        subs["barbell_squat"] = ["belt_squat", "hack_squat"]
        exclude.append("pistol_squat")
    if HealthCondition.JOINT_ISSUES_SHOULDER in health:
        subs["overhead_press"] = ["landmine_press", "neutral_press"]
        subs["bench_press"] = ["floor_press", "neutral_grip_db_press"]
        exclude.extend(["behind_neck_press", "upright_row"])
    if HealthCondition.LOWER_BACK in health:
        subs["deadlift"] = ["trap_bar_dl", "rdl_light", "back_extension"]
        exclude.append("conventional_deadlift")
    if HealthCondition.CARDIO_LIMITED in health:
        subs["interval_pattern"] = ["low_intensity_walk"]
        exclude.extend(["sprint", "burpee"])
    if HealthCondition.PREGNANCY in health:
        exclude.extend(["supine_work", "valsalva_loads", "high_impact"])
    if HealthCondition.POSTPARTUM in health and age_group != AgeGroup.ELDER:
        subs["core"] = ["diaphragmatic_breathing", "pelvic_floor_activation"]
        exclude.extend(["sit_up", "heavy_ab_wheel"])

    return ExerciseRule(
        include=sorted(set(include)),
        exclude=sorted(set(exclude)),
        substitute_map={k: sorted(set(v)) for k, v in subs.items()},
    )


# --------------------------------------------------------------------------- #
# Periodisation                                                               #
# --------------------------------------------------------------------------- #
@dataclass
class Periodisation:
    scheme: str
    cycle_weeks: int
    deload_every: int
    description: str


def periodisation(goal: GoalArchetype, experience: ExperienceLevel) -> Periodisation:
    if experience in (ExperienceLevel.NOVICE, ExperienceLevel.BEGINNER):
        return Periodisation(
            scheme="Linear Progression",
            cycle_weeks=8, deload_every=4,
            description=(
                "Add 2.5–5 kg or 1–2 reps per session until stall; "
                "then mini-deload or small reset."
            ),
        )
    if goal == GoalArchetype.STRENGTH:
        return Periodisation(
            scheme="5/3/1 (Wendler)",
            cycle_weeks=4, deload_every=4,
            description="3-week wave + 1-week deload; assistance by category.",
        )
    if goal == GoalArchetype.MUSCLE_GAIN:
        return Periodisation(
            scheme="Daily Undulating Periodisation (DUP)",
            cycle_weeks=6, deload_every=6,
            description="Rep target rotates day-to-day within the week.",
        )
    if goal == GoalArchetype.ENDURANCE:
        return Periodisation(
            scheme="Block Periodisation",
            cycle_weeks=12, deload_every=4,
            description="Base → Build → Peak blocks; deload each transition.",
        )
    return Periodisation(
        scheme="Linear with RPE Cap",
        cycle_weeks=6, deload_every=6,
        description="Add load if RPE cap not reached; deload every 6 weeks.",
    )


# --------------------------------------------------------------------------- #
# Session density                                                             #
# --------------------------------------------------------------------------- #
@dataclass
class SessionDensity:
    work_seconds: int
    rest_seconds: int
    density: str


def session_density(goal: GoalArchetype, session: SessionLength) -> SessionDensity:
    base = {
        GoalArchetype.FAT_LOSS: (30, 15),
        GoalArchetype.MUSCLE_GAIN: (45, 90),
        GoalArchetype.RECOMPOSITION: (45, 75),
        GoalArchetype.STRENGTH: (60, 180),
        GoalArchetype.ENDURANCE: (180, 60),
        GoalArchetype.ATHLETIC_PERFORMANCE: (45, 90),
        GoalArchetype.GENERAL_HEALTH: (40, 60),
        GoalArchetype.REHABILITATION: (30, 60),
    }[goal]
    w, r = base
    if session == SessionLength.EXPRESS_30:
        # Supersets to compress
        r = max(15, r - 30)
        return SessionDensity(w, r, "supersets + circuits")
    if session == SessionLength.SHORT_45:
        r = max(15, r - 15)
    if session == SessionLength.EXTENDED_90:
        r = r + 30
    return SessionDensity(w, r, "standard density")


# --------------------------------------------------------------------------- #
# Progression                                                                 #
# --------------------------------------------------------------------------- #
@dataclass
class ProgressionRule:
    primary: str
    accessory: str
    rule: str


def progression_rule(goal: GoalArchetype, experience: ExperienceLevel,
                     health: List[HealthCondition]) -> ProgressionRule:
    if experience in (ExperienceLevel.NOVICE, ExperienceLevel.BEGINNER):
        return ProgressionRule(
            primary="Add reps each session; add load when top of rep range.",
            accessory="Add 1 rep/set/week.",
            rule="Linear, weekly; resets after 3 stalls.",
        )
    if goal == GoalArchetype.STRENGTH:
        return ProgressionRule(
            primary="Wave-load: 3×5, 3×3, 1×5, deload.",
            accessory="Pump work RPE 8; chase rep PRs.",
            rule="Top-set + back-off volume.",
        )
    if HealthCondition.HYPERTENSION in health:
        return ProgressionRule(
            primary="Slow RPE climb, never above 7.",
            accessory="Rep-range progression only.",
            rule="Sub-maximal, no 1RM testing.",
        )
    return ProgressionRule(
        primary="Double-progression: hit top of rep range, then add load.",
        accessory="Rep-range progression with weekly target.",
        rule="Add load in 2.5-kg increments when reps capped.",
    )


# --------------------------------------------------------------------------- #
# Macro / diet overrides for medical conditions                                #
# --------------------------------------------------------------------------- #
def macro_overrides(health: List[HealthCondition]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if HealthCondition.TYPE_2_DIABETES in health or \
       HealthCondition.PRE_DIABETES in health:
        out["carbs"]    = "moderate, low-glycaemic; cluster around training"
        out["fibre"]    = "30-40 g/day minimum"
        out["meal_freq"]= "3 meals + 1 snack to flatten glucose curve"
    if HealthCondition.HYPERTENSION in health:
        out["sodium"]   = "< 2300 mg/day"
        out["potassium"]= "3500+ mg/day from whole foods"
    if HealthCondition.HIGH_CHOLESTEROL in health:
        out["saturated_fat"] = "< 7% kcal"
        out["fibre"]         = "≥ 30 g/day, with soluble fibre"
    if HealthCondition.PCOS in health:
        out["protein"]   = "≥ 1.8 g/kg"
        out["glycaemic"] = "low-GI, anti-inflammatory"
    if HealthCondition.IBS in health or HealthCondition.CELIAC in health:
        out["fodmap"]    = "low-FODMAP / gluten-free substitutions"
    if HealthCondition.PREGNANCY in health:
        out["folate"]    = "≥ 600 mcg"
        out["iron"]      = "27 mg with vit C co-factor"
    if HealthCondition.POSTPARTUM in health:
        out["protein"]   = "≥ 1.8 g/kg to support recovery"
        out["omega3"]    = "≥ 250 mg DHA+EPA"
    return out


# --------------------------------------------------------------------------- #
# Cuisine selection                                                           #
# --------------------------------------------------------------------------- #
def cuisine_pick(prefs: List[str], diet: DietaryPreference) -> List[str]:
    """Pick 2-3 cuisines that suit preferences + dietary pattern.

    Order respects user preference: their first-listed cuisine comes
    first so the recommender anchors on it.
    """
    if not prefs:
        if diet == DietaryPreference.MEDITERRANEAN:
            return ["mediterranean"]
        if diet == DietaryPreference.KETO:
            return ["mediterranean", "american"]
        return ["american", "mediterranean"]
    # Preserve user order; build a list of distinct cuisines
    out = []
    seen = set()
    for c in prefs:
        if c in seen:
            continue
        out.append(c)
        seen.add(c)
    if not out:
        out = ["american", "mediterranean"]
    return out[:3]


# --------------------------------------------------------------------------- #
# Supplement recommendations                                                  #
# --------------------------------------------------------------------------- #
@dataclass
class SupplementStack:
    foundational: List[Tuple[str, str, str]]   # (name, dose, rationale)
    goal_specific: List[Tuple[str, str, str]]
    conditional: List[Tuple[str, str, str]]


def supplement_stack(goal: GoalArchetype, sex: Sex,
                     health: List[HealthCondition]) -> SupplementStack:
    found = [
        ("Vitamin D", "1000-2000 IU/day", "Most adults deficient; supports bone + immune."),
        ("Omega-3", "1-2 g EPA+DHA/day", "Anti-inflammatory, cardiovascular health."),
        ("Magnesium", "200-400 mg/day", "Sleep, muscle function, glycaemic control."),
        ("Protein powder", "as needed", "Convenience to hit protein target."),
    ]
    if sex == Sex.FEMALE:
        found.append(("Iron", "test-first; supplement if low", "Pre-menopausal common deficiency."))
    if HealthCondition.LOWER_BACK in health or \
       HealthCondition.JOINT_ISSUES_KNEE in health:
        found.append(("Collagen peptides", "10-15 g/day", "Connective-tissue support."))

    goal_sp: List[Tuple[str, str, str]] = []
    if goal in (GoalArchetype.MUSCLE_GAIN, GoalArchetype.STRENGTH,
                GoalArchetype.RECOMPOSITION, GoalArchetype.ATHLETIC_PERFORMANCE):
        goal_sp.append(("Creatine monohydrate", "5 g/day", "Most evidenced performance aid."))
    if goal == GoalArchetype.ENDURANCE:
        goal_sp.append(("Sodium bicarbonate", "300 mg/kg pre-race", "Buffering for high-intensity efforts."))

    conditional: List[Tuple[str, str, str]] = []
    if HealthCondition.TYPE_2_DIABETES in health:
        conditional.append(("Berberine", "500 mg 2-3x/day", "Adjunct glycaemic control."))
    if HealthCondition.HYPERTENSION in health:
        conditional.append(("Potassium citrate", "as advised", "Counter sodium load."))

    return SupplementStack(foundational=found,
                           goal_specific=goal_sp,
                           conditional=conditional)
