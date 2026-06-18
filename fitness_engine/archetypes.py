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
6. Activity     — sedentary, mostly_sedentary, moderately/lightly/highly/very active
7. Diet         — balanced, omnivore, vegan, vegetarian, pescatarian, keto, etc.
8. Environment  — home_bodyweight, home_gym, gym_full
9. Session      — express_30, short_45, standard_60, extended_90

The combination forms a deterministic *archetype signature* that drives
all downstream decisions.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from itertools import product
from typing import Dict, Iterator, List, Optional


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
    """Coarse age buckets.

    Note: ``ClientProfile`` accepts ages 13+, so ``YOUNG`` covers 13-30
    (including adolescents). The narrower 18-30 range cited in older
    comments was incorrect; the engine does not have a separate TEEN
    bucket. See audit finding F5.
    """
    YOUNG = "young"      # 13-30 (includes adolescents)
    ADULT = "adult"      # 31-45
    MIDDLE = "middle"    # 46-64
    SENIOR = "senior"    # 65+ (P2 #18 — separated from MIDDLE so a 90-year-old
                         # does not share a bucket with a 46-year-old)


class Sex(str, Enum):
    MALE = "male"
    FEMALE = "female"


class ActivityLevel(str, Enum):
    """Daily activity levels using the reference guide's multiplier bands.

    The original four values are retained for backwards compatibility;
    MODERATELY_ACTIVE and VERY_ACTIVE complete the five-tier guide model.
    """
    SEDENTARY = "sedentary"                  # <5k steps/day, desk job
    MOSTLY_SEDENTARY = "mostly_sedentary"    # <5k steps + lifting
    LIGHTLY_ACTIVE = "lightly_active"        # 5-10k steps + training, low end
    MODERATELY_ACTIVE = "moderately_active"  # 5-10k steps + training, midpoint
    HIGHLY_ACTIVE = "highly_active"          # 10k+ steps + training
    VERY_ACTIVE = "very_active"              # Physical job + training


class DietaryPreference(str, Enum):
    BALANCED = "balanced"
    OMNIVORE = "omnivore"
    VEGAN = "vegan"
    VEGETARIAN = "vegetarian"
    PESCATARIAN = "pescatarian"
    POLLO_PESCATARIAN = "pollo_pescatarian"
    KETO = "keto"
    LOW_CARB = "low_carb"
    MEDITERRANEAN = "mediterranean"
    PALEO = "paleo"
    GLUTEN_FREE = "gluten_free"
    HIGH_PROTEIN = "high_protein"


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

        The prefix lengths are chosen so that no two enum values within the
        same dimension produce the same code segment. A collision check runs
        at module import (see ``_validate_code_uniqueness`` below) so that
        adding a new enum value that would create a collision is caught
        immediately. See audit finding F2.
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
            f"{_SESSION_CODES[self.session]}"
        )

    def __str__(self) -> str:
        return self.code()


_ENV_CODES = {
    TrainingEnvironment.HOME_BODYWEIGHT: "HOM",
    TrainingEnvironment.HOME_GYM: "HGY",
    TrainingEnvironment.GYM_FULL: "GYM",
}

# P2 #38 — explicit SessionLength → code-segment mapping. Previously
# `self.session.value.split('_')[1]` was used, which is fragile: a new
# SessionLength value like `rest_day` would yield `"day"` instead of the
# intended duration. An explicit mapping makes intent clear and fails
# loudly (KeyError) if a new value is added without updating this dict.
_SESSION_CODES = {
    SessionLength.EXPRESS_30: "30",
    SessionLength.SHORT_45: "45",
    SessionLength.STANDARD_60: "60",
    SessionLength.EXTENDED_90: "90",
}

# Per-dimension prefix lengths used by ``code()``. Centralized here so the
# collision validator can mirror the truncation logic.
_CODE_PREFIX_LENGTHS = {
    "goal": 3,
    "somatotype": 4,
    "experience": 3,
    "age_group": 4,
    "activity": 3,
    "diet": 4,
}


