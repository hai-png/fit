"""
exercise_database.py
=====================

Integration module for the comprehensive exercise database scraped from
muscleandstrength.com. Provides utilities to:
- Load and filter the exercise database
- Convert between database format and engine Exercise format
- Build environment-specific exercise libraries
- Query exercises by pattern, muscle, equipment, difficulty

Usage:
    from exercise_database import ExerciseDatabase
    
    db = ExerciseDatabase()
    exercises = db.filter_by_equipment(['dumbbells', 'barbell'])
    exercises = db.filter_by_muscle('chest')
    exercises = db.filter_by_pattern('horizontal_push')
    
    # Get exercises for specific environment
    home_exercises = db.get_exercises_for_environment('home_bodyweight')
"""

from __future__ import annotations

import dataclasses as _dc
import json
import os
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

# Import engine components
from .archetypes import TrainingEnvironment


# --------------------------------------------------------------------------- #
# Data classes for scraped exercise format
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class ScrapedExercise:
    """Extended exercise representation from scraped database."""
    id: str
    name: str
    pattern: str
    primary_muscle: str
    secondary_muscles: List[str] = field(default_factory=list)
    equipment: List[str] = field(default_factory=list)
    difficulty: int = 1
    mechanics: str = "compound"
    experience_level: str = "beginner"
    views: int = 0
    comments: int = 0
    source_url: str = ""
    regression: Optional[str] = None
    progression: Optional[str] = None
    alternative_names: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    best_for: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Coerce numeric fields to int.

        JSON sources sometimes return strings ("3", "7400000") for difficulty
        and views. Without coercion, downstream filters like
        ``filter_by_difficulty`` raise TypeError on `'3' <= 3`, and
        ``generate_report`` fails to sum views. See P1 #16.

        Because the dataclass is frozen, we use ``object.__setattr__`` to
        mutate fields from ``__post_init__``.
        """
        for fld in ("difficulty", "views", "comments"):
            v = getattr(self, fld)
            if isinstance(v, str):
                try:
                    object.__setattr__(self, fld, int(v))
                except ValueError:
                    object.__setattr__(self, fld, 0)
            elif v is None:
                object.__setattr__(self, fld, 0)
        # Normalise mechanics to lowercase so case-sensitive comparisons in
        # get_compound_exercises_for_environment (line 408) work regardless of
        # how the JSON capitalised the value. See P1 #17.
        if isinstance(self.mechanics, str):
            object.__setattr__(self, "mechanics", self.mechanics.lower())
        if isinstance(self.experience_level, str):
            object.__setattr__(self, "experience_level", self.experience_level.lower())

    def to_engine_exercise(self):
        """Convert to engine Exercise format.

        P2 #30 — equipment tokens are now normalised via
        ``_normalise_external_equipment`` (imported from exercise_plans) so
        the resulting Exercise is usable by the picker. Previously a
        ScrapedExercise with ``equipment=["dumbbell"]`` (singular) produced
        an Exercise with ``equipment=["dumbbell"]``, which the picker
        rejected (expects ``"dumbbells"``).
        """
        from .exercise_plans import Exercise, _normalise_external_equipment
        normalised = _normalise_external_equipment(list(self.equipment))
        return Exercise(
            name=self.name,
            pattern=self.pattern,
            primary_muscle=self.primary_muscle,
            secondary_muscles=self.secondary_muscles,
            equipment=normalised if normalised is not None else list(self.equipment),
            difficulty=self.difficulty,
            regression=self.regression,
            progression=self.progression,
            cues=[],  # Cues not in scraped data
            contraindications=[],  # Not scraped
            tags=self.tags,
        )


# --------------------------------------------------------------------------- #
# Environment → Equipment mapping (single source of truth)
# --------------------------------------------------------------------------- #
# This mapping is intentionally kept consistent with the one in
# `exercise_plans.py`. The two files used to drift (HOME_BODYWEIGHT was []
# in one and ["bodyweight"] in the other). The contract now is:
# `HOME_BODYWEIGHT` is the empty list — exercises that require no equipment
# are picked when their `equipment` field is empty. The bodyweight token is
# NOT stored in the available list to avoid matching the comprehensive DB's
# `["bodyweight"]` equipment entries via set intersection; instead,
# `_equipment_feasible` special-cases bodyweight exercises (empty list).

# P2 (NEW-P2 #11) — ENVIRONMENT_EQUIPMENT is now imported from
# exercise_plans.py to eliminate the DRY violation. The two files used to
# have separate copies that could drift; a unit test asserts they match.
from .exercise_plans import ENVIRONMENT_EQUIPMENT  # noqa: E402


# --------------------------------------------------------------------------- #
# Equipment name mapping (scraped → engine)
# --------------------------------------------------------------------------- #

EQUIPMENT_MAPPING = {
    "barbell": "barbell",
    "dumbbell": "dumbbells",
    "dumbbells": "dumbbells",
    "cable": "machine",
    "machine": "machine",
    "bodyweight": [],
    "ez_bar": "ez_bar",
    "bands": "bands",
    "kettlebell": "kettlebell",
    "kettlebells": "kettlebell",
    "trap_bar": "trap_bar",
    "exercise_ball": "exercise_ball",
}


# --------------------------------------------------------------------------- #
# Movement pattern mapping
# --------------------------------------------------------------------------- #

PATTERN_MAPPING = {
    "horizontal_push": "horizontal_push",
    "vertical_push": "vertical_push",
    "horizontal_pull": "horizontal_pull",
    "vertical_pull": "vertical_pull",
    "squat": "squat",
    "hinge": "hinge",
    "single_leg": "single_leg",
    "isolation": "isolation",
    "core": "core",
    "carry": "carry",
    "cardio": "cardio",
}


# --------------------------------------------------------------------------- #
# Muscle group mapping
# --------------------------------------------------------------------------- #

MUSCLE_MAPPING = {
    "chest": "chest",
    "shoulders": "shoulders",
    "triceps": "triceps",
    "biceps": "biceps",
    "back": "back",
    "lats": "lats",
    "traps": "traps",
    "quads": "quads",
    "hamstrings": "hamstrings",
    "glutes": "glutes",
    "calves": "calves",
    "abs": "abs",
    "obliques": "obliques",
    "forearms": "forearms",
    "core": "core",
    "cardio": "cardio",
}


# --------------------------------------------------------------------------- #
# Exercise Database Class
# --------------------------------------------------------------------------- #

class ExerciseDatabase:
    """Comprehensive exercise database from scraped M&S data."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Load the exercise database from JSON file."""
        if db_path is None:
            db_path = Path(__file__).parent.parent / "data" / "exercises" / "comprehensive_exercise_database.json"
        
        self._load_database(db_path)
    
    def _load_database(self, path: Path):
        """Load and parse the exercise database."""
        if not os.path.exists(path):
            # Fall back to built-in exercises
            self.exercises: Dict[str, ScrapedExercise] = {}
            self._build_fallback_database()
            return
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.metadata = data.get('metadata', {})
        self.movement_patterns = data.get('movement_patterns', {})
        
        self.exercises: Dict[str, ScrapedExercise] = {}
        # Track skipped records so a single malformed entry does not abort
        # the entire load. See audit finding F41.
        skipped = 0
        for ex_data in data.get('exercises', []):
            # Defensive: if a malformed JSON has `exercises` as a dict (not a
            # list), iterating yields strings, and `ex_data.items()` raises
            # AttributeError — previously uncaught. See P1 #15.
            if not isinstance(ex_data, dict):
                print(f"[fitness_engine] warning: skipped non-dict exercise "
                      f"record: {ex_data!r}", file=sys.stderr)
                skipped += 1
                continue
            try:
                # Filter to known ScrapedExercise fields so unexpected keys
                # in the JSON do not cause a TypeError.
                field_names = {f.name for f in _dc.fields(ScrapedExercise)}
                filtered = {k: v for k, v in ex_data.items() if k in field_names}
                ex = ScrapedExercise(**filtered)
                self.exercises[ex.id] = ex
            except (TypeError, ValueError, KeyError, AttributeError) as e:
                print(f"[fitness_engine] warning: skipped malformed exercise "
                      f"record: {e}. Record: {ex_data!r}", file=sys.stderr)
                skipped += 1
        if skipped:
            print(f"[fitness_engine] exercise database load: loaded="
                  f"{len(self.exercises)}, skipped={skipped}", file=sys.stderr)

        self.filters = data.get('filter_categories', {})
    
    def _build_fallback_database(self):
        """Build minimal database from the built-in exercise library."""
        from .exercise_plans import EXERCISE_LIBRARY

        self.metadata = {"source": "built_in_fallback", "exercise_count": len(EXERCISE_LIBRARY)}
        self.movement_patterns = {}
        self.filters = {}
        self.exercises = {
            key: ScrapedExercise(
                id=key,
                name=ex.name,
                pattern=ex.pattern,
                primary_muscle=ex.primary_muscle,
                secondary_muscles=ex.secondary_muscles,
                equipment=ex.equipment,
                difficulty=ex.difficulty,
                regression=ex.regression,
                progression=ex.progression,
                tags=ex.tags,
            )
            for key, ex in EXERCISE_LIBRARY.items()
        }
    
    def get_all_exercises(self) -> List[ScrapedExercise]:
        """Return all exercises as a list."""
        return list(self.exercises.values())
    
    def get_exercise(self, exercise_id: str) -> Optional[ScrapedExercise]:
        """Get a specific exercise by ID."""
        return self.exercises.get(exercise_id)
    
    def filter_by_muscle(self, muscle: str) -> List[ScrapedExercise]:
        """Filter exercises by primary muscle group."""
        muscle = muscle.lower()
        results = []
        for ex in self.exercises.values():
            if ex.primary_muscle.lower() == muscle:
                results.append(ex)
            elif muscle in ex.secondary_muscles:
                results.append(ex)
        return results
    
    def filter_by_pattern(self, pattern: str) -> List[ScrapedExercise]:
        """Filter exercises by movement pattern."""
        pattern = pattern.lower()
        return [
            ex for ex in self.exercises.values()
            if ex.pattern.lower() == pattern
        ]
    
    def filter_by_equipment(self, equipment: List[str]) -> List[ScrapedExercise]:
        """Filter exercises by available equipment.

        An exercise is included when its required equipment list is satisfied
        by ``equipment``. Bodyweight exercises (empty equipment list OR the
        explicit ``["bodyweight"]`` token used by the comprehensive DB) are
        always available. See audit finding F39.
        """
        available = set(equipment)
        # Treat the bodyweight token as universally available
        available.add("bodyweight")
        results = []
        for ex in self.exercises.values():
            if not ex.equipment or ex.equipment == ["bodyweight"]:
                results.append(ex)
            elif all(eq in available for eq in ex.equipment):
                results.append(ex)
        return results
    
    def filter_by_difficulty(self, max_difficulty: int) -> List[ScrapedExercise]:
        """Filter exercises by maximum difficulty level."""
        return [
            ex for ex in self.exercises.values()
            if ex.difficulty <= max_difficulty
        ]
    
    def filter_by_mechanics(self, mechanics: str) -> List[ScrapedExercise]:
        """Filter exercises by mechanics (compound/isolation)."""
        mechanics = mechanics.lower()
        return [
            ex for ex in self.exercises.values()
            if ex.mechanics.lower() == mechanics
        ]
    
    def get_exercises_for_environment(
        self,
        environment: TrainingEnvironment,
        max_difficulty: int = 5,
    ) -> List[ScrapedExercise]:
        """Get all exercises suitable for a training environment."""
        available_equipment = ENVIRONMENT_EQUIPMENT.get(environment, [])
        results = []
        
        for ex in self.exercises.values():
            if ex.difficulty > max_difficulty:
                continue
            
            # Check if exercise is feasible
            if self._equipment_feasible(ex.equipment, available_equipment):
                results.append(ex)
        
        # Sort by popularity (views)
        results.sort(key=lambda x: x.views, reverse=True)
        return results
    
    def _equipment_feasible(
        self,
        required_equipment: List[str],
        available: List[str]
    ) -> bool:
        """Check if exercise equipment requirements are met.

        Treats bodyweight exercises (empty list or ``["bodyweight"]``) as
        always available regardless of environment.
        """
        if not required_equipment or required_equipment == ['bodyweight']:
            return True
        # Also treat the bodyweight token as universally available
        avail = set(available)
        avail.add('bodyweight')
        return all(eq in avail for eq in required_equipment)
    
    def search(self, query: str) -> List[ScrapedExercise]:
        """Search exercises by name, alternative names, or tags."""
        query = query.lower()
        results = []
        for ex in self.exercises.values():
            if query in ex.name.lower():
                results.append(ex)
            elif any(query in alt.lower() for alt in ex.alternative_names):
                results.append(ex)
            elif any(query in tag.lower() for tag in ex.tags):
                results.append(ex)
        return results
    
    def get_regression_chain(self, exercise_id: str) -> List[ScrapedExercise]:
        """Get the full regression chain for an exercise."""
        chain = []
        current_id = exercise_id
        
        while current_id:
            ex = self.exercises.get(current_id)
            if not ex:
                break
            chain.append(ex)
            current_id = ex.regression
        
        return chain
    
    def get_progression_chain(self, exercise_id: str) -> List[ScrapedExercise]:
        """Get the full progression chain for an exercise."""
        chain = []
        current_id = exercise_id
        
        while current_id:
            ex = self.exercises.get(current_id)
            if not ex:
                break
            chain.append(ex)
            current_id = ex.progression
        
        return chain
    
    def get_popular_exercises(
        self, 
        limit: int = 10,
        pattern: Optional[str] = None,
        muscle: Optional[str] = None,
    ) -> List[ScrapedExercise]:
        """Get most popular exercises, optionally filtered."""
        exercises = self.get_all_exercises()
        
        if pattern:
            exercises = [ex for ex in exercises if ex.pattern == pattern]
        if muscle:
            exercises = [
                ex for ex in exercises 
                if ex.primary_muscle == muscle or muscle in ex.secondary_muscles
            ]
        
        exercises.sort(key=lambda x: x.views, reverse=True)
        return exercises[:limit]
    
    def get_compound_exercises_for_environment(
        self,
        environment: TrainingEnvironment,
    ) -> Dict[str, List[ScrapedExercise]]:
        """Get compound exercises grouped by pattern for an environment."""
        exercises = self.get_exercises_for_environment(environment, max_difficulty=4)
        # Case-insensitive comparison — JSON source may have "Compound" or
        # "COMPOUND". ScrapedExercise.__post_init__ now lowercases the field,
        # but this defensive .lower() protects exercises constructed directly
        # without going through __post_init__. See P1 #17.
        exercises = [ex for ex in exercises if ex.mechanics.lower() == "compound"]

        grouped: Dict[str, List[ScrapedExercise]] = {}
        for ex in exercises:
            if ex.pattern not in grouped:
                grouped[ex.pattern] = []
            grouped[ex.pattern].append(ex)
        
        return grouped
    
    def build_session_exercises(
        self,
        environment: TrainingEnvironment,
        patterns: List[str],
        max_difficulty: int = 4,
        exclude_ids: Optional[Set[str]] = None,
    ) -> List[ScrapedExercise]:
        """Build a training session by selecting exercises for each pattern.

        P2 (NEW-P2 #5) — operates on a local copy of exclude_ids so the
        caller's set is not mutated. Previously the function added to the
        caller's set as a side effect.
        """
        # P2 (NEW-P2 #5) — copy the caller's set so we don't mutate it.
        exclude_ids = set(exclude_ids or ())
        selected = []
        
        for pattern in patterns:
            candidates = [
                ex for ex in self.exercises.values()
                if ex.pattern == pattern
                and ex.difficulty <= max_difficulty
                and self._equipment_feasible(ex.equipment, ENVIRONMENT_EQUIPMENT.get(environment, []))
                and ex.id not in exclude_ids
            ]
            
            if candidates:
                # Sort by difficulty (harder first), then by popularity
                candidates.sort(key=lambda x: (-x.difficulty, -x.views))
                selected.append(candidates[0])
                exclude_ids.add(candidates[0].id)
        
        return selected
    
    def to_engine_format(self):
        """Convert all scraped exercises to engine Exercise format.

        Returns a ``Dict[str, Exercise]`` (typed loosely here to avoid a
        circular import at type-check time). See P2 (NEW-P2 #4).
        """
        from .exercise_plans import Exercise
        engine_exercises: Dict[str, Exercise] = {}
        for ex_id, ex in self.exercises.items():
            engine_exercises[ex_id] = ex.to_engine_exercise()
        return engine_exercises
    
    def generate_report(self) -> Dict:
        """Generate a summary report of the database."""
        patterns = {}
        muscles = {}
        equipment_counts = {}
        
        for ex in self.exercises.values():
            patterns[ex.pattern] = patterns.get(ex.pattern, 0) + 1
            muscles[ex.primary_muscle] = muscles.get(ex.primary_muscle, 0) + 1
            
            for eq in ex.equipment:
                equipment_counts[eq] = equipment_counts.get(eq, 0) + 1
        
        return {
            "total_exercises": len(self.exercises),
            "patterns": patterns,
            "muscle_groups": muscles,
            "equipment_types": equipment_counts,
            "total_views": sum(ex.views for ex in self.exercises.values()),
            "total_comments": sum(ex.comments for ex in self.exercises.values()),
        }
    
    def export_to_json(self, path: str):
        """Export filtered exercises to JSON file."""
        data = {
            "metadata": self.metadata,
            "exercises": [
                {
                    "id": ex.id,
                    "name": ex.name,
                    "pattern": ex.pattern,
                    "primary_muscle": ex.primary_muscle,
                    "equipment": ex.equipment,
                    "difficulty": ex.difficulty,
                }
                for ex in self.exercises.values()
            ],
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)


