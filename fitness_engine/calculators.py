"""
calculators.py
==============

All numerical engines used to translate raw client data into actionable
metrics. Every calculator returns a typed result object so that downstream
consumers can introspect, log and unit-test individual computations.

Included:
  * Body composition (BMI, body-fat Navy / BMI-method, lean mass)
  * Energy expenditure (BMR via Mifflin-St Jeor, Harris-Benedict,
    Katch-McArdle; TDEE multipliers; calorie target by goal)
  * Macronutrient partitioning
  * Hydration requirement
  * Strength estimation (1-Rep-Max via Epley, Brzycki, Lander)
  * Cardiovascular training zones (Karvonen, %HRmax)
  * Protein floor, fat floor, carb target
  * Volume load, intensity, weekly tonnage

Each calculator is independently tested and pure-functional.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
from typing import List, Optional

from .archetypes import (
    ActivityLevel, AgeGroup, GoalArchetype, Sex, Somatotype,
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


@dataclass
class EnergyExpenditure:
    bmr_mifflin: float
    bmr_harris: float
    bmr_katch: Optional[float]
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


def body_fat_navy(
    sex: Sex, height_cm: float, neck_cm: float,
    waist_cm: float, hip_cm: Optional[float] = None,
) -> float:
    """U.S. Navy body-fat formula. Hip required for females."""
    if sex == Sex.MALE:
        bf = 86.010 * (waist_cm - neck_cm) / height_cm - 70.041 * 0.393700787  # inches->cm
        # Convert to a percentage form directly via metric variant:
        bf = 495 / (1.0324 - 0.19077 * (waist_cm - neck_cm) / height_cm
                    + 0.15456 * (waist_cm / height_cm)) - 450
        # Actually use the canonical metric Navy formula:
        # men: 495 / (1.0324 - 0.19077·log10(waist-neck) + 0.15456·log10(height)) - 450
        import math
        bf = (495 / (1.0324 - 0.19077 * math.log10(waist_cm - neck_cm)
                     + 0.15456 * math.log10(height_cm))) - 450
    else:
        if hip_cm is None:
            raise ValueError("hip_cm required for female Navy BF estimate")
        import math
        bf = (495 / (1.29579 - 0.35004 * math.log10(waist_cm + hip_cm - neck_cm)
                     + 0.22100 * math.log10(height_cm))) - 450
    return round(max(2.0, min(bf, 60.0)), 1)


def body_fat_bmi_method(b: float, age: int, sex: Sex) -> float:
    """Deurenberg BF% estimate from BMI, age and sex."""
    sex_coef = 1.0 if sex == Sex.MALE else 0.0
    bf = (1.20 * b) + (0.23 * age) - (10.8 * sex_coef) - 5.4
    return round(max(2.0, min(bf, 60.0)), 1)


def body_composition(
    weight_kg: float, height_cm: float, age: int, sex: Sex,
    bf_pct: Optional[float] = None,
    waist_cm: Optional[float] = None, neck_cm: Optional[float] = None,
    hip_cm: Optional[float] = None,
) -> BodyComposition:
    """Compute composite body-composition metrics."""
    b = bmi(weight_kg, height_cm)
    if bf_pct is None and waist_cm and neck_cm:
        bf = body_fat_navy(sex, height_cm, neck_cm, waist_cm, hip_cm)
    else:
        bf = bf_pct if bf_pct is not None else body_fat_bmi_method(b, age, sex)

    lean = round(weight_kg * (1 - bf / 100.0), 2)
    fat = round(weight_kg - lean, 2)
    return BodyComposition(
        bmi=round(b, 2),
        bmi_category=bmi_category(b).value,
        body_fat_pct=bf,
        lean_mass_kg=lean,
        fat_mass_kg=fat,
    )


# --------------------------------------------------------------------------- #
# Energy expenditure                                                          #
# --------------------------------------------------------------------------- #
ACTIVITY_MULTIPLIERS = {
    ActivityLevel.SEDENTARY: 1.2,
    ActivityLevel.LIGHT: 1.375,
    ActivityLevel.MODERATE: 1.55,
    ActivityLevel.VERY_ACTIVE: 1.725,
    ActivityLevel.ATHLETE: 1.9,
}


def bmr_mifflin(weight_kg: float, height_cm: float, age: int, sex: Sex) -> float:
    """Mifflin-St Jeor BMR (kcal/day) — modern gold-standard."""
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return base + 5 if sex == Sex.MALE else base - 161


def bmr_harris(weight_kg: float, height_cm: float, age: int, sex: Sex) -> float:
    """Revised Harris-Benedict BMR."""
    if sex == Sex.MALE:
        return 88.362 + (13.397 * weight_kg) + (4.799 * height_cm) - (5.677 * age)
    return 447.593 + (9.247 * weight_kg) + (3.098 * height_cm) - (4.330 * age)


def bmr_katch(weight_kg: float, lean_mass_kg: float) -> float:
    """Katch-McArdle BMR (requires lean body mass)."""
    return 370 + (21.6 * lean_mass_kg)


def tdee(bmr: float, level: ActivityLevel) -> float:
    return bmr * ACTIVITY_MULTIPLIERS[level]


def calorie_target(
    tdee_value: float, goal: GoalArchetype,
    deficit_pct: float = 0.20, surplus_pct: float = 0.12,
) -> Tuple[float, dict]:
    """Goal-driven calorie target with traceable breakdown."""
    breakdown = {"tdee": round(tdee_value, 1)}
    if goal == GoalArchetype.FAT_LOSS:
        target = tdee_value * (1 - deficit_pct)
        breakdown.update({"mode": "fat_loss", "deficit_pct": deficit_pct})
    elif goal == GoalArchetype.MUSCLE_GAIN:
        target = tdee_value * (1 + surplus_pct)
        breakdown.update({"mode": "lean_gain", "surplus_pct": surplus_pct})
    elif goal == GoalArchetype.RECOMPOSITION:
        target = tdee_value * 1.0           # isocaloric
        breakdown.update({"mode": "recomp", "delta_pct": 0.0})
    elif goal == GoalArchetype.STRENGTH:
        target = tdee_value * 1.05          # small surplus
        breakdown.update({"mode": "strength", "delta_pct": 0.05})
    elif goal == GoalArchetype.ENDURANCE:
        target = tdee_value * 1.10          # endurance carb demand
        breakdown.update({"mode": "endurance", "delta_pct": 0.10})
    elif goal == GoalArchetype.ATHLETIC_PERFORMANCE:
        target = tdee_value * 1.12
        breakdown.update({"mode": "athletic", "delta_pct": 0.12})
    elif goal == GoalArchetype.GENERAL_HEALTH:
        target = tdee_value * 1.0
        breakdown.update({"mode": "maintenance", "delta_pct": 0.0})
    elif goal == GoalArchetype.REHABILITATION:
        target = tdee_value * 1.05          # slight surplus to support recovery
        breakdown.update({"mode": "rehab", "delta_pct": 0.05})
    else:
        target = tdee_value
        breakdown.update({"mode": "default", "delta_pct": 0.0})
    breakdown["target"] = round(target, 1)
    return round(target, 1), breakdown


def energy_expenditure(
    weight_kg: float, height_cm: float, age: int, sex: Sex,
    activity: ActivityLevel, goal: GoalArchetype,
    lean_mass_kg: Optional[float] = None,
    deficit_pct: float = 0.20, surplus_pct: float = 0.12,
) -> EnergyExpenditure:
    """Compute BMR × TDEE × target in one pass."""
    mif = bmr_mifflin(weight_kg, height_cm, age, sex)
    har = bmr_harris(weight_kg, height_cm, age, sex)
    kat = bmr_katch(weight_kg, lean_mass_kg) if lean_mass_kg else None
    # Use Mifflin as primary TDEE basis
    tdee_v = tdee(mif, activity)
    target, breakdown = calorie_target(tdee_v, goal, deficit_pct, surplus_pct)
    return EnergyExpenditure(
        bmr_mifflin=round(mif, 1),
        bmr_harris=round(har, 1),
        bmr_katch=round(kat, 1) if kat else None,
        tdee=round(tdee_v, 1),
        activity_multiplier=ACTIVITY_MULTIPLIERS[activity],
        calorie_target=target,
        calorie_target_breakdown=breakdown,
    )


# --------------------------------------------------------------------------- #
# Macronutrient partitioning                                                  #
# --------------------------------------------------------------------------- #
PROTEIN_G_PER_KG = {
    GoalArchetype.FAT_LOSS: 2.0,
    GoalArchetype.MUSCLE_GAIN: 1.9,
    GoalArchetype.RECOMPOSITION: 1.9,
    GoalArchetype.STRENGTH: 1.8,
    GoalArchetype.ENDURANCE: 1.6,
    GoalArchetype.ATHLETIC_PERFORMANCE: 1.8,
    GoalArchetype.GENERAL_HEALTH: 1.4,
    GoalArchetype.REHABILITATION: 1.6,
}

FAT_G_FLOOR = {
    Sex.MALE: 0.8,
    Sex.FEMALE: 0.9,
}

CARB_G_PER_KG_ENDURANCE = 5.0   # high-carb zones
CARB_G_PER_KG_DEFAULT = 3.5


def macros_for(
    calories: float, weight_kg: float, lean_mass_kg: Optional[float],
    goal: GoalArchetype, sex: Sex,
    somatotype: Somatotype, dietary_pref,  # DietaryPreference
) -> Macros:
    """Compute macro split. Somatotype biases carb vs fat; goal biases
    protein. Diet preference adjusts fat quality / carb floor."""
    # Protein
    p_g_per_kg = PROTEIN_G_PER_KG[goal]
    protein_g = round(p_g_per_kg * weight_kg, 1)

    # Fat floor
    fat_floor_g = FAT_G_FLOOR[sex] * weight_kg
    # Somatotype modifier:
    if somatotype == Somatotype.ECTOMORPH:
        fat_g = max(fat_floor_g, calories * 0.27 / 9)   # a bit more fat
    elif somatotype == Somatotype.ENDOMORPH:
        fat_g = fat_floor_g
    else:
        fat_g = max(fat_floor_g, calories * 0.25 / 9)
    # Diet preference adjustment
    from .archetypes import DietaryPreference
    if dietary_pref == DietaryPreference.KETO:
        fat_g = calories * 0.70 / 9
    elif dietary_pref == DietaryPreference.MEDITERRANEAN:
        fat_g = max(fat_g, calories * 0.30 / 9)
    fat_g = round(min(fat_g, calories * 0.45 / 9), 1)

    # Protein + fat calories
    pf_cal = protein_g * 4 + fat_g * 9
    carb_cal = max(0.0, calories - pf_cal)
    carb_g = round(carb_cal / 4, 1)

    # Keto overrides
    if dietary_pref == DietaryPreference.KETO:
        carb_g = round(min(carb_g, 50), 1)   # hard ceiling at 50 g
        # rebalance fat
        fat_g = round((calories - protein_g * 4 - carb_g * 4) / 9, 1)

    total = protein_g + carb_g + fat_g
    return Macros(
        calories=round(calories, 1),
        protein_g=protein_g,
        carbs_g=carb_g,
        fat_g=fat_g,
        protein_pct=round(protein_g * 4 / calories * 100, 1),
        carbs_pct=round(carb_g * 4 / calories * 100, 1),
        fat_pct=round(fat_g * 9 / calories * 100, 1),
        rationale=(
            f"Protein {p_g_per_kg} g/kg driven by goal={goal.value}; "
            f"fat floor {FAT_G_FLOOR[sex]} g/kg for hormonal health; "
            f"carbs as remainder."
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
def one_rep_max(weight: float, reps: int) -> StrengthEstimate:
    """Three classic 1RM estimates + average + percent-of-1RM table."""
    if reps < 1:
        raise ValueError("reps must be >= 1")
    epley = weight * (1 + reps / 30.0)
    brzycki = weight * 36.0 / (37.0 - reps)
    lander = (100 * weight) / (101.3 - 2.67123 * reps)
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
# Somatotype heuristic                                                        #
# --------------------------------------------------------------------------- #
def infer_somatotype(
    weight_kg: float, height_cm: float, age: int, sex: Sex,
    body_fat_pct: Optional[float] = None,
    wrist_cm: Optional[float] = None,
) -> Somatotype:
    """Cheap heuristic using frame size + adiposity. Falls back to MIXED."""
    b = bmi(weight_kg, height_cm)
    bf = body_fat_pct if body_fat_pct is not None else body_fat_bmi_method(b, age, sex)
    if sex == Sex.MALE:
        if bf <= 14 and b <= 23:
            return Somatotype.ECTOMORPH
        if bf >= 22 or b >= 28:
            return Somatotype.ENDOMORPH
        return Somatotype.MESOMORPH
    else:
        if bf <= 20 and b <= 22:
            return Somatotype.ECTOMORPH
        if bf >= 30 or b >= 28:
            return Somatotype.ENDOMORPH
        return Somatotype.MESOMORPH


# --------------------------------------------------------------------------- #
# Age group inference                                                         #
# --------------------------------------------------------------------------- #
def infer_age_group(age: int) -> AgeGroup:
    if age < 18:  return AgeGroup.YOUTH
    if age <= 25: return AgeGroup.YOUNG_ADULT
    if age <= 40: return AgeGroup.ADULT
    if age <= 55: return AgeGroup.MIDDLE
    if age <= 70: return AgeGroup.SENIOR
    return AgeGroup.ELDER


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
