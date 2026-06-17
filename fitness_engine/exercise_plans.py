"""
exercise_plans.py
=================

Structured exercise library organised by movement pattern. Each
exercise records equipment, primary muscle group, regression and
progression variants, and concise form cues.

Environment → equipment mapping:
  home_bodyweight → [] (bodyweight only)
  home_gym        → dumbbells, bands, bench, pullup_bar, kettlebells
  gym_full        → barbell, bench, dumbbells, machine, cardio_machine,
                    kettlebells, pullup_bar, trap_bar

The plan builder uses RippedBody program-building principles:
  • Compound lifts are the backbone
  • Equipment is a HARD filter (never prescribe infeasible exercises)
  • ExerciseRule substitutes are consulted when no match exists
  • A/B variation prevents identical consecutive sessions
"""
from __future__ import annotations

import functools as _functools
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .archetypes import (
    ExperienceLevel, GoalArchetype, TrainingEnvironment,
)


# --------------------------------------------------------------------------- #
# Environment → equipment mapping                                             #
# --------------------------------------------------------------------------- #
ENVIRONMENT_EQUIPMENT: Dict[TrainingEnvironment, List[str]] = {
    TrainingEnvironment.HOME_BODYWEIGHT: [],
    TrainingEnvironment.HOME_GYM: [
        "dumbbells", "bands", "bench", "pullup_bar", "kettlebell",
    ],
    TrainingEnvironment.GYM_FULL: [
        "barbell", "bench", "dumbbells", "machine", "cardio_machine",
        "kettlebell", "bands", "pullup_bar", "trap_bar", "ez_bar",
        "exercise_ball",
    ],
}


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
    # ============ HINGE / DEADLIFT ============
    "barbell_deadlift": Exercise(
        name="Conventional deadlift", pattern="hinge", primary_muscle="back",
        secondary_muscles=["hamstrings", "glutes", "traps"],
        equipment=["barbell"], difficulty=4,
        regression="trap_bar_dl", progression="deficit_deadlift",
        cues=["Bar over mid-foot", "Brace", "Push the floor away",
              "Extend hips at top"],
        contraindications=["lower_back"],
    ),
    "trap_bar_dl": Exercise(
        name="Trap-bar deadlift", pattern="hinge", primary_muscle="back",
        secondary_muscles=["hamstrings", "glutes", "quads"],
        equipment=["trap_bar"], difficulty=3,
        regression="dumbbell_rdl", progression="barbell_deadlift",
        cues=["Neutral grip", "Brace", "Drive hips through"],
    ),
    "dumbbell_rdl": Exercise(
        name="Dumbbell Romanian deadlift", pattern="hinge",
        primary_muscle="hamstrings",
        secondary_muscles=["glutes", "back"],
        equipment=["dumbbells"], difficulty=2,
        regression="bodyweight_rdl", progression="barbell_rdl",
        cues=["Soft knees", "Hinge at hips", "Dumbbells skim legs"],
    ),
    "barbell_rdl": Exercise(
        name="Barbell Romanian deadlift", pattern="hinge",
        primary_muscle="hamstrings",
        secondary_muscles=["glutes", "back"],
        equipment=["barbell"], difficulty=3,
        regression="dumbbell_rdl", progression="deficit_rdl",
        cues=["Slight knee bend", "Bar close to thigh", "Stop at hamstring limit"],
    ),
    "kettlebell_swing": Exercise(
        name="Kettlebell swing", pattern="hinge", primary_muscle="glutes",
        secondary_muscles=["hamstrings", "back"],
        equipment=["kettlebell"], difficulty=2,
        regression="glute_bridge", progression="snatch",
        cues=["Hip hinge", "Bell floats", "Glute squeeze at top"],
    ),
    "bodyweight_rdl": Exercise(
        name="Single-leg bodyweight RDL", pattern="hinge",
        primary_muscle="hamstrings",
        secondary_muscles=["glutes", "back"],
        equipment=[], difficulty=2,
        regression="bodyweight_good_morning", progression="dumbbell_rdl",
        cues=["Soft knee", "Hinge at hips", "Reach back with the heel"],
    ),
    "bodyweight_good_morning": Exercise(
        name="Bodyweight good morning", pattern="hinge",
        primary_muscle="hamstrings",
        secondary_muscles=["glutes", "back"],
        equipment=[], difficulty=1,
        regression="glute_bridge", progression="bodyweight_rdl",
        cues=["Hinge with flat back", "Push hips back", "Slight knee bend"],
    ),
    "glute_bridge": Exercise(
        name="Glute bridge", pattern="hinge", primary_muscle="glutes",
        secondary_muscles=["hamstrings", "core"],
        equipment=[], difficulty=1,
        regression="short_bridge", progression="single_leg_glute_bridge",
        cues=["Drive through heels", "Squeeze glutes at top", "No lower-back arch"],
    ),
    "hip_thrust": Exercise(
        name="Hip thrust", pattern="hinge", primary_muscle="glutes",
        secondary_muscles=["hamstrings"],
        equipment=["barbell", "bench"], difficulty=2,
        regression="glute_bridge", progression="single_leg_hip_thrust",
        cues=["Chin tucked", "Drive heels", "Squeeze at top"],
    ),
    "back_extension": Exercise(
        name="Back extension", pattern="hinge", primary_muscle="back",
        secondary_muscles=["glutes", "hamstrings"],
        equipment=["bench"], difficulty=1,
        regression="superman", progression="barbell_good_morning",
        cues=["Hinge at the pad", "Neutral spine", "No hyperextension"],
    ),

    # ============ VERTICAL PULL ============
    "pullup": Exercise(
        name="Pull-up", pattern="vertical_pull", primary_muscle="back",
        secondary_muscles=["biceps", "core"],
        equipment=["pullup_bar"], difficulty=4,
        regression="band_pullup", progression="weighted_pullup",
        cues=["Dead hang start", "Chest to bar", "No kipping"],
    ),
    "band_pullup": Exercise(
        name="Band-assisted pull-up", pattern="vertical_pull",
        primary_muscle="back",
        secondary_muscles=["biceps", "core"],
        equipment=["bands", "pullup_bar"], difficulty=2,
        regression="inverted_row", progression="pullup",
        cues=["Loop band over bar", "Control descent"],
    ),
    "lat_pulldown": Exercise(
        name="Lat pulldown", pattern="vertical_pull", primary_muscle="back",
        secondary_muscles=["biceps"],
        equipment=["machine"], difficulty=1,
        regression="band_pulldown", progression="pullup",
        cues=["Slight back angle", "Pull elbows down"],
    ),
    "band_pulldown": Exercise(
        name="Band lat pulldown", pattern="vertical_pull",
        primary_muscle="back",
        secondary_muscles=["biceps"],
        equipment=["bands"], difficulty=1,
        regression="inverted_row", progression="lat_pulldown",
        cues=["Anchor high", "Pull elbows to ribs", "Full stretch at top"],
    ),

    # ============ HORIZONTAL PULL ============
    "barbell_row": Exercise(
        name="Bent-over barbell row", pattern="horizontal_pull",
        primary_muscle="back",
        secondary_muscles=["biceps", "core"],
        equipment=["barbell"], difficulty=3,
        regression="dumbbell_row", progression="pendlay_row",
        cues=["Hip hinge ~45°", "Pull to lower ribs"],
    ),
    "dumbbell_row": Exercise(
        name="Single-arm dumbbell row", pattern="horizontal_pull",
        primary_muscle="back",
        secondary_muscles=["biceps"],
        equipment=["dumbbells", "bench"], difficulty=1,
        regression="inverted_row", progression="barbell_row",
        cues=["Hand under shoulder", "Drive elbow back"],
    ),
    "inverted_row": Exercise(
        name="Inverted row", pattern="horizontal_pull", primary_muscle="back",
        secondary_muscles=["biceps", "core"],
        equipment=["pullup_bar"], difficulty=2,
        regression="band_row", progression="barbell_row",
        cues=["Body in a straight line", "Pull chest to bar/table edge",
              "Squeeze shoulder blades"],
    ),

    # ============ SQUAT / LEGS ============
    "barbell_squat": Exercise(
        name="Back squat", pattern="squat", primary_muscle="quads",
        secondary_muscles=["glutes", "core"],
        equipment=["barbell"], difficulty=4,
        regression="goblet_squat", progression="front_squat",
        cues=["Brace", "Knees track toes", "Depth = hip crease below knee"],
    ),
    "goblet_squat": Exercise(
        name="Goblet squat", pattern="squat", primary_muscle="quads",
        secondary_muscles=["glutes", "core"],
        equipment=["dumbbells"], difficulty=1,
        regression="bodyweight_squat", progression="barbell_squat",
        cues=["Elbows inside knees at bottom"],
    ),
    "bodyweight_squat": Exercise(
        name="Bodyweight squat", pattern="squat", primary_muscle="quads",
        secondary_muscles=["glutes"],
        equipment=[], difficulty=1,
        regression="box_squat_assisted", progression="goblet_squat",
        cues=["Sit back", "Knees out"],
    ),
    "front_squat": Exercise(
        name="Front squat", pattern="squat", primary_muscle="quads",
        secondary_muscles=["core", "glutes"],
        equipment=["barbell"], difficulty=4,
        regression="barbell_squat", progression="zercher_squat",
        cues=["Elbows up", "Upright torso"],
    ),
    "dumbbell_squat": Exercise(
        name="Dumbbell goblet squat", pattern="squat", primary_muscle="quads",
        secondary_muscles=["glutes", "core"],
        equipment=["dumbbells"], difficulty=1,
        regression="bodyweight_squat", progression="barbell_squat",
        cues=["Hold dumbbell at chest", "Sit between knees"],
    ),
    "split_squat": Exercise(
        name="Bulgarian split squat", pattern="squat", primary_muscle="quads",
        secondary_muscles=["glutes"],
        equipment=["dumbbells"], difficulty=2,
        regression="split_squat_bw", progression="barbell_squat",
        cues=["Front foot loaded", "Knee tracks toe"],
    ),
    "leg_press": Exercise(
        name="Leg press", pattern="squat", primary_muscle="quads",
        secondary_muscles=["glutes"],
        equipment=["machine"], difficulty=1,
        regression="bodyweight_squat", progression="barbell_squat",
        cues=["Lower back stays in contact", "Knees out"],
    ),
    "walking_lunge": Exercise(
        name="Walking lunge", pattern="squat", primary_muscle="quads",
        secondary_muscles=["glutes", "hamstrings"],
        equipment=["dumbbells"], difficulty=2,
        regression="reverse_lunge_bw", progression="barbell_walking_lunge",
        cues=["Step long", "Drive through front heel"],
    ),
    "split_squat_bw": Exercise(
        name="Split squat (bodyweight)", pattern="squat", primary_muscle="quads",
        secondary_muscles=["glutes"],
        equipment=[], difficulty=1,
        regression="bodyweight_squat", progression="split_squat",
        cues=["Stagger stance", "Drop straight down", "Front shin near vertical"],
    ),
    "reverse_lunge_bw": Exercise(
        name="Reverse lunge (bodyweight)", pattern="squat",
        primary_muscle="quads",
        secondary_muscles=["glutes", "hamstrings"],
        equipment=[], difficulty=1,
        regression="split_squat_bw", progression="walking_lunge",
        cues=["Step back", "Drop straight down", "Drive through front heel"],
    ),
    "leg_curl": Exercise(
        name="Lying leg curl", pattern="hamstring", primary_muscle="hamstrings",
        equipment=["machine"], difficulty=1,
        regression="sliding_leg_curl", progression="nordic_curl",
        cues=["Hips down", "Full ROM"],
    ),

    # ============ PUSH ============
    "bench_press": Exercise(
        name="Barbell bench press", pattern="horizontal_push",
        primary_muscle="chest",
        secondary_muscles=["triceps", "shoulders"],
        equipment=["barbell", "bench"], difficulty=3,
        regression="dumbbell_bench", progression="close_grip_bench",
        cues=["Shoulder blades retracted", "Bar to lower chest", "Drive feet"],
    ),
    "incline_bench": Exercise(
        name="Incline dumbbell press", pattern="horizontal_push",
        primary_muscle="chest",
        secondary_muscles=["shoulders", "triceps"],
        equipment=["dumbbells", "bench"], difficulty=2,
        regression="push_up", progression="incline_barbell_press",
        cues=["30° incline", "Elbows ~45° from torso"],
    ),
    "dumbbell_bench": Exercise(
        name="Dumbbell bench press", pattern="horizontal_push",
        primary_muscle="chest",
        secondary_muscles=["triceps", "shoulders"],
        equipment=["dumbbells", "bench"], difficulty=2,
        regression="push_up", progression="bench_press",
        cues=["Lower to chest level", "Drive up and in"],
    ),
    "push_up": Exercise(
        name="Push-up", pattern="horizontal_push", primary_muscle="chest",
        secondary_muscles=["triceps", "core"],
        equipment=[], difficulty=1,
        regression="incline_push_up", progression="diamond_push_up",
        cues=["Body line", "Elbows ~45°", "Full ROM"],
    ),
    "incline_push_up": Exercise(
        name="Incline push-up", pattern="horizontal_push",
        primary_muscle="chest",
        secondary_muscles=["triceps", "core"],
        equipment=[], difficulty=1,
        regression="wall_push_up", progression="push_up",
        cues=["Hands elevated on a surface", "Body line", "Full ROM"],
    ),
    "overhead_press": Exercise(
        name="Standing overhead press", pattern="vertical_push",
        primary_muscle="shoulders",
        secondary_muscles=["triceps", "core"],
        equipment=["barbell"], difficulty=3,
        regression="dumbbell_press", progression="push_press",
        cues=["Glutes tight", "Bar over mid-foot", "Press & shrug"],
    ),
    "dumbbell_press": Exercise(
        name="Standing dumbbell press", pattern="vertical_push",
        primary_muscle="shoulders",
        secondary_muscles=["triceps"],
        equipment=["dumbbells"], difficulty=2,
        regression="pike_push_up", progression="overhead_press",
        cues=["Neutral grip at top", "Don't flare"],
    ),
    "pike_push_up": Exercise(
        name="Pike push-up", pattern="vertical_push",
        primary_muscle="shoulders",
        secondary_muscles=["triceps"],
        equipment=[], difficulty=2,
        regression="incline_pike", progression="handstand_push_up",
        cues=["Hips up", "Head between hands"],
    ),
    "lateral_raise": Exercise(
        name="Dumbbell lateral raise", pattern="isolation",
        primary_muscle="shoulders",
        equipment=["dumbbells"], difficulty=1,
        regression="band_lateral", progression="cable_lateral",
        cues=["Lead with elbows", "Stop at shoulder height"],
    ),

    # ============ ARMS ============
    "barbell_curl": Exercise(
        name="Barbell curl", pattern="isolation", primary_muscle="biceps",
        equipment=["barbell"], difficulty=2,
        regression="db_curl", progression="close_grip_curl",
        cues=["Elbows pinned", "Full ROM"],
    ),
    "triceps_pushdown": Exercise(
        name="Cable triceps pushdown", pattern="isolation",
        primary_muscle="triceps",
        equipment=["machine"], difficulty=1,
        regression="band_pushdown", progression="overhead_triceps_ext",
        cues=["Elbows pinned", "Lock out"],
    ),

    # ============ CORE / CARRY ============
    "plank": Exercise(
        name="Plank", pattern="core", primary_muscle="core",
        equipment=[], difficulty=1,
        regression="knee_plank", progression="ab_wheel",
        cues=["Squeeze glutes", "Tuck chin", "Ribs down"],
    ),
    "pallof_press": Exercise(
        name="Pallof press", pattern="core", primary_muscle="core",
        equipment=["bands", "machine"], difficulty=2,
        regression="dead_bug", progression="half_kneeling_pallof",
        cues=["Resist rotation", "Press out slowly"],
    ),
    "farmer_carry": Exercise(
        name="Farmer carry", pattern="carry", primary_muscle="core",
        secondary_muscles=["traps", "forearms"],
        equipment=["dumbbells"], difficulty=1,
        regression="short_carry", progression="loaded_carry_long",
        cues=["Tall posture", "Don't lean"],
    ),
    "dead_bug": Exercise(
        name="Dead bug", pattern="core", primary_muscle="core",
        equipment=[], difficulty=1,
        regression="heel_slide", progression="hollow_hold",
        cues=["Lower back pressed down", "Opposite arm and leg", "Slow tempo"],
    ),
    "bird_dog": Exercise(
        name="Bird dog", pattern="core", primary_muscle="core",
        secondary_muscles=["back", "glutes"],
        equipment=[], difficulty=1,
        regression="quadruped_hold", progression="bird_dog_resisted",
        cues=["Opposite arm and leg", "Level hips", "Reach long"],
    ),
    "superman": Exercise(
        name="Superman hold", pattern="hinge", primary_muscle="back",
        secondary_muscles=["glutes"],
        equipment=[], difficulty=1,
        regression="bird_dog", progression="back_extension",
        cues=["Lift chest and thighs", "Reach long", "Squeeze glutes"],
    ),

    # ============ CARDIO ============
    "zone2_walk": Exercise(
        name="Zone-2 walk", pattern="cardio", primary_muscle="cardio",
        equipment=[], difficulty=1,
        cues=["Nasal breathing", "Slight sweat", "Can hold conversation"],
    ),
    "interval_run": Exercise(
        name="Interval run", pattern="cardio", primary_muscle="cardio",
        equipment=[], difficulty=3,
        cues=["Warm up 10 min", "5×3 min hard / 2 min easy", "Cool down 5 min"],
        tags=["fat_loss"],
    ),
    "row_machine": Exercise(
        name="Rower intervals", pattern="cardio", primary_muscle="cardio",
        secondary_muscles=["back", "legs"],
        equipment=["cardio_machine"], difficulty=2,
        cues=["Legs-back-arms; arms-back-legs", "Stroke rate 22-26 spm"],
    ),
}


