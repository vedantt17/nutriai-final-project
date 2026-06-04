from __future__ import annotations

import math
import time
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .embedding import HashingEmbedder
from .models import DailyPlan, MealSelection, PlanResult, UserProfile
from .rda import NUTRIENT_COLUMNS, RDA_NUTRIENTS, compare_to_rda, load_rda, select_rda
from .rules import build_allergen_bloom, evaluate_row, explain_exclusions, load_condition_rules, normalize


BOOL_COLUMNS = [
    "vegetarian",
    "vegan",
    "pescatarian",
    "contains_dairy",
    "contains_gluten",
    "contains_tree_nuts",
    "contains_peanuts",
    "contains_shellfish",
    "contains_soy",
    "contains_sesame",
    "contains_eggs",
    "contains_pork",
    "contains_beef",
    "contains_meat",
    "contains_fish",
    "contains_honey",
]

MEAL_CALORIE_SPLIT = {
    "Breakfast": 0.25,
    "Lunch": 0.35,
    "Dinner": 0.40,
}

MICRO_MAP = {
    "iron": "iron_mg",
    "calcium": "calcium_mg",
    "vitamin b12": "vitamin_b12_mcg",
    "b12": "vitamin_b12_mcg",
    "vitamin d": "vitamin_d_mcg",
    "zinc": "zinc_mg",
    "potassium": "potassium_mg",
    "magnesium": "magnesium_mg",
    "omega 3": "omega3_g",
    "omega-3": "omega3_g",
    "fiber": "fiber_g",
}


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


