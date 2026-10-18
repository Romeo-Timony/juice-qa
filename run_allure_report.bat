@echo off
setlocal
chcp 65001 > nul
title [QA Automation] Allure Test Report
cd /d "%~dp0"

echo ================================================================================
echo  [QA AUTOMATION] ALLURE TEST REPORT GENERATOR
echo  Source: allure-results/
echo ================================================================================
echo.

if not exist "allure-results" (
    echo [WARN] Directory allure-results does not exist yet. Please run tests first!
    pause
    exit /b 1
)

echo [*] Launching Allure web server... (Press Ctrl+C to stop)
allure serve allure-results
pause
