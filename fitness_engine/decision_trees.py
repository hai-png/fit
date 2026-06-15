"""
decision_trees.py
=================

Decision logic that maps a client profile to concrete plan parameters,
grounded in the RippedBody / Muscle & Strength Training Pyramid
methodology.

Key sources: rippedbody.com/how-to-build-training-programs/
  • Step 1: Adherence → frequency / split choice
  • Step 2: Volume, Intensity, Frequency → sets, reps, RIR
  • Step 3: Progression → progression scheme by experience
  • Step 4: Exercise selection → based on environment/equipment
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from .archetypes import (
    ExperienceLevel, GoalArchetype, SessionLength, Somatotype,
    TrainingEnvironment,
)


# --------------------------------------------------------------------------- #
# Training split                                                              #
# --------------------------------------------------------------------------- #
@dataclass
class TrainingSplit:
    name: str
    days: List[str]       # day labels with session type
    description: str


def training_split(
    goal: GoalArchetype, experience: ExperienceLevel,
    days_per_week: int,
) -> TrainingSplit:
    """Choose a split based on days/week (RippedBody Frequency Matrix).

    Simplified to the most common, proven setups:
      2 days : Full Body A/B
      3 days : Full Body A/B/C
      4 days : Upper / Lower (A/B)
      5 days : Upper Push / Upper Pull / Lower (variant)
      6 days : Push/Pull/Legs × 2
    """
    if days_per_week <= 2:
        return TrainingSplit(
            name="Full Body 2-day",
            days=["Full Body A", "Full Body B"],
            description=(
                "Two full-body sessions hitting every muscle group. "
                "Ideal for beginners or time-constrained schedules. "
                "Keep each session under 60 min."
            ),
        )
    if days_per_week == 3:
        return TrainingSplit(
            name="Full Body 3-day",
            days=["Full Body A", "Full Body B", "Full Body C"],
            description=(
                "Three full-body sessions per week. The RippedBody default "
                "for most people — balances stimulus and recovery."
            ),
        )
    if days_per_week == 4:
        return TrainingSplit(
            name="Upper / Lower",
            days=["Upper A", "Lower A", "Upper B", "Lower B"],
            description=(
                "Four-day upper/lower split. Each muscle group is hit twice "
                "per week. Great for intermediate trainees chasing hypertrophy."
            ),
        )
    if days_per_week == 5:
        return TrainingSplit(
            name="Upper Push / Upper Pull / Legs",
            days=["Push", "Pull", "Legs", "Upper Push", "Upper Pull"],
            description=(
                "Five-day split alternating push/pull/legs. Higher frequency "
                "for advanced trainees who can recover adequately."
            ),
        )
    # 6+
    return TrainingSplit(
        name="Push / Pull / Legs × 2",
        days=["Push A", "Pull A", "Legs A", "Push B", "Pull B", "Legs B"],
        description=(
            "Six-day PPL split. High volume and frequency — only for advanced "
            "trainees with excellent recovery capacity."
        ),
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
    days_per_week: int,
) -> WeeklyVolume:
    """Sets per muscle group per week.

    RippedBody Pyramid guidelines:
      Practical range: 10-20 sets/muscle/wk for hypertrophy.
      Beginners start lower (6-10) and build up.
      Cutting: reduce volume ~20-30% from maintenance.
    """
    # Base sets per major muscle group per week
    if goal == GoalArchetype.STRENGTH:
        base = {
            ExperienceLevel.BEGINNER: 8,
            ExperienceLevel.INTERMEDIATE: 12,
            ExperienceLevel.ADVANCED: 16,
        }[experience]
    elif goal == GoalArchetype.FAT_LOSS:
        base = {
            ExperienceLevel.BEGINNER: 8,
            ExperienceLevel.INTERMEDIATE: 10,
            ExperienceLevel.ADVANCED: 12,
        }[experience]
    else:  # muscle_gain, recomp, general_health
        base = {
            ExperienceLevel.BEGINNER: 10,
            ExperienceLevel.INTERMEDIATE: 14,
            ExperienceLevel.ADVANCED: 18,
        }[experience]

    groups = {
        "chest": base,
        "back": base + 2,
        "shoulders": max(6, base - 2),
        "quads": base,
        "hamstrings": max(6, base - 2),
        "glutes": max(4, base - 4),
        "calves": max(4, base - 6),
        "arms": max(6, base - 4),
        "core": 6,
    }
    total = sum(groups.values())
    return WeeklyVolume(
        total_sets=total,
        per_muscle_group=groups,
        rationale=(
            f"{base} sets/major group based on goal={goal.value}, "
            f"experience={experience.value}. "
            f"RippedBody practical range: 10-20 sets/muscle/wk."
        ),
    )


# --------------------------------------------------------------------------- #
# Intensity                                                                   #
# --------------------------------------------------------------------------- #
@dataclass
class IntensityScheme:
    primary_reps: str
    primary_rir: float       # Reps in Reserve
    accessory_reps: str
    accessory_rir: float
    rationale: str


def intensity_scheme(
    goal: GoalArchetype, experience: ExperienceLevel,
) -> IntensityScheme:
    """Intensity (RIR) guidelines from the Training Pyramid.

    RIR = Reps in Reserve (how many more reps you could have done).
    RippedBody RIR guidelines:
      4-6 reps/set → 4-0 RIR
      6-8 reps/set → 3-0 RIR
      8-12 reps/set → 2-0 RIR
      >12 reps/set → 1-0 RIR
    """
    if goal == GoalArchetype.STRENGTH:
        reps, rir = "3-6", 2.0
        acc_reps, acc_rir = "6-10", 2.0
    elif goal == GoalArchetype.FAT_LOSS:
        reps, rir = "6-12", 2.0
        acc_reps, acc_rir = "10-15", 1.0
    elif goal == GoalArchetype.MUSCLE_GAIN:
        reps, rir = "6-12", 2.0
        acc_reps, acc_rir = "8-15", 1.0
    else:  # recomp, general_health
        reps, rir = "8-12", 2.0
        acc_reps, acc_rir = "10-15", 2.0

    # Beginners stay further from failure
    if experience == ExperienceLevel.BEGINNER:
        rir = max(rir, 3.0)
        acc_rir = max(acc_rir, 3.0)

    return IntensityScheme(
        primary_reps=reps, primary_rir=rir,
        accessory_reps=acc_reps, accessory_rir=acc_rir,
        rationale=(
            f"RIR-based intensity. Goal={goal.value}, "
            f"experience={experience.value}. "
            f"Beginners stay 3+ RIR; advanced push closer to failure."
        ),
    )


# --------------------------------------------------------------------------- #
# Exercise selection rules                                                    #
# --------------------------------------------------------------------------- #
@dataclass
class ExerciseRule:
    """Include/exclude/substitute directives for exercise selection."""
    include: List[str]
    exclude: List[str]
    substitute_map: Dict[str, List[str]]


def exercise_selection(
    goal: GoalArchetype, environment: TrainingEnvironment,
) -> ExerciseRule:
    """Generate exercise selection rules based on environment + goal.

    Equipment mapping:
      home_bodyweight → bodyweight only
      home_gym        → dumbbells, bands, bench, pullup_bar, kettlebells
      gym_full        → everything (barbell, rack, machines, cables)
    """
    include: List[str] = []
    exclude: List[str] = []
    subs: Dict[str, List[str]] = {}

    # Universal compound patterns
    include.extend([
        "horizontal_push", "vertical_pull", "hinge",
        "squat", "carry", "core",
    ])

    # Goal-specific emphasis
    if goal in (GoalArchetype.STRENGTH,):
        include.extend(["barbell_squat", "deadlift", "bench_press",
                        "overhead_press"])
    if goal in (GoalArchetype.MUSCLE_GAIN, GoalArchetype.RECOMPOSITION):
        include.extend(["incline_press", "lat_pulldown", "leg_curl",
                        "lateral_raise"])

    # Environment-based substitutions
    if environment == TrainingEnvironment.HOME_BODYWEIGHT:
        subs = {
            "barbell_squat": ["bodyweight_squat", "split_squat_bw"],
            "deadlift": ["bodyweight_rdl", "bodyweight_good_morning"],
            "bench_press": ["push_up", "incline_push_up"],
            "overhead_press": ["pike_push_up"],
            "barbell_row": ["inverted_row"],
            "lat_pulldown": ["inverted_row", "band_pulldown"],
        }
    elif environment == TrainingEnvironment.HOME_GYM:
        subs = {
            "barbell_squat": ["goblet_squat", "dumbbell_squat"],
            "deadlift": ["dumbbell_rdl", "single_leg_rdl"],
            "bench_press": ["dumbbell_bench", "floor_press"],
            "overhead_press": ["dumbbell_press"],
        }
    # gym_full → no substitutions needed

    return ExerciseRule(
        include=sorted(set(include)),
        exclude=sorted(set(exclude)),
        substitute_map={k: sorted(set(v)) for k, v in subs.items()},
    )


# --------------------------------------------------------------------------- #
# Progression                                                                 #
# --------------------------------------------------------------------------- #
@dataclass
class ProgressionRule:
    primary: str
    accessory: str
    rule: str


def progression_rule(
    goal: GoalArchetype, experience: ExperienceLevel,
) -> ProgressionRule:
    """Progression scheme by experience (RippedBody Pyramid).

    Beginners: linear progression — add weight/reps each session.
    Intermediate: double progression — hit top of rep range, then add load.
    Advanced: periodised — wave loading, RPE-based auto-regulation.
    """
    if experience == ExperienceLevel.BEGINNER:
        return ProgressionRule(
            primary="Add reps or load each session until you stall.",
            accessory="Add 1 rep per set per week.",
            rule="Linear progression. When you hit the top of the rep range "
                 "for all sets, increase load by 2.5 kg.",
        )
    if experience == ExperienceLevel.INTERMEDIATE:
        return ProgressionRule(
            primary="Double progression: hit top of rep range on all sets, "
                    "then add 2.5 kg.",
            accessory="Rep-range progression with a weekly target.",
            rule="Add load in small increments when the top of the rep range "
                 "is consistently achieved.",
        )
    # Advanced
    return ProgressionRule(
        primary="Wave loading / RPE-based auto-regulation.",
        accessory="Chase rep PRs on accessories; vary load by daily readiness.",
        rule="Periodise intensity. Use RIR caps and deload every 4-6 weeks.",
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
    """Rest periods by goal (RippedBody Pyramid Step 5).

    Strength: 3-5 min rest (180-300s)
    Hypertrophy: 1.5-3 min rest (90-180s)
    Fat loss: 60-90s rest (circuit/density style)
    """
    base = {
        GoalArchetype.STRENGTH: (60, 180),
        GoalArchetype.MUSCLE_GAIN: (45, 120),
        GoalArchetype.RECOMPOSITION: (45, 90),
        GoalArchetype.FAT_LOSS: (40, 60),
        GoalArchetype.GENERAL_HEALTH: (45, 90),
    }[goal]
    w, r = base

    if session == SessionLength.EXPRESS_30:
        r = max(30, r - 30)
        return SessionDensity(w, r, "supersets / circuits")
    if session == SessionLength.SHORT_45:
        r = max(45, r - 15)
    if session == SessionLength.EXTENDED_90:
        r = r + 30
    return SessionDensity(w, r, "standard density")


# --------------------------------------------------------------------------- #
# Periodisation                                                               #
# --------------------------------------------------------------------------- #
@dataclass
class Periodisation:
    scheme: str
    cycle_weeks: int
    deload_every: int
    description: str


def periodisation(
    goal: GoalArchetype, experience: ExperienceLevel,
) -> Periodisation:
    if experience == ExperienceLevel.BEGINNER:
        return Periodisation(
            scheme="Linear Progression",
            cycle_weeks=8, deload_every=6,
            description=(
                "Add load or reps each session. Deload (reduce volume ~50%) "
                "every 6 weeks or when progress stalls."
            ),
        )
    if experience == ExperienceLevel.INTERMEDIATE:
        return Periodisation(
            scheme="Double Progression",
            cycle_weeks=8, deload_every=5,
            description=(
                "Progress within a rep range, then add load. "
                "Deload every 5 weeks."
            ),
        )
    return Periodisation(
        scheme="Periodised / Auto-regulated",
        cycle_weeks=12, deload_every=4,
        description=(
            "Wave loading or RPE-based blocks. Deload every 4 weeks. "
            "Adjust intensity based on daily readiness."
        ),
    )


# --------------------------------------------------------------------------- #
# Cuisine selection                                                           #
# --------------------------------------------------------------------------- #
def cuisine_pick(prefs: List[str]) -> List[str]:
    """Pick cuisines for meal rotation.

    If the user added a traditional cuisine preference, it comes first.
    Otherwise we default to American + Mediterranean.
    """
    if not prefs or prefs == ["none"]:
        return ["american", "mediterranean"]
    out = []
    for c in prefs:
        if c and c != "none" and c not in out:
            out.append(c)
    if not out:
        out = ["american", "mediterranean"]
    return out[:3]


# --------------------------------------------------------------------------- #
# Supplement recommendations                                                  #
# --------------------------------------------------------------------------- #
@dataclass
class SupplementStack:
    foundational: List[Tuple[str, str, str]]
    goal_specific: List[Tuple[str, str, str]]
    conditional: List[Tuple[str, str, str]]


def supplement_stack(
    goal: GoalArchetype, diet_pref,
) -> SupplementStack:
    """Evidence-based supplement recommendations.

    RippedBody stance: supplements are the least important layer (bottom
    of the pyramid). Most people don't need them, but a few are
    well-supported.
    """
    from .archetypes import DietaryPreference

    found: List[Tuple[str, str, str]] = []
    goal_sp: List[Tuple[str, str, str]] = []

    # Vegan-specific foundational supplements
    if diet_pref == DietaryPreference.VEGAN:
        found.append(("Vitamin B12", "1000 mcg, 2-3×/week",
                       "Vegans cannot get B12 from plant foods. Essential."))
        found.append(("Vitamin D3", "1000-2000 IU/day",
                       "Most adults are deficient; supports bone + immune."))
        found.append(("Algae omega-3 (EPA/DHA)", "250-500 mg/day",
                       "Vegan alternative to fish oil for EPA/DHA."))
        found.append(("Creatine monohydrate", "5 g/day",
                       "Not found in plant foods; boosts training performance."))
    else:
        found.append(("Vitamin D3", "1000-2000 IU/day",
                       "Most adults are deficient; supports bone + immune."))
        found.append(("Omega-3 (EPA/DHA)", "1-2 g/day",
                       "Anti-inflammatory, cardiovascular support."))

    # Goal-specific
    if goal in (GoalArchetype.MUSCLE_GAIN, GoalArchetype.STRENGTH,
                GoalArchetype.RECOMPOSITION):
        goal_sp.append(("Creatine monohydrate", "5 g/day",
                         "Most evidenced performance supplement."))
    if goal == GoalArchetype.MUSCLE_GAIN:
        goal_sp.append(("Whey protein", "as needed",
                         "Convenience to hit protein targets."))
    if diet_pref == DietaryPreference.VEGAN and goal != GoalArchetype.MUSCLE_GAIN:
        goal_sp.append(("Vegan protein powder", "as needed",
                         "Convenience to hit protein targets."))

    return SupplementStack(
        foundational=found,
        goal_specific=goal_sp,
        conditional=[],
    )
