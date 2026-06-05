# NutriAI Submission Checklist

- [x] Working Streamlit app in `code/app.py`.
- [x] `requirements.txt` included in `code/`.
- [x] Offline `data/food_database.csv` with 10,750 deduplicated records.
- [x] USDA/source-reference cache covers 97/97 meal-template ingredients, with live/cached FDC matches counted separately.
- [x] RDA table, clinical lookup files, source inventory, and clinical rules included.
- [x] 7-day, 3-meal-per-day plan generation.
- [x] Clinical condition filtering for IBS, GERD, type 2 diabetes, and hypertension.
- [x] Allergy and cross-contamination hard exclusions.
- [x] Vegetarian, vegan, non-vegetarian, and pescatarian diet handling.
- [x] Diversity engine with no exact meal repeats, no repeated base dishes, and score reporting.
- [x] Macro and micronutrient analytics with RDA comparison.
- [x] Sub-60-second generation with benchmark display.
- [x] Explain feature for selected and excluded meals.
- [x] Required persona test table in app and brief.
- [x] Acceptance tests in `code/tests/test_nutriai.py`.
- [x] Technical brief as `brief.pdf`.
- [x] Prompts log as `prompts.md`.
