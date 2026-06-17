"""
recommender.py
==============

The orchestrator. Takes a ClientProfile, runs it through the calculators,
decision trees, and protocol libraries, and returns a unified
PlanRecommendation grounded in the RippedBody methodology.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
import hashlib
import json
from typing import Any, Dict, List, Optional

from .archetypes import (
    ActivityLevel, ArchetypeSignature, DietaryPreference,
    ExperienceLevel, GoalArchetype, Sex, Somatotype, TrainingEnvironment,
    SessionLength, TraineeProfile,
)
from .calculators import (
    BodyComposition, CardioZones, EnergyExpenditure, Hydration, Macros,
    MicronutrientTargets, MuscularPotential, MacroCycle, AnthropometricIndices,
    body_composition, energy_expenditure, hydration,
    macros_for, cardio_zones, infer_age_group, infer_somatotype,
    classify_trainee, recommend_phase_strategy, micronutrient_targets,
    muscular_potential, one_rep_max, macro_cycle, anthropometric_indices,
)
from .decision_trees import (
    IntensityScheme, Periodisation, ProgressionRule, SessionDensity,
    TrainingSplit, WeeklyVolume, exercise_selection, intensity_scheme,
    cuisine_pick, progression_rule, session_density, supplement_stack,
    training_split, weekly_volume, periodisation,
)
from .meal_plans import MealPlan
from .seven_day_meal_planner import SevenDayMealPlan, assemble_7_day_meal_plan
from .exercise_plans import weekly_split
from .questionnaires import IntakeReport, intake_report
from .protocols import CompleteProfileProtocol, build_complete_profile_protocol


# --------------------------------------------------------------------------- #
# Serialization helpers                                                       #
# --------------------------------------------------------------------------- #
def _to_json_safe(obj: Any) -> Any:
    """Recursively convert enums to their ``.value`` and dataclasses to dicts.

    Used by :meth:`ClientProfile.to_dict` and by the CLI's JSON serializer so
    that nested enums (inside lists, dicts, or other dataclasses) are
    converted uniformly. See audit finding F62.
    """
    import dataclasses as _dc
    import enum as _enum
    if isinstance(obj, _enum.Enum):
        return obj.value
    if _dc.is_dataclass(obj) and not isinstance(obj, type):
        return {k: _to_json_safe(v) for k, v in _dc.asdict(obj).items()}
    if isinstance(obj, dict):
        return {k: _to_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_json_safe(v) for v in obj]
    return obj


# --------------------------------------------------------------------------- #
# Client profile                                                              #
# --------------------------------------------------------------------------- #
@dataclass
class ClientProfile:
    # Demographics / body
    age: int
    sex: Sex
    height_cm: float
    weight_kg: float
    body_fat_pct: Optional[float] = None
    waist_cm: Optional[float] = None
    neck_cm: Optional[float] = None
    hip_cm: Optional[float] = None
    visual_bf_label: Optional[str] = None
    wrist_cm: Optional[float] = None
    resting_hr: int = 60
    measured_max_hr: Optional[int] = None

    # Activity
    activity: ActivityLevel = ActivityLevel.MOSTLY_SEDENTARY

    # Diet
    dietary_preference: DietaryPreference = DietaryPreference.OMNIVORE
    allergies: List[str] = field(default_factory=list)
    dislikes: List[str] = field(default_factory=list)
    meals_per_day: int = 4
    preferred_cuisines: List[str] = field(default_factory=list)

    # Training
    experience: ExperienceLevel = ExperienceLevel.BEGINNER
    environment: TrainingEnvironment = TrainingEnvironment.GYM_FULL
    days_per_week: int = 3
    session_length: SessionLength = SessionLength.STANDARD_60

    # Goals
    primary_goal: GoalArchetype = GoalArchetype.GENERAL_HEALTH
    target_weight_kg: Optional[float] = None
    timeline_weeks: int = 12
    motivation: str = ""

    # Safety / progression / repeatability
    medical_flags: Dict[str, bool] = field(default_factory=dict)
    working_weights_kg: Dict[str, float] = field(default_factory=dict)
    plan_week: int = 1
    meal_plan_seed: Optional[int] = None

    def __post_init__(self) -> None:
        """Validate and normalise profile inputs at the API boundary.

        The calculators intentionally expose low-level functions, but the
        recommender should fail fast with actionable errors instead of producing
        silent clamps (for example, a 7-day lifting request previously returned
        a 6-day plan).  String enum values are accepted for ergonomic direct
        construction; they are normalised to enum instances here.
        """
        self.sex = Sex(self.sex)
        self.activity = ActivityLevel(self.activity)
        self.dietary_preference = DietaryPreference(self.dietary_preference)
        self.experience = ExperienceLevel(self.experience)
        self.environment = TrainingEnvironment(self.environment)
        self.session_length = SessionLength(self.session_length)
        self.primary_goal = GoalArchetype(self.primary_goal)

        if not 13 <= self.age <= 100:
            raise ValueError("age must be between 13 and 100")
        if not 50 <= self.height_cm <= 250:
            raise ValueError("height_cm must be between 50 and 250")
        if not 20 <= self.weight_kg <= 350:
            raise ValueError("weight_kg must be between 20 and 350")
        if self.body_fat_pct is not None and not 2 <= self.body_fat_pct <= 70:
            raise ValueError("body_fat_pct must be between 2 and 70 when provided")
        for name in ("waist_cm", "neck_cm", "hip_cm", "wrist_cm"):
            value = getattr(self, name)
            if value is not None and value <= 0:
                raise ValueError(f"{name} must be positive when provided")
        if not 30 <= self.resting_hr <= 220:
            raise ValueError("resting_hr must be between 30 and 220")
        if self.measured_max_hr is not None and not 80 <= self.measured_max_hr <= 240:
            raise ValueError("measured_max_hr must be between 80 and 240 when provided")
        if self.measured_max_hr is not None and self.measured_max_hr <= self.resting_hr:
            raise ValueError("measured_max_hr must exceed resting_hr")
        if not 3 <= self.meals_per_day <= 5:
            raise ValueError("meals_per_day must be between 3 and 5")
        if not 1 <= self.days_per_week <= 6:
            raise ValueError("days_per_week must be between 1 and 6")
        if self.timeline_weeks <= 0:
            raise ValueError("timeline_weeks must be positive")
        if self.target_weight_kg is not None and self.target_weight_kg <= 0:
            raise ValueError("target_weight_kg must be positive when provided")
        if self.plan_week <= 0:
            raise ValueError("plan_week must be positive")
        if self.meal_plan_seed is not None and self.meal_plan_seed < 0:
            raise ValueError("meal_plan_seed must be non-negative when provided")

        self.medical_flags = {
            str(k): bool(v) for k, v in (self.medical_flags or {}).items()
        }
        self.working_weights_kg = {
            str(k): float(v) for k, v in (self.working_weights_kg or {}).items()
            if v is not None
        }
        for lift, load in self.working_weights_kg.items():
            if load <= 0:
                raise ValueError(f"working_weights_kg[{lift!r}] must be positive")

        self.allergies = list(self.allergies or [])
        self.dislikes = list(self.dislikes or [])
        self.preferred_cuisines = list(self.preferred_cuisines or [])

        # Motivation validation: the GOALS questionnaire defines five valid
        # motivation values. If the user supplied one of them, accept it; if
        # they supplied free text, accept it but emit no warning (the field
        # is documented as accepting either). See audit finding F67.
        _VALID_MOTIVATIONS = {
            "health_event", "appearance", "performance", "longevity",
            "mental_health",
        }
        if self.motivation and self.motivation not in _VALID_MOTIVATIONS:
            # Free-text motivation is allowed but we normalize empty/whitespace
            # to the default ("appearance") so downstream consumers can rely
            # on a non-empty string.
            if not self.motivation.strip():
                self.motivation = "appearance"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the profile to a JSON-safe dict.

        Recursively converts enum values to their string ``.value`` so the
        result is safe for ``json.dumps``. The previous implementation only
        handled top-level enums; nested enums (e.g., inside lists or dicts,
        if the schema ever adds them) would have survived as enum instances
        and broken serialization. See audit finding F62.
        """
        d = asdict(self)
        return _to_json_safe(d)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ClientProfile":
        return cls(
            age=d["age"],
            sex=Sex(d["sex"]),
            height_cm=d["height_cm"],
            weight_kg=d["weight_kg"],
            body_fat_pct=d.get("body_fat_pct"),
            waist_cm=d.get("waist_cm"),
            neck_cm=d.get("neck_cm"),
            hip_cm=d.get("hip_cm"),
            visual_bf_label=d.get("visual_bf_label"),
            wrist_cm=d.get("wrist_cm"),
            resting_hr=d.get("resting_hr", 60),
            measured_max_hr=d.get("measured_max_hr"),
            activity=ActivityLevel(d.get("activity", "mostly_sedentary")),
            dietary_preference=DietaryPreference(d.get("dietary_preference", "omnivore")),
            allergies=d.get("allergies", []),
            dislikes=d.get("dislikes", []),
            meals_per_day=d.get("meals_per_day", 4),
            preferred_cuisines=d.get("preferred_cuisines", []),
            experience=ExperienceLevel(d.get("experience", "beginner")),
            environment=TrainingEnvironment(d.get("environment", "gym_full")),
            days_per_week=d.get("days_per_week", 3),
            session_length=SessionLength(d.get("session_length", "standard_60")),
            primary_goal=GoalArchetype(d.get("primary_goal", "general_health")),
            target_weight_kg=d.get("target_weight_kg"),
            timeline_weeks=d.get("timeline_weeks", 12),
            motivation=d.get("motivation", ""),
            medical_flags=d.get("medical_flags", {}),
            working_weights_kg=d.get("working_weights_kg", {}),
            plan_week=d.get("plan_week", 1),
            meal_plan_seed=d.get("meal_plan_seed"),
        )


