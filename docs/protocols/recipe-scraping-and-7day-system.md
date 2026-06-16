# Recipe Scraping, Normalization, Filtering, and 7-Day Meal Planning

## File organization

Meal/recipe files are now organized as follows:

```text
scripts/
├── scrape_external_recipes.py              # Trifecta scraper + M&S direct scrape attempt
├── import_muscleandstrength_recipes.py     # imports attached M&S export
├── build_unified_recipe_database.py        # builds canonical clean external recipe DB
└── generate_common_profile_meal_plans.py   # generates common-profile 7-day plans

data/recipes/
├── unified_external_recipes.json           # canonical planner database
├── normalized/
│   ├── muscleandstrength_recipes.json      # normalized M&S attachment
│   └── trifecta_recipes.json               # normalized Trifecta scrape
└── status/
    └── muscleandstrength_scrape_status.json

output/
├── sample_7day_meal_plan.json
├── sample_7day_meal_plan_audit.json
└── common_meal_plans/
    ├── README.md
    └── *.json
```

## External recipe sources

### Muscle & Strength attachment

Imported with:

```bash
python3 scripts/import_muscleandstrength_recipes.py /home/user/uploads/recipes.json \
  --out data/recipes/normalized/muscleandstrength_recipes.json
```

Result:

```text
149 recipes imported
148 planner-eligible before strict unified quality filtering
147 recipes retained in the canonical unified database
```

### Trifecta scrape

Scraped/normalized with:

```bash
python3 scripts/scrape_external_recipes.py --skip-mns \
  --out data/recipes/normalized/trifecta_recipes.json
```

Result:

```text
256 normalized entries
43 planner-eligible before strict unified quality filtering
41 recipes retained in the canonical unified database
```

### Muscle & Strength direct scraping status

Direct headless scraping of M&S was implemented but the site returned Cloudflare/403 in this environment. The user-attached export was therefore used as the high-quality M&S source.

Status is recorded in:

```text
data/recipes/status/muscleandstrength_scrape_status.json
```

## Unified standardized recipe file

Built with:

```bash
python3 scripts/build_unified_recipe_database.py \
  --out data/recipes/unified_external_recipes.json
```

Current canonical database:

```text
323 clean external recipes
147 Muscle & Strength
137 Trifecta
```

Standard schema includes:

- `id`
- `source`
- `source_url`
- `title`
- `description`
- `slot`
- `cuisine`
- `diet_tags`
- `goal_tags`
- `prep_time_min`
- `cook_time_min`
- `total_time_min`
- `servings`
- `difficulty`
- `nutrition_per_serving`
- `macro_ratio`
- `ingredients`
- `instructions`
- `quality`

## Quality filtering

Recipes are excluded unless they have:

- sane calories/protein/carbs/fat
- at least 3 clean ingredients
- at least 1 usable instruction
- no obvious page artifacts inside ingredients
- clean diet tags
- corrected slot classification

The cleaner removes artifacts such as:

- `Tools`
- `Kitchen Needs`
- `Step 1`
- `Cook Time`
- `Prep Time`
- `Yield`
- CTA/article fragments
- social/share text

## 7-day planner

Main API:

```python
from fitness_engine import assemble_7_day_meal_plan

week = assemble_7_day_meal_plan(
    diet=profile.dietary_preference,
    target_calories=rec.energy.calorie_target,
    target_macros=rec.nutrition.macros,
    meals_per_day=profile.meals_per_day,
    allergens=profile.allergies,
    preferred_cuisines=profile.preferred_cuisines,
    include_external=True,
    include_internal=False,
)
```

The recommender now exposes this automatically:

```python
rec.nutrition.weekly_meal_plan
```

The legacy `rec.nutrition.meal_plan` is now the first day of the same external-only weekly plan.

## Meal selection algorithm

For each day:

