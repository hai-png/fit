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

def load_external_recipe_meals(path: Optional[str] = None) -> List[MealItem]:
    """Load normalized external recipes.

    If `path` is omitted, all known normalized recipe files in `data/` are
    loaded: scraped Trifecta plus imported Muscle & Strength recipes when
    present. If `path` is a directory, all `*.json` files in it are attempted.
    """
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
    for p in paths:
        if not p.exists():
            continue
        try:
            payload = json.loads(p.read_text())
        except Exception:
            continue
        for rec in payload.get("recipes", []):
            meal = _external_to_meal(rec)
            if meal is None:
                continue
            key = (meal.name, meal.cuisine, tuple(meal.ingredients[:3]))
            if key in seen:
                continue
            seen.add(key)
            out.append(meal)
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


def _score(meal: MealItem, slot_target: float, protein_slot_target: float, preferred_cuisines: Sequence[str], used_names: set) -> float:
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
    return score + random.random() * 0.01


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
    used_names: set,
) -> MealPlan:
    layout = _slot_layout(meals_per_day)
    picks: List[MealItem] = []
    for slot, weight in layout:
        slot_target = target_calories * weight
        protein_target = target_macros.protein_g * weight
        if slot in {"lunch", "dinner"}:
            # Lunch/dinner are interchangeable main meals; this prevents tiny
            # dinner pools from causing repetition while keeping the displayed
            # slot aligned with the plan layout.
            candidates = [m for m in pool if m.slot in {"lunch", "dinner"}]
        else:
            candidates = [m for m in pool if m.slot == slot]
        if not candidates:
            fallback_slots = {"breakfast": ["snack"], "snack": ["breakfast"]}.get(slot, [])
            candidates = [m for m in pool if m.slot in fallback_slots]
        if not candidates:
            continue
        candidates.sort(key=lambda m: _score(m, slot_target, protein_target, preferred_cuisines, used_names))
        chosen = candidates[0]
        used_names.add(chosen.name)
        if chosen.slot != slot:
            import copy
            chosen = copy.copy(chosen)
            chosen.slot = slot
        picks.append(chosen)

    # If the selected meals are too low in protein density, add small protein
    # boosters before scaling the whole day back to the calorie target.
    for _ in range(4):
        base_total_preview = sum(m.calories for m in picks) or 1
        predicted_protein = sum(m.protein_g for m in picks) * (target_calories / base_total_preview)
        if predicted_protein >= target_macros.protein_g * 0.85:
            break
        booster = _best_protein_booster(pool, used_names)
        if booster is None:
            break
        import copy
        booster = copy.copy(booster)
        booster.slot = "snack"
        used_names.add(booster.name)
        picks.append(booster)

    # Imported recipe fibre data is often missing. Prefer an external
    # high-fibre recipe/add-on when known fibre would otherwise be very low.
    base_total_preview = sum(m.calories for m in picks) or 1
    predicted_fibre = sum(m.fibre_g for m in picks) * (target_calories / base_total_preview)
    if predicted_fibre < micronutrient_targets(target_calories).fibre_g * 0.60:
        side = _best_fibre_side(pool, used_names)
        if side is not None:
            import copy
            side = copy.copy(side)
            side.slot = "snack"
            used_names.add(side.name)
            picks.append(side)

    base_total = sum(m.calories for m in picks) or 1
    scale = target_calories / base_total
    scaled = [_scale(m, scale) for m in picks]
    actual = sum(m.calories for m in scaled)
    return MealPlan(
        name="Protocol day plan",
        cuisine="mixed",
        diet=diet,
        meals=scaled,
        notes=[
            f"Target {target_calories:.0f} kcal",
            f"Total {actual:.0f} kcal",
            f"Protein {sum(m.protein_g for m in scaled):.0f} g",
            f"Carbs {sum(m.carbs_g for m in scaled):.0f} g",
            f"Fat {sum(m.fat_g for m in scaled):.0f} g",
            f"Fibre {sum(m.fibre_g for m in scaled):.0f} g",
        ],
    )


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
) -> List[MealItem]:
    target_cal = selected.calories / max(selected.portion_scale, 0.01)
    target_pro = selected.protein_g / max(selected.portion_scale, 0.01)
    candidates = [
        m for m in pool
        if m.name != selected.name and m.slot == selected.slot and m.name not in used_names
    ]
    if not candidates:
        candidates = [m for m in pool if m.name != selected.name and m.slot == selected.slot]
    candidates.sort(key=lambda m: _score(m, target_cal, target_pro, preferred_cuisines, set()))
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
    if seed is not None:
        random.seed(seed)
    preferred_cuisines = list(preferred_cuisines or [])
    pool = recipe_pool(diet, allergens, include_external, external_path, include_internal=include_internal)
    if not pool:
        raise ValueError(f"No compatible recipes found for diet={diet.value}")

    days: List[MealPlan] = []
    used_names: set = set()
    for idx in range(7):
        # Allow repeats only after the pool is running thin.
        if len(used_names) > max(8, len(pool) * 0.60):
            used_names.clear()
        day = _choose_day(pool, diet, target_calories, target_macros, meals_per_day, preferred_cuisines, used_names)
        day.name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][idx]
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
            alts = _alternatives_for(m, pool, preferred_cuisines, day_names, alternatives_per_meal)
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
