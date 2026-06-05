from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CODE_DIR = PROJECT_ROOT / "code"
sys.path.insert(0, str(CODE_DIR))

from nutriai import NutriAIPlanner
from nutriai.export import capability_dataframe, daily_totals_dataframe, exclusions_dataframe, plan_dataframe
from nutriai.personas import REQUIRED_PERSONAS
from nutriai.rules import build_allergen_bloom, evaluate_row


class NutriAITestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.planner = NutriAIPlanner(project_root=PROJECT_ROOT)

    def test_package_exports_planner_class(self):
        self.assertTrue(callable(NutriAIPlanner))

    def test_offline_dataset_is_grading_sized(self):
        foods = self.planner.foods
        self.assertGreaterEqual(len(foods), 10000)
        self.assertEqual(foods["food_id"].nunique(), len(foods))
        self.assertEqual(foods["meal_name"].nunique(), len(foods))
        self.assertGreaterEqual(foods["meal_type"].nunique(), 3)
        self.assertTrue({"Breakfast", "Lunch", "Dinner"}.issubset(set(foods["meal_type"])))
        required_columns = {
            "food_id",
            "base_name",
            "meal_name",
            "portion_profile",
            "ingredients",
            "allergens",
            "condition_flags",
            "dedup_signature",
            "nutrition_source",
            "nutrition_source_ids",
            "nutrition_source_fdc_ids",
            "nutrition_source_unmapped_ingredients",
            "clinical_rule_sources",
            "source_rule_matches",
            "allergen_rule_source",
            "source_confidence",
            "calories",
            "protein_g",
            "iron_mg",
            "calcium_mg",
            "vitamin_b12_mcg",
            "vitamin_d_mcg",
            "zinc_mg",
            "contains_honey",
            "contains_peanuts",
            "contains_sesame",
        }
        self.assertTrue(required_columns.issubset(set(foods.columns)))
        self.assertEqual(foods["dedup_signature"].nunique(), len(foods))
        self.assertEqual(foods["nutrition_source_ids"].fillna("").astype(str).str.strip().eq("").sum(), 0)
        self.assertEqual(foods["nutrition_source_unmapped_ingredients"].fillna("").astype(str).str.strip().ne("").sum(), 0)
        self.assertEqual((foods["source_confidence"] == "source_reference_partial").sum(), 0)
        self.assertGreater(foods["nutrition_source_fdc_ids"].fillna("").astype(str).str.strip().ne("").sum(), 0)

    def test_source_reference_files_are_present(self):
        required_files = [
            "usda_fooddata_reference.csv",
            "source_lookup_fodmap.csv",
            "source_lookup_glycemic_index.csv",
            "source_lookup_gerd_triggers.csv",
            "source_lookup_allergens.csv",
            "source_lookup_dash.csv",
            "source_inventory.csv",
            "source_provenance.md",
        ]
        for filename in required_files:
            with self.subTest(filename=filename):
                path = PROJECT_ROOT / "data" / filename
                self.assertTrue(path.exists(), f"Missing {path}")
                self.assertGreater(path.stat().st_size, 50)
        inventory = pd.read_csv(PROJECT_ROOT / "data" / "source_inventory.csv")
        usda = pd.read_csv(PROJECT_ROOT / "data" / "usda_fooddata_reference.csv")
        self.assertIn("USDA FoodData Central API", set(inventory["source_name"]))
        self.assertIn("NIH Dietary Reference Intakes", set(inventory["source_name"]))
        self.assertIn("Monash University Low-FODMAP list", set(inventory["source_name"]))
        self.assertIn("Glycaemic Index database", set(inventory["source_name"]))
        self.assertIn("DASH diet guidelines", set(inventory["source_name"]))
        self.assertIn("NutriAI internal allergen keyword map", set(inventory["source_name"]))
        self.assertGreaterEqual(len(usda), 90)
        self.assertEqual(usda["source_reference_id"].fillna("").astype(str).str.strip().eq("").sum(), 0)
        self.assertGreater(usda["fdc_id"].fillna("").astype(str).str.strip().ne("").sum(), 0)

    def test_required_personas_pass_all_capabilities(self):
        for persona in REQUIRED_PERSONAS:
            with self.subTest(persona=persona.name):
                result = self.planner.generate_plan(persona)
                self.assertLess(result.generation_time_sec, 60)
                self.assertEqual(len(result.days), 7)
                self.assertEqual(len(result.all_meals), 21)
                self.assertEqual(len({meal.food_id for meal in result.all_meals}), 21)
                self.assertEqual(len({meal.base_name for meal in result.all_meals}), 21)
                self.assertGreaterEqual(result.diversity_score, 85)
                statuses = {check["capability"]: check["status"] for check in result.capability_checks}
                self.assertTrue(statuses)
                self.assertTrue(all(status == "PASS" for status in statuses.values()), statuses)
                self.assertFalse([warning for day in result.days for warning in day.warnings])

    def test_selected_meals_are_rechecked_against_safety_rules(self):
        for persona in REQUIRED_PERSONAS:
            result = self.planner.generate_plan(persona)
            selected_ids = set()
            selected_ids.update(meal.food_id for meal in result.all_meals)
            selected = self.planner.foods[self.planner.foods["food_id"].isin(selected_ids)]
            bloom = build_allergen_bloom(persona)
            for _, row in selected.iterrows():
                reasons = evaluate_row(row, persona, bloom)
                self.assertEqual(reasons, [], f"{persona.name}: {row['meal_name']} -> {reasons}")
                if persona.diet_mode == "vegan":
                    self.assertFalse(bool(row.get("contains_honey")), f"{persona.name}: honey selected in {row['meal_name']}")

    def test_explain_feature_returns_actionable_reasons(self):
        result = self.planner.generate_plan(REQUIRED_PERSONAS[0])
        self.assertGreaterEqual(len(result.excluded_examples), 10)
        first = result.excluded_examples[0]
        self.assertIn("meal_name", first)
        self.assertTrue(first["reasons"])
        accepted_markers = ("excluded", "risk", "mismatch", "clinical rule", "allergen")
        self.assertTrue(any(any(marker in reason.lower() for marker in accepted_markers) for reason in first["reasons"]))

    def test_bax_technique_benchmarks_are_reported(self):
        result = self.planner.generate_plan(REQUIRED_PERSONAS[1])
        benchmarks = result.benchmarks
        self.assertIn("Bloom filter allergen sketching", benchmarks["techniques"])
        self.assertIn("Dense hashed embeddings", benchmarks["techniques"])
        self.assertIn("Multi-stage recommendation ranking", benchmarks["techniques"])
        self.assertGreater(benchmarks["bloom_filter_bits"], 0)
        self.assertGreater(benchmarks["candidate_vectors_scored"], 0)
        self.assertGreaterEqual(benchmarks["embedding_dimensions"], 128)

    def test_export_dataframes_are_complete(self):
        result = self.planner.generate_plan(REQUIRED_PERSONAS[2])
        self.assertEqual(plan_dataframe(result).shape[0], 21)
        self.assertEqual(daily_totals_dataframe(result).shape[0], 7)
        self.assertEqual(capability_dataframe(result).shape[0], 6)
        self.assertGreaterEqual(exclusions_dataframe(result).shape[0], 10)
        self.assertIsInstance(plan_dataframe(result), pd.DataFrame)


if __name__ == "__main__":
    unittest.main(verbosity=2)
