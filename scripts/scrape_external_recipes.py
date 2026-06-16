#!/usr/bin/env python3
"""
Scrape external recipe indexes into the local normalized recipe format.

Sources requested by the user:
  - Trifecta recipe topic index (direct HTTP works)
  - Muscle & Strength recipe index (often Cloudflare-protected in headless HTTP;
    the scraper attempts it and records blocked URLs for manual/import fallback)

The output is intentionally conservative: we retain source URL/title, infer tags,
parse macros when visible, and assign a confidence level. Meal-plan generation can
filter to `macro_confidence in {'verified','parsed'}` or allow estimated entries.
"""
from __future__ import annotations

import argparse
import json
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (compatible; fit-recipe-scraper/1.0; +https://arena.ai)"


@dataclass
class ExternalRecipe:
    source: str
    source_url: str
    title: str
    slot: str
    cuisine: str
    calories: Optional[float]
    protein_g: Optional[float]
    carbs_g: Optional[float]
    fat_g: Optional[float]
    fibre_g: Optional[float] = None
    servings: Optional[float] = None
    prep_minutes: Optional[int] = None
    cook_minutes: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    ingredients: List[str] = field(default_factory=list)
    instructions: List[str] = field(default_factory=list)
    summary: str = ""
    macro_confidence: str = "missing"  # verified | parsed | estimated | missing
    include_in_planner: bool = False


def get(url: str, sleep: float = 0.1) -> Optional[str]:
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=25)
        time.sleep(sleep)
        if r.status_code != 200 or "Just a moment" in r.text[:1000]:
            return None
        return r.text
    except Exception:
        return None


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def infer_slot(title: str, text: str = "") -> str:
    t = f"{title} {text}".lower()
    if any(k in t for k in ["breakfast", "pancake", "french toast", "oat", "omelette", "smoothie", "shake"]):
        return "breakfast"
    if any(k in t for k in ["snack", "bar", "bite", "muffin", "cookie", "brownie", "sauce", "dressing", "salsa"]):
        return "snack"
    if any(k in t for k in ["lunch", "sandwich", "wrap", "salad", "bowl"]):
        return "lunch"
    if any(k in t for k in ["dinner", "steak", "chicken", "salmon", "pasta", "chili", "casserole", "taco", "burger"]):
        return "dinner"
    return "dinner"


def infer_cuisine(title: str, text: str = "") -> str:
    t = f"{title} {text}".lower()
    mapping = [
        ("mexican", ["taco", "burrito", "nacho", "enchilada", "chipotle", "salsa", "mexican"]),
        ("asian", ["teriyaki", "miso", "ginger", "thai", "pad thai", "soy", "sushi", "curry"]),
        ("mediterranean", ["greek", "mediterranean", "hummus", "tahini", "feta", "falafel"]),
        ("indian", ["masala", "tikka", "dal", "curry", "roti"]),
        ("italian", ["pasta", "pizza", "lasagna", "bolognese", "italian"]),
    ]
    for cuisine, keys in mapping:
        if any(k in t for k in keys):
            return cuisine
    return "american"


