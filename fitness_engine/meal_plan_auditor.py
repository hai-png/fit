"""Meal-plan quality audit helpers."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List

from .meal_plans import DIET_COMPATIBILITY, MealItem
from .seven_day_meal_planner import SevenDayMealPlan


@dataclass
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
        if quality.fibre_g and quality.fibre_g < plan.micronutrients.fibre_g * 0.6:
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
    checks["calories"] = "pass" if not calorie_failures else "fail"
    checks["protein"] = "pass" if not protein_failures else "warn"
    checks["fibre"] = "pass" if not fibre_low else "warn"

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
    # The previous check also looked for "missing_or_incomplete" which is never
    # emitted — dead code. Removed. See second-audit finding (dead confidence check).
    missing_or_est = [c for c in confidences if c in {"missing", "estimated"}]
    if missing_or_est:
        issues.append(f"Some meals have missing/estimated macro confidence: {missing_or_est[:5]}.")
        score -= 15
    checks["macro_confidence"] = "pass" if not missing_or_est else "fail"

    # Practicality: extreme portion scaling.
    extreme = [(d.name, m.name, m.portion_scale) for d in plan.days for m in d.meals if m.portion_scale < 0.35 or m.portion_scale > 2.5]
    if extreme:
        issues.append(f"Extreme portion scaling found: {extreme[:6]}.")
        recs.append("Prefer recipes closer to slot targets or add smaller side items instead of scaling entire recipes.")
        score -= 8
    checks["portion_scaling"] = "pass" if not extreme else "warn"

    # Slot sanity: flag desserts/snacks in main-meal slots using word-boundary
    # regex matching. See audit F56.
    slot_mismatch = []
    for day in plan.days:
        for meal in day.meals:
            if meal.slot in {"lunch", "dinner"}:
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
    score = max(40, min(100, score))
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
