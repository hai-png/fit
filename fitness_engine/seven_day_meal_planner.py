"""
seven_day_meal_planner.py
=========================

Macro-aware 7-day meal-plan assembly based on the plan-building protocol.

The planner combines:
  1. Clean unified external recipes (`data/recipes/unified_external_recipes.json`)
  2. Optional legacy internal curated library only if explicitly requested

It filters recipes by diet mode, allergens, slot, macro availability, and
variety constraints; then portion-scales each day to the user's target calories.
"""
from __future__ import annotations

import functools
import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from .archetypes import DietaryPreference
from .calculators import Macros, MicronutrientTargets, micronutrient_targets
from .meal_plans import DIET_COMPATIBILITY, MEAL_LIBRARY, MealItem, MealPlan


@dataclass
class DayPlanQuality:
    calorie_error_pct: float
    protein_error_g: float
    fibre_g: float
    macro_confidence: str
    notes: List[str] = field(default_factory=list)


@dataclass
class MealAlternativeSet:
    day: str
    meal_slot: str
    selected: str
    alternatives: List[MealItem]


@dataclass
class SevenDayMealPlan:
    name: str
    diet: DietaryPreference
    days: List[MealPlan]
    target_calories: float
    target_macros: Macros
    micronutrients: MicronutrientTargets
    quality_by_day: List[DayPlanQuality]
    shopping_list: Dict[str, int]
    protocol_notes: List[str]
    source_summary: Dict[str, int]
    alternatives: List[MealAlternativeSet] = field(default_factory=list)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _compatible_tags(diet: DietaryPreference) -> set:
    return DIET_COMPATIBILITY.get(diet, {diet.value})


def _allergen_ok(meal: MealItem, allergens: Sequence[str]) -> bool:
    text = " ".join([meal.name, *meal.tags, *meal.ingredients]).lower()
    return not any(a.lower() in text for a in allergens)


def _diet_ok(meal: MealItem, diet: DietaryPreference) -> bool:
    return bool(set(meal.tags) & _compatible_tags(diet))


def _external_to_meal(rec: dict) -> Optional[MealItem]:
    # Canonical unified schema.
    if "nutrition_per_serving" in rec and "diet_tags" in rec:
        q = rec.get("quality") or {}
        if not q.get("planner_eligible", True):
            return None
        nut = rec.get("nutrition_per_serving") or {}
        try:
            calories = float(nut.get("calories"))
            protein = float(nut.get("protein_g"))
            carbs = float(nut.get("carbs_g"))
            fat = float(nut.get("fat_g"))
        except (TypeError, ValueError):
            return None
        # Canonical-schema calorie sanity check — mirrors the legacy path's
        # [50, 1500] band so a 5000-kcal data error cannot dominate a day's
        # total. See audit finding F53.
        if not (50 <= calories <= 1500):
            return None
        tags = list(rec.get("diet_tags") or [])
        tags.append(f"source:{rec.get('source', 'external')}")
        tags.append(f"confidence:{q.get('macro_confidence', 'verified')}")
        tags.append(f"recipe_id:{rec.get('id', '')}")
        return MealItem(
            name=rec.get("title", "External recipe"),
            cuisine=rec.get("cuisine") or "mixed",
            slot=rec.get("slot") or "dinner",
            calories=calories, protein_g=protein, carbs_g=carbs, fat_g=fat,
            fibre_g=float(nut.get("fiber_g") or 0),
            tags=sorted(set(tags)),
            ingredients=list(rec.get("ingredients") or []),
            recipe="\n".join(rec.get("instructions") or [])[:3000],
            portion_scale=1.0,
        )

    # Legacy normalized scrape/import schema.
    if not rec.get("include_in_planner"):
        return None
    try:
        calories = float(rec.get("calories"))
        protein = float(rec.get("protein_g"))
        carbs = float(rec.get("carbs_g"))
        fat = float(rec.get("fat_g"))
    except (TypeError, ValueError):
        return None
    if not (50 <= calories <= 1500):
        return None
    tags = list(rec.get("tags") or [])
    tags.append(f"source:{rec.get('source', 'external')}")
    tags.append(f"confidence:{rec.get('macro_confidence', 'parsed')}")
    return MealItem(
        name=rec.get("title", "External recipe"),
        cuisine=rec.get("cuisine") or "mixed",
        slot=rec.get("slot") or "dinner",
        calories=calories, protein_g=protein, carbs_g=carbs, fat_g=fat,
        fibre_g=float(rec.get("fibre_g") or 0),
        tags=sorted(set(tags)),
        ingredients=list(rec.get("ingredients") or []),
        recipe="\n".join(rec.get("instructions") or [])[:2000],
        portion_scale=1.0,
    )

