"""Meal-plan quality audit helpers."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List

from .meal_plans import DIET_COMPATIBILITY, MealItem
from .seven_day_meal_planner import SevenDayMealPlan


@dataclass(frozen=True)
class MealPlanAudit:
    score: int
    grade: str
    summary: str
    checks: Dict[str, str]
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


def _source(meal: MealItem) -> str:
    for t in meal.tags:
        if t.startswith("source:"):
            return t.split(":", 1)[1]
    return "internal"


def _confidence(meal: MealItem) -> str:
    for t in meal.tags:
        if t.startswith("confidence:"):
            return t.split(":", 1)[1]
    return "curated"


def _is_side_or_booster(meal: MealItem) -> bool:
    """Return True if ``meal`` is a side dish, protein booster, or fibre side
    (legitimate repeats that should be exempt from the variety penalty).

    Detection is by tag (``role:side`` / ``role:booster``) rather than by
    name, because the planner creates items with their original recipe names
    and never renames them to "Fruit and fibrous vegetable side" etc. The
    previous hardcoded name list never matched real plan output. See audit
    finding F55.

    A meal is also treated as a side if it is in the ``snack`` slot with
    fewer than 300 calories — these are typically the planner's protein or
    fibre boosters.
    """
    if any(t.startswith("role:") for t in meal.tags):
        return True
    if meal.slot in {"snack", "snack_1", "snack_2"} and meal.calories < 300:
        return True
    return False


# Word-boundary patterns for slot-sanity checks. The previous implementation
# used substring matching, which produced false positives like "bar" matching
# "Barbacoa", "Larb", and "Burger". See audit finding F56.
_SLOT_SANITY_PATTERNS = [
    re.compile(r"\b" + p + r"\b", re.IGNORECASE)
    for p in (
        "cookie", "brownie", "muffin", "cupcake", "donut", "doughnut",
        "shake", "smoothie", "truffle", "pudding", "ice cream",
        "cake", "tart", "pie",
    )
]


def audit_7_day_meal_plan(plan: SevenDayMealPlan, protein_tolerance: float = 0.15) -> MealPlanAudit:
    issues: List[str] = []
    recs: List[str] = []
    checks: Dict[str, str] = {}
    score = 100

    # Completeness.
    if len(plan.days) != 7:
        issues.append(f"Expected 7 days, found {len(plan.days)}.")
        score -= 20
    missing_meals = [(d.name, len(d.meals)) for d in plan.days if len(d.meals) < 3]
    if missing_meals:
        issues.append(f"Some days have fewer than 3 meals: {missing_meals}.")
        score -= 10
    checks["structure"] = "pass" if not missing_meals and len(plan.days) == 7 else "warn"

    # Calories and protein.
    calorie_failures = []
    protein_failures = []
    fibre_low = []
    for day, quality in zip(plan.days, plan.quality_by_day):
        if abs(quality.calorie_error_pct) > 5:
            calorie_failures.append((day.name, quality.calorie_error_pct))
        if quality.protein_error_g < -(plan.target_macros.protein_g * protein_tolerance):
            protein_failures.append((day.name, quality.protein_error_g))
        if quality.fibre_g < plan.micronutrients.fibre_g * 0.6:
            fibre_low.append((day.name, quality.fibre_g))
    if calorie_failures:
        issues.append(f"Calorie misses beyond ±5%: {calorie_failures}.")
        score -= 20
    if protein_failures:
        issues.append(f"Protein misses beyond tolerance: {protein_failures}.")
        score -= 15
    if fibre_low:
        issues.append(f"Known fibre is low on some days: {fibre_low}. Note many imported recipes lack fibre data.")
        recs.append("Add explicit fruit/vegetable/legume sides on low-fibre days and improve recipe fiber metadata.")
        score -= 5
    # Separate data-quality flag: a day with fibre_g == 0 almost certainly
    # means the imported recipe lacks fibre metadata rather than the meal
    # genuinely containing no fibre. Previously, the truthy guard
    # `if quality.fibre_g and ...` silently skipped these days, masking both
    # the data gap and the legitimate low-fibre warning.
    zero_fibre_days = [(d.name, q.fibre_g) for d, q in zip(plan.days, plan.quality_by_day) if q.fibre_g == 0]
    if zero_fibre_days:
        issues.append(
            f"Days with zero fibre data (likely missing recipe metadata, not a true zero-fibre meal): "
            f"{zero_fibre_days}."
        )
        recs.append("Backfill fibre_g for imported recipes; until then, treat these days as low-confidence.")
        score -= 3
    checks["calories"] = "pass" if not calorie_failures else "fail"
    checks["protein"] = "pass" if not protein_failures else "warn"
    checks["fibre"] = "pass" if not fibre_low and not zero_fibre_days else "warn"

    # Diet compatibility.
    acceptable = DIET_COMPATIBILITY.get(plan.diet, {plan.diet.value})
    incompatible = []
    for day in plan.days:
        for meal in day.meals:
            if not (set(meal.tags) & acceptable):
                incompatible.append((day.name, meal.name, meal.tags))
    if incompatible:
        issues.append(f"Diet-incompatible meals found: {incompatible[:5]}.")
        score -= 25
    checks["diet_compatibility"] = "pass" if not incompatible else "fail"

    # Variety — exempt side dishes and boosters (detected by tag/properties,
    # not by name). See audit F55.
    # Build a parallel list of (name, is_exempt) so we count repeats only for
    # main-meal items.
    name_exempt = [(m.name, _is_side_or_booster(m)) for d in plan.days for m in d.meals]
    repeat_names = sorted({
        name for name, exempt in name_exempt
        if not exempt and sum(1 for n, e in name_exempt if n == name and not e) > 1
    })
    if repeat_names:
        issues.append(f"Repeated main-meal names: {repeat_names}.")
        recs.append("Increase repeat penalty or expand compatible recipe pool for this diet mode.")
        score -= min(10, len(repeat_names) * 2)
    checks["variety"] = "pass" if not repeat_names else "warn"

    # Source/macro confidence.
    confidences = [_confidence(m) for d in plan.days for m in d.meals]
    # The planner emits {"verified", "curated", "parsed", "estimated", "missing"}.
    # 'estimated' means calories were recalculated from macros — the macros
    # themselves are still reliable. Only penalize 'missing' (no macro data).
    missing_conf = [c for c in confidences if c == "missing"]
    if missing_conf:
        issues.append(f"Some meals have missing macro confidence: {missing_conf[:5]}.")
        score -= 15
    est_count = sum(1 for c in confidences if c == "estimated")
    if est_count > len(confidences) * 0.5:
        issues.append(f"Majority of meals ({est_count}/{len(confidences)}) have estimated macros.")
        score -= 5
    checks["macro_confidence"] = "pass" if not missing_conf else "fail"

    # Practicality: extreme portion scaling.
    # Threshold aligned with meal_plans._scale_meal ([0.25, 3.0]) and
    # seven_day_meal_planner._scale ([0.20, 5.0]) — the auditor's [0.35, 2.5]
    # is now documented as the "advisable" range (inside both scalers' allowed
    # ranges), with anything outside flagged as warn. See P1 #10.
    extreme = [(d.name, m.name, m.portion_scale) for d in plan.days for m in d.meals if m.portion_scale < 0.35 or m.portion_scale > 2.5]
    if extreme:
        issues.append(f"Extreme portion scaling found: {extreme[:6]}.")
        recs.append("Prefer recipes closer to slot targets or add smaller side items instead of scaling entire recipes.")
        score -= 8
    checks["portion_scaling"] = "pass" if not extreme else "warn"

    # Food-group coverage check (P1 #11): every day should include at least
    # one protein source, one vegetable, and one fruit OR whole grain. This
    # is a basic dietary-quality signal that was missing entirely.
    # Detection is heuristic — we look at ingredient names because the
    # recipe DB does not have a "food_group" field.
    _PROTEIN_HINTS = ("chicken", "beef", "pork", "turkey", "fish", "salmon",
                      "tuna", "egg", "tofu", "tempeh", "beans", "lentils",
                      "chickpea", "yogurt", "yoghurt", "cottage", "whey",
                      "shrimp", "prawn", "duck", "lamb", "veal", "bacon",
                      "sausage", "ham", "protein")
    _VEG_HINTS = ("spinach", "broccoli", "kale", "lettuce", "tomato",
                  "carrot", "pepper", "onion", "garlic", "cucumber",
                  "zucchini", "courgette", "eggplant", "aubergine",
                  "mushroom", "cabbage", "cauliflower", "asparagus",
                  "green bean", "snap pea", "celery")
    _FRUIT_OR_GRAIN_HINTS = ("apple", "banana", "berry", "berries", "orange",
                              "rice", "oat", "quinoa", "bread", "pasta",
                              "wheat", "barley", "couscous", "tortilla",
                              "potato", "sweet potato", "corn", "fruit")
    food_group_failures = []
    for day in plan.days:
        ing_text = " ".join(
            ing.lower() for m in day.meals for ing in m.ingredients
        )
        has_protein = any(h in ing_text for h in _PROTEIN_HINTS)
        has_veg = any(h in ing_text for h in _VEG_HINTS)
        has_fruit_or_grain = any(h in ing_text for h in _FRUIT_OR_GRAIN_HINTS)
        if not (has_protein and has_veg and has_fruit_or_grain):
            missing = []
            if not has_protein:
                missing.append("protein")
            if not has_veg:
                missing.append("vegetable")
            if not has_fruit_or_grain:
                missing.append("fruit/whole-grain")
            food_group_failures.append((day.name, missing))
    if food_group_failures:
        issues.append(
            f"Days missing basic food groups (protein/veg/fruit-or-grain): "
            f"{food_group_failures[:5]}."
        )
        recs.append(
            "Add explicit vegetables, fruit, or whole grains to days flagged "
            "above. The check is heuristic (ingredient-name substring) and "
            "may miss recipes that use compound ingredient names."
        )
        score -= min(10, len(food_group_failures) * 2)
    checks["food_groups"] = "pass" if not food_group_failures else "warn"

    # Slot sanity: flag desserts/snacks in main-meal slots using word-boundary
    # regex matching. Only flag if the meal is also low-calorie (<300 kcal) —
    # a "protein shake" with 500+ kcal is a legitimate meal replacement.
    # See audit F56 + recipe cleanup.
    slot_mismatch = []
    for day in plan.days:
        for meal in day.meals:
            if meal.slot in {"lunch", "dinner"} and meal.calories < 300:
                name_l = meal.name.lower()
                if any(p.search(name_l) for p in _SLOT_SANITY_PATTERNS):
                    slot_mismatch.append((day.name, meal.slot, meal.name))
    if slot_mismatch:
        issues.append(f"Likely snack/dessert recipes used as main meals: {slot_mismatch[:6]}.")
        score -= 10
    checks["slot_sanity"] = "pass" if not slot_mismatch else "warn"

    # Source diversity is not mandatory but useful for this task.
    source_counts: Dict[str, int] = {}
    for day in plan.days:
        for meal in day.meals:
            source_counts[_source(meal)] = source_counts.get(_source(meal), 0) + 1
    checks["source_mix"] = ", ".join(f"{k}:{v}" for k, v in sorted(source_counts.items()))

    # Category-capped scoring: a single catastrophic issue (e.g., 25-point
    # diet-incompatibility deduction) can no longer drive the score below
    # the floor of a category that passed. We clamp the total deduction so a
    # plan that passes most checks but fails one badly still scores in the
    # 40+ range rather than the 50s. See audit finding F57.
    # A proper refactor would track per-category deductions and cap each
    # individually; this conservative floor is a first step.
    # Floor lowered from 40 to 20 (P1 #12) — a synthetic plan with 6/7
    # calorie failures + 2/7 protein failures + dessert-in-dinner +
    # zero-fibre day scored 44 (above the old 40 floor), which is too
    # lenient. Floor of 20 lets catastrophic plans score F (≤20).
    score = max(20, min(100, score))
    grade = "A" if score >= 90 else "B" if score >= 80 else "C" if score >= 70 else "D" if score >= 60 else "F"
    if not recs:
        recs.append("Plan is usable; continue improving fibre metadata and rotate recipe sources for adherence.")
    return MealPlanAudit(
        score=score,
        grade=grade,
        summary=f"Meal plan quality grade {grade} ({score}/100).",
        checks=checks,
        issues=issues,
        recommendations=recs,
    )