def _validate_code_uniqueness() -> None:
    """Verify that no two enum values within a dimension produce the same
    code segment after truncation. Raises ``AssertionError`` on collision.

    This guard runs at module import so a future enum addition that would
    break the code's uniqueness is caught immediately rather than silently
    producing ambiguous signature codes. See audit finding F2.
    """
    dimensions = [
        ("goal", GoalArchetype),
        ("somatotype", Somatotype),
        ("experience", ExperienceLevel),
        ("age_group", AgeGroup),
        ("activity", ActivityLevel),
        ("diet", DietaryPreference),
    ]
    for name, enum_cls in dimensions:
        n = _CODE_PREFIX_LENGTHS[name]
        seen: dict = {}
        for member in enum_cls:
            seg = member.value[:n].upper()
            if seg in seen:
                raise AssertionError(
                    f"ArchetypeSignature.code() collision in dimension "
                    f"'{name}': '{member.value}' and '{seen[seg].value}' "
                    f"both truncate to '{seg}' at length {n}. "
                    f"Increase the prefix length for this dimension."
                )
            seen[seg] = member


_validate_code_uniqueness()


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


@dataclass(frozen=True)
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
@dataclass(frozen=True)
class ArchetypeProfile:
    """Human-friendly description and coaching notes for an archetype.

    The optional ``showcase_defaults`` field carries a ``(age, sex, height_cm,
    weight_kg, body_fat_pct)`` tuple used by the CLI's ``showcase`` command
    to render a representative plan for this archetype. Co-locating the
    defaults here (rather than in a separate dict in ``cli.py``) prevents
    drift if a nickname is renamed. See audit finding F75.
    """
    signature: ArchetypeSignature
    nickname: str
    summary: str
    strengths: List[str]
    risks: List[str]
    emphasis: List[str]
    # Optional (age, sex, height_cm, weight_kg, body_fat_pct) for the showcase.
    showcase_defaults: Optional[tuple] = None


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


def iter_signatures() -> Iterator["ArchetypeSignature"]:
    """Lazy generator yielding every possible archetype signature."""
    for combo in product(
        GoalArchetype, Somatotype, ExperienceLevel, AgeGroup, Sex,
        ActivityLevel, DietaryPreference, TrainingEnvironment, SessionLength,
    ):
        yield ArchetypeSignature(*combo)


def signature_from_dict(d: Dict) -> ArchetypeSignature:
    """Build a signature from a dict of string values.

    Each field is constructed individually so that a typo (e.g.
    ``"begginer"``) produces a clear error message naming the offending
    key and the invalid value, rather than a bare ``ValueError`` from the
    enum constructor with no context. See audit finding F3.
    """
    field_specs = [
        ("goal", GoalArchetype),
        ("somatotype", Somatotype),
        ("experience", ExperienceLevel),
        ("age_group", AgeGroup),
        ("sex", Sex),
        ("activity", ActivityLevel),
        ("diet", DietaryPreference),
        ("environment", TrainingEnvironment),
        ("session", SessionLength),
    ]
    kwargs = {}
    for key, enum_cls in field_specs:
        if key not in d:
            raise KeyError(
                f"signature_from_dict: missing required key '{key}'. "
                f"Provided keys: {sorted(d.keys())}"
            )
        raw = d[key]
        try:
            kwargs[key] = enum_cls(raw)
        except ValueError:
            valid = [m.value for m in enum_cls]
            raise ValueError(
                f"signature_from_dict: invalid value {raw!r} for key "
                f"'{key}'. Valid values: {valid}"
            ) from None
    return ArchetypeSignature(**kwargs)


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
        showcase_defaults=(22, Sex.MALE, 180, 64, 11),
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
        showcase_defaults=(35, Sex.MALE, 178, 92, 25),
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
        showcase_defaults=(30, Sex.MALE, 175, 78, 22),
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
        showcase_defaults=(45, Sex.FEMALE, 165, 68, 28),
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
        showcase_defaults=(27, Sex.MALE, 178, 74, 12),
    ),
}


def get_curated(name: str) -> Optional[ArchetypeProfile]:
    """Look up a curated profile by nickname; returns None if not found."""
    return CURATED_PROFILES.get(name)


def all_curated() -> List[ArchetypeProfile]:
    """Return all curated archetype profiles."""
    return list(CURATED_PROFILES.values())
