"""
render_html.py
==============

Take a ClientProfile (or a JSON file) and render a beautiful, printable
HTML plan that can be saved, emailed, or printed for the client.

Usage:
    python3 examples/render_html.py examples/sample_client.json output/sara_plan.html
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from html import escape

# Only mutate sys.path if fitness_engine is not already importable (e.g.
# when running from a checkout rather than an installed package). The
# previous unconditional mutation was a side-effect on import.
try:
    import fitness_engine  # noqa: F401
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fitness_engine import ClientProfile, Recommender, __version__


# --------------------------------------------------------------------------- #
# CSS (inline so the file works fully offline / in iframes)                    #
# --------------------------------------------------------------------------- #
CSS = """
:root {
  --bg: #f7f8fa; --panel: #fff; --ink: #1f2937; --muted: #6b7280;
  --accent: #2f6fed; --accent-2: #e8f0ff; --warn: #b91c1c; --note: #0369a1;
  --good: #15803d;
}
* { box-sizing: border-box; }
body {
  margin: 0; padding: 32px; background: var(--bg); color: var(--ink);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
               Roboto, "Helvetica Neue", Arial, sans-serif;
  font-size: 14px; line-height: 1.55;
}
header { background: var(--accent); color: white; padding: 24px 32px;
  border-radius: 12px; margin-bottom: 24px; }
header h1 { margin: 0 0 6px 0; font-size: 26px; }
header .meta { font-size: 13px; opacity: 0.92; }
.signature { display: inline-block; background: rgba(255,255,255,0.18);
  padding: 4px 10px; border-radius: 6px; margin-top: 8px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 13px; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; }
.panel { background: var(--panel); border: 1px solid #e5e7eb;
  border-radius: 10px; padding: 18px 20px; margin-bottom: 16px; }
