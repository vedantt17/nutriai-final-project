from __future__ import annotations

import csv
import json
import os
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
FDC_SEARCH_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"


USDA_QUERIES = [
    ("quinoa", "quinoa cooked"),
    ("banana", "banana raw"),
    ("chia", "chia seeds dried"),
    ("fortified oat milk", "oat milk fortified"),
    ("egg", "egg whole cooked"),
    ("spinach", "spinach raw"),
    ("brown rice", "rice brown cooked"),
    ("tofu", "tofu firm"),
    ("greek yogurt", "greek yogurt plain nonfat"),
    ("blueberries", "blueberries raw"),
    ("pumpkin seeds", "pumpkin seeds dried"),
    ("almonds", "almonds raw"),
    ("millet", "millet cooked"),
    ("peanut butter", "peanut butter smooth"),
    ("corn tortilla", "corn tortilla"),
    ("avocado", "avocado raw"),
    ("salmon", "salmon cooked"),
    ("lentils", "lentils cooked"),
    ("chickpeas", "chickpeas cooked"),
    ("chicken", "chicken breast cooked"),
    ("shrimp", "shrimp cooked"),
    ("sweet potato", "sweet potato cooked"),
    ("kale", "kale raw"),
    ("cod", "cod cooked"),
    ("tempeh", "tempeh"),
    ("black beans", "black beans cooked"),
    ("wheat pasta", "pasta cooked wheat"),
    ("pork", "pork cooked"),
]


NUTRIENT_MATCHES = {
    "calories_per_100g": ("energy", "kcal"),
    "protein_g_per_100g": ("protein", None),
    "carbs_g_per_100g": ("carbohydrate, by difference", None),
    "fat_g_per_100g": ("total lipid", None),
    "fiber_g_per_100g": ("fiber, total dietary", None),
    "iron_mg_per_100g": ("iron, fe", None),
    "calcium_mg_per_100g": ("calcium, ca", None),
    "vitamin_b12_mcg_per_100g": ("vitamin b-12", None),
    "vitamin_d_mcg_per_100g": ("vitamin d", None),
    "zinc_mg_per_100g": ("zinc, zn", None),
    "potassium_mg_per_100g": ("potassium, k", None),
    "magnesium_mg_per_100g": ("magnesium, mg", None),
    "sodium_mg_per_100g": ("sodium, na", None),
}


USDA_FIELDNAMES = [
    "ingredient",
    "fdc_query",
    "fdc_id",
    "fdc_description",
    "data_type",
    "publication_date",
    *NUTRIENT_MATCHES.keys(),
    "source_url",
    "source_status",
]


def _empty_usda_row(ingredient: str, query: str, status: str) -> dict[str, Any]:
    row = {
        "ingredient": ingredient,
        "fdc_query": query,
        "fdc_id": "",
        "fdc_description": "",
        "data_type": "",
        "publication_date": "",
        "source_url": "https://fdc.nal.usda.gov/api-guide/",
        "source_status": status,
    }
    for column in NUTRIENT_MATCHES:
        row[column] = ""
    return row


def normalize_key(value: Any) -> str:
    return str(value or "").strip().lower().replace("_", " ").replace("-", " ")


def _nutrient_value(food: dict[str, Any], target_name: str, target_unit: str | None) -> float | str:
    nutrients = food.get("foodNutrients", [])
    for nutrient in nutrients:
        name = str(nutrient.get("nutrientName", "")).strip().lower()
        unit = str(nutrient.get("unitName", "")).strip().lower()
        if target_name in name and (target_unit is None or target_unit in unit):
            value = nutrient.get("value")
            try:
                return round(float(value), 3)
            except (TypeError, ValueError):
                return ""
    return ""


def _best_food(payload: dict[str, Any]) -> dict[str, Any] | None:
    foods = payload.get("foods") or []
    if not foods:
        return None

    preferred_types = {"Foundation", "SR Legacy", "Survey (FNDDS)"}
    for food in foods:
        if food.get("dataType") in preferred_types:
            return food
    return foods[0]


