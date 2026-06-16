# Organized Workout Matrix

## Overview

606 workout HTML files from Muscle & Strength, classified into a 6-dimensional matrix and curated down to **258 workouts** across **184 nonzero combinations**. After basic duplicate/fragment removal, every multi-workout combination went through a **strict manual review**: only options that are *distinctly different* (different muscle group, equipment subtype, demographic, or split structure) were kept, so app users see a few clear choices instead of a wall of near-identical programs.

## Dimensions (3×4×3×3×3×7 = 2,268 total combos)

| Dimension | Values |
|-----------|--------|
| Equipment | fully equipped gym, body weight, home / small gym |
| Fitness Goal | fat loss, muscle building, general fitness, strength |
| Workout Type | full body, split, single muscle group |
| Gender | men, women, both |
| Training Level | beginner, intermediate, advanced |
| Days Per Week | 1–7 |

## Pipeline (`parse_and_organize.py`)

### Step 1 — Parse & Classify
Reads all 606 HTML files, extracts metadata, classifies into 6 dimensions.
→ **574** classifiable, **32** unclassifiable (index/listing pages with missing fields)

### Step 2 — Manual Content Filter
Applies `keep_out_filenames.json` (52 entries): celebrity/novelty, military/sport-specific, gimmicks, chain-specific, non-program pages.
→ **52** removed, **522** remain

### Step 3 — Duplicate / Fragment Removal
Series duplicates (Cut Like Cutler cycles 2–6, Conjugate phases 2–3, Start from Scratch phase 3), single-day MPP fragments, Planet Fitness sample, contest-prep workout.
→ **14** removed, **508** remain

### Step 3.5 — Strict Multi-Combo Curation (NEW)
All 77 multi-workout combos manually reviewed one by one (`strict_multicombo_review.txt`).
Keep rule: an option survives only if it is **distinctly different** from the others in
its combo and is a choice a user would plausibly want:
- **Different muscle group** (single-muscle-group combos keep exactly one workout per muscle: chest, back, shoulders, arms, legs, glutes, abs…)
- **Different equipment subtype** (e.g. dumbbell-only vs barbell-only vs kettlebell at home, machine-only in the gym)
- **Different demographic** (e.g. adults 40+, parent & teen, women-specific in a "both" slot only when no women's combo exists)
- **Different program structure** (e.g. PPL vs upper/lower vs body-part split)

Removed: near-identical "8-week shred"-style duplicates, gimmicks (dice/cards, AMRAP-vs-clock, random generators), niche variants (tall guys/girls, crowded-gym, hotel-gym, seasonal/holiday themes), athlete-branded duplicates, multi-program listicles, series fragments, and misclassified entries.
→ **250** removed (`strict_filtered.csv` / `strict_multicombo_removals.json`), **258** final

### Final Count

| Category | Count |
|----------|-------|
| Total HTML files | 606 |
| Parse audit (unclassifiable) | 32 |
| Content filtered (manual) | 52 |
| Duplicates/fragments removed | 14 |
| Strict curation removed | 250 |
| **Final classified** | **258** |
| Nonzero combinations | 184 / 2,268 (8.11%) |
| Multi-workout combos remaining | 41 (all ≤6, each option distinct) |

After curation, **143 of 184 combos have exactly one workout**; the remaining 41 multi-combos only offer genuinely different choices (mostly one workout per muscle group in single-muscle-group slots, or clear equipment/demographic/structure alternatives).

## Output Files

```
organized_workouts/
├── workouts_classified.csv     # 258 curated workouts
├── content_filtered.csv        # 52 removed by manual content review
├── duplicate_filtered.csv      # 14 duplicate/fragment removals
├── strict_filtered.csv         # 250 strict multi-combo curation removals
├── parse_audit.csv             # 32 unclassifiable pages
├── matrix_coverage.json        # 2,268 keys → workout count per combo
├── summary.json                # Aggregated stats
├── by_dimension/               # 23 CSVs (one per dimension-value)
├── by_combination/             # 184 CSVs (one per nonzero combo)
└── README.md
```

## Source Files

```
exer/
├── raw pages/                       # 606 HTML source files
├── parse_and_organize.py            # Classification pipeline (single script)
├── extract_app_data.py              # App-data extraction (runs after pipeline)
├── keep_out_filenames.json          # 52 manual content-filter entries
├── manual_review.json               # 119 content-review decisions backing keep_out
├── strict_multicombo_decisions.py   # Per-combo keep/remove decisions (editable)
├── strict_multicombo_removals.json  # 250 strict curation removals (file → reason)
├── strict_multicombo_review.txt     # Full per-combo decision log (all 77 combos)
├── organized_workouts/              # Classification outputs (this folder)
└── app_data/                        # Fitness-app dataset (workouts.json etc.)
```