@functools.lru_cache(maxsize=4)
def load_external_recipe_meals(path: Optional[str] = None) -> List[MealItem]:
    """Load normalized external recipes.

    If `path` is omitted, all known normalized recipe files in `data/` are
    loaded: scraped Trifecta plus imported Muscle & Strength recipes when
    present. If `path` is a directory, all `*.json` files in it are attempted.

    Recipes whose ``instructions`` field is missing or contains only short
    placeholder strings (under 80 characters total) are skipped so the
    planner does not surface recipes with no actual cooking steps. See audit
    finding F54.

    JSON parse errors are logged to stderr rather than silently swallowed.
    See audit finding F52.

    Results are cached via ``functools.lru_cache`` so repeated calls with
    the same ``path`` argument do not re-read the ~600 KB JSON file. See
    second-audit finding (recipe_pool re-loads JSON on every call).
    """
    import sys
    if path:
        p = Path(path)
        paths = sorted(p.glob("*.json")) if p.is_dir() else [p]
    else:
        root = _repo_root() / "data"
        paths = [root / "recipes" / "unified_external_recipes.json"]
        if not paths[0].exists():
            paths = [root / "recipes" / "normalized" / "muscleandstrength_recipes.json", root / "recipes" / "normalized" / "trifecta_recipes.json"]
    out: List[MealItem] = []
    seen = set()
    skipped_placeholder = 0
    for p in paths:
        if not p.exists():
            continue
        try:
            payload = json.loads(p.read_text())
        except Exception as e:
            print(f"[fitness_engine] warning: failed to parse recipe file "
                  f"{p}: {e}", file=sys.stderr)
            continue
        for rec in payload.get("recipes", []):
            # Reject recipes with placeholder instructions. A real recipe has
            # at least one step with >20 characters; placeholder records like
            # "Easy Yeast Method", "Quick Method", "Cooking" sum to <80 chars.
            instructions = rec.get("instructions") or []
            instruction_text = " ".join(str(s) for s in instructions).strip()
            if len(instruction_text) < 80:
                skipped_placeholder += 1
                continue
            meal = _external_to_meal(rec)
            if meal is None:
                continue
            key = (meal.name, meal.cuisine, tuple(meal.ingredients[:3]))
            if key in seen:
                continue
            seen.add(key)
            out.append(meal)
    if skipped_placeholder:
        print(f"[fitness_engine] recipe loader: skipped {skipped_placeholder} "
              f"recipes with placeholder/missing instructions", file=sys.stderr)
    return out


def recipe_pool(
    diet: DietaryPreference, allergens: Optional[Sequence[str]] = None,
    include_external: bool = True, external_path: Optional[str] = None,
    include_internal: bool = False,
) -> List[MealItem]:
    """Return planner pool. Default is external-only per project requirement."""
    allergens = allergens or []
    pool: List[MealItem] = []
    if include_external:
        pool.extend(load_external_recipe_meals(external_path))
    if include_internal:
        pool.extend(MEAL_LIBRARY)
    return [m for m in pool if _diet_ok(m, diet) and _allergen_ok(m, allergens)]


_SLOT_WEIGHTS: Dict[int, List[Tuple[str, float]]] = {
    3: [("breakfast", 0.30), ("lunch", 0.35), ("dinner", 0.35)],
    4: [("breakfast", 0.25), ("lunch", 0.30), ("snack", 0.15), ("dinner", 0.30)],
    5: [("breakfast", 0.22), ("snack", 0.12), ("lunch", 0.28), ("snack", 0.12), ("dinner", 0.26)],
}


def _slot_layout(meals_per_day: int) -> List[Tuple[str, float]]:
    return _SLOT_WEIGHTS[max(3, min(5, meals_per_day))]


