#!/usr/bin/env python3
"""
Join app_data/exercise_library.csv with FitClick's calories-burned database
(fitclick_exercises_raw.json, scraped from https://www.fitclick.com/calories_burned
at the site defaults: Body Weight 150 lbs, Exercise Duration 15 min).

FitClick's displayed number is linear in body weight and duration (verified by
querying the calculator at 75/150/300 lbs and 15/30/60 min), so any value can
be rescaled:

    calories = cal_per_hr_150lb * (body_weight_lb / 150) * (duration_min / 60)

Equivalently with METs (cal_per_hr = MET * 3.5 * kg / 200 * 60, kg at 150lb = 68.04):
    MET = cal_per_hr_150lb / 71.4

Output: app_data/exercise_calories.csv
"""
import json, csv, re, difflib
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
fc = json.load(open(ROOT/'fitclick_exercises_raw.json'))
ours = list(csv.DictReader(open(ROOT/'app_data/exercise_library.csv')))

SYN = [
 (r'\bdb\b','dumbbell'), (r'\bbb\b','barbell'),
 (r'\bmilitary press\b','overhead press'), (r'\blat pull ?down\b','lat pulldown'),
 (r'\bskull ?crusher\b','lying triceps extension'), (r'\bhover\b','plank'),
 (r'\bsldl\b','stiff leg deadlift'), (r'\brdl\b','romanian deadlift'),
 (r'^\d+[a-z]?[.):]\s*',''), (r'^[a-f][.):]\s*',''),
]
def norm_tokens(s):
    s = s.lower()
    s = re.sub(r'\(.*?\)', ' ', s)
    for a,b in SYN: s = re.sub(a,b,s)
    s = re.sub(r'[^a-z0-9 ]', ' ', s)
    out=[]
    for w in s.split():
        if w.endswith('s') and len(w)>3 and not w.endswith('ss'): w=w[:-1]
        out.append(w)
    return out
def key(s): return ' '.join(norm_tokens(s))

fc_norm = {}
for i in fc:
    k = key(i['name'])
    cur = fc_norm.get(k)
    if cur is None or (i['created_by']=='FitClick' and cur['created_by']!='FitClick'):
        fc_norm[k] = i
fc_keys = list(fc_norm)
fc_tokensets = {k: set(k.split()) for k in fc_keys}

def jaccard(a,b):
    return len(a&b)/len(a|b) if a and b else 0

def best_match(name, aliases):
    cands = [name] + [a.strip() for a in aliases.split(';') if a.strip()][:6]
    for c in cands:
        k = key(c)
        if k in fc_norm: return fc_norm[k], 'exact', 1.0
    best, bs = None, 0
    for c in cands[:3]:
        ts = set(key(c).split())
        for k, fs in fc_tokensets.items():
            j = jaccard(ts, fs)
            if j > bs: bs, best = j, k
    if best and bs >= 0.75: return fc_norm[best], 'fuzzy', bs
    k0 = key(name)
    near = difflib.get_close_matches(k0, fc_keys, n=1, cutoff=0.87)
    if near: return fc_norm[near[0]], 'fuzzy', 0.87
    if best and bs >= 0.6: return fc_norm[best], 'fuzzy_low', bs
    return None, None, 0.0

# manual overrides for high-usage exercises the auto-matcher misses
# (our canonical slug/name -> FitClick eqID)
MANUAL = {
    'Plank': 371,                         # Bridge (Plank) 221 — static hold
    'Chest Dip': 74,                      # Parallel-Bar Dips 425
    'Walking Lunges': 539,                # Walking Lunges without Weight 391
    'Arnold Press': 2762,                 # Dumbbell Arnold Shoulder Press 374
    'Seated Arnold Press': 2762,
    'Bodyweight Squat': 1841,             # Squat - (No extra weights) 442
    'High Bar Close Stance Squats': 1841, # closest: bodyweight/standard squat 442
}
fc_by_id = {i['eqID']: i for i in fc}

# category fallback: median cal/hr of FitClick-created entries per category
import statistics
cat_vals = {}
for i in fc:
    if i['created_by'] != 'FitClick' or not i['cal_per_hr_150lb']: continue
    cat_vals.setdefault(i['category'], []).append(i['cal_per_hr_150lb'])
