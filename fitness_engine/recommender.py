"""
recommender.py
==============

The orchestrator. Takes a fully-populated ClientProfile, runs it
through the calculators, decision trees, and protocol libraries,
and returns a unified PlanRecommendation containing a training
program, a nutrition program, and an actionable summary.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from .archetypes import (
    ActivityLevel, AgeGroup, ArchetypeSignature, CookingSkill,
    DietaryPreference, ExperienceLevel, GoalArchetype, HealthCondition,
    SessionLength, Sex, Somatotype, TrainingEnvironment,
    signature_from_dict,
)
from .calculators import (
    BodyComposition, CardioZones, EnergyExpenditure, Hydration, Macros,
    StrengthEstimate, body_composition, energy_expenditure, hydration,
    macros_for, cardio_zones, infer_age_group, infer_somatotype,
)
from .decision_trees import (
    IntensityScheme, Periodisation, ProgressionRule, SessionDensity,
    TrainingSplit, WeeklyVolume, exercise_selection, intensity_scheme,
    macro_overrides, periodisation, cuisine_pick, progression_rule,
    session_density, supplement_stack, training_split, weekly_volume,
)
from .meal_plans import MealItem, MealPlan, assemble_day
from .exercise_plans import EXERCISE_LIBRARY, Exercise, weekly_split, build_session
from .questionnaires import IntakeReport, intake_report


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
    resting_hr: int = 60

    # Lifestyle
    activity: ActivityLevel = ActivityLevel.MODERATE
    sleep_hours: float = 7.5
    stress_level: int = 5

    # Health
    health_conditions: List[HealthCondition] = field(default_factory=list)
    medications: str = ""
    injuries: str = ""
    parq_answers: Dict[str, str] = field(default_factory=dict)

    # Diet
    dietary_preference: DietaryPreference = DietaryPreference.OMNIVORE
    allergies: List[str] = field(default_factory=list)
    dislikes: List[str] = field(default_factory=list)
    meals_per_day: int = 3
    cooking_skill: CookingSkill = CookingSkill.INTERMEDIATE
    preferred_cuisines: List[str] = field(default_factory=list)

    # Training
    experience: ExperienceLevel = ExperienceLevel.BEGINNER
    environment: TrainingEnvironment = TrainingEnvironment.GYM_COMMERCIAL
    equipment: List[str] = field(default_factory=list)
    days_per_week: int = 4
    session_length: SessionLength = SessionLength.STANDARD_60

    # Goals
    primary_goal: GoalArchetype = GoalArchetype.GENERAL_HEALTH
    secondary_goals: List[GoalArchetype] = field(default_factory=list)
    target_weight_kg: Optional[float] = None
    timeline_weeks: int = 12

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # Convert enums to values for JSON-friendliness
        for k, v in list(d.items()):
            if hasattr(v, "value"):
                d[k] = v.value
        return d

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
            resting_hr=d.get("resting_hr", 60),
            activity=ActivityLevel(d.get("activity", "moderate")),
            sleep_hours=d.get("sleep_hours", 7.5),
            stress_level=d.get("stress_level", 5),
            health_conditions=[HealthCondition(c) for c in d.get("health_conditions", [])],
            medications=d.get("medications", ""),
            injuries=d.get("injuries", ""),
            parq_answers=d.get("parq_answers", {}),
            dietary_preference=DietaryPreference(d.get("dietary_preference", "omnivore")),
            allergies=d.get("allergies", []),
            dislikes=d.get("dislikes", []),
            meals_per_day=d.get("meals_per_day", 3),
            cooking_skill=CookingSkill(d.get("cooking_skill", "intermediate")),
            preferred_cuisines=d.get("preferred_cuisines", []),
            experience=ExperienceLevel(d.get("experience", "beginner")),
            environment=TrainingEnvironment(d.get("environment", "gym_commercial")),
            equipment=d.get("equipment", []),
            days_per_week=d.get("days_per_week", 4),
            session_length=SessionLength(d.get("session_length", "standard_60")),
            primary_goal=GoalArchetype(d.get("primary_goal", "general_health")),
            secondary_goals=[GoalArchetype(g) for g in d.get("secondary_goals", [])],
            target_weight_kg=d.get("target_weight_kg"),
            timeline_weeks=d.get("timeline_weeks", 12),
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
    weekly_schedule: Dict[str, List[dict]]   # weekday -> list of exercise specs
    cardio_zones: CardioZones
    cardio_prescription: Dict[str, str]
    warmup_protocol: List[str]
    cooldown_protocol: List[str]


@dataclass
class NutritionPlan:
    calories: float
    macros: Macros
    hydration: Hydration
    meal_plan: MealPlan
    cuisine: List[str]
    overrides: Dict[str, str]
    supplements: dict


@dataclass
class PlanRecommendation:
    profile: Dict[str, Any]
    archetype_signature: str
    archetype_summary: Dict[str, Any]
    body_composition: BodyComposition
    energy: EnergyExpenditure
    training: TrainingPlan
    nutrition: NutritionPlan
    intake_report: IntakeReport
    warnings: List[str]
    notes: List[str]


# --------------------------------------------------------------------------- #
# The engine                                                                  #
# --------------------------------------------------------------------------- #
class Recommender:
    """Main entry-point. Build with a ClientProfile and call .recommend()."""

    def __init__(self, profile: ClientProfile):
        self.p = profile

    # ------------------------------------------------------------------ #
    def _archetype_signature(self) -> ArchetypeSignature:
        # Infer somatotype if not supplied explicitly
        somatotype = infer_somatotype(
            self.p.weight_kg, self.p.height_cm, self.p.age, self.p.sex,
            self.p.body_fat_pct,
        )
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

    # ------------------------------------------------------------------ #
    def recommend(self) -> PlanRecommendation:
        # 1. Archetype signature
        sig = self._archetype_signature()

        # 2. Body composition
        bc = body_composition(
            self.p.weight_kg, self.p.height_cm, self.p.age, self.p.sex,
            bf_pct=self.p.body_fat_pct,
            waist_cm=self.p.waist_cm, neck_cm=self.p.neck_cm, hip_cm=self.p.hip_cm,
        )

        # 3. Energy expenditure
        ee = energy_expenditure(
            self.p.weight_kg, self.p.height_cm, self.p.age, self.p.sex,
            self.p.activity, self.p.primary_goal,
            lean_mass_kg=bc.lean_mass_kg,
        )

        # 4. Macros
        m = macros_for(
            calories=ee.calorie_target,
            weight_kg=self.p.weight_kg, lean_mass_kg=bc.lean_mass_kg,
            goal=self.p.primary_goal, sex=self.p.sex,
            somatotype=sig.somatotype, dietary_pref=self.p.dietary_preference,
        )

        # 5. Hydration
        h = hydration(self.p.weight_kg, workout_minutes=45 * self.p.days_per_week)

        # 6. Decision trees (training)
        ts = training_split(self.p.primary_goal, self.p.experience,
                            [c.value for c in self.p.health_conditions])
        wv = weekly_volume(self.p.primary_goal, self.p.experience,
                           self.p.days_per_week, sig.age_group)
        ins = intensity_scheme(self.p.primary_goal, self.p.experience,
                               [c.value for c in self.p.health_conditions])
        per = periodisation(self.p.primary_goal, self.p.experience)
        dty = session_density(self.p.primary_goal, self.p.session_length)
        er = exercise_selection(
            self.p.primary_goal, self.p.environment, self.p.equipment,
            [c.value for c in self.p.health_conditions], sig.age_group,
        )
        prog = progression_rule(self.p.primary_goal, self.p.experience,
                                [c.value for c in self.p.health_conditions])
        cz = cardio_zones(self.p.age, self.p.resting_hr)

        # 7. Weekly schedule (raw Exercise objects)
        sched_raw = weekly_split(
            self.p.primary_goal, self.p.experience,
            self.p.days_per_week, self.p.environment,
            self.p.equipment, [c.value for c in self.p.health_conditions],
        )
        # Pretty schedule with sets/reps based on intensity scheme
        ins_for_schedule = ins
        sched = {}
        for day, exs in sched_raw.items():
            day_list = []
            for i, ex in enumerate(exs):
                is_compound = ex.pattern in (
                    "squat", "hinge", "horizontal_push",
                    "vertical_push", "horizontal_pull", "vertical_pull"
                )
                rep_range = (ins_for_schedule.primary_reps
                             if is_compound else
                             ins_for_schedule.accessory_reps)
                rpe = (ins_for_schedule.primary_rpe
                       if is_compound else
                       ins_for_schedule.accessory_rpe)
                day_list.append({
                    "name": ex.name,
                    "pattern": ex.pattern,
                    "primary_muscle": ex.primary_muscle,
                    "sets_reps": f"3 x {rep_range}",
                    "rpe": rpe,
                    "rest_seconds": dty.work_seconds + dty.rest_seconds,
                    "equipment": ex.equipment or ["bodyweight"],
                    "cues": ex.cues[:3],
                })
            sched[day] = day_list

        # 8. Decision trees (nutrition)
        overrides = macro_overrides([c.value for c in self.p.health_conditions])
        cuisines = cuisine_pick(self.p.preferred_cuisines,
                                 self.p.dietary_preference)
        supps = supplement_stack(self.p.primary_goal, self.p.sex,
                                 [c.value for c in self.p.health_conditions])

        # 9. Meal plan assembly (primary cuisine first; rotate in plan)
        primary_cuisine = cuisines[0] if cuisines else "american"
        day_plan = assemble_day(
            cuisine=primary_cuisine,
            diet=self.p.dietary_preference,
            target_calories=ee.calorie_target,
            meals_per_day=self.p.meals_per_day,
            allergens=self.p.allergies,
        )

        # 10. Intake report (PAR-Q + health caveats)
        intake_dict = self._flatten_answers_for_intake()
        ir = intake_report(intake_dict)

        # 11. Final warning / note roll-up
        warnings = list(ir.warnings)
        notes = list(ir.notes)
        if self.p.stress_level >= 8:
            notes.append("High self-reported stress — emphasise sleep and Zone-2 work.")
        if not self.p.parq_answers or all(v == "no" for v in self.p.parq_answers.values()):
            notes.append("PAR-Q clear — proceed with standard progression.")
        if self.p.sleep_hours < 6:
            warnings.append("Sleep < 6 h — recovery may be impaired; raise sleep hygiene priority.")
        if self.p.timeline_weeks < 8 and self.p.primary_goal == GoalArchetype.MUSCLE_GAIN:
            notes.append("Timeline < 8 weeks for hypertrophy — adjust expectations to ~0.5-1 kg/mo.")
        if self.p.primary_goal == GoalArchetype.FAT_LOSS and \
           ee.calorie_target < 1200:
            warnings.append("Calorie target below 1200 kcal — medical supervision recommended.")

        # 11b. Cardio prescription, warm-up/cool-down
        cardio_rx = self._cardio_prescription(self.p.primary_goal,
                                              self.p.days_per_week,
                                              ts, self.p.health_conditions)
        warmup = self._warmup_protocol()
        cooldown = self._cooldown_protocol()

        # 12. Build archetype summary
        archetype_summary = self._archetype_summary(sig)

        return PlanRecommendation(
            profile=self.p.to_dict(),
            archetype_signature=sig.code(),
            archetype_summary=archetype_summary,
            body_composition=bc,
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
                cardio_zones=cz,
                cardio_prescription=cardio_rx,
                warmup_protocol=warmup,
                cooldown_protocol=cooldown,
            ),
            nutrition=NutritionPlan(
                calories=ee.calorie_target,
                macros=m,
                hydration=h,
                meal_plan=day_plan,
                cuisine=cuisines,
                overrides=overrides,
                supplements={
                    "foundational": supps.foundational,
                    "goal_specific": supps.goal_specific,
                    "conditional": supps.conditional,
                },
            ),
            intake_report=ir,
            warnings=warnings,
            notes=notes,
        )

    # ------------------------------------------------------------------ #
    def _archetype_summary(self, sig: ArchetypeSignature) -> Dict[str, Any]:
        return {
            "signature_code": sig.code(),
            "goal": sig.goal.value,
            "somatotype": sig.somatotype.value,
            "experience": sig.experience.value,
            "age_group": sig.age_group.value,
            "sex": sig.sex.value,
            "activity": sig.activity.value,
            "diet": sig.diet.value,
            "environment": sig.environment.value,
            "session": sig.session.value,
        }

    def _flatten_answers_for_intake(self) -> Dict[str, Any]:
        """Build a flat dict for the questionnaire intake_report helper."""
        answers: Dict[str, Any] = {}
        answers.update(self.p.parq_answers)
        answers["ls_sleep_hours"] = self.p.sleep_hours
        answers["ls_stress"] = self.p.stress_level
        answers["hh_conditions"] = [c.value for c in self.p.health_conditions]
        return answers


    # ------------------------------------------------------------------ #
    def _cardio_prescription(self, goal, days_per_week: int,
                             split: TrainingSplit,
                             health: List[HealthCondition]) -> Dict[str, str]:
        """Build a per-week cardio prescription."""
        # Base weekly cardio minutes from split
        weekly_minutes = round(180 * split.cardio_pct + 60)
        z2_pct = {
            GoalArchetype.FAT_LOSS: 0.6,
            GoalArchetype.MUSCLE_GAIN: 0.5,
            GoalArchetype.RECOMPOSITION: 0.6,
            GoalArchetype.STRENGTH: 0.5,
            GoalArchetype.ENDURANCE: 0.3,
            GoalArchetype.ATHLETIC_PERFORMANCE: 0.4,
            GoalArchetype.GENERAL_HEALTH: 0.7,
            GoalArchetype.REHABILITATION: 0.8,
        }[goal]
        z2_min = round(weekly_minutes * z2_pct)
        hiit_min = weekly_minutes - z2_min
        # Spread
        sessions = max(2, min(4, days_per_week))
        z2_per = round(z2_min / sessions)
        # Cardio-limited: walk-only
        if HealthCondition.CARDIO_LIMITED in health:
            return {
                "weekly_cardio_minutes": str(weekly_minutes),
                "modality": "low-intensity walking only",
                "zone_2": f"{z2_per} min walking, {sessions} sessions/week",
                "hiit": "0 min",
                "step_target": "8-10k steps/day outside sessions",
            }
        return {
            "weekly_cardio_minutes": str(weekly_minutes),
            "modality": "mixed (rower / bike / walk / jog)",
            "zone_2": f"{z2_per} min per session, {sessions} sessions/week",
            "hiit": (f"{hiit_min} min total weekly (2-3 sessions, "
                     f"20-30 min each including warm-up)"),
            "step_target": "8-10k steps/day outside sessions",
        }

    # ------------------------------------------------------------------ #
    def _warmup_protocol(self) -> List[str]:
        return [
            "5 min easy cardio (bike, walk, row) to raise temperature",
            "Dynamic mobility: hip openers, thoracic rotations, ankle circles",
            "Activation: 2 x 15 band pull-aparts, 2 x 10 glute bridges",
            "Specific warm-up: 2 sets of the first compound at ~50% then ~70%",
        ]

    # ------------------------------------------------------------------ #
    def _cooldown_protocol(self) -> List[str]:
        return [
            "5 min walking / slow cycling to bring heart rate down",
            "Static stretches holding 30s each: hip flexors, hamstrings, "
            "thoracic spine, pecs, lats",
            "Box breathing 4-4-4-4 for 2 min to down-regulate",
        ]