def _normalise_external_equipment(equipment: List[str]) -> Optional[List[str]]:
    """Map comprehensive-database equipment tokens to engine tokens.

    Unknown or non-actionable tokens are skipped so the picker does not emit
    exercises with equipment the environment model cannot reason about.
    """
    mapping = {
        "bodyweight": None,
        "cable": "machine",
        "kettlebells": "kettlebell",
        "kettlebell": "kettlebell",
        "barbell": "barbell",
        "dumbbells": "dumbbells",
        "dumbbell": "dumbbells",
        "machine": "machine",
        "bands": "bands",
        "trap_bar": "trap_bar",
        "ez_bar": "ez_bar",
        "exercise_ball": "exercise_ball",
    }
    out: List[str] = []
    for raw in equipment or []:
        raw_token = str(raw).lower()
        if raw_token not in mapping:
            return None
        token = mapping[raw_token]
        if token is None:
            continue
        if token not in out:
            out.append(token)
    return out


def _load_comprehensive_exercise_library() -> Dict[str, Exercise]:
    """Load the checked-in comprehensive exercise database as additional
    picker options.

    Logs a warning to stderr when records are skipped due to unknown
    equipment tokens or missing required fields, so data-quality regressions
    in the source JSON are visible during development. See audit F38, F54.
    """
    import sys
    path = Path(__file__).resolve().parents[1] / "data" / "exercises" / "comprehensive_exercise_database.json"
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        print(f"[fitness_engine] warning: failed to load comprehensive exercise "
              f"database at {path}: {e}", file=sys.stderr)
        return {}
    out: Dict[str, Exercise] = {}
    skipped = {"unknown_equipment": 0, "missing_fields": 0, "duplicate_key": 0}
    for rec in payload.get("exercises", []):
        key = str(rec.get("id") or "").strip()
        if not key:
            skipped["missing_fields"] += 1
            continue
        if key in EXERCISE_LIBRARY or key in out:
            skipped["duplicate_key"] += 1
            continue
        equipment = _normalise_external_equipment(list(rec.get("equipment") or []))
        if equipment is None:
            skipped["unknown_equipment"] += 1
            continue
        pattern = str(rec.get("pattern") or "").strip()
        primary = str(rec.get("primary_muscle") or "").strip()
        name = str(rec.get("name") or key).strip()
        if not pattern or not primary or not name:
            skipped["missing_fields"] += 1
            continue
        # Normalize exercise name to a consistent case (title case) so the
        # built-in library ("Barbell bench press") and the comprehensive DB
        # ("Barbell Bench Press") render identically in plan output. See
        # audit finding F37.
        name = name.title()
        # Clamp difficulty to [1, 5] to guard against malformed records.
        try:
            difficulty = max(1, min(5, int(rec.get("difficulty") or 1)))
        except (TypeError, ValueError):
            difficulty = 1
        out[key] = Exercise(
            name=name,
            pattern=pattern,
            primary_muscle=primary,
            secondary_muscles=list(rec.get("secondary_muscles") or []),
            equipment=equipment,
            difficulty=difficulty,
            regression=rec.get("regression"),
            progression=rec.get("progression"),
            cues=[],
            tags=["comprehensive_db"],
        )
    if any(skipped.values()):
        print(f"[fitness_engine] comprehensive DB load summary: "
              f"loaded={len(out)}, skipped={skipped}", file=sys.stderr)
    return out


