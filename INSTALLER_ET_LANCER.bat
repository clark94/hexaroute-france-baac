@echo off
setlocal
cd /d "%~dp0"

echo ==============================================
echo   HexaRoute France - Installation + Streamlit

echo ==============================================
if not exist ".venv\Scripts\python.exe" (
    echo Creation de l'environnement Python...
    py -m venv .venv
    if errorlevel 1 goto err
)
echo Installation des dependances...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto err

echo Lancement du dashboard officiel BAAC...
".venv\Scripts\python.exe" -m streamlit run app.py
if errorlevel 1 goto err
exit /b 0
:err
echo Une erreur est survenue. Verifier Python, Internet et le terminal.
pause
exit /b 1
