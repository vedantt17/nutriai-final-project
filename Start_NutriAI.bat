@echo off
setlocal
cd /d "%~dp0"

echo Starting NutriAI...
echo.

set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python312\python.exe"
if not exist "%PYTHON_EXE%" (
  set "PYTHON_EXE=python"
)

"%PYTHON_EXE%" -c "import streamlit" >nul 2>nul
if errorlevel 1 (
  echo Streamlit was not found for this Python.
  echo Installing requirements with Python...
  "%PYTHON_EXE%" -m pip install -r code\requirements.txt
  if errorlevel 1 (
    echo.
    echo Install failed. Try running:
    echo   pip install -r code\requirements.txt
    pause
    exit /b 1
  )
)

"%PYTHON_EXE%" -m streamlit run code\app.py --server.port 8501

if errorlevel 1 (
  echo.
  echo NutriAI did not start. If port 8501 is busy, try:
  echo   streamlit run code\app.py --server.port 8502
  pause
  exit /b 1
)