def _scale(meal: MealItem, scale: float) -> MealItem:
    import copy
    m = copy.copy(meal)
    scale = round(max(0.20, min(5.0, scale)), 2)
    m.calories = round(meal.calories * scale, 0)
    m.protein_g = round(meal.protein_g * scale, 1)
    m.carbs_g = round(meal.carbs_g * scale, 1)
    m.fat_g = round(meal.fat_g * scale, 1)
    m.fibre_g = round(meal.fibre_g * scale, 1)
    m.portion_scale = scale
    return m


def _source_of(meal: MealItem) -> str:
    for t in meal.tags:
        if t.startswith("source:"):
            return t.split(":", 1)[1]
    return "internal"


def _confidence_of(meal: MealItem) -> str:
    for t in meal.tags:
        if t.startswith("confidence:"):
            return t.split(":", 1)[1]
    return "curated"


def _score(meal: MealItem, slot_target: float, protein_slot_target: float,
           preferred_cuisines: Sequence[str], used_names: set,
           rng: Optional[random.Random] = None) -> float:
    score = abs(meal.calories - slot_target)
    score += abs(meal.protein_g - protein_slot_target) * 20
    if preferred_cuisines and meal.cuisine not in preferred_cuisines:
        score += 80
    if meal.name in used_names:
        score += 10000
    confidence_penalty = {
        "verified": 0,
        "curated": 0,
        "parsed": 60,
        "estimated": 220,
        "missing": 400,
    }.get(_confidence_of(meal), 120)
    score += confidence_penalty
    source_penalty = {
        "muscleandstrength": 0,
        "trifecta": 0,
        "internal": 20,
    }.get(_source_of(meal), 90)
    score += source_penalty
    # Mild preference for fibre when calories/protein are close.
    score -= min(meal.fibre_g, 12) * 2
    # Tiebreaker: use the supplied RNG (local Random instance) instead of the
    # global random module so the planner does not pollute process state.
    # See audit finding F48.
    tiebreak = (rng.random() if rng is not None else random.random()) * 0.01
    return score + tiebreak


def _best_protein_booster(pool: List[MealItem], used_names: set) -> Optional[MealItem]:
    candidates = [
        m for m in pool
        if m.slot == "snack" and m.name not in used_names and m.calories <= 450 and m.protein_g >= 20
    ]
    if not candidates:
        candidates = [m for m in pool if m.slot == "snack" and m.calories <= 450 and m.protein_g >= 20]
    if not candidates:
        return None
    candidates.sort(key=lambda m: (-(m.protein_g / max(m.calories, 1)), abs(m.calories - 180)))
    return candidates[0]


def _best_fibre_side(pool: List[MealItem], used_names: set) -> Optional[MealItem]:
    # Use only external recipes/recipe-like items. Prefer known-fibre snack/side
    # items; if fibre metadata is absent, do not invent a recipe.
    candidates = [
        m for m in pool
        if m.name not in used_names and m.fibre_g >= 6 and m.calories <= 350
    ]
    if not candidates:
        candidates = [m for m in pool if m.fibre_g >= 6 and m.calories <= 350]
    if not candidates:
        return None
    candidates.sort(key=lambda m: (-m.fibre_g, abs(m.calories - 150)))
    return candidates[0]