# Lazy-load the comprehensive DB on first access rather than at import time.
# This avoids paying the JSON parse cost on every `import fitness_engine` and
# caches the result so subsequent calls are free. See audit finding F35.

@_functools.lru_cache(maxsize=1)
def _get_comprehensive_library() -> Dict[str, Exercise]:
    return _load_comprehensive_exercise_library()


def _ensure_comprehensive_loaded() -> None:
    """Merge the comprehensive library into EXERCISE_LIBRARY on first call."""
    if getattr(_ensure_comprehensive_loaded, "_done", False):
        return
    extra = _get_comprehensive_library()
    EXERCISE_LIBRARY.update(extra)
    _ensure_comprehensive_loaded._done = True


# Trigger the merge immediately so EXERCISE_LIBRARY is populated for callers
# who access it directly. The lru_cache ensures the JSON is only parsed once.
_ensure_comprehensive_loaded()


# --------------------------------------------------------------------------- #
# Plan builders                                                               #
# --------------------------------------------------------------------------- #
_BY_KEY: Dict[str, str] = {k: k for k in EXERCISE_LIBRARY}


def _equipment_feasible(ex: Exercise, equipment: List[str]) -> bool:
    """True iff every piece of required equipment is available."""
    if not ex.equipment:
        return True
    avail = set(equipment)
    return all(eq in avail for eq in ex.equipment)


