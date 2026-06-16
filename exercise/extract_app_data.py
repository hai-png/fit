#!/usr/bin/env python3
"""
Extract all valuable data for the fitness app from the 258 curated workouts.

Categorizes every workout into exactly one of:
  - focused           : single-muscle-group workouts (chest day, glute builder, ...)
  - program           : complete plans with an explicit fixed duration ("8 Week ...")
  - full_workout      : ongoing repeatable routines (PHUL, dumbbell split, ...)

Extracts per workout:
  identity (slug, title, url), summary, 6-dim classification, raw metadata,
  program duration, time per workout, author, video, PDF link,
  recommended supplements, and the full training schedule
  (day/section labels + exercise tables: exercise, sets, reps, rest, links).

Outputs to app_data/.
"""
import re, csv, json
from html import unescape
from pathlib import Path
from collections import Counter, OrderedDict

ROOT = Path(__file__).resolve().parent
RAW  = ROOT / "raw pages"
OUT  = ROOT / "app_data"
OUT.mkdir(exist_ok=True)

rows = list(csv.DictReader(open(ROOT/'organized_workouts/workouts_classified.csv')))

TAG = re.compile(r'<[^>]+>')
def text(s):
    return unescape(TAG.sub('', s)).replace('\xa0',' ').strip()

def clean_title(t):
    return re.sub(r'\s*\|\s*Muscle & Strength\s*$', '', unescape(t)).strip()

DUR_RE = re.compile(r'\b(\d+)[\s-]*(week|day)s?\b', re.I)

def parse_duration_weeks(h):
    m = re.search(r'Program Duration</span>([^<]*)', h)
    if not m: return None
    mm = re.search(r'(\d+)', m.group(1))
    return int(mm.group(1)) if mm else None

def title_fixed_duration(title, desc):
    """Explicit fixed length stated in title (preferred) or description."""
    for src in (title, desc or ''):
        m = re.search(r'\b(\d+)[\s-]*[Ww]eeks?\b', src)
        if m: return int(m.group(1))
        m = re.search(r'\b(\d+)[\s-]*[Dd]ays?\s+(?:to|of)\b', src)  # "30 Days to..."
        if m: return max(1, round(int(m.group(1))/7))
        m = re.search(r'\b(\d+)[\s-]*[Dd]ay\s+(shredding|workout cycle|cycle)\b', src, re.I)
        if m: return max(1, round(int(m.group(1))/7))
    return None

def get_field(h, label):
    m = re.search(label + r'</span>(.*?)</li>', h, re.S)
    if not m: return ''
    return text(m.group(1))

def get_supps(h):
    m = re.search(r'Recommended Supps</span>(.*?)</li>', h, re.S)
    if not m: return []
    return [text(x) for x in re.findall(r'<span class="supplement">(.*?)</span>', m.group(1), re.S)]

def get_author(h):
    m = re.search(r'"author":\s*{\s*"@type":\s*"Person",\s*"name":\s*"([^"]*)"(?:,\s*"sameAs":\s*"([^"]*)")?', h)
    if not m: return None, None
    url = (m.group(2) or '').replace('\\/','/') or None
    return unescape(m.group(1)), url

def get_pdf(h):
    m = re.search(r'Workout PDF</span>\s*<a[^>]*href="([^"]+)"', h, re.S)
    return m.group(1) if m else None

def get_video(h):
    m = re.search(r'<iframe[^>]*src="(https://(?:player\.vimeo\.com|www\.youtube\.com)[^"]+)"', h)
    return m.group(1) if m else None

def parse_table(tbl_html):
    """Return (headers, rows) where each row = list of {text, link} cells."""
    trs = re.findall(r'<tr[^>]*>(.*?)</tr>', tbl_html, re.S)
    headers, data = [], []
    for tr in trs:
        ths = re.findall(r'<th[^>]*>(.*?)</th>', tr, re.S)
        if ths and not headers:
            headers = [text(x) for x in ths]
            continue
        tds = re.findall(r'<td[^>]*>(.*?)</td>', tr, re.S)
        if not tds: continue
        cells = []
        for td in tds:
            link = re.search(r'href="([^"]+)"', td)
            href = link.group(1) if link else None
            if href and href.startswith('/'):
                href = 'https://www.muscleandstrength.com' + href
            cells.append({'text': text(td), 'link': href})
        if not headers and not data and len(cells) >= 2 and \
           cells[0]['text'].lower() in ('exercise','exercises'):
            headers = [c['text'] for c in cells]
            continue
        data.append(cells)
    return headers, data

