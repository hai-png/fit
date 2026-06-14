# 08 — Python API Reference

Every public symbol in the `fitness_engine` package. Module paths
given as `fitness_engine.<module>`.

## 8.1 `fitness_engine` — top-level

```python
from fitness_engine import (
    # archetypes
    ActivityLevel, AgeGroup, ArchetypeSignature, CookingSkill,
    DietaryPreference, ExperienceLevel, GoalArchetype, HealthCondition,
    SessionLength, Sex, Somatotype, TrainingEnvironment,
    CURATED_PROFILES, all_curated, get_curated, signature_from_dict,

    # calculators
    BodyComposition, CardioZones, EnergyExpenditure, Hydration, Macros,
    StrengthEstimate,
    body_composition, body_fat_navy, body_fat_bmi_method,
    bmi, bmi_category, bmr_mifflin, bmr_harris, bmr_katch, tdee,
    calorie_target, energy_expenditure, hydration, macros_for,
    cardio_zones, one_rep_max, weekly_tonnage,
    infer_age_group, infer_somatotype,

    # decision trees
    IntensityScheme, Periodisation, ProgressionRule, SessionDensity,
    TrainingSplit, WeeklyVolume,
    exercise_selection, intensity_scheme, macro_overrides,
    periodisation, cuisine_pick, progression_rule,
    session_density, supplement_stack, training_split, weekly_volume,

    # meal plans
    MealItem, MealPlan, MEAL_LIBRARY, assemble_day,

    # exercise plans
    EXERCISE_LIBRARY, Exercise, weekly_split, build_session,

    # questionnaires
    PAR_Q, HEALTH_HISTORY, LIFESTYLE, DIETARY, FITNESS_HISTORY, GOALS,
    FULL_INTAKE, parq_score, intake_report, IntakeReport,

    # main
    ClientProfile, PlanRecommendation, TrainingPlan, NutritionPlan,
    Recommender,
    assemble_week,
    enumerate_signatures, total_combinations,
)
```

## 8.2 `archetypes` — enums & catalog

### `GoalArchetype`
`FAT_LOSS, MUSCLE_GAIN, RECOMPOSITION, STRENGTH, ENDURANCE,
GENERAL_HEALTH, ATHLETIC_PERFORMANCE, REHABILITATION`

### `Somatotype`
`ECTOMORPH, MESOMORPH, ENDOMORPH, MIXED`

### `ExperienceLevel`
`NOVICE, BEGINNER, INTERMEDIATE, ADVANCED, ELITE`

### `AgeGroup`
`YOUTH, YOUNG_ADULT, ADULT, MIDDLE, SENIOR, ELDER`

### `Sex`
`MALE, FEMALE`

### `ActivityLevel`
`SEDENTARY, LIGHT, MODERATE, VERY_ACTIVE, ATHLETE`

### `DietaryPreference`
`OMNIVORE, PESCATARIAN, POLLO_PESCATARIAN, VEGETARIAN, VEGAN,
KETO, MEDITERRANEAN, LOW_FODMAP, HALAL, KOSHER, FLEXIBLE`

### `TrainingEnvironment`
`HOME_BODYWEIGHT, HOME_MINIMAL, HOME_FULL, GYM_COMMERCIAL,
GYM_FULL, HYBRID, OUTDOOR`

### `HealthCondition`
`NONE, TYPE_2_DIABETES, PRE_DIABETES, HYPERTENSION, HIGH_CHOLESTEROL,
PCOS, HYPOTHYROIDISM, JOINT_ISSUES_KNEE, JOINT_ISSUES_SHOULDER,
LOWER_BACK, CARDIO_LIMITED, CELIAC, IBS, PREGNANCY, POSTPARTUM`

### `SessionLength`
`EXPRESS_30, SHORT_45, STANDARD_60, EXTENDED_90`

### `CookingSkill`
`BASIC, INTERMEDIATE, ADVANCED`

