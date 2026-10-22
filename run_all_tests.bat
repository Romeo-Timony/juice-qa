@echo off
setlocal
chcp 65001 > nul
title [QA Automation] Full Test Suite (UI + API + E2E + Unit)
cd /d "%~dp0"

echo ================================================================================
echo  [QA AUTOMATION] FULL REGRESSION SUITE (UI + API + E2E + Unit)
echo  Targets: tests/ (Domain Architecture: API, UI, E2E, Unit)
echo ================================================================================
echo.

if not exist ".venv\Scripts\pytest.exe" (
    echo [ERROR] Virtual environment .venv was not found!
    pause
    exit /b 1
)

echo [*] Executing all tests with Pytest...
.venv\Scripts\pytest.exe tests/api tests/ui %*

echo.
echo ================================================================================
echo  [*] Execution finished.
echo  [*] To open Allure report run: run_allure_report.bat
echo ================================================================================
pause
