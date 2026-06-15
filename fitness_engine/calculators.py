"""
calculators.py
==============

Numerical engines grounded in the RippedBody Nutrition Pyramid
methodology and the Muscle & Strength body-type framework.

Key sources
-----------
• Calories:  rippedbody.com/calories — Harris-Benedict BMR,
             4-tier TDEE multipliers, 0.75%/wk fat-loss rate,
             experience-tiered bulk surplus.
• Macros:    rippedbody.com/macros — protein by lean mass or body weight,
             fat 15-30% of calories, carbs as the remainder.
• Body fat:  rippedbody.com/body-fat-guide — visual estimation ranges
             used when tape measurements are unavailable.
• Somatotype: muscleandstrength.com body-type article — frame + adiposity.

Every calculator is pure-functional and returns a typed result object.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

from .archetypes import (
    ActivityLevel, AgeGroup, ExperienceLevel, GoalArchetype, Sex, Somatotype,
    TraineeCategory, TraineeProfile,
)


# --------------------------------------------------------------------------- #
# Result containers                                                           #
# --------------------------------------------------------------------------- #
@dataclass
class BodyComposition:
    bmi: float
    bmi_category: str
    body_fat_pct: Optional[float]
    lean_mass_kg: Optional[float]
    fat_mass_kg: Optional[float]
    estimation_method: str   # "navy", "deurenberg", "visual", "user_input"


@dataclass
class EnergyExpenditure:
    bmr: float
    tdee: float
    activity_multiplier: float
    calorie_target: float
    calorie_target_breakdown: dict


@dataclass
class Macros:
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    protein_pct: float
    carbs_pct: float
    fat_pct: float
    rationale: str


@dataclass
class Hydration:
    base_ml: float
    workout_bonus_ml: float
    total_ml: float


@dataclass
class StrengthEstimate:
    epley_1rm: float
    brzycki_1rm: float
    lander_1rm: float
    average_1rm: float
    pct_of_1rm: dict


@dataclass
class CardioZones:
    age: int
    hr_max_simple: int
    hr_max_tanaka: int
    zones: dict   # zone_name -> (low_bpm, high_bpm)


# --------------------------------------------------------------------------- #
# Body composition                                                            #
# --------------------------------------------------------------------------- #
class BMICategory(str, Enum):
    UNDERWEIGHT = "underweight"
    NORMAL = "normal"
    OVERWEIGHT = "overweight"
    OBESE_I = "obese_class_i"
    OBESE_II = "obese_class_ii"
    OBESE_III = "obese_class_iii"


def bmi(weight_kg: float, height_cm: float) -> float:
    """Body Mass Index (kg/m^2)."""
    if height_cm <= 0:
        raise ValueError("height_cm must be positive")
    h = height_cm / 100.0
    return weight_kg / (h * h)


def bmi_category(b: float) -> BMICategory:
    if b < 18.5:
        return BMICategory.UNDERWEIGHT
    if b < 25.0:
        return BMICategory.NORMAL
    if b < 30.0:
        return BMICategory.OVERWEIGHT
    if b < 35.0:
        return BMICategory.OBESE_I
    if b < 40.0:
        return BMICategory.OBESE_II
    return BMICategory.OBESE_III


# --- Navy body-fat (tape measurements) --- #
def body_fat_navy(
    sex: Sex, height_cm: float, neck_cm: float,
    waist_cm: float, hip_cm: Optional[float] = None,
) -> float:
    """U.S. Navy body-fat estimate (metric, Hodgdon & Beckett 1984)."""
    if height_cm <= 0:
        raise ValueError("height_cm must be positive")
    if waist_cm <= neck_cm:
        raise ValueError("waist_cm must exceed neck_cm")
    if sex == Sex.MALE:
        bf = (495 / (1.0324
                     - 0.19077 * math.log10(waist_cm - neck_cm)
                     + 0.15456 * math.log10(height_cm))) - 450
    else:
        if hip_cm is None:
            raise ValueError("hip_cm required for female Navy BF estimate")
        if waist_cm + hip_cm <= neck_cm:
            raise ValueError("waist + hip must exceed neck")
        bf = (495 / (1.29579
                     - 0.35004 * math.log10(waist_cm + hip_cm - neck_cm)
                     + 0.22100 * math.log10(height_cm))) - 450
    return round(max(2.0, min(bf, 60.0)), 1)


# --- Deurenberg (BMI-based fallback) --- #
def body_fat_bmi_method(b: float, age: int, sex: Sex) -> float:
    """Deurenberg BF% estimate from BMI, age and sex."""
    sex_coef = 1.0 if sex == Sex.MALE else 0.0
    bf = (1.20 * b) + (0.23 * age) - (10.8 * sex_coef) - 5.4
    return round(max(2.0, min(bf, 60.0)), 1)


# --- Visual body-fat estimation (RippedBody guide) --- #
# When tape measurements aren't available, the user compares themselves to
# the visual ranges from rippedbody.com/body-fat-guide. Each band maps to a
# representative midpoint used for downstream calculations.
VISUAL_BF_BANDS: List[Tuple[str, Tuple[float, float], float, str]] = [
    # (label, (low_pct, high_pct), midpoint, description)
    ("shredded",     (6.0, 9.0),   8.0,  "Visible abs, vascularity, lower-back fat gone."),
    ("very_lean",    (10.0, 12.0), 11.0, "Clear abs, some definition everywhere."),
    ("lean",         (13.0, 15.0), 14.0, "Blurry six-pack when flexed."),
    ("average_fit",  (16.0, 19.0), 17.5, "Some muscle definition; no visible abs."),
    ("soft",         (20.0, 24.0), 22.0, "Little definition; noticeable fat layer."),
    ("overweight",   (25.0, 29.0), 27.0, "Round physique; fat is dominant."),
    ("obese",        (30.0, 40.0), 33.0, "Significant fat; obese category."),
]

VISUAL_BF_LABEL_TO_KEY: Dict[str, str] = {
    b[0]: b[0] for b in VISUAL_BF_BANDS
}


def body_fat_from_visual(label: str) -> float:
    """Return a representative body-fat % from a visual-band label.

    Labels correspond to the rippedbody.com/body-fat-guide photo ranges.
    Most people underestimate their body fat — the midpoints are set
    accordingly.
    """
    for lbl, (lo, hi), mid, _ in VISUAL_BF_BANDS:
        if label == lbl:
            return mid
    raise ValueError(
        f"Unknown visual BF label '{label}'. "
        f"Choose from: {[b[0] for b in VISUAL_BF_BANDS]}"
    )


def visual_bf_description(label: str) -> str:
    """Return the human-readable description for a visual BF band."""
    for lbl, _, _, desc in VISUAL_BF_BANDS:
        if label == lbl:
            return desc
    raise ValueError(f"Unknown visual BF label '{label}'.")


# --- Composite body composition --- #
def body_composition(
    weight_kg: float, height_cm: float, age: int, sex: Sex,
    bf_pct: Optional[float] = None,
    waist_cm: Optional[float] = None, neck_cm: Optional[float] = None,
    hip_cm: Optional[float] = None,
    visual_bf_label: Optional[str] = None,
) -> BodyComposition:
    """Compute body-composition metrics.

    Priority for body-fat estimation:
      1. ``bf_pct`` — user-supplied (most trusted)
      2. Navy formula — if waist + neck given
      3. Visual estimation — if ``visual_bf_label`` given
      4. Deurenberg BMI method — fallback
    """
    b = bmi(weight_kg, height_cm)

    if bf_pct is not None:
        bf = bf_pct
        method = "user_input"
    elif waist_cm and neck_cm:
        bf = body_fat_navy(sex, height_cm, neck_cm, waist_cm, hip_cm)
        method = "navy"
    elif visual_bf_label is not None:
        bf = body_fat_from_visual(visual_bf_label)
        method = "visual"
    else:
        bf = body_fat_bmi_method(b, age, sex)
        method = "deurenberg"

    lean = round(weight_kg * (1 - bf / 100.0), 2)
    fat = round(weight_kg - lean, 2)
    return BodyComposition(
        bmi=round(b, 2),
        bmi_category=bmi_category(b).value,
        body_fat_pct=bf,
        lean_mass_kg=lean,
        fat_mass_kg=fat,
        estimation_method=method,
    )


# --------------------------------------------------------------------------- #
# Energy expenditure (RippedBody methodology)                                 #
# --------------------------------------------------------------------------- #
# RippedBody's 4-tier activity multipliers (rippedbody.com/calories Step 2).
ACTIVITY_MULTIPLIERS = {
    ActivityLevel.SEDENTARY: 1.15,
    ActivityLevel.MOSTLY_SEDENTARY: 1.35,
    ActivityLevel.LIGHTLY_ACTIVE: 1.55,
    ActivityLevel.HIGHLY_ACTIVE: 1.75,
}


def bmr_harris_benedict(
    weight_kg: float, height_cm: float, age: int, sex: Sex,
) -> float:
    """Harris-Benedict BMR (metric) — RippedBody's preferred formula.

    Men:   BMR = 66 + (13.7 × kg) + (5 × cm) − (6.8 × age)
    Women: BMR = 655 + (9.6 × kg) + (1.8 × cm) − (4.7 × age)
    """
    if sex == Sex.MALE:
        return 66 + (13.7 * weight_kg) + (5 * height_cm) - (6.8 * age)
    return 655 + (9.6 * weight_kg) + (1.8 * height_cm) - (4.7 * age)


def bmr_mifflin(
    weight_kg: float, height_cm: float, age: int, sex: Sex,
) -> float:
    """Mifflin-St Jeor BMR (alternative reference)."""
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return base + 5 if sex == Sex.MALE else base - 161


def bmr_katch(lean_mass_kg: float) -> float:
    """Katch-McArdle BMR (requires lean body mass only)."""
    if lean_mass_kg <= 0:
        raise ValueError("lean_mass_kg must be positive")
    return 370 + (21.6 * lean_mass_kg)


def tdee(bmr: float, level: ActivityLevel) -> float:
    return bmr * ACTIVITY_MULTIPLIERS[level]


# --- Experience-tiered weight-gain rates (RippedBody bulk) --- #
BULK_MONTHLY_RATE = {
    ExperienceLevel.BEGINNER: 0.02,     # 2% body weight / month
    ExperienceLevel.INTERMEDIATE: 0.01, # 1%
    ExperienceLevel.ADVANCED: 0.005,    # 0.5%
}

# Fat-loss rate: 0.75% body weight/week (RippedBody default,
# accounts for metabolic adaptation).
FAT_LOSS_WEEKLY_RATE = 0.0075


def calorie_target(
    tdee_value: float, goal: GoalArchetype,
    bodyweight_kg: float, experience: ExperienceLevel,
    target_weight_kg: Optional[float] = None,
    fat_loss_rate: float = FAT_LOSS_WEEKLY_RATE,
) -> Tuple[float, dict]:
    """Goal-driven calorie target (RippedBody methodology).

    Cut (fat loss):
        TDCI = TDEE − (BW × rate × 1100*)   # 1100 kcal per kg fat/wk
        *RippedBody uses 0.75% BW/week with a metabolic-adaptation buffer.

    Bulk (muscle gain):
        TDCI = TDEE + (BW × monthly_rate × 330*)   # 330 kcal per kg gain/mo
        *Rates tiered by experience (2%/1%/0.5% per month).

    Recomp / General health:
        TDCI = TDEE (maintenance)
    """
    breakdown: dict = {"tdee": round(tdee_value, 1)}

    if goal == GoalArchetype.FAT_LOSS:
        bw = target_weight_kg or bodyweight_kg
        deficit = bw * fat_loss_rate * 1100  # 1100 kcal per kg fat
        target = tdee_value - deficit
        breakdown.update({
            "mode": "fat_loss (cut)",
            "weekly_loss_rate_pct": fat_loss_rate * 100,
            "daily_deficit": round(deficit, 1),
        })
    elif goal == GoalArchetype.MUSCLE_GAIN:
        monthly_rate = BULK_MONTHLY_RATE.get(experience, 0.01)
        surplus = bodyweight_kg * monthly_rate * 330  # 330 kcal per kg gain/mo
        # Add 50% buffer for NEAT adaptation (RippedBody heuristic)
        surplus_adj = surplus * 1.5
        target = tdee_value + surplus_adj
        breakdown.update({
            "mode": "muscle_gain (bulk)",
            "monthly_gain_rate_pct": monthly_rate * 100,
            "experience_tier": experience.value,
            "daily_surplus": round(surplus_adj, 1),
        })
    elif goal == GoalArchetype.RECOMPOSITION:
        target = tdee_value
        breakdown.update({"mode": "recomposition", "delta": 0.0})
    elif goal == GoalArchetype.STRENGTH:
        target = tdee_value * 1.02  # very slight surplus
        breakdown.update({"mode": "strength", "delta_pct": 2.0})
    elif goal == GoalArchetype.GENERAL_HEALTH:
        target = tdee_value
        breakdown.update({"mode": "maintenance", "delta": 0.0})
    else:
        target = tdee_value
        breakdown.update({"mode": "default", "delta": 0.0})

    # Safety floor — never drop below ~1200 kcal without a warning flag
    MIN_CALORIES = 1200
    if target < MIN_CALORIES:
        breakdown["warning"] = (
            f"Calculated target {target:.0f} kcal is below the {MIN_CALORIES} "
            f"kcal safety floor; clamped to {MIN_CALORIES}. Medical "
            f"supervision recommended."
        )
        target = MIN_CALORIES

    breakdown["target"] = round(target, 1)
    return round(target, 1), breakdown


def energy_expenditure(
    weight_kg: float, height_cm: float, age: int, sex: Sex,
    activity: ActivityLevel, goal: GoalArchetype,
    experience: ExperienceLevel,
    lean_mass_kg: Optional[float] = None,
    target_weight_kg: Optional[float] = None,
) -> EnergyExpenditure:
    """Compute BMR → TDEE → target in one pass."""
    bmr = bmr_harris_benedict(weight_kg, height_cm, age, sex)
    tdee_v = tdee(bmr, activity)
    target, breakdown = calorie_target(
        tdee_v, goal, weight_kg, experience, target_weight_kg,
    )
    return EnergyExpenditure(
        bmr=round(bmr, 1),
        tdee=round(tdee_v, 1),
        activity_multiplier=ACTIVITY_MULTIPLIERS[activity],
        calorie_target=target,
        calorie_target_breakdown=breakdown,
    )


# --------------------------------------------------------------------------- #
# Macronutrient partitioning (RippedBody methodology)                         #
# --------------------------------------------------------------------------- #
# rippedbody.com/macros — protein is set by lean mass or body weight,
# fat is 15-30% of calories, carbs fill the rest.

def _protein_target(
    goal: GoalArchetype, weight_kg: float,
    lean_mass_kg: Optional[float], body_fat_pct: Optional[float],
    target_weight_kg: Optional[float], is_vegan: bool = False,
) -> Tuple[float, str]:
    """Calculate protein in grams using RippedBody rules.

    Vegan targets are set higher because plant protein is less well
    absorbed and has lower BCAA/leucine content.
    Source: rippedbody.com/advice-for-vegans/
    """
    if body_fat_pct is not None and lean_mass_kg is not None and lean_mass_kg > 0:
        if goal == GoalArchetype.FAT_LOSS:
            mult = 2.6 if is_vegan else 2.5
            label = 'vegan' if is_vegan else 'omnivore'
            return round(lean_mass_kg * mult, 1), \
                f"{mult} g/kg lean mass (cutting, BF% known, {label})"
        mult = 2.2
        return round(lean_mass_kg * mult, 1), \
            f"{mult} g/kg lean mass (bulk/recomp, BF% known)"

    if goal == GoalArchetype.FAT_LOSS:
        ref_bw = target_weight_kg or weight_kg
        mult = 2.6 if is_vegan else 2.2
        label = 'vegan' if is_vegan else 'omnivore'
        return round(ref_bw * mult, 1), \
            f"{mult} g/kg target BW (cutting, BF% unknown, {label})"
    mult = 2.2 if is_vegan else 1.6
    label = 'vegan' if is_vegan else 'omnivore'
    return round(weight_kg * mult, 1), \
        f"{mult} g/kg body weight (bulk/recomp, BF% unknown, {label})"


def macros_for(
    calories: float, weight_kg: float, lean_mass_kg: Optional[float],
    goal: GoalArchetype, sex: Sex,
    somatotype: Somatotype, dietary_pref,
    body_fat_pct: Optional[float] = None,
    target_weight_kg: Optional[float] = None,
) -> Macros:
    """Compute macro split using RippedBody Nutrition Pyramid.

    1. Protein  — set first (by lean mass or body weight)
    2. Fat      — 20-30% of calories (bulking), 15-25% (cutting)
    3. Carbs    — the remainder

    Minimums enforced:
      Fat floor: 0.5 g/kg
      Carb floor: 1 g/kg
    """
    from .archetypes import DietaryPreference

    is_vegan = dietary_pref == DietaryPreference.VEGAN

    # 1. Protein
    protein_g, protein_rationale = _protein_target(
        goal, weight_kg, lean_mass_kg, body_fat_pct, target_weight_kg,
        is_vegan=is_vegan,
    )

    # 2. Fat — percentage band depends on goal
    if goal == GoalArchetype.FAT_LOSS:
        fat_pct = 0.20   # lower end for cutting (15-25%)
    else:
        fat_pct = 0.25   # middle for bulking (20-30%)

    # Somatotype refinement: endomorphs skew slightly lower fat, ectomorphs higher
    if somatotype == Somatotype.ENDOMORPH:
        fat_pct = max(0.15, fat_pct - 0.03)
    elif somatotype == Somatotype.ECTOMORPH:
        fat_pct = min(0.30, fat_pct + 0.03)

    fat_g = calories * fat_pct / 9
    # Enforce minimum fat floor
    fat_floor = 0.5 * weight_kg
    fat_g = max(fat_g, fat_floor)
    fat_g = round(fat_g, 1)

    # 3. Carbs — remainder
    pf_cal = protein_g * 4 + fat_g * 9
    carb_cal = max(0.0, calories - pf_cal)
    carb_g = round(carb_cal / 4, 1)
    # Enforce minimum carb floor
    carb_floor = 1.0 * weight_kg
    carb_g = max(carb_g, carb_floor)
    carb_g = round(carb_g, 1)

    return Macros(
        calories=round(calories, 1),
        protein_g=protein_g,
        carbs_g=carb_g,
        fat_g=fat_g,
        protein_pct=round(protein_g * 4 / calories * 100, 1),
        carbs_pct=round(carb_g * 4 / calories * 100, 1),
        fat_pct=round(fat_g * 9 / calories * 100, 1),
        rationale=(
            f"Protein: {protein_rationale}. "
            f"Fat: ~{fat_pct*100:.0f}% of calories ({somatotype.value} adjusted). "
            f"Carbs: remainder of calorie budget."
        ),
    )


# --------------------------------------------------------------------------- #
# Hydration                                                                   #
# --------------------------------------------------------------------------- #
def hydration(weight_kg: float, workout_minutes: int = 0) -> Hydration:
    """Daily water target. Base 35 ml/kg + 350 ml per 30 min workout."""
    base = weight_kg * 35
    bonus = (workout_minutes / 30.0) * 350
    return Hydration(base_ml=round(base, 0),
                     workout_bonus_ml=round(bonus, 0),
                     total_ml=round(base + bonus, 0))


# --------------------------------------------------------------------------- #
# Strength estimation                                                         #
# --------------------------------------------------------------------------- #
MAX_1RM_REPS = 12  # Epley/Brzycki/Lander valid for ≤12 reps


def one_rep_max(weight: float, reps: int) -> StrengthEstimate:
    """Three classic 1RM estimates + average + percent-of-1RM table.

    Clamped to [1, 12] reps — beyond that the equations diverge.
    """
    if reps < 1:
        raise ValueError("reps must be >= 1")
    if weight <= 0:
        raise ValueError("weight must be positive")
    r = min(reps, MAX_1RM_REPS)
    epley = weight * (1 + r / 30.0)
    brzycki = weight * 36.0 / (37.0 - r)
    lander = (100 * weight) / (101.3 - 2.67123 * r)
    avg = (epley + brzycki + lander) / 3.0
    pcts = {f"{p}%": round(avg * p / 100.0, 1) for p in
            [50, 60, 65, 70, 75, 80, 85, 90, 95, 100]}
    return StrengthEstimate(
        epley_1rm=round(epley, 1),
        brzycki_1rm=round(brzycki, 1),
        lander_1rm=round(lander, 1),
        average_1rm=round(avg, 1),
        pct_of_1rm=pcts,
    )


# --------------------------------------------------------------------------- #
# Cardiovascular zones                                                        #
# --------------------------------------------------------------------------- #
def cardio_zones(age: int, resting_hr: int = 60) -> CardioZones:
    hr_max = 220 - age
    hr_max_tanaka = 208 - (0.7 * age)
    hrr = hr_max_tanaka - resting_hr
    pct = lambda lo, hi: (round(resting_hr + hrr * lo, 0),
                          round(resting_hr + hrr * hi, 0))
    return CardioZones(
        age=age, hr_max_simple=hr_max, hr_max_tanaka=round(hr_max_tanaka, 0),
        zones={
            "Z1_recovery":      pct(0.50, 0.60),
            "Z2_aerobic_base":  pct(0.60, 0.70),
            "Z3_tempo":         pct(0.70, 0.80),
            "Z4_threshold":     pct(0.80, 0.90),
            "Z5_vo2max":        pct(0.90, 1.00),
        },
    )


# --------------------------------------------------------------------------- #
# Somatotype inference (M&S body-type framework)                             #
# --------------------------------------------------------------------------- #
# Based on muscleandstrength.com/articles/body-types-ectomorph-mesomorph-endomorph
# Uses frame size (wrist circumference) + BMI + body fat % to classify.

_FRAME_THRESHOLDS = {
    Sex.MALE:   {"small": 16.5, "large": 19.0},
    Sex.FEMALE: {"small": 15.5, "large": 18.0},
}


def _frame_size(sex: Sex, wrist_cm: float) -> str:
    t = _FRAME_THRESHOLDS[sex]
    if wrist_cm < t["small"]:
        return "small"
    if wrist_cm > t["large"]:
        return "large"
    return "medium"


def infer_somatotype(
    weight_kg: float, height_cm: float, age: int, sex: Sex,
    body_fat_pct: Optional[float] = None,
    wrist_cm: Optional[float] = None,
) -> Somatotype:
    """Infer somatotype using the M&S body-type framework.

    Combines adiposity (BMI/body fat) with frame size to classify:
      • Ectomorph — small frame, low BMI, lean. Hard gainer, fast metabolism.
      • Mesomorph — medium frame, athletic BMI. Gains easily.
      • Endomorph — large frame, high BMI/BF. Gains fat easily, stocky.

    M&S notes most people are a mix of two; we return the dominant type.
    """
    b = bmi(weight_kg, height_cm)
    bf = body_fat_pct if body_fat_pct is not None else body_fat_bmi_method(b, age, sex)

    # Frame-size component (if available)
    frame = None
    if wrist_cm is not None:
        frame = _frame_size(sex, wrist_cm)

    # Adiposity-based classification
    if sex == Sex.MALE:
        if bf <= 14 and b <= 23:
            base = Somatotype.ECTOMORPH
        elif bf >= 22 or b >= 28:
            base = Somatotype.ENDOMORPH
        else:
            base = Somatotype.MESOMORPH
    else:
        if bf <= 20 and b <= 22:
            base = Somatotype.ECTOMORPH
        elif bf >= 30 or b >= 28:
            base = Somatotype.ENDOMORPH
        else:
            base = Somatotype.MESOMORPH

    # Frame refinement in borderline (mesomorph) cases
    if frame is not None and base == Somatotype.MESOMORPH:
        if frame == "small":
            base = Somatotype.ECTOMORPH
        elif frame == "large":
            base = Somatotype.ENDOMORPH

    return base


# --------------------------------------------------------------------------- #
# Age group inference                                                         #
# --------------------------------------------------------------------------- #
def infer_age_group(age: int) -> AgeGroup:
    if age < 31:
        return AgeGroup.YOUNG
    if age <= 45:
        return AgeGroup.ADULT
    return AgeGroup.MIDDLE


# --------------------------------------------------------------------------- #
# Trainee category classification (RippedBody 9 categories)                   #
# --------------------------------------------------------------------------- #
def classify_trainee(
    body_fat_pct: float, experience: ExperienceLevel,
    sex: Sex, bmi_val: float,
) -> TraineeProfile:
    """Classify a trainee into one of the RippedBody 9 categories.

    Uses body-fat % and training experience to determine the current
    physique state and recommend a strategy (cut / bulk / recomp).
    Muscle mass is inferred from BMI + body fat (lean mass ratio).
    """
    # Estimate "has significant muscle" from lean mass density
    lean_ratio = 1 - body_fat_pct / 100
    has_muscle = lean_ratio > 0.78 and bmi_val >= 22

    # Sex-adjusted body-fat thresholds
    if sex == Sex.MALE:
        low_bf, mid_bf, high_bf, obese_bf = 10, 15, 22, 30
    else:
        low_bf, mid_bf, high_bf, obese_bf = 18, 24, 32, 38

    if body_fat_pct >= obese_bf:
        cat = TraineeCategory.OBESE
        strategy = "cut"
        summary = ("Carrying significant body fat. Focus on sustainable habit "
                   "changes — clean up obvious junk, add vegetables, walk daily.")
        pitfalls = [
            "Trying to diet too aggressively and rebounding",
            "Neglecting resistance training",
            "Focusing on scale weight instead of habits",
        ]
        recs = [
            "Cut obvious junk food and sugary drinks",
            "Start resistance training 3×/week",
            "Target ~0.75% body weight loss per week",
            "Walk 8,000-10,000 steps daily",
        ]
    elif body_fat_pct >= high_bf and has_muscle:
        cat = TraineeCategory.FAT_BUT_MUSCLED
        strategy = "cut"
        summary = ("Solid muscular base under a fat layer. A straightforward "
                   "cut will reveal it.")
        pitfalls = [
            "Over-reducing training volume when cutting",
            "Dieting too aggressively (>0.75%/wk)",
            "Panic at water-weight fluctuations",
        ]
        recs = [
            "Moderate deficit: ~0.5-0.75% BW/week",
            "Train 3 days/week on compound lifts",
            "Maintain strength to preserve muscle",
            "Expect ~1-1.25 lbs/week fat loss",
        ]
    elif body_fat_pct >= high_bf and not has_muscle:
        cat = TraineeCategory.FAT_AND_WEAK
        strategy = "cut"
        summary = ("Newer to training with extra body fat. You have newbie "
                   "muscle gains ahead while losing fat — the best of both worlds.")
        pitfalls = [
            "Dieting too hard and hampering newbie gains",
            "Believing you gain muscle easily without training",
            "Buying a fad program with no progressive overload",
        ]
        recs = [
            "Start a sensible strength program (3-4×/week)",
            "Target 3-5 lbs weight loss per month",
            "Focus on progressive overload and form",
            "Expect simultaneous muscle gain + fat loss",
        ]
    elif body_fat_pct >= mid_bf and has_muscle:
        cat = TraineeCategory.MUSCLED_LEAN
        strategy = "cut"
        summary = ("Muscled with a few pounds to lose. Close to a lean, "
                   "defined physique.")
        pitfalls = [
            "Getting impatient as loss slows near single digits",
            "Not taking diet breaks",
            "Mirror anxiety as water shifts daily",
        ]
        recs = [
            "Target ~0.5% BW/week loss",
            "Take a diet break every 6-8 weeks",
            "Track stomach measurements, not just scale",
            "3 days/week training suffices for retention",
        ]
    elif body_fat_pct >= mid_bf and not has_muscle:
        cat = TraineeCategory.SKINNY_FAT
        strategy = "recomp"
        summary = ("Low muscle mass with moderate-to-high fat. A recomp or "
                   "gentle bulk will build the foundation.")
        pitfalls = [
            "Dieting too hard and losing what little muscle exists",
            "Excessive cardio instead of lifting",
            "Impatience with the naturally slow recomp process",
        ]
        recs = [
            "Eat at maintenance or a slight surplus",
            "Prioritise progressive overload on compound lifts",
            "Ensure 1.8-2.2 g/kg protein daily",
            "Expect ~0.5-1% BW/month change (muscle up, fat down)",
        ]
    elif body_fat_pct >= low_bf and not has_muscle:
        cat = TraineeCategory.SKINNY
        strategy = "bulk"
        summary = ("Naturally lean with little muscle. Exciting category — "
                   "biggest visible changes are ahead with a proper bulk.")
        pitfalls = [
            "Not eating enough (especially if naturally skinny)",
            "Choosing a gym without a squat rack",
            "Not focusing on strength acquisition",
            "Adding too much cardio",
        ]
        recs = [
            "Surplus: ~2% BW/month (beginner), ~1% (intermediate)",
            "Compound lifts 3-4×/week",
            "Track calories — guessing leads to under-eating",
            "Choose calorie-dense foods if appetite is low",
        ]
    else:  # bf < low_bf → shredded or skinny depending on muscle
        if has_muscle:
            cat = TraineeCategory.SHREDDED
            strategy = "maintenance"
            summary = ("Lean and muscled. Maintain or enter a slow, careful "
                       "bulk to add more mass.")
            pitfalls = [
                "Dirty bulking and gaining excessive fat",
                "Not tracking weight gain rate",
                "Excessive cardio to stay lean",
            ]
            recs = [
                "Maintain or add a small surplus (~100-200 kcal)",
                "Continue progressive overload",
                "If bulking, cap at 0.5-1% BW/month",
            ]
        else:
            cat = TraineeCategory.SKINNY
            strategy = "bulk"
            summary = ("Very lean with little muscle. The biggest visible "
                       "changes of your life are ahead with a proper bulk.")
            pitfalls = [
                "Not eating enough (especially if naturally skinny)",
                "Not focusing on strength acquisition",
                "Adding too much cardio",
            ]
            recs = [
                "Surplus: ~2% BW/month (beginner), ~1% (intermediate)",
                "Compound lifts 3-4×/week",
                "Track calories — guessing leads to under-eating",
            ]

    return TraineeProfile(
        category=cat,
        strategy=strategy,
        estimated_body_fat=body_fat_pct,
        has_significant_muscle=has_muscle,
        summary=summary,
        pitfalls=pitfalls,
        recommendations=recs,
    )


# --------------------------------------------------------------------------- #
# Volume / tonnage                                                            #
# --------------------------------------------------------------------------- #
@dataclass
class WeeklyTonnage:
    sets: int
    reps: int
    load_kg: float
    total_volume_kg: float


def weekly_tonnage(sessions: List[dict]) -> WeeklyTonnage:
    """sessions: [{sets, reps, load_kg}, ...]"""
    s = sum(x.get("sets", 0) for x in sessions)
    r = sum(x.get("reps", 0) for x in sessions)
    L = sum(x.get("sets", 0) * x.get("reps", 0) * x.get("load_kg", 0)
            for x in sessions)
    return WeeklyTonnage(sets=s, reps=r, load_kg=round(L / max(r, 1), 1),
                         total_volume_kg=round(L, 1))


# --------------------------------------------------------------------------- #
# Micronutrient guidelines (rippedbody.com/micros/)                           #
# --------------------------------------------------------------------------- #
@dataclass
class MicronutrientTargets:
    """Daily micronutrient and hydration guidance.

    Source: rippedbody.com/micros/
    """
    fruit_cups: int
    veg_cups: int
    fibre_g: float
    water_guidance: List[str]


def micronutrient_targets(calories: float) -> MicronutrientTargets:
    """Calculate fruit/veg/fibre targets based on calorie intake.

    RippedBody guidelines:
      1200-2000 kcal → 2 cups fruit + 2 cups veg
      2000-3000 kcal → 3 cups each
      3000-4000 kcal → 4 cups each
      Fibre: 14 g per 1000 kcal
    """
    if calories < 2000:
        cups = 2
    elif calories < 3000:
        cups = 3
    else:
        cups = 4

    fibre = round(calories / 1000 * 14, 1)

    return MicronutrientTargets(
        fruit_cups=cups,
        veg_cups=cups,
        fibre_g=fibre,
        water_guidance=[
            "Aim to be peeing clear by noon.",
            "Have five clear urinations a day.",
            "Don't be dehydrated at the time of your workouts.",
            "Taper water toward the end of the day so you don't wake to pee.",
        ],
    )


# --------------------------------------------------------------------------- #
# Maximum muscular potential (rippedbody.com/maximum-muscular-potential/)     #
# --------------------------------------------------------------------------- #
@dataclass
class MuscularPotential:
    """Drug-free muscular potential estimates."""
    berkhan_stage_max_kg: float        # Berkhan model: (height_cm - 100)
    ffmi: float                        # Fat-Free Mass Index
    ffmi_category: str                 # below average / average / excellent / elite
    ceiling_ffmi: float                # Natural ceiling (~25)
    summary: str


def muscular_potential(
    height_cm: float, weight_kg: float, body_fat_pct: float,
) -> MuscularPotential:
    """Estimate drug-free muscular potential.

    Sources:
      • Berkhan model: (height_cm - 98~102) = stage-shredded max bodyweight kg
      • FFMI = fat-free mass / height_m² (Kouri et al. 1995)
      • Natural FFMI ceiling: ~25
    """
    # Berkhan model (midpoint of 98-102)
    berkhan_max = height_cm - 100

    # FFMI
    lean_mass = weight_kg * (1 - body_fat_pct / 100)
    height_m = height_cm / 100
    ffmi = lean_mass / (height_m * height_m)

    # FFMI normalized to 1.8m (for comparison)
    # Normalized FFMI = FFMI + 6.1 × (1.8 − height_m)
    normalized_ffmi = ffmi + 6.1 * (1.8 - height_m)

    if normalized_ffmi < 18:
        cat = "below average"
    elif normalized_ffmi < 20:
        cat = "average"
    elif normalized_ffmi < 22:
        cat = "above average"
    elif normalized_ffmi < 23:
        cat = "excellent"
    elif normalized_ffmi < 25:
        cat = "superior"
    elif normalized_ffmi < 26:
        cat = "suspicious (possible PED use)"
    else:
        cat = "highly suspicious (likely PED use)"

    return MuscularPotential(
        berkhan_stage_max_kg=round(berkhan_max, 1),
        ffmi=round(ffmi, 1),
        ffmi_category=cat,
        ceiling_ffmi=25.0,
        summary=(
            f"Berkhan model: your drug-free stage-shredded maximum (~5-6% BF) "
            f"is ~{berkhan_max:.0f} kg. Your current FFMI is {ffmi:.1f} "
            f"({cat}). The natural ceiling is ~25 FFMI."
        ),
    )


# --------------------------------------------------------------------------- #
# Body-fat self-estimate correction                                           #
# --------------------------------------------------------------------------- #
def correct_bf_estimate(bf_pct: float, is_self_estimate: bool = True) -> float:
    """Correct body-fat self-estimates.

    Source: rippedbody.com/body-fat-guide/
    'Most people underestimate their body-fat percentage. If you haven't
    cut down to see your abs before and you are trying to estimate how
    much fat you have to lose, add 50% to your estimate.'
    """
    if is_self_estimate:
        return round(bf_pct * 1.5, 1)
    return bf_pct
