@echo off
setlocal
chcp 65001 > nul
title [QA Automation] Unit Tests (Framework Self-Testing)
cd /d "%~dp0"

echo ================================================================================
echo  [QA AUTOMATION] UNIT TESTS (Framework Self-Testing ^<10ms, No Network)
echo  Target: tests/unit/
echo ================================================================================
echo.

if not exist ".venv\Scripts\pytest.exe" (
    echo [ERROR] Virtual environment .venv was not found!
    pause
    exit /b 1
)

echo [*] Executing unit tests with Pytest...
.venv\Scripts\pytest.exe tests/unit %*

echo.
echo ================================================================================
echo  [*] Execution finished.
echo ================================================================================
pause