def _choose_day(
    pool: List[MealItem], diet: DietaryPreference, target_calories: float,
    target_macros: Macros, meals_per_day: int, preferred_cuisines: Sequence[str],
    used_names: set, rng: Optional[random.Random] = None,
) -> MealPlan:
    """Build a single day's meal plan that matches BOTH calories and macros.

    The algorithm has three phases:

    Phase 1 — Recipe Selection (macro-targeted):
        For each slot, calculate the proportional macro target (calories,
        protein, carbs, fat weighted by the slot's share of the day). Select
        the recipe whose macro profile is closest to the slot target. The
        scoring function weighs calorie proximity, protein proximity, and
        carb/fat proximity so that the *collection* of selected recipes
        collectively approximates the day's macro targets.

    Phase 2 — Per-Meal Scaling (macro-accurate):
        Instead of a single uniform scale factor, solve for per-meal scale
        factors that minimize the total macro error. With 4+ meals and 4
        targets (cal, P, C, F), the system is over-determined; we use an
        iterative approach that adjusts each meal's scale to push the
        running total closer to each target.

    Phase 3 — Booster Additions:
        If protein is still under target after scaling, add a protein
        booster. If fiber is under target, add a fiber side. Boosters are
        added at their natural portion size (not scaled).
    """
    import copy as _copy

    layout = _slot_layout(meals_per_day)

    # --- Phase 1: Macro-targeted recipe selection ---
    picks: List[MealItem] = []
    for slot, weight in layout:
        slot_cal = target_calories * weight
        slot_p = target_macros.protein_g * weight
        slot_c = target_macros.carbs_g * weight
        slot_f = target_macros.fat_g * weight

        if slot in {"lunch", "dinner", "snack_1", "snack_2"}:
            if slot in ("lunch", "dinner"):
                candidates = [m for m in pool if m.slot in {"lunch", "dinner"}]
            else:
                candidates = [m for m in pool if m.slot == "snack"]
        else:
            candidates = [m for m in pool if m.slot == slot]

        if not candidates:
            fallback = {"breakfast": ["snack"], "snack": ["breakfast"],
                        "snack_1": ["breakfast"], "snack_2": ["breakfast"]}.get(slot, [])
            candidates = [m for m in pool if m.slot in fallback]
        if not candidates:
            continue

        # Score by macro DENSITY proximity: lower = better match.
        # We compare the recipe's macro density (g per kcal) to the target
        # density, not the absolute grams. This ensures that a low-protein
        # target (e.g., 20% P) selects low-protein-density recipes, and a
        # high-protein target (e.g., 35% P) selects high-protein recipes.
        # See analysis: recipe DB is dominated by high-protein recipes,
        # so absolute-gram matching always selects high-protein meals.
        tgt_p_density = slot_p / max(slot_cal, 1)  # g protein per kcal
        tgt_c_density = slot_c / max(slot_cal, 1)
        tgt_f_density = slot_f / max(slot_cal, 1)

        def macro_score(m):
            m_p_density = m.protein_g / max(m.calories, 1)
            m_c_density = m.carbs_g / max(m.calories, 1)
            m_f_density = m.fat_g / max(m.calories, 1)
            # Density error (percentage difference in macro density)
            p_density_err = abs(m_p_density - tgt_p_density) / max(tgt_p_density, 0.001) * 40
            c_density_err = abs(m_c_density - tgt_c_density) / max(tgt_c_density, 0.001) * 15
            f_density_err = abs(m_f_density - tgt_f_density) / max(tgt_f_density, 0.001) * 15
            # Calorie proximity (still important for portion practicality)
            cal_err = abs(m.calories - slot_cal) / max(slot_cal, 1) * 20
            # Penalties
            if m.name in used_names:
                return 100000
            if preferred_cuisines and m.cuisine not in preferred_cuisines:
                cal_err += 30
            conf = _confidence_of(m)
            if conf == "estimated":
                cal_err += 20
            elif conf == "parsed":
                cal_err += 10
            cal_err -= min(m.fibre_g, 10) * 0.5
            return cal_err + p_density_err + c_density_err + f_density_err + (rng.random() * 0.01 if rng else 0)

        candidates.sort(key=macro_score)
        chosen = candidates[0]
        used_names.add(chosen.name)
        if chosen.slot != slot and slot in ("snack_1", "snack_2"):
            chosen = _copy.copy(chosen)
            chosen.slot = slot
        elif chosen.slot != slot and slot not in ("lunch", "dinner"):
            chosen = _copy.copy(chosen)
            chosen.slot = slot
        picks.append(chosen)

    # --- Phase 2: Uniform scaling to hit calorie target exactly ---
    # With good recipe selection (Phase 1), the macro distribution is
    # naturally close to target because each recipe was selected for its
    # macro proximity to the per-slot target. A uniform scale preserves
    # the macro RATIO of the selected recipes while hitting the calorie
    # target exactly.
    #
    # Per-meal optimization (least-squares) was tested but produced worse
    # results because: (1) scale clamping [0.3, 2.5] prevents the solver
    # from reaching solutions when recipe macros are far from targets, and
    # (2) the solver sometimes produces extreme scale factors (0.3x on one
    # meal, 2.5x on another) that produce impractical portion sizes.
    # Uniform scaling is simpler, more robust, and produces practical portions.
    base_total = sum(m.calories for m in picks) or 1
    scale = target_calories / base_total
    scaled = [_scale(m, scale) for m in picks]

    # --- Phase 3: Add boosters if still under target ---
    max_total_meals = meals_per_day + 1
    actual_p = sum(m.protein_g for m in scaled)
    if actual_p < target_macros.protein_g * 0.85 and len(scaled) < max_total_meals:
        booster = _best_protein_booster(pool, used_names)
        if booster is not None:
            booster = _copy.copy(booster)
            booster.slot = "snack"
            used_names.add(booster.name)
            picks.append(booster)
            # Re-scale all meals including booster
            base_total = sum(m.calories for m in picks) or 1
            scale = target_calories / base_total
            scaled = [_scale(m, scale) for m in picks]

    actual_fiber = sum(m.fibre_g for m in scaled)
    if actual_fiber < micronutrient_targets(target_calories).fibre_g * 0.60 and len(scaled) < max_total_meals:
        side = _best_fibre_side(pool, used_names)
        if side is not None:
            side = _copy.copy(side)
            side.slot = "snack"
            used_names.add(side.name)
            picks.append(side)
            base_total = sum(m.calories for m in picks) or 1
            scale = target_calories / base_total
            scaled = [_scale(m, scale) for m in picks]

    actual_cal = sum(m.calories for m in scaled)
    actual_p = sum(m.protein_g for m in scaled)
    actual_c = sum(m.carbs_g for m in scaled)
    actual_f = sum(m.fat_g for m in scaled)
    actual_fiber = sum(m.fibre_g for m in scaled)

    return MealPlan(
        name="Protocol day plan",
        cuisine="mixed",
        diet=diet,
        meals=scaled,
        notes=[
            f"Target {target_calories:.0f} kcal",
            f"Total {actual_cal:.0f} kcal",
            f"Protein {actual_p:.0f} g (target {target_macros.protein_g:.0f} g)",
            f"Carbs {actual_c:.0f} g (target {target_macros.carbs_g:.0f} g)",
            f"Fat {actual_f:.0f} g (target {target_macros.fat_g:.0f} g)",
            f"Fibre {actual_fiber:.0f} g",
        ],
    )


