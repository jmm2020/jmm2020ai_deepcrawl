@echo off
setlocal EnableDelayedExpansion

if not "%1"=="silent" (
    echo Stopping Crawl4AI servers...
    echo ======================================
)

REM Stop any API server processes
if not "%1"=="silent" echo Stopping API server processes...
taskkill /F /FI "WINDOWTITLE eq *Crawl4AI API Server*" /IM python.exe >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq *api_bridge*" /IM python.exe >nul 2>nul
if %ERRORLEVEL% equ 0 (
    if not "%1"=="silent" echo Successfully terminated API server processes
) else (
    if not "%1"=="silent" echo No running API server processes found
)

REM Stop any frontend server processes
if not "%1"=="silent" echo Stopping web frontend processes...
taskkill /F /FI "WINDOWTITLE eq *Crawl4AI Frontend*" /IM node.exe >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq *next*" /IM node.exe >nul 2>nul
if %ERRORLEVEL% equ 0 (
    if not "%1"=="silent" echo Successfully terminated frontend server processes
) else (
    if not "%1"=="silent" echo No running frontend server processes found
)

if not "%1"=="silent" (
    echo ======================================
    echo All servers have been stopped.
    echo ======================================
    pause
) 