HEADER_ROW = re.compile(r'^(exercise|exercises)$', re.I)
JUNK_ROW = re.compile(
    r'^(notes?|rest|cardio|superset:?|super-?set:?|tri-?set:?|giant set:?|circuit:?|'
    r'day\s*\d+|week\s*\d+|workout\s*[#a-z0-9]*|bar|exercise|sets?|reps?|'
    r'\d+|\d+%\s*of\s*1 ?rm|\*.*|monday|tuesday|wednesday|thursday|friday|saturday|sunday)$', re.I)

def rows_to_exercises(headers, data):
    """Map table rows onto normalized exercise dicts using the header row."""
    hl = [h.lower() for h in headers]
    def col(*names):
        for n in names:
            for i, h in enumerate(hl):
                if n in h: return i
        return None
    i_sets = col('sets x reps','set')
    i_reps = col('rep')
    i_rest = col('rest')
    i_tempo = col('tempo')
    i_time = col('time','duration')
    exercises = []
    group = None  # current superset/circuit grouping label
    for cells in data:
        name_cell = cells[0]
        nm = name_cell['text']
        if not nm: continue
        # header row that slipped through as <td>
        if HEADER_ROW.match(nm): continue
        is_linked = bool(name_cell['link'] and '/exercises/' in (name_cell['link'] or ''))
        rest_text = ' '.join(c['text'] for c in cells[1:]).strip()
        # label / spacer / note rows
        if not is_linked and JUNK_ROW.match(nm):
            low = nm.lower()
            if 'set' in low or 'circuit' in low:
                group = nm.rstrip(':')
            continue
        # rows with a name but no data anywhere and no link, looking like labels
        if not is_linked and not rest_text and len(cells) == 1 and len(nm) < 30:
            group = None
            continue
        ex = {'exercise': nm}
        if is_linked:
            ex['exercise_url'] = name_cell['link']
        if group:
            ex['group'] = group
        def grab(idx, key):
            if idx is not None and idx < len(cells) and cells[idx]['text']:
                ex[key] = cells[idx]['text']
        if i_sets is not None and 'sets x reps' in hl[i_sets]:
            grab(i_sets, 'sets_x_reps')
        else:
            grab(i_sets, 'sets'); grab(i_reps, 'reps')
        grab(i_rest, 'rest'); grab(i_tempo, 'tempo'); grab(i_time, 'time')
        # tables with no headers: best-effort positional sets/reps
        if not headers and len(cells) >= 3:
            ex.setdefault('sets', cells[1]['text'])
            ex.setdefault('reps', cells[2]['text'])
        exercises.append(ex)
    return exercises

BAD_HEADINGS = re.compile(r'(plain text|free workouts|join over|comments|about the author|related)', re.I)

