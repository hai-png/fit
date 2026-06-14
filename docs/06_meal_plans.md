# 06 — Meal Plans Library

## 6.1 Data model

```python
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
    tags: List[str]                 # diet compatibility flags
    ingredients: List[str]
    recipe: str
```

Every meal carries full nutrition data so the recommender can
assemble calorie-precise daily plans. `tags` declare which dietary
patterns the meal fits. `recipe` is a short instruction string.

## 6.2 Cuisines

| Cuisine | Sample meals |
|---|---|
| American | Greek yogurt parfait, turkey sandwich, sheet-pan salmon |
| Mediterranean | Greek yogurt & walnuts, shakshuka, chickpea salad, baked fish + lentils |
| Asian | Congee, miso tofu bowl, pho, teriyaki salmon, tofu pad thai |
| Indian | Masala scramble, upma, chicken tikka salad, chana masala, paneer tikka |
| Mexican | Huevos rancheros, burrito bowl, black-bean tacos, carne asada, fish tacos |
| Middle Eastern | Labneh, falafel wrap, chicken shawarma, mujadara, grilled fish + freekeh |
| African | Akara, jollof rice, egusi soup |
| Nordic | Skyr, open-faced herring, salmon + root veg |

## 6.3 Diet compatibility

Each `MealItem` is tagged with compatible diets:

```python
tags=["omnivore", "pollo_pescatarian", "pescatarian", "vegetarian", "vegan"]
```

A meal is **compatible with a diet** if any of its tags intersect
with the diet's accepted set:

| Diet | Accepts tags |
|---|---|
| omnivore | omnivore, pollo_pescatarian, pescatarian, vegetarian, vegan, keto, mediterranean |
| pescatarian | pescatarian, vegetarian, vegan |
| pollo_pescatarian | pollo_pescatarian, pescatarian, vegetarian, vegan |
| vegetarian | vegetarian, vegan |
| vegan | vegan |
| keto | keto, omnivore, pollo_pescatarian, pescatarian |
| mediterranean | omnivore, pollo_pescatarian, pescatarian, vegetarian, vegan, mediterranean |
| low_fodmap | omnivore, pollo_pescatarian, pescatarian, vegetarian, vegan |
| halal | omnivore, pollo_pescatarian, pescatarian, vegetarian, vegan, mediterranean |
| kosher | omnivore, pollo_pescatarian, pescatarian, vegetarian, vegan, mediterranean |
| flexible | all |

## 6.4 Allergen filter

After the diet filter, a simple keyword filter on `ingredients`
removes meals containing the client's allergens:

```python
allergens=["dairy", "nuts"]
# removes any meal with ingredient text containing "dairy" or "nuts"
```

The filter is intentionally conservative — when in doubt, exclude.

## 6.5 Cuisine filter

If a cuisine is requested (from `cuisine_pick`), only meals tagged
with that cuisine are considered. If no compatible meals exist,
the filter is **dropped** so a meal is still produced.

## 6.6 Daily plan assembly

`assemble_day()` greedily picks the closest-calorie meal for each
slot:

```python
assemble_day(
    cuisine="mediterranean",
    diet=DietaryPreference.MEDITERRANEAN,
    target_calories=1381,
    meals_per_day=4,
    allergens=[],
)
# MealPlan(
#   name='Mediterranean (Mediterranean) day plan',
#   cuisine='mediterranean',
#   diet=MEDITERRANEAN,
#   meals=[
#     MealItem('Shakshuka with whole-grain bread', 480 kcal, ...),
#     MealItem('Grilled chicken souvlaki with tzatziki', 560 kcal, ...),
#     MealItem('Hummus with veg sticks', 220 kcal, ...),
#     MealItem('Baked white fish with lentils', 580 kcal, ...),
#   ],
#   notes=['Target 1381 kcal', 'Total 1840 kcal', 'Protein 100 g'],
# )
```

### Slot layout

| `meals_per_day` | Slots |
|---|---|
| 3 | breakfast, lunch, dinner |
| 4 | breakfast, lunch, snack, dinner |
| 5 | breakfast, snack, lunch, snack, dinner |
| 1 (OMAD) | dinner |

