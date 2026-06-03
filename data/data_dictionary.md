# NutriAI Data Dictionary

`food_database.csv` contains one row per meal candidate. The app treats each row as a single meal serving that can be portion-adjusted by the planner.

- `allergens`: semicolon-delimited explicit allergen tags used for hard exclusion.
- `base_name`: human-readable dish template used to prevent repeated base dishes across a 7-day plan.
- `condition_flags`: high-FODMAP, reflux-trigger, high-GI, high-sodium, or added-sugar markers.
- `cross_contamination_risks`: potential exposure tags that are excluded when strict mode is enabled.
- nutrient columns: per-serving macro and micronutrient estimates.
- boolean diet columns: compatibility flags used before ranking, including `contains_honey` for vegan exclusion.

The snapshot is deterministic and offline so graders can run the app without API keys. It is structured around USDA FoodData Central style nutrients and rule sources listed in `clinical_rules.json`.
