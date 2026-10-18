@echo off
setlocal
chcp 65001 > nul
title [QA Automation] Full Test Suite (Frontend + Backend)
cd /d "%~dp0"

echo ================================================================================
echo  [QA AUTOMATION] FULL REGRESSION SUITE (Frontend UI + Backend API)
echo  Targets: tests/backend/ and tests/frontend/
echo ================================================================================
echo.

if not exist ".venv\Scripts\pytest.exe" (
    echo [ERROR] Virtual environment .venv was not found!
    pause
    exit /b 1
)

echo [*] Executing all tests with Pytest...
.venv\Scripts\pytest.exe tests/frontend tests/backend %*

echo.
echo ================================================================================
echo  [*] Execution finished.
echo  [*] To open Allure report run: run_allure_report.bat
echo ================================================================================
pause