### Greedy algorithm

For each slot in order:
1. Filter library to that slot + compatible diet + allergens + cuisine.
2. Sort by absolute difference between meal.calories and remaining target.
3. Pick the first match.

This is a simple heuristic. A future version could use linear
programming to hit macro targets exactly.

## 6.7 Adding a new meal

```python
from fitness_engine.meal_plans import MealItem, MEAL_LIBRARY

MEAL_LIBRARY.append(MealItem(
    name="Tofu & vegetable stir-fry",
    cuisine="asian",
    slot="dinner",
    calories=520, protein_g=28, carbs_g=58, fat_g=14, fibre_g=8,
    tags=["vegetarian", "vegan"],
    ingredients=["200g firm tofu", "mixed vegetables", "rice", "soy"],
    recipe="Stir-fry tofu + vegetables; serve over rice.",
))
```

The recommender will consider it on the next call.

## 6.8 Sample-day macros

The total macros from a sample day for a 1381 kcal Mediterranean
fat-loss plan:

| Meal | kcal | P | C | F | Fibre |
|---|---|---|---|---|---|
| Shakshuka | 480 | 22 | 42 | 22 | 9 |
| Chicken souvlaki | 560 | 42 | 50 | 16 | 6 |
| Hummus + veg | 220 | 8 | 24 | 10 | 6 |
| White fish + lentils | 580 | 40 | 50 | 18 | 11 |
| **Total** | **1840** | **112** | **166** | **66** | **32** |

The total is **higher** than the calorie target because each meal
is itself a complete portion; in practice the client eats a fraction
of each. Use the recipe's `recipe` field to communicate portioning.

A future improvement: scale meals by `target_calories / sum(meal.calories)`.

## 6.9 Cuisine × diet matrix

| Cuisine \ Diet | omni | pollo | pesc | veg | vegan | keto |
|---|---|---|---|---|---|---|
| american | 8 | 8 | 8 | 8 | 6 | 2 |
| mediterranean | 7 | 7 | 7 | 7 | 6 | 1 |
| asian | 6 | 6 | 6 | 6 | 5 | 0 |
| indian | 6 | 6 | 5 | 6 | 5 | 1 |
| mexican | 6 | 5 | 5 | 6 | 5 | 1 |
| middle_eastern | 6 | 6 | 5 | 6 | 5 | 0 |
| african | 4 | 4 | 3 | 4 | 3 | 1 |
| nordic | 4 | 4 | 4 | 4 | 0 | 0 |

(Numbers are meal counts in the library; the recommender falls back
across cuisines when the requested one has no compatible meal.)

## 6.10 Weekly rotation

`assemble_week()` produces a `days`-day plan with cycling variety:

```python
from fitness_engine import assemble_week, DietaryPreference
week = assemble_week(
    cuisine="mediterranean",
    diet=DietaryPreference.MEDITERRANEAN,
    target_calories=1381,
    meals_per_day=4,
    secondary_cuisines=["asian"],   # used when primary is exhausted
    days=7,
)
```

Returns a `List[MealPlan]`, one per day. Algorithm:

1. For each day, iterate over `breakfast/lunch/snack/dinner` slots
2. For each slot, try the primary cuisine first
3. Pick the meal closest to the remaining daily calorie target
4. Track (name, cuisine) per slot — exclude already-used this week
5. Fall back to secondary cuisines when primary is exhausted
6. After all meals used, cycle back to the start

### Rotation example output

```
Monday    Shakshuka          (480 kcal)   Hummus    (220 kcal)   ...
Tuesday   Greek yogurt       (350 kcal)   Hummus    (220 kcal)   ...
Wednesday Shakshuka          (480 kcal)   Falafel   (TBD)        ... (uses asian fallback)
```

## 6.11 Future extensions

* Per-meal macro hit / deficit reporting
* Portion-scaling to hit calorie target exactly
* Grocery-list generator
* Cuisine-day pairing for variety
* More meals per cuisine (current: 4-8 per major cuisine)