.panel h2 { margin: 0 0 12px 0; font-size: 16px; color: var(--accent); }
.panel h3 { margin: 16px 0 6px 0; font-size: 13px; color: var(--muted);
  text-transform: uppercase; letter-spacing: 0.06em; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td { text-align: left; padding: 8px 6px; border-bottom: 1px solid #f3f4f6; }
th { background: #f9fafb; color: var(--muted); font-weight: 600; }
.kpi { display: flex; align-items: baseline; gap: 8px; }
.kpi .v { font-size: 22px; font-weight: 700; color: var(--ink); }
.kpi .u { color: var(--muted); font-size: 12px; }
.bar { height: 8px; background: #eef2ff; border-radius: 6px; overflow: hidden; }
.bar > span { display: block; height: 100%; background: var(--accent); }
ul { padding-left: 18px; margin: 6px 0; }
li { margin: 3px 0; }
.warn { color: var(--warn); }
.note { color: var(--note); }
.good { color: var(--good); }
.tag { display: inline-block; background: var(--accent-2); color: var(--accent);
  padding: 1px 8px; border-radius: 4px; font-size: 12px; margin-right: 4px; }
.day { font-weight: 700; color: var(--accent); margin: 8px 0 4px 0; }
.exercise { display: grid; grid-template-columns: 1.4fr 0.8fr 0.5fr;
  font-size: 13px; padding: 4px 0; border-bottom: 1px dotted #e5e7eb; }
.exercise:last-child { border-bottom: none; }
.recipe { background: #f9fafb; padding: 6px 10px; border-left: 3px solid var(--accent);
  margin: 4px 0 8px 0; font-size: 12px; color: var(--muted); }
footer { color: var(--muted); font-size: 12px; text-align: center;
  margin-top: 24px; }
@media print { body { background: white; padding: 12px; } .panel { break-inside: avoid; } }
"""


def render(rec, client_name: str = "Client") -> str:
    bc = rec.body_composition
    e = rec.energy
    m = rec.nutrition.macros
    t = rec.training
    n = rec.nutrition
    tc = rec.trainee_category
    ai = rec.anthropometrics

    html = ['<!doctype html><html><head><meta charset="utf-8">']
    html.append(f"<title>{escape(client_name)} - Personalised Plan</title>")
    html.append(f"<style>{CSS}</style></head><body>")

    # Header
    html.append('<header>')
    html.append(f'<h1>Personalised Plan for {escape(client_name)}</h1>')
    html.append('<div class="meta">')
    html.append(
        f"Archetype signature: <span class=\"signature\">"
        f"{escape(rec.archetype_signature)}</span>"
    )
    html.append('</div></header>')

    # Trainee category banner
    html.append('<div class="panel">')
    cat_label = tc.category.value.replace("_", " ").title()
    html.append(f'<h2>Trainee Profile: {escape(cat_label)} '
                f'({escape(tc.strategy)})</h2>')
    html.append(f'<p>{escape(tc.summary)}</p>')
    if tc.pitfalls:
        html.append('<h3>Common Pitfalls to Avoid</h3><ul>')
        for pf in tc.pitfalls:
            html.append(f'<li>{escape(pf)}</li>')
        html.append('</ul>')
    if tc.recommendations:
        html.append('<h3>Key Recommendations</h3><ul>')
        for r in tc.recommendations:
            html.append(f'<li>{escape(r)}</li>')
        html.append('</ul>')
    html.append('</div>')

    # KPI row
    html.append('<div class="grid-3">')
    html.append(f'''<div class="panel">
      <h3>Body Composition</h3>
      <div class="kpi"><span class="v">{bc.bmi}</span><span class="u">BMI ({bc.bmi_category})</span></div>
      <div class="kpi"><span class="v">{bc.body_fat_pct}%</span><span class="u">body fat [{bc.estimation_method}]</span></div>
      <div class="kpi"><span class="v">{bc.lean_mass_kg}</span><span class="u">kg lean mass</span></div>
      <div class="kpi"><span class="v">{ai.waist_to_height_ratio if ai.waist_to_height_ratio is not None else '-'}</span><span class="u">waist-to-height</span></div>
      <div class="kpi"><span class="v">{ai.ideal_body_weight_kg}</span><span class="u">kg Devine IBW ref.</span></div>
    </div>''')
    html.append(f'''<div class="panel">
      <h3>Energy & Macros</h3>
      <div class="kpi"><span class="v">{e.calorie_target:.0f}</span><span class="u">kcal target</span></div>
      <div class="kpi"><span class="v">{m.protein_g:.0f}g</span><span class="u">protein ({m.protein_pct}%)</span></div>
      <div class="kpi"><span class="v">{m.carbs_g:.0f}g</span><span class="u">carbs ({m.carbs_pct}%)</span></div>
      <div class="kpi"><span class="v">{m.fat_g:.0f}g</span><span class="u">fat ({m.fat_pct}%)</span></div>
      <div class="kpi"><span class="v">{n.macro_cycle.training_day.calories:.0f}/{n.macro_cycle.rest_day.calories:.0f}</span><span class="u">training/rest kcal option</span></div>
    </div>''')
    html.append(f'''<div class="panel">
      <h3>Training</h3>
      <div class="kpi"><span class="v">{t.weekly_volume.total_sets}</span><span class="u">sets / week</span></div>
      <div class="kpi"><span class="v">{t.split.name}</span><span class="u">split</span></div>
      <div class="kpi"><span class="v">{t.cardio_prescription.get("weekly_cardio_minutes","-")}</span><span class="u">min cardio / wk</span></div>
      <div class="kpi"><span class="v">{n.hydration.total_ml:.0f}</span><span class="u">ml water / day</span></div>
    </div>''')
    html.append('</div>')

    # Warnings / notes — escape ALL strings to prevent XSS via
    # user-supplied medical_flags keys. See second-audit finding (XSS).
    if rec.warnings or rec.notes:
        html.append('<div class="panel"><h2>Health & Lifestyle Notes</h2>')
        for w in rec.warnings:
            html.append(f'<div class="warn">! {escape(str(w))}</div>')
        for note in rec.notes:
            html.append(f'<div class="note">i {escape(str(note))}</div>')
        if rec.intake_report.recommendations:
            html.append('<h3>Daily Habits</h3><ul>')
            for r in rec.intake_report.recommendations:
                html.append(f'<li>{escape(r)}</li>')
            html.append('</ul>')
        html.append('</div>')

    # Volume + intensity + progression
    html.append('<div class="panel"><h2>Training Setup</h2>')
    html.append('<h3>Volume per muscle group (sets/week)</h3>')
    html.append('<table>')
    for grp, sets_ in t.weekly_volume.per_muscle_group.items():
        html.append(f'<tr><td>{grp.title()}</td>'
                    f'<td><div class="bar"><span style="width:{min(100, sets_*8)}%"></span></div></td>'
                    f'<td style="text-align:right">{sets_}</td></tr>')
    html.append('</table>')
    if getattr(t, "volume_reconciliation", None):
        html.append('<h3>Scheduled vs Target Volume</h3>')
        html.append(f'<p>{escape(t.volume_reconciliation.get("summary", ""))}</p>')
        html.append('<table><tr><th>Muscle</th><th>Target</th><th>Scheduled</th><th>Diff</th></tr>')
        for muscle, target in t.volume_reconciliation.get("target_sets", {}).items():
            scheduled = t.volume_reconciliation.get("scheduled_sets", {}).get(muscle, 0)
            diff = t.volume_reconciliation.get("diff_sets", {}).get(muscle, 0)
            cls = "good" if abs(diff) <= 1 else "warn"
            html.append(f'<tr><td>{escape(muscle.title())}</td><td>{target}</td>'
                        f'<td>{scheduled}</td><td class="{cls}">{diff:+d}</td></tr>')
        html.append('</table>')
    html.append('<h3>Intensity</h3>')
    html.append(f'<p>Primary lifts: <b>{t.intensity.primary_reps}</b> reps @ '
                f'{t.intensity.primary_rir} RIR | '
                f'Accessories: <b>{t.intensity.accessory_reps}</b> reps @ '
                f'{t.intensity.accessory_rir} RIR</p>')
    html.append('<h3>Progression</h3>')
    html.append(f'<p>{escape(t.progression.primary)}<br>'
                f'<small>{escape(t.progression.rule)}</small></p>')
    html.append(f'<h3>Periodisation: {escape(t.periodisation.scheme)}</h3>')
    html.append(f'<p>{escape(t.periodisation.description)}</p>')
    html.append('</div>')

    # Schedule
    html.append('<div class="panel"><h2>Weekly Schedule</h2>')
    for day, exs in t.weekly_schedule.items():
        html.append(f'<div class="day">{escape(day)}</div>')
        for ex in exs:
            html.append(
                f'<div class="exercise">'
                f'<div><b>{escape(ex["name"])}</b><br>'
                f'<small>{escape(ex["primary_muscle"])}</small></div>'
                f'<div>{escape(ex["sets_reps"])}<br><small>{ex["rir"]} RIR</small></div>'
                f'<div>{escape(" | ".join(ex["equipment"]))}</div>'
                f'</div>'
            )
            if ex.get("load_guidance"):
                lg = ex["load_guidance"]
                html.append(
                    f'<div class="recipe">Load guide: start around '
                    f'{lg["suggested_working_weight_kg"]:.1f} kg '
                    f'(from {escape(lg["source_lift"])}; est. 1RM '
                    f'{lg["estimated_1rm_kg"]:.1f} kg).</div>'
                )
    html.append('</div>')

    # Warm-up / Cool-down
    html.append('<div class="grid">')
    html.append('<div class="panel"><h2>Warm-up</h2><ul>')
    for s in t.warmup_protocol:
        html.append(f'<li>{escape(s)}</li>')
    html.append('</ul></div>')
    html.append('<div class="panel"><h2>Cool-down</h2><ul>')
    for s in t.cooldown_protocol:
        html.append(f'<li>{escape(s)}</li>')
    html.append('</ul></div>')
    html.append('</div>')

    # Cardio
    html.append('<div class="panel"><h2>Cardio Prescription</h2>')
    html.append('<table>')
    for k, v in t.cardio_prescription.items():
        html.append(f'<tr><th>{escape(k.replace("_", " ").title())}</th><td>{escape(v)}</td></tr>')
    html.append('</table>')
    html.append('<h3>Heart-rate Zones (Karvonen)</h3>')
    html.append('<table><tr><th>Zone</th><th>Range</th></tr>')
    for name, (lo, hi) in t.cardio_zones.zones.items():
        html.append(f'<tr><td>{escape(name.replace("_", " ").title())}</td>'
                    f'<td>{lo:.0f} - {hi:.0f} bpm</td></tr>')
    html.append('</table></div>')

    # Meal plan
    html.append('<div class="panel"><h2>Meal Plan</h2>')
    html.append(f'<p>Cuisines: {escape(" | ".join(n.cuisine))}</p>')
    # Track snack position so 5-meal layouts render "Morning Snack" / "Afternoon Snack"
    # rather than two identical "Snack" labels. See audit finding F78.
    snack_position = 0
    for meal in n.meal_plan.meals:
        slot_label = meal.slot.title()
        # Render snack_1 / snack_2 with positional disambiguation.
        if meal.slot in {"snack_1", "snack_2"} or meal.slot == "snack":
            snack_position += 1
            if meal.slot == "snack_1" or (meal.slot == "snack" and snack_position == 1):
                slot_label = "Morning Snack"
            elif meal.slot == "snack_2" or (meal.slot == "snack" and snack_position == 2):
                slot_label = "Afternoon Snack"
            else:
                slot_label = f"Snack {snack_position}"
        else:
            # Reset snack counter when we leave snack territory.
            snack_position = 0
        html.append(f'<div class="day">{escape(slot_label)}</div>')
        html.append(f'<b>{escape(meal.name)}</b> '
                    f'<span class="tag">{meal.calories:.0f} kcal</span> '
                    f'<span class="tag">P {meal.protein_g:.0f}</span> '
                    f'<span class="tag">C {meal.carbs_g:.0f}</span> '
                    f'<span class="tag">F {meal.fat_g:.0f}</span>')
        if meal.recipe:
            html.append(f'<div class="recipe">{escape(meal.recipe)}</div>')
    html.append('</div>')

    # Supplements
    html.append('<div class="panel"><h2>Supplement Stack</h2>')
    any_supps = False
    for section in ("foundational", "goal_specific", "conditional"):
        items = n.supplements.get(section, [])
        if not items:
            continue
        any_supps = True
        html.append(f'<h3>{escape(section.replace("_", " ").title())}</h3>')
        html.append('<table><tr><th>Name</th><th>Dose</th><th>Rationale</th></tr>')
        for nm, dose, why in items:
            html.append(f'<tr><td>{escape(nm)}</td>'
                        f'<td>{escape(dose)}</td>'
                        f'<td>{escape(why)}</td></tr>')
        html.append('</table>')
    if not any_supps:
        html.append('<p>No specific supplements recommended. Focus on whole foods.</p>')
    html.append('</div>')

    html.append(f'<footer>Generated by Fitness Engine v{__version__} | '
                f'{escape(rec.archetype_signature)} | '
                f'Target: {e.calorie_target:.0f} kcal | '
                f'Volume: {t.weekly_volume.total_sets} sets/wk<br>'
                f'Educational/coaching use only; not medical advice. '
                f'Consult a qualified clinician before starting if you have '
                f'a medical condition, injury, pregnancy/post-partum status, '
                f'eating-disorder history, or recent surgery.</footer>')
    html.append('</body></html>')
    return "\n".join(html)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("profile", help="path to client JSON")
    parser.add_argument("output",  help="path to output HTML")
    args = parser.parse_args()

    with open(args.profile) as fh:
        data = json.load(fh)
    profile = ClientProfile.from_dict(data)
    rec = Recommender(profile).recommend()

    html = render(rec, data.get("name", "Client"))
    # Auto-create the output directory if it doesn't exist. Previously the
    # script crashed with FileNotFoundError when the user supplied a path
    # whose parent directory didn't exist (e.g., `output/foo.html` when
    # `output/` hadn't been created). See audit finding F77.
    out_dir = os.path.dirname(os.path.abspath(args.output))
    os.makedirs(out_dir, exist_ok=True)
    with open(args.output, "w") as fh:
        fh.write(html)
    print(f"Wrote {args.output}  ({len(html):,} bytes)")


if __name__ == "__main__":
    main()