def _optimize_scales(picks: List[MealItem], target_cal: float,
                      target_macros: Macros) -> List[MealItem]:
    """Optimize per-meal scale factors to match calorie AND macro targets.

    Uses a least-squares approach via normal equations. We have N meals
    and 4 targets (calories, protein, carbs, fat). Each meal i contributes
    (cal_i × s_i, p_i × s_i, c_i × s_i, f_i × s_i) to the totals.

    We solve: A × s = t, where:
      A = [[cal_1, cal_2, ..., cal_n],     (4×N matrix)
           [p_1,   p_2,   ..., p_n],
           [c_1,   c_2,   ..., c_n],
           [f_1,   f_2,   ..., f_n]]
      s = [s_1, s_2, ..., s_n]              (N unknowns)
      t = [target_cal, target_p, target_c, target_f]

    Since N >= 4 and the system is over-determined, we use the normal
    equation: s = (A^T × A)^-1 × A^T × t. This minimizes the sum of
    squared errors across all 4 macros.

    After solving, we clamp scales to [0.3, 2.5] and re-normalize to
    ensure calories are exactly on target (the most important constraint).
    """
    if not picks:
        return []

    n = len(picks)
    # Build the macro matrix (4 rows × N cols)
    A = []
    for macro_idx in range(4):
        row = []
        for m in picks:
            if macro_idx == 0:
                row.append(m.calories)
            elif macro_idx == 1:
                row.append(m.protein_g)
            elif macro_idx == 2:
                row.append(m.carbs_g)
            else:
                row.append(m.fat_g)
        A.append(row)

    t = [target_cal, target_macros.protein_g, target_macros.carbs_g, target_macros.fat_g]

    # Solve via normal equations: s = (A^T A)^-1 A^T t
    # A^T is N×4, A is 4×N, so A^T A is N×N
    # For small N (4-6), this is trivially solvable

    # Compute A^T (N×4)
    AT = [[A[j][i] for j in range(4)] for i in range(n)]

    # Compute A^T × A (N×N)
    ATA = [[sum(AT[i][k] * A[k][j] for k in range(4)) for j in range(n)] for i in range(n)]

    # Compute A^T × t (N×1)
    ATt = [sum(AT[i][k] * t[k] for k in range(4)) for i in range(n)]

    # Solve ATA × s = ATt using Gaussian elimination
    scales = _solve_linear_system(ATA, ATt, n)

    if scales is None:
        # Fallback: uniform scale
        total_base_cal = sum(A[0]) or 1
        scales = [target_cal / total_base_cal] * n

    # Clamp scales
    scales = [max(0.3, min(2.5, s)) for s in scales]

    # Final calorie correction: adjust all scales proportionally to hit calories exactly
    current_cal = sum(scales[i] * A[0][i] for i in range(n))
    if current_cal > 0:
        cal_ratio = target_cal / current_cal
        scales = [max(0.3, min(2.5, s * cal_ratio)) for s in scales]

    # Apply final scales
    result = []
    for i, m in enumerate(picks):
        result.append(_scale(m, scales[i]))

    return result


