@echo off
setlocal
chcp 65001 > nul
title [QA Automation] Frontend UI Playwright Tests
cd /d "%~dp0"

echo ================================================================================
echo  [QA AUTOMATION] FRONTEND UI TESTS (Playwright + Page Object Model)
echo  Target: tests/frontend/
echo ================================================================================
echo.

if not exist ".venv\Scripts\pytest.exe" (
    echo [ERROR] Virtual environment .venv was not found!
    echo Please install dependencies: .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

echo [*] Executing frontend tests with Pytest...
.venv\Scripts\pytest.exe tests/frontend %*

echo.
echo ================================================================================
echo  [*] Execution finished.
echo  [*] To open Allure report with video screencasts run: run_allure_report.bat
echo ================================================================================
pause
