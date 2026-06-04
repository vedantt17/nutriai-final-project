# Prompts Used

1. "Which one is easier to complete?"  
   Used to compare the NutriAI and EngageIQ project documents; the output was used only to choose NutriAI as the lower-risk build.

2. "Act as an expert senior level developer and build the NutriAI project such that I get full 100/100."  
   Used as the implementation brief. The generated plan was converted into a scoped Streamlit project with tests, data, documentation, and a PDF brief.

3. "Follow the instructions given in the docx file."  
   Used to map each assignment requirement to a concrete deliverable: six core capabilities, 5,000+ offline records, technical brief, prompts log, and single-command runnable app.

4. "Debug after each step."  
   Used to run syntax checks, persona smoke tests, dataset coverage checks, and a unittest acceptance suite after implementation layers were added.

5. "Be transparent about whether the data was generated, then incorporate the expected data sources where applicable."
   Used to add a source-reference build step, USDA FoodData Central ingredient cache, Monash/GI/NIDDK/FDA/NHLBI lookup files, provenance columns, and a visible Sources tab while keeping the app offline-runnable for grading.

All generated code and content were edited for consistency, deterministic offline grading, and alignment with the BAX-423 rubric.