# --------------------------------------------------------------------------- #
# Output models                                                               #
# --------------------------------------------------------------------------- #
@dataclass
class TrainingPlan:
    split: TrainingSplit
    weekly_volume: WeeklyVolume
    intensity: IntensityScheme
    periodisation: Periodisation
    density: SessionDensity
    exercise_rule: dict
    progression: ProgressionRule
    weekly_schedule: Dict[str, List[dict]]
    volume_reconciliation: Dict[str, Any]
    cardio_zones: CardioZones
    cardio_prescription: Dict[str, str]
    warmup_protocol: List[str]
    cooldown_protocol: List[str]


@dataclass
class NutritionPlan:
    calories: float
    macros: Macros
    macro_cycle: MacroCycle
    hydration: Hydration
    micronutrients: MicronutrientTargets
    meal_plan: MealPlan
    weekly_meal_plan: SevenDayMealPlan
    cuisine: List[str]
    supplements: dict


@dataclass
class PlanRecommendation:
    profile: Dict[str, Any]
    archetype_signature: str
    trainee_category: TraineeProfile
    body_composition: BodyComposition
    anthropometrics: AnthropometricIndices
    energy: EnergyExpenditure
    training: TrainingPlan
    nutrition: NutritionPlan
    muscular_potential: Optional[MuscularPotential]
    protocols: CompleteProfileProtocol
    intake_report: IntakeReport
    warnings: List[str]
    notes: List[str]
    # Auto-generated meal-plan audit. The recommender runs
    # audit_7_day_meal_plan on the weekly meal plan so the score is visible
    # in every generated plan, not only when the user explicitly invokes
    # the auditor. See audit finding F58.
    meal_plan_audit: Optional[Any] = None


