# NutriAI Source Provenance

This project now separates professor-listed source data from generated meal candidates.

## Professor-Listed Sources Incorporated

- `usda_fooddata_reference.csv`: ingredient nutrition reference records fetched from USDA FoodData Central when an API key or `DEMO_KEY` is available. Current cache API matches: 7 of 28 requested ingredients.
- `rda_reference.csv`: compact age/sex RDA and AI targets used directly by the planner for daily nutrient gap checks.
- `source_lookup_fodmap.csv`: conservative IBS/FODMAP ingredient categories based on Monash Low-FODMAP public guidance concepts. This is not a licensed Monash app database export.
- `source_lookup_glycemic_index.csv`: optional Glycaemic Index database mapping for diabetes GI thresholds and low-GI preference.
- `source_lookup_dash.csv`: optional NHLBI DASH guideline mapping for hypertension sodium caps and potassium/calcium/magnesium/fiber emphasis.

## Internal Rule Tables

- `source_lookup_allergens.csv`: user-declared allergen keyword map used to hard-exclude ingredients such as dairy, gluten/wheat, peanuts, tree nuts, shellfish, soy, sesame, and eggs. This is not presented as an external data source.
- `source_lookup_gerd_triggers.csv`: low-acid rule map for the GERD/acidity capability. This is not presented as an external data source because the professor source list does not include a GERD-specific API.

## What Is Still Generated

`food_database.csv` contains 10,000 deterministic meal candidate records generated from curated recipe templates. The generator links each candidate to USDA reference IDs where mapped, deduplicates records by semantic candidate signature, and then applies the clinical/allergen lookup rules. This keeps grading fast and offline while making the data lineage visible.

## Runtime Behavior

The Streamlit app does not call external APIs during normal use or Streamlit Community Cloud deployment. To refresh the USDA reference cache, run:

```powershell
python scripts\build_source_reference_data.py
python scripts\build_offline_dataset.py
```

Set `FDC_API_KEY` for a personal USDA/data.gov key. Without it, the script uses `DEMO_KEY`, which has lower official rate limits.