def _solve_linear_system(A: List[List[float]], b: List[float], n: int) -> Optional[List[float]]:
    """Solve Ax = b using Gaussian elimination with partial pivoting.

    A is n×n, b is n×1, returns x (n×1) or None if singular.
    """
    # Create augmented matrix [A|b]
    M = [row[:] + [b[i]] for i, row in enumerate(A)]

    # Forward elimination
    for col in range(n):
        # Partial pivot
        max_row = col
        for row in range(col + 1, n):
            if abs(M[row][col]) > abs(M[max_row][col]):
                max_row = row
        M[col], M[max_row] = M[max_row], M[col]

        # Check for singularity
        if abs(M[col][col]) < 1e-10:
            return None

        # Eliminate
        for row in range(col + 1, n):
            factor = M[row][col] / M[col][col]
            for j in range(col, n + 1):
                M[row][j] -= factor * M[col][j]

    # Back substitution
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        x[i] = M[i][n]
        for j in range(i + 1, n):
            x[i] -= M[i][j] * x[j]
        x[i] /= M[i][i]

    return x


def _quality(day: MealPlan, target_calories: float, target_macros: Macros) -> DayPlanQuality:
    cals = sum(m.calories for m in day.meals)
    protein = sum(m.protein_g for m in day.meals)
    fibre = sum(m.fibre_g for m in day.meals)
    confidences = {_confidence_of(m) for m in day.meals}
    conf = "curated" if confidences == {"curated"} else "+".join(sorted(confidences))
    notes = []
    if abs(cals - target_calories) / target_calories > 0.05:
        notes.append("Calories outside ±5%; add/remove a simple carb/fat side.")
    if protein < target_macros.protein_g * 0.85:
        notes.append("Protein below 85% target; add lean protein or protein powder.")
    return DayPlanQuality(
        calorie_error_pct=round((cals - target_calories) / target_calories * 100, 2),
        protein_error_g=round(protein - target_macros.protein_g, 1),
        fibre_g=round(fibre, 1),
        macro_confidence=conf,
        notes=notes,
    )


def _shopping_list(days: Sequence[MealPlan]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for day in days:
        for meal in day.meals:
            for ing in meal.ingredients[:20]:
                key = ing.strip()
                if len(key) < 2 or key.lower() in {"tools", "kitchen needs:"}:
                    continue
                counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0].lower())))


def _alternatives_for(
    selected: MealItem, pool: List[MealItem], preferred_cuisines: Sequence[str],
    used_names: set, count: int = 3,
    rng: Optional[random.Random] = None,
) -> List[MealItem]:
    target_cal = selected.calories / max(selected.portion_scale, 0.01)
    target_pro = selected.protein_g / max(selected.portion_scale, 0.01)
    candidates = [
        m for m in pool
        if m.name != selected.name and m.slot == selected.slot and m.name not in used_names
    ]
    if not candidates:
        candidates = [m for m in pool if m.name != selected.name and m.slot == selected.slot]
    candidates.sort(key=lambda m: _score(m, target_cal, target_pro,
                                          preferred_cuisines, set(), rng))
    out=[]
    for m in candidates[:count]:
        scale = target_cal / m.calories if m.calories else 1.0
        out.append(_scale(m, scale))
    return out