### `ArchetypeSignature`
```python
@dataclass(frozen=True)
class ArchetypeSignature:
    goal: GoalArchetype
    somatotype: Somatotype
    experience: ExperienceLevel
    age_group: AgeGroup
    sex: Sex
    activity: ActivityLevel
    diet: DietaryPreference
    environment: TrainingEnvironment
    session: SessionLength
    def code(self) -> str: ...
```

### Catalog functions
```python
total_combinations() -> int                    # 1,178,880
enumerate_signatures() -> List[ArchetypeSignature]
signature_from_dict(d: Dict) -> ArchetypeSignature
all_curated() -> List[ArchetypeProfile]
get_curated(name: str) -> Optional[ArchetypeProfile]
```

### `ArchetypeProfile`
```python
@dataclass
class ArchetypeProfile:
    signature: ArchetypeSignature
    nickname: str
    summary: str
    strengths: List[str]
    risks: List[str]
    emphasis: List[str]
```

## 8.3 `calculators` — numerical engines

### `BodyComposition`
```python
@dataclass
class BodyComposition:
    bmi: float
    bmi_category: str
    body_fat_pct: Optional[float]
    lean_mass_kg: Optional[float]
    fat_mass_kg: Optional[float]
```

### `EnergyExpenditure`
```python
@dataclass
class EnergyExpenditure:
    bmr_mifflin: float
    bmr_harris: float
    bmr_katch: Optional[float]
    tdee: float
    activity_multiplier: float
    calorie_target: float
    calorie_target_breakdown: dict
```

### `Macros`
```python
@dataclass
class Macros:
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    protein_pct: float
    carbs_pct: float
    fat_pct: float
    rationale: str
```

### `Hydration`
```python
@dataclass
class Hydration:
    base_ml: float
    workout_bonus_ml: float
    total_ml: float
```

### `StrengthEstimate`
```python
@dataclass
class StrengthEstimate:
    epley_1rm: float
    brzycki_1rm: float
    lander_1rm: float
    average_1rm: float
    pct_of_1rm: dict
```

### `CardioZones`
```python
@dataclass
class CardioZones:
    age: int
    hr_max_simple: int
    hr_max_tanaka: int
    zones: dict   # name -> (low, high) bpm
```

### Calculator functions
```python
bmi(weight_kg, height_cm) -> float
bmi_category(b) -> BMICategory
bmr_mifflin(weight_kg, height_cm, age, sex) -> float
bmr_harris(weight_kg, height_cm, age, sex) -> float
bmr_katch(weight_kg, lean_mass_kg) -> float
tdee(bmr, activity_level) -> float
calorie_target(tdee, goal, deficit_pct=0.20, surplus_pct=0.12) -> (float, dict)
energy_expenditure(weight_kg, height_cm, age, sex,
                   activity, goal, lean_mass_kg=None) -> EnergyExpenditure
hydration(weight_kg, workout_minutes=0) -> Hydration
macros_for(calories, weight_kg, lean_mass_kg, goal, sex,
           somatotype, dietary_pref) -> Macros
cardio_zones(age, resting_hr=60) -> CardioZones
one_rep_max(weight, reps) -> StrengthEstimate
weekly_tonnage(sessions) -> WeeklyTonnage
body_fat_navy(sex, height_cm, neck_cm, waist_cm, hip_cm=None) -> float
body_fat_bmi_method(bmi, age, sex) -> float
body_composition(weight_kg, height_cm, age, sex,
                  bf_pct=None, waist_cm=None, neck_cm=None,
                  hip_cm=None) -> BodyComposition
infer_age_group(age) -> AgeGroup
infer_somatotype(weight_kg, height_cm, age, sex,
                 body_fat_pct=None) -> Somatotype
```

## 8.4 `questionnaires` — intake forms

