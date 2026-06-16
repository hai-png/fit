#!/usr/bin/env python3
"""
Complete workout matrix pipeline.

Step 1: Parse all 606 HTML → extract + classify into 6 dimensions
Step 2: Apply manual content filter (keep_out_filenames.json)
Step 3: Multi-combo review — remove only duplicates/fragments, keep everything else
Step 4: Output all artifacts
"""

import os, re, csv, json
from collections import defaultdict
from html import unescape
from pathlib import Path

REPO_ROOT  = Path(__file__).resolve().parent
REPO_DIR   = REPO_ROOT / "raw pages"
OUTPUT_DIR = REPO_ROOT / "organized_workouts"
KEEP_OUT   = REPO_ROOT / "keep_out_filenames.json"
STRICT     = REPO_ROOT / "strict_multicombo_removals.json"

EQUIP_VALS = ["fully equipped gym", "body weight", "home / small gym"]
GOAL_VALS  = ["fat loss", "muscle building", "general fitness", "strength"]
TYPE_VALS  = ["full body", "split", "single muscle group"]
GEND_VALS  = ["men", "women", "both"]
LVL_VALS   = ["beginner", "intermediate", "advanced"]
DAY_VALS   = ["1","2","3","4","5","6","7"]
TOTAL_COMBOS = 3*4*3*3*3*7  # 2268

# ─── HTML extractors ─────────────────────────────────────────────────

def _field(html, label):
    pat = rf'<span class="row-label">{re.escape(label)}</span><div[^>]*><div[^>]*><div[^>]*>([^<]+)</div>'
    m = re.search(pat, html)
    if m: return unescape(m.group(1)).strip()
    pat2 = rf'<span class="row-label">{re.escape(label)}</span>\s*\n?\s*(.*?)\s*</li>'
    m = re.search(pat2, html, re.DOTALL)
    if m:
        return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', unescape(m.group(1)))).strip()
    return ""

def _title(html):
    m = re.search(r'<title>([^<]+)</title>', html)
    return unescape(m.group(1)).strip() if m else ""

def _url(html):
    m = re.search(r'<link rel="canonical" href="([^"]+)"', html)
    return m.group(1).strip() if m else ""

def _desc(html):
    m = re.search(r'<meta\s+(?:property="og:description"|name="description")\s+content="([^"]*)"', html)
    return unescape(m.group(1)).strip() if m else ""

# ─── Classifiers ──────────────────────────────────────────────────────

GYM_ONLY = {"machines","machine","cable","cables","smith","leg press",
    "hack squat","leg extension","leg curl","lat pulldown","cable crossover",
    "crossover","pulley"}

def classify_equipment(raw):
    if not raw: return "unknown"
    items = [x.strip() for x in re.sub(r'\s+',' ',raw.lower()).split(",") if x.strip()]
    if not items: return "unknown"
    if any(any(g in i for g in GYM_ONLY) for i in items): return "fully equipped gym"
    bw = {"bodyweight","body weight","none","no equipment"}
    if len(items)==1 and any(b in items[0] for b in bw): return "body weight"
    if all(any(b in i for b in bw) for i in items): return "body weight"
    home_ok = {"dumbbell","dumbbells","barbell","barbells","kettle bell","kettlebell",
        "kettlebells","kettle bells","band","bands","resistance band","resistance bands",
        "bench","flat bench","adjustable bench","pull-up bar","pull up bar","chin-up bar",
        "pullup bar","bodyweight","body weight","ez bar","medicine ball","dumbbells only",
        "barbell only","jump rope","foam roller","stability ball","swiss ball","exercise ball",
        "suspension trainer","trx","sandbag","abo mat","other","yoga mat","ab roller","ab wheel"}
    if all(any(h in i for h in home_ok) for i in items if i): return "home / small gym"
    return "unknown"

def classify_goal(raw):
    if not raw: return "unknown"
    g = raw.lower()
    if "lose fat" in g: return "fat loss"
    if "build muscle" in g: return "muscle building"
    if any(k in g for k in ["strength","powerlifting","powerbuilding","increase strength"]): return "strength"
    return "general fitness"

