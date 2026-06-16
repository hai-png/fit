#!/usr/bin/env python3
"""Scrape Ethiopian recipe URLs into the normalized external recipe schema.

This is a pragmatic recipe-card scraper:
- follows direct URLs and discovers Ethiopian recipe links from search/list pages
- prefers JSON-LD Recipe data
- falls back to page headings/lists where possible
- keeps recipes with missing macros in normalized data, but flags planner eligibility
  only when sane calories/protein/carbs/fat are available
"""
from __future__ import annotations

import argparse
import json
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (compatible; fit-ethiopian-recipe-importer/1.0)"
ETHIOPIAN_HINTS = re.compile(
    r"ethiopian|doro|wat|wot|tibs|shiro|misir|gomen|berbere|injera|kitfo|kik|azefa|niter|spris|teff",
    re.I)
BAD_DOMAINS = {
    "happyforks.com",
    "eatthismuch.com",
    "macros.menu",
    "nutriscan.app"}

SEED_URLS = [
    "https://www.daringgourmet.com/sega-wat-spicy-ethiopian-beef-stew/",
    "https://www.daringgourmet.com/misir-wat-ethiopian-spiced-red-lentils/",
    "https://www.daringgourmet.com/?s=ethiopian",
    "https://honest-food.net/?s=ethiopian",
    "https://www.africanbites.com/doro-wat-ethiopian-chicken-stew/",
    "https://www.africanbites.com/?s=ethiopian",
    "https://lowcarbafrica.com/?s=ethiopian",
    "https://www.aspicyperspective.com/ethiopian-recipes/",
    "https://www.feastingathome.com/berbere-potatoes/",
    "https://www.feastingathome.com/teff-cakes/#tasty-recipes-30035-jump-target",
    "https://www.feastingathome.com/teff-porridge-with-figs-walnuts-and-honey/#tasty-recipes-19909-jump-target",
    "https://www.fermentingforfoodies.com/simple-chickpea-flour-shiro-wat/",
    "https://www.fermentingforfoodies.com/simple-spiced-cabbage-and-potatoes/",
    "https://www.allrecipes.com/search?q=ethiopian",
    "https://www.cookedbyjulie.com/ethiopian-spris/",
    "https://www.africanbites.com/ethiopian-cabbage/",
    "https://lowcarbafrica.com/niter-kibbeh-ethiopian-spiced-clarified-butter/",
    "https://globalkitchentravels.com/azefa-ehiopian-lentil-salad/",
    "https://globalkitchentravels.com/ethiopian-collard-greens-gomen/",
    "https://globalkitchentravels.com/ethiopian-tibs/",
    "https://www.aspicyperspective.com/kitfo-ethiopian-steak-tartare-recipe/",
    "https://chopthegreens.com/ethiopian-pomegranate-rice-pilaf/#recipe",
    "https://www.africanbites.com/ethiopian-collard-greens/",
    "https://thespiceadventuress.com/2015/01/13/ethiopian-tomato-salad/",
    "https://www.africanbites.com/ethiopian-lentil-stew/",
    "https://ethiopianfood.wordpress.com/recipes/",
    "https://www.allrecipes.com/gallery/vegetarian-ethiopian-recipes/",
    "https://www.allrecipes.com/gallery/ethiopian-recipes/",
    "https://www.allrecipes.com/recipe/245948/kik-wat-ethiopian-red-lentil-stew/",
    "https://www.foodandwine.com/recipes/kwames-waffle-fries",
    "https://www.foodandwine.com/ethiopian-recipes-11954742",
    "https://www.gourmettraveller.com.au/chefs-recipes/ethiopian-recipes-saba-alemayoh-19302/",
    "https://www.forksoverknives.com/recipes/vegan-salads-sides/ethiopian-collard-greens-and-chard/",
    "https://www.forksoverknives.com/recipes/vegan-menus-collections/incredible-ethiopian-recipes/",
    "https://www.delinaonline.com/recipes",
    "https://ethiopianrecipes.home.blog/",
    "https://www.eleniskitchen.com/blog",
    "https://glebekitchen.com/doro-wat-ethiopian-chicken-curry/",
    "https://www.daringgourmet.com/doro-wat-spicy-ethiopian-chicken-stew/#recipe",
    "https://www.capitalmarketethiopia.com/traditional-authentic-ethiopian-recipes/",
    "https://boondockingrecipes.com/25-traditional-ethiopian-recipes/",
    "https://www.dietassassinista.com/blog/tag/Ethiopian",
    "https://insanelygoodrecipes.com/ethiopian-food/",
]


@dataclass
class NormRecipe:
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
    macro_confidence: str = "missing"
    include_in_planner: bool = False


def get(url: str) -> Optional[str]:
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=25)
        if r.status_code != 200 or "Just a moment" in r.text[:1000]:
            return None
        time.sleep(0.1)
        return r.text
    except Exception:
        return None


def clean(s: Any) -> str:
    return re.sub(r"\s+", " ", str(s or "")).strip(" \t\n\r-*•")