def infer_tags(title: str, text: str, ingredients: Iterable[str]) -> List[str]:
    title_text = f"{title} {text}".lower()
    ingredient_blob = " ".join(ingredients).lower()
    tags = {"balanced"}
    if any(k in title_text for k in ["high-protein", "high protein", "protein"]):
        tags.add("high_protein")
    if any(k in title_text for k in ["keto", "low carb", "low-carb"]):
        tags.update(["keto", "low_carb"] )
    if "gluten-free" in title_text or "gluten free" in title_text:
        tags.add("gluten_free")
    if "paleo" in title_text:
        tags.add("paleo")
    if "mediterranean" in title_text:
        tags.add("mediterranean")

    red_meat = ["beef", "pork", "steak", "bacon", "ham", "lamb", "bison"]
    poultry = ["chicken", "turkey"]
    seafood = ["salmon", "tuna", "shrimp", "fish", "cod"]
    dairy_egg = ["egg", "cheese", "yogurt", "whey", "milk", "cream"]
    plant_protein = ["tofu", "tempeh", "seitan", "lentil", "bean", "chickpea"]

    has_red = any(k in ingredient_blob for k in red_meat)
    has_poultry = any(k in ingredient_blob for k in poultry)
    has_seafood = any(k in ingredient_blob for k in seafood)
    has_dairy_egg = any(k in ingredient_blob for k in dairy_egg)

    if has_red:
        tags.add("omnivore")
    elif has_poultry:
        tags.update(["omnivore", "pollo_pescatarian"])
    elif has_seafood:
        tags.update(["pescatarian", "pollo_pescatarian"])
    elif has_dairy_egg:
        tags.update(["vegetarian", "pescatarian", "pollo_pescatarian"])
    else:
        tags.update(["vegan", "vegetarian", "pescatarian", "pollo_pescatarian"])

    if any(k in ingredient_blob for k in plant_protein):
        tags.add("high_protein")
    return sorted(tags)

def parse_minutes(text: str, label: str) -> Optional[int]:
    m = re.search(label + r"\s*(?:time)?\s*:?\s*~?\s*(\d+)\s*(?:minute|min)", text, re.I)
    return int(m.group(1)) if m else None


def parse_servings(text: str) -> Optional[float]:
    for pat in [r"Servings?\s*:?\s*(\d+(?:\.\d+)?)", r"Number of Servings\s*:?\s*(\d+(?:\.\d+)?)", r"Makes\s+(\d+(?:\.\d+)?)\s+serv"]:
        m = re.search(pat, text, re.I)
        if m:
            return float(m.group(1))
    return None


def find_macro(text: str, names: List[str]) -> Optional[float]:
    """Robust macro parser for Trifecta pages.

    Handles forms like:
      Calories Per Serving: 370
      Total Fat 17g
      Total Carbohydrates 49g
      Protein 32g
    where labels and values are often separated by many newlines.
    """
    lines = [clean(x) for x in text.splitlines()]
    lines = [x for x in lines if x]
    aliases = [n.lower() for n in names]

    def is_label(line: str) -> bool:
        low = line.lower()
        return any(a in low for a in aliases)

    # label and value on same line or nearby following lines
    for i, line in enumerate(lines):
        if not is_label(line):
            continue
        # Avoid percent daily value lines by preferring first numeric after label.
        tail = line
        for name in names:
            tail = re.sub(name, '', tail, flags=re.I)
        m = re.search(r"(\d+(?:\.\d+)?)\s*g?\b", tail)
        if m:
            return float(m.group(1))
        for nxt in lines[i+1:i+8]:
            # Stop if another macro label appears before a number.
            if nxt != line and any(lbl in nxt.lower() for lbl in ["calories", "protein", "carbohydrate", "carbs", "total fat", "sodium", "cholesterol"]):
                # except if current label is calories and next line says per serving
                if not ("per serving" in nxt.lower() and "calorie" in " ".join(aliases)):
                    break
            m = re.search(r"(\d+(?:\.\d+)?)\s*g?\b", nxt)
            if m:
                return float(m.group(1))
    return None

def extract_between_lines(lines: List[str], start_terms: List[str], stop_terms: List[str]) -> List[str]:
    start = None
    for i, line in enumerate(lines):
        low = line.lower().strip()
        if any(low == st or low.startswith(st + " ") for st in start_terms):
            start = i + 1
            break
    if start is None:
        return []
    out = []
    for line in lines[start:]:
        low = line.lower().strip()
        if any(low == st or low.startswith(st) for st in stop_terms):
            break
        if line and len(line) > 1:
            out.append(line)
    return out[:80]


