@echo off
REM Double-click to pull fresh Asana data and rebuild the dashboard.
REM Requires .env with your ASANA_TOKEN and deps installed (pip install -r requirements.txt).
cd /d "%~dp0"

echo Pulling latest from Asana (all 24 schools)...
python snapshot.py
if errorlevel 1 goto :err

echo.
echo Rebuilding dashboard metrics...
python metrics.py
if errorlevel 1 goto :err

echo.
echo Done. Open index.html to view the updated dashboard.
pause
exit /b 0

:err
echo.
echo Something went wrong.
echo  - Make sure .env exists and contains your ASANA_TOKEN
echo  - Make sure dependencies are installed:  pip install -r requirements.txt
pause
exit /b 1