def fetch_fdc_row(ingredient: str, query: str, api_key: str) -> dict[str, Any]:
    params = urlencode(
        {
            "api_key": api_key,
            "query": query,
            "pageSize": 5,
        },
    )
    request = Request(f"{FDC_SEARCH_URL}?{params}", headers={"User-Agent": "NutriAI-BAX423/1.0"})
    try:
        with urlopen(request, timeout=12) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        return _empty_usda_row(ingredient, query, f"api_http_error_{exc.code}")
    except URLError as exc:
        reason = str(getattr(exc, "reason", exc)).replace(",", " ")
        return _empty_usda_row(ingredient, query, f"api_url_error_{reason[:80]}")
    except TimeoutError:
        return _empty_usda_row(ingredient, query, "api_timeout")
    except json.JSONDecodeError:
        return _empty_usda_row(ingredient, query, "api_json_decode_error")

    food = _best_food(payload)
    if food is None:
        return _empty_usda_row(ingredient, query, "api_no_match")

    row = {
        "ingredient": ingredient,
        "fdc_query": query,
        "fdc_id": food.get("fdcId", ""),
        "fdc_description": food.get("description", ""),
        "data_type": food.get("dataType", ""),
        "publication_date": food.get("publishedDate", ""),
        "source_url": f"https://fdc.nal.usda.gov/fdc-app.html#/food-details/{food.get('fdcId', '')}/nutrients",
        "source_status": "api_match",
    }
    for column, (target_name, target_unit) in NUTRIENT_MATCHES.items():
        row[column] = _nutrient_value(food, target_name, target_unit)
    return row


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    fieldnames = fieldnames or list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_usda_reference() -> list[dict[str, Any]]:
    api_key = os.getenv("FDC_API_KEY", "DEMO_KEY").strip() or "DEMO_KEY"
    skip_api = os.getenv("NUTRIAI_SKIP_FDC_API", "").strip().lower() in {"1", "true", "yes"}
    existing_rows = {}
    existing_path = DATA_DIR / "usda_fooddata_reference.csv"
    if existing_path.exists():
        with existing_path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if str(row.get("fdc_id", "")).strip():
                    existing_rows[normalize_key(row.get("ingredient"))] = row
    rows = []
    for index, (ingredient, query) in enumerate(USDA_QUERIES):
        if skip_api:
            rows.append(existing_rows.get(normalize_key(ingredient), _empty_usda_row(ingredient, query, "api_skipped_by_env")))
            continue
        row = fetch_fdc_row(ingredient, query, api_key)
        if not str(row.get("fdc_id", "")).strip() and normalize_key(ingredient) in existing_rows:
            row = existing_rows[normalize_key(ingredient)]
            row["source_status"] = "api_match_cached"
        rows.append(row)
        if index < len(USDA_QUERIES) - 1:
            time.sleep(0.25)
    return rows