def flatten_jsonld(obj: Any) -> Iterable[dict]:
    if isinstance(obj, dict):
        if "@graph" in obj:
            for x in obj["@graph"]:
                yield from flatten_jsonld(x)
        else:
            yield obj
    elif isinstance(obj, list):
        for x in obj:
            yield from flatten_jsonld(x)


def types(obj: dict) -> set:
    t = obj.get("@type")
    if isinstance(t, list):
        return {str(x).lower() for x in t}
    return {str(t).lower()} if t else set()


def minutes(v: Any) -> Optional[int]:
    if v is None:
        return None
    s = str(v)
    m = re.search(r"PT(?:(\d+)H)?(?:(\d+)M)?", s, re.I)
    if m:
        return int(m.group(1) or 0) * 60 + int(m.group(2) or 0)
    m = re.search(r"(\d+)\s*(?:min|minute)", s, re.I)
    return int(m.group(1)) if m else None


def num(v: Any) -> Optional[float]:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    m = re.search(r"-?\d+(?:\.\d+)?", str(v).replace(",", ""))
    return float(m.group(0)) if m else None


def nutrition(n: Any) -> tuple[Optional[float],
                               Optional[float],
                               Optional[float],
                               Optional[float],
                               Optional[float]]:
    if not isinstance(n, dict):
        return (None, None, None, None, None)
    cal = num(n.get("calories") or n.get("calorieContent"))
    p = num(n.get("proteinContent") or n.get("protein"))
    c = num(n.get("carbohydrateContent") or n.get(
        "carbs") or n.get("carbohydrates"))
    f = num(n.get("fatContent") or n.get("fat"))
    fib = num(n.get("fiberContent") or n.get("fibreContent") or n.get("fiber"))
    return cal, p, c, f, fib


def tags_for(
        title: str,
        ingredients: List[str],
        calories,
        protein,
        carbs,
        fat) -> List[str]:
    blob = (title + " " + " ".join(ingredients)).lower()
    tags = {"balanced", "ethiopian", "african"}
    red = ["beef", "steak", "lamb", "goat", "kitfo", "tibs"]
    poultry = ["chicken", "doro"]
    seafood = ["fish", "salmon", "shrimp"]
    dairy = ["butter", "ghee", "yogurt", "milk", "cheese", "egg"]
    grains_leg = ["lentil", "misir", "chickpea", "shiro", "split pea", "beans"]
    if any(x in blob for x in red):
        tags.add("omnivore")
    elif any(x in blob for x in poultry):
        tags.update(["omnivore", "pollo_pescatarian"])
    elif any(x in blob for x in seafood):
        tags.update(["pescatarian", "pollo_pescatarian"])
    elif any(x in blob for x in dairy):
        tags.update(["vegetarian", "pescatarian", "pollo_pescatarian"])
    else:
        tags.update(
            ["vegan", "vegetarian", "pescatarian", "pollo_pescatarian"])
    if any(x in blob for x in grains_leg):
        tags.add("high_protein")
    if protein and calories and protein * 4 / calories >= .25:
        tags.add("high_protein")
    if carbs is not None and carbs <= 15:
        tags.update(["low_carb"])
    if carbs is not None and carbs <= 10 and fat is not None and fat * \
            9 / max(calories or 1, 1) > .45:
        tags.add("keto")
    if not any(
        x in blob for x in [
            "wheat",
            "bread",
            "injera",
            "flour",
            "barley"]):
        tags.add("gluten_free")
    return sorted(tags)


def slot_for(title: str, ingredients: List[str]) -> str:
    t = title.lower()
    if any(x in t for x in ["porridge", "teff cakes", "spris", "breakfast"]):
        return "breakfast"
    if any(x in t for x in ["salad", "sauce", "butter", "niter"]):
        return "snack"
    if any(
        x in t for x in [
            "stew",
            "wat",
            "wot",
            "tibs",
            "chicken",
            "beef",
            "lentil"]):
        return "dinner"
    return "lunch"


def parse_jsonld_recipe(url: str, soup: BeautifulSoup) -> List[NormRecipe]:
    out = []
    for sc in soup.find_all("script", type="application/ld+json"):
        txt = sc.string or sc.get_text()
        if not txt:
            continue
        try:
            data = json.loads(txt)
        except Exception:
            continue
        for obj in flatten_jsonld(data):
            if "recipe" not in types(obj):
                continue
            title = clean(obj.get("name"))
            if not title or not ETHIOPIAN_HINTS.search(title + " " + url):
                continue
            ingredients = [
                clean(x) for x in (
                    obj.get("recipeIngredient") or []) if clean(x)]
            instr = []
            ri = obj.get("recipeInstructions") or []
            for step in ri if isinstance(ri, list) else [ri]:
                if isinstance(step, dict):
                    instr.append(clean(step.get("text") or step.get("name")))
                else:
                    instr.append(clean(step))
            instr = [x for x in instr if x]
            cal, p, c, f, fib = nutrition(obj.get("nutrition"))
            source = urlparse(url).netloc.replace("www.", "")
            tags = tags_for(title, ingredients, cal, p, c, f)
            sane = all(
                v is not None for v in [
                    cal,
                    p,
                    c,
                    f]) and 40 <= cal <= 1600 and 0 <= p <= 180 and 0 <= c <= 300 and 0 <= f <= 160
            out.append(NormRecipe(source,
                                  url,
                                  title,
                                  slot_for(title,
                                           ingredients),
                                  "ethiopian",
                                  cal,
                                  p,
                                  c,
                                  f,
                                  fib,
                                  num(obj.get("recipeYield")),
                                  minutes(obj.get("prepTime")),
                                  minutes(obj.get("cookTime")),
                                  tags,
                                  ingredients[:40],
                                  instr[:30],
                                  clean(obj.get("description")),
                                  "parsed" if sane else "missing",
                                  sane))
    return out


