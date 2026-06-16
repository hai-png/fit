#!/usr/bin/env python3
"""Build one clean, standardized, planner-ready external recipe database.

Inputs are normalized scraper/import outputs. Output is a single canonical file:
  data/recipes/unified_external_recipes.json

Quality rules are intentionally stricter than the earlier scrape outputs:
  - must have sane calories/protein/carbs/fat
  - must have real ingredients and instructions
  - ingredients are scrubbed of page artifacts (tools, step headings, CTAs)
  - snack/dessert slot noise is corrected
  - recipes with contaminated ingredient/instruction sections are excluded
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional

BAD_INGREDIENT_PATTERNS = re.compile(
    r"\b(step\s*\d+|cook time|prep time|yield:|kitchen needs|kitchen tools|tools|too busy|meal prep resources|calorie goals|want to|get more out|recipe$|print|share|subscribe)\b",
    re.I,
)
DESSERT_SNACK = [
    "shake", "smoothie", "bar", "cookie", "brownie", "muffin", "cupcake",
    "donut", "mug cake", "truffle", "bark", "pudding", "ice cream", "soft serve",
    "sauce", "dressing", "salsa", "bites", "deviled eggs",
]
BREAKFAST_WORDS = ["breakfast", "pancake", "oatmeal", "omelette", "waffle", "french toast", "crepe", "scrambled egg"]


def clean_text(s: object) -> str:
    return re.sub(r"\s+", " ", str(s or "")).strip(" -•\t\n\r")


def normalized_slot(title: str, slot: str) -> str:
    t = title.lower()
    if any(k in t for k in DESSERT_SNACK):
        return "snack"
    if any(k in t for k in BREAKFAST_WORDS):
        return "breakfast"
    if slot in {"breakfast", "lunch", "dinner", "snack"}:
        return slot
    return "dinner"


def sanitize_ingredients(items: Iterable[object]) -> List[str]:
    out: List[str] = []
    for raw in items or []:
        x = clean_text(raw)
        if not x:
            continue
        if BAD_INGREDIENT_PATTERNS.search(x):
            # Page artifact; stop if this looks like the beginning of article body.
            if re.search(r"\b(step\s*\d+|kitchen needs|kitchen tools|tools|cook time|prep time|yield:)\b", x, re.I):
                break
            continue
        if len(x) > 180:
            continue
        if x.lower() in {"or", "and", "for the", "optional", "ingredients"}:
            continue
        out.append(x)
        if len(out) >= 28:
            break
    # de-dupe preserving order
    seen = set(); dedup = []
    for x in out:
        key = x.lower()
        if key not in seen:
            seen.add(key); dedup.append(x)
    return dedup


def sanitize_instructions(items: Iterable[object]) -> List[str]:
    out: List[str] = []
    for raw in items or []:
        x = clean_text(raw)
        if not x:
            continue
        if re.search(r"\b(calorie goals|free meal prep toolkit|subscribe|printed|share on|facebook|pinterest|too busy)\b", x, re.I):
            continue
        if x.lower() in {"instructions", "cooking instructions", "directions", "method"}:
            continue
        if len(x) > 500:
            x = x[:497].rstrip() + "..."
        out.append(x)
        if len(out) >= 20:
            break
    return out


def estimate_fiber(ingredients: List[str], carbs_g: float) -> float:
    blob = " ".join(ingredients).lower()
    score = 0.0
    rules = [
        (["oat", "oatmeal", "rolled oats"], 4),
        (["bean", "lentil", "chickpea", "black beans", "kidney"], 6),
        (["berries", "blueber", "raspber", "strawber"], 4),
        (["banana", "apple", "peach", "mango"], 3),
        (["broccoli", "spinach", "kale", "lettuce", "cabbage", "bok choy", "green beans", "pepper", "onion", "mushroom", "zucchini", "cauliflower", "salad"], 4),
        (["sweet potato", "potato", "jicama"], 4),
        (["avocado", "chia", "flax", "hemp"], 5),
        (["whole wheat", "whole grain", "corn tortilla", "tortilla"], 3),
        (["almond flour", "coconut flour", "almonds", "walnuts", "cashews"], 3),
    ]
    for keys, val in rules:
        if any(k in blob for k in keys):
            score += val
    # keep plausible and bounded by carbohydrate amount
    return round(max(0.0, min(score, carbs_g * 0.45, 20.0)), 1)


def macro_sane(r: dict) -> bool:
    try:
        cal = float(r.get("calories")); p = float(r.get("protein_g")); c = float(r.get("carbs_g")); f = float(r.get("fat_g"))
    except (TypeError, ValueError):
        return False
    return 40 <= cal <= 1600 and 0 <= p <= 180 and 0 <= c <= 300 and 0 <= f <= 160


def canonical_id(source: str, title: str, url: str) -> str:
    h = hashlib.sha1(f"{source}|{title}|{url}".encode()).hexdigest()[:10].upper()
    prefix = "MS" if source == "muscleandstrength" else "TR" if source == "trifecta" else "EX"
    return f"{prefix}-{h}"


def normalize_recipe(r: dict) -> Optional[dict]:
    if not r.get("include_in_planner") or not macro_sane(r):
        return None
    title = clean_text(r.get("title"))
    url = clean_text(r.get("source_url"))
    source = clean_text(r.get("source")) or "external"
    ingredients = sanitize_ingredients(r.get("ingredients") or [])
    instructions = sanitize_instructions(r.get("instructions") or [])
    if len(ingredients) < 3 or len(instructions) < 1:
        return None
    # reject remaining contaminated ingredients
    if any(BAD_INGREDIENT_PATTERNS.search(x) for x in ingredients):
        return None
    tags = sorted(t for t in set(r.get("tags") or []) if not str(t).startswith(("source:", "confidence:")))
    slot = normalized_slot(title, r.get("slot") or "")
    cal = float(r["calories"]); p = float(r["protein_g"]); c = float(r["carbs_g"]); f = float(r["fat_g"])
    fibre = r.get("fibre_g")
    estimated_fibre = False
    try:
        fibre = None if fibre is None else float(fibre)
    except (TypeError, ValueError):
        fibre = None
    if fibre is None:
        fibre = estimate_fiber(ingredients, c)
        estimated_fibre = fibre > 0
    macro_sum = p * 4 + c * 4 + f * 9
    macro_error_pct = round((macro_sum - cal) / cal * 100, 1) if cal else 0
    quality_score = 100
    if fibre is None:
        quality_score -= 5
    elif estimated_fibre:
        quality_score -= 2
    if abs(macro_error_pct) > 15:
        quality_score -= 10
    if len(instructions) < 3:
        quality_score -= 5
    return {
        "id": canonical_id(source, title, url),
        "source": source,
        "source_url": url,
        "title": title,
        "description": clean_text(r.get("summary")),
        "slot": slot,
        "cuisine": clean_text(r.get("cuisine")) or "american",
        "diet_tags": tags,
        "goal_tags": r.get("fitness_goal_tags", []),
        "prep_time_min": r.get("prep_minutes"),
        "cook_time_min": r.get("cook_minutes"),
        "total_time_min": (r.get("prep_minutes") or 0) + (r.get("cook_minutes") or 0) if r.get("prep_minutes") is not None or r.get("cook_minutes") is not None else None,
        "servings": r.get("servings"),
        "difficulty": r.get("difficulty"),
        "nutrition_per_serving": {
            "calories": cal,
            "protein_g": p,
            "carbs_g": c,
            "fat_g": f,
            "fiber_g": fibre,
        },
        "macro_ratio": {
            "protein_pct": round(p * 4 / cal * 100, 1),
            "carbs_pct": round(c * 4 / cal * 100, 1),
            "fat_pct": round(f * 9 / cal * 100, 1),
        },
        "ingredients": ingredients,
        "instructions": instructions,
        "quality": {
            "macro_confidence": "verified" if source == "muscleandstrength" else "parsed",
            "quality_score": quality_score,
            "macro_energy_error_pct": macro_error_pct,
            "has_fiber": fibre is not None,
            "fiber_estimated": estimated_fibre,
            "planner_eligible": True,
        },
    }


def load_recipes(path: Path) -> List[dict]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text())
    return payload.get("recipes", [])


def build(inputs: List[Path], out_path: Path) -> dict:
    recipes = []
    rejected = []
    seen = set()
    for path in inputs:
        for r in load_recipes(path):
            nr = normalize_recipe(r)
            if nr is None:
                rejected.append({"source_file": str(path), "title": r.get("title"), "reason": "failed_quality_or_schema"})
                continue
            key = (nr["source"], nr["title"].lower())
            if key in seen:
                continue
            seen.add(key)
            recipes.append(nr)
    recipes.sort(key=lambda x: (x["source"], x["slot"], x["title"]))
    stats = {
        "total": len(recipes),
        "by_source": {},
        "by_slot": {},
        "by_diet_tag": {},
        "rejected": len(rejected),
    }
    for r in recipes:
        stats["by_source"][r["source"]] = stats["by_source"].get(r["source"], 0) + 1
        stats["by_slot"][r["slot"]] = stats["by_slot"].get(r["slot"], 0) + 1
        for t in r["diet_tags"]:
            stats["by_diet_tag"][t] = stats["by_diet_tag"].get(t, 0) + 1
    payload = {
        "schema": "fit.unified_external_recipes.v1",
        "description": "Clean standardized external recipe database for 7-day meal planning.",
        "stats": stats,
        "recipes": recipes,
        "rejected_examples": rejected[:50],
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    return payload


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/recipes/unified_external_recipes.json")
    ap.add_argument("inputs", nargs="*", default=["data/recipes/normalized/muscleandstrength_recipes.json", "data/recipes/normalized/trifecta_recipes.json", "data/recipes/normalized/ethiopian_recipes.json"])
    args = ap.parse_args()
    payload = build([Path(x) for x in args.inputs], Path(args.out))
    print(json.dumps(payload["stats"], indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