def rule_rows() -> dict[str, list[dict[str, Any]]]:
    fodmap = [
        {"ingredient_pattern": "garlic", "fodmap_level": "high", "rule_action": "exclude for IBS", "source_name": "Monash University Low FODMAP program", "source_url": "https://www.monashfodmap.com/", "directness": "curated public-guidance mapping; not an official Monash app export", "notes": "Used as conservative high-FODMAP trigger."},
        {"ingredient_pattern": "onion", "fodmap_level": "high", "rule_action": "exclude for IBS", "source_name": "Monash University Low FODMAP program", "source_url": "https://www.monashfodmap.com/", "directness": "curated public-guidance mapping; not an official Monash app export", "notes": "Used as conservative high-FODMAP trigger."},
        {"ingredient_pattern": "wheat", "fodmap_level": "high", "rule_action": "exclude for IBS", "source_name": "Monash University Low FODMAP program", "source_url": "https://www.monashfodmap.com/", "directness": "curated public-guidance mapping; not an official Monash app export", "notes": "Also overlaps gluten allergy logic."},
        {"ingredient_pattern": "honey", "fodmap_level": "high", "rule_action": "exclude for IBS and flag added sugar", "source_name": "Monash University Low FODMAP program", "source_url": "https://www.monashfodmap.com/", "directness": "curated public-guidance mapping; not an official Monash app export", "notes": "Also excluded for vegan profiles."},
        {"ingredient_pattern": "lentils", "fodmap_level": "medium", "rule_action": "portion-sensitive for IBS", "source_name": "Monash University Low FODMAP program", "source_url": "https://www.monashfodmap.com/", "directness": "curated public-guidance mapping; not an official Monash app export", "notes": "Allows ranking but tracks medium FODMAP category."},
        {"ingredient_pattern": "chickpeas", "fodmap_level": "medium", "rule_action": "portion-sensitive for IBS", "source_name": "Monash University Low FODMAP program", "source_url": "https://www.monashfodmap.com/", "directness": "curated public-guidance mapping; not an official Monash app export", "notes": "Allows ranking but tracks medium FODMAP category."},
        {"ingredient_pattern": "black beans", "fodmap_level": "medium", "rule_action": "portion-sensitive for IBS", "source_name": "Monash University Low FODMAP program", "source_url": "https://www.monashfodmap.com/", "directness": "curated public-guidance mapping; not an official Monash app export", "notes": "Allows ranking but tracks medium FODMAP category."},
        {"ingredient_pattern": "quinoa", "fodmap_level": "low", "rule_action": "allow", "source_name": "Monash University Low FODMAP program", "source_url": "https://www.monashfodmap.com/", "directness": "curated public-guidance mapping; not an official Monash app export", "notes": "Used as low-FODMAP grain alternative."},
        {"ingredient_pattern": "rice", "fodmap_level": "low", "rule_action": "allow", "source_name": "Monash University Low FODMAP program", "source_url": "https://www.monashfodmap.com/", "directness": "curated public-guidance mapping; not an official Monash app export", "notes": "Used as low-FODMAP starch alternative."},
        {"ingredient_pattern": "firm tofu", "fodmap_level": "low", "rule_action": "allow", "source_name": "Monash University Low FODMAP program", "source_url": "https://www.monashfodmap.com/", "directness": "curated public-guidance mapping; not an official Monash app export", "notes": "Firm tofu treated separately from silken tofu."},
    ]
    gi = [
        {"food_pattern": "honey", "gi_band": "high/added sugar", "gi_max_used": 55, "rule_action": "exclude for diabetes", "source_name": "University of Sydney Glycemic Index database", "source_url": "https://glycemicindex.com/", "directness": "curated category mapping from GI database concept", "notes": "App excludes added sugar and GI above 55 for diabetes profiles."},
        {"food_pattern": "white rice", "gi_band": "higher", "gi_max_used": 55, "rule_action": "penalize or exclude when row GI exceeds threshold", "source_name": "University of Sydney Glycemic Index database", "source_url": "https://glycemicindex.com/", "directness": "curated category mapping from GI database concept", "notes": "Template GI values are conservative approximations by food pattern."},
        {"food_pattern": "wheat pasta", "gi_band": "medium/high", "gi_max_used": 55, "rule_action": "exclude when row GI exceeds threshold", "source_name": "University of Sydney Glycemic Index database", "source_url": "https://glycemicindex.com/", "directness": "curated category mapping from GI database concept", "notes": "Used for diabetes filtering."},
        {"food_pattern": "quinoa", "gi_band": "low/medium", "gi_max_used": 55, "rule_action": "allow", "source_name": "University of Sydney Glycemic Index database", "source_url": "https://glycemicindex.com/", "directness": "curated category mapping from GI database concept", "notes": "Preferred lower-GI grain option."},
        {"food_pattern": "lentils", "gi_band": "low", "gi_max_used": 55, "rule_action": "allow", "source_name": "University of Sydney Glycemic Index database", "source_url": "https://glycemicindex.com/", "directness": "curated category mapping from GI database concept", "notes": "Preferred fiber-rich lower-GI ingredient."},
        {"food_pattern": "beans", "gi_band": "low", "gi_max_used": 55, "rule_action": "allow", "source_name": "University of Sydney Glycemic Index database", "source_url": "https://glycemicindex.com/", "directness": "curated category mapping from GI database concept", "notes": "Preferred fiber-rich lower-GI ingredient."},
    ]
    gerd = [
        {"trigger_pattern": "tomato", "acidity_level": "high", "rule_action": "exclude for GERD/acidity", "source_name": "NutriAI internal low-acid rule map", "source_url": "", "directness": "internal rule table for the rubric's low-acid constraint", "notes": "Course source list does not provide a GERD API; this rule is not claimed as an external dataset."},
        {"trigger_pattern": "citrus", "acidity_level": "high", "rule_action": "exclude for GERD/acidity", "source_name": "NutriAI internal low-acid rule map", "source_url": "", "directness": "internal rule table for the rubric's low-acid constraint", "notes": "Covers lime, orange, lemon, and citrus salsa."},
        {"trigger_pattern": "chocolate", "acidity_level": "high", "rule_action": "exclude for GERD/acidity", "source_name": "NutriAI internal low-acid rule map", "source_url": "", "directness": "internal rule table for the rubric's low-acid constraint", "notes": "Reserved for future recipe expansion."},
        {"trigger_pattern": "coffee", "acidity_level": "high", "rule_action": "exclude for GERD/acidity", "source_name": "NutriAI internal low-acid rule map", "source_url": "", "directness": "internal rule table for the rubric's low-acid constraint", "notes": "Reserved for future recipe expansion."},
        {"trigger_pattern": "high-fat foods", "acidity_level": "high", "rule_action": "exclude for GERD/acidity when flagged", "source_name": "NutriAI internal low-acid rule map", "source_url": "", "directness": "internal rule table for the rubric's low-acid constraint", "notes": "Used with fried/high-fat templates."},
        {"trigger_pattern": "spicy foods", "acidity_level": "high", "rule_action": "exclude for GERD/acidity when flagged", "source_name": "NutriAI internal low-acid rule map", "source_url": "", "directness": "internal rule table for the rubric's low-acid constraint", "notes": "Used with salsa/spicy flags."},
    ]
    allergens = [
        {"allergen_category": "milk/dairy", "ingredient_patterns": "milk; cheese; yogurt; paneer; dairy", "app_column": "contains_dairy", "source_name": "NutriAI internal allergen keyword map", "source_url": "", "directness": "internal rule table for user-declared allergen exclusion", "notes": "Matches user-declared allergens against USDA/meal ingredient terms."},
        {"allergen_category": "eggs", "ingredient_patterns": "egg; eggs", "app_column": "contains_eggs", "source_name": "NutriAI internal allergen keyword map", "source_url": "", "directness": "internal rule table for user-declared allergen exclusion", "notes": "Hard exclusion when user declares egg allergy."},
        {"allergen_category": "fish", "ingredient_patterns": "salmon; cod; tuna; trout; fish", "app_column": "contains_fish", "source_name": "NutriAI internal allergen keyword map", "source_url": "", "directness": "internal rule table for user-declared allergen exclusion", "notes": "Available for future user allergy input and pescatarian rules."},
        {"allergen_category": "shellfish", "ingredient_patterns": "shrimp; crab; lobster; prawn; shellfish", "app_column": "contains_shellfish", "source_name": "NutriAI internal allergen keyword map", "source_url": "", "directness": "internal rule table for user-declared allergen exclusion", "notes": "Hard exclusion when user declares shellfish."},
        {"allergen_category": "tree nuts", "ingredient_patterns": "almond; almonds; cashew; walnut; pistachio; pecan", "app_column": "contains_tree_nuts", "source_name": "NutriAI internal allergen keyword map", "source_url": "", "directness": "internal rule table for user-declared allergen exclusion", "notes": "Hard exclusion and strict cross-contact option."},
        {"allergen_category": "peanuts", "ingredient_patterns": "peanut; peanut butter", "app_column": "contains_peanuts", "source_name": "NutriAI internal allergen keyword map", "source_url": "", "directness": "internal rule table for user-declared allergen exclusion", "notes": "Hard exclusion when user declares peanuts."},
        {"allergen_category": "wheat/gluten", "ingredient_patterns": "wheat; wheat pasta; wheat tortilla; wheat pita; barley; rye; gluten", "app_column": "contains_gluten", "source_name": "NutriAI internal allergen keyword map", "source_url": "", "directness": "internal rule table for user-declared allergen exclusion", "notes": "Mapped to gluten/wheat exclusion."},
        {"allergen_category": "soy", "ingredient_patterns": "soy; tofu; tempeh; edamame; soy sauce", "app_column": "contains_soy", "source_name": "NutriAI internal allergen keyword map", "source_url": "", "directness": "internal rule table for user-declared allergen exclusion", "notes": "Hard exclusion when user declares soy."},
        {"allergen_category": "sesame", "ingredient_patterns": "sesame; tahini", "app_column": "contains_sesame", "source_name": "NutriAI internal allergen keyword map", "source_url": "", "directness": "internal rule table for user-declared allergen exclusion", "notes": "Hard exclusion when user declares sesame."},
    ]
    dash = [
        {"rule_name": "daily sodium cap", "threshold_or_focus": "2300 mg/day", "app_field": "sodium_mg", "source_name": "NHLBI DASH eating plan", "source_url": "https://www.nhlbi.nih.gov/education/dash-eating-plan", "implementation": "Hypertension profiles use 2300 mg/day and a derived 760 mg/meal soft cap."},
        {"rule_name": "vegetables/fruits/whole grains focus", "threshold_or_focus": "prefer high-fiber patterns", "app_field": "fiber_g", "source_name": "NHLBI DASH eating plan", "source_url": "https://www.nhlbi.nih.gov/education/dash-eating-plan", "implementation": "Ranking rewards fiber-rich bowls, grains, vegetables, beans, and seeds."},
        {"rule_name": "potassium focus", "threshold_or_focus": "prefer potassium-rich meals", "app_field": "potassium_mg", "source_name": "NHLBI DASH eating plan", "source_url": "https://www.nhlbi.nih.gov/education/dash-eating-plan", "implementation": "Hypertension scoring rewards potassium density."},
        {"rule_name": "magnesium focus", "threshold_or_focus": "prefer magnesium-rich meals", "app_field": "magnesium_mg", "source_name": "NHLBI DASH eating plan", "source_url": "https://www.nhlbi.nih.gov/education/dash-eating-plan", "implementation": "Hypertension scoring rewards magnesium density."},
        {"rule_name": "calcium focus", "threshold_or_focus": "compare against RDA/AI", "app_field": "calcium_mg", "source_name": "NHLBI DASH eating plan", "source_url": "https://www.nhlbi.nih.gov/education/dash-eating-plan", "implementation": "RDA analytics and ranking prioritize calcium when requested."},
    ]
    return {
        "source_lookup_fodmap.csv": fodmap,
        "source_lookup_glycemic_index.csv": gi,
        "source_lookup_gerd_triggers.csv": gerd,
        "source_lookup_allergens.csv": allergens,
        "source_lookup_dash.csv": dash,
    }