def parse_article(source: str, url: str, html: str) -> Optional[ExternalRecipe]:
    soup = BeautifulSoup(html, "html.parser")
    title = clean(soup.find("h1").get_text(" ") if soup.find("h1") else (soup.title.string if soup.title else url))
    meta = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
    summary = clean(meta.get("content", "")) if meta else ""
    text = soup.get_text("\n")
    lines = [clean(x) for x in text.splitlines()]
    lines = [x for x in lines if x]
    ingredients = extract_between_lines(lines, ["ingredients", "ingredients:"], ["kitchen tools", "instructions", "cooking instructions", "directions", "step 1", "method", "nutrition"])
    instructions = extract_between_lines(lines, ["instructions", "cooking instructions", "directions", "method"], ["nutrition", "serving suggestions", "notes", "print", "share"])
    if not instructions:
        instructions = [x for x in lines if re.match(r"^(step\s+\d+|\d+\.)", x, re.I)][:30]
    servings = parse_servings(text)
    prep = parse_minutes(text, "Prep")
    cook = parse_minutes(text, "Cook")
    calories = find_macro(text, ["Calories Per Serving", "Calories", "Calorie"])
    protein = find_macro(text, ["Protein"])
    carbs = find_macro(text, ["Total Carbohydrates", "Carbs", "Carbohydrates"])
    fat = find_macro(text, ["Total Fat", "Fat", "Fats"])
    fibre = find_macro(text, ["Fiber", "Fibre"])

    # Discard obvious index/listicle pages unless they have ingredients or macros.
    if not ingredients and not any(v is not None for v in [calories, protein, carbs, fat]):
        if "recipe" not in title.lower():
            return None

    macro_ok = (
        calories is not None and 50 <= calories <= 1500 and
        protein is not None and 0 <= protein <= 150 and
        carbs is not None and 0 <= carbs <= 250 and
        fat is not None and 0 <= fat <= 150
    )
    confidence = "parsed" if macro_ok else "missing"
    include = confidence in {"parsed", "verified"}
    classify_text = f"{summary} {' '.join(ingredients[:20])}"
    return ExternalRecipe(
        source=source, source_url=url, title=title, slot=infer_slot(title, classify_text),
        cuisine=infer_cuisine(title, classify_text), calories=calories, protein_g=protein,
        carbs_g=carbs, fat_g=fat, fibre_g=fibre, servings=servings,
        prep_minutes=prep, cook_minutes=cook,
        tags=infer_tags(title, summary, ingredients), ingredients=ingredients,
        instructions=instructions, summary=summary, macro_confidence=confidence,
        include_in_planner=include,
    )



def discover_trifecta_recipe_links(url: str, html: str) -> List[str]:
    """Find recipe-looking Trifecta blog links inside listicles/articles."""
    soup = BeautifulSoup(html, "html.parser")
    out: List[str] = []
    for a in soup.select('a[href]'):
        href = urljoin(url, a.get("href", "")).split("?")[0].split("#")[0]
        if "trifectanutrition.com/blog/" not in href:
            continue
        if "/blog/topic/" in href or href.endswith("/blog"):
            continue
        txt = clean(a.get_text(" "))
        hay = f"{txt} {href}".lower()
        if any(k in hay for k in ["recipe", "meal-prep", "keto", "paleo", "low-carb", "high-protein", "salad", "chicken", "beef", "shrimp", "salmon", "breakfast"]):
            if href not in out:
                out.append(href)
    return out

