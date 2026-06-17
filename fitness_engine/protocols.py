"""
protocols.py
============

Comprehensive plan-building protocols that cover every valid archetype/profile
combination without needing to hand-author 100k+ individual plans.

The implementation follows the source hierarchy used in the reference guide:

Training
--------
1. Adherence: choose a realistic frequency/session length first.
2. Volume, Intensity, Frequency: cap per-session muscle-group volume, preserve
   intensity during cuts, and spread work over the week.
3. Progression: linear -> double progression -> auto-regulated periodisation.
4. Exercise selection: movement-pattern coverage with equipment as a hard filter.
5. Rest/tempo/warm-up: goal-specific rest, controlled eccentrics, progressive
   ramp-up sets.

Nutrition
---------
1. Calories first.
2. Protein by body weight / lean mass, then fat minimum/preference.
3. Carbs fill the remainder unless a diet-mode constraint applies.
4. Micros/fibre/hydration minimums.
5. Supplements last.

These are protocol blueprints. The recommender turns them into concrete daily
exercise and meal selections using `exercise_plans.py` and `meal_plans.py`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .archetypes import (
    ActivityLevel, DietaryPreference, ExperienceLevel, GoalArchetype,
    SessionLength, Sex, TrainingEnvironment,
)
from .calculators import Macros, micronutrient_targets
from .decision_trees import (
    exercise_selection, intensity_scheme, periodisation, progression_rule,
    session_density, training_split, weekly_volume,
)


@dataclass
class ExercisePlanProtocol:
    profile_scope: str
    split: str
    days: List[str]
    movement_pattern_priority: List[str]
    weekly_sets_by_muscle: Dict[str, int]
    per_session_caps: Dict[str, int]
    primary_rep_range: str
    accessory_rep_range: str
    rir_targets: Dict[str, float]
    rest_seconds: int
    tempo: str
    progression: str
    periodisation: str
    deload_rule: str
    exercise_selection_rules: Dict[str, object]
    warmup_protocol: List[str]
    conditioning_protocol: List[str]
    adjustment_protocol: List[str]
    special_population_modifiers: List[str] = field(default_factory=list)


@dataclass
class MealPlanProtocol:
    profile_scope: str
    diet_mode: str
    calorie_protocol: List[str]
    macro_protocol: List[str]
    meal_timing_protocol: List[str]
    food_selection_protocol: List[str]
    micronutrient_protocol: List[str]
    hydration_protocol: List[str]
    adjustment_protocol: List[str]
    diet_specific_protocol: List[str]
    progress_tracking_protocol: List[str]


@dataclass
class CompleteProfileProtocol:
    exercise: ExercisePlanProtocol
    meal: MealPlanProtocol
    conflict_resolution: List[str]


MOVEMENT_PRIORITY = {
    GoalArchetype.STRENGTH: [
        "squat", "horizontal_push", "hinge", "horizontal_pull",
        "vertical_push", "vertical_pull", "core", "carry",
    ],
    GoalArchetype.MUSCLE_GAIN: [
        "squat", "hinge", "horizontal_push", "vertical_pull",
        "horizontal_pull", "vertical_push", "single_leg", "isolation", "core",
    ],
    GoalArchetype.FAT_LOSS: [
        "squat", "hinge", "horizontal_push", "horizontal_pull",
        "vertical_pull", "single_leg", "core", "carry",
    ],
    GoalArchetype.RECOMPOSITION: [
        "squat", "hinge", "horizontal_push", "vertical_pull",
        "horizontal_pull", "single_leg", "core", "carry",
    ],
    GoalArchetype.GENERAL_HEALTH: [
        "squat", "hinge", "push", "pull", "single_leg", "carry", "core",
    ],
}


def _per_session_caps(session: SessionLength, experience: ExperienceLevel) -> Dict[str, int]:
    base = {
        SessionLength.EXPRESS_30: 5,
        SessionLength.SHORT_45: 7,
        SessionLength.STANDARD_60: 9,
        SessionLength.EXTENDED_90: 11,
    }[session]
    if experience == ExperienceLevel.BEGINNER:
        base = min(base, 7)
    return {
        "max_sets_per_muscle_per_session": base,
        "max_hard_sets_total_per_session": {
            SessionLength.EXPRESS_30: 14,
            SessionLength.SHORT_45: 20,
            SessionLength.STANDARD_60: 26,
            SessionLength.EXTENDED_90: 34,
        }[session],
    }


def _conditioning(goal: GoalArchetype, days_per_week: int) -> List[str]:
    lifting_minutes = 45 * max(1, days_per_week)
    cap = int(lifting_minutes * 0.5)
    if goal == GoalArchetype.FAT_LOSS:
        return [
            f"Start with 45-90 min/week Zone-2 cardio, capped at {cap} min/week (< half lifting time).",
            "Prefer walking/cycling that does not impair lower-body recovery.",
            "Increase steps before adding hard conditioning; diet remains the main deficit lever.",
        ]
    if goal == GoalArchetype.GENERAL_HEALTH:
        return [
            "Accumulate 90-150 min/week easy-to-moderate aerobic work if recovery permits.",
            "Keep at least two resistance sessions weekly for muscle and bone health.",
        ]
    return [
        "Keep cardio optional and easy: 0-60 min/week Zone-2 or daily walking.",
        "Do not let conditioning reduce progressive overload performance.",
    ]


def _special_modifiers(age: int, sex: Sex, goal: GoalArchetype,
                       medical_flags: Optional[Dict[str, bool]] = None) -> List[str]:
    out: List[str] = []
    if age >= 46:
        out.extend([
            "Use longer warm-ups and slower load jumps; prioritize joint-friendly variations.",
            "Keep 1-3 reps in reserve on most work; add volume only if recovery markers are stable.",
        ])
    if age < 18:
        out.extend([
            "Adolescent trainees should focus on technique over load; avoid max-effort 1RM testing.",
            "Prioritise sleep, school, and social commitments over training volume.",
        ])
    if sex == Sex.FEMALE:
        out.append("Interpret scale trends with menstrual-cycle water fluctuations in mind when applicable.")
    if goal == GoalArchetype.FAT_LOSS:
        out.append("During the final third of a cut, preserve load/intensity and reduce volume before reducing effort quality.")

    # Medical-flag modifiers. The medical_flags dict is provided by the
    # caller (the recommender passes ``ClientProfile.medical_flags``). See
    # audit finding F64.
    medical_flags = medical_flags or {}
    if medical_flags.get("pregnant_or_recent_postpartum"):
        out.extend([
            "Pregnancy/post-partum: avoid supine exercises after the first trimester; "
            "avoid heavy lifting, Valsalva, and contact sports; consult the OB-GYN before any plan.",
            "Prioritise pelvic-floor and core stability work; walking and swimming are excellent.",
        ])
    if medical_flags.get("recent_surgery"):
        out.append(
            "Recent surgery: obtain surgeon clearance before starting; avoid loading the affected "
            "tissue for the full healing window; start with ROM and isometric work."
        )
    if medical_flags.get("diagnosed_eating_disorder"):
        out.append(
            "Eating-disorder history: de-emphasise calorie/macro tracking; work with a registered "
            "dietitian and therapist; consider habit-based rather than numbers-based guidance."
        )
    if medical_flags.get("cardiac_condition") or medical_flags.get("unexplained_chest_pain_or_fainting"):
        out.append(
            "Cardiac flag: obtain cardiologist clearance before starting; avoid Valsalva, max-effort "
            "lifts, and high-intensity intervals until cleared."
        )
    return out


def build_exercise_plan_protocol(
    goal: GoalArchetype, experience: ExperienceLevel, days_per_week: int,
    session_length: SessionLength, environment: TrainingEnvironment,
    age: int = 30, sex: Sex = Sex.MALE,
    medical_flags: Optional[Dict[str, bool]] = None,
) -> ExercisePlanProtocol:
    split = training_split(goal, experience, days_per_week)
    vol = weekly_volume(goal, experience, days_per_week)
    intensity = intensity_scheme(goal, experience)
    density = session_density(goal, session_length)
    prog = progression_rule(goal, experience)
    period = periodisation(goal, experience)
    rule = exercise_selection(goal, environment)

    return ExercisePlanProtocol(
        profile_scope=(
            f"goal={goal.value}; experience={experience.value}; days={days_per_week}; "
            f"session={session_length.value}; environment={environment.value}"
        ),
        split=split.name,
        days=split.days,
        movement_pattern_priority=MOVEMENT_PRIORITY[goal],
        weekly_sets_by_muscle=vol.per_muscle_group,
        per_session_caps=_per_session_caps(session_length, experience),
        primary_rep_range=intensity.primary_reps,
        accessory_rep_range=intensity.accessory_reps,
        rir_targets={"primary": intensity.primary_rir, "accessory": intensity.accessory_rir},
        rest_seconds=density.rest_seconds,
        tempo="Controlled eccentric (~2-3 s), stable pause where needed, forceful concentric without form breakdown.",
        progression=prog.rule,
        periodisation=period.scheme,
        deload_rule=f"Deload every {period.deload_every} weeks or earlier if performance, sleep, soreness, or joint pain trends deteriorate.",
        exercise_selection_rules={
            "include": rule.include,
            "exclude": rule.exclude,
            "substitute_map": rule.substitute_map,
            "hard_filter": "Never prescribe exercises requiring unavailable equipment.",
        },
        warmup_protocol=[
            "5-10 min general warm-up until warm, not fatigued.",
            "Dynamic mobility for the first major pattern of the day.",
            "Ramp-up sets: empty/light x8-10, ~50% x5, ~70% x3, ~85% x1-2 before work sets.",
        ],
        conditioning_protocol=_conditioning(goal, days_per_week),
        adjustment_protocol=[
            "If target muscles receive <2 exposures/week and recovery is good, redistribute volume before adding sets.",
            "If a session exceeds the set cap, move accessory work to another day or trim isolation work first.",
            "If progress stalls: check sleep, calories, protein, RIR accuracy, frequency, technique, pain, then volume.",
        ],
        special_population_modifiers=_special_modifiers(age, sex, goal, medical_flags),
    )


DIET_MODE_NOTES = {
    DietaryPreference.BALANCED: [
        "No exclusions; aim for a mix of lean protein, whole grains, vegetables, fruit, and healthy fats.",
        "Use the macro split as the primary guide; food choice is flexible within the macro budget.",
    ],
    DietaryPreference.OMNIVORE: [
        "No specific exclusions; include meat, fish, eggs, dairy, grains, and produce as preferred.",
        "Prioritise whole foods over processed; treat the macro split as the primary guide.",
    ],
    DietaryPreference.VEGETARIAN: [
        "Combine grains and legumes (rice + beans, hummus + pita) for complete protein.",
        "Include eggs and dairy for B12, calcium, and high-quality protein.",
        "Iron from plant sources is less well absorbed; pair with vitamin C-rich foods.",
    ],
    DietaryPreference.PESCATARIAN: [
        "Aim for 2-3 fish servings per week (salmon, sardines, mackerel) for EPA/DHA.",
        "Combine with vegetarian protein (legumes, eggs, dairy) on non-fish days.",
    ],
    DietaryPreference.POLLO_PESCATARIAN: [
        "Rotate poultry, fish, eggs, and dairy for protein variety.",
        "Limit red-meat-style recipes; this mode is closest to a Mediterranean pattern.",
    ],
    DietaryPreference.KETO: [
        "Keep carbs generally <50 g/day; maintain protein and set fats as the remaining calories.",
        "Use as a preference/tolerance mode, not because ketosis is superior for fat loss when calories are matched.",
        "Run a 4-week trial and rate mood, energy, hunger, and training performance daily.",
        "Supplement sodium, magnesium, and potassium to offset electrolyte losses.",
    ],
    DietaryPreference.LOW_CARB: [
        "Lower carbs only as far as training performance and adherence remain acceptable.",
        "Prefer vegetables, lean protein, and fats from whole-food sources.",
    ],
    DietaryPreference.MEDITERRANEAN: [
        "Emphasize fish/seafood, legumes, vegetables, fruit, whole grains, olive oil, yogurt, nuts, and herbs.",
        "This pattern is associated with cardiovascular and longevity benefits in observational research.",
    ],
    DietaryPreference.GLUTEN_FREE: [
        "Use gluten-free grains/starches (rice, quinoa, potato, buckwheat); confirm sauces and packaged foods are gluten-free if medically required.",
        "If avoiding gluten for non-medical reasons, consider whether whole-grain wheat has benefits you'd be giving up.",
    ],
    DietaryPreference.PALEO: [
        "Emphasize meat/fish/eggs, fruit, vegetables, tubers, nuts, and oils; ensure carbs are sufficient for training.",
        "Legumes and whole grains are excluded by the strict definition; many people find a 'practical paleo' approach with occasional legumes is more sustainable.",
    ],
    DietaryPreference.HIGH_PROTEIN: [
        "Protein is already set first; avoid pushing protein so high that carbs/fats impair training or adherence.",
        "≥2.0 g/kg is appropriate during a cut or for older adults; >3 g/kg has no clear additional benefit.",
    ],
    DietaryPreference.VEGAN: [
        "Use higher protein targets and combine plant proteins; consider pea/rice protein blends.",
        "Supplement B12; consider D3, algae omega-3, calcium, iron, zinc, and creatine as needed.",
        "Iron from plant sources is less well absorbed; pair with vitamin C-rich foods and avoid coffee/tea around meals.",
    ],
}


def build_meal_plan_protocol(
    goal: GoalArchetype, diet: DietaryPreference, calories: float,
    macros: Macros, meals_per_day: int, activity: ActivityLevel,
) -> MealPlanProtocol:
    micros = micronutrient_targets(calories)
    meal_count = max(3, min(5, meals_per_day))
    if goal == GoalArchetype.FAT_LOSS:
        calorie_notes = [
            "Create the deficit primarily via food intake; use cardio sparingly.",
            "Use body-fat-aware loss rates and Alpert's max-deficit cap when BF% is available.",
            "Assess using weekly-average weight after ignoring the first week of water/glycogen changes.",
        ]
    elif goal == GoalArchetype.MUSCLE_GAIN:
        calorie_notes = [
            "Use an experience-tiered surplus; faster gain rates mostly add fat for trained lifters.",
            "Expect initial scale jump from glycogen/gut content; judge the trend after several weeks.",
        ]
    elif goal == GoalArchetype.RECOMPOSITION:
        calorie_notes = [
            "Start near maintenance or a small deficit/surplus depending on body-fat and experience.",
            "Track photos, measurements, and strength because scale change may be slow.",
        ]
    else:
        calorie_notes = ["Start at maintenance and adjust from trend data and adherence."]

    return MealPlanProtocol(
        profile_scope=f"goal={goal.value}; diet={diet.value}; calories={calories:.0f}; activity={activity.value}",
        diet_mode=diet.value,
        calorie_protocol=calorie_notes,
        macro_protocol=[
            f"Daily target: {calories:.0f} kcal, {macros.protein_g:.0f} g protein, {macros.carbs_g:.0f} g carbs, {macros.fat_g:.0f} g fat.",
            "Set protein first; do not use fixed macro ratios as the target.",
            "Keep fat above the minimum floor; use carbs as the main performance/adherence lever unless diet mode constrains carbs.",
            "When adjusting calories, preserve protein and change carbs/fats at an approximate 1:1 to 2:1 calorie ratio.",
        ],
        meal_timing_protocol=[
            f"Use {meal_count} meals/day unless adherence is better with a different schedule.",
            "Distribute protein across 3-5 feedings; include a protein serving near training when convenient.",
            "Place more carbs pre/post workout if it improves performance; timing is secondary to daily totals.",
        ],
        food_selection_protocol=[
            "Build each meal from: lean protein or appropriate plant protein, carb/fat source per macro needs, and fruit/vegetables.",
            "Use cuisine preference for adherence; allergen filtering is a hard constraint.",
            "Prefer whole foods most of the time, but allow flexible choices that fit calories and macros.",
        ],
        micronutrient_protocol=[
            f"Fruit: {micros.fruit_cups} cups/day; vegetables: {micros.veg_cups} cups/day.",
            f"Fiber target: about {micros.fibre_g:.0f} g/day; adjust if constipation or loose stools occur.",
            "Do not treat multivitamins as a substitute for fruit, vegetables, and varied whole foods.",
        ],
        hydration_protocol=[
            "Aim to be peeing clear by noon and have roughly five clear urinations/day.",
            "Do not begin training dehydrated; taper fluids late if sleep is disrupted.",
        ],
        adjustment_protocol=[
            "Before cutting calories: check logging, hunger management, food environment, stress, sleep, steps, and patience window.",
            "Cut adjustment last resort: ~200-250 kcal/day, then wait 3-4 weeks.",
            "Bulk adjustment last resort: +~5% calories or 150-200 kcal/day, then wait ~5 weeks.",
            "Use adaptive TDEE when 2-4+ weeks of intake and weight logs exist.",
            "After extended cuts, reverse diet using +50/+100/+150 kcal weekly depending on risk tolerance and diet duration.",
        ],
        diet_specific_protocol=DIET_MODE_NOTES.get(diet, ["No special diet constraints beyond calorie, macro, and micronutrient targets."]),
        progress_tracking_protocol=[
            "Daily weigh-ins, weekly averages, first week ignored after diet changes.",
            "Weekly 9-point measurements: chest, left/right arm, left/right thigh, navel, above navel, below navel.",
            "Monthly progress photos in consistent lighting/poses.",
            "Do not use short-term BF% readings as progress metrics.",
        ],
    )


def build_complete_profile_protocol(
    goal: GoalArchetype, experience: ExperienceLevel, days_per_week: int,
    session_length: SessionLength, environment: TrainingEnvironment,
    diet: DietaryPreference, calories: float, macros: Macros,
    meals_per_day: int, activity: ActivityLevel, age: int = 30,
    sex: Sex = Sex.MALE,
    medical_flags: Optional[Dict[str, bool]] = None,
) -> CompleteProfileProtocol:
    return CompleteProfileProtocol(
        exercise=build_exercise_plan_protocol(goal, experience, days_per_week, session_length, environment, age, sex, medical_flags),
        meal=build_meal_plan_protocol(goal, diet, calories, macros, meals_per_day, activity),
        conflict_resolution=[
            "If body composition suggests cut/bulk/recomp differs from the selected goal, flag the mismatch and ask for a deliberate phase choice.",
            "Adherence constraints override theoretical optimality: choose the plan the client can repeat for 8-12 weeks.",
            "Medical symptoms, diagnosed conditions, pregnancy, eating-disorder risk, or very low calorie targets require professional oversight.",
        ],
    )