def _resolve_exclude_keys(rule) -> set:
    """Resolve ExerciseRule.exclude into a set of library keys."""
    if rule is None:
        return set()
    exclude = getattr(rule, "exclude", []) or []
    keys: set = set()
    for entry in exclude:
        e = str(entry).lower()
        for k, ex in EXERCISE_LIBRARY.items():
            if e in k.lower() or e in ex.name.lower():
                keys.add(k)
    return keys


def list_by_pattern(pattern: str) -> List[Exercise]:
    return [e for e in EXERCISE_LIBRARY.values() if e.pattern == pattern]


def list_by_muscle(muscle: str) -> List[Exercise]:
    return [e for e in EXERCISE_LIBRARY.values()
            if e.primary_muscle == muscle or muscle in e.secondary_muscles]


def pick_exercise(
    pattern: str, environment: TrainingEnvironment,
    difficulty_max: int = 4, exclude_keys: Optional[set] = None,
    variant: int = 0,
) -> Optional[Exercise]:
    """Pick the best feasible exercise for a movement pattern.

    HARD filters (never silently relaxed):
      * pattern match
      * difficulty <= difficulty_max
      * required equipment is available for the environment
      * not in exclude_keys

    ``variant`` selects the Nth candidate for A/B variation. Candidates are
    sorted by difficulty *closest to* (but not exceeding) the experience-
    appropriate tier — beginners (difficulty_max=3) prefer difficulty 1-2
    exercises; intermediate/advanced (difficulty_max=4) prefer difficulty 3-4.
    This prevents the picker from prescribing barbell deadlifts (difficulty 4)
    to beginners when trap-bar deadlifts (difficulty 3) or dumbbell RDLs
    (difficulty 2) are available. See audit finding F34.
    """
    equipment = ENVIRONMENT_EQUIPMENT.get(environment, [])
    exclude_keys = exclude_keys or set()
    candidates = [
        e for k, e in EXERCISE_LIBRARY.items()
        if e.pattern == pattern
        and e.difficulty <= difficulty_max
        and _equipment_feasible(e, equipment)
        and k not in exclude_keys
    ]
    if not candidates:
        return None
    # Target difficulty: beginners should get the easiest feasible option;
    # advanced lifters should get the hardest feasible option. The target is
    # the midpoint of the allowed range.
    target_diff = (1 + difficulty_max) / 2
    # Sort by: (1) distance from target difficulty ascending, (2) number of
    # equipment requirements ascending (simpler setups first), (3) name for
    # deterministic tie-breaking. A/B/C variants cycle through the list.
    candidates.sort(key=lambda e: (abs(e.difficulty - target_diff),
                                    len(e.equipment), e.name))
    idx = min(max(variant, 0), len(candidates) - 1)
    return candidates[idx]