def classify_type(raw):
    if not raw: return "unknown"
    w = raw.lower()
    if "single muscle group" in w: return "single muscle group"
    if "full body" in w: return "full body"
    if any(s in w for s in ["split","upper/lower","push/pull/legs","body part split","general split","cardio"]): return "split"
    return "unknown"

def classify_gender(raw):
    if not raw: return "unknown"
    g = raw.lower().strip()
    if g in ("male","men"): return "men"
    if g in ("female","women"): return "women"
    if "male" in g and "female" in g: return "both"
    return "unknown"

def classify_level(raw):
    if not raw: return "unknown"
    l = raw.lower()
    if "beginner" in l: return "beginner"
    if "intermediate" in l: return "intermediate"
    if "advanced" in l: return "advanced"
    if "all level" in l: return "beginner"
    return "unknown"

def classify_days(raw):
    if not raw: return "unknown"
    d = raw.strip()
    return d if d in DAY_VALS else "unknown"

# ─── Multi-combo duplicate/fragment removals ──────────────────────────

MULTI_COMBO_REMOVALS = {
    # ── Duplicate series: keep earliest/representative phase only ──
    "workouts__cut-like-cutler-cycle-2__e27529515f.html":
        "Duplicate series: Cut Like Cutler Cycle 2 (keep Cycle 1)",
    "workouts__cut-like-cutler-cycle-3__d135e08c63.html":
        "Duplicate series: Cut Like Cutler Cycle 3 (keep Cycle 1)",
    "workouts__cut-like-cutler-cycle-4__da2d5e636e.html":
        "Duplicate series: Cut Like Cutler Cycle 4 (keep Cycle 1)",
    "workouts__cut-like-cutler-cycle-5__68bbe98934.html":
        "Duplicate series: Cut Like Cutler Cycle 5 (keep Cycle 1)",
    "workouts__cut-like-cutler-cycle-6__4776025dfd.html":
        "Duplicate series: Cut Like Cutler Cycle 6 (keep Cycle 1)",
    "workouts__conjugate-system-beginner-powerlifting-workout-phase-2__4622f1d03c.html":
        "Duplicate series: Conjugate Phase 2 (keep Phase 1)",
    "workouts__conjugate-system-beginner-powerlifting-workout-phase-3__2d67fcf336.html":
        "Duplicate series: Conjugate Phase 3 (keep Phase 1)",
    "workouts__start-from-scratch-phase-3__96b22967b1.html":
        "Duplicate series: Start from Scratch Phase 3 (keep Phase 2)",

    # ── Fragments: single-day sheets, not standalone programs ──
    "workouts__mpp-day-1__7b1a901117.html":
        "Fragment: single day of Mass Performance Program (not standalone)",
    "workouts__mpp-day-2__52acc89a59.html":
        "Fragment: single day of Mass Performance Program (not standalone)",
    "workouts__mpp-day-4__f5c68451ef.html":
        "Fragment: single day of Mass Performance Program (not standalone)",
    "workouts__mpp-day-5__22f78cf143.html":
        "Fragment: single day of Mass Performance Program (not standalone)",

    # ── Chain-specific: designed for one gym chain's equipment, not general ──
    "workouts__push-pull-sample-planet-fitness-workout__5bc08b01ea.html":
        "Chain-specific: Planet Fitness equipment/limitations, not general gym",

    # ── Competition-specific: not suitable for general population ──
    "workouts__first-show-contest-prep-workout__15e70bcec8.html":
        "Competition-specific: bodybuilding contest prep for first show, not general fat loss",
}

# ─── Main pipeline ────────────────────────────────────────────────────

