from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = PROJECT_ROOT / "code"
sys.path.insert(0, str(CODE_DIR))

from nutriai import NutriAIPlanner
from nutriai.personas import REQUIRED_PERSONAS


def main():
    planner = NutriAIPlanner(project_root=PROJECT_ROOT)
    foods = pd.read_csv(PROJECT_ROOT / "data" / "food_database.csv")
    rows = []
    for persona in REQUIRED_PERSONAS:
        result = planner.generate_plan(persona)
        rows.append(
            {
                "persona": persona.name,
                "generation_time_sec": result.generation_time_sec,
                "diversity_score": result.diversity_score,
                "benchmarks": result.benchmarks,
                "capability_checks": result.capability_checks,
                "daily_warnings": {str(day.day): day.warnings for day in result.days},
            }
        )
    report = {
        "dataset_records": int(len(planner.foods)),
        "deduplication": {
            "unique_food_ids": int(foods["food_id"].nunique()),
            "duplicate_food_ids": int(foods["food_id"].duplicated().sum()),
            "unique_dedup_signatures": int(foods["dedup_signature"].nunique()) if "dedup_signature" in foods else 0,
            "duplicate_dedup_signatures": int(foods["dedup_signature"].duplicated().sum()) if "dedup_signature" in foods else int(len(foods)),
        },
        "personas": rows,
    }
    output = PROJECT_ROOT / "validation_report.json"
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
