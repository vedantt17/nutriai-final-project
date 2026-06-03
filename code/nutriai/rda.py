from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


NUTRIENT_COLUMNS = [
    "calories",
    "protein_g",
    "carbs_g",
    "fat_g",
    "fiber_g",
    "iron_mg",
    "calcium_mg",
    "vitamin_b12_mcg",
    "vitamin_d_mcg",
    "zinc_mg",
    "potassium_mg",
    "magnesium_mg",
    "sodium_mg",
    "omega3_g",
]

RDA_NUTRIENTS = [
    "protein_g",
    "fiber_g",
    "iron_mg",
    "calcium_mg",
    "vitamin_b12_mcg",
    "vitamin_d_mcg",
    "zinc_mg",
    "potassium_mg",
    "magnesium_mg",
]

DISPLAY_NAMES = {
    "calories": "Calories",
    "protein_g": "Protein",
    "carbs_g": "Carbs",
    "fat_g": "Fat",
    "fiber_g": "Fiber",
    "iron_mg": "Iron",
    "calcium_mg": "Calcium",
    "vitamin_b12_mcg": "Vitamin B12",
    "vitamin_d_mcg": "Vitamin D",
    "zinc_mg": "Zinc",
    "potassium_mg": "Potassium",
    "magnesium_mg": "Magnesium",
    "sodium_mg": "Sodium",
    "omega3_g": "Omega-3",
}


def load_rda(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def select_rda(rda_df: pd.DataFrame, age: int, sex: str, calorie_target: int) -> dict[str, float]:
    sex = (sex or "female").lower()
    candidates = rda_df[
        (rda_df["sex"].str.lower() == sex)
        & (rda_df["age_min"] <= age)
        & (rda_df["age_max"] >= age)
    ]
    if candidates.empty:
        candidates = rda_df[
            (rda_df["sex"].str.lower() == "female")
            & (rda_df["age_min"] <= age)
            & (rda_df["age_max"] >= age)
        ]
    if candidates.empty:
        candidates = rda_df.iloc[[0]]
    row = candidates.iloc[0].to_dict()
    result = {nutrient: float(row.get(nutrient, 0.0)) for nutrient in RDA_NUTRIENTS}
    result["calories"] = float(calorie_target)
    result["sodium_mg"] = float(row.get("sodium_mg", 2300.0))
    result["omega3_g"] = float(row.get("omega3_g", 1.1 if sex == "female" else 1.6))
    return result


def compare_to_rda(totals: dict[str, float], rda: dict[str, float]) -> dict[str, dict[str, Any]]:
    comparison: dict[str, dict[str, Any]] = {}
    for nutrient, target in rda.items():
        if target <= 0:
            continue
        actual = float(totals.get(nutrient, 0.0))
        ratio = actual / target
        if nutrient == "sodium_mg":
            passes = actual <= target
            target_type = "cap"
        elif nutrient == "calories":
            passes = 0.85 <= ratio <= 1.15
            target_type = "range"
        else:
            passes = ratio >= 0.8
            target_type = "minimum"
        comparison[nutrient] = {
            "name": DISPLAY_NAMES.get(nutrient, nutrient),
            "actual": round(actual, 2),
            "target": round(float(target), 2),
            "percent": round(ratio * 100, 1),
            "passes_80pct": passes,
            "target_type": target_type,
        }
    return comparison