1. Load only the unified external recipe database.
2. Hard-filter by diet compatibility and allergens.
3. Soft-score cuisine preference.
4. Allocate calories by slot:
   - 3 meals: 30 / 35 / 35
   - 4 meals: 25 / 30 / 15 / 30
   - 5 meals: 22 / 12 / 28 / 12 / 26
5. Score candidates by calorie fit, protein fit, cuisine preference, repeat penalty, macro confidence, and fiber.
6. Lunch and dinner can substitute for each other to prevent tiny dinner pools from causing repeats.
7. Add external high-protein snack recipes if protein density is too low.
8. Add external high-fiber recipes if known/estimated fiber is too low.
9. Portion-scale the day to target calories.
10. Generate alternatives for each meal from the same slot and similar macro target.

## Alternatives

`SevenDayMealPlan.alternatives` contains alternative meals for each selected meal:

```python
week.alternatives[0].day
week.alternatives[0].meal_slot
week.alternatives[0].selected
week.alternatives[0].alternatives
```

Each alternative is portion-scaled close to the selected meal's calorie target.

## Quality audit

Audit API:

```python
from fitness_engine import audit_7_day_meal_plan

audit = audit_7_day_meal_plan(rec.nutrition.weekly_meal_plan)
```

Sample profile result:

```text
Grade: A
Score: 100/100
Source mix: Trifecta 9, Muscle & Strength 18, Daring Gourmet 1
```

See:

- `../reports/meal-plan-quality-audit.md`
- `output/sample_7day_meal_plan_audit.json`

## Common profile meal plans

Generated with:

```bash
python3 scripts/generate_common_profile_meal_plans.py
```

Output:

```text
output/common_meal_plans/
├── README.md
├── male_fat_loss_omnivore.json
├── female_fat_loss_gluten_free.json
├── male_muscle_gain_omnivore.json
├── female_recomp_vegetarian.json
├── male_vegan_muscle_gain.json
├── male_keto_fat_loss.json
└── adult_general_health_mediterranean.json
```

Each JSON contains:

- profile
- calories/macros
- audit result
- 7-day meal plan
- alternatives per meal
- shopping list
- protocol notes

## Ethiopian recipe expansion

Added scraper/import support for the Ethiopian recipe URL set:

```bash
python3 scripts/scrape_ethiopian_recipes.py \
  --out data/recipes/normalized/ethiopian_recipes.json

python3 scripts/build_unified_recipe_database.py \
  --out data/recipes/unified_external_recipes.json
```

Result from the supplied Ethiopian links/search pages:

```text
normalized Ethiopian recipes: 50
planner-eligible Ethiopian recipes before strict unified filtering: 39
```

Unified database after adding Ethiopian recipes:

```text
clean external recipes total: 323
Muscle & Strength: 147
Trifecta: 137
Ethiopian/African sources: 39
```

Ethiopian source domains retained include:

- africanbites.com
- aspicyperspective.com
- chopthegreens.com
- cookedbyjulie.com
- daringgourmet.com
- feastingathome.com
- fermentingforfoodies.com
- forksoverknives.com
- glebekitchen.com
- globalkitchentravels.com
- honest-food.net
- lowcarbafrica.com
- thespiceadventuress.com

Common profile plans now include Ethiopian-focused examples:

- `output/common_meal_plans/ethiopian_omnivore_fat_loss.json`
- `output/common_meal_plans/ethiopian_vegan_recomp.json`

## Trifecta full systematic rescrape update

The Trifecta scraper was upgraded to avoid under-recognizing eligible recipes:

- Crawls all topic pages.
- Parses every article found from the topic index.
- Detects listicle/roundup pages and follows internal recipe links inside them.
- Handles nutrition labels such as `Calories Per Serving`, `Total Fat`, and `Total Carbohydrates` where values are separated by newlines.
- Keeps recipe-like pages in normalized data even when macros are missing, but only marks as planner-eligible when macros are sane.

Updated result:

```text
Trifecta normalized entries: 371
Trifecta planner-eligible before strict unified filtering: 166
Trifecta clean unified planner recipes: 137
```
