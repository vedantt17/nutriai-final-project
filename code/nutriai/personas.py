from __future__ import annotations

from .models import UserProfile


REQUIRED_PERSONAS = [
    UserProfile(
        name="Priya",
        age=27,
        sex="female",
        calorie_target=1800,
        diet_mode="vegetarian",
        allergies=("lactose",),
        conditions=("IBS",),
        micro_priorities=("iron", "calcium", "vitamin d"),
        meal_preferences=("low fodmap", "egg", "tofu", "rice"),
    ),
    UserProfile(
        name="Ravi",
        age=31,
        sex="male",
        calorie_target=2200,
        diet_mode="non-vegetarian",
        allergies=("gluten",),
        conditions=("GERD",),
        cultural_constraints=("no pork",),
        micro_priorities=("vitamin b12", "zinc", "magnesium"),
        meal_preferences=("fish", "chicken", "rice", "low acid"),
    ),
    UserProfile(
        name="Mei",
        age=35,
        sex="female",
        calorie_target=1600,
        diet_mode="vegan",
        allergies=("tree nuts",),
        conditions=("type 2 diabetes",),
        micro_priorities=("vitamin b12", "iron", "zinc", "omega-3"),
        meal_preferences=("low glycemic", "quinoa", "lentils", "fortified"),
    ),
    UserProfile(
        name="James",
        age=42,
        sex="male",
        calorie_target=2000,
        diet_mode="pescatarian",
        allergies=("soy",),
        conditions=("hypertension",),
        micro_priorities=("potassium", "magnesium", "omega-3"),
        meal_preferences=("fish", "low sodium", "DASH", "vegetables"),
    ),
]


def persona_by_name(name: str) -> UserProfile | None:
    lookup = {profile.name.lower(): profile for profile in REQUIRED_PERSONAS}
    return lookup.get(name.lower())