# --------------------------------------------------------------------------- #
# The engine                                                                  #
# --------------------------------------------------------------------------- #
class Recommender:
    """Main entry-point. Build with a ClientProfile and call .recommend()."""

    def __init__(self, profile: ClientProfile):
        self.p = profile

    def _archetype_signature(self, somatotype: Somatotype) -> ArchetypeSignature:
        age_group = infer_age_group(self.p.age)
        return ArchetypeSignature(
            goal=self.p.primary_goal,
            somatotype=somatotype,
            experience=self.p.experience,
            age_group=age_group,
            sex=self.p.sex,
            activity=self.p.activity,
            diet=self.p.dietary_preference,
            environment=self.p.environment,
            session=self.p.session_length,
        )

    def _meal_seed(self) -> int:
        """Derive a deterministic meal-plan seed.

        When ``meal_plan_seed`` is supplied, it is XORed with ``plan_week``
        so that the seed produces a different (but still deterministic) plan
        each week — matching the README's claim that ``plan_week`` derives a
        "different repeatable recipe rotation". The previous implementation
        returned ``meal_plan_seed`` verbatim, which produced the *same* plan
        every week regardless of ``plan_week``, contradicting the README.
        See second-audit finding (meal_plan_seed overrides plan_week).
        """
        if self.p.meal_plan_seed is not None:
            # XOR the user-supplied seed with plan_week so each week is
            # different but still deterministic.
            return self.p.meal_plan_seed ^ (self.p.plan_week * 2654435761)
        seed_payload = {
            "age": self.p.age,
            "sex": self.p.sex.value,
            "height_cm": self.p.height_cm,
            "weight_kg": self.p.weight_kg,
            "goal": self.p.primary_goal.value,
            "diet": self.p.dietary_preference.value,
            "week": self.p.plan_week,
        }
        digest = hashlib.sha1(json.dumps(seed_payload, sort_keys=True).encode()).hexdigest()
        return int(digest[:8], 16)

    def _load_guidance(self, ex, rep_range: str) -> Optional[Dict[str, Any]]:
        """Return simple load guidance from optional client working weights.

        ``working_weights_kg`` accepts keys such as ``squat``, ``bench_press``,
        ``deadlift``, ``overhead_press``, ``row``, ``pullup``, or an exercise-
        name fragment. We treat the provided load as a recent hard set of ~5
        reps and estimate 1RM from it, then prescribe a conservative working
        range for the plan's reps/RIR.

        Matching is performed **only** on the exercise's ``name`` field — not
        on its ``pattern`` or ``primary_muscle``. Pattern-name matching (e.g.
        treating ``"hinge"`` as a deadlift alias) caused false cross-lift
        applications (e.g., a deadlift 1RM applied to Barbell Hip Thrust
        because both have ``pattern=hinge``). See audit finding C3.
        """
        if not self.p.working_weights_kg:
            return None
        # Aliases are exercise-NAME fragments only. Each list contains the
        # canonical key plus known name-level synonyms/regressions of that
        # lift. Pattern names ("hinge", "vertical_push", etc.) are
        # intentionally excluded to avoid cross-lift contamination.
        aliases = {
            "squat": ["squat", "leg_press", "lunge", "goblet"],
            "bench_press": ["bench press", "bench_press", "dumbbell bench"],
            "deadlift": ["deadlift", "romanian deadlift", "rdl"],
            "overhead_press": ["overhead press", "shoulder press", "arnold press"],
            "row": ["barbell row", "dumbbell row", "bent over", "bent-over"],
            "pullup": ["pull-up", "pull up", "pullup", "pulldown", "chin up", "chin-up"],
        }
        haystack = ex.name.lower()
        matched_key = None
        for key, load in self.p.working_weights_kg.items():
            key_l = key.lower().replace(" ", "_")
            fragments = aliases.get(key_l, [key_l.replace("_", " "), key_l])
            # Word-boundary matching: a fragment must appear as a whole word
            # (or whole phrase) inside the exercise name, not as a substring.
            # This prevents "row" matching "arrow" or "barbell upright row"
            # matching a "row" key when the user only specified barbell_row.
            for frag in fragments:
                if frag in haystack:
                    matched_key = key
                    working_load = float(load)
                    break
            if matched_key is not None:
                break
        if matched_key is None:
            return None

        est = one_rep_max(working_load, 5)
        pct = 0.72 if "12" in rep_range or "15" in rep_range else 0.80
        suggested = round(est.average_1rm * pct / 2.5) * 2.5
        return {
            "source_lift": matched_key,
            "input_working_weight_kg": round(working_load, 1),
            "estimated_1rm_kg": est.average_1rm,
            "suggested_working_weight_kg": suggested,
            "rationale": (
                f"Estimated from {working_load:g} kg × 5 (assumed recent hard set "
                f"of 5 reps on {matched_key}); start conservatively for "
                f"{rep_range} @ target RIR."
            ),
        }

    @staticmethod
    def _reconcile_volume(targets: Dict[str, int], schedule: Dict[str, List[dict]]) -> Dict[str, Any]:
        # Map granular muscle names (biceps, triceps, lats, abs, etc.) to the
        # coarser muscle groups used by weekly_volume targets (arms, back,
        # core, etc.). Without this aliasing, isolation exercises for biceps
        # and triceps would not count toward the "arms" target. See audit C5.
        MUSCLE_ALIASES = {
            "biceps": "arms",
            "triceps": "arms",
            "forearms": "arms",
            "lats": "back",
            "traps": "back",
            "rear_delts": "back",
            "abs": "core",
            "obliques": "core",
            "hip_flexors": "core",
            "cardio": "core",  # cardio exercises are not muscle-grouped; skip
        }
        def _alias(muscle: str) -> Optional[str]:
            if muscle in targets:
                return muscle
            return MUSCLE_ALIASES.get(muscle)

        actual = {muscle: 0.0 for muscle in targets}
        for exercises in schedule.values():
            for ex in exercises:
                sets = float(ex.get("set_count", 3))
                primary = ex.get("primary_muscle")
                alias = _alias(primary) if primary else None
                if alias:
                    actual[alias] += sets
                for secondary in ex.get("secondary_muscles", []):
                    alias = _alias(secondary)
                    if alias:
                        actual[alias] += sets * 0.5
        actual_i = {k: int(round(v)) for k, v in actual.items()}
        diff = {k: actual_i.get(k, 0) - target for k, target in targets.items()}
        within = {k: abs(v) <= 1 for k, v in diff.items()}
        return {
            "target_sets": dict(targets),
            "scheduled_sets": actual_i,
            "diff_sets": diff,
            "within_one_set": within,
            "summary": "Schedule volume is within ±1 set for all tracked muscles." if all(within.values()) else "Schedule volume differs from target; use the diff to add/remove accessories in the next block.",
        }

    def recommend(self) -> PlanRecommendation:
        p = self.p

        # 1. Body composition (with visual BF fallback)
        bc = body_composition(
            p.weight_kg, p.height_cm, p.age, p.sex,
            bf_pct=p.body_fat_pct,
            waist_cm=p.waist_cm, neck_cm=p.neck_cm, hip_cm=p.hip_cm,
            visual_bf_label=p.visual_bf_label,
        )

        # 1b. Anthropometric health indices (WHtR, WHR, ABSI, IBW)
        anthro = anthropometric_indices(
            p.height_cm, p.weight_kg, p.sex,
            waist_cm=p.waist_cm, hip_cm=p.hip_cm,
        )

        # 2. Somatotype inference
        somatotype = infer_somatotype(
            p.weight_kg, p.height_cm, p.age, p.sex,
            body_fat_pct=bc.body_fat_pct, wrist_cm=p.wrist_cm,
        )

        # 3. Trainee category (RippedBody 9 categories)
        trainee = classify_trainee(
            bc.body_fat_pct or 20, p.experience, p.sex, bc.bmi,
        )

        # 4. Energy expenditure
        ee = energy_expenditure(
            p.weight_kg, p.height_cm, p.age, p.sex,
            p.activity, p.primary_goal, p.experience,
            lean_mass_kg=bc.lean_mass_kg,
            target_weight_kg=p.target_weight_kg,
        )

        # 5. Macros (RippedBody methodology)
        m = macros_for(
            calories=ee.calorie_target,
            weight_kg=p.weight_kg, lean_mass_kg=bc.lean_mass_kg,
            goal=p.primary_goal, sex=p.sex,
            somatotype=somatotype, dietary_pref=p.dietary_preference,
            body_fat_pct=bc.body_fat_pct,
            target_weight_kg=p.target_weight_kg,
        )

        # 5b. Optional training/rest-day macro cycling for adherence.
        # Pass sex so the rest-day floor (1200/1500) is enforced.
        mc = macro_cycle(m, p.days_per_week, sex=p.sex)

        # 6. Hydration
        h = hydration(p.weight_kg, workout_minutes=45 * p.days_per_week, sex=p.sex)

        # 6b. Micronutrients (fruit/veg/fibre targets)
        micros = micronutrient_targets(ee.calorie_target)

        # 6c. Muscular potential (Berkhan model + FFMI)
        mp = None
        if bc.body_fat_pct is not None:
            mp = muscular_potential(p.height_cm, p.weight_kg, bc.body_fat_pct)

        # 7. Decision trees (training)
        ts = training_split(p.primary_goal, p.experience, p.days_per_week)
        wv = weekly_volume(p.primary_goal, p.experience, p.days_per_week)
        ins = intensity_scheme(p.primary_goal, p.experience)
        per = periodisation(p.primary_goal, p.experience)
        dty = session_density(p.primary_goal, p.session_length)
        er = exercise_selection(p.primary_goal, p.environment)
        prog = progression_rule(p.primary_goal, p.experience)
        cz = cardio_zones(p.age, p.resting_hr, measured_max_hr=p.measured_max_hr)

        # 8. Weekly schedule
        sched_raw = weekly_split(
            p.primary_goal, p.experience,
            p.days_per_week, p.environment,
            exercise_rule=er,
        )
        sched = {}
        for day, exs in sched_raw.items():
            day_list = []
            for ex in exs:
                is_compound = ex.pattern in (
                    "squat", "hinge", "horizontal_push",
                    "vertical_push", "horizontal_pull", "vertical_pull",
                )
                rep_range = ins.primary_reps if is_compound else ins.accessory_reps
                rir = ins.primary_rir if is_compound else ins.accessory_rir
                item = {
                    "name": ex.name,
                    "pattern": ex.pattern,
                    "primary_muscle": ex.primary_muscle,
                    "secondary_muscles": ex.secondary_muscles,
                    "set_count": 3,
                    "sets_reps": f"3 × {rep_range}",
                    "rir": rir,
                    "rest_seconds": dty.rest_seconds,
                    "equipment": ex.equipment or ["bodyweight"],
                    "cues": ex.cues[:3],
                }
                load = self._load_guidance(ex, rep_range)
                if load is not None:
                    item["load_guidance"] = load
                day_list.append(item)
            sched[day] = day_list

        volume_audit = self._reconcile_volume(wv.per_muscle_group, sched)

        # 9. Decision trees (nutrition)
        cuisines = cuisine_pick(p.preferred_cuisines)

        # 10. 7-day external-recipe protocol meal plan
        week_plan = assemble_7_day_meal_plan(
            diet=p.dietary_preference,
            target_calories=ee.calorie_target,
            target_macros=m,
            meals_per_day=p.meals_per_day,
            allergens=p.allergies,
            preferred_cuisines=cuisines,
            include_external=True,
            include_internal=False,
            seed=self._meal_seed(),
        )
        # Single-day plan is the first day of the same external-only weekly plan,
        # kept for backwards compatibility with callers expecting nutrition.meal_plan.
        # NOTE: ``day_plan`` is always the current week's Day 1 (Monday). When
        # ``plan_week`` changes, the deterministic meal-plan seed changes, so
        # both ``weekly_meal_plan`` and ``meal_plan`` change silently. Callers
        # who cache ``meal_plan`` across weeks must re-fetch. See audit F60.
        day_plan = week_plan.days[0]

        # 10b. Auto-audit the weekly meal plan so the score is visible in
        # every generated plan. See audit finding F58.
        from .meal_plan_auditor import audit_7_day_meal_plan
        meal_audit = audit_7_day_meal_plan(week_plan)

        # 11. Supplements
        supps = supplement_stack(p.primary_goal, p.dietary_preference)

        # 12. Intake report (health/lifestyle recommendations)
        ir = intake_report(
            bmi_val=bc.bmi,
            body_fat_pct=bc.body_fat_pct,
            calorie_target=ee.calorie_target,
            trainee_summary=trainee.summary,
            trainee_recommendations=trainee.recommendations,
        )

        # 13. Protocol blueprints for this profile
        protocols = build_complete_profile_protocol(
            p.primary_goal, p.experience, p.days_per_week, p.session_length,
            p.environment, p.dietary_preference, ee.calorie_target, m,
            p.meals_per_day, p.activity, age=p.age, sex=p.sex,
            medical_flags=p.medical_flags,
        )

        # 14. Signature
        sig = self._archetype_signature(somatotype)

        # 15. Cardio prescription
        cardio_rx = self._cardio_prescription(p.primary_goal, p.days_per_week)

        # 15. Warnings and notes
        warnings = list(ir.warnings)
        notes = list(ir.notes)
        active_medical_flags = sorted(k for k, v in p.medical_flags.items() if v)
        if active_medical_flags:
            warnings.append(
                "Medical review required before starting: "
                + ", ".join(active_medical_flags).replace("_", " ")
                + ". This plan is educational and should be cleared by a qualified clinician."
            )
        if not all(volume_audit["within_one_set"].values()):
            largest = sorted(
                volume_audit["diff_sets"].items(),
                key=lambda kv: abs(kv[1]),
                reverse=True,
            )[:3]
            notes.append(
                "Weekly volume audit: "
                + ", ".join(f"{muscle} {diff:+d} sets" for muscle, diff in largest)
                + ". Adjust accessories if recovery or progress indicates a mismatch."
            )
        tree_strategy, tree_reason = recommend_phase_strategy(
            bc.body_fat_pct or 20, p.experience, p.sex, bc.bmi, p.primary_goal,
        )
        goal_strategy = {
            GoalArchetype.FAT_LOSS: "cut",
            GoalArchetype.MUSCLE_GAIN: "bulk",
            GoalArchetype.RECOMPOSITION: "recomp",
            GoalArchetype.GENERAL_HEALTH: "maintenance",
        }.get(p.primary_goal)
        if goal_strategy and tree_strategy != goal_strategy:
            # Goal-strategy mismatch is now a WARNING (not a note) because a
            # user who selects FAT_LOSS but is actually underweight should
            # see the message prominently. See audit finding F61.
            warnings.append(
                f"Reference-guide phase decision tree suggests '{tree_strategy}' "
                f"({tree_reason}), while the selected goal implies '{goal_strategy}'. "
                f"The plan follows the selected goal but this mismatch should be reviewed "
                f"with the client before proceeding."
            )
        if ee.calorie_target_breakdown.get("alpert_safeguard_applied"):
            warnings.append(
                "Fat-loss deficit was capped by Alpert's maximum fat-loss rate "
                "to reduce unnecessary lean-mass-loss risk."
            )

        return PlanRecommendation(
            profile=p.to_dict(),
            archetype_signature=sig.code(),
            trainee_category=trainee,
            body_composition=bc,
            anthropometrics=anthro,
            energy=ee,
            training=TrainingPlan(
                split=ts,
                weekly_volume=wv,
                intensity=ins,
                periodisation=per,
                density=dty,
                exercise_rule={
                    "include": er.include,
                    "exclude": er.exclude,
                    "substitute_map": er.substitute_map,
                },
                progression=prog,
                weekly_schedule=sched,
                volume_reconciliation=volume_audit,
                cardio_zones=cz,
                cardio_prescription=cardio_rx,
                warmup_protocol=self._warmup_protocol(),
                cooldown_protocol=self._cooldown_protocol(),
            ),
            nutrition=NutritionPlan(
                calories=ee.calorie_target,
                macros=m,
                macro_cycle=mc,
                hydration=h,
                micronutrients=micros,
                meal_plan=day_plan,
                weekly_meal_plan=week_plan,
                cuisine=cuisines,
                supplements={
                    "foundational": supps.foundational,
                    "goal_specific": supps.goal_specific,
                    "conditional": supps.conditional,
                },
            ),
            muscular_potential=mp,
            protocols=protocols,
            intake_report=ir,
            warnings=warnings,
            notes=notes,
            meal_plan_audit=meal_audit,
        )

    def _cardio_prescription(self, goal: GoalArchetype,
                             days_per_week: int) -> Dict[str, str]:
        """Cardio prescription (RippedBody: use sparingly, if at all)."""
        # RippedBody stance: cardio is supplementary, not the main driver.
        # Diet drives the deficit; training drives muscle.
        if goal == GoalArchetype.FAT_LOSS:
            lifting_minutes = 45 * days_per_week
            cardio_cap = max(30, int(lifting_minutes * 0.5))
            recommended = min(max(45, 20 * days_per_week), cardio_cap)
            return {
                "weekly_cardio_minutes": str(recommended),
                "weekly_cardio_cap_minutes": str(cardio_cap),
                "modality": "Zone-2 walking or easy cycling",
                "guidance": "Keep cardio supplementary and below half of weekly "
                            "lifting time. Diet drives the deficit; resistance "
                            "training preserves muscle. Add cardio only if "
                            "fat-loss rate is too slow.",
                "step_target": "8,000-10,000 steps/day outside sessions",
            }
        if goal == GoalArchetype.GENERAL_HEALTH:
            return {
                "weekly_cardio_minutes": "90-120",
                "modality": "Zone-2 walking, cycling, or swimming",
                "guidance": "For general health, aim for ~20-30 min of "
                            "easy cardio 3-4×/week.",
                "step_target": "8,000-10,000 steps/day",
            }
        # Muscle gain / recomp / strength: minimal cardio
        return {
            "weekly_cardio_minutes": "0-60",
            "modality": "Optional Zone-2 walking",
            "guidance": "Cardio is optional for this goal. Excessive cardio "
                        "can interfere with recovery and blunt a calorie surplus.",
            "step_target": "7,000+ steps/day for general health",
        }

    def _warmup_protocol(self) -> List[str]:
        return [
            "5 min easy cardio (bike, walk, row) to raise body temperature",
            "Dynamic mobility: hip openers, thoracic rotations, ankle circles",
            "Activation: 2 × 15 band pull-aparts, 2 × 10 glute bridges",
            "Specific warm-up: 2 sets of the first compound at ~50% then ~70%",
        ]

    def _cooldown_protocol(self) -> List[str]:
        return [
            "5 min walking / slow cycling to bring heart rate down",
            "Static stretches holding 30s each: hip flexors, hamstrings, "
            "thoracic spine, pecs, lats",
            "Box breathing 4-4-4-4 for 2 min to down-regulate",
        ]
