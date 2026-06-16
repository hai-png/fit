"""
Strict multi-combo review: for each of the 77 multi-workout combos, keep only
options that are DISTINCTLY different (muscle group, equipment subtype,
demographic, split structure) and easy for an app user to choose between.
Decisions reference workouts by their [n] index when each combo is sorted by title.
"""
import csv, json
from collections import defaultdict

rows = list(csv.DictReader(open('organized_workouts/workouts_classified.csv')))
matrix = defaultdict(list)
for r in rows:
    key = (r['equipment'], r['fitness_goal'], r['workout_type'], r['gender'], r['training_level'], r['days_per_week'])
    matrix[key].append(r)
multi = {k: sorted(v, key=lambda x: x['title']) for k, v in sorted(matrix.items()) if len(v) > 1}
combos = list(multi.items())  # combo #i = combos[i-1]

# decisions: combo_num -> (keep_indices(1-based), {remove_idx: reason}, note)
D = {}
D[1]=( [1], {2:"Duplicate concept: another beginner bodyweight fat-loss circuit; women-titled in a 'both' slot"} , "Keep one standard bodyweight fat-loss program")
D[2]=( [1], {2:"Gimmick format (dice & cards randomized workout) — confusing choice"}, "Keep standard bodyweight circuit")
D[3]=( [1], {2:"Requires outdoor stairs — situational/niche vs. general lower-body circuit"}, "Keep general lower-body circuit")
D[4]=( [1,3,4], {2:"Generic fat-loss circuit, duplicates the standard 8-week option"}, "Keep: 40+ (demographic), standard 8-week, 30-min time-saver — three distinct user choices")
D[5]=( [1], {2:"Older duplicate cutting routine with thin description; same audience as 10 Weeks to Shredded"}, "Keep one advanced 6-day cut")
D[6]=( [2,3], {1:"Sponsor-branded collection of 5 workout variations — not a single followable program"}, "Keep: glute-focused (distinct emphasis) + standard fat-loss program")
D[7]=( [1], {2:"Duplicate: generic 8-week beginner fat-loss program", 3:"Duplicate: generic 10-week beginner fat-loss program"}, "Three near-identical beginner fat-loss splits; keep clearest one")
D[8]=( [2], {1:"Add-on conditioning samples (raw type 'Cardio'), not a standalone program", 3:"Duplicate concept: generic summer shred, same as kept option"}, "Keep one 3-day split + cardio program")
D[9]=( [1,2], {3:"Situational gimmick (crowded-gym workaround)", 4:"Older duplicate weights+cardio cut", 5:"21-day crash cycle, diet-centric duplicate", 6:"Duplicate concept of kept shred cycle", 7:"Generic shred duplicate", 8:"Generic shred duplicate", 9:"Generic seasonal shred duplicate"}, "Keep: standard shred cycle + ab-focused V-Cut (distinct emphasis)")
D[10]=( [3], {1:"Older duplicate 5-day cutting routine", 2:"Generic 8-week fat-loss duplicate", 4:"Generic 8-week fat-loss duplicate", 5:"Generic 8-week fat-loss duplicate"}, "Five interchangeable 5-day fat-loss splits; keep one")
D[11]=( [1], {2:"Dice-roll gimmick programming", 3:"Duplicate weights+HIIT concept"}, "Keep one standard 6-day weights/cardio cut")
D[12]=( [2], {1:"Older duplicate; kept the more complete modern 12-week program"}, "Keep one")
D[13]=( [1], {2:"Duplicate: seasonal 6-week version of the same women's fat-loss concept"}, "Keep flagship 12-week women's trainer")
D[14]=( [1,6], {2:"Duplicate generic beginner 3-day full body", 3:"Women-specific program in a 'both' slot; women's combo exists separately", 4:"Duplicate beginner full body", 5:"Tall-guys variant — niche", 7:"Generic staged mass program, duplicate concept", 8:"Duplicate beginner full body", 9:"Duplicate generic 8-week beginner program"}, "Keep: classic 12-week beginner routine + HIT (genuinely different training style)")
D[15]=( [1,4], {2:"Generic intermediate full body duplicate", 3:"Generic time-saver system, duplicate concept"}, "Keep: 30-min toning option + strength & hypertrophy option")
D[16]=( [1], {2:"Supplement-brand tie-in program"}, "Keep weakness-priority program")
D[17]=( [2,3], {1:"Tall-women variant — niche", 4:"Duplicate: shorter version of same beginner women's plan"}, "Keep: Smith-machine-only (equipment distinct) + standard 8-week program")
D[18]=( [1,2,3,4,10], {5:"Duplicate arm day (arms already covered)", 6:"Duplicate shoulder workout", 7:"Duplicate shoulder workout (same coach)", 8:"Duplicate arm program", 9:"Duplicate leg cycle"}, "Keep exactly one per muscle group: legs, arms, chest, shoulders, back")
D[19]=( [5,6,7,8,18], {1:"Duplicate chest (bench-focus)", 2:"Duplicate chest", 3:"Niche quad variant", 4:"Duplicate arms", 9:"Triceps-only; arms covered by biceps+triceps pick", 10:"Multi-muscle combo (back/shoulders/traps) — overlaps back pick", 11:"Duplicate chest collection", 12:"Duplicate arms collection", 13:"Duplicate chest", 14:"Duplicate arms", 15:"Duplicate back", 16:"3-level glute collection — overlaps glute pick", 17:"Duplicate legs", 19:"Duplicate chest/bench", 20:"Duplicate legs"}, "Keep one per muscle group: arms, back, chest, legs, glutes")
D[20]=( [1,2], {3:"Duplicate arm specialization (arms already covered)"}, "Keep arms + quads (different muscle groups)")
D[21]=( [3,6,8,9,20,25], {1:"Duplicate back",2:"Duplicate shoulders",4:"Duplicate shoulders",5:"Duplicate chest",7:"Duplicate back",10:"Duplicate chest",11:"Duplicate chest collection",12:"Duplicate quads (legs covered)",13:"Cable-only arms — minor equipment variant of arms pick",14:"Duplicate shoulders",15:"Duplicate chest",16:"Duplicate shoulders",17:"Women-specific chest in 'both' slot; duplicate chest",18:"Athlete-profile article, not a clean program",19:"Duplicate legs",21:"Duplicate legs",22:"Duplicate arms",23:"Triceps-only; arms covered",24:"Duplicate quads",26:"Duplicate back",27:"Duplicate chest",28:"Duplicate shoulders",29:"Chest+back combo — overlaps two picks",30:"Duplicate back",31:"Duplicate shoulders",32:"Women-specific legs in 'both' slot; duplicate legs",33:"Duplicate shoulders",34:"Duplicate back"}, "34 → 6: one per muscle group (back, shoulders, chest, arms, legs, glutes)")
D[22]=( [1,4,7,8], {2:"Arm workout collection — duplicate arms",3:"Duplicate arms (biceps-only)",5:"Celebrity/competition prep workout",6:"Single leg day, legs covered by 2-day leg pick",9:"Push-day (multi-muscle) — doesn't fit single-muscle-group slot"}, "Keep one per muscle group: legs, abs, arms, back")
D[23]=( [1], {2:"Misclassified: a general 4-day split, not single-muscle-group",3:"Vague plateau system, not muscle-group specific"}, "Keep abs program")
D[24]=( [2], {1:"Full split training system — misfit for single-muscle-group slot"}, "Keep legs program")
D[25]=( [2,3,4], {1:"Back+shoulders combo — overlaps the dedicated back and shoulder picks"}, "Keep one per muscle group: back, shoulders, chest")
D[26]=( [2,3,4], {1:"Triceps-only; arms covered by giant-arms pick",5:"Inner-chest niche; chest covered",6:"Duplicate chest"}, "Keep one per muscle group: legs, arms, chest")
D[27]=( [1,2], {}, "Keep both: biceps vs hamstrings — different muscle groups")
D[28]=( [1], {2:"Older duplicate intense 3-day routine"}, "Keep modern HIT3 program")
D[29]=( [1,2], {3:"Generic TUT method duplicate"}, "Keep: body-part split + German Volume upper/lower (distinct structures)")
D[30]=( [1], {2:"Old vague duplicate",3:"Generic off-season duplicate",4:"Military-themed (novelty category already filtered elsewhere)"}, "Keep one advanced 5-day bodybuilding split")
D[31]=( [1,2], {3:"Generic advanced duplicate",4:"Generic anti-plateau duplicate"}, "Keep PPL + upper/lower (distinct 6-day structures)")
D[32]=( [1,3,4], {2:"Method-specific HIT variant — duplicate concept",5:"Pause-rep technique program — niche method",6:"Phase 2 of a multi-part series (Phase 1 lives in the 4-day combo) — confusing as standalone"}, "Keep: classic beginner split, machine-only (equipment), PPL (structure)")
D[33]=( [2,3,8,13,18], {1:"2-day specialization, not a true 4-day program",4:"Generic system duplicate",5:"Generic transformation duplicate",6:"College-themed duplicate",7:"Generic system duplicate",9:"Generic mass duplicate",10:"Part 2 of a phase series — fragment",11:"Seasonal duplicate",12:"Series part 1 — standard beginner option already kept",14:"Exercise-guide listicle with sample workouts",15:"College-themed duplicate",16:"Generic volume duplicate",17:"Overlaps the kept 40+ program"}, "Keep: standard beginner mass, 40+ (demographic), machine-only (equipment), parent & teen (demographic), upper/lower (structure)")
D[34]=( [2], {1:"Two-exercise article, not a full 5-day program",3:"Celebrity-trainer series cycle — novelty",4:"Tips article, not a clean program",5:"Intermediate-flavored duplicate"}, "Keep the true beginner 5-day foundation program")
D[35]=( [2,7], {1:"Generic body-part duplicate",3:"Drop-set method duplicate",4:"Method duplicate",5:"Forum-member duplicate",6:"Forum-member duplicate",8:"Maintenance routine — unclear goal fit"}, "Keep: Power Muscle Burn (popular system) + PPL (distinct structure)")
D[36]=( [4,5,26], {1:"Generic mass duplicate",2:"Forum duplicate",3:"Generic mass duplicate",6:"Method duplicate (rest-pause covered)",7:"Generic mass duplicate",8:"Generic duplicate",9:"Generic duplicate",10:"Volume-method duplicate",11:"Athlete-branded duplicate",12:"Superhero novelty",13:"Bulldozer variant duplicate",14:"Bulldozer duplicate",15:"Concept variant, duplicate audience",16:"Forum duplicate",17:"Forum duplicate",18:"Powerbuilding duplicate of PHUL",19:"Method duplicate",20:"Forum staple but duplicate of kept options",21:"Body-type niche framing, same training",22:"Method duplicate",23:"Superset duplicate",24:"Generic duplicate",25:"PHUL variant duplicate",27:"Forum duplicate",28:"Athlete duplicate",29:"Forum duplicate",30:"Forum duplicate",31:"Seasonal novelty",32:"Seasonal novelty",33:"Seasonal duplicate",34:"Tall-guys niche",35:"Method duplicate"}, "35 → 3: PPL, body-part (Power Muscle Burn), upper/lower (PHUL) — three structures users actually choose between")
D[37]=( [1,13,14], {2:"Timed-set method duplicate",3:"10-sessions/week retro program — extreme niche",4:"HIT variant duplicate",5:"Generic duplicate",6:"Periodization method duplicate",7:"Same bro-split concept as kept option",8:"Tall niche",9:"Seasonal novelty",10:"Specialization, not general program",11:"Duplicate, time-gimmick",12:"Sports-fan novelty"}, "Keep: PPL cycle, women's toning option, classic bro split")
D[38]=( [1,2], {3:"3-week shred — goal mismatch in muscle-building slot",4:"Retro novelty",5:"Retro novelty",6:"Tall niche",7:"Generic split duplicate",8:"Method duplicate",9:"Travel/hotel niche in fully-equipped-gym slot"}, "Keep: body-part 6-day + PPL powerbuilding (distinct structures)")
D[39]=( [1,3], {2:"Hybrid gimmick — duplicate audience"}, "Keep: body-part split + upper/lower (distinct structures)")
D[40]=( [1], {2:"Pro-bodybuilder pre-contest feature — competition niche",3:"Celebrity-inspired compilation",4:"AMRAP gimmick duplicate"}, "Keep one advanced 5-day program")
D[41]=( [1], {2:"Duplicate 3-day muscle program"}, "Keep established Bulldozer system")
D[42]=( [3], {1:"Timed-set method duplicate",2:"Generic duplicate",4:"Cycling-method duplicate",5:"Continuation of a beginner series — fragment"}, "Keep one clear upper/lower mass program")
D[43]=( [3], {1:"Bodybuilding-division specific (competition oriented)",2:"Duplicate strength+size concept"}, "Keep popular powerbuilding system")
D[44]=( [1,3], {2:"Tall-women niche"}, "Keep: 40+ (demographic) + standard women's 8-week program")
D[45]=( [1], {2:"Duplicate beginner strength program"}, "Keep famous ICF 5x5")
D[46]=( [1,2], {}, "Keep both: bench/chest vs core — different muscle groups")
D[47]=( [1,2], {}, "Keep both: bench vs deadlift — different lifts")
D[48]=( [3,4], {1:"Invented-lifts gimmick",2:"Celebrity-branded general strength duplicate"}, "Keep: squat specialization + beginner powerlifting (distinct focuses)")
D[49]=( [1], {2:"Rebuild-phase duplicate",3:"Method duplicate",4:"Older duplicate",5:"Westside variant duplicate",6:"Influencer-branded duplicate"}, "Keep one clear powerlifting program")
D[50]=( [1], {2:"Transformation-feature circuit, duplicate concept"}, "Keep dumbbell HIIT")
D[51]=( [4,10], {1:"Duplicate quick home circuit",2:"Duplicate circuit",3:"Duplicate dumbbell circuit",5:"Needs treadmill; duplicate kettlebell option",6:"Random-generator gimmick",7:"Duplicate circuit",8:"Single complex, duplicate kettlebell option",9:"Duplicate HIIT program"}, "Keep: kettlebell option vs dumbbell option — clear equipment choice")
D[52]=( [2], {1:"Random WOD collection, not a program"}, "Keep kettlebell program")
D[53]=( [1], {2:"Single circuit, not a full plan"}, "Keep complete 6-week plan")
D[54]=( [1], {2:"Time-gimmick duplicate"}, "Keep standard at-home women's program")
D[55]=( [1], {2:"Partner-based single cardio workout, not a program"}, "Keep kettlebell+bodyweight program")
D[56]=( [3], {1:"2-sessions/week density article — day-count mismatch",2:"Duplicate time-efficient shred"}, "Keep one clear 4-day quick fat-loss program")
D[57]=( [2,4], {1:"Core-focused, overlaps single-muscle-group combos",3:"Fight/kickbox themed niche",5:"Sports-performance niche",6:"Muscle-building flavored duplicate"}, "Keep: bodyweight vs kettlebell — clear equipment choice")
D[58]=( [1], {2:"Duplicate dumbbell circuit for women"}, "Keep one")
D[59]=( [1], {2:"Kickboxing niche (mitts required)"}, "Keep kettlebell fast-start")
D[60]=( [2], {1:"Abs listicle — overlaps single-muscle-group combos"}, "Keep conditioning program")
D[61]=( [1,5,7], {2:"Time-gimmick duplicate",3:"Unconventional tools niche",4:"Bodyweight-centric — overlaps bodyweight category",6:"Medicine-ball niche",8:"Duplicate barbell/DB full body",9:"Historical-figure program (novelty category)",10:"Body-type niche framing",11:"Sports/intramural novelty"}, "Keep: kettlebell, dumbbell-only, barbell+dumbbell — clear equipment choice")
D[62]=( [1], {2:"Duplicate glute-focused women's home plan"}, "Keep dumbbell-only option (also glute-focused)")
D[63]=( [1,3,4,5,6,7], {2:"Combined biceps+triceps — overlaps dedicated bicep and tricep picks",8:"Duplicate shoulders"}, "Keep one per muscle group: legs, biceps, forearms, shoulders, core, triceps")
D[64]=( [1,2,3], {}, "Keep all: chest vs abs vs forearms — different muscle groups")
D[65]=( [1,2], {}, "Keep both: abs vs glutes — different muscle groups")
D[66]=( [1,2], {}, "Keep both: upper-body (chin-up/dip) vs abs — different muscle groups")
D[67]=( [1,3,4,5], {2:"Duplicate shoulders",6:"Biceps-only; arms covered"}, "Keep one per muscle group: chest, shoulders, arms, traps")
D[68]=( [1,2,3], {}, "Keep all: chest/bench vs traps vs abs — different muscle groups")
D[69]=( [2], {1:"Beginner-to-advanced routine collection, not one program"}, "Keep single arm+shoulder session")
D[70]=( [1,2,3], {4:"Single ab circuit — mismatch for a 3-day split slot",5:"10-minute fragments, not a program",6:"Vague flexible-schedule plan"}, "Keep: barbell+bands vs bands-only vs dumbbell-only — clear equipment choice")
D[71]=( [2,3,5,8], {1:"New-year themed duplicate",4:"Duplicate limited-equipment superset plan",6:"New-year themed duplicate",7:"Duplicate barbell/DB plan"}, "Keep: dumbbell-only, glute-focused, barbell-only, kettlebell — distinct choices")
D[72]=( [2], {1:"Collection of 3 programs, not one",3:"Bench-press specialization — goal mismatch"}, "Keep 5-day at-home muscle split")
D[73]=( [1], {2:"Method-specific home variant — duplicate audience"}, "Keep standard dumbbell & barbell home workout")
D[74]=( [1,3], {2:"Squat/deadlift specialization niche",4:"Strength-goal mismatch in muscle-building slot"}, "Keep: barbell-only (no rack) + standard DB/BB home plan")
D[75]=( [1,2], {}, "Keep both: with-barbell vs dumbbell-only — meaningful home equipment choice")
D[76]=( [1,2], {}, "Keep both: bench press vs core — different muscle groups")
D[77]=( [1], {2:"Single-lift (bench) block cycle — specialization overlap"}, "Keep general intermediate strength program")

