"""
meal_plans.py
=============

A structured library of meal items organised by cuisine and dietary
pattern. Each item carries nutrition info so the recommender can
assemble calorie-precise daily plans. Items are designed to be
substitutable: the recommender picks a cuisine, then samples meals
per slot that fit macro targets.

Cuisines
--------
american, mediterranean, asian, indian, mexican, middle_eastern,
african, nordic.

Diets supported
---------------
omnivore, pollo_pescatarian, pescatarian, vegetarian, vegan,
keto, mediterranean, low_fodmap. Each meal has tags so the
recommender can filter by compatibility.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import random
from typing import Dict, List, Optional

from .archetypes import DietaryPreference


# --------------------------------------------------------------------------- #
# Data model                                                                  #
# --------------------------------------------------------------------------- #
@dataclass
class MealItem:
    name: str
    cuisine: str
    slot: str                       # breakfast / lunch / dinner / snack
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fibre_g: float
    tags: List[str] = field(default_factory=list)
    ingredients: List[str] = field(default_factory=list)
    recipe: str = ""


@dataclass
class MealPlan:
    name: str
    cuisine: str
    diet: DietaryPreference
    meals: List[MealItem]
    notes: List[str] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Master library                                                             #
# --------------------------------------------------------------------------- #
MEAL_LIBRARY: List[MealItem] = [
    # ---------------- AMERICAN ----------------
    MealItem(
        name="Greek yogurt parfait with berries and granola",
        cuisine="american", slot="breakfast",
        calories=380, protein_g=28, carbs_g=42, fat_g=10, fibre_g=6,
        tags=["omnivore", "vegetarian", "pollo_pescatarian", "pescatarian"],
        ingredients=["200g Greek yogurt 2%", "60g mixed berries", "30g granola"],
        recipe="Layer yogurt, berries, granola. Serve cold.",
    ),
    MealItem(
        name="Veggie scramble with rye toast",
        cuisine="american", slot="breakfast",
        calories=420, protein_g=24, carbs_g=34, fat_g=20, fibre_g=7,
        tags=["vegetarian", "pollo_pescatarian", "pescatarian", "omnivore"],
        ingredients=["3 eggs", "spinach", "pepper", "60g feta", "2 slices rye"],
        recipe="Scramble eggs with veggies, serve with rye toast.",
    ),
    MealItem(
        name="Turkey & avocado sandwich",
        cuisine="american", slot="lunch",
        calories=520, protein_g=35, carbs_g=45, fat_g=20, fibre_g=8,
        tags=["omnivore"],
        ingredients=["100g turkey", "1/2 avocado", "lettuce", "2 slices sourdough"],
        recipe="Build sandwich; pair with side salad.",
    ),
    MealItem(
        name="Chicken & quinoa power bowl",
        cuisine="american", slot="lunch",
        calories=560, protein_g=42, carbs_g=55, fat_g=14, fibre_g=9,
        tags=["omnivore"],
        ingredients=["150g chicken breast", "80g quinoa", "mixed veg", "tahini"],
        recipe="Cook quinoa, grill chicken, assemble bowl, drizzle tahini.",
    ),
    MealItem(
        name="Sheet-pan salmon, sweet potato, broccoli",
        cuisine="american", slot="dinner",
        calories=620, protein_g=38, carbs_g=55, fat_g=22, fibre_g=10,
        tags=["omnivore", "pescatarian", "pollo_pescatarian"],
        ingredients=["180g salmon", "250g sweet potato", "200g broccoli", "olive oil"],
        recipe="Roast at 220°C for 25 min. Drizzle olive oil + lemon.",
    ),
    MealItem(
        name="Beef & vegetable stir-fry with brown rice",
        cuisine="american", slot="dinner",
        calories=640, protein_g=40, carbs_g=60, fat_g=20, fibre_g=8,
        tags=["omnivore"],
        ingredients=["150g lean beef", "mixed vegetables", "80g brown rice", "soy"],
        recipe="Stir-fry beef + veg, serve over brown rice.",
    ),
    MealItem(
        name="Apple + almond butter",
        cuisine="american", slot="snack",
        calories=220, protein_g=6, carbs_g=28, fat_g=11, fibre_g=5,
        tags=["omnivore", "vegetarian", "vegan", "pollo_pescatarian", "pescatarian"],
        ingredients=["1 apple", "20g almond butter"],
        recipe="Slice apple, dip.",
    ),
    MealItem(
        name="Cottage cheese + pineapple",
        cuisine="american", slot="snack",
        calories=200, protein_g=22, carbs_g=18, fat_g=4, fibre_g=1,
        tags=["vegetarian", "pollo_pescatarian", "pescatarian"],
        ingredients=["200g cottage cheese", "100g pineapple"],
        recipe="Combine and serve cold.",
    ),

    # ---------------- MEDITERRANEAN ----------------
    MealItem(
        name="Greek yogurt with honey & walnuts",
        cuisine="mediterranean", slot="breakfast",
        calories=350, protein_g=22, carbs_g=30, fat_g=14, fibre_g=3,
        tags=["vegetarian", "pollo_pescatarian", "pescatarian"],
        ingredients=["200g Greek yogurt", "1 tbsp honey", "20g walnuts"],
        recipe="Top yogurt with honey and walnuts.",
    ),
    MealItem(
        name="Shakshuka with whole-grain bread",
        cuisine="mediterranean", slot="breakfast",
        calories=480, protein_g=22, carbs_g=42, fat_g=22, fibre_g=9,
        tags=["vegetarian", "pollo_pescatarian", "pescatarian"],
        ingredients=["3 eggs", "tomato", "pepper", "onion", "feta", "1 slice whole-grain bread"],
        recipe="Simmer tomato base, crack eggs, finish with feta.",
    ),
    MealItem(
        name="Mediterranean chickpea salad",
        cuisine="mediterranean", slot="lunch",
        calories=540, protein_g=22, carbs_g=58, fat_g=20, fibre_g=12,
        tags=["vegetarian", "vegan", "pollo_pescatarian", "pescatarian"],
        ingredients=["200g chickpeas", "cucumber", "tomato", "olives", "feta", "olive oil"],
        recipe="Toss all ingredients with lemon and olive oil.",
    ),
    MealItem(
        name="Grilled chicken souvlaki with tzatziki",
        cuisine="mediterranean", slot="lunch",
        calories=560, protein_g=42, carbs_g=50, fat_g=16, fibre_g=6,
        tags=["omnivore"],
        ingredients=["150g chicken", "80g pita", "tzatziki", "salad"],
        recipe="Grill chicken skewers, assemble in pita.",
    ),
    MealItem(
        name="Baked white fish with lentils",
        cuisine="mediterranean", slot="dinner",
        calories=580, protein_g=40, carbs_g=50, fat_g=18, fibre_g=11,
        tags=["pescatarian", "pollo_pescatarian", "omnivore"],
        ingredients=["180g white fish", "100g lentils", "lemon", "olive oil"],
        recipe="Bake fish; cook lentils; combine with greens.",
    ),
    MealItem(
        name="Stuffed peppers with bulgur & lamb",
        cuisine="mediterranean", slot="dinner",
        calories=620, protein_g=32, carbs_g=55, fat_g=24, fibre_g=10,
        tags=["omnivore"],
        ingredients=["2 peppers", "100g bulgur", "120g lean lamb", "spices"],
        recipe="Stuff peppers; bake at 200°C 35 min.",
    ),
    MealItem(
        name="Hummus with veg sticks",
        cuisine="mediterranean", slot="snack",
        calories=220, protein_g=8, carbs_g=24, fat_g=10, fibre_g=6,
        tags=["vegetarian", "vegan", "pollo_pescatarian", "pescatarian"],
        ingredients=["60g hummus", "carrot", "cucumber", "pepper"],
        recipe="Slice vegetables, dip in hummus.",
    ),

    # ---------------- ASIAN ----------------
    MealItem(
        name="Vegetable congee with egg",
        cuisine="asian", slot="breakfast",
        calories=380, protein_g=18, carbs_g=58, fat_g=8, fibre_g=4,
        tags=["vegetarian", "pollo_pescatarian", "pescatarian", "omnivore"],
        ingredients=["60g rice", "ginger", "greens", "1 egg", "soy"],
        recipe="Simmer rice in stock to creamy texture, top with egg.",
    ),
    MealItem(
        name="Miso soup + tofu rice bowl",
        cuisine="asian", slot="breakfast",
        calories=420, protein_g=22, carbs_g=55, fat_g=10, fibre_g=6,
        tags=["vegetarian", "vegan", "pollo_pescatarian", "pescatarian"],
        ingredients=["miso", "tofu", "rice", "greens"],
        recipe="Prepare miso, fry tofu, serve over rice.",
    ),
    MealItem(
        name="Chicken pho",
        cuisine="asian", slot="lunch",
        calories=520, protein_g=38, carbs_g=55, fat_g=10, fibre_g=5,
        tags=["omnivore"],
        ingredients=["chicken broth", "120g chicken", "rice noodles", "herbs"],
        recipe="Simmer broth, add chicken, top with herbs.",
    ),
    MealItem(
        name="Salmon teriyaki bowl",
        cuisine="asian", slot="lunch",
        calories=600, protein_g=40, carbs_g=60, fat_g=18, fibre_g=6,
        tags=["pescatarian", "pollo_pescatarian", "omnivore"],
        ingredients=["160g salmon", "80g rice", "broccoli", "teriyaki"],
        recipe="Glaze salmon, serve over rice with broccoli.",
    ),
    MealItem(
        name="Tofu pad thai",
        cuisine="asian", slot="dinner",
        calories=560, protein_g=26, carbs_g=70, fat_g=14, fibre_g=7,
        tags=["vegetarian", "vegan", "pollo_pescatarian", "pescatarian"],
        ingredients=["150g tofu", "rice noodles", "vegetables", "peanuts"],
        recipe="Stir-fry tofu + veg + noodles with tamarind sauce.",
    ),
    MealItem(
        name="Beef & broccoli with jasmine rice",
        cuisine="asian", slot="dinner",
        calories=620, protein_g=38, carbs_g=62, fat_g=18, fibre_g=6,
        tags=["omnivore"],
        ingredients=["150g lean beef", "broccoli", "rice", "ginger"],
        recipe="Stir-fry beef + broccoli; serve over jasmine rice.",
    ),
    MealItem(
        name="Edamame",
        cuisine="asian", slot="snack",
        calories=180, protein_g=15, carbs_g=14, fat_g=7, fibre_g=8,
        tags=["vegetarian", "vegan", "pollo_pescatarian", "pescatarian"],
        ingredients=["150g edamame", "sea salt"],
        recipe="Steam and salt.",
    ),

    # ---------------- INDIAN ----------------
    MealItem(
        name="Masala egg scramble with roti",
        cuisine="indian", slot="breakfast",
        calories=420, protein_g=22, carbs_g=38, fat_g=18, fibre_g=6,
        tags=["vegetarian", "pollo_pescatarian", "pescatarian", "omnivore"],
        ingredients=["3 eggs", "onion", "tomato", "spices", "1 roti"],
        recipe="Spice scramble, serve with roti.",
    ),
    MealItem(
        name="Vegetable upma",
        cuisine="indian", slot="breakfast",
        calories=380, protein_g=10, carbs_g=58, fat_g=10, fibre_g=6,
        tags=["vegetarian", "vegan"],
        ingredients=["semolina", "vegetables", "mustard seeds", "curry leaves"],
        recipe="Roast semolina, sauté veg, combine.",
    ),
    MealItem(
        name="Chicken tikka salad",
        cuisine="indian", slot="lunch",
        calories=540, protein_g=42, carbs_g=40, fat_g=18, fibre_g=8,
        tags=["omnivore", "pollo_pescatarian"],
        ingredients=["150g chicken", "yogurt marinade", "salad", "naan"],
        recipe="Marinate & grill chicken; serve on salad.",
    ),
    MealItem(
        name="Chana masala with brown rice",
        cuisine="indian", slot="lunch",
        calories=560, protein_g=20, carbs_g=80, fat_g=14, fibre_g=14,
        tags=["vegetarian", "vegan", "pollo_pescatarian", "pescatarian"],
        ingredients=["200g chickpeas", "tomato", "spices", "rice"],
        recipe="Simmer chickpeas in spiced tomato gravy.",
    ),
    MealItem(
        name="Lamb curry with cauliflower rice",
        cuisine="indian", slot="dinner",
        calories=560, protein_g=36, carbs_g=24, fat_g=30, fibre_g=8,
        tags=["omnivore", "keto"],
        ingredients=["150g lamb", "yogurt", "spices", "cauliflower rice"],
        recipe="Slow-cook lamb curry; serve over cauli rice.",
    ),
    MealItem(
        name="Paneer tikka masala with roti",
        cuisine="indian", slot="dinner",
        calories=620, protein_g=24, carbs_g=50, fat_g=30, fibre_g=8,
        tags=["vegetarian"],
        ingredients=["150g paneer", "tomato", "cream", "roti"],
        recipe="Grill paneer, simmer in masala.",
    ),
    MealItem(
        name="Roasted chana (chickpeas)",
        cuisine="indian", slot="snack",
        calories=200, protein_g=12, carbs_g=28, fat_g=4, fibre_g=9,
        tags=["vegetarian", "vegan", "pollo_pescatarian", "pescatarian"],
        ingredients=["60g roasted chana", "chaat masala"],
        recipe="Toss with spices.",
    ),

    # ---------------- MEXICAN ----------------
    MealItem(
        name="Huevos rancheros",
        cuisine="mexican", slot="breakfast",
        calories=480, protein_g=24, carbs_g=42, fat_g=20, fibre_g=9,
        tags=["vegetarian", "pollo_pescatarian", "pescatarian", "omnivore"],
        ingredients=["2 eggs", "tortilla", "beans", "salsa"],
        recipe="Fry eggs, serve on tortilla with beans + salsa.",
    ),
    MealItem(
        name="Chicken burrito bowl",
        cuisine="mexican", slot="lunch",
        calories=620, protein_g=45, carbs_g=60, fat_g=18, fibre_g=12,
        tags=["omnivore"],
        ingredients=["150g chicken", "rice", "black beans", "salsa", "avocado"],
        recipe="Build bowl with all toppings.",
    ),
    MealItem(
        name="Black bean & corn tacos (vegan)",
        cuisine="mexican", slot="lunch",
        calories=540, protein_g=22, carbs_g=80, fat_g=12, fibre_g=18,
        tags=["vegan", "vegetarian"],
        ingredients=["black beans", "corn", "tortillas", "lime", "cilantro"],
        recipe="Heat beans + corn; assemble tacos.",
    ),
    MealItem(
        name="Carne asada with peppers",
        cuisine="mexican", slot="dinner",
        calories=600, protein_g=42, carbs_g=30, fat_g=30, fibre_g=6,
        tags=["omnivore", "keto"],
        ingredients=["150g flank steak", "peppers", "lime", "cilantro"],
        recipe="Grill steak + peppers, finish with lime.",
    ),
    MealItem(
        name="Fish tacos with cabbage slaw",
        cuisine="mexican", slot="dinner",
        calories=540, protein_g=32, carbs_g=55, fat_g=16, fibre_g=9,
        tags=["pescatarian", "pollo_pescatarian", "omnivore"],
        ingredients=["160g white fish", "tortillas", "slaw", "lime crema"],
        recipe="Pan-fry fish, assemble tacos.",
    ),
    MealItem(
        name="Guacamole + jicama",
        cuisine="mexican", slot="snack",
        calories=220, protein_g=3, carbs_g=22, fat_g=14, fibre_g=10,
        tags=["vegetarian", "vegan", "pollo_pescatarian", "pescatarian", "keto"],
        ingredients=["avocado", "lime", "jicama"],
        recipe="Mash avocado with lime; serve with jicama sticks.",
    ),

    # ---------------- MIDDLE EASTERN ----------------
    MealItem(
        name="Labneh with cucumber & olive oil",
        cuisine="middle_eastern", slot="breakfast",
        calories=320, protein_g=16, carbs_g=18, fat_g=20, fibre_g=3,
        tags=["vegetarian", "pollo_pescatarian", "pescatarian"],
        ingredients=["200g labneh", "cucumber", "olive oil", "za'atar"],
        recipe="Spread labneh, drizzle oil, top za'atar.",
    ),
    MealItem(
        name="Falafel & tabbouleh wrap",
        cuisine="middle_eastern", slot="lunch",
        calories=560, protein_g=18, carbs_g=70, fat_g=22, fibre_g=12,
        tags=["vegetarian", "vegan"],
        ingredients=["falafel", "tabbouleh", "tahini", "wrap"],
        recipe="Wrap falafel + tabbouleh in flatbread.",
    ),
    MealItem(
        name="Chicken shawarma plate",
        cuisine="middle_eastern", slot="lunch",
        calories=620, protein_g=42, carbs_g=55, fat_g=22, fibre_g=8,
        tags=["omnivore", "pollo_pescatarian"],
        ingredients=["150g chicken", "rice", "salad", "tahini"],
        recipe="Marinate + grill chicken; plate with rice + salad.",
    ),
    MealItem(
        name="Mujadara (lentils & rice)",
        cuisine="middle_eastern", slot="dinner",
        calories=540, protein_g=20, carbs_g=85, fat_g=10, fibre_g=14,
        tags=["vegetarian", "vegan"],
        ingredients=["lentils", "rice", "caramelised onion", "cumin"],
        recipe="Simmer lentils + rice; top with onion.",
    ),
    MealItem(
        name="Grilled fish with freekeh",
        cuisine="middle_eastern", slot="dinner",
        calories=580, protein_g=38, carbs_g=55, fat_g=18, fibre_g=9,
        tags=["pescatarian", "pollo_pescatarian", "omnivore"],
        ingredients=["160g fish", "freekeh", "herbs"],
        recipe="Grill fish; cook freekeh; combine.",
    ),
    MealItem(
        name="Dates & walnuts",
        cuisine="middle_eastern", slot="snack",
        calories=200, protein_g=4, carbs_g=30, fat_g=9, fibre_g=5,
        tags=["vegetarian", "vegan", "pollo_pescatarian", "pescatarian"],
        ingredients=["3 dates", "20g walnuts"],
        recipe="Stuff dates with walnuts.",
    ),

    # ---------------- AFRICAN ----------------
    MealItem(
        name="Akara (bean fritters) with avocado",
        cuisine="african", slot="breakfast",
        calories=380, protein_g=18, carbs_g=34, fat_g=18, fibre_g=10,
        tags=["vegetarian", "vegan"],
        ingredients=["black-eyed peas", "onion", "spice", "avocado"],
        recipe="Fritter beans; serve with avocado.",
    ),
    MealItem(
        name="Jollof rice with grilled chicken",
        cuisine="african", slot="lunch",
        calories=620, protein_g=38, carbs_g=70, fat_g=16, fibre_g=7,
        tags=["omnivore", "pollo_pescatarian"],
        ingredients=["rice", "tomato", "spices", "150g chicken"],
        recipe="Cook jollof rice; grill chicken; combine.",
    ),
    MealItem(
        name="Egusi soup with fish (low-carb)",
        cuisine="african", slot="dinner",
        calories=540, protein_g=38, carbs_g=18, fat_g=34, fibre_g=6,
        tags=["pescatarian", "pollo_pescatarian", "omnivore", "keto"],
        ingredients=["melon seeds", "fish", "leafy greens", "spices"],
        recipe="Simmer soup base; add fish.",
    ),
    MealItem(
        name="Plantain & peanut snack",
        cuisine="african", slot="snack",
        calories=220, protein_g=5, carbs_g=32, fat_g=10, fibre_g=4,
        tags=["vegetarian", "vegan"],
        ingredients=["ripe plantain", "20g peanuts"],
        recipe="Roast plantain; serve with peanuts.",
    ),

    # ---------------- NORDIC ----------------
    MealItem(
        name="Skyr with berries & rye crisps",
        cuisine="nordic", slot="breakfast",
        calories=320, protein_g=24, carbs_g=34, fat_g=6, fibre_g=6,
        tags=["vegetarian", "pollo_pescatarian", "pescatarian"],
        ingredients=["200g skyr", "berries", "rye crispbread"],
        recipe="Top skyr with berries; serve with crispbread.",
    ),
    MealItem(
        name="Open-faced herring sandwich",
        cuisine="nordic", slot="lunch",
        calories=460, protein_g=24, carbs_g=42, fat_g=18, fibre_g=8,
        tags=["pescatarian", "pollo_pescatarian", "omnivore"],
        ingredients=["herring", "rye bread", "egg", "mustard", "dill"],
        recipe="Layer ingredients on rye.",
    ),
    MealItem(
        name="Salmon with root vegetables",
        cuisine="nordic", slot="dinner",
        calories=600, protein_g=38, carbs_g=42, fat_g=24, fibre_g=9,
        tags=["pescatarian", "pollo_pescatarian", "omnivore"],
        ingredients=["180g salmon", "carrots", "parsnip", "potato"],
        recipe="Roast root veg; bake salmon.",
    ),
    MealItem(
        name="Wasa crispbread + cottage cheese",
        cuisine="nordic", slot="snack",
        calories=180, protein_g=14, carbs_g=20, fat_g=4, fibre_g=4,
        tags=["vegetarian", "pollo_pescatarian", "pescatarian"],
        ingredients=["2 Wasa", "100g cottage cheese", "cucumber"],
        recipe="Top crispbread with cottage cheese + cucumber.",
    ),

    # ---------------- KETO / LOW-CARB ----------------
    MealItem(
        name="Keto avocado-boiled-egg plate",
        cuisine="american", slot="breakfast",
        calories=420, protein_g=20, carbs_g=8, fat_g=34, fibre_g=7,
        tags=["keto", "vegetarian", "pollo_pescatarian", "pescatarian"],
        ingredients=["2 boiled eggs", "1 avocado", "olive oil", "salt"],
        recipe="Halve eggs + avocado; drizzle oil.",
    ),
    MealItem(
        name="Steak + buttered asparagus",
        cuisine="american", slot="dinner",
        calories=620, protein_g=42, carbs_g=10, fat_g=42, fibre_g=5,
        tags=["keto", "omnivore"],
        ingredients=["160g steak", "asparagus", "butter"],
        recipe="Pan-sear steak; sauté asparagus in butter.",
    ),
]


# --------------------------------------------------------------------------- #
# Filters / queries                                                           #
# --------------------------------------------------------------------------- #
def by_cuisine(cuisine: str) -> List[MealItem]:
    return [m for m in MEAL_LIBRARY if m.cuisine == cuisine]


def by_diet(diet: DietaryPreference) -> List[MealItem]:
    return [m for m in MEAL_LIBRARY if diet.value in m.tags]


def by_slot(slot: str) -> List[MealItem]:
    return [m for m in MEAL_LIBRARY if m.slot == slot]


# Dietary compatibility matrix: for each DietaryPreference, which
# meal tags are acceptable.
DIET_COMPATIBILITY = {
    DietaryPreference.OMNIVORE: {
        "omnivore", "pollo_pescatarian", "pescatarian",
        "vegetarian", "vegan", "keto", "mediterranean",
    },
    DietaryPreference.PESCATARIAN: {
        "pescatarian", "vegetarian", "vegan",
    },
    DietaryPreference.POLLO_PESCATARIAN: {
        "pollo_pescatarian", "pescatarian", "vegetarian", "vegan",
    },
    DietaryPreference.VEGETARIAN: {
        "vegetarian", "vegan",
    },
    DietaryPreference.VEGAN: {
        "vegan",
    },
    DietaryPreference.KETO: {
        "keto", "omnivore", "pollo_pescatarian", "pescatarian",
    },
    DietaryPreference.MEDITERRANEAN: {
        "omnivore", "pollo_pescatarian", "pescatarian",
        "vegetarian", "vegan", "mediterranean",
    },
    DietaryPreference.LOW_FODMAP: {
        "omnivore", "pollo_pescatarian", "pescatarian",
        "vegetarian", "vegan",
    },
    DietaryPreference.HALAL: {
        "omnivore", "pollo_pescatarian", "pescatarian",
        "vegetarian", "vegan", "mediterranean",
    },
    DietaryPreference.KOSHER: {
        "omnivore", "pollo_pescatarian", "pescatarian",
        "vegetarian", "vegan", "mediterranean",
    },
    DietaryPreference.FLEXIBLE: {
        "omnivore", "pollo_pescatarian", "pescatarian",
        "vegetarian", "vegan", "keto", "mediterranean",
    },
}


def filter_compatible(diet: DietaryPreference,
                      allergens: List[str]) -> List[MealItem]:
    """Filter meals compatible with a given dietary pattern + allergens.

    Mediterranean diet is implemented as a pattern (any meal that's
    reasonably Mediterranean — includes most omnivore / pescatarian /
    vegetarian options). The cuisine filter is applied separately.
    """
    acceptable = DIET_COMPATIBILITY.get(diet, set())
    out = []
    for m in MEAL_LIBRARY:
        # A meal is compatible if any of its tags intersects acceptable
        if not (set(m.tags) & acceptable):
            continue
        # Allergen check on ingredients (very simple keyword search)
        ing_text = " ".join(m.ingredients).lower()
        if any(a.lower() in ing_text for a in allergens):
            continue
        out.append(m)
    return out

# --------------------------------------------------------------------------- #
# Plan assembler                                                              #
# --------------------------------------------------------------------------- #
def assemble_day(
    cuisine: str, diet: DietaryPreference, target_calories: float,
    meals_per_day: int = 3, allergens: Optional[List[str]] = None,
) -> MealPlan:
    """Pick a breakfast, lunch, dinner (and snack) that best match the
    calorie target while honouring dietary pattern and cuisine."""
    pool = filter_compatible(diet, allergens or [])
    if cuisine:
        pool = [m for m in pool if m.cuisine == cuisine]
    if not pool:
        pool = filter_compatible(diet, allergens or [])

    if meals_per_day == 3:
        chosen_slots = ["breakfast", "lunch", "dinner"]
    elif meals_per_day == 4:
        chosen_slots = ["breakfast", "lunch", "snack", "dinner"]
    elif meals_per_day == 5:
        chosen_slots = ["breakfast", "snack", "lunch", "snack", "dinner"]
    else:
        chosen_slots = ["dinner"]

    picks: List[MealItem] = []
    for slot in chosen_slots:
        candidates = [m for m in pool if m.slot == slot]
        if not candidates:
            candidates = [m for m in filter_compatible(diet, allergens or [])
                          if m.slot == slot]
        if candidates:
            used = sum(m.calories for m in picks)
            remaining = target_calories - used
            candidates.sort(key=lambda m: abs(m.calories - remaining))
            picks.append(candidates[0])

    cu = cuisine or "mixed"
    return MealPlan(
        name=f"{diet.value.title()} day plan ({cu.title()})",
        cuisine=cuisine or "", diet=diet, meals=picks,
        notes=[
            f"Target {target_calories:.0f} kcal",
            f"Total {sum(m.calories for m in picks):.0f} kcal",
            f"Protein {sum(m.protein_g for m in picks):.0f} g",
        ],
    )


# --------------------------------------------------------------------------- #
# Weekly rotation                                                             #
# --------------------------------------------------------------------------- #
def assemble_week(
    cuisine: str, diet: DietaryPreference, target_calories: float,
    meals_per_day: int = 3, allergens: Optional[List[str]] = None,
    days: int = 7, secondary_cuisines: Optional[List[str]] = None,
) -> List[MealPlan]:
    """Generate a `days`-day rotation that cycles through compatible
    meals before repeating. Accepts optional secondary cuisines to
    draw from when the primary is exhausted.
    """
    out: List[MealPlan] = []
    cuisines = [cuisine] + (secondary_cuisines or [])
    cuisines = [c for c in cuisines if c]
    if not cuisines:
        cuisines = ["american", "mediterranean"]

    used_by_slot = {
        "breakfast": [], "lunch": [], "dinner": [], "snack": [],
    }

    for day_idx in range(days):
        picks: List[MealItem] = []
        slots_order = {
            3: ["breakfast", "lunch", "dinner"],
            4: ["breakfast", "lunch", "snack", "dinner"],
            5: ["breakfast", "snack", "lunch", "snack", "dinner"],
        }.get(meals_per_day, ["dinner"])

        for slot in slots_order:
            chosen = None
            for cu in cuisines:
                pool = [m for m in filter_compatible(diet, allergens or [])
                        if m.cuisine == cu and m.slot == slot]
                if not pool:
                    continue
                used = used_by_slot[slot]
                fresh = [m for m in pool if (m.name, m.cuisine) not in used]
                if not fresh:
                    fresh = pool
                used_cal = sum(m.calories for m in picks)
                remaining = target_calories - used_cal
                fresh.sort(key=lambda m: (abs(m.calories - remaining),
                                          random.random()))
                chosen = fresh[0]
                used_by_slot[slot].append((chosen.name, chosen.cuisine))
                break

            if chosen is None:
                pool = [m for m in filter_compatible(diet, allergens or [])
                        if m.slot == slot]
                if pool:
                    used_cal = sum(m.calories for m in picks)
                    remaining = target_calories - used_cal
                    pool.sort(key=lambda m: abs(m.calories - remaining))
                    chosen = pool[0]
                    used_by_slot[slot].append((chosen.name, chosen.cuisine))

            if chosen:
                picks.append(chosen)

        day_name = ["Monday", "Tuesday", "Wednesday", "Thursday",
                    "Friday", "Saturday", "Sunday"][day_idx % 7]
        cu_label = "+".join(cuisines) if len(cuisines) > 1 else cuisines[0]
        out.append(MealPlan(
            name=f"{day_name} - {cu_label.title()} ({diet.value.title()})",
            cuisine=cuisines[0], diet=diet, meals=picks,
            notes=[
                f"Target {target_calories:.0f} kcal",
                f"Total {sum(m.calories for m in picks):.0f} kcal",
                f"Protein {sum(m.protein_g for m in picks):.0f} g",
                f"Carbs   {sum(m.carbs_g   for m in picks):.0f} g",
                f"Fat     {sum(m.fat_g     for m in picks):.0f} g",
                f"Fibre   {sum(m.fibre_g   for m in picks):.0f} g",
            ],
        ))
    return out
