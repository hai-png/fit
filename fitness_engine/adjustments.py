"""
adjustments.py
==============

Diet and training adjustment protocols, plateau troubleshooting
checklists, and progress tracking guidance — all grounded in the
RippedBody methodology.

Sources:
  • rippedbody.com/how-to-adjust-macros/   (cutting adjustments)
  • rippedbody.com/how-to-adjust-macros-bulk/ (bulking adjustments)
  • rippedbody.com/training-plateaus/       (training plateau tree)
  • rippedbody.com/why-my-weight-going-up-and-down-while-dieting/
  • rippedbody.com/initial-adjustment/
  • rippedbody.com/diet-progress-tracking
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .archetypes import ExperienceLevel
from .calculators import BULK_MONTHLY_RATE, FAT_LOSS_WEEKLY_RATE


# --------------------------------------------------------------------------- #
# Cut/bulk decision boundaries (rippedbody.com/cut-or-bulk)                  #
# --------------------------------------------------------------------------- #
# Body-fat % boundaries for phase transitions. Men's boundaries are tighter;
# add ~8% for women.
CUT_BULK_BOUNDARIES = {
    # (sex, lower_limit, upper_limit) in body-fat %
    "male":   {"end_cut": 10, "end_bulk": 20},
    "female": {"end_cut": 18, "end_bulk": 28},
}


# --------------------------------------------------------------------------- #
# Fat-loss troubleshooting checklist                                          #
# --------------------------------------------------------------------------- #
@dataclass
class CutAdjustmentChecklist:
    """Decision-tree checklist for when fat loss stalls (cutting).

    RippedBody's key principle: calorie reduction is the LAST resort.
    Work through these in order before reducing food intake.
    """
    steps: List[Dict[str, str]] = field(default_factory=list)
    cardio_guidance: str = ""
    adjustment_kcal: int = 200


def cut_adjustment_checklist() -> CutAdjustmentChecklist:
    """Return the RippedBody fat-loss troubleshooting decision tree.

    Source: rippedbody.com/how-to-adjust-macros/#checklist
    """
    steps = [
        {
            "step": 1,
            "check": "Are you tracking accurately?",
            "action": "Verify you're weighing food (not estimating), logging "
                      "everything including oils, sauces, and drinks. "
                      "Under-reporting is the #1 cause of 'stalls'.",
        },
        {
            "step": 2,
            "check": "Are you managing hunger?",
            "action": "Swap liquid calories for whole food. Cut highly-palatable "
                      "sugary foods. Eat more fruit, vegetables, salads, soups. "
                      "Consider lowering meal frequency for larger, more "
                      "satisfying meals.",
        },
        {
            "step": 3,
            "check": "Is your food environment managed?",
            "action": "Control what's around you: clear junk from the house, "
                      "stock the fridge with foods you want to eat, reduce "
                      "temptations at work.",
        },
        {
            "step": 4,
            "check": "Have you revisited your 'why'?",
            "action": "Think deeply about your motivations. When things get "
                      "tough, a strong emotional connection to your goal keeps "
                      "you going.",
        },
        {
            "step": 5,
            "check": "Is stress under control?",
            "action": "Stress causes water retention and impairs recovery. "
                      "It is the silent killer of muscle mass. Consider "
                      "stress-management strategies.",
        },
        {
            "step": 6,
            "check": "Are you sleeping 7+ hours?",
            "action": "Poor sleep exacerbates hunger, dampens training "
                      "response, and mimics the effects of stress. If you "
                      "wake chronically tired, you need more sleep.",
        },
        {
            "step": 7,
            "check": "Has your daily activity (steps) decreased?",
            "action": "NEAT drops during a cut due to lethargy. Check your "
                      "step count. Set a daily minimum (e.g., 5,000-8,000). "
                      "Don't wait — walk more.",
        },
        {
            "step": 8,
            "check": "Have you waited long enough?",
            "action": "Use 3-4 weeks of tracking data before deciding. "
                      "Weight can stall for 1-2 weeks due to water retention "
                      "even while fat loss continues. Don't panic.",
        },
        {
            "step": 9,
            "check": "Can you add cardio instead of cutting food?",
            "action": "Add Zone-2 cardio before reducing calories. This keeps "
                      "you eating as much as possible for as long as possible, "
                      "minimizing muscle loss risk.",
        },
        {
            "step": 10,
            "check": "Last resort: reduce calories",
            "action": "Reduce daily intake by ~200-250 kcal. Reduce from "
                      "carbs first (and fat if already low). Never reduce "
                      "protein. Wait 3-4 weeks before adjusting again.",
        },
    ]
    return CutAdjustmentChecklist(
        steps=steps,
        cardio_guidance=(
            "Cardio should be less than half the time you spend lifting. "
            "If you lift 3 hours/week, cap cardio at 90 min/week. "
            "Excessive cardio is unsustainable and interferes with recovery."
        ),
        adjustment_kcal=200,
    )


# --------------------------------------------------------------------------- #
# Bulk adjustment checklist                                                   #
# --------------------------------------------------------------------------- #
@dataclass
class BulkAdjustmentChecklist:
    """Decision-tree checklist for when weight gain stalls (bulking)."""
    steps: List[Dict[str, str]] = field(default_factory=list)
    adjustment_pct: float = 5.0  # 5% calorie increase
    wait_weeks: int = 5


def bulk_adjustment_checklist() -> BulkAdjustmentChecklist:
    """Return the RippedBody bulk troubleshooting decision tree.

    Source: rippedbody.com/how-to-adjust-macros-bulk/#checklist
    """
    steps = [
        {
            "step": 1,
            "check": "Are you tracking accurately?",
            "action": "Verify you're eating as much as you think. Under-eating "
                      "is common for hard gainers who rely on feel rather than "
                      "tracking.",
        },
        {
            "step": 2,
            "check": "Are you feeling too full?",
            "action": "Swap some whole food for liquid calories (shakes, smoothies). "
                      "Eat more quickly. Consider higher meal frequency. If "
                      "skipping breakfast, add it back.",
        },
        {
            "step": 3,
            "check": "Is your food environment set up?",
            "action": "Keep calorie-dense foods in the house and at work. "
                      "Stock nuts, dried fruit, oils, nut butters.",
        },
        {
            "step": 4,
            "check": "Have you revisited your 'why'?",
            "action": "Bulking can be a chore — eating enough is hard. "
                      "Reconnect with why you're doing this.",
        },
        {
            "step": 5,
            "check": "Is stress under control?",
            "action": "Stress causes you to gain more fat and less muscle than "
                      "you should. It impacts recovery and partitioning.",
        },
        {
            "step": 6,
            "check": "Are you sleeping 7+ hours?",
            "action": "Poor sleep kills gains — more fat, less muscle from the "
                      "same surplus. Prioritise sleep.",
        },
        {
            "step": 7,
            "check": "Has your daily activity (NEAT) increased?",
            "action": "High NEAT responders burn off surplus calories through "
                      "fidgeting and movement. Don't restrict activity — just "
                      "eat more.",
        },
        {
            "step": 8,
            "check": "Have you waited 5 weeks?",
            "action": "Weight comes up fast in week 1 (water/glycogen), then "
                      "slows. Wait 5 weeks of data before deciding if the rate "
                      "is right.",
        },
        {
            "step": 9,
            "check": "Last resort: increase calories",
            "action": "Increase daily intake by ~5% (~150-200 kcal). "
                      "Add mostly carbs. Wait 5 weeks before adjusting again.",
        },
    ]
    return BulkAdjustmentChecklist(
        steps=steps,
        adjustment_pct=5.0,
        wait_weeks=5,
    )


# --------------------------------------------------------------------------- #
# Training plateau troubleshooting                                            #
# --------------------------------------------------------------------------- #
@dataclass
class PlateauChecklist:
    """Training plateau decision tree.

    Source: rippedbody.com/training-plateaus/#checklist
    """
    steps: List[Dict[str, str]] = field(default_factory=list)


def training_plateau_checklist() -> PlateauChecklist:
    """Return the training plateau troubleshooting decision tree."""
    steps = [
        {
            "step": 1,
            "check": "Are you sleeping 7+ hours?",
            "action": "Sleep deprivation impairs recovery, reduces strength, "
                      "and blunts hypertrophy. If you're at 6 hours, aim for 7.",
        },
        {
            "step": 2,
            "check": "Are you eating enough?",
            "action": "You can't build something from nothing. The leaner and "
                      "more experienced you are, the harder progress is at "
                      "maintenance or below. Consider a slight surplus.",
        },
        {
            "step": 3,
            "check": "Are you eating enough protein?",
            "action": "Minimum 1.6 g/kg (0.7 g/lb) of body weight. More if "
                      "dieting (2.2+ g/kg). Protein preserves muscle during "
                      "cuts and drives growth during bulks.",
        },
        {
            "step": 4,
            "check": "Are you training hard enough (or too hard)?",
            "action": "Overestimating RPE = not training close enough to failure "
                      "(exceptionally common). Underestimating RPE = training too "
                      "close to failure too often (less common, but causes "
                      "excessive fatigue). Use RIR guidelines.",
        },
        {
            "step": 5,
            "check": "Are you hitting each muscle group 2×/week?",
            "action": "Frequency of at least 2×/week per muscle group optimises "
                      "hypertrophy. Check your split — if you train each body "
                      "part once/week, consider increasing frequency.",
        },
        {
            "step": 6,
            "check": "Is your technique sound?",
            "action": "Poor form cheats you out of progress. Have a trusted "
                      "coach or experienced friend review your lifts. Film "
                      "yourself.",
        },
        {
            "step": 7,
            "check": "Do you have joint or tendon pain?",
            "action": "If yes, increase reps to 12-20 on painful movements. "
                      "If still painful, consider blood flow restriction (BFR) "
                      "training at 20-30% 1RM. Don't push through sharp pain.",
        },
        {
            "step": 8,
            "check": "Are you managing volume appropriately?",
            "action": "If progress stalls, try increasing volume (1-2 sets per "
                      "exercise). If you're chronically fatigued, try reducing "
                      "volume 20-30% or taking a deload week.",
        },
    ]
    return PlateauChecklist(steps=steps)


# --------------------------------------------------------------------------- #
# Progress tracking guidance                                                  #
# --------------------------------------------------------------------------- #
@dataclass
class ProgressTrackingGuide:
    """Guidance on how to track diet and training progress.

    Source: rippedbody.com/diet-progress-tracking
    """
    weight_tracking: List[str] = field(default_factory=list)
    measurement_tracking: List[str] = field(default_factory=list)
    photo_tracking: List[str] = field(default_factory=list)
    strength_tracking: List[str] = field(default_factory=list)
    what_to_expect: List[str] = field(default_factory=list)


def progress_tracking_guide() -> ProgressTrackingGuide:
    return ProgressTrackingGuide(
        weight_tracking=[
            "Weigh yourself every morning, immediately after using the "
            "bathroom, before eating or drinking.",
            "Record daily weight. Use the weekly average — not individual days.",
            "Ignore the first week of data after starting/changing a diet "
            "(water and glycogen shifts dominate).",
        ],
        measurement_tracking=[
            "Measure 9 points weekly: chest at nipple line; left/right upper arm; "
            "left/right thigh; stomach at navel, 3 finger-widths above, and "
            "3 finger-widths below.",
            "Use a non-stretch or auto-tightening tape measure. Measure at the "
            "same time of day (morning is best).",
            "Measurements confirm whether the intended tissue is changing, "
            "especially during recomp when scale weight may be stable.",
        ],
        photo_tracking=[
            "Take monthly progress photos in the same lighting, distance, poses, "
            "and time of day.",
            "Use photos as a recomp indicator, not day-to-day mirror checks.",
        ],
        strength_tracking=[
            "Log exercises, sets, reps, load, and RIR/RPE for progressive overload.",
            "Assess strength trends over weeks; short-term dips are common during cuts.",
        ],
        what_to_expect=[
            "Weight loss is rarely linear — expect stalls and 'whooshes'.",
            "A 'whoosh' is when the scale suddenly drops after a stall. Fat "
            "cells empty of fat but fill with water temporarily, then release.",
            "Water retention from stress, poor sleep, high sodium, or hormonal "
            "changes can mask fat loss for 1-2 weeks.",
            "When bulking, expect a large weight jump in week 1 (water + "
            "glycogen), then a slower, steadier rate.",
            "As you get leaner, fat loss rate should slow down to preserve "
            "muscle. 0.5% BW/week is the sweet spot near single-digit BF%.",
        ],
    )


# --------------------------------------------------------------------------- #
# Metabolic adaptation guidance                                               #
# --------------------------------------------------------------------------- #
@dataclass
class MetabolicAdaptationInfo:
    """Information about metabolic adaptation during dieting.

    Sources: zolthealth.com/learn/what-is-adaptive-tdee,
             rippedbody.com/calories/
    """
    explanation: str = ""
    impact_range: str = ""
    mitigation: List[str] = field(default_factory=list)


def metabolic_adaptation_info() -> MetabolicAdaptationInfo:
    return MetabolicAdaptationInfo(
        explanation=(
            "When you diet, your metabolism slows down to fight the calorie "
            "deficit. This is called metabolic adaptation (or adaptive "
            "thermogenesis). It reduces your TDEE by 15-25% during prolonged "
            "calorie restriction, which is why weight loss plateaus occur "
            "even when you haven't changed your intake."
        ),
        impact_range="TDEE can drop by 15-25% during prolonged dieting",
        mitigation=[
            "Our calorie calculations use a 0.75%/week fat-loss rate (not "
            "0.5%) to pre-account for metabolic adaptation.",
            "Take a diet break (eat at maintenance for 1-2 weeks) every "
            "6-8 weeks to partially reverse adaptation.",
            "Don't reduce calories proactively — wait until the weight-loss "
            "rate actually slows, then adjust by 200-250 kcal.",
            "Track steps/NEAT — it drops during a cut and accelerates "
            "adaptation. Maintain a daily minimum.",
            "If using an adaptive TDEE approach (tracking real weight change "
            "vs intake over weeks), trust the trend over the formula.",
        ],
    )


# --------------------------------------------------------------------------- #
# Expected rates of progress (by training status)                             #
# --------------------------------------------------------------------------- #
# The bulk monthly rates and fat-loss weekly rate are imported from
# calculators.py (see top of file) so we have a single source of truth.
# See audit finding F72.

PROGRESS_RATES = {
    # RippedBody expected rates of progress by training status
    "muscle_gain_per_month_kg": {
        "beginner": (1.0, 1.5),      # 2-3 lbs/month
        "intermediate": (0.5, 1.0),  # 1-2 lbs/month
        "advanced": (0.25, 0.5),     # 0.5-1 lb/month
    },
    # Re-export the canonical bulk monthly rates from calculators.py keyed
    # by experience-level string. This guarantees the adjustment guidance
    # and the calorie calculator use the same source of truth.
    "weight_gain_rate_per_month_pct": {
        ExperienceLevel.BEGINNER.value: BULK_MONTHLY_RATE[ExperienceLevel.BEGINNER],
        ExperienceLevel.INTERMEDIATE.value: BULK_MONTHLY_RATE[ExperienceLevel.INTERMEDIATE],
        ExperienceLevel.ADVANCED.value: BULK_MONTHLY_RATE[ExperienceLevel.ADVANCED],
    },
    "fat_loss_rate_per_week_pct": FAT_LOSS_WEEKLY_RATE,
}


# --------------------------------------------------------------------------- #
# Initial calorie assessment (first 3-4 weeks)                                #
# --------------------------------------------------------------------------- #
@dataclass
class InitialAssessmentGuidance:
    """Structured initial-assessment guidance.

    The legacy ``initial_assessment_guidance`` function returns a list of
    strings with ASCII-art bullets that render poorly in HTML. This
    dataclass provides the same information in a machine-readable form so
    renderers can format it appropriately. See audit finding F73.
    """
    expected_rate_kg_per_week: float
    wait_weeks: int
    rules: List[Dict[str, str]]  # each: {"condition": ..., "action": ..., "adjustment": ...}
    summary: str


def initial_assessment_guidance(
    goal: str, expected_change_per_week_kg: float,
) -> List[str]:
    """Return guidance for assessing whether initial calculations are correct.

    Source: rippedbody.com/initial-adjustment/

    Returns a list of strings for backwards compatibility. For a machine-
    readable form, use :func:`initial_assessment_guidance_structured`.
    See audit finding F73.
    """
    guidance = [
        f"Expected rate: ~{expected_change_per_week_kg:.2f} kg/week.",
        "Wait 3-4 weeks before assessing — ignore the first week (water shifts).",
        "If weight changes faster than expected after week 1:",
        "  -> Adjust calorie intake to correct the rate.",
        "  -> For cuts: if losing >1% BW/week, increase calories by 200-250.",
        "  -> For cuts: if losing <0.5% BW/week (after week 2), decrease by 200-250.",
        "  -> For bulks: if gaining >2% BW/month, decrease by 150 kcal.",
        "  -> For bulks: if gaining <0.5% BW/month (after week 3), increase by 150 kcal.",
    ]
    return guidance


def initial_assessment_guidance_structured(
    goal: str, expected_change_per_week_kg: float,
) -> InitialAssessmentGuidance:
    """Structured version of :func:`initial_assessment_guidance`.

    Returns an :class:`InitialAssessmentGuidance` dataclass with machine-
    readable fields. See audit finding F73.
    """
    rules = [
        {
            "condition": "Losing >1% BW/week (cut)",
            "action": "increase calories",
            "adjustment": "200-250 kcal/day",
        },
        {
            "condition": "Losing <0.5% BW/week after week 2 (cut)",
            "action": "decrease calories",
            "adjustment": "200-250 kcal/day",
        },
        {
            "condition": "Gaining >2% BW/month (bulk)",
            "action": "decrease calories",
            "adjustment": "150 kcal/day",
        },
        {
            "condition": "Gaining <0.5% BW/month after week 3 (bulk)",
            "action": "increase calories",
            "adjustment": "150 kcal/day",
        },
    ]
    return InitialAssessmentGuidance(
        expected_rate_kg_per_week=round(expected_change_per_week_kg, 3),
        wait_weeks=3,
        rules=rules,
        summary=(
            f"Expected rate: ~{expected_change_per_week_kg:.2f} kg/week. "
            f"Wait 3-4 weeks before assessing; ignore the first week "
            f"(water shifts). Adjust calories per the rules if the trend "
            f"diverges from the expected rate."
        ),
    )
