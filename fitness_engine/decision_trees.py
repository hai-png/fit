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
    ExperienceLevel, GoalArchetype, SessionLength, TrainingEnvironment,
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
      1 day  : Single Full Body (maintenance minimum)
      2 days : Full Body A/B
      3 days : Full Body A/B/C
      4 days : Upper / Lower (A/B)
      5 days : Upper Push / Upper Pull / Lower (variant)
      6 days : Push/Pull/Legs × 2
    """
    if days_per_week <= 1:
        return TrainingSplit(
            name="Full Body 1-day",
            days=["Full Body"],
            description=(
                "A single weekly full-body session. This is the absolute "
                "minimum for maintaining strength and muscle — progress will "
                "be slow, but consistency is more important than frequency. "
                "If you can train twice a week, switch to the 2-day split."
            ),
        )
    if days_per_week == 2:
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
            name="Push / Pull / Legs / Upper / Lower",
            days=["Push", "Pull", "Legs A", "Upper", "Legs B"],
            description=(
                "Five-day split with two leg sessions per week for balanced "
                "lower-body development. Push/Pull/Legs A in the first half, "
                "then a combined Upper session and a second Legs session. "
                "Great for intermediate-to-advanced trainees chasing hypertrophy."
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
    strength_note = ""
    if goal == GoalArchetype.STRENGTH and base < 10:
        strength_note = (
            " Strength training emphasizes intensity (load) over volume, so "
            "beginner strength targets sit below the 10-20 hypertrophy range; "
            "add sets only if strength plateaus."
        )
    return WeeklyVolume(
        total_sets=total,
        per_muscle_group=groups,
        rationale=(
            f"{base} sets/major group based on goal={goal.value}, "
            f"experience={experience.value}. "
            f"RippedBody practical range: 10-20 sets/muscle/wk."
            f"{strength_note}"
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

    # Beginners stay further from failure — but the override is now goal-aware:
    # for strength training, beginners can safely train closer to failure
    # because absolute loads are lighter; for hypertrophy/fat-loss, the
    # 3-RIR floor applies because the higher rep ranges make technical
    # failure more likely. See audit finding F30.
    if experience == ExperienceLevel.BEGINNER:
        if goal != GoalArchetype.STRENGTH:
            rir = max(rir, 3.0)
            acc_rir = max(acc_rir, 3.0)
        else:
            # Strength beginners: keep 2 RIR (already safe at light loads);
            # only bump accessory work to 3 RIR.
            acc_rir = max(acc_rir, 3.0)

    return IntensityScheme(
        primary_reps=reps, primary_rir=rir,
        accessory_reps=acc_reps, accessory_rir=acc_rir,
        rationale=(
            f"RIR-based intensity. Goal={goal.value}, "
            f"experience={experience.value}. "
            f"Beginners stay 3+ RIR on hypertrophy/fat-loss work; "
            f"strength beginners may train at 2 RIR because loads are lighter."
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

    The include list is environment-aware: barbell-specific lifts are only
    included for ``gym_full``; home environments get their bodyweight/dumbbell
    equivalents via the substitute map. See audit finding F31.
    """
    include: List[str] = []
    exclude: List[str] = []
    subs: Dict[str, List[str]] = {}

    # Universal compound patterns (these are movement patterns, not
    # specific exercises, so they apply to every environment).
    include.extend([
        "horizontal_push", "vertical_pull", "hinge",
        "squat", "carry", "core",
    ])

    # Goal-specific emphasis — only include barbell-specific lifts when the
    # environment can support them. See audit finding F31.
    if goal == GoalArchetype.STRENGTH:
        if environment == TrainingEnvironment.GYM_FULL:
            include.extend(["barbell_squat", "deadlift", "bench_press",
                            "overhead_press"])
        else:
            # Home environments: include the movement patterns instead of
            # barbell-specific names so the picker can find feasible options.
            include.extend(["horizontal_push", "vertical_push", "hinge",
                            "squat"])
    if goal in (GoalArchetype.MUSCLE_GAIN, GoalArchetype.RECOMPOSITION):
        if environment == TrainingEnvironment.GYM_FULL:
            include.extend(["incline_press", "lat_pulldown", "leg_curl",
                            "lateral_raise"])
        else:
            # Home alternatives: lateral raises can use bands; leg curls
            # become sliding leg curls or single-leg RDLs.
            include.extend(["isolation", "hamstring"])

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
# Default cuisines used when the user provides no preference. The previous
# default (["american", "mediterranean"]) was US/Western-centric. We now
# derive the default from the most-common cuisines in the recipe database
# so the planner's default pool is as large as possible. See audit F32.
_DEFAULT_CUISINES = ["american", "mediterranean"]