def parse_fallback(url: str, soup: BeautifulSoup) -> Optional[NormRecipe]:
    h = soup.find("h1")
    title = clean(h.get_text(" ") if h else (
        soup.title.string if soup.title else ""))
    if not title or not ETHIOPIAN_HINTS.search(title + " " + url):
        return None
    ingredients = []
    for sel in [
        '[class*="ingredient"] li',
        '.wprm-recipe-ingredient',
        '.tasty-recipes-ingredients li',
            '.recipe-ingredients li']:
        ingredients += [clean(x.get_text(" ")) for x in soup.select(sel)]
    ingredients = [x for x in ingredients if x and len(x) < 180]
    instructions = []
    for sel in [
        '[class*="instruction"] li',
        '.wprm-recipe-instruction',
        '.tasty-recipes-instructions li',
            '.recipe-instructions li']:
        instructions += [clean(x.get_text(" ")) for x in soup.select(sel)]
    instructions = [x for x in instructions if x]
    if len(ingredients) < 3 or not instructions:
        return None
    source = urlparse(url).netloc.replace("www.", "")
    return NormRecipe(source,
                      url,
                      title,
                      slot_for(title,
                               ingredients),
                      "ethiopian",
                      None,
                      None,
                      None,
                      None,
                      None,
                      None,
                      None,
                      None,
                      tags_for(title,
                               ingredients,
                               None,
                               None,
                               None,
                               None),
                      ingredients[:40],
                      instructions[:30],
                      "",
                      "missing",
                      False)


def discover(url: str, html: str) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    base_netloc = urlparse(url).netloc
    urls = []
    for a in soup.select('a[href]'):
        href = urljoin(url, a.get('href', '')).split('#')[0]
        if urlparse(href).netloc != base_netloc:
            continue
        txt = clean(a.get_text(" ")) + " " + href
        if ETHIOPIAN_HINTS.search(txt) and not re.search(
                r"/tag/|/category/|\?s=|/search", href):
            urls.append(href)
    return list(dict.fromkeys(urls))[:40]


def scrape(urls: List[str], max_discovered: int = 120) -> dict:
    queue = list(dict.fromkeys(urls))
    seen = set()
    discovered = []
    recipes = []
    failed = []
    while queue and len(seen) < len(urls) + max_discovered:
        url = queue.pop(0).split('#')[0]
        if url in seen:
            continue
        seen.add(url)
        if urlparse(url).netloc.replace('www.', '') in BAD_DOMAINS:
            continue
        html = get(url)
        if not html:
            failed.append(url)
            continue
        soup = BeautifulSoup(html, "html.parser")
        rs = parse_jsonld_recipe(url, soup)
        fb = None if rs else parse_fallback(url, soup)
        if rs:
            recipes.extend(rs)
        elif fb:
            recipes.append(fb)
        # Discover from search/list pages and broad collections.
        if ('?s=' in url or 'search' in url or 'gallery' in url or 'recipes' in url or 'category' in url or 'tag' in url) and len(
                discovered) < max_discovered:
            for u in discover(url, html):
                if u not in seen and u not in queue:
                    queue.append(u)
                    discovered.append(u)
    # dedupe by title/source
    out = []
    keys = set()
    for r in recipes:
        k = (r.source, r.title.lower())
        if k in keys:
            continue
        keys.add(k)
        out.append(asdict(r))
    return {"schema": "fit.external_recipes.v1",
            "recipe_count": len(out),
            "planner_eligible_count": sum(1 for r in out if r['include_in_planner']),
            "sources": sorted(set(r['source'] for r in out)),
            "failed": failed,
            "discovered_count": len(discovered),
            "recipes": out}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        '--out',
        default='data/recipes/normalized/ethiopian_recipes.json')
    ap.add_argument('--max-discovered', type=int, default=120)
    ap.add_argument('urls', nargs='*')
    args = ap.parse_args()
    payload = scrape(args.urls or SEED_URLS, args.max_discovered)
    p = Path(args.out)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(
        json.dumps(
            {
                k: payload[k] for k in [
                    'recipe_count',
                    'planner_eligible_count',
                    'sources',
                    'discovered_count']},
            indent=2))


if __name__ == '__main__':
    main()