# --------------------------------------------------------------------------- #
# Convenience functions
# --------------------------------------------------------------------------- #

# P2 #31 — module-level lock for thread-safe singleton init.
_get_database_lock = threading.Lock()


def get_database() -> ExerciseDatabase:
    """Get a singleton instance of the exercise database.

    P2 #31 — thread-safe via double-checked locking. Previously two threads
    calling get_database() simultaneously could both pass the hasattr check
    and both construct an ExerciseDatabase, racing on file I/O.
    """
    if hasattr(get_database, '_instance'):
        return get_database._instance
    with _get_database_lock:
        if not hasattr(get_database, '_instance'):
            get_database._instance = ExerciseDatabase()
    return get_database._instance


def get_exercises_for_goal(
    environment: TrainingEnvironment,
    goal,
    max_per_pattern: int = 2,
) -> List[ScrapedExercise]:
    """Get exercises optimized for a specific goal archetype.

    ``goal`` accepts either a ``GoalArchetype`` enum or its string value
    (e.g. ``"fat_loss"``, ``"muscle_gain"``, ``"strength"``). Strings are
    coerced to the enum; unknown values raise ``ValueError``.
    See NEW-P2 #7.
    """
    # Coerce str → GoalArchetype for type safety.
    from .archetypes import GoalArchetype
    if isinstance(goal, str):
        try:
            goal = GoalArchetype(goal)
        except ValueError:
            raise ValueError(
                f"unknown goal {goal!r}; expected one of "
                f"{[g.value for g in GoalArchetype]}"
            )
    db = get_database()
    exercises = db.get_exercises_for_environment(environment)

    # Filter by goal alignment
    if goal in (GoalArchetype.FAT_LOSS, GoalArchetype.GENERAL_HEALTH):
        # Prefer compound exercises, bodyweight-friendly
        exercises = [ex for ex in exercises if ex.mechanics.lower() == 'compound']
        exercises.sort(key=lambda x: x.difficulty)
    elif goal == GoalArchetype.MUSCLE_GAIN:
        # Prefer high-view compound exercises
        exercises.sort(key=lambda x: x.views, reverse=True)
    elif goal == GoalArchetype.STRENGTH:
        # Prefer lower difficulty compound lifts
        exercises = [ex for ex in exercises if ex.difficulty >= 3]
        exercises = [ex for ex in exercises if ex.mechanics.lower() == 'compound']

    return exercises[:max_per_pattern * 6]  # ~6 patterns × 2 exercises


# --------------------------------------------------------------------------- #
# Main execution for testing
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    db = ExerciseDatabase()
    report = db.generate_report()
    
    print("=" * 60)
    print("EXERCISE DATABASE REPORT")
    print("=" * 60)
    print(f"Total Exercises: {report['total_exercises']}")
    print(f"Total Views: {report['total_views']:,}")
    print(f"Total Comments: {report['total_comments']:,}")
    print()
    
    print("By Movement Pattern:")
    for pattern, count in sorted(report['patterns'].items(), key=lambda x: -x[1]):
        print(f"  {pattern}: {count}")
    
    print()
    print("By Muscle Group:")
    for muscle, count in sorted(report['muscle_groups'].items(), key=lambda x: -x[1]):
        print(f"  {muscle}: {count}")
    
    print()
    print("Top 10 Most Viewed Exercises:")
    for ex in db.get_popular_exercises(10):
        print(f"  {ex.name}: {ex.views:,} views")
    
    print()
    print("Sample: Chest Exercises for Home Gym:")
    chest_exercises = db.filter_by_muscle('chest')
    for ex in chest_exercises[:5]:
        print(f"  {ex.name} (Difficulty: {ex.difficulty}, Equipment: {ex.equipment})")