def build_inventory(usda_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    api_matches = sum(1 for row in usda_rows if str(row.get("fdc_id", "")).strip())
    return [
        {"source_name": "USDA FoodData Central API", "url": "https://fdc.nal.usda.gov/api-guide/", "local_file": "usda_fooddata_reference.csv", "used_for": "Ingredient-level nutrition reference records and nutrient field schema", "incorporation_type": f"professor-listed source; API fetch/cache ({api_matches} matched rows in current cache)", "runtime_requirement": "None at Streamlit runtime", "caveat": "Meal candidates still use deterministic recipe-template scaling rather than live per-gram recipe calculation."},
        {"source_name": "NIH Dietary Reference Intakes", "url": "https://www.ncbi.nlm.nih.gov/books/NBK56068/", "local_file": "rda_reference.csv", "used_for": "Age/sex nutrient targets for protein, fiber, iron, calcium, B12, vitamin D, zinc, potassium, magnesium, sodium, omega-3", "incorporation_type": "professor-listed source; compact RDA/AI table used directly by app", "runtime_requirement": "None", "caveat": "Simplified adult bands for class demo."},
        {"source_name": "Monash University Low-FODMAP list", "url": "https://www.monashfodmap.com/", "local_file": "source_lookup_fodmap.csv", "used_for": "IBS high/medium/low FODMAP rule mapping", "incorporation_type": "professor-listed source; curated public-guidance mapping", "runtime_requirement": "None", "caveat": "Not a licensed export of the Monash mobile-app food database."},
        {"source_name": "Glycaemic Index database", "url": "https://www.glycemicindex.com/", "local_file": "source_lookup_glycemic_index.csv", "used_for": "Diabetes GI threshold and lower-GI ranking categories", "incorporation_type": "professor-listed optional source; curated GI-band mapping", "runtime_requirement": "None", "caveat": "Template GI values are approximations by ingredient pattern."},
        {"source_name": "DASH diet guidelines", "url": "https://www.nhlbi.nih.gov/education/dash-eating-plan", "local_file": "source_lookup_dash.csv", "used_for": "Hypertension sodium cap and DASH nutrient emphasis", "incorporation_type": "professor-listed optional source; public guideline mapping", "runtime_requirement": "None", "caveat": "Meal cap is derived from the daily sodium cap for practical meal-level filtering."},
        {"source_name": "NutriAI internal allergen keyword map", "url": "", "local_file": "source_lookup_allergens.csv", "used_for": "User-declared allergen keyword exclusion against meal/USDA ingredient terms", "incorporation_type": "internal implementation table for required allergy capability", "runtime_requirement": "None", "caveat": "Not presented as an external data source."},
        {"source_name": "NutriAI internal low-acid rule map", "url": "", "local_file": "source_lookup_gerd_triggers.csv", "used_for": "GERD/acidity low-acid constraint examples", "incorporation_type": "internal implementation table for required GERD/acidity capability", "runtime_requirement": "None", "caveat": "Not presented as an external data source because the professor list does not provide a GERD API."},
    ]


def write_provenance(usda_rows: list[dict[str, Any]]) -> None:
    api_matches = sum(1 for row in usda_rows if str(row.get("fdc_id", "")).strip())
    text = f"""# NutriAI Source Provenance

This project now separates professor-listed source data from generated meal candidates.

## Professor-Listed Sources Incorporated

- `usda_fooddata_reference.csv`: ingredient nutrition reference records fetched from USDA FoodData Central when an API key or `DEMO_KEY` is available. Current cache API matches: {api_matches} of {len(usda_rows)} requested ingredients.
- `rda_reference.csv`: compact age/sex RDA and AI targets used directly by the planner for daily nutrient gap checks.
- `source_lookup_fodmap.csv`: conservative IBS/FODMAP ingredient categories based on Monash Low-FODMAP public guidance concepts. This is not a licensed Monash app database export.
- `source_lookup_glycemic_index.csv`: optional Glycaemic Index database mapping for diabetes GI thresholds and low-GI preference.
- `source_lookup_dash.csv`: optional NHLBI DASH guideline mapping for hypertension sodium caps and potassium/calcium/magnesium/fiber emphasis.

## Internal Rule Tables

- `source_lookup_allergens.csv`: user-declared allergen keyword map used to hard-exclude ingredients such as dairy, gluten/wheat, peanuts, tree nuts, shellfish, soy, sesame, and eggs. This is not presented as an external data source.
- `source_lookup_gerd_triggers.csv`: low-acid rule map for the GERD/acidity capability. This is not presented as an external data source because the professor source list does not include a GERD-specific API.

## What Is Still Generated

`food_database.csv` contains 5,200 deterministic meal candidate records generated from curated recipe templates. The generator links each candidate to USDA reference IDs where mapped and then applies the clinical/allergen lookup rules. This keeps grading fast and offline while making the data lineage visible.

## Runtime Behavior

The Streamlit app does not call external APIs during normal use or Streamlit Community Cloud deployment. To refresh the USDA reference cache, run:

```powershell
python scripts\\build_source_reference_data.py
python scripts\\build_offline_dataset.py
```

Set `FDC_API_KEY` for a personal USDA/data.gov key. Without it, the script uses `DEMO_KEY`, which has lower official rate limits.
"""
    (DATA_DIR / "source_provenance.md").write_text(text, encoding="utf-8")


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    usda_rows = build_usda_reference()
    write_csv(DATA_DIR / "usda_fooddata_reference.csv", usda_rows, USDA_FIELDNAMES)
    for filename, rows in rule_rows().items():
        write_csv(DATA_DIR / filename, rows)
    inventory = build_inventory(usda_rows)
    write_csv(DATA_DIR / "source_inventory.csv", inventory)
    write_provenance(usda_rows)
    api_matches = sum(1 for row in usda_rows if str(row.get("fdc_id", "")).strip())
    print(f"Wrote source reference files to {DATA_DIR}")
    print(f"USDA FoodData Central API matches: {api_matches}/{len(usda_rows)}")


if __name__ == "__main__":
    main()
