# NutriAI - BAX 423 Final Project

NutriAI is a runnable Streamlit application that generates a clinically filtered 7-day, 3-meal-a-day meal plan in under 60 seconds. It supports demographic inputs, diet modes, allergies, cross-contamination exclusion, clinical conditions, nutrient analytics, explainability, diversity scoring, and BAX-423 technique benchmarks.

## Quick Start

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

The app uses the included offline dataset in `data/`, so no API key is required for grading.

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

- 5,000+ offline meal records.
- All four required personas generate 21 meals.
- No exact repeated meals and no repeated base dishes in a 7-day plan.
- All selected meals pass clinical, allergen, cross-contamination, diet, and cultural filters.
- RDA analytics and explainability tables are present.
- Generation remains below the 60-second requirement.

## Submission Contents

- `code/`: Streamlit app, planning package, tests, and `requirements.txt`.
- `data/`: 5,200-record offline food snapshot, RDA reference table, clinical rules, and data dictionary.
- `brief.pdf`: 4-page technical brief.
- `prompts.md`: AI prompts and how outputs were modified.
- `README.md`: setup, run, and test instructions.

## BAX-423 Techniques

NutriAI integrates three course techniques:

- Bloom filter sketching for fast allergen and cross-contamination pre-screening.
- Dense hashed embeddings for matching user clinical/diet profiles to meal candidates without downloading model weights.
- Multi-stage recommendation ranking for calorie fit, micronutrient priorities, clinical fit, semantic similarity, and diversity.

## Data and Rule References

The offline dataset is structured around public nutrition and diet-rule sources so the app can run without network access:

- USDA FoodData Central API guide: https://fdc.nal.usda.gov/api-guide
- NIH Office of Dietary Supplements nutrient recommendations: https://ods.od.nih.gov/HealthInformation/nutrientrecommendations/
- NHLBI DASH eating plan: https://www.nhlbi.nih.gov/education/dash-eating-plan
- Monash University Low FODMAP program: https://www.monashfodmap.com/
- NIDDK celiac cross-contact guidance: https://www.niddk.nih.gov/health-information/digestive-diseases/celiac-disease/eating-diet-nutrition

## Safety Note

This is an educational class project. It is not medical advice and should not be used as a substitute for a clinician or registered dietitian.