def run():
    print("STEP 1 — Parsing HTML files")
    html_files = sorted(p for p in REPO_DIR.glob("*.html") if "(copy)" not in p.name)
    print(f"  Found {len(html_files)} files")

    all_rows = []
    for fp in html_files:
        html = fp.read_text(encoding="utf-8", errors="replace")
        raw = {
            "title": _title(html), "url": _url(html), "description": _desc(html),
            "main_goal_raw": _field(html,"Main Goal"),
            "workout_type_raw": _field(html,"Workout Type"),
            "training_level_raw": _field(html,"Training Level"),
            "days_per_week_raw": _field(html,"Days Per Week"),
            "equipment_raw": _field(html,"Equipment Required"),
            "target_gender_raw": _field(html,"Target Gender"),
        }
        dims = {
            "equipment": classify_equipment(raw["equipment_raw"]),
            "fitness_goal": classify_goal(raw["main_goal_raw"]),
            "workout_type": classify_type(raw["workout_type_raw"]),
            "gender": classify_gender(raw["target_gender_raw"]),
            "training_level": classify_level(raw["training_level_raw"]),
            "days_per_week": classify_days(raw["days_per_week_raw"]),
        }
        all_rows.append({"filename": fp.name, **raw, **dims})

    # ── Separate audit from classifiable ──
    audit_rows = []
    classifiable = []
    for row in all_rows:
        fields_missing = (not row["main_goal_raw"] and not row["workout_type_raw"]
                          and not row["training_level_raw"] and not row["days_per_week_raw"])
        has_unknown = any(v == "unknown" for v in [row["equipment"],row["fitness_goal"],
                          row["workout_type"],row["gender"],row["training_level"],row["days_per_week"]])
        if fields_missing:
            row["audit_reason"] = "all classification fields missing (index/listing page)"
            audit_rows.append(row)
        elif has_unknown:
            unknowns = "; ".join(f"{k}: {v}" for k,v in [
                ("equipment",row["equipment"]),("fitness_goal",row["fitness_goal"]),
                ("workout_type",row["workout_type"]),("gender",row["gender"]),
                ("training_level",row["training_level"]),("days_per_week",row["days_per_week"])
            ] if v == "unknown")
            row["audit_reason"] = unknowns
            audit_rows.append(row)
        else:
            classifiable.append(row)

    print(f"  Classifiable: {len(classifiable)}")
    print(f"  Audit:        {len(audit_rows)}")

    # ── Step 2: Manual content filter ──
    print("\nSTEP 2 — Manual content filter")
    keep_out = json.loads(KEEP_OUT.read_text()) if KEEP_OUT.exists() else {}
    content_filtered = []
    prefilter = []
    for row in classifiable:
        if row["filename"] in keep_out:
            row["filter_reason"] = keep_out[row["filename"]]
            content_filtered.append(row)
        else:
            prefilter.append(row)
    print(f"  Kept out:   {len(content_filtered)}")
    print(f"  Remaining:  {len(prefilter)}")

    # ── Step 3: Multi-combo duplicate/fragment removal ──
    print("\nSTEP 3 — Multi-combo review (remove only duplicates & fragments)")
    dup_filtered = []
    final = []
    for row in prefilter:
        if row["filename"] in MULTI_COMBO_REMOVALS:
            row["filter_reason"] = MULTI_COMBO_REMOVALS[row["filename"]]
            dup_filtered.append(row)
        else:
            final.append(row)
    print(f"  Removed (duplicates/fragments): {len(dup_filtered)}")
    print(f"  Kept:                           {len(final)}")
    for r in dup_filtered:
        print(f"    ❌ {r['title'][:65]} → {r['filter_reason']}")

    # ── Step 3.5: Strict multi-combo curation ──
    # Keep only distinctly different options per combo (different muscle group,
    # equipment subtype, demographic, or split structure). Remove near-duplicates,
    # gimmicks, niche variants, fragments, and overwhelming look-alike choices.
    print("\nSTEP 3.5 — Strict multi-combo curation (app UX: few, distinct choices)")
    strict_removals = json.loads(STRICT.read_text()) if STRICT.exists() else {}
    strict_filtered = []
    kept_final = []
    for row in final:
        if row["filename"] in strict_removals:
            row["filter_reason"] = strict_removals[row["filename"]]
            strict_filtered.append(row)
        else:
            kept_final.append(row)
    final = kept_final
    print(f"  Removed (strict curation): {len(strict_filtered)}")
    print(f"  Kept:                      {len(final)}")

    # Build combo matrix
    matrix = defaultdict(list)
    for r in final:
        key = "|".join([r["equipment"],r["fitness_goal"],r["workout_type"],
                        r["gender"],r["training_level"],r["days_per_week"]])
        matrix[key].append(r)

    multi = {k:v for k,v in matrix.items() if len(v) > 1}
    print(f"\n  Final combos: {len(matrix)} nonzero ({len(multi)} with >1 workout)")

    # ── Step 4: Write outputs ──
    print("\nSTEP 4 — Writing outputs")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 4a. Master classified CSV
    cols = ["filename","title","url","equipment","fitness_goal","workout_type",
            "gender","training_level","days_per_week",
            "main_goal_raw","workout_type_raw","training_level_raw",
            "days_per_week_raw","equipment_raw","target_gender_raw"]
    with open(OUTPUT_DIR/"workouts_classified.csv","w",newline="",encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(cols)
        for r in final: w.writerow([r.get(c,"") for c in cols])
    print(f"  ✓ workouts_classified.csv ({len(final)} workouts)")

    # 4b. Content filtered (manual)
    fcols = ["filename","title","url","filter_reason",
             "equipment","fitness_goal","workout_type","gender","training_level","days_per_week"]
    with open(OUTPUT_DIR/"content_filtered.csv","w",newline="",encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(fcols)
        for r in content_filtered: w.writerow([r.get(c,"") for c in fcols])
    print(f"  ✓ content_filtered.csv ({len(content_filtered)} workouts)")

    # 4c. Duplicate/fragment removals
    with open(OUTPUT_DIR/"duplicate_filtered.csv","w",newline="",encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(fcols)
        for r in dup_filtered: w.writerow([r.get(c,"") for c in fcols])
    print(f"  ✓ duplicate_filtered.csv ({len(dup_filtered)} workouts)")

    # 4c-2. Strict multi-combo curation removals
    with open(OUTPUT_DIR/"strict_filtered.csv","w",newline="",encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(fcols)
        for r in strict_filtered: w.writerow([r.get(c,"") for c in fcols])
    print(f"  ✓ strict_filtered.csv ({len(strict_filtered)} workouts)")

    # 4d. Parse audit
    acols = ["filename","title","url","audit_reason",
             "main_goal_raw","workout_type_raw","training_level_raw",
             "days_per_week_raw","equipment_raw","target_gender_raw"]
    with open(OUTPUT_DIR/"parse_audit.csv","w",newline="",encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(acols)
        for r in audit_rows: w.writerow([r.get(c,"") for c in acols])
    print(f"  ✓ parse_audit.csv ({len(audit_rows)} entries)")

    # 4e. Matrix coverage
    coverage = {}
    nz = 0
    for eq in EQUIP_VALS:
        for goal in GOAL_VALS:
            for wt in TYPE_VALS:
                for g in GEND_VALS:
                    for lvl in LVL_VALS:
                        for d in DAY_VALS:
                            key = f"{eq}|{goal}|{wt}|{g}|{lvl}|{d}"
                            c = len(matrix.get(key, []))
                            coverage[key] = c
                            if c > 0: nz += 1
    with open(OUTPUT_DIR/"matrix_coverage.json","w") as f:
        json.dump(coverage, f, indent=2)
    print(f"  ✓ matrix_coverage.json ({nz}/{TOTAL_COMBOS} nonzero)")

    # 4f. by_dimension
    dim_dir = OUTPUT_DIR/"by_dimension"; dim_dir.mkdir(exist_ok=True)
    dim_specs = [("equipment","equipment",EQUIP_VALS),("goal","fitness_goal",GOAL_VALS),
                 ("workout_type","workout_type",TYPE_VALS),("gender","gender",GEND_VALS),
                 ("level","training_level",LVL_VALS),("days","days_per_week",DAY_VALS)]
    for dn, field, vals in dim_specs:
        for val in vals:
            rows = [r for r in final if r[field] == val]
            safe = val.replace(" ","_").replace("/","_or_")
            with open(dim_dir/f"{dn}__{safe}.csv","w",newline="",encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["filename","title","url","equipment","fitness_goal","workout_type","gender","training_level","days_per_week"])
                for r in rows: w.writerow([r[k] for k in ["filename","title","url","equipment","fitness_goal","workout_type","gender","training_level","days_per_week"]])
    print(f"  ✓ by_dimension/ ({len(list(dim_dir.glob('*.csv')))} files)")

    # 4g. by_combination
    combo_dir = OUTPUT_DIR/"by_combination"; combo_dir.mkdir(exist_ok=True)
    for old in combo_dir.glob("*.csv"): old.unlink()
    for key, count in coverage.items():
        if count == 0: continue
        parts = key.split("|")
        rows = matrix.get(key, [])
        safe = [p.replace(" ","_").replace("/","_or_") for p in parts]
        fname = f"{safe[0]}__{safe[1]}__{safe[2]}__{safe[3]}__{safe[4]}__{parts[5]}d.csv"
        with open(combo_dir/fname,"w",newline="",encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["# equipment",parts[0],"# fitness_goal",parts[1],"# workout_type",parts[2],
                         "# gender",parts[3],"# training_level",parts[4],"# days_per_week",parts[5]])
            w.writerow(["filename","title","url"])
            for r in rows: w.writerow([r["filename"],r["title"],r["url"]])
    print(f"  ✓ by_combination/ ({len(list(combo_dir.glob('*.csv')))} files)")

    # 4h. Summary
    summary = {
        "total_files": len(all_rows),
        "parse_audit": len(audit_rows),
        "content_filtered": len(content_filtered),
        "duplicate_filtered": len(dup_filtered),
        "strict_filtered": len(strict_filtered),
        "final_classified": len(final),
        "nonzero_combinations": nz,
        "total_combinations": TOTAL_COMBOS,
        "coverage_pct": round(nz/TOTAL_COMBOS*100, 2),
        "multi_workout_combos": len(multi),
        "dimension_counts": {
            "equipment":     {eq: sum(1 for r in final if r["equipment"]==eq) for eq in EQUIP_VALS},
            "fitness_goal":  {g:  sum(1 for r in final if r["fitness_goal"]==g) for g in GOAL_VALS},
            "workout_type":  {wt: sum(1 for r in final if r["workout_type"]==wt) for wt in TYPE_VALS},
            "gender":        {g:  sum(1 for r in final if r["gender"]==g) for g in GEND_VALS},
            "training_level":{l:  sum(1 for r in final if r["training_level"]==l) for l in LVL_VALS},
            "days_per_week": {d:  sum(1 for r in final if r["days_per_week"]==d) for d in DAY_VALS},
        },
    }
    with open(OUTPUT_DIR/"summary.json","w") as f:
        json.dump(summary, f, indent=2)
    print(f"  ✓ summary.json")

    # ── Report ──
    print("\n" + "="*70)
    print("FINAL REPORT")
    print("="*70)
    print(f"  Total HTML:                  {summary['total_files']}")
    print(f"  Parse audit:                 {summary['parse_audit']}")
    print(f"  Content filtered (manual):   {summary['content_filtered']}")
    print(f"  Duplicate/fragment removed:  {summary['duplicate_filtered']}")
    print(f"  Strict curation removed:     {summary['strict_filtered']}")
    print(f"  FINAL CLASSIFIED:            {summary['final_classified']}")
    print(f"  Nonzero combos:              {nz}/{TOTAL_COMBOS} ({summary['coverage_pct']}%)")
    print(f"  Multi-workout combos:        {len(multi)}")
    print()
    print("  Dimension breakdown:")
    for dim, counts in summary["dimension_counts"].items():
        print(f"    {dim}: {dict(counts)}")

    accounted = len(audit_rows) + len(content_filtered) + len(dup_filtered) + len(strict_filtered) + len(final)
    print(f"\n  Integrity: {accounted} = {summary['total_files']} → {'✅ PASS' if accounted == summary['total_files'] else '❌ FAIL'}")


if __name__ == "__main__":
    run()