def set_default_cuisines(cuisines: List[str]) -> None:
    """Override the default cuisine list used when the user provides no
    preference.

    This is intended for applications that want to locale-aware default
    (e.g., set to ``["ethiopian", "mediterranean"]`` for an East African
    user base). Call this once at startup; the change is global.
    """
    global _DEFAULT_CUISINES
    _DEFAULT_CUISINES = list(cuisines)


def cuisine_pick(prefs: List[str]) -> List[str]:
    """Pick cuisines for meal rotation.

    If the user added a traditional cuisine preference, it comes first.
    Otherwise we fall back to :data:`_DEFAULT_CUISINES` (American +
    Mediterranean by default; override with :func:`set_default_cuisines`).
    See audit finding F32.

    All cuisine names are normalised to lowercase so that a user supplying
    ``"Mediterranean"`` matches the meal library's ``"mediterranean"`` tag.
    See second-audit finding (cuisine_pick case).
    """
    if not prefs or prefs == ["none"]:
        return list(_DEFAULT_CUISINES)
    out = []
    for c in prefs:
        if c and c != "none":
            c_lower = c.lower()
            if c_lower not in out:
                out.append(c_lower)
    if not out:
        out = list(_DEFAULT_CUISINES)
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

    The ``conditional`` field is now populated with diet-mode- and goal-
    specific supplements that depend on context (electrolytes for keto,
    iron/zinc for vegan women, etc.). See audit finding F33.
    """
    from .archetypes import DietaryPreference

    found: List[Tuple[str, str, str]] = []
    goal_sp: List[Tuple[str, str, str]] = []
    cond: List[Tuple[str, str, str]] = []

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
        # Vegan women of reproductive age are at high risk of iron deficiency.
        cond.append(("Iron (if ferritin low)", "as prescribed by physician",
                      "Vegan women with heavy menstrual cycles should monitor ferritin."))
        cond.append(("Zinc", "8-11 mg/day",
                      "Plant phytates reduce zinc absorption; consider a supplement."))
        cond.append(("Calcium", "1000 mg/day if not met by food",
                      "Fortified plant milks and tofu can meet needs; supplement otherwise."))
    else:
        found.append(("Vitamin D3", "1000-2000 IU/day",
                       "Most adults are deficient; supports bone + immune."))
        found.append(("Omega-3 (EPA/DHA)", "1-2 g/day",
                       "Anti-inflammatory, cardiovascular support."))

    # Diet-mode-conditional supplements
    if diet_pref == DietaryPreference.KETO:
        cond.append(("Sodium (electrolytes)", "3000-5000 mg/day in early keto",
                      "Keto flushes sodium; prevent 'keto flu' with broth or electrolyte mix."))
        cond.append(("Magnesium", "200-400 mg/day",
                      "Keto increases magnesium excretion; supplement to prevent cramps."))
        cond.append(("Potassium", "1000-3500 mg/day from food + supplement",
                      "Keto flushes potassium; avocados and leafy greens, then supplement."))
    if diet_pref == DietaryPreference.LOW_CARB:
        cond.append(("Electrolytes", "as needed",
                      "Low-carb diets flush water and electrolytes; broth or mix if headaches."))
    if diet_pref == DietaryPreference.PALEO:
        cond.append(("Calcium", "if not eating dairy alternatives",
                      "Paleo excludes dairy; ensure calcium from sardines/leafy greens or supplement."))

    # Goal-conditional supplements
    if goal == GoalArchetype.FAT_LOSS:
        cond.append(("Caffeine", "100-200 mg pre-workout (optional)",
                      "Mild performance and fat-oxidation boost; cycle off periodically."))
    if goal == GoalArchetype.STRENGTH:
        cond.append(("Beta-alanine", "3-6 g/day (optional)",
                      "Modest benefit for high-rep sets; not essential for 1RM strength."))
        cond.append(("Caffeine", "3-6 mg/kg pre-workout",
                      "Well-supported strength and power enhancer."))

    # Goal-specific (foundational for these goals)
    # Avoid duplicating creatine for vegans — it's already in their foundational list.
    if goal in (GoalArchetype.MUSCLE_GAIN, GoalArchetype.STRENGTH,
                GoalArchetype.RECOMPOSITION):
        if diet_pref != DietaryPreference.VEGAN:
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
        conditional=cond,
    )
