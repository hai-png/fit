"""
archetypes.py
=============

Systematic categorization of client profiles using a streamlined
multi-dimensional archetype framework, grounded in the RippedBody
methodology and the Muscle & Strength body-type classification.

Dimensions
----------
1. Goal         — fat_loss (cut), muscle_gain (bulk), recomposition,
                   strength, general_health
2. Somatotype   — ectomorph, mesomorph, endomorph (M&S classification)
3. Experience   — beginner, intermediate, advanced
4. Age group    — young, adult, middle
5. Sex          — male, female
6. Activity     — sedentary, mostly_sedentary, lightly_active, highly_active
7. Diet         — omnivore, vegan
8. Environment  — home_bodyweight, home_gym, gym_full
9. Session      — express_30, short_45, standard_60, extended_90

The combination forms a deterministic *archetype signature* that drives
all downstream decisions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from itertools import product
from typing import Dict, List, Optional


# --------------------------------------------------------------------------- #
# Dimension enums                                                             #
# --------------------------------------------------------------------------- #
class GoalArchetype(str, Enum):
    """Primary training / nutrition goal (RippedBody strategies)."""
    FAT_LOSS = "fat_loss"             # Cut
    MUSCLE_GAIN = "muscle_gain"       # Bulk
    RECOMPOSITION = "recomposition"   # Simultaneous fat loss + muscle gain
    STRENGTH = "strength"             # Strength-focused
    GENERAL_HEALTH = "general_health" # Maintenance / health


class Somatotype(str, Enum):
    """Body-type classification (M&S / Sheldon-derived).

    Ectomorph: small frame, fast metabolism, hard gainer, lean.
    Mesomorph: athletic, muscular, gains easily, rectangular.
    Endomorph: soft/round, gains fat easily, stocky, strong legs.
    """
    ECTOMORPH = "ectomorph"
    MESOMORPH = "mesomorph"
    ENDOMORPH = "endomorph"


class ExperienceLevel(str, Enum):
    """Training experience — simplified to three tiers (RippedBody)."""
    BEGINNER = "beginner"        # New to training; weekly load jumps
    INTERMEDIATE = "intermediate"  # Monthly progress
    ADVANCED = "advanced"        # Progress over months/year


class AgeGroup(str, Enum):
    """Coarse age buckets."""
    YOUNG = "young"      # 18-30
    ADULT = "adult"      # 31-45
    MIDDLE = "middle"    # 46+


class Sex(str, Enum):
    MALE = "male"
    FEMALE = "female"


class ActivityLevel(str, Enum):
    """Daily activity levels (RippedBody TDEE multipliers).

    These bundle NEAT + occupational activity with the assumption that the
    client lifts weights 3–6 days per week.
    """
    SEDENTARY = "sedentary"             # Little/no exercise → BMR × 1.15
    MOSTLY_SEDENTARY = "mostly_sedentary"  # Office work + lifting → × 1.35
    LIGHTLY_ACTIVE = "lightly_active"   # Lightly active + lifting → × 1.55
    HIGHLY_ACTIVE = "highly_active"     # Highly active + lifting → × 1.75


class DietaryPreference(str, Enum):
    OMNIVORE = "omnivore"
    VEGAN = "vegan"


class TrainingEnvironment(str, Enum):
    HOME_BODYWEIGHT = "home_bodyweight"  # Bodyweight only, no equipment
    HOME_GYM = "home_gym"                # Dumbbells, bands, bench, rack
    GYM_FULL = "gym_full"               # Full commercial gym (all equipment)


class SessionLength(str, Enum):
    """Available time per training session."""
    EXPRESS_30 = "express_30"
    SHORT_45 = "short_45"
    STANDARD_60 = "standard_60"
    EXTENDED_90 = "extended_90"


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
        """Short human-readable code.

        Format: GOAL-SOMA-EXP-AGE-SEX-ACT-DIET-ENV-LEN
        e.g. 'MUS-ECTO-BEG-YOUN-M-SED-OMNI-HOM-60'
        """
        return (
            f"{self.goal.value[:3].upper()}-"
            f"{self.somatotype.value[:4].upper()}-"
            f"{self.experience.value[:3].upper()}-"
            f"{self.age_group.value[:4].upper()}-"
            f"{'M' if self.sex == Sex.MALE else 'F'}-"
            f"{self.activity.value[:3].upper()}-"
            f"{self.diet.value[:4].upper()}-"
            f"{_ENV_CODES[self.environment]}-"
            f"{self.session.value.split('_')[1]}"
        )

    def __str__(self) -> str:
        return self.code()


_ENV_CODES = {
    TrainingEnvironment.HOME_BODYWEIGHT: "HOM",
    TrainingEnvironment.HOME_GYM: "HGY",
    TrainingEnvironment.GYM_FULL: "GYM",
}


# --------------------------------------------------------------------------- #
# Trainee category (RippedBody 9 categories)                                  #
# --------------------------------------------------------------------------- #
class TraineeCategory(str, Enum):
    """The 9 categories of trainee from RippedBody goal-setting guide.

    These classify a person's *current physique state* and drive the
    recommended strategy (cut / bulk / recomp / maintenance).
    """
    SKINNY = "skinny"                       # Low muscle, low body fat → Bulk
    FAT_BUT_MUSCLED = "fat_but_muscled"     # Muscular + high BF → Cut
    MUSCLED_LEAN = "muscled_lean"           # Muscled, few lbs to lose → Cut
    SHREDDED = "shredded"                   # Defined abs → Maintenance / Slow bulk
    FAT_AND_WEAK = "fat_and_weak"           # High BF, new to training → Cut + newbie gains
    OBESE = "obese"                         # Very high BF → Habit change + cut
    SKINNY_FAT = "skinny_fat"               # Low muscle + moderate-high BF → Recomp or Bulk
    PURGATORY = "purgatory"                 # Stuck spinning wheels → Cycle cut/bulk
    NEW_TRAINEE_HEALTHY = "new_trainee_healthy"  # Healthy BW, new to training → Recomp / Bulk


@dataclass
class TraineeProfile:
    """Classification result with strategy and coaching notes."""
    category: TraineeCategory
    strategy: str         # "cut", "bulk", "recomp", "maintenance"
    estimated_body_fat: float
    has_significant_muscle: bool
    summary: str
    pitfalls: List[str]
    recommendations: List[str]


# --------------------------------------------------------------------------- #
# Population catalog                                                          #
# --------------------------------------------------------------------------- #
@dataclass
class ArchetypeProfile:
    """Human-friendly description and coaching notes for an archetype."""
    signature: ArchetypeSignature
    nickname: str
    summary: str
    strengths: List[str]
    risks: List[str]
    emphasis: List[str]


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
    """Enumerate every possible archetype signature (returns a list)."""
    return list(iter_signatures())


def iter_signatures():
    """Lazy generator yielding every possible archetype signature."""
    for combo in product(
        GoalArchetype, Somatotype, ExperienceLevel, AgeGroup, Sex,
        ActivityLevel, DietaryPreference, TrainingEnvironment, SessionLength,
    ):
        yield ArchetypeSignature(*combo)


def signature_from_dict(d: Dict) -> ArchetypeSignature:
    """Build a signature from a dict of string values."""
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
# Curated archetype profiles                                                  #
# --------------------------------------------------------------------------- #
CURATED_PROFILES: Dict[str, ArchetypeProfile] = {
    "skinny_hardgainer": ArchetypeProfile(
        signature=ArchetypeSignature(
            goal=GoalArchetype.MUSCLE_GAIN,
            somatotype=Somatotype.ECTOMORPH,
            experience=ExperienceLevel.BEGINNER,
            age_group=AgeGroup.YOUNG,
            sex=Sex.MALE,
            activity=ActivityLevel.LIGHTLY_ACTIVE,
            diet=DietaryPreference.OMNIVORE,
            environment=TrainingEnvironment.GYM_FULL,
            session=SessionLength.STANDARD_60,
        ),
        nickname="The Classic Hard Gainer",
        summary=(
            "Naturally lean with a fast metabolism. Needs a calorie "
            "surplus and compound lifting to build visible mass."
        ),
        strengths=[
            "Insulin sensitivity usually good",
            "Fast recovery from training",
        ],
        risks=[
            "Chronic under-eating → low energy availability",
            "Excessive cardio blunts the surplus",
            "Neglecting progressive overload",
        ],
        emphasis=[
            "Caloric surplus of ~200-300 kcal above TDEE (scaled to body weight)",
            "Carb-forward nutrition around training",
            "Heavy compound lifts 3-4×/week, minimal cardio",
        ],
    ),
    "fat_but_muscled": ArchetypeProfile(
        signature=ArchetypeSignature(
            goal=GoalArchetype.FAT_LOSS,
            somatotype=Somatotype.MESOMORPH,
            experience=ExperienceLevel.INTERMEDIATE,
            age_group=AgeGroup.ADULT,
            sex=Sex.MALE,
            activity=ActivityLevel.MOSTLY_SEDENTARY,
            diet=DietaryPreference.OMNIVORE,
            environment=TrainingEnvironment.GYM_FULL,
            session=SessionLength.STANDARD_60,
        ),
        nickname="The Muscled Cutter",
        summary=(
            "Has a solid muscular base hidden under a layer of fat. "
            "The hard work is done — it's just a case of revealing it."
        ),
        strengths=[
            "Excellent response to a calorie deficit",
            "Strength preservation during cuts is natural",
        ],
        risks=[
            "Over-reducing training volume",
            "Dieting too aggressively",
            "Water-weight fluctuation messing with motivation",
        ],
        emphasis=[
            "Moderate deficit (~0.5-0.75% body weight/week)",
            "3 days/week training focused on compound lifts",
            "Maintain strength; reduce accessory volume",
        ],
    ),
    "skinny_fat": ArchetypeProfile(
        signature=ArchetypeSignature(
            goal=GoalArchetype.RECOMPOSITION,
            somatotype=Somatotype.ENDOMORPH,
            experience=ExperienceLevel.BEGINNER,
            age_group=AgeGroup.ADULT,
            sex=Sex.MALE,
            activity=ActivityLevel.SEDENTARY,
            diet=DietaryPreference.OMNIVORE,
            environment=TrainingEnvironment.GYM_FULL,
            session=SessionLength.STANDARD_60,
        ),
        nickname="The Skinny-Fat Recomper",
        summary=(
            "Low muscle mass with moderate-to-high body fat. Newbie gains "
            "are possible with a recomp or gentle bulk approach."
        ),
        strengths=[
            "Strong potential for simultaneous fat loss and muscle gain",
            "Quick visible changes from resistance training",
        ],
        risks=[
            "Dieting too hard → losing what little muscle exists",
            "Spinning wheels with excessive cardio",
            "Impatience with slow recomp progress",
        ],
        emphasis=[
            "Maintenance calories or slight surplus",
            "Focus on progressive overload and compound lifts",
            "Prioritise protein and patience",
        ],
    ),
    "home_beginner": ArchetypeProfile(
        signature=ArchetypeSignature(
            goal=GoalArchetype.GENERAL_HEALTH,
            somatotype=Somatotype.MESOMORPH,
            experience=ExperienceLevel.BEGINNER,
            age_group=AgeGroup.MIDDLE,
            sex=Sex.FEMALE,
            activity=ActivityLevel.MOSTLY_SEDENTARY,
            diet=DietaryPreference.OMNIVORE,
            environment=TrainingEnvironment.HOME_GYM,
            session=SessionLength.SHORT_45,
        ),
        nickname="The Home-Gym Beginner",
        summary=(
            "Middle-aged beginner training at home with minimal equipment, "
            "focused on building a foundation of strength and health."
        ),
        strengths=[
            "Strong response to basic resistance training",
            "Improved metabolic markers from diet + exercise",
        ],
        risks=[
            "Inconsistent progressive overload at home",
            "Underestimating the importance of protein",
        ],
        emphasis=[
            "Bodyweight + dumbbell compound movements",
            "Maintenance calories with adequate protein (1.6 g/kg)",
            "Consistency over intensity; 3 sessions/week",
        ],
    ),
    "vegan_builder": ArchetypeProfile(
        signature=ArchetypeSignature(
            goal=GoalArchetype.MUSCLE_GAIN,
            somatotype=Somatotype.MESOMORPH,
            experience=ExperienceLevel.INTERMEDIATE,
            age_group=AgeGroup.YOUNG,
            sex=Sex.MALE,
            activity=ActivityLevel.LIGHTLY_ACTIVE,
            diet=DietaryPreference.VEGAN,
            environment=TrainingEnvironment.GYM_FULL,
            session=SessionLength.STANDARD_60,
        ),
        nickname="The Plant-Powered Builder",
        summary=(
            "Vegan intermediate wanting to build muscle. Higher attention "
            "to protein quantity and micronutrient density is essential."
        ),
        strengths=[
            "High antioxidant intake from plant foods",
            "Often good insulin sensitivity",
        ],
        risks=[
            "Protein quantity without deliberate planning",
            "B12, D3, omega-3, iron, zinc gaps",
        ],
        emphasis=[
            "Protein 1.8-2.2 g/kg with strategic combining",
            "Supplement: B12, D3, algae omega-3",
            "Calorie surplus prioritising calorie-dense plant foods",
        ],
    ),
}


def get_curated(name: str) -> Optional[ArchetypeProfile]:
    return CURATED_PROFILES.get(name)


def all_curated() -> List[ArchetypeProfile]:
    return list(CURATED_PROFILES.values())