class NutriAIPlanner:
    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path(__file__).resolve().parents[2]
        self.data_dir = self.project_root / "data"
        self.foods = self._load_foods()
        self.rda_df = load_rda(self.data_dir / "rda_reference.csv")
        self.clinical_rules = load_condition_rules(self.data_dir / "clinical_rules.json")
        self.embedder = HashingEmbedder(dimensions=160)
        self.search_text = self.foods.apply(self._row_search_text, axis=1).tolist()
        index_start = time.perf_counter()
        self.embedding_matrix = self.embedder.encode_many(self.search_text)
        self.index_build_seconds = time.perf_counter() - index_start

    def _load_foods(self) -> pd.DataFrame:
        path = self.data_dir / "food_database.csv"
        if not path.exists():
            raise FileNotFoundError(f"Missing {path}. Run scripts/build_offline_dataset.py first.")
        foods = pd.read_csv(path)
        for column in BOOL_COLUMNS:
            if column in foods.columns:
                foods[column] = foods[column].map(_as_bool)
        for column in NUTRIENT_COLUMNS + ["glycemic_index"]:
            foods[column] = pd.to_numeric(foods[column], errors="coerce").fillna(0.0)
        return foods

    @staticmethod
    def _row_search_text(row: pd.Series) -> str:
        fields = [
            row.get("meal_name", ""),
            row.get("base_name", ""),
            row.get("meal_type", ""),
            row.get("category", ""),
            row.get("cuisine", ""),
            row.get("ingredients", ""),
            row.get("variant_addons", ""),
            row.get("allergens", ""),
            row.get("condition_flags", ""),
            row.get("fodmap_level", ""),
            row.get("acidity_level", ""),
        ]
        return " ".join(str(field) for field in fields if str(field).strip())

    def _safe_candidates(self, profile: UserProfile) -> tuple[pd.DataFrame, dict[str, Any]]:
        start = time.perf_counter()
        bloom = build_allergen_bloom(profile)
        safe_indices: list[int] = []
        exclusion_reasons: dict[str, list[str]] = {}
        for index, row in self.foods.iterrows():
            reasons = evaluate_row(row, profile, bloom)
            if reasons:
                exclusion_reasons[str(row.get("food_id"))] = reasons
            else:
                safe_indices.append(index)
        elapsed = time.perf_counter() - start
        safe = self.foods.loc[safe_indices].copy()
        benchmark = {
            "safe_filter_seconds": round(elapsed, 4),
            "total_records": int(len(self.foods)),
            "safe_records": int(len(safe)),
            "excluded_records": int(len(self.foods) - len(safe)),
            "bloom_filter_hashes": bloom.hash_count,
            "bloom_filter_bits": bloom.size,
        }
        return safe, benchmark

    def _attach_embedding_scores(self, safe: pd.DataFrame, profile: UserProfile) -> tuple[pd.DataFrame, dict[str, Any]]:
        start = time.perf_counter()
        if safe.empty:
            raise ValueError("No clinically safe meal candidates remain after filtering.")
        matrix = self.embedding_matrix[safe.index.to_numpy()]
        similarity = self.embedder.similarity(profile.query_text, matrix)
        safe = safe.copy()
        safe["embedding_score"] = similarity
        min_score = float(np.min(similarity)) if len(similarity) else 0.0
        max_score = float(np.max(similarity)) if len(similarity) else 1.0
        spread = max(max_score - min_score, 1e-9)
        safe["embedding_norm"] = (safe["embedding_score"] - min_score) / spread
        benchmark = {
            "embedding_seconds": round(time.perf_counter() - start, 4),
            "embedding_dimensions": self.embedder.dimensions,
            "index_build_seconds": round(self.index_build_seconds, 4),
            "candidate_vectors_scored": int(len(safe)),
        }
        return safe, benchmark

    @staticmethod
    def _priority_columns(profile: UserProfile) -> list[str]:
        columns = []
        for priority in profile.micro_priorities:
            column = MICRO_MAP.get(normalize(priority))
            if column:
                columns.append(column)
        if not columns:
            columns = ["protein_g", "fiber_g", "iron_mg", "calcium_mg", "vitamin_b12_mcg", "vitamin_d_mcg", "zinc_mg"]
        return list(dict.fromkeys(columns))

    def _micro_score(self, row: pd.Series, profile: UserProfile, rda: dict[str, float]) -> float:
        columns = self._priority_columns(profile)
        scores = []
        for column in columns:
            target = max(float(rda.get(column, 1.0)) / 3.0, 0.1)
            scores.append(min(float(row.get(column, 0.0)) / target, 1.35))
        return float(np.mean(scores)) if scores else 0.0

    @staticmethod
    def _condition_score(row: pd.Series, profile: UserProfile) -> float:
        conditions = {normalize(item) for item in profile.conditions}
        score = 0.55
        gi = float(row.get("glycemic_index", 45))
        sodium = float(row.get("sodium_mg", 0))
        if {"ibs", "ibs d", "irritable bowel syndrome"} & conditions:
            score += 0.15 if normalize(row.get("fodmap_level")) == "low" else 0.04
        if {"gerd", "acid reflux", "acidity"} & conditions:
            score += 0.15 if normalize(row.get("acidity_level")) == "low" else 0.03
        if {"type 2 diabetes", "diabetes", "t2d"} & conditions:
            score += max(0.0, (55.0 - gi) / 55.0) * 0.28
            score += min(float(row.get("fiber_g", 0)) / 18.0, 1.0) * 0.08
        if {"hypertension", "high blood pressure"} & conditions:
            score += max(0.0, (760.0 - sodium) / 760.0) * 0.22
            score += min(float(row.get("potassium_mg", 0)) / 1200.0, 1.0) * 0.08
            score += min(float(row.get("magnesium_mg", 0)) / 180.0, 1.0) * 0.05
        return min(score, 1.2)

    def _score_row(
        self,
        row: pd.Series,
        profile: UserProfile,
        rda: dict[str, float],
        target_calories: float,
        category_counts: Counter,
        cuisine_counts: Counter,
        base_counts: Counter,
    ) -> tuple[float, str]:
        calories = float(row.get("calories", 0.0))
        calorie_score = 1.0 - min(abs(calories - target_calories) / max(target_calories, 1.0), 1.0)
        embedding_score = float(row.get("embedding_norm", 0.0))
        micro_score = self._micro_score(row, profile, rda)
        condition_score = self._condition_score(row, profile)

        category_penalty = min(category_counts[row.get("category", "")] * 0.08, 0.24)
        cuisine_penalty = min(cuisine_counts[row.get("cuisine", "")] * 0.04, 0.16)
        base_penalty = min(base_counts[row.get("base_name", "")] * 0.10, 0.28)
        diversity_score = max(0.0, 1.0 - category_penalty - cuisine_penalty - base_penalty)

        score = (
            calorie_score * 0.32
            + embedding_score * 0.21
            + min(micro_score, 1.2) * 0.22
            + condition_score * 0.17
            + diversity_score * 0.08
        )
        reason = (
            f"calorie fit {calorie_score:.2f}, nutrient fit {min(micro_score, 1.2):.2f}, "
            f"clinical fit {condition_score:.2f}, similarity {embedding_score:.2f}, diversity {diversity_score:.2f}"
        )
        return score, reason

    def _choose_meal(
        self,
        candidates: pd.DataFrame,
        meal_type: str,
        profile: UserProfile,
        rda: dict[str, float],
        target_calories: float,
        used_food_ids: set[str],
        used_base_names: set[str],
        category_counts: Counter,
        cuisine_counts: Counter,
        base_counts: Counter,
    ) -> tuple[pd.Series, float, str]:
        pool = candidates[
            (candidates["meal_type"] == meal_type)
            & (~candidates["food_id"].isin(used_food_ids))
            & (~candidates["base_name"].isin(used_base_names))
        ]
        if pool.empty:
            pool = candidates[(candidates["meal_type"] == meal_type) & (~candidates["food_id"].isin(used_food_ids))]
        if pool.empty:
            pool = candidates[(~candidates["food_id"].isin(used_food_ids)) & (~candidates["base_name"].isin(used_base_names))]
        if pool.empty:
            pool = candidates[~candidates["food_id"].isin(used_food_ids)]
        if pool.empty:
            raise ValueError(f"No unused safe meals available for {meal_type}.")

        scored: list[tuple[float, int, str]] = []
        for index, row in pool.iterrows():
            score, reason = self._score_row(row, profile, rda, target_calories, category_counts, cuisine_counts, base_counts)
            scored.append((score, index, reason))
        scored.sort(key=lambda item: item[0], reverse=True)

        best_score, best_index, best_reason = scored[0]
        best_base = pool.loc[best_index].get("base_name", "")
        if base_counts[best_base] > 0:
            threshold = best_score * 0.94
            for score, index, reason in scored[:80]:
                base = pool.loc[index].get("base_name", "")
                if base_counts[base] == 0 and score >= threshold:
                    best_score, best_index, best_reason = score, index, reason
                    break
        return pool.loc[best_index], best_score, best_reason

    @staticmethod
    def _scaled_nutrients(row: pd.Series, multiplier: float) -> dict[str, float]:
        return {column: round(float(row.get(column, 0.0)) * multiplier, 3) for column in NUTRIENT_COLUMNS}

    @staticmethod
    def _sum_nutrients(meals: list[MealSelection]) -> dict[str, float]:
        totals = {column: 0.0 for column in NUTRIENT_COLUMNS}
        for meal in meals:
            for column in NUTRIENT_COLUMNS:
                totals[column] += float(meal.nutrients.get(column, 0.0))
        return {column: round(value, 2) for column, value in totals.items()}

    @staticmethod
    def _warning_lines(comparison: dict[str, dict[str, Any]], profile: UserProfile) -> list[str]:
        warnings = []
        priority_columns = {MICRO_MAP.get(normalize(item)) for item in profile.micro_priorities}
        priority_columns.discard(None)
        conditions = {normalize(item) for item in profile.conditions}
        sodium_is_clinical = bool({"hypertension", "high blood pressure"} & conditions)
        for nutrient, data in comparison.items():
            if nutrient == "sodium_mg":
                if sodium_is_clinical and not data["passes_80pct"]:
                    warnings.append(f"Sodium exceeds cap: {data['actual']} mg vs {data['target']} mg.")
            elif nutrient == "calories":
                if not data["passes_80pct"]:
                    warnings.append(f"Calories outside +/-15% target: {data['actual']} vs {data['target']}.")
            elif (nutrient in priority_columns or not priority_columns) and not data["passes_80pct"]:
                warnings.append(f"{data['name']} below 80% threshold: {data['percent']}%.")
        return warnings

    @staticmethod
    def _diversity_score(meals: list[MealSelection]) -> float:
        if not meals:
            return 0.0
        unique_meals = len({meal.base_name for meal in meals}) / len(meals)
        unique_categories = len({meal.category for meal in meals}) / min(10, len(meals))
        unique_cuisines = len({meal.cuisine for meal in meals}) / min(8, len(meals))
        meal_type_balance = len({meal.meal_type for meal in meals}) / 3.0
        score = (unique_meals * 0.50 + min(unique_categories, 1.0) * 0.22 + min(unique_cuisines, 1.0) * 0.18 + meal_type_balance * 0.10) * 100
        return round(score, 1)

    def _capability_checks(self, result: PlanResult, profile: UserProfile) -> list[dict[str, Any]]:
        meals = result.all_meals
        safety_violations = []
        bloom = build_allergen_bloom(profile)
        selected_rows = self.foods[self.foods["food_id"].isin({meal.food_id for meal in meals})]
        for _, row in selected_rows.iterrows():
            reasons = evaluate_row(row, profile, bloom)
            if reasons:
                safety_violations.append({"meal_name": row.get("meal_name"), "reasons": reasons})

        repeated = len({meal.food_id for meal in meals}) != len(meals)
        repeated_base = len({meal.base_name for meal in meals}) != len(meals)
        daily_computed = all(day.totals and day.rda_comparison for day in result.days)
        calorie_pass = all(day.rda_comparison.get("calories", {}).get("passes_80pct", False) for day in result.days)
        conditions = {normalize(item) for item in profile.conditions}
        sodium_required = bool({"hypertension", "high blood pressure"} & conditions)
        sodium_ok = True
        if sodium_required:
            sodium_ok = all(day.rda_comparison.get("sodium_mg", {}).get("passes_80pct", True) for day in result.days)

        checks = [
            {
                "capability": "Clinical Condition Filtering",
                "status": "PASS" if not safety_violations else "FAIL",
                "evidence": f"{len(selected_rows)} selected meals rechecked against condition rules; {len(safety_violations)} violations.",
            },
            {
                "capability": "Allergy Detection & Exclusion",
                "status": "PASS" if not safety_violations else "FAIL",
                "evidence": "Bloom pre-screen plus exact allergen/cross-contamination exclusion used before ranking.",
            },
            {
                "capability": "Dietary Preference Handling",
                "status": "PASS" if not safety_violations else "FAIL",
                "evidence": f"Generated for {profile.diet_mode}; cultural constraints: {', '.join(profile.cultural_constraints) or 'none'}.",
            },
            {
                "capability": "Diversity Engine",
                "status": "PASS" if not repeated and not repeated_base and result.diversity_score >= 85 else "REVIEW",
                "evidence": f"Diversity score {result.diversity_score}/100; no repeated meal IDs: {not repeated}; no repeated base dishes: {not repeated_base}.",
            },
            {
                "capability": "Macro & Micronutrient Analysis",
                "status": "PASS" if daily_computed and calorie_pass and sodium_ok else "REVIEW",
                "evidence": "Daily macro/micro totals computed and compared to RDA/AI references; low nutrients are explicitly flagged.",
            },
            {
                "capability": "Sub-60-Second Generation",
                "status": "PASS" if result.generation_time_sec < 60 else "FAIL",
                "evidence": f"Generation completed in {result.generation_time_sec:.3f} seconds over {len(self.foods)} offline records.",
            },
        ]
        return checks

    def generate_plan(self, profile: UserProfile) -> PlanResult:
        profile = profile.normalized()
        total_start = time.perf_counter()
        rda = select_rda(self.rda_df, profile.age, profile.sex, profile.calorie_target)
        if {"hypertension", "high blood pressure"} & {normalize(item) for item in profile.conditions}:
            rda["sodium_mg"] = min(rda.get("sodium_mg", 2300.0), 2300.0)

        safe, safety_benchmark = self._safe_candidates(profile)
        safe, embedding_benchmark = self._attach_embedding_scores(safe, profile)

        used_food_ids: set[str] = set()
        used_base_names: set[str] = set()
        category_counts: Counter = Counter()
        cuisine_counts: Counter = Counter()
        base_counts: Counter = Counter()
        days: list[DailyPlan] = []
        ranking_seconds = 0.0

        for day_number in range(1, 8):
            day_meals: list[MealSelection] = []
            selected_rows: list[tuple[pd.Series, float, str]] = []
            for meal_type, split in MEAL_CALORIE_SPLIT.items():
                target_calories = profile.calorie_target * split
                rank_start = time.perf_counter()
                row, score, reason = self._choose_meal(
                    safe,
                    meal_type,
                    profile,
                    rda,
                    target_calories,
                    used_food_ids,
                    used_base_names,
                    category_counts,
                    cuisine_counts,
                    base_counts,
                )
                ranking_seconds += time.perf_counter() - rank_start
                selected_rows.append((row, score, reason))
                used_food_ids.add(str(row["food_id"]))
                used_base_names.add(str(row.get("base_name", "")))
                category_counts[str(row.get("category", ""))] += 1
                cuisine_counts[str(row.get("cuisine", ""))] += 1
                base_counts[str(row.get("base_name", ""))] += 1

            raw_day_calories = sum(float(row.get("calories", 0.0)) for row, _, _ in selected_rows)
            day_multiplier = profile.calorie_target / max(raw_day_calories, 1.0)
            day_multiplier = min(max(day_multiplier, 0.76), 1.24)
            for row, score, reason in selected_rows:
                nutrients = self._scaled_nutrients(row, day_multiplier)
                day_meals.append(
                    MealSelection(
                        day=day_number,
                        meal_type=str(row["meal_type"]),
                        food_id=str(row["food_id"]),
                        base_name=str(row.get("base_name", row["meal_name"])),
                        meal_name=str(row["meal_name"]),
                        category=str(row["category"]),
                        cuisine=str(row["cuisine"]),
                        serving_multiplier=round(day_multiplier, 2),
                        score=round(float(score), 4),
                        why_selected=reason,
                        nutrients=nutrients,
                        ingredients=str(row.get("ingredients", "")),
                        nutrition_source=str(row.get("nutrition_source", "")),
                        nutrition_source_ids=str(row.get("nutrition_source_ids", "")),
                        clinical_rule_sources=str(row.get("clinical_rule_sources", "")),
                        source_rule_matches=str(row.get("source_rule_matches", "")),
                    )
                )
            totals = self._sum_nutrients(day_meals)
            comparison = compare_to_rda(totals, rda)
            warnings = self._warning_lines(comparison, profile)
            days.append(DailyPlan(day=day_number, meals=day_meals, totals=totals, rda_comparison=comparison, warnings=warnings))

        generation_time = time.perf_counter() - total_start
        all_meals = [meal for day in days for meal in day.meals]
        diversity_score = self._diversity_score(all_meals)
        notes = [
            "Educational demo only; not medical advice.",
            "Allergen and clinical exclusions are hard filters before ranking.",
        ]
        if normalize(profile.diet_mode) == "vegan":
            notes.append("Vegan profiles include fortified foods where possible; real users should confirm B12 and vitamin D with a clinician.")

        result = PlanResult(
            profile=profile,
            days=days,
            excluded_examples=explain_exclusions(self.foods, profile, max_rows=35),
            capability_checks=[],
            diversity_score=diversity_score,
            generation_time_sec=round(generation_time, 4),
            benchmarks={
                **safety_benchmark,
                **embedding_benchmark,
                "ranking_seconds": round(ranking_seconds, 4),
                "total_generation_seconds": round(generation_time, 4),
                "techniques": ["Bloom filter allergen sketching", "Dense hashed embeddings", "Multi-stage recommendation ranking"],
            },
            notes=notes,
        )
        result.capability_checks = self._capability_checks(result, profile)
        return result


def plan_to_rows(result: PlanResult) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for day in result.days:
        for meal in day.meals:
            row = {
                "day": day.day,
                "meal_type": meal.meal_type,
                "base_name": meal.base_name,
                "meal_name": meal.meal_name,
                "serving_multiplier": meal.serving_multiplier,
                "score": meal.score,
                "why_selected": meal.why_selected,
                "ingredients": meal.ingredients,
                "nutrition_source": getattr(meal, "nutrition_source", ""),
                "nutrition_source_ids": getattr(meal, "nutrition_source_ids", ""),
                "clinical_rule_sources": getattr(meal, "clinical_rule_sources", ""),
                "source_rule_matches": getattr(meal, "source_rule_matches", ""),
            }
            row.update(meal.nutrients)
            rows.append(row)
    return rows


def daily_totals_to_rows(result: PlanResult) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for day in result.days:
        row = {"day": day.day}
        row.update(day.totals)
        rows.append(row)
    return rows
