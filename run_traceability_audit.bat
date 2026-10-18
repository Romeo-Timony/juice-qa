@echo off
setlocal
chcp 65001 > nul
title [QA Automation] Qase TMS Traceability Audit
cd /d "%~dp0"

echo ================================================================================
echo  [QA AUTOMATION] TRACEABILITY AUDIT: QASE TMS ^<--^> CODEBASE
echo ================================================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment .venv was not found!
    pause
    exit /b 1
)

.venv\Scripts\python.exe sync_qase_tests.py

echo.
pause
