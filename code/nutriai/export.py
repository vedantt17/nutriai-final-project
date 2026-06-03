from __future__ import annotations

from io import StringIO
from typing import Any

import pandas as pd

from .planner import daily_totals_to_rows, plan_to_rows
from .models import PlanResult


def plan_dataframe(result: PlanResult) -> pd.DataFrame:
    return pd.DataFrame(plan_to_rows(result))


def daily_totals_dataframe(result: PlanResult) -> pd.DataFrame:
    return pd.DataFrame(daily_totals_to_rows(result))


def capability_dataframe(result: PlanResult) -> pd.DataFrame:
    return pd.DataFrame(result.capability_checks)


def exclusions_dataframe(result: PlanResult) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for item in result.excluded_examples:
        rows.append(
            {
                "food_id": item["food_id"],
                "meal_name": item["meal_name"],
                "meal_type": item["meal_type"],
                "reasons": " | ".join(item["reasons"]),
            }
        )
    return pd.DataFrame(rows)


def rda_dataframe(result: PlanResult, day: int) -> pd.DataFrame:
    selected = result.days[day - 1]
    rows = []
    for nutrient, data in selected.rda_comparison.items():
        rows.append(
            {
                "nutrient": data["name"],
                "actual": data["actual"],
                "target": data["target"],
                "percent_of_target": data["percent"],
                "target_type": data["target_type"],
                "pass": data["passes_80pct"],
            }
        )
    return pd.DataFrame(rows)


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    buffer = StringIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8")
