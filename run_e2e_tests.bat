@echo off
setlocal
chcp 65001 > nul
title [QA Automation] E2E Tests (User Journeys)
cd /d "%~dp0"

echo ================================================================================
echo  [QA AUTOMATION] END-TO-END (E2E) TESTS (Full User Journeys)
echo  Target: tests/e2e/
echo ================================================================================
echo.

if not exist ".venv\Scripts\pytest.exe" (
    echo [ERROR] Virtual environment .venv was not found!
    pause
    exit /b 1
)

echo [*] Executing E2E tests with Pytest...
.venv\Scripts\pytest.exe tests/e2e %*

echo.
echo ================================================================================
echo  [*] Execution finished.
echo  [*] To open Allure report with video screencasts run: run_allure_report.bat
echo ================================================================================
pause