### `Question`, `Choice`, `QuestionType`
```python
@dataclass
class Question:
    id: str
    prompt: str
    qtype: QuestionType
    required: bool = True
    choices: List[Choice]
    help: str = ""
    min_value: Optional[float]
    max_value: Optional[float]
    units: str

@dataclass
class Choice:
    id: str
    label: str
    score: float = 0.0

class QuestionType(str, Enum):
    SINGLE, MULTI, INT, FLOAT, TEXT, BOOL
```

### Form lists
```python
PAR_Q          # 7 items
HEALTH_HISTORY # 8 items
LIFESTYLE      # 7 items
DIETARY        # 6 items
FITNESS_HISTORY # 7 items
GOALS          # 7 items
FULL_INTAKE    # [(name, form_list), ...]
```

### Scoring & reporting
```python
parq_score(answers) -> float                       # 0.0-15.5
intake_report(answers) -> IntakeReport

@dataclass
class IntakeReport:
    parq_score: float
    parq_clear: bool
    warnings: List[str]
    notes: List[str]
```

## 8.5 `decision_trees` — recommendation logic

```python
training_split(goal, experience, health) -> TrainingSplit
weekly_volume(goal, experience, days_per_week, age_group) -> WeeklyVolume
intensity_scheme(goal, experience, health) -> IntensityScheme
exercise_selection(goal, environment, equipment, health, age_group) -> ExerciseRule
periodisation(goal, experience) -> Periodisation
session_density(goal, session) -> SessionDensity
progression_rule(goal, experience, health) -> ProgressionRule
macro_overrides(health) -> Dict[str, str]
cuisine_pick(prefs, diet) -> List[str]
supplement_stack(goal, sex, health) -> SupplementStack
```

## 8.6 `meal_plans` — meal library

```python
MEAL_LIBRARY: List[MealItem]      # 40+ meals
by_cuisine(cuisine) -> List[MealItem]
by_diet(diet) -> List[MealItem]
by_slot(slot) -> List[MealItem]
filter_compatible(diet, allergens) -> List[MealItem]
assemble_day(cuisine, diet, target_calories,
             meals_per_day=3, allergens=None) -> MealPlan
assemble_week(cuisine, diet, target_calories,
              meals_per_day=3, allergens=None,
              days=7, secondary_cuisines=None) -> List[MealPlan]
```

The `assemble_week` function rotates through compatible meals across
multiple days, cycling through secondary cuisines when the primary
is exhausted, to maximise variety while staying close to the calorie
target.

```python
@dataclass
class MealItem:
    name: str
    cuisine: str
    slot: str
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fibre_g: float
    tags: List[str]
    ingredients: List[str]
    recipe: str

@dataclass
class MealPlan:
    name: str
    cuisine: str
    diet: DietaryPreference
    meals: List[MealItem]
    notes: List[str]
```

## 8.7 `exercise_plans` — exercise library

```python
EXERCISE_LIBRARY: Dict[str, Exercise]   # 38+ exercises
list_by_pattern(pattern) -> List[Exercise]
list_by_muscle(muscle) -> List[Exercise]
pick_exercise(pattern, environment, equipment, difficulty_max=4) -> Exercise
build_session(goal, environment, equipment, health, session_minutes,
              difficulty_max=4, patterns=None) -> List[Exercise]
weekly_split(goal, experience, days_per_week, environment,
             equipment, health) -> Dict[str, List[Exercise]]
```

```python
@dataclass
class Exercise:
    name: str
    pattern: str
    primary_muscle: str
    secondary_muscles: List[str]
    equipment: List[str]
    difficulty: int
    regression: Optional[str]
    progression: Optional[str]
    cues: List[str]
    contraindications: List[str]
    tags: List[str]
```

## 8.8 `recommender` — orchestrator

