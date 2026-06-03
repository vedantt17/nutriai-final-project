# NutriAI Streamlit Community Cloud Deployment

NutriAI is ready to deploy on Streamlit Community Cloud from a GitHub repository.

## Streamlit Cloud Settings

Use these values when creating the app:

- Repository: your NutriAI GitHub repository
- Branch: `main`
- Main file path: `code/app.py`
- Python dependencies: `code/requirements.txt`
- Secrets: none required

The app uses the offline files in `data/`, so no API keys, database credentials, or cloud storage setup are required.

## Deployment Steps

1. Push the `nutriai_final_project` folder to a clean GitHub repository.
2. Go to https://share.streamlit.io.
3. Sign in with GitHub.
4. Click `Create app`.
5. Select the GitHub repository and branch.
6. Set the main file path to `code/app.py`.
7. Click `Deploy`.

## Smoke Check After Deploy

After the public app opens:

- Confirm the sidebar opens and closes.
- Generate the default plan.
- Confirm the 7-day plan table loads.
- Hover the weekly macro donut chart and confirm the tooltip appears.
- Open the `Personas` tab and run required persona tests.

## Local Command

From this project folder:

```powershell
pip install -r code\requirements.txt
streamlit run code\app.py
```