def parse_schedule(h):
    """Body region: headings + tables in document order -> sections."""
    start = h.find('field-name-body')
    if start == -1: start = h.find('node-stats-block')
    end = h.find('id="comments"', start)
    body = h[start:end if end != -1 else None]
    events = []
    for m in re.finditer(r'<h([2-5])[^>]*>(.*?)</h\1>|(<table[^>]*>.*?</table>)', body, re.S):
        if m.group(3):
            events.append(('table', m.group(3)))
        else:
            t = text(m.group(2))
            if t and not BAD_HEADINGS.search(t):
                events.append(('heading', t))
    sections, current = [], None
    pending_heading = None
    for kind, payload in events:
        if kind == 'heading':
            pending_heading = payload
        else:
            headers, data = parse_table(payload)
            # day-of-week style tables: header IS the day label
            label = pending_heading
            if headers and len(headers) == 1:
                label = headers[0]; headers = []
            # instruction tables ("Day | Notes"): keep as notes, not exercises
            if headers and len(headers) == 2 and headers[1].lower().startswith('note'):
                notes = [{'label': c[0]['text'], 'note': c[1]['text']}
                         for c in data if len(c) >= 2 and c[1]['text']]
                if notes:
                    sections.append({'label': label or f'Workout {len(sections)+1}',
                                     'notes': notes, 'exercises': []})
                    pending_heading = None
                continue
            exercises = rows_to_exercises(headers, data)
            if not exercises: continue
            sections.append({'label': label or f'Workout {len(sections)+1}',
                             'exercises': exercises})
            pending_heading = None
    if sections:
        return sections
    # fallback for list-format workouts (no tables): heading + <ul>/<ol> lists
    REPS_HINT = re.compile(r'(\d+\s*(reps?|rounds?|minutes?|mins?|seconds?|secs?|x\s*\d)|^\d+\s)', re.I)
    pending_heading = None
    for m in re.finditer(r'<h([2-5])[^>]*>(.*?)</h\1>|(<(?:ul|ol)[^>]*>.*?</(?:ul|ol)>)', body, re.S):
        if not m.group(3):
            t = text(m.group(2))
            if t and not BAD_HEADINGS.search(t):
                pending_heading = t
            continue
        lis = [text(x) for x in re.findall(r'<li[^>]*>(.*?)</li>', m.group(3), re.S)]
        lis = [x for x in lis if x]
        if not lis or not any(REPS_HINT.search(x) for x in lis):
            continue
        sections.append({'label': pending_heading or f'Workout {len(sections)+1}',
                         'exercises': [{'exercise': x} for x in lis]})
        pending_heading = None
    return sections

MUSCLE_PATTERNS = [
    ('abs/core',  r'\b(abs?|core|six pack|8 pack|midsection|v[- ]?cuts?)\b'),
    ('chest',     r'\b(chest|pec|pecs|bench press)\b'),
    ('back',      r'\b(back|lats?|wingspan|v[- ]?taper|pull[- ]?up|chin[- ]?up|deadlift)\b'),
    ('shoulders', r'\b(shoulder|delt|deltoid|traps?|trapezius)\b'),
    ('arms',      r'\b(arms?|biceps?|triceps?|guns|forearms?)\b'),
    ('legs',      r'\b(legs?|quads?|hamstrings?|squat|wheels|calf|calves)\b'),
    ('glutes',    r'\b(glutes?|butt|booty)\b'),
]
def muscle_focus(title, summary):
    s = (title + ' ' + (summary or '')).lower()
    hits = [m for m, p in MUSCLE_PATTERNS if re.search(p, s)]
    return hits

# ── build records ─────────────────────────────────────────────────────
records = []
exercise_lib = Counter()
exercise_links = {}
for r in rows:
    h = (RAW / r['filename']).read_text(errors='ignore')
    title = clean_title(r['title'])
    desc_m = re.search(r'<meta name="description" content="([^"]*)"', h)
    desc = unescape(desc_m.group(1)) if desc_m else ''
    slug = r['url'].rstrip('/').split('/')[-1].replace('.html','')
    author, author_url = get_author(h)
    dur_meta = parse_duration_weeks(h)
    dur_title = title_fixed_duration(title, desc)

    # ── category ──
    # source-data corrections: pages tagged "single muscle group" that are
    # actually complete multi-day, all-muscle plans
    NOT_FOCUSED = {'sculpted-strength-bodybuilding-program'}
    if r['workout_type'] == 'single muscle group' and slug not in NOT_FOCUSED:
        category = 'focused'
    elif dur_title:
        category = 'program'
    else:
        category = 'full_workout'

    schedule = parse_schedule(h)
    n_ex = sum(len(s['exercises']) for s in schedule)
    for s in schedule:
        for ex in s['exercises']:
            exercise_lib[ex['exercise']] += 1
            if ex.get('exercise_url'):
                exercise_links[ex['exercise']] = ex['exercise_url']

    records.append(OrderedDict(
        id=slug,
        title=title,
        category=category,
        full_workout=category == 'full_workout',
        program=category == 'program',
        focused_workout=category == 'focused',
        url=r['url'],
        summary=desc,
        equipment=r['equipment'],
        fitness_goal=r['fitness_goal'],
        workout_type=r['workout_type'],
        gender=r['gender'],
        training_level=r['training_level'],
        days_per_week=int(r['days_per_week']),
        program_duration_weeks=dur_title or (dur_meta if dur_meta else None),
        is_fixed_duration=category == 'program' or (category == 'focused' and bool(dur_title)),
        time_per_workout=get_field(h, 'Time Per Workout') or None,
        equipment_detail=[e.strip() for e in r['equipment_raw'].split(',') if e.strip()],
        author=author,
        author_url=author_url,
        video_url=get_video(h),
        pdf_url=get_pdf(h),
        recommended_supplements=get_supps(h),
        muscle_focus=muscle_focus(title, desc) if category == 'focused' else [],
        num_sections=len(schedule),
        num_exercises=n_ex,
        schedule=schedule,
        source_file=r['filename'],
    ))

# ── outputs ───────────────────────────────────────────────────────────
json.dump(records, open(OUT/'workouts.json','w'), indent=2, ensure_ascii=False)

by_cat = {'full_workout': [], 'program': [], 'focused': []}
for rec in records: by_cat[rec['category']].append(rec)
json.dump(by_cat['full_workout'], open(OUT/'full_workouts.json','w'), indent=2, ensure_ascii=False)
json.dump(by_cat['program'],      open(OUT/'programs.json','w'),      indent=2, ensure_ascii=False)
json.dump(by_cat['focused'],      open(OUT/'focused_workouts.json','w'), indent=2, ensure_ascii=False)

# flat index CSV
idx_cols = ['id','title','category','equipment','fitness_goal','workout_type','gender',
            'training_level','days_per_week','program_duration_weeks','time_per_workout',
            'author','num_sections','num_exercises','has_video','has_pdf','url']
with open(OUT/'workouts_index.csv','w',newline='',encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(idx_cols)
    for rec in records:
        w.writerow([rec['id'],rec['title'],rec['category'],rec['equipment'],rec['fitness_goal'],
                    rec['workout_type'],rec['gender'],rec['training_level'],rec['days_per_week'],
                    rec['program_duration_weeks'] or '', rec['time_per_workout'] or '',
                    rec['author'] or '', rec['num_sections'], rec['num_exercises'],
                    bool(rec['video_url']), bool(rec['pdf_url']), rec['url']])

# exercise library — canonicalized by M&S exercise-page slug where available
canon = {}
for name, cnt in exercise_lib.items():
    url = exercise_links.get(name)
    key = url.rstrip('/').split('/')[-1].replace('.html','') if url else name.lower()
    c = canon.setdefault(key, {'slug': key if url else '', 'names': Counter(), 'count': 0, 'url': url or ''})
    c['names'][name] += cnt
    c['count'] += cnt
    if url: c['url'] = url; c['slug'] = key
with open(OUT/'exercise_library.csv','w',newline='',encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['canonical_name','slug','used_in_n_workout_slots','aliases','exercise_url'])
    for key, c in sorted(canon.items(), key=lambda kv: -kv[1]['count']):
        primary = c['names'].most_common(1)[0][0]
        aliases = '; '.join(n for n, _ in c['names'].most_common() if n != primary)
        w.writerow([primary, c['slug'], c['count'], aliases, c['url']])

# stats
stats = {
    'total_workouts': len(records),
    'by_category': {k: len(v) for k,v in by_cat.items()},
    'with_schedule': sum(1 for r in records if r['num_sections']),
    'without_schedule': [r['id'] for r in records if not r['num_sections']],
    'total_exercise_slots': sum(r['num_exercises'] for r in records),
    'unique_exercise_names': len(exercise_lib),
    'canonical_exercises': len(canon),
    'linked_to_exercise_pages': sum(1 for c in canon.values() if c['url']),
    'with_video': sum(1 for r in records if r['video_url']),
    'with_pdf': sum(1 for r in records if r['pdf_url']),
    'with_author': sum(1 for r in records if r['author']),
    'with_time_per_workout': sum(1 for r in records if r['time_per_workout']),
}
json.dump(stats, open(OUT/'stats.json','w'), indent=2)
print(json.dumps(stats, indent=2))