# Build removal map and report
removals = {}
report_lines = []
total_keep = total_remove = 0
for i, (key, items) in enumerate(combos, 1):
    keep_idx, rm_reasons, note = D[i]
    keep_idx = set(keep_idx)
    expected = set(range(1, len(items)+1))
    rm_idx = set(rm_reasons.keys())
    assert keep_idx | rm_idx == expected and not (keep_idx & rm_idx), f"combo {i}: keep={keep_idx} rm={rm_idx} n={len(items)}"
    report_lines.append(f"#{i:02d} [{len(items)}] {' | '.join(key)}")
    report_lines.append(f"    DECISION: {note}")
    for j, r in enumerate(items, 1):
        if j in keep_idx:
            report_lines.append(f"    KEEP   [{j}] {r['title']}")
            total_keep += 1
        else:
            removals[r['filename']] = f"Strict review #{i:02d}: {rm_reasons[j]}"
            report_lines.append(f"    REMOVE [{j}] {r['title']}  -- {rm_reasons[j]}")
            total_remove += 1
    report_lines.append("")
report_lines.append(f"TOTAL: kept {total_keep}, removed {total_remove} across {len(combos)} multi-combos")
open('strict_multicombo_review.txt','w').write("\n".join(report_lines))
json.dump(removals, open('strict_multicombo_removals.json','w'), indent=2)
print(f"kept {total_keep}, removed {total_remove}, removal file entries {len(removals)}")
