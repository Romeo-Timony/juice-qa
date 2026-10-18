@echo off
setlocal
chcp 65001 > nul
title [QA Automation] Backend API Tests
cd /d "%~dp0"

echo ================================================================================
echo  [QA AUTOMATION] BACKEND API TESTS (Requests + Pydantic v2)
echo  Target: tests/backend/
echo ================================================================================
echo.

if not exist ".venv\Scripts\pytest.exe" (
    echo [ERROR] Virtual environment .venv was not found!
    echo Please install dependencies: .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

echo [*] Executing backend tests with Pytest...
.venv\Scripts\pytest.exe tests/backend %*

echo.
echo ================================================================================
echo  [*] Execution finished.
echo  [*] To open Allure report run: run_allure_report.bat
echo ================================================================================
pause
