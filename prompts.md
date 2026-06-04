# NutriAI Prompts Used

This file documents the AI prompts used to design, build, debug, and refine the NutriAI BAX-423 final project. The prompts below were written specifically for this application: a Streamlit-based clinical meal-planning dashboard that generates a safe, diverse, source-backed 7-day meal plan using nutrition references, clinical filters, recommender ranking, and BAX-423 techniques.

## 1. Full NutriAI Build Brief

```text
Act as an expert senior AI developer, data engineer, and clinical decision-support app architect. Build the NutriAI final project as a complete, runnable Streamlit application for BAX-423.

The app must generate a 7-day meal plan with 3 meals per day. It must support user inputs for age, sex, calorie target, diet mode, allergies, clinical conditions, cultural constraints, micronutrient priorities, and strict cross-contamination handling.

Implement the six required capabilities:
1. Clinical condition filtering for IBS, GERD/acidity, diabetes, and hypertension.
2. Allergy detection and hard exclusion for gluten, dairy, tree nuts, peanuts, shellfish, soy, sesame, and eggs.
3. Dietary preference handling for vegetarian, vegan, non-vegetarian, pescatarian, and cultural/religious constraints.
4. A diversity engine that prevents repeated meals and repeated base dishes across the 7-day plan.
5. Macro and micronutrient analysis for calories, protein, carbs, fat, fiber, iron, calcium, vitamin B12, vitamin D, zinc, potassium, magnesium, sodium, and omega-3.
6. Sub-60-second generation with visible runtime benchmarks.

Use BAX-423 techniques in a defensible way:
- Bloom filter sketching for allergen pre-screening.
- Hashed embedding vectors for profile-to-meal similarity.
- Multi-stage recommender ranking for calorie fit, nutrient fit, clinical fit, similarity, and diversity.

Produce a professional app structure with:
- `code/app.py` for the Streamlit UI.
- A `code/nutriai/` package for planner logic, safety rules, embeddings, Bloom filter, RDA analysis, personas, and exports.
- `data/` files for the meal database, source references, RDA targets, and rule lookup tables.
- `scripts/` for data/source generation and validation.
- `code/tests/` for automated acceptance tests.
- Documentation files for README, deployment, source provenance, and submission checklist.

Keep the app deterministic, offline-runnable at Streamlit runtime, and suitable for grading without requiring private credentials. Make the UI polished, light, professional, and focused on the actual meal-planning workflow.
```

This prompt became the main implementation contract for the app architecture, UI, data files, planner package, and testing workflow.

## 2. Source-Backed Data Layer

```text
Revise NutriAI's data approach so it is not described as synthetic data alone. Incorporate the professor-listed sources where applicable while keeping the app runnable on Streamlit Community Cloud without requiring live API calls during normal use.

Implement a source-backed data layer with:
- A USDA FoodData Central API ingestion script that queries ingredient-level nutrition records and writes `data/usda_fooddata_reference.csv`.
- A compact NIH RDA/DRI reference table used directly by the planner for nutrient gap checks.
- Monash-informed FODMAP lookup rules for IBS filtering, clearly labeled as curated public-guidance mappings rather than a licensed Monash database export.
- Glycemic Index lookup rules for diabetes filtering and lower-GI ranking.
- DASH guideline mappings for hypertension sodium caps and potassium/calcium/magnesium/fiber emphasis.
- Internal allergen and GERD/acidity rule maps, clearly labeled as internal implementation tables rather than external datasets.

Update the generated meal candidate table so each row includes provenance fields:
- `nutrition_source`
- `nutrition_source_ids`
- `nutrition_source_ingredients`
- `clinical_rule_sources`
- `source_rule_matches`
- `source_confidence`
- `source_note`

Add a Streamlit Sources tab that transparently shows source inventory, USDA cache coverage, runtime API behavior, deduplication metrics, and limitations. Be honest that the final 10,000 meal candidates are deterministic recipe-template records linked to USDA references where available.
```

This prompt was used to add the USDA ingestion script, source inventory, provenance files, source columns in the dataset, and the Sources tab.

## 3. Clinical Safety and Filtering Engine

```text
Design the NutriAI safety layer as a hard-filter engine that runs before ranking. The ranking system must never see unsafe meals.

Create a function that evaluates each meal candidate against the user's profile and returns explicit exclusion reasons. If the returned reason list is empty, the row is safe. If it contains any reason, the row is removed before recommendation ranking.

The safety function must check:
- Diet mode: vegan, vegetarian, pescatarian, and non-vegetarian.
- Cultural constraints: no pork, halal, kosher, no beef, no shellfish.
- Allergens: gluten/wheat/barley/rye, dairy/lactose, tree nuts, peanuts, shellfish, soy, sesame, and eggs.
- Cross-contamination risks when strict cross-contamination mode is enabled.
- IBS rules using FODMAP level and high-FODMAP flags.
- GERD/acidity rules using acidity level and reflux-trigger flags.
- Diabetes rules using glycemic index, high-GI flags, and added-sugar flags.
- Hypertension rules using sodium thresholds and high-sodium flags.

Use a Bloom filter to pre-screen expanded allergen terms efficiently, but still perform exact checks against ingredient text, allergen text, cross-contamination text, and boolean allergen columns. Return human-readable reasons that can be shown in the Excluded Examples table.
```

