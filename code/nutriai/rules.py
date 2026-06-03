from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

from .bloom import BloomFilter
from .models import UserProfile


TOKEN_SPLIT_RE = re.compile(r"[,;/|]+")

ALLERGEN_SYNONYMS = {
    "lactose": {"dairy", "lactose", "milk", "cheese", "yogurt"},
    "dairy": {"dairy", "lactose", "milk", "cheese", "yogurt"},
    "gluten": {"gluten", "wheat", "barley", "rye"},
    "celiac": {"gluten", "wheat", "barley", "rye"},
    "tree nuts": {"tree nuts", "almond", "almonds", "cashew", "walnut", "pistachio", "pecan"},
    "nuts": {"tree nuts", "almond", "almonds", "cashew", "walnut", "pistachio", "pecan"},
    "shellfish": {"shellfish", "shrimp", "prawn", "crab", "lobster"},
    "soy": {"soy", "tofu", "tempeh", "edamame", "soy sauce"},
    "eggs": {"egg", "eggs"},
    "egg": {"egg", "eggs"},
    "pork": {"pork", "ham", "bacon"},
}

ALLERGEN_COLUMNS = {
    "dairy": "contains_dairy",
    "lactose": "contains_dairy",
    "milk": "contains_dairy",
    "cheese": "contains_dairy",
    "yogurt": "contains_dairy",
    "gluten": "contains_gluten",
    "wheat": "contains_gluten",
    "barley": "contains_gluten",
    "rye": "contains_gluten",
    "tree nuts": "contains_tree_nuts",
    "almond": "contains_tree_nuts",
    "almonds": "contains_tree_nuts",
    "cashew": "contains_tree_nuts",
    "walnut": "contains_tree_nuts",
    "pistachio": "contains_tree_nuts",
    "pecan": "contains_tree_nuts",
    "shellfish": "contains_shellfish",
    "shrimp": "contains_shellfish",
    "prawn": "contains_shellfish",
    "crab": "contains_shellfish",
    "lobster": "contains_shellfish",
    "soy": "contains_soy",
    "tofu": "contains_soy",
    "tempeh": "contains_soy",
    "edamame": "contains_soy",
    "soy sauce": "contains_soy",
    "egg": "contains_eggs",
    "eggs": "contains_eggs",
    "pork": "contains_pork",
    "ham": "contains_pork",
    "bacon": "contains_pork",
}


def normalize(value: Any) -> str:
    return str(value or "").strip().lower().replace("_", " ").replace("-", " ")


def split_terms(value: Any) -> set[str]:
    if pd.isna(value):
        return set()
    text = normalize(value)
    return {part.strip() for part in TOKEN_SPLIT_RE.split(text) if part.strip()}


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return normalize(value) in {"1", "true", "yes", "y"}