def scrape_trifecta(max_pages: int = 40) -> Tuple[List[ExternalRecipe], List[str]]:
    base = "https://www.trifectanutrition.com/blog/topic/recipes"
    seed_urls: List[str] = []
    # 1) Crawl all topic pages.
    for page in range(1, max_pages + 1):
        url = base if page == 1 else f"{base}/page/{page}"
        html = get(url)
        if not html:
            break
        soup = BeautifulSoup(html, "html.parser")
        page_urls = []
        for a in soup.select('a[href]'):
            href = a.get("href", "")
            if "/blog/" in href and "/blog/topic/" not in href and not href.endswith('/blog'):
                full = urljoin(url, href).split("?")[0].split("#")[0]
                if full not in seed_urls:
                    seed_urls.append(full)
                    page_urls.append(full)
        if not page_urls and page > 1:
            break

    # 2) Parse seeds, and if a seed is an article/listicle, discover linked recipe pages.
    queue = list(seed_urls)
    seen: set[str] = set()
    recipes: List[ExternalRecipe] = []
    failed: List[str] = []
    while queue:
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        html = get(url)
        if not html:
            failed.append(url)
            continue
        rec = parse_article("trifecta", url, html)
        if rec:
            recipes.append(rec)
        for linked in discover_trifecta_recipe_links(url, html):
            if linked not in seen and linked not in queue:
                queue.append(linked)

    return recipes, failed

def scrape_muscleandstrength_index() -> Tuple[List[ExternalRecipe], List[str]]:
    """Attempt direct scraping. In this environment M&S commonly returns 403.

    We still provide this so the scraper works in environments with access, and
    we record failures/blocked pages for transparency.
    """
    cats = ["protein-shakes", "protein-bars", "high-protein", "low-carb", "snacks", "vegetarian", "breakfast", "lunch", "dinner", "bbq"]
    urls: List[str] = []
    blocked: List[str] = []
    for cat in cats:
        for page in range(0, 6):
            url = f"https://www.muscleandstrength.com/recipes/{cat}" + (f"?page={page}" if page else "")
            html = get(url)
            if not html:
                if page == 0:
                    blocked.append(url)
                break
            soup = BeautifulSoup(html, "html.parser")
            found = 0
            for a in soup.select('a[href]'):
                href = a.get("href", "")
                if ("/recipes/" in href or "/recipe/" in href or "/articles/" in href) and "View Recipe" not in clean(a.get_text(" ")):
                    full = urljoin(url, href).split("?")[0]
                    if re.search(r"/recipes?/[^/#]+$|/articles/[^/#]+recipe", full) and full not in urls:
                        urls.append(full)
                        found += 1
            if found == 0 and page > 0:
                break
    recipes: List[ExternalRecipe] = []
    for url in urls:
        html = get(url)
        if not html:
            blocked.append(url)
            continue
        rec = parse_article("muscleandstrength", url, html)
        if rec:
            recipes.append(rec)
    return recipes, blocked


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/recipes/normalized/trifecta_recipes.json")
    ap.add_argument("--trifecta-pages", type=int, default=30)
    ap.add_argument("--skip-mns", action="store_true")
    args = ap.parse_args()

    all_recipes: List[ExternalRecipe] = []
    failures: Dict[str, List[str]] = {}

    tri, tri_failed = scrape_trifecta(args.trifecta_pages)
    all_recipes.extend(tri)
    failures["trifecta_failed"] = tri_failed

    if not args.skip_mns:
        mns, mns_failed = scrape_muscleandstrength_index()
        all_recipes.extend(mns)
        failures["muscleandstrength_blocked_or_failed"] = mns_failed

    # Deduplicate by URL.
    seen = set()
    deduped = []
    for r in all_recipes:
        if r.source_url in seen:
            continue
        seen.add(r.source_url)
        deduped.append(r)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "fit.external_recipes.v1",
        "recipe_count": len(deduped),
        "planner_eligible_count": sum(1 for r in deduped if r.include_in_planner),
        "sources": sorted(set(r.source for r in deduped)),
        "failures": failures,
        "recipes": [asdict(r) for r in deduped],
    }
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(json.dumps({k: payload[k] for k in ["recipe_count", "planner_eligible_count", "sources"]}, indent=2))
    if failures.get("muscleandstrength_blocked_or_failed"):
        print(f"M&S blocked/failed URLs: {len(failures['muscleandstrength_blocked_or_failed'])}; see JSON failures.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
