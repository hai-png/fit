"""
demo_arthur.py
==============

Quick demo of the senior-strength archetype. Same flow as demo_basic
but reading a different sample JSON.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fitness_engine import ClientProfile, Recommender

with open("examples/sample_arthur.json") as fh:
    data = json.load(fh)
profile = ClientProfile.from_dict(data)
rec = Recommender(profile).recommend()

print(f"Client   : {data['name']}  ({profile.age}y {profile.sex.value})")
print(f"Sig      : {rec.archetype_signature}")
print(f"BMI      : {rec.body_composition.bmi} ({rec.body_composition.bmi_category})")
print(f"BMR/TDEE : {rec.energy.bmr_mifflin} / {rec.energy.tdee}")
print(f"Target   : {rec.energy.calorie_target} kcal")
print(f"Macros   : P {rec.nutrition.macros.protein_g}  "
      f"C {rec.nutrition.macros.carbs_g}  "
      f"F {rec.nutrition.macros.fat_g}")
print(f"Volume   : {rec.training.weekly_volume.total_sets} sets/wk")
print(f"Period   : {rec.training.periodisation.scheme}")
print(f"\nWarnings:")
for w in rec.warnings: print(f"  - {w}")
print(f"\nNotes:")
for n in rec.notes: print(f"  - {n}")
print(f"\nSchedule:")
for d, exs in rec.training.weekly_schedule.items():
    print(f"  {d}:")
    for e in exs:
        print(f"    - {e['name']:35s} {e['sets_reps']:8s} RPE {e['rpe']}")
print(f"\nMeal plan ({rec.nutrition.meal_plan.name}):")
for m in rec.nutrition.meal_plan.meals:
    print(f"  {m.slot:10s} {m.name:50s} {m.calories:.0f} kcal")