This prompt produced the safety approach implemented in `code/nutriai/rules.py` and used by the planner before ranking.

## 4. Recommendation Ranking and Diversity

```text
Implement the NutriAI meal recommender as a multi-stage ranking pipeline.

The pipeline should:
1. Load the 10,000-record meal candidate table.
2. Apply the clinical, allergen, diet, cultural, and cross-contamination hard filters.
3. Embed the user's profile text and each meal candidate using deterministic hashed embeddings.
4. Score safe candidates using calorie fit, micronutrient fit, clinical fit, profile similarity, and diversity.
5. Select breakfast, lunch, and dinner for each of 7 days.
6. Prevent exact repeated meals and avoid repeated base dishes.
7. Scale meal portions per day to stay near the user's calorie target.
8. Compute daily macro and micronutrient totals.
9. Compare daily totals against age/sex RDA or AI targets.
10. Return benchmarks for filtering time, embedding time, ranking time, total runtime, safe candidates, excluded candidates, and diversity score.

Make the ranking explainable by storing the score components in a `why_selected` string for each chosen meal. The result object should support Streamlit tables for the plan, nutrient analysis, explainability, benchmarks, and persona validation.
```

This prompt guided the planner design in `code/nutriai/planner.py`, including safe candidate generation, hashed embedding similarity, ranking factors, diversity controls, RDA comparison, and runtime metrics.

## 5. Professional Streamlit UI

```text
Act as a senior frontend engineer and redesign the NutriAI Streamlit app so it feels like a professional clinical meal-planning dashboard, not a raw dataframe demo.

Use a light, calm, healthcare-appropriate color scheme. The first screen should be the actual dashboard, not a marketing landing page. The sidebar should contain compact plan inputs. The main canvas should show:
- A polished NutriAI header with user profile pills.
- Runtime, diversity, safe candidate, and excluded candidate metrics.
- Capability status chips for clinical, allergy, diet, diversity, nutrients, and speed.
- Tabs for Plan, Nutrients, Explain, Benchmarks, Sources, and Personas.

The Plan tab should show the selected 7-day plan and an interactive macronutrient calorie-share donut/pie chart with hover values.
The Nutrients tab should show daily totals, trend charts, RDA comparisons, and warnings.
The Explain tab should focus on selected meal reasoning, ingredients, and excluded examples.
The Benchmarks tab should show capability checks and BAX-423 technique metrics.
The Sources tab should show source provenance and caveats.
The Personas tab should run required clinical personas and show pass/fail evidence.

Keep the UI readable, light, and professional. Avoid dark dataframe-heavy styling, cluttered layouts, oversized decorative sections, and unnecessary explanatory text inside the app.
```

This prompt drove the lighter professional visual design, sidebar layout, dashboard metrics, macro chart, source tab, and cleaned-up Explain tab.

## 6. Testing and Debugging

```text
Act as a senior tester and debugger for the NutriAI project. Review the implementation for functional errors, hidden rubric gaps, stale state issues, safety failures, data leakage, and deployment problems.

Create and run tests that verify:
- The meal database has at least 10,000 records.
- The generated candidate table has unique food IDs and zero duplicate semantic deduplication signatures.
- The required source/provenance columns exist.
- USDA reference data is present and linked where available.
- Each required clinical persona generates exactly 21 meals.
- No selected meal violates allergies, cross-contamination rules, diet mode, cultural constraints, or clinical condition filters.
- The 7-day plan avoids exact repeated meals and repeated base dishes.
- Macro and micronutrient fields are computed for every selected meal.
- RDA comparison outputs are generated.
- Runtime remains under 60 seconds for typical profiles.

After each major change, run syntax checks and the unit test suite. If an error appears, identify the root cause, fix it, and rerun the relevant checks before considering the step complete.
```

This prompt was used throughout implementation to run acceptance checks, debug stale Streamlit behavior, and keep the project aligned with the grading rubric.

## 7. Deployment and Submission Readiness

```text
Prepare NutriAI for final BAX-423 submission and Streamlit Community Cloud deployment.

Create deployment instructions that explain:
- The GitHub repository structure.
- The Streamlit main file path: `code/app.py`.
- The dependency file: `code/requirements.txt`.
- That no runtime secrets are required for the deployed app.
- That source ingestion can be refreshed locally with `scripts/build_source_reference_data.py` and `scripts/build_offline_dataset.py`.

Create submission documentation that includes:
- README with quick start, test command, techniques, data sources, and safety note.
- Source provenance explaining what comes from USDA, NIH, Monash-informed mappings, GI, DASH, and internal rule tables.
- A technical brief covering architecture, BAX-423 techniques, clinical test persona results, benchmarks, and limitations.
- A prompts file that documents the AI prompts used and how their outputs were edited into the final app.

Verify that the app can run locally, the tests pass, and the live Streamlit deployment reflects the latest GitHub commit.
```

This prompt was used to prepare the deployment docs, README, source provenance, technical brief, and final submission checklist.

## Human Review and Editing

The AI-generated outputs were not submitted blindly. Code and documentation were reviewed and edited for:

- Alignment with the NutriAI project document and BAX-423 rubric.
- Transparent source/data language.
- Deterministic offline grading behavior.
- Professional Streamlit UI quality.
- Runtime under the 60-second requirement.
- Automated test coverage for safety, diversity, nutrients, and persona results.

Final implementation choices were constrained to this NutriAI app only.
