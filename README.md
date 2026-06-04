# NutriAI - BAX 423 Final Project

NutriAI is a runnable Streamlit application that generates a clinically filtered 7-day, 3-meal-a-day meal plan in under 60 seconds. It supports demographic inputs, diet modes, allergies, cross-contamination exclusion, clinical conditions, nutrient analytics, explainability, diversity scoring, and BAX-423 technique benchmarks.

## Quick Start

Live app:

```text
https://nutriaii.streamlit.app/
```

The deployed app runs on Streamlit Community Cloud from the GitHub repository and does not require any setup from the grader.

Easiest option on Windows: double-click `Start_NutriAI.bat`, keep the terminal window open, then open:

```text
http://localhost:8501
```

Manual option:

Run these commands from the project root:

```powershell
pip install -r code\requirements.txt
streamlit run code\app.py
```

The app uses the included offline dataset and source-reference files in `data/`, so no API key is required for grading.

## Streamlit Community Cloud

This project is ready for Streamlit Community Cloud. Deploy from a clean GitHub repository with:

- Main file path: `code/app.py`
- Dependency file: `code/requirements.txt`
- Secrets: none

See `DEPLOYMENT.md` for the full checklist.

## Test Command

```powershell
python -m unittest discover -s code\tests -v
```

The tests verify:

- 10,750 deduplicated offline meal records.
- All four required personas generate 21 meals.
- No exact repeated meals and no repeated base dishes in a 7-day plan.
- All selected meals pass clinical, allergen, cross-contamination, diet, and cultural filters.
- RDA analytics and explainability tables are present.
- Generation remains below the 60-second requirement.

## Submission Contents

- `code/`: Streamlit app, planning package, tests, and `requirements.txt`.
- `data/`: 10,750-record deduplicated offline food snapshot, USDA ingredient cache, RDA table, clinical lookup files, source provenance, and data dictionary.
- `brief.pdf`: 4-page technical brief.
- `prompts.md`: AI prompts and how outputs were modified.
- `README.md`: setup, run, and test instructions.

## BAX-423 Techniques

NutriAI integrates three course techniques:

- Bloom filter sketching for fast allergen and cross-contamination pre-screening.
- Dense hashed embeddings for matching user clinical/diet profiles to meal candidates without downloading model weights.
- Multi-stage recommendation ranking for calorie fit, micronutrient priorities, clinical fit, semantic similarity, and diversity.

## Data and Rule References

The planner is offline at runtime, but the data layer now includes explicit source-reference files:

- `data/usda_fooddata_reference.csv`: USDA FoodData Central ingredient cache built by `scripts/build_source_reference_data.py`.
- `data/rda_reference.csv`: compact age/sex RDA and AI targets.
- `data/source_lookup_fodmap.csv`: Monash-informed FODMAP rule mapping.
- `data/source_lookup_glycemic_index.csv`: GI-band and diabetes threshold mapping.
- `data/source_lookup_gerd_triggers.csv`: internal low-acid rule map for GERD/acidity filtering.
- `data/source_lookup_allergens.csv`: internal allergen keyword map for user-declared exclusions.
- `data/source_lookup_dash.csv`: NHLBI DASH sodium and nutrient-emphasis rules.
- `data/source_inventory.csv` and `data/source_provenance.md`: transparent source coverage and caveats.

References:

- USDA FoodData Central API guide: https://fdc.nal.usda.gov/api-guide.html
- NIH Dietary Reference Intakes: https://www.ncbi.nlm.nih.gov/books/NBK56068/
- NHLBI DASH eating plan: https://www.nhlbi.nih.gov/education/dash-eating-plan
- Monash University Low FODMAP program: https://www.monashfodmap.com/
- University of Sydney Glycemic Index database: https://glycemicindex.com/

To refresh source references before rebuilding the meal snapshot:

```powershell
python scripts\build_source_reference_data.py
python scripts\build_offline_dataset.py
```

Set `FDC_API_KEY` to use a personal USDA/data.gov key. Without it, the script uses `DEMO_KEY`, which has lower rate limits. Monash and GI are used as curated public-guidance mappings, not bulk licensed database exports. Allergy and low-acid GERD/acidity handling are internal rule maps matched against meal and USDA ingredient terms, not extra external data sources.

## Safety Note

This is an educational class project. It is not medical advice and should not be used as a substitute for a clinician or registered dietitian.