def load_condition_rules(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def expand_allergens(allergies: tuple[str, ...]) -> set[str]:
    expanded: set[str] = set()
    for allergen in allergies:
        token = normalize(allergen)
        expanded.add(token)
        expanded.update(ALLERGEN_SYNONYMS.get(token, set()))
    return {item for item in expanded if item}


def build_allergen_bloom(profile: UserProfile) -> BloomFilter:
    terms = expand_allergens(profile.allergies)
    bloom = BloomFilter(expected_items=max(8, len(terms) * 2))
    for term in terms:
        bloom.add(term)
    return bloom


def row_text_terms(row: pd.Series) -> set[str]:
    terms = set()
    for column in ("ingredients", "allergens", "condition_flags", "cross_contamination_risks"):
        terms.update(split_terms(row.get(column, "")))
    return terms


def evaluate_row(row: pd.Series, profile: UserProfile, allergen_bloom: BloomFilter | None = None) -> list[str]:
    profile = profile.normalized()
    reasons: list[str] = []
    diet = normalize(profile.diet_mode)

    if diet == "vegan" and not bool_value(row.get("vegan")):
        reasons.append("Diet mismatch: vegan profile cannot receive meals with animal-derived ingredients.")
    if diet == "vegan" and bool_value(row.get("contains_honey")):
        reasons.append("Diet mismatch: vegan profile cannot receive honey.")
    elif diet == "vegetarian" and not bool_value(row.get("vegetarian")):
        reasons.append("Diet mismatch: vegetarian profile cannot receive meat, fish, or shellfish.")
    elif diet == "pescatarian" and not bool_value(row.get("pescatarian")):
        reasons.append("Diet mismatch: pescatarian profile can receive fish/seafood but no other meat.")

    constraints = {normalize(item) for item in profile.cultural_constraints}
    if ({"no pork", "halal", "kosher"} & constraints) and bool_value(row.get("contains_pork")):
        reasons.append("Cultural constraint: pork item excluded.")
    if "no beef" in constraints and bool_value(row.get("contains_beef")):
        reasons.append("Cultural constraint: beef item excluded.")
    if "no shellfish" in constraints and bool_value(row.get("contains_shellfish")):
        reasons.append("Cultural constraint: shellfish item excluded.")

    allergen_terms = expand_allergens(profile.allergies)
    row_terms = row_text_terms(row)
    for allergen in sorted(allergen_terms):
        column = ALLERGEN_COLUMNS.get(allergen)
        bloom_hit = allergen_bloom is not None and allergen in allergen_bloom and (
            allergen in row_terms or (column and bool_value(row.get(column)))
        )
        exact_hit = allergen in row_terms or (column and bool_value(row.get(column)))
        if bloom_hit or exact_hit:
            reasons.append(f"Allergen exclusion: {allergen} detected in ingredients or allergen tags.")

    if profile.strict_cross_contamination:
        risks = split_terms(row.get("cross_contamination_risks", ""))
        for allergen in sorted(allergen_terms):
            if allergen in risks:
                reasons.append(f"Cross-contamination risk: possible {allergen} exposure.")

    conditions = {normalize(item) for item in profile.conditions}
    flags = split_terms(row.get("condition_flags", ""))
    fodmap_level = normalize(row.get("fodmap_level", "low"))
    acidity_level = normalize(row.get("acidity_level", "low"))
    gi = float(row.get("glycemic_index", 0) or 0)
    sodium = float(row.get("sodium_mg", 0) or 0)

    if {"ibs", "ibs d", "irritable bowel syndrome"} & conditions:
        if fodmap_level == "high" or "high fodmap" in flags:
            reasons.append("Clinical rule: high-FODMAP food excluded for IBS.")
    if {"gerd", "acid reflux", "acidity"} & conditions:
        if acidity_level == "high" or "reflux trigger" in flags:
            reasons.append("Clinical rule: GERD trigger excluded.")
    if {"type 2 diabetes", "diabetes", "t2d"} & conditions:
        if gi > 55 or "high gi" in flags or "added sugar" in flags:
            reasons.append("Clinical rule: high-glycemic food excluded for diabetes.")
    if {"hypertension", "high blood pressure"} & conditions:
        if sodium > 760 or "high sodium" in flags:
            reasons.append("Clinical rule: high-sodium food excluded for hypertension.")

    return list(dict.fromkeys(reasons))


def explain_exclusions(
    foods: pd.DataFrame,
    profile: UserProfile,
    max_rows: int = 30,
) -> list[dict[str, Any]]:
    bloom = build_allergen_bloom(profile)
    examples: list[dict[str, Any]] = []
    for _, row in foods.iterrows():
        reasons = evaluate_row(row, profile, bloom)
        if reasons:
            examples.append(
                {
                    "food_id": row.get("food_id"),
                    "meal_name": row.get("meal_name"),
                    "meal_type": row.get("meal_type"),
                    "reasons": reasons,
                }
            )
        if len(examples) >= max_rows:
            break
    return examples