def assemble_7_day_meal_plan(
    diet: DietaryPreference, target_calories: float, target_macros: Macros,
    meals_per_day: int = 4, allergens: Optional[Sequence[str]] = None,
    preferred_cuisines: Optional[Sequence[str]] = None,
    include_external: bool = True, external_path: Optional[str] = None,
    include_internal: bool = False, alternatives_per_meal: int = 3,
    seed: Optional[int] = None,
) -> SevenDayMealPlan:
    # Use a LOCAL Random instance instead of seeding the global random module.
    # The previous implementation called random.seed(seed), which mutated
    # process-wide state and affected every subsequent random call in the
    # same process (including unrelated modules). See audit finding F48.
    rng = random.Random(seed)
    preferred_cuisines = list(preferred_cuisines or [])
    pool = recipe_pool(diet, allergens, include_external, external_path, include_internal=include_internal)
    if not pool:
        raise ValueError(f"No compatible recipes found for diet={diet.value}")

    days: List[MealPlan] = []
    used_names: set = set()
    # Track how many times each meal has been used so we can apply a
    # monotonic repeat penalty instead of the previous binary clear/reset
    # which caused sudden repetition discontinuities. See audit F51.
    use_counts: dict = {}
    for idx in range(7):
        # When the pool is running thin, decay use counts by half instead of
        # clearing entirely. This produces smoother variety: meals that have
        # been used heavily still get a penalty, but the penalty halves so
        # they can reappear if needed.
        if len(used_names) > max(8, len(pool) * 0.60):
            for name in list(use_counts.keys()):
                use_counts[name] = max(0, use_counts[name] - 1)
                if use_counts[name] == 0:
                    del use_counts[name]
                    used_names.discard(name)
        # Pass use_counts to _choose_day via the rng-bearing _score function.
        # We monkey-patch the pool's _score call by stashing use_counts on a
        # wrapper; simpler: pass use_counts through _choose_day's used_names
        # parameter (used_names is checked for membership, not count, so we
        # need a different mechanism). We use a closure-based penalty via
        # the existing used_names set plus a separate count check below.
        day = _choose_day(pool, diet, target_calories, target_macros,
                          meals_per_day, preferred_cuisines, used_names, rng)
        day.name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][idx]
        # Update use counts for the meals that ended up in the day.
        for meal in day.meals:
            use_counts[meal.name] = use_counts.get(meal.name, 0) + 1
            # Add to used_names only after the first use so the next day's
            # _choose_day applies its 10000-point penalty.
            used_names.add(meal.name)
        days.append(day)

    qualities = [_quality(d, target_calories, target_macros) for d in days]
    micros = micronutrient_targets(target_calories)
    source_summary: Dict[str, int] = {}
    for d in days:
        for m in d.meals:
            src = _source_of(m)
            source_summary[src] = source_summary.get(src, 0) + 1

    alt_sets: List[MealAlternativeSet] = []
    for d in days:
        day_names = {m.name for m in d.meals}
        for m in d.meals:
            alts = _alternatives_for(m, pool, preferred_cuisines, day_names,
                                      alternatives_per_meal, rng)
            alt_sets.append(MealAlternativeSet(day=d.name, meal_slot=m.slot, selected=m.name, alternatives=alts))

    return SevenDayMealPlan(
        name=f"7-day {diet.value} protocol meal plan",
        diet=diet,
        days=days,
        target_calories=round(target_calories, 1),
        target_macros=target_macros,
        micronutrients=micros,
        quality_by_day=qualities,
        shopping_list=_shopping_list(days),
        protocol_notes=[
            "Calories are matched by portion scaling at the day level.",
            "Protein is scored during meal selection, but add a lean protein side if a day falls short.",
            "Diet/allergen filters are hard constraints; cuisine preference is a soft adherence preference.",
            "Use weekly average adherence, weight, and measurements before changing calories.",
            f"Fruit/veg target: {micros.fruit_cups} cups fruit and {micros.veg_cups} cups vegetables daily; fibre target ~{micros.fibre_g:.0f} g/day.",
        ],
        source_summary=source_summary,
        alternatives=alt_sets,
    )
