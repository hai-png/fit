# 06 — Meal Plans

## Library

51 meal items across 8 cuisines, each carrying full macro data.

**Cuisines:** american, mediterranean, asian, indian, mexican,
middle_eastern, african, nordic.

**Diet compatibility** is simplified to omnivore and vegan only:

| Diet | Acceptable tags |
|---|---|
| Omnivore | omnivore, pollo_pescatarian, pescatarian, vegetarian, vegan |
| Vegan | vegan only |

## Calorie-accurate assembly

`assemble_day()` uses a two-pass approach:

1. **Proportional allocation** — each meal slot gets a fraction of the
   daily target (e.g., breakfast 25%, lunch 30%, snack 15%, dinner 30%).
   The best-matching meal is chosen per slot.
2. **Portion scaling** — a uniform scale factor brings the day total to
   the target. Each meal records its `portion_scale`.

Result: **≤0.4% error** across all archetypes (was up to 47% in v1).

## Weekly rotation

`assemble_week()` cycles through compatible meals per slot before
repeating, cycling through the primary + secondary cuisines. Each day
is independently portion-scaled.

## Allergen filtering

Simple keyword search on ingredient text. Meals containing a listed
allergen are excluded from the pool.

## Cuisine selection

If the user specified an optional traditional cuisine, it anchors the
plan. Otherwise defaults to American + Mediterranean.
