@echo off
chcp 65001 > nul
echo ==============================================================================
echo  🏥 QA ECOSYS — SDET PRE-FLIGHT READINESS & INFRASTRUCTURE HEALTH CHECK
echo ==============================================================================

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Виртуальное окружение .venv не найдено!
    pause
    exit /b 1
)

.venv\Scripts\python.exe scripts\tools\check_environment_health.py
echo.
pause
