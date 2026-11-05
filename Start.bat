@echo off
rem Startet den Landingpage-Builder. Einfach doppelklicken.
cd /d "%~dp0"

python -c "import streamlit, anthropic, pandas, PIL" 2>nul
if errorlevel 1 (
    echo Einmalige Einrichtung: benoetigte Pakete werden installiert ...
    python -m pip install -r requirements.txt
)

echo Die App oeffnet sich gleich im Browser. Dieses Fenster offen lassen, solange du sie benutzt.
python -m streamlit run streamlit_app.py
pause