### `ClientProfile`
```python
@dataclass
class ClientProfile:
    age: int
    sex: Sex
    height_cm: float
    weight_kg: float
    body_fat_pct: Optional[float]
    waist_cm: Optional[float]
    neck_cm: Optional[float]
    hip_cm: Optional[float]
    resting_hr: int = 60
    activity: ActivityLevel = MODERATE
    sleep_hours: float = 7.5
    stress_level: int = 5
    health_conditions: List[HealthCondition] = []
    medications: str = ""
    injuries: str = ""
    parq_answers: Dict[str, str] = {}
    dietary_preference: DietaryPreference = OMNIVORE
    allergies: List[str] = []
    dislikes: List[str] = []
    meals_per_day: int = 3
    cooking_skill: CookingSkill = INTERMEDIATE
    preferred_cuisines: List[str] = []
    experience: ExperienceLevel = BEGINNER
    environment: TrainingEnvironment = GYM_COMMERCIAL
    equipment: List[str] = []
    days_per_week: int = 4
    session_length: SessionLength = STANDARD_60
    primary_goal: GoalArchetype = GENERAL_HEALTH
    secondary_goals: List[GoalArchetype] = []
    target_weight_kg: Optional[float] = None
    timeline_weeks: int = 12

    def to_dict(self) -> Dict
    @classmethod
    def from_dict(cls, d: Dict) -> "ClientProfile"
```

### `PlanRecommendation`
```python
@dataclass
class PlanRecommendation:
    profile: Dict[str, Any]
    archetype_signature: str
    archetype_summary: Dict[str, Any]
    body_composition: BodyComposition
    energy: EnergyExpenditure
    training: TrainingPlan
    nutrition: NutritionPlan
    intake_report: IntakeReport
    warnings: List[str]
    notes: List[str]

@dataclass
class TrainingPlan:
    split: TrainingSplit
    weekly_volume: WeeklyVolume
    intensity: IntensityScheme
    periodisation: Periodisation
    density: SessionDensity
    exercise_rule: dict
    progression: ProgressionRule
    weekly_schedule: Dict[str, List[dict]]
    cardio_zones: CardioZones
    cardio_prescription: Dict[str, str]
    warmup_protocol: List[str]
    cooldown_protocol: List[str]

@dataclass
class NutritionPlan:
    calories: float
    macros: Macros
    hydration: Hydration
    meal_plan: MealPlan
    cuisine: List[str]
    overrides: Dict[str, str]
    supplements: dict
```

### `Recommender`
```python
class Recommender:
    def __init__(self, profile: ClientProfile): ...
    def recommend(self) -> PlanRecommendation: ...
```

## 8.9 Usage examples

### Minimal
```python
from fitness_engine import ClientProfile, Recommender, Sex
p = ClientProfile(age=30, sex=Sex.FEMALE, height_cm=165, weight_kg=60)
rec = Recommender(p).recommend()
```

### From JSON
```python
import json
data = json.load(open("client.json"))
p = ClientProfile.from_dict(data)
rec = Recommender(p).recommend()
```

### Round-trip to JSON
```python
rec.energy.calorie_target_breakdown
# {'tdee': 1726.8, 'mode': 'fat_loss', 'deficit_pct': 0.2, 'target': 1381.4}

# rec itself is a dataclass; use dataclasses.asdict for full dump:
import dataclasses, json
json.dumps(dataclasses.asdict(rec), default=str)
```

### Override a decision tree
```python
import fitness_engine.decision_trees as dt
def my_split(goal, experience, health):
    return dt.TrainingSplit(0.5, 0.3, 0.1, 0.1)
dt.training_split = my_split
```

### Build a custom meal plan
```python
from fitness_engine.meal_plans import assemble_day, MealItem, MEAL_LIBRARY
plan = assemble_day("indian", DietaryPreference.VEGETARIAN,
                    target_calories=1800, meals_per_day=4)
for m in plan.meals:
    print(m.slot, m.name, m.calories)
```

### Render HTML
```python
from examples.render_html import render
html = render(rec, "Sara Martinez")
open("plan.html", "w").write(html)
```