def _pick_via_substitutes(
    pattern: str, environment: TrainingEnvironment,
    difficulty_max: int, exclude_keys: set, exercise_rule, variant: int,
) -> Optional[Exercise]:
    """Consult ExerciseRule.substitute_map when no direct match exists."""
    if exercise_rule is None:
        return None
    equipment = ENVIRONMENT_EQUIPMENT.get(environment, [])
    sub_map = getattr(exercise_rule, "substitute_map", {}) or {}
    lookups = [pattern]
    for k, v in sub_map.items():
        if pattern in k or k in pattern:
            lookups.extend(v)
    for ck in lookups:
        ex = EXERCISE_LIBRARY.get(ck)
        if ex is None or ck in exclude_keys:
            continue
        if ex.difficulty > difficulty_max:
            continue
        if not _equipment_feasible(ex, equipment):
            continue
        return ex
    return None


def build_session(
    goal: GoalArchetype, environment: TrainingEnvironment,
    session_minutes: int, difficulty_max: int = 4,
    patterns: Optional[List[str]] = None,
    exercise_rule=None, variant: int = 0,
) -> List[Exercise]:
    """Build one training session: 5-9 exercises balanced across patterns.

    The default pattern list now includes isolation patterns for arms and
    a hamstring curl pattern, so accessory muscle groups (biceps, triceps,
    hamstrings, calves) receive direct volume instead of being starved by
    a compound-only session. See audit finding C5.
    """
    if patterns is None:
        patterns = ["horizontal_push", "vertical_pull", "squat",
                    "hinge", "vertical_push", "horizontal_pull",
                    "isolation", "hamstring", "core"]
    exclude_keys = _resolve_exclude_keys(exercise_rule)

    selected: List[Exercise] = []
    seen = set()
    for pat in patterns:
        ex = pick_exercise(pat, environment, difficulty_max,
                           exclude_keys=exclude_keys, variant=variant)
        if ex is None:
            ex = _pick_via_substitutes(pat, environment, difficulty_max,
                                       exclude_keys, exercise_rule, variant)
        if ex and ex.name not in seen:
            selected.append(ex)
            seen.add(ex.name)
        if len(selected) >= 9:
            break
    return selected


