"""
exercise_plans.py
=================

Structured exercise library organised by movement pattern. Each
exercise records equipment, primary muscle group, regression and
progression variants, and concise form cues. The recommender uses
these records together with the decision-tree output to build
week-by-week training plans.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Exercise:
    name: str
    pattern: str              # horizontal_push, vertical_pull, hinge, ...
    primary_muscle: str       # chest, back, quads, ...
    secondary_muscles: List[str] = field(default_factory=list)
    equipment: List[str] = field(default_factory=list)
    difficulty: int = 2       # 1 easy → 5 hard
    regression: Optional[str] = None
    progression: Optional[str] = None
    cues: List[str] = field(default_factory=list)
    contraindications: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


EXERCISE_LIBRARY: Dict[str, Exercise] = {
    # -------------- HINGE / PULL --------------
    "barbell_deadlift": Exercise(
        name="Conventional deadlift",
        pattern="hinge", primary_muscle="back",
        secondary_muscles=["hamstrings", "glutes", "traps"],
        equipment=["barbell"], difficulty=4,
        regression="trap_bar_dl", progression="deficit_deadlift",
        cues=["Bar over mid-foot", "Brace", "Push the floor away",
              "Hinge until bar below knees, then extend hips"],
        contraindications=["lower_back"],
    ),
    "trap_bar_dl": Exercise(
        name="Trap-bar deadlift",
        pattern="hinge", primary_muscle="back",
        secondary_muscles=["hamstrings", "glutes", "quads"],
        equipment=["trap_bar"], difficulty=3,
        regression="dumbbell_rdl", progression="barbell_deadlift",
        cues=["Neutral grip", "Brace", "Drive hips through"],
    ),
    "dumbbell_rdl": Exercise(
        name="Dumbbell Romanian deadlift",
        pattern="hinge", primary_muscle="hamstrings",
        secondary_muscles=["glutes", "back"],
        equipment=["dumbbells"], difficulty=2,
        regression="bodyweight_rdl", progression="barbell_rdl",
        cues=["Soft knees", "Hinge at hips", "Dumbbells skim legs"],
    ),
    "barbell_rdl": Exercise(
        name="Barbell Romanian deadlift",
        pattern="hinge", primary_muscle="hamstrings",
        secondary_muscles=["glutes", "back"],
        equipment=["barbell"], difficulty=3,
        regression="dumbbell_rdl", progression="deficit_rdl",
        cues=["Slight knee bend", "Bar travels close to thigh",
              "Stop when hamstring stretch limits"],
    ),
    "kettlebell_swing": Exercise(
        name="Kettlebell swing",
        pattern="hinge", primary_muscle="glutes",
        secondary_muscles=["hamstrings", "back"],
        equipment=["kettlebell"], difficulty=2,
        regression="deadlift_pattern", progression="snatch",
        cues=["Hip hinge", "Bell floats", "Glute squeeze at top"],
    ),
    "pullup": Exercise(
        name="Pull-up",
        pattern="vertical_pull", primary_muscle="back",
        secondary_muscles=["biceps", "core"],
        equipment=["pullup_bar"], difficulty=4,
        regression="band_pullup", progression="weighted_pullup",
        cues=["Dead hang start", "Chest to bar", "No kipping"],
    ),
    "band_pullup": Exercise(
        name="Band-assisted pull-up",
        pattern="vertical_pull", primary_muscle="back",
        secondary_muscles=["biceps", "core"],
        equipment=["bands", "pullup_bar"], difficulty=2,
        regression="negative_pullup", progression="pullup",
        cues=["Loop band over bar", "Control descent"],
    ),
    "lat_pulldown": Exercise(
        name="Lat pulldown",
        pattern="vertical_pull", primary_muscle="back",
        secondary_muscles=["biceps"],
        equipment=["machine"], difficulty=1,
        regression="band_pulldown", progression="pullup",
        cues=["Slight back angle", "Pull elbows down"],
    ),
    "barbell_row": Exercise(
        name="Bent-over barbell row",
        pattern="horizontal_pull", primary_muscle="back",
        secondary_muscles=["biceps", "core"],
        equipment=["barbell"], difficulty=3,
        regression="dumbbell_row", progression="pendlay_row",
        cues=["Hip hinge ~45°", "Pull to lower ribs"],
    ),
    "dumbbell_row": Exercise(
        name="Single-arm dumbbell row",
        pattern="horizontal_pull", primary_muscle="back",
        secondary_muscles=["biceps"],
        equipment=["dumbbells", "bench"], difficulty=1,
        regression="chest_supported_machine_row",
        progression="barbell_row",
        cues=["Hand under shoulder", "Drive elbow back"],
    ),

    # -------------- SQUAT / LEGS --------------
    "barbell_squat": Exercise(
        name="Back squat",
        pattern="squat", primary_muscle="quads",
        secondary_muscles=["glutes", "core"],
        equipment=["barbell"], difficulty=4,
        regression="goblet_squat", progression="front_squat",
        cues=["Brace", "Knees track toes", "Depth = hip crease below knee"],
    ),
    "goblet_squat": Exercise(
        name="Goblet squat",
        pattern="squat", primary_muscle="quads",
        secondary_muscles=["glutes", "core"],
        equipment=["dumbbells", "kettlebells"], difficulty=1,
        regression="bodyweight_squat", progression="barbell_squat",
        cues=["Elbows inside knees at bottom"],
    ),
    "bodyweight_squat": Exercise(
        name="Bodyweight squat",
        pattern="squat", primary_muscle="quads",
        secondary_muscles=["glutes"],
        equipment=[], difficulty=1,
        regression="box_squat_assisted", progression="goblet_squat",
        cues=["Sit back", "Knees out"],
    ),
    "front_squat": Exercise(
        name="Front squat",
        pattern="squat", primary_muscle="quads",
        secondary_muscles=["core", "glutes"],
        equipment=["barbell"], difficulty=4,
        regression="barbell_squat", progression="zercher_squat",
        cues=["Elbows up", "Upright torso"],
    ),
    "split_squat": Exercise(
        name="Bulgarian split squat",
        pattern="squat", primary_muscle="quads",
        secondary_muscles=["glutes"],
        equipment=["dumbbells"], difficulty=2,
        regression="split_squat_bw", progression="barbell_squat",
        cues=["Front foot loaded", "Knee tracks toe"],
    ),
    "leg_press": Exercise(
        name="Leg press",
        pattern="squat", primary_muscle="quads",
        secondary_muscles=["glutes"],
        equipment=["machine"], difficulty=1,
        regression="bodyweight_squat", progression="barbell_squat",
        cues=["Lower back stays in contact", "Knees out"],
    ),
    "walking_lunge": Exercise(
        name="Walking lunge",
        pattern="squat", primary_muscle="quads",
        secondary_muscles=["glutes", "hamstrings"],
        equipment=["dumbbells"], difficulty=2,
        regression="reverse_lunge_bw", progression="barbell_walking_lunge",
        cues=["Step long", "Drive through front heel"],
    ),
    "leg_curl": Exercise(
        name="Lying leg curl",
        pattern="hamstring", primary_muscle="hamstrings",
        equipment=["machine"], difficulty=1,
        regression="sliding_leg_curl", progression="nordic_curl",
        cues=["Hips down", "Full ROM"],
    ),
    "hip_thrust": Exercise(
        name="Hip thrust",
        pattern="hinge", primary_muscle="glutes",
        secondary_muscles=["hamstrings"],
        equipment=["barbell", "bench"], difficulty=2,
        regression="glute_bridge", progression="single_leg_hip_thrust",
        cues=["Chin tucked", "Drive heels", "Squeeze at top"],
    ),

    # -------------- PUSH --------------
    "bench_press": Exercise(
        name="Barbell bench press",
        pattern="horizontal_push", primary_muscle="chest",
        secondary_muscles=["triceps", "shoulders"],
        equipment=["barbell", "bench"], difficulty=3,
        regression="dumbbell_bench", progression="close_grip_bench",
        cues=["Shoulder blades retracted", "Bar to lower chest", "Drive feet"],
    ),
    "incline_bench": Exercise(
        name="Incline dumbbell press",
        pattern="horizontal_push", primary_muscle="chest",
        secondary_muscles=["shoulders", "triceps"],
        equipment=["dumbbells", "bench"], difficulty=2,
        regression="push_up", progression="incline_barbell_press",
        cues=["30° incline", "Elbows ~45° from torso"],
    ),
    "dumbbell_bench": Exercise(
        name="Dumbbell bench press",
        pattern="horizontal_push", primary_muscle="chest",
        secondary_muscles=["triceps", "shoulders"],
        equipment=["dumbbells", "bench"], difficulty=2,
        regression="push_up", progression="barbell_bench_press",
        cues=["Lower to chest level", "Drive up and in"],
    ),
    "push_up": Exercise(
        name="Push-up",
        pattern="horizontal_push", primary_muscle="chest",
        secondary_muscles=["triceps", "core"],
        equipment=[], difficulty=1,
        regression="incline_push_up", progression="diamond_push_up",
        cues=["Body line", "Elbows ~45°", "Full ROM"],
    ),
    "overhead_press": Exercise(
        name="Standing overhead press",
        pattern="vertical_push", primary_muscle="shoulders",
        secondary_muscles=["triceps", "core"],
        equipment=["barbell"], difficulty=3,
        regression="dumbbell_press", progression="push_press",
        cues=["Glutes tight", "Bar over mid-foot", "Press & shrug"],
    ),
    "dumbbell_press": Exercise(
        name="Standing dumbbell press",
        pattern="vertical_push", primary_muscle="shoulders",
        secondary_muscles=["triceps"],
        equipment=["dumbbells"], difficulty=2,
        regression="seated_db_press", progression="barbell_press",
        cues=["Neutral grip at top", "Don't flare"],
    ),
    "pike_push_up": Exercise(
        name="Pike push-up",
        pattern="vertical_push", primary_muscle="shoulders",
        secondary_muscles=["triceps"],
        equipment=[], difficulty=2,
        regression="incline_pike", progression="handstand_push_up",
        cues=["Hips up", "Head between hands"],
    ),
    "lateral_raise": Exercise(
        name="Dumbbell lateral raise",
        pattern="isolation", primary_muscle="shoulders",
        equipment=["dumbbells"], difficulty=1,
        regression="band_lateral", progression="cable_lateral",
        cues=["Lead with elbows", "Stop at shoulder height"],
    ),

    # -------------- ARMS --------------
    "barbell_curl": Exercise(
        name="Barbell curl",
        pattern="isolation", primary_muscle="biceps",
        equipment=["barbell"], difficulty=2,
        regression="db_curl", progression="close_grip_curl",
        cues=["Elbows pinned", "Full ROM"],
    ),
    "triceps_pushdown": Exercise(
        name="Cable triceps pushdown",
        pattern="isolation", primary_muscle="triceps",
        equipment=["machine"], difficulty=1,
        regression="band_pushdown", progression="overhead_triceps_ext",
        cues=["Elbows pinned", "Lock out"],
    ),

    # -------------- CORE / CARRY --------------
    "plank": Exercise(
        name="Plank",
        pattern="core", primary_muscle="core",
        equipment=[], difficulty=1,
        regression="knee_plank", progression="ab_wheel",
        cues=["Squeeze glutes", "Tuck chin", "Ribs down"],
    ),
    "pallof_press": Exercise(
        name="Pallof press",
        pattern="core", primary_muscle="core",
        equipment=["bands", "machine"], difficulty=2,
        regression="dead_bug", progression="half_kneeling_pallof",
        cues=["Resist rotation", "Press out slowly"],
    ),
    "farmer_carry": Exercise(
        name="Farmer carry",
        pattern="carry", primary_muscle="core",
        secondary_muscles=["traps", "forearms"],
        equipment=["dumbbells", "kettlebells"], difficulty=1,
        regression="short_carry", progression="loaded_carry_long",
        cues=["Tall posture", "Don't lean"],
    ),

    # -------------- CARDIO --------------
    "zone2_walk": Exercise(
        name="Zone-2 walk",
        pattern="cardio", primary_muscle="cardio",
        equipment=[], difficulty=1,
        cues=["Nasal breathing", "Slight sweat", "Can hold conversation"],
    ),
    "interval_run": Exercise(
        name="Interval run",
        pattern="cardio", primary_muscle="cardio",
        equipment=[], difficulty=3,
        cues=["Warm up 10 min", "5×3 min hard / 2 min easy", "Cool down 5 min"],
        tags=["endurance", "fat_loss"],
    ),
    "row_machine": Exercise(
        name="Rower intervals",
        pattern="cardio", primary_muscle="cardio",
        secondary_muscles=["back", "legs"],
        equipment=["cardio_machine"], difficulty=2,
        cues=["Legs-back-arms; arms-back-legs", "Stroke rate 22-26 spm"],
    ),
}


# --------------------------------------------------------------------------- #
# Plan builders                                                               #
# --------------------------------------------------------------------------- #
def list_by_pattern(pattern: str) -> List[Exercise]:
    return [e for e in EXERCISE_LIBRARY.values() if e.pattern == pattern]


def list_by_muscle(muscle: str) -> List[Exercise]:
    return [e for e in EXERCISE_LIBRARY.values()
            if e.primary_muscle == muscle or muscle in e.secondary_muscles]


def pick_exercise(pattern: str, environment, equipment: List[str],
                  difficulty_max: int = 4) -> Optional[Exercise]:
    """Pick the best exercise for a movement pattern given environment
    and equipment. Returns None if no compatible exercise found.
    """
    candidates = [e for e in EXERCISE_LIBRARY.values()
                  if e.pattern == pattern
                  and e.difficulty <= difficulty_max]
    # Equipment match: must be subset of available
    candidates = [e for e in candidates
                  if all(eq in equipment or eq == "" for eq in e.equipment)
                  or e.equipment == []]
    if not candidates:
        # Drop equipment requirement, keep bodyweight options
        candidates = [e for e in EXERCISE_LIBRARY.values()
                      if e.pattern == pattern and e.difficulty <= difficulty_max]
    if not candidates:
        return None
    # Prefer harder exercises when equipment is available
    candidates.sort(key=lambda e: (-e.difficulty, len(e.equipment)))
    return candidates[0]


def build_session(
    goal, environment, equipment: List[str], health: List[str],
    session_minutes: int, difficulty_max: int = 4,
    patterns: Optional[List[str]] = None,
) -> List[Exercise]:
    """Build one training session: 4-7 exercises balanced across patterns.
    Ensures each exercise is unique within a session.
    """
    if patterns is None:
        patterns = ["horizontal_push", "vertical_pull", "squat",
                    "hinge", "vertical_push", "horizontal_pull", "core"]
    selected: List[Exercise] = []
    seen = set()
    for pat in patterns:
        ex = pick_exercise(pat, environment, equipment, difficulty_max)
        if ex and ex.name not in seen:
            selected.append(ex)
            seen.add(ex.name)
        if len(selected) >= 7:
            break
    return selected


def weekly_split(
    goal, experience, days_per_week: int, environment, equipment: List[str],
    health: List[str],
) -> Dict[str, List[Exercise]]:
    """Return a dict mapping weekday -> list of exercises for that day.

    Common splits:
        3 days : Full Body (Mon/Wed/Fri)
        4 days : Upper/Lower (Mon/Tue/Thu/Fri)
        5 days : Push/Pull/Legs (Mon-Fri)
        6 days : PPL x2
    """
    plan: Dict[str, List[Exercise]] = {}

    def fb():
        return build_session(goal, environment, equipment, health, 60)

    def _build(patterns):
        exs, seen = [], set()
        for pat in patterns:
            e = pick_exercise(pat, environment, equipment, 4)
            if e and e.name not in seen:
                exs.append(e); seen.add(e.name)
        return exs

    def upper():    return _build(["horizontal_push","horizontal_pull",
                                    "vertical_push","vertical_pull",
                                    "isolation","core"])
    def lower():    return _build(["squat","hinge","hinge","carry","core"])
    def push_day(): return _build(["horizontal_push","vertical_push",
                                    "horizontal_pull","isolation","core"])
    def pull_day(): return _build(["horizontal_pull","vertical_pull",
                                    "horizontal_push","isolation","core"])
    def leg_day():  return _build(["squat","hinge","squat","carry","core"])

    if days_per_week <= 3:
        days = ["Monday", "Wednesday", "Friday"][:days_per_week]
        for d in days:
            plan[d] = fb()
    elif days_per_week == 4:
        plan["Monday"]    = upper()
        plan["Tuesday"]   = lower()
        plan["Thursday"]  = upper()
        plan["Friday"]    = lower()
    elif days_per_week == 5:
        plan["Monday"]    = push_day()
        plan["Tuesday"]   = pull_day()
        plan["Wednesday"] = leg_day()
        plan["Thursday"]  = push_day()
        plan["Friday"]    = pull_day()
    else:  # 6+
        plan["Monday"]    = push_day()
        plan["Tuesday"]   = pull_day()
        plan["Wednesday"] = leg_day()
        plan["Thursday"]  = push_day()
        plan["Friday"]    = pull_day()
        plan["Saturday"]  = leg_day()
    return plan
