"""
recommender.py
==============

The orchestrator. Takes a ClientProfile, runs it through the calculators,
decision trees, and protocol libraries, and returns a unified
PlanRecommendation grounded in the RippedBody methodology.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from .archetypes import (
    ActivityLevel, AgeGroup, ArchetypeSignature, DietaryPreference,
    ExperienceLevel, GoalArchetype, Sex, Somatotype, TrainingEnvironment,
    SessionLength, TraineeProfile,
)
from .calculators import (
    BodyComposition, CardioZones, EnergyExpenditure, Hydration, Macros,
    MicronutrientTargets, MuscularPotential,
    body_composition, energy_expenditure, hydration,
    macros_for, cardio_zones, infer_age_group, infer_somatotype,
    classify_trainee, micronutrient_targets, muscular_potential,
)
from .decision_trees import (
    IntensityScheme, Periodisation, ProgressionRule, SessionDensity,
    TrainingSplit, WeeklyVolume, exercise_selection, intensity_scheme,
    cuisine_pick, progression_rule, session_density, supplement_stack,
    training_split, weekly_volume, periodisation,
)
from .meal_plans import MealPlan, assemble_day
from .exercise_plans import weekly_split
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
    visual_bf_label: Optional[str] = None
    wrist_cm: Optional[float] = None
    resting_hr: int = 60

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

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
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
            visual_bf_label=d.get("visual_bf_label"),
            wrist_cm=d.get("wrist_cm"),
            resting_hr=d.get("resting_hr", 60),
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
    cardio_zones: CardioZones
    cardio_prescription: Dict[str, str]
    warmup_protocol: List[str]
    cooldown_protocol: List[str]


@dataclass
class NutritionPlan:
    calories: float
    macros: Macros
    hydration: Hydration
    micronutrients: MicronutrientTargets
    meal_plan: MealPlan
    cuisine: List[str]
    supplements: dict


@dataclass
class PlanRecommendation:
    profile: Dict[str, Any]
    archetype_signature: str
    trainee_category: TraineeProfile
    body_composition: BodyComposition
    energy: EnergyExpenditure
    training: TrainingPlan
    nutrition: NutritionPlan
    muscular_potential: Optional[MuscularPotential]
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

    def recommend(self) -> PlanRecommendation:
        p = self.p

        # 1. Body composition (with visual BF fallback)
        bc = body_composition(
            p.weight_kg, p.height_cm, p.age, p.sex,
            bf_pct=p.body_fat_pct,
            waist_cm=p.waist_cm, neck_cm=p.neck_cm, hip_cm=p.hip_cm,
            visual_bf_label=p.visual_bf_label,
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

        # 6. Hydration
        h = hydration(p.weight_kg, workout_minutes=45 * p.days_per_week)

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
        cz = cardio_zones(p.age, p.resting_hr)

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
                day_list.append({
                    "name": ex.name,
                    "pattern": ex.pattern,
                    "primary_muscle": ex.primary_muscle,
                    "sets_reps": f"3 × {rep_range}",
                    "rir": rir,
                    "rest_seconds": dty.rest_seconds,
                    "equipment": ex.equipment or ["bodyweight"],
                    "cues": ex.cues[:3],
                })
            sched[day] = day_list

        # 9. Decision trees (nutrition)
        cuisines = cuisine_pick(p.preferred_cuisines)

        # 10. Meal plan assembly
        primary_cuisine = cuisines[0] if cuisines else "american"
        day_plan = assemble_day(
            cuisine=primary_cuisine,
            diet=p.dietary_preference,
            target_calories=ee.calorie_target,
            meals_per_day=p.meals_per_day,
            allergens=p.allergies,
        )

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

        # 13. Signature
        sig = self._archetype_signature(somatotype)

        # 14. Cardio prescription
        cardio_rx = self._cardio_prescription(p.primary_goal, p.days_per_week)

        # 15. Warnings and notes
        warnings = list(ir.warnings)
        notes = list(ir.notes)

        return PlanRecommendation(
            profile=p.to_dict(),
            archetype_signature=sig.code(),
            trainee_category=trainee,
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
                warmup_protocol=self._warmup_protocol(),
                cooldown_protocol=self._cooldown_protocol(),
            ),
            nutrition=NutritionPlan(
                calories=ee.calorie_target,
                macros=m,
                hydration=h,
                micronutrients=micros,
                meal_plan=day_plan,
                cuisine=cuisines,
                supplements={
                    "foundational": supps.foundational,
                    "goal_specific": supps.goal_specific,
                    "conditional": supps.conditional,
                },
            ),
            muscular_potential=mp,
            intake_report=ir,
            warnings=warnings,
            notes=notes,
        )

    def _cardio_prescription(self, goal: GoalArchetype,
                             days_per_week: int) -> Dict[str, str]:
        """Cardio prescription (RippedBody: use sparingly, if at all)."""
        # RippedBody stance: cardio is supplementary, not the main driver.
        # Diet drives the deficit; training drives muscle.
        if goal == GoalArchetype.FAT_LOSS:
            weekly_min = max(60, 30 * days_per_week)
            return {
                "weekly_cardio_minutes": str(weekly_min),
                "modality": "Zone-2 walking or easy cycling",
                "guidance": "Keep cardio supplementary. Diet drives the "
                            "deficit; resistance training preserves muscle. "
                            "Add cardio only if fat-loss rate is too slow.",
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