cat_median = {c: round(statistics.median(v)) for c, v in cat_vals.items()}
strength_overall = round(statistics.median(
    [i['cal_per_hr_150lb'] for i in fc
     if i['created_by']=='FitClick' and i['cal_per_hr_150lb'] and i['category'] != 'Cardio']))

CAT_KEYWORDS = [
 ('Cardio',     r'\b(run|sprint|jog|treadmill|bike|cycling|rower|rowing machine|elliptical|jump rope|burpee|hiit|cardio|stair|sled|swim|walk|battle rope|mountain climber|jumping jack)\b'),
 ('Abdominals', r'\b(crunch|sit ?up|plank|ab |abs|oblique|russian twist|leg raise|knee raise|v ?up|hollow|dead bug|woodchop|wood chop|rollout)\b'),
 ('Thighs',     r'\b(squat|lunge|leg press|leg extension|leg curl|deadlift|hip thrust|glute|step up|good morning|hamstring|adduct|abduct|pull through|swing)\b'),
 ('Calves',     r'\b(calf|calve)\b'),
 ('Back',       r'\b(row|pull ?up|chin ?up|pulldown|pullover|lat |back extension|hyperextension|shrug|rack pull|face pull)\b'),
 ('Chest',      r'\b(bench press|chest|fly|flye|push ?up|dip|pec|crossover)\b'),
 ('Shoulders',  r'\b(shoulder|overhead press|lateral raise|front raise|rear delt|arnold|upright row|push press|delt)\b'),
 ('Biceps',     r'\b(curl)\b'),
 ('Triceps',    r'\b(tricep|skullcrusher|extension|kickback|close grip|pushdown)\b'),
 ('Forearms',   r'\b(wrist|forearm|grip|farmer)\b'),
]
def infer_category(name):
    s = ' '.join(norm_tokens(name))
    for cat, pat in CAT_KEYWORDS:
        if re.search(pat, s): return cat
    return None

out_rows = []
counts = Counter()
for o in ours:
    if o['canonical_name'] in MANUAL:
        m, how, score = fc_by_id[MANUAL[o['canonical_name']]], 'manual', 1.0
    else:
        m, how, score = best_match(o['canonical_name'], o['aliases'])
    if m and m['cal_per_hr_150lb']:
        cal_hr = m['cal_per_hr_150lb']
        src = 'fitclick_match'
        cat = m['category']; muscle = m['muscle']
        fc_name = m['name']; fc_id = m['eqID']
        fc_url = f"https://www.fitclick.com/exercises_{m['slug']}?eqID={m['eqID']}"
    else:
        cat = infer_category(o['canonical_name']) or ''
        cal_hr = cat_median.get(cat, strength_overall)
        src = 'category_estimate' if cat else 'strength_median_estimate'
        how, score, muscle, fc_name, fc_id, fc_url = '', 0.0, '', '', '', ''
    counts[src] += 1
    out_rows.append({
        'canonical_name': o['canonical_name'],
        'slug': o['slug'],
        'used_in_n_workout_slots': o['used_in_n_workout_slots'],
        'cal_per_hr_150lb': cal_hr,
        'cal_15min_150lb': round(cal_hr/4),
        'met_estimate': round(cal_hr/71.4, 2),
        'calorie_source': src,
        'match_type': how or '',
        'match_score': round(score,2) if score else '',
        'fitclick_name': fc_name,
        'fitclick_eqID': fc_id,
        'fitclick_url': fc_url,
        'fitclick_category': cat,
        'fitclick_muscle': muscle,
        'exercise_url': o['exercise_url'],
    })

cols = list(out_rows[0].keys())
with open(ROOT/'app_data/exercise_calories.csv','w',newline='',encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(out_rows)

slots_matched = sum(int(r['used_in_n_workout_slots']) for r in out_rows if r['calorie_source']=='fitclick_match')
slots_total = sum(int(r['used_in_n_workout_slots']) for r in out_rows)
print(dict(counts))
print(f"every exercise has a calorie value: {all(r['cal_per_hr_150lb'] for r in out_rows)}")
print(f"workout-slot coverage by direct FitClick match: {slots_matched}/{slots_total} = {slots_matched/slots_total:.0%}")
print("category medians (cal/hr @150lb):", cat_median, "| strength overall:", strength_overall)
