"""
archetypes.py
=============

Systematic categorization of client profiles using a multi-dimensional
archetype framework. Every client is described by a unique combination of
orthogonal dimensions (goal × somatotype × experience × age × sex ×
activity × diet × environment × health × time). The combination forms a
deterministic *archetype signature* that drives all downstream decisions.

Design principles
-----------------
1. **Orthogonality**: each dimension captures one independent axis of
   variation so that archetypes can be combined freely.
2. **Enumerability**: every value is an enum member, so we can index
   the full combinatorial space.
3. **Determinism**: given a profile, the archetype signature is unique
   and reproducible.
4. **Explainability**: every recommendation can be traced back to the
   archetype combination that produced it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from itertools import product
from typing import Dict, List, Optional, Tuple


# --------------------------------------------------------------------------- #
# Dimension enums                                                             #
# --------------------------------------------------------------------------- #
class GoalArchetype(str, Enum):
    """Primary training / nutrition goal."""
    FAT_LOSS = "fat_loss"
    MUSCLE_GAIN = "muscle_gain"
    RECOMPOSITION = "recomposition"
    STRENGTH = "strength"
    ENDURANCE = "endurance"
    GENERAL_HEALTH = "general_health"
    ATHLETIC_PERFORMANCE = "athletic_performance"
    REHABILITATION = "rehabilitation"


class Somatotype(str, Enum):
    """Body-type classification (Sheldon-derived, simplified)."""
    ECTOMORPH = "ectomorph"        # Lean, fast metabolism, hard gainer
    MESOMORPH = "mesomorph"        # Athletic, moderate gain/loss
    ENDOMORPH = "endomorph"        # Higher adiposity, easier gain
    MIXED = "mixed"                # Cannot be cleanly classified


class ExperienceLevel(str, Enum):
    """Resistance-training experience."""
    NOVICE = "novice"              # < 3 months consistent training
    BEGINNER = "beginner"          # 3-12 months
    INTERMEDIATE = "intermediate"  # 1-3 years
    ADVANCED = "advanced"          # 3-5 years
    ELITE = "elite"                # 5+ years competitive / specialised


class AgeGroup(str, Enum):
    """Coarse age buckets that share physiological norms."""
    YOUTH = "youth"                # 14-17
    YOUNG_ADULT = "young_adult"    # 18-25
    ADULT = "adult"                # 26-40
    MIDDLE = "middle"              # 41-55
    SENIOR = "senior"              # 56-70
    ELDER = "elder"                # 71+


class Sex(str, Enum):
    MALE = "male"
    FEMALE = "female"


class ActivityLevel(str, Enum):
    """Non-training daily activity (NEAT)."""
    SEDENTARY = "sedentary"        # Desk job, minimal walking
    LIGHT = "light"                # Light walking 1-3 days/wk
    MODERATE = "moderate"          # Active job or 3-5 walks/wk
    VERY_ACTIVE = "very_active"    # Physical job or daily activity
    ATHLETE = "athlete"            # Multiple daily training sessions


class DietaryPreference(str, Enum):
    OMNIVORE = "omnivore"
    PESCATARIAN = "pescatarian"
    POLLO_PESCATARIAN = "pollo_pescatarian"   # Poultry + fish, no red meat
    VEGETARIAN = "vegetarian"                # Eggs + dairy OK
    VEGAN = "vegan"
    KETO = "keto"                            # High-fat, very low carb
    MEDITERRANEAN = "mediterranean"
    LOW_FODMAP = "low_fodmap"
    HALAL = "halal"
    KOSHER = "kosher"
    FLEXIBLE = "flexible"


class TrainingEnvironment(str, Enum):
    HOME_BODYWEIGHT = "home_bodyweight"
    HOME_MINIMAL = "home_minimal"             # Bands, dumbbells
    HOME_FULL = "home_full"                   # Full home gym
    GYM_COMMERCIAL = "gym_commercial"
    GYM_FULL = "gym_full"                     # Powerlifting/strongman
    HYBRID = "hybrid"
    OUTDOOR = "outdoor"


class HealthCondition(str, Enum):
    NONE = "none"
    TYPE_2_DIABETES = "t2_diabetes"
    PRE_DIABETES = "pre_diabetes"
    HYPERTENSION = "hypertension"
    HIGH_CHOLESTEROL = "high_cholesterol"
    PCOS = "pcos"
    HYPOTHYROIDISM = "hypothyroidism"
    JOINT_ISSUES_KNEE = "joint_knee"
    JOINT_ISSUES_SHOULDER = "joint_shoulder"
    LOWER_BACK = "lower_back"
    CARDIO_LIMITED = "cardio_limited"
    CELIAC = "celiac"
    IBS = "ibs"
    PREGNANCY = "pregnancy"
    POSTPARTUM = "postpartum"


class SessionLength(str, Enum):
    """Available time per training session."""
    EXPRESS_30 = "express_30"        # 30 min
    SHORT_45 = "short_45"            # 45 min
    STANDARD_60 = "standard_60"      # 60 min
    EXTENDED_90 = "extended_90"      # 90 min


class CookingSkill(str, Enum):
    BASIC = "basic"           # Can boil, fry, simple assembly
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"     # Multi-step, complex recipes


# --------------------------------------------------------------------------- #
# Archetype combination                                                       #
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ArchetypeSignature:
    """Immutable combination of all archetype dimensions."""
    goal: GoalArchetype
    somatotype: Somatotype
    experience: ExperienceLevel
    age_group: AgeGroup
    sex: Sex
    activity: ActivityLevel
    diet: DietaryPreference
    environment: TrainingEnvironment
    session: SessionLength

    def code(self) -> str:
        """Short human-readable code, e.g. 'FL-MESO-INT-ADLT-F-MOD-OMNI-GYM-S60'.

        Useful as a primary key for caching, telemetry, and cohort analysis.
        """
        return (
            f"{self.goal.value[:3].upper()}-"
            f"{self.somatotype.value[:4].upper()}-"
            f"{self.experience.value[:3].upper()}-"
            f"{self.age_group.value[:4].upper()}-"
            f"{'M' if self.sex == Sex.MALE else 'F'}-"
            f"{self.activity.value[:3].upper()}-"
            f"{self.diet.value[:4].upper()}-"
            f"{self.environment.value[:3].upper()}-"
            f"{self.session.value.split('_')[1]}"
        )

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        return self.code()


# --------------------------------------------------------------------------- #
# Population catalog                                                          #
# --------------------------------------------------------------------------- #
@dataclass
class ArchetypeProfile:
    """Human-friendly description and behavioral notes for an archetype."""
    signature: ArchetypeSignature
    nickname: str
    summary: str
    strengths: List[str]
    risks: List[str]
    emphasis: List[str]   # training / nutrition emphasis areas


# --------------------------------------------------------------------------- #
# Catalog generator                                                           #
# --------------------------------------------------------------------------- #
def total_combinations() -> int:
    """Return the cardinality of the archetype space."""
    return (
        len(GoalArchetype) * len(Somatotype) * len(ExperienceLevel)
        * len(AgeGroup) * len(Sex) * len(ActivityLevel)
        * len(DietaryPreference) * len(TrainingEnvironment)
        * len(SessionLength)
    )


def enumerate_signatures() -> List[ArchetypeSignature]:
    """Enumerate every legally-possible archetype signature.

    Useful for QA testing, regression coverage, and cohort dashboards.
    Note: not every combination is biologically sensible (e.g. elite +
    youth), so downstream logic still validates.
    """
    sigs: List[ArchetypeSignature] = []
    for combo in product(
        GoalArchetype, Somatotype, ExperienceLevel, AgeGroup, Sex,
        ActivityLevel, DietaryPreference, TrainingEnvironment, SessionLength,
    ):
        sigs.append(ArchetypeSignature(*combo))
    return sigs


def signature_from_dict(d: Dict) -> ArchetypeSignature:
    """Build a signature from a dict of string values (e.g. JSON)."""
    return ArchetypeSignature(
        goal=GoalArchetype(d["goal"]),
        somatotype=Somatotype(d["somatotype"]),
        experience=ExperienceLevel(d["experience"]),
        age_group=AgeGroup(d["age_group"]),
        sex=Sex(d["sex"]),
        activity=ActivityLevel(d["activity"]),
        diet=DietaryPreference(d["diet"]),
        environment=TrainingEnvironment(d["environment"]),
        session=SessionLength(d["session"]),
    )


# --------------------------------------------------------------------------- #
# Example archetype profiles (curated library)                                #
# --------------------------------------------------------------------------- #
CURATED_PROFILES: Dict[str, ArchetypeProfile] = {
    "office_worker_fat_loss": ArchetypeProfile(
        signature=ArchetypeSignature(
            goal=GoalArchetype.FAT_LOSS,
            somatotype=Somatotype.ENDOMORPH,
            experience=ExperienceLevel.BEGINNER,
            age_group=AgeGroup.ADULT,
            sex=Sex.FEMALE,
            activity=ActivityLevel.SEDENTARY,
            diet=DietaryPreference.MEDITERRANEAN,
            environment=TrainingEnvironment.GYM_COMMERCIAL,
            session=SessionLength.STANDARD_60,
        ),
        nickname="The Desk-Bound Reset",
        summary=(
            "Sedentary knowledge worker with modest training history, "
            "looking to drop body fat while protecting lean tissue."
        ),
        strengths=[
            "Likely responsive to small calorie deficits",
            "Can train 3-4 days per week consistently",
        ],
        risks=[
            "Low NEAT → TDEE often overestimated",
            "Joint creep from desk posture",
            "Under-eating protein while dieting",
        ],
        emphasis=[
            "Daily step target (8-10k)",
            "High-protein (1.8 g/kg)",
            "Resistance training 3x/week to preserve lean mass",
        ],
    ),
    "ectomorph_lean_gain": ArchetypeProfile(
        signature=ArchetypeSignature(
            goal=GoalArchetype.MUSCLE_GAIN,
            somatotype=Somatotype.ECTOMORPH,
            experience=ExperienceLevel.INTERMEDIATE,
            age_group=AgeGroup.YOUNG_ADULT,
            sex=Sex.MALE,
            activity=ActivityLevel.LIGHT,
            diet=DietaryPreference.OMNIVORE,
            environment=TrainingEnvironment.GYM_COMMERCIAL,
            session=SessionLength.STANDARD_60,
        ),
        nickname="The Classic Hard Gainer",
        summary=(
            "Naturally lean male wanting to add visible mass. "
            "Metabolically expensive to feed."
        ),
        strengths=[
            "Insulin sensitivity usually good",
            "Fast recovery from training",
        ],
        risks=[
            "Chronic under-eating → low energy availability",
            "Excessive cardio blunts surplus",
            "Neglecting progressive overload",
        ],
        emphasis=[
            "Caloric surplus of 300-500 kcal",
            "Carb-forward nutrition around training",
            "Heavy compound lifts 4x/week",
        ],
    ),
    "postpartum_recomp": ArchetypeProfile(
        signature=ArchetypeSignature(
            goal=GoalArchetype.RECOMPOSITION,
            somatotype=Somatotype.MIXED,
            experience=ExperienceLevel.BEGINNER,
            age_group=AgeGroup.ADULT,
            sex=Sex.FEMALE,
            activity=ActivityLevel.LIGHT,
            diet=DietaryPreference.OMNIVORE,
            environment=TrainingEnvironment.HOME_MINIMAL,
            session=SessionLength.SHORT_45,
        ),
        nickname="The Reclaiming Parent",
        summary=(
            "Postpartum woman rebuilding strength and recomposition "
            "from a home setup on limited time."
        ),
        strengths=[
            "Strong adherence potential when sessions fit life",
            "High motivation tied to identity shift",
        ],
        risks=[
            "Pelvic-floor dysfunction if progressed too fast",
            "Diastasis recti considerations",
            "Sleep deficit undermining recovery",
        ],
        emphasis=[
            "Pelvic-floor safe progression",
            "Dumbbell + band based home program",
            "Protein target 1.8 g/kg adjusted to current intake",
        ],
    ),
    "senior_strength_health": ArchetypeProfile(
        signature=ArchetypeSignature(
            goal=GoalArchetype.STRENGTH,
            somatotype=Somatotype.MIXED,
            experience=ExperienceLevel.NOVICE,
            age_group=AgeGroup.SENIOR,
            sex=Sex.MALE,
            activity=ActivityLevel.LIGHT,
            diet=DietaryPreference.MEDITERRANEAN,
            environment=TrainingEnvironment.GYM_COMMERCIAL,
            session=SessionLength.STANDARD_60,
        ),
        nickname="The Vital Retiree",
        summary=(
            "60+ male new to resistance training, focused on longevity, "
            "strength, and metabolic health."
        ),
        strengths=[
            "Excellent response to low-volume strength work",
            "Cardiometabolic gains rapid",
        ],
        risks=[
            "Sarcopenia progression",
            "Osteoporosis risk if loading absent",
            "Cardiac event screening needed",
        ],
        emphasis=[
            "Progressive overload with sub-maximal loads",
            "Bone-loading exercises (squats, presses)",
            "Adequate calcium + vitamin D",
        ],
    ),
    "diabetes_reversal": ArchetypeProfile(
        signature=ArchetypeSignature(
            goal=GoalArchetype.GENERAL_HEALTH,
            somatotype=Somatotype.ENDOMORPH,
            experience=ExperienceLevel.NOVICE,
            age_group=AgeGroup.MIDDLE,
            sex=Sex.MALE,
            activity=ActivityLevel.SEDENTARY,
            diet=DietaryPreference.MEDITERRANEAN,
            environment=TrainingEnvironment.HOME_BODYWEIGHT,
            session=SessionLength.STANDARD_60,
        ),
        nickname="The Metabolic Rebuild",
        summary=(
            "Newly diagnosed type-2 diabetic with sedentary lifestyle, "
            "needing safe but effective entry-level programming."
        ),
        strengths=[
            "Glycaemic control responds quickly to diet + exercise",
        ],
        risks=[
            "Hypoglycaemia if on insulin secretagogues",
            "Cardiovascular co-morbidity",
        ],
        emphasis=[
            "Low-glycaemic-load Mediterranean meals",
            "Daily walking protocol post-meals",
            "Resistance training 3x/week",
        ],
    ),
    "athlete_endurance": ArchetypeProfile(
        signature=ArchetypeSignature(
            goal=GoalArchetype.ENDURANCE,
            somatotype=Somatotype.ECTOMORPH,
            experience=ExperienceLevel.ADVANCED,
            age_group=AgeGroup.YOUNG_ADULT,
            sex=Sex.FEMALE,
            activity=ActivityLevel.ATHLETE,
            diet=DietaryPreference.OMNIVORE,
            environment=TrainingEnvironment.HYBRID,
            session=SessionLength.EXTENDED_90,
        ),
        nickname="The Endurance Specialist",
        summary=(
            "Advanced endurance athlete with hybrid gym + outdoor setup, "
            "aiming at race-day performance."
        ),
        strengths=[
            "High training tolerance",
            "Aerobic base already substantial",
        ],
        risks=[
            "RED-S if under-fuelled",
            "Iron deficiency common in females",
        ],
        emphasis=[
            "Periodised carb intake around sessions",
            "Strength maintenance block 2x/week",
            "Iron-rich food emphasis",
        ],
    ),
    "vegan_athlete": ArchetypeProfile(
        signature=ArchetypeSignature(
            goal=GoalArchetype.ATHLETIC_PERFORMANCE,
            somatotype=Somatotype.MESOMORPH,
            experience=ExperienceLevel.INTERMEDIATE,
            age_group=AgeGroup.YOUNG_ADULT,
            sex=Sex.MALE,
            activity=ActivityLevel.VERY_ACTIVE,
            diet=DietaryPreference.VEGAN,
            environment=TrainingEnvironment.HYBRID,
            session=SessionLength.STANDARD_60,
        ),
        nickname="The Plant-Powered Performer",
        summary=(
            "Vegan intermediate athlete wanting to optimise performance "
            "without compromising ethics. Higher attention to protein "
            "and micronutrient density required."
        ),
        strengths=[
            "High antioxidant intake from plant foods",
            "Often lower body fat at same caloric intake",
        ],
        risks=[
            "Subtle protein deficiency without planning",
            "B12, D3, omega-3 (EPA/DHA), iron, zinc gaps",
            "Lower creatine status",
        ],
        emphasis=[
            "Protein 1.8-2.0 g/kg with strategic combining",
            "Supplementation: B12, D3, algae omega-3, creatine",
            "Iron + vitamin C co-consumption",
        ],
    ),
    "keto_cruiser": ArchetypeProfile(
        signature=ArchetypeSignature(
            goal=GoalArchetype.GENERAL_HEALTH,
            somatotype=Somatotype.MESOMORPH,
            experience=ExperienceLevel.INTERMEDIATE,
            age_group=AgeGroup.ADULT,
            sex=Sex.MALE,
            activity=ActivityLevel.MODERATE,
            diet=DietaryPreference.KETO,
            environment=TrainingEnvironment.GYM_COMMERCIAL,
            session=SessionLength.STANDARD_60,
        ),
        nickname="The Keto Cruiser",
        summary=(
            "Intermediate client committed to ketogenic eating for "
            "metabolic and cognitive benefits."
        ),
        strengths=[
            "Stable energy and reduced hunger",
            "Improved triglycerides / HDL pattern",
        ],
        risks=[
            "Reduced glycogen -> training capacity",
            "Electrolyte loss (Na, K, Mg)",
            "Saturated fat ceiling for lipids",
        ],
        emphasis=[
            "Carbs <= 50 g/day, fat 70% kcal",
            "Daily electrolytes: Na 3-5 g, K 3.5 g, Mg 400 mg",
        ],
    ),
    "shift_worker": ArchetypeProfile(
        signature=ArchetypeSignature(
            goal=GoalArchetype.GENERAL_HEALTH,
            somatotype=Somatotype.MIXED,
            experience=ExperienceLevel.BEGINNER,
            age_group=AgeGroup.ADULT,
            sex=Sex.MALE,
            activity=ActivityLevel.LIGHT,
            diet=DietaryPreference.OMNIVORE,
            environment=TrainingEnvironment.HOME_MINIMAL,
            session=SessionLength.SHORT_45,
        ),
        nickname="The Shift-Worker",
        summary=(
            "Nurse / firefighter / driver on rotating shifts. "
            "Needs flexible, time-efficient programming."
        ),
        strengths=[
            "Adaptability to irregular schedule",
            "Often high physical job demands",
        ],
        risks=[
            "Circadian disruption -> recovery impairment",
            "Sleep variability blunts training response",
            "Meal timing collapse",
        ],
        emphasis=[
            "Short, dense sessions (45 min)",
            "Resistance on day-shift; Zone-2 on night-shift",
            "Protein-forward meals regardless of clock time",
        ],
    ),
    "back_pain_returner": ArchetypeProfile(
        signature=ArchetypeSignature(
            goal=GoalArchetype.REHABILITATION,
            somatotype=Somatotype.MESOMORPH,
            experience=ExperienceLevel.NOVICE,
            age_group=AgeGroup.ADULT,
            sex=Sex.FEMALE,
            activity=ActivityLevel.SEDENTARY,
            diet=DietaryPreference.OMNIVORE,
            environment=TrainingEnvironment.GYM_COMMERCIAL,
            session=SessionLength.STANDARD_60,
        ),
        nickname="The Back-Pain Returner",
        summary=(
            "Client with chronic lower-back issue wanting to return to "
            "training safely after a layoff. Needs physio-aware programming."
        ),
        strengths=[
            "High motivation after recovery",
            "Often excellent body awareness",
        ],
        risks=[
            "Re-injury if progressed too fast",
            "Fear-avoidance behaviour",
        ],
        emphasis=[
            "Trap-bar DL / light RDL only - no conventional DL",
            "Core stability work daily",
            "McGill Big-3 as warm-up",
        ],
    ),
    "youth_athlete": ArchetypeProfile(
        signature=ArchetypeSignature(
            goal=GoalArchetype.ATHLETIC_PERFORMANCE,
            somatotype=Somatotype.MESOMORPH,
            experience=ExperienceLevel.INTERMEDIATE,
            age_group=AgeGroup.YOUTH,
            sex=Sex.MALE,
            activity=ActivityLevel.VERY_ACTIVE,
            diet=DietaryPreference.OMNIVORE,
            environment=TrainingEnvironment.GYM_COMMERCIAL,
            session=SessionLength.STANDARD_60,
        ),
        nickname="The Youth Athlete",
        summary=(
            "16-year-old multi-sport athlete. Skeletally immature "
            "but training at high volume."
        ),
        strengths=[
            "High motor learning capacity",
            "Strong recovery",
        ],
        risks=[
            "Growth-plate injury if load mismanaged",
            "Relative Energy Deficiency in Sport (RED-S)",
        ],
        emphasis=[
            "No max-effort lifts (no 1RM testing)",
            "Higher reps (8-15) for safety",
            "Energy availability > caloric restriction",
        ],
    ),
    "pcos_balancer": ArchetypeProfile(
        signature=ArchetypeSignature(
            goal=GoalArchetype.FAT_LOSS,
            somatotype=Somatotype.ENDOMORPH,
            experience=ExperienceLevel.BEGINNER,
            age_group=AgeGroup.ADULT,
            sex=Sex.FEMALE,
            activity=ActivityLevel.SEDENTARY,
            diet=DietaryPreference.MEDITERRANEAN,
            environment=TrainingEnvironment.GYM_COMMERCIAL,
            session=SessionLength.STANDARD_60,
        ),
        nickname="The PCOS Balancer",
        summary=(
            "Woman with PCOS wanting to reduce visceral fat, improve "
            "insulin sensitivity, and protect lean mass."
        ),
        strengths=[
            "Strong response to resistance training",
            "Anti-inflammatory diet benefits",
        ],
        risks=[
            "Insulin resistance complicates deficit",
            "Androgen excess may limit muscle gain",
        ],
        emphasis=[
            "Protein >= 1.8 g/kg, distributed across meals",
            "Low-glycaemic carbs, high fibre",
            "Resistance training > cardio for IR",
        ],
    ),
}


def get_curated(name: str) -> Optional[ArchetypeProfile]:
    return CURATED_PROFILES.get(name)


def all_curated() -> List[ArchetypeProfile]:
    return list(CURATED_PROFILES.values())
