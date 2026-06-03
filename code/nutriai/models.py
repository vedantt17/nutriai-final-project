from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _clean_token(value: str) -> str:
    return value.strip().lower().replace("_", " ").replace("-", " ")


def clean_tuple(values: Any) -> tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, str):
        values = [part for part in values.split(",")]
    cleaned = []
    for value in values:
        token = _clean_token(str(value))
        if token:
            cleaned.append(token)
    return tuple(dict.fromkeys(cleaned))


@dataclass(frozen=True)
class UserProfile:
    name: str = "Demo User"
    age: int = 28
    sex: str = "female"
    calorie_target: int = 1800
    diet_mode: str = "vegetarian"
    allergies: tuple[str, ...] = field(default_factory=tuple)
    conditions: tuple[str, ...] = field(default_factory=tuple)
    cultural_constraints: tuple[str, ...] = field(default_factory=tuple)
    micro_priorities: tuple[str, ...] = field(default_factory=tuple)
    meal_preferences: tuple[str, ...] = field(default_factory=tuple)
    strict_cross_contamination: bool = True

    def normalized(self) -> "UserProfile":
        return UserProfile(
            name=self.name.strip() or "Demo User",
            age=max(2, min(int(self.age), 100)),
            sex=_clean_token(self.sex or "female"),
            calorie_target=max(900, min(int(self.calorie_target), 4200)),
            diet_mode=_clean_token(self.diet_mode or "non vegetarian"),
            allergies=clean_tuple(self.allergies),
            conditions=clean_tuple(self.conditions),
            cultural_constraints=clean_tuple(self.cultural_constraints),
            micro_priorities=clean_tuple(self.micro_priorities),
            meal_preferences=clean_tuple(self.meal_preferences),
            strict_cross_contamination=bool(self.strict_cross_contamination),
        )

    @property
    def query_text(self) -> str:
        parts = [
            self.name,
            f"{self.age} {self.sex}",
            f"{self.calorie_target} calories",
            self.diet_mode,
            " ".join(self.conditions),
            " ".join(self.allergies),
            " ".join(self.micro_priorities),
            " ".join(self.meal_preferences),
            " ".join(self.cultural_constraints),
        ]
        return " ".join(part for part in parts if part).strip()


@dataclass
class MealSelection:
    day: int
    meal_type: str
    food_id: str
    base_name: str
    meal_name: str
    category: str
    cuisine: str
    serving_multiplier: float
    score: float
    why_selected: str
    nutrients: dict[str, float]
    ingredients: str


@dataclass
class DailyPlan:
    day: int
    meals: list[MealSelection]
    totals: dict[str, float]
    rda_comparison: dict[str, dict[str, Any]]
    warnings: list[str]


@dataclass
class PlanResult:
    profile: UserProfile
    days: list[DailyPlan]
    excluded_examples: list[dict[str, Any]]
    capability_checks: list[dict[str, Any]]
    diversity_score: float
    generation_time_sec: float
    benchmarks: dict[str, Any]
    notes: list[str]

    @property
    def all_meals(self) -> list[MealSelection]:
        meals: list[MealSelection] = []
        for day in self.days:
            meals.extend(day.meals)
        return meals