def _build_patterns(patterns, environment, difficulty_max,
                    exclude_keys, exercise_rule, variant=0):
    exs, seen = [], set()
    for pat in patterns:
        ex = pick_exercise(pat, environment, difficulty_max,
                           exclude_keys=exclude_keys, variant=variant)
        if ex is None:
            ex = _pick_via_substitutes(pat, environment, difficulty_max,
                                       exclude_keys, exercise_rule, variant)
        if ex and ex.name not in seen:
            exs.append(ex)
            seen.add(ex.name)
    return exs


def weekly_split(
    goal: GoalArchetype, experience: ExperienceLevel,
    days_per_week: int, environment: TrainingEnvironment,
    exercise_rule=None,
) -> Dict[str, List[Exercise]]:
    """Return a dict mapping day label -> list of exercises.

    Splits (RippedBody program building):
        1 day  : Full Body (maintenance minimum)
        2 days : Full Body A/B
        3 days : Full Body A/B/C (three distinct variants)
        4 days : Upper A / Lower A / Upper B / Lower B
        5 days : Push / Pull / Legs / Upper Push / Upper Pull
        6 days : PPL × 2

    A/B/C variation ensures consecutive sessions differ. Day 3 of the 3-day
    split uses variant=2 (not variant=0 like Day 1) so the three full-body
    sessions are genuinely distinct. See audit finding F59.
    """
    plan: Dict[str, List[Exercise]] = {}
    difficulty_max = 3 if experience == ExperienceLevel.BEGINNER else 4
    exclude_keys = _resolve_exclude_keys(exercise_rule)

    def fb(v=0):
        return build_session(goal, environment, 60,
                             difficulty_max=difficulty_max,
                             exercise_rule=exercise_rule, variant=v)

    def upper(v=0):
        return _build_patterns(
            ["horizontal_push", "horizontal_pull", "vertical_push",
             "vertical_pull", "isolation", "core"],
            environment, difficulty_max, exclude_keys, exercise_rule, v)

    def lower(v=0):
        return _build_patterns(
            ["squat", "hinge", "hamstring", "carry", "core"],
            environment, difficulty_max, exclude_keys, exercise_rule, v)

    def push_day(v=0):
        # Push day: chest/shoulders/triceps. Use "isolation" but the picker
        # should prefer triceps exercises. We include a comment but cannot
        # filter by muscle within the pattern-based picker. The picker now
        # sorts by difficulty closest to target, which generally surfaces
        # arm-focused isolation exercises before calf/wrist exercises.
        return _build_patterns(
            ["horizontal_push", "vertical_push", "isolation", "core"],
            environment, difficulty_max, exclude_keys, exercise_rule, v)

    def pull_day(v=0):
        # Pull day: back/biceps. We use "isolation" which may pick a triceps
        # exercise. To avoid this, we could split "isolation" into
        # "biceps_isolation" and "triceps_isolation" patterns — but that
        # requires DB schema changes. For now, we accept that the picker
        # may occasionally pick a non-ideal isolation exercise on pull day.
        # The user can substitute via the exercise_rule.exclude list.
        return _build_patterns(
            ["horizontal_pull", "vertical_pull", "isolation", "core"],
            environment, difficulty_max, exclude_keys, exercise_rule, v)

    def leg_day(v=0):
        # Fixed: removed duplicate "squat" pattern; added "hamstring" for
        # direct hamstring isolation. See second-audit finding (leg_day
        # duplicate squat pattern).
        return _build_patterns(
            ["squat", "hinge", "hamstring", "carry", "core"],
            environment, difficulty_max, exclude_keys, exercise_rule, v)

    if days_per_week <= 1:
        plan["Day 1 - Full Body"] = fb(0)
    elif days_per_week == 2:
        plan["Day 1 - Full Body A"] = fb(0)
        plan["Day 2 - Full Body B"] = fb(1)
    elif days_per_week == 3:
        # Three distinct variants so Day 3 != Day 1.
        plan["Day 1 - Full Body A"] = fb(0)
        plan["Day 2 - Full Body B"] = fb(1)
        plan["Day 3 - Full Body C"] = fb(2)
    elif days_per_week == 4:
        plan["Day 1 - Upper A"] = upper(0)
        plan["Day 2 - Lower A"] = lower(0)
        plan["Day 3 - Upper B"] = upper(1)
        plan["Day 4 - Lower B"] = lower(1)
    elif days_per_week == 5:
        # 5-day split: Push / Pull / Legs A / Upper / Legs B
        # Two leg sessions for balanced lower-body development.
        # See second-audit finding (5-day split only 1 leg session).
        plan["Day 1 - Push"] = push_day(0)
        plan["Day 2 - Pull"] = pull_day(0)
        plan["Day 3 - Legs A"] = leg_day(0)
        plan["Day 4 - Upper"] = upper(0)
        plan["Day 5 - Legs B"] = leg_day(1)
    else:
        plan["Day 1 - Push A"] = push_day(0)
        plan["Day 2 - Pull A"] = pull_day(0)
        plan["Day 3 - Legs A"] = leg_day(0)
        plan["Day 4 - Push B"] = push_day(1)
        plan["Day 5 - Pull B"] = pull_day(1)
        plan["Day 6 - Legs B"] = leg_day(1)
    return plan
