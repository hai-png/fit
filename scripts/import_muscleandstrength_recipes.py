#!/usr/bin/env python3
"""Normalize the user-provided Muscle & Strength recipe export for the planner."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable, List, Optional


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def choose_slot(meal_types: List[str], categories: List[str], title: str) -> str:
    vals = [x.lower() for x in meal_types + categories]
    title_l = title.lower()
    # Correct common scraped category noise first. Sweet baked goods, shakes,
    # bars and desserts are snacks/breakfast even if a source page lists them
    # generically as lunch/dinner.
    if any(k in title_l for k in ["shake", "smoothie", "bar", "cookie", "brownie", "truffle", "bark", "pudding", "ice cream", "soft serve", "cupcake", "donut", "mug cake"]):
        return "snack"
    if any(k in title_l for k in ["breakfast", "pancake", "oatmeal", "omelette", "waffle", "french toast", "muffin", "crepe", "scrambled egg"]):
        return "breakfast"
    if "breakfast" in vals:
        return "breakfast"
    if "snack" in vals or "between-meals" in vals:
        return "snack"
    if "lunch" in vals:
        return "lunch"
    if "dinner" in vals:
        return "dinner"
    return "dinner"


def infer_cuisine(title: str, categories: Iterable[str], ingredients: Iterable[str]) -> str:
    blob = " ".join([title, *categories, *ingredients]).lower()
    rules = [
        ("mexican", ["taco", "burrito", "quesadilla", "fajita", "salsa", "chipotle", "mexican", "enchilada"]),
        ("asian", ["thai", "soy", "sesame", "bok choy", "ginger", "teriyaki"]),
        ("mediterranean", ["mediterranean", "gyro", "greek", "feta", "tzatziki", "hummus"]),
        ("indian", ["dhal", "dal", "madras", "curry", "garam masala", "turmeric"]),
        ("italian", ["lasagna", "pizza", "pasta", "carbonara"]),
    ]
    for cuisine, keys in rules:
        if any(k in blob for k in keys):
            return cuisine
    return "american"


def tags_for(r: dict) -> List[str]:
    tags = {"balanced"}
    dts = [x.lower().replace("-", "_") for x in r.get("dietary_tags", [])]
    goals = [x.lower().replace("-", "_") for x in r.get("fitness_goal_tags", [])]
    cats = [x.lower().replace(" ", "_").replace("-", "_") for x in r.get("categories", [])]
    ing = " ".join(r.get("ingredients", [])).lower()
    title = r.get("name", "").lower()
    all_labels = set(dts + goals + cats)

    if "high_protein" in all_labels or "high protein" in title or "protein" in title:
        tags.add("high_protein")
    if "low_carb" in all_labels:
        tags.add("low_carb")
    if "keto_friendly" in all_labels:
        # Only call it keto if carbs are genuinely low enough for the planner.
        carbs = (r.get("nutrition_per_serving") or {}).get("carbs_g")
        if carbs is not None and carbs <= 15:
            tags.add("keto")
            tags.add("low_carb")
    if any(x.startswith("gluten_free") for x in dts):
        tags.add("gluten_free")
    if "pescatarian" in dts:
        tags.add("pescatarian")
    if "vegetarian" in dts:
        tags.add("vegetarian")
    if "dairy_free" in dts and "vegetarian" in dts and not any(k in ing for k in ["egg", "whey", "milk", "yogurt", "cheese", "chicken", "beef", "pork", "turkey", "fish", "tuna", "shrimp", "scallop"]):
        tags.add("vegan")

    red_meat = ["beef", "pork", "steak", "bacon", "ham", "bison", "sirloin"]
    poultry = ["chicken", "turkey"]
    seafood = ["salmon", "tuna", "shrimp", "scallop", "tilapia", "fish"]
    dairy_egg = ["egg", "cheese", "yogurt", "whey", "milk", "cream", "casein", "cottage cheese"]

    if any(k in ing for k in red_meat):
        tags.add("omnivore")
    elif any(k in ing for k in poultry):
        tags.update(["omnivore", "pollo_pescatarian"])
    elif any(k in ing for k in seafood):
        tags.update(["pescatarian", "pollo_pescatarian"])
    elif any(k in ing for k in dairy_egg):
        tags.update(["vegetarian", "pescatarian", "pollo_pescatarian"])
    else:
        tags.update(["vegan", "vegetarian", "pescatarian", "pollo_pescatarian"])

    if "mediterranean" in infer_cuisine(r.get("name", ""), r.get("categories", []), r.get("ingredients", [])):
        tags.add("mediterranean")
    # Conservative paleo compatibility: whole-food meat/seafood/egg/veg recipes
    # without obvious grains, dairy, legumes, or protein powders.
    paleo_forbidden = [
        "oat", "bread", "pasta", "rice", "bean", "lentil", "chickpea",
        "cheese", "yogurt", "whey", "casein", "milk", "flour", "tortilla",
        "roll", "bun", "corn", "peanut", "soy", "tvp", "cottage",
    ]
    paleo_anchor = ["chicken", "turkey", "beef", "pork", "steak", "shrimp", "salmon", "fish", "egg", "vegetable", "broccoli", "cauliflower", "bok choy", "sweet potato"]
    if ("gluten_free" in all_labels or "dairy_free" in all_labels) and any(k in ing for k in paleo_anchor) and not any(k in ing for k in paleo_forbidden):
        tags.add("paleo")

    return sorted(tags)


def sane(nut: dict) -> bool:
    vals = [nut.get("calories"), nut.get("protein_g"), nut.get("carbs_g"), nut.get("fat_g")]
    if any(v is None for v in vals):
        return False
    cal, p, c, f = vals
    return 40 <= cal <= 1600 and 0 <= p <= 180 and 0 <= c <= 300 and 0 <= f <= 160


def convert(input_path: str, out_path: str) -> dict:
    raw = json.loads(Path(input_path).read_text())
    out = []
    for r in raw.get("recipes", []):
        nut = r.get("nutrition_per_serving") or {}
        ok = sane(nut)
        ingredients = [clean(x) for x in r.get("ingredients", []) if clean(x)]
        instructions = [clean(x) for x in r.get("instructions", []) if clean(x)]
        out.append({
            "source": "muscleandstrength",
            "source_url": r.get("url"),
            "title": r.get("name"),
            "slot": choose_slot(r.get("meal_type", []), r.get("categories", []), r.get("name", "")),
            "cuisine": infer_cuisine(r.get("name", ""), r.get("categories", []), ingredients),
            "calories": nut.get("calories"),
            "protein_g": nut.get("protein_g"),
            "carbs_g": nut.get("carbs_g"),
            "fat_g": nut.get("fat_g"),
            "fibre_g": nut.get("fiber_g"),
            "servings": r.get("servings"),
            "prep_minutes": r.get("prep_time_min"),
            "cook_minutes": r.get("cook_time_min"),
            "tags": tags_for(r),
            "ingredients": ingredients,
            "instructions": instructions,
            "summary": r.get("description") or "",
            "macro_confidence": "verified" if ok else "missing_or_incomplete",
            "include_in_planner": bool(ok),
            "external_id": r.get("id"),
            "difficulty": r.get("difficulty"),
            "fitness_goal_tags": r.get("fitness_goal_tags", []),
        })
    payload = {
        "schema": "fit.external_recipes.v1",
        "recipe_count": len(out),
        "planner_eligible_count": sum(1 for x in out if x["include_in_planner"]),
        "sources": ["muscleandstrength"],
        "source_metadata": raw.get("metadata", {}),
        "recipes": out,
    }
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    return payload


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", nargs="?", default="/home/user/uploads/recipes.json")
    ap.add_argument("--out", default="data/recipes/normalized/muscleandstrength_recipes.json")
    args = ap.parse_args()
    payload = convert(args.input, args.out)
    print(json.dumps({k: payload[k] for k in ["recipe_count", "planner_eligible_count", "sources"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
