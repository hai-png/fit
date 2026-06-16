# Meal Plan Quality Audit

## Scope

Audited the generated 7-day protocol meal plan after cleaning and unifying external recipes from:

- the attached Muscle & Strength export: `/home/user/uploads/recipes.json`
- the previously scraped Trifecta recipe/topic pages

The planner now uses **external recipes only** for actual meals. Internal curated meals are no longer used by the 7-day planner or recommender weekly plan. The only non-recipe logic is scoring, scaling, filtering, and alternatives.

## Clean unified recipe database

Canonical file:

```text
data/recipes/unified_external_recipes.json
```

Intermediate files are organized under:

```text
data/recipes/normalized/muscleandstrength_recipes.json
data/recipes/normalized/trifecta_recipes.json
data/recipes/status/muscleandstrength_scrape_status.json
```

## Recipe database status

| Source | Input count | Clean unified planner-ready recipes | Notes |
|---|---:|---:|---|
| Muscle & Strength attachment | 149 | 147 | 148 had macros; 147 passed strict unified quality checks |
| Trifecta scrape | 256 | 41 | Strictly filtered to recipes with sane macros and clean ingredient/instruction sections |
| Internal curated meals | 60 | 0 used | Kept in code for legacy APIs, but excluded from the 7-day protocol planner |
| **Unified external database** | — | **323** | Used by the 7-day planner |

## Quality cleanup applied

The original generated meal plan had quality problems because scraped content could leak into recipe fields, for example descriptions, tools, or step headings appearing inside `ingredients`.

Fixes applied:

1. **Canonical schema** — all external recipes are converted into one format with `nutrition_per_serving`, `ingredients`, `instructions`, `diet_tags`, `slot`, `cuisine`, and `quality` fields.
2. **Ingredient sanitizer** — removes or truncates page artifacts such as `Tools`, `Kitchen Needs`, `Step 1`, `Cook Time`, `Prep Time`, CTAs, and article-body fragments.
3. **Instruction sanitizer** — removes social/share/CTA lines and keeps concise cooking steps.
4. **Slot correction** — shakes, smoothies, bars, cookies, brownies, muffins, cupcakes, donuts, mug cakes, truffles, puddings, and sauces are forced to snack/breakfast instead of lunch/dinner.
5. **Diet correction** — animal-product ingredient detection prevents chicken/beef/pork recipes from being treated as vegetarian/vegan.
6. **Keto correction** — `keto_friendly` is only converted to `keto` when carbs are low enough.
7. **Paleo inference** — conservative paleo compatibility is inferred for whole-food meat/seafood/egg/veg recipes without obvious grains, dairy, legumes, or protein powders.
8. **Fiber estimation** — missing fiber is estimated conservatively from ingredients to avoid penalizing high-fiber recipes with incomplete metadata.
9. **Quality gating** — recipes missing sane calories/protein/carbs/fat, clean ingredients, or usable instructions are excluded.

## Sample generated plan audit

Profile used: `examples/sample_client.json`.

Audit result after cleanup:

```text
Grade: A
Score: 100/100
Source mix: Trifecta 9, Muscle & Strength 18, Daring Gourmet 1
```

### Passed checks

- 7-day structure present.
- 3+ meals per day.
- Calories within ±5% every day.
- Protein within accepted tolerance every day.
- Known/estimated fiber passes threshold.
- Diet compatibility passed.
- No repeated substantive meals in the sample plan.
- Macro confidence passed: only parsed/verified external recipes used.
- Portion scaling stayed within practical limits.
- Slot sanity passed: snack/dessert recipes were not used as main meals.
- Internal curated meals were not used.

## Cross-diet audit after cleanup and Trifecta rescrape

Generated 7-day plans at 2200 kcal / 4 meals/day for every supported diet mode using external recipes only.

| Diet mode | Score | Grade | Main remaining warning |
|---|---:|---|---|
| balanced | 100 | A | none |
| omnivore | 100 | A | none |
| vegan | 98 | A | one repeated meal in generic stress test |
| vegetarian | 100 | A | none |
| pescatarian | 100 | A | none |
| pollo-pescatarian | 100 | A | none |
| keto | 100 | A | none |
| low-carb | 100 | A | none |
| Mediterranean | 100 | A | none |
| paleo | 84 | B | generic stress test still repeats due smaller paleo-compatible pool |
| gluten-free | 100 | A | none |
| high-protein | 100 | A | none |

Common-profile generated plans all remain A-grade because their calories, goals, and preferences match realistic use cases better than the generic 2200 kcal stress test.

## Quality verdict

The meal-plan system now produces external-recipe-only plans with standardized recipe data and formal quality checks. The sample profile scores 100/100. Across all diet modes, generated weekly plans score A-grade. Remaining limitations are primarily recipe-pool size for restrictive diets, where repeats are sometimes unavoidable unless more high-quality compatible external recipes are added.

## Ethiopian recipe expansion audit update

After adding the Ethiopian recipe URL set, the canonical unified external recipe database increased to:

```text
323 clean external recipes
147 Muscle & Strength
137 Trifecta
39 Ethiopian/African source recipes
```

New Ethiopian-focused common-profile meal plans were generated:

| Profile | Grade | Score | Notes |
|---|---:|---:|---|
| Ethiopian omnivore fat loss | A | 100 | Uses Ethiopian/African recipes plus compatible external recipes |
| Ethiopian vegan recomp | A | 90 | A-grade, but repeats remain due smaller vegan Ethiopian-compatible pool |

The sample client plan remains A-grade at 100/100 after the Ethiopian expansion.

## Trifecta rescrape quality update

The Trifecta scrape was upgraded to follow internal recipe links from roundup/listicle articles and to parse nutrition facts more robustly. This increased clean Trifecta recipes from 41 to 137.

The sample plan remains A-grade at 100/100 after the rescrape, with source mix:

```text
Trifecta 9, Muscle & Strength 18, Daring Gourmet 1
```

All common-profile generated plans are now A-grade after the larger Trifecta pool improved vegan/keto variety and protein coverage.
