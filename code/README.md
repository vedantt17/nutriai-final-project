# NutriAI Code

From the project root:

```powershell
pip install -r code\requirements.txt
streamlit run code\app.py
```

Run acceptance tests:

```powershell
python -m unittest discover -s code\tests -v
```

Regenerate the offline dataset if needed:

```powershell
python scripts\build_offline_dataset.py
```
