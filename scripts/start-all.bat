@echo off
setlocal EnableDelayedExpansion

echo Starting Crawl4AI API Server and Frontend...
echo ======================================
echo Crawl4AI Development Environment
echo ======================================
echo API Server: http://localhost:1111
echo Web UI: http://localhost:3112/crawler

REM Stop any existing servers
echo Stopping any existing servers...
call "%~dp0stop-all.bat" silent

REM Start the API server
echo Starting API server...
start "Crawl4AI API Server" cmd /c "cd %~dp0..\api && python api_bridge.py"

REM Wait for the API server to start
timeout /t 3 > nul

REM Start the web frontend
echo Starting web frontend...
start "Crawl4AI Frontend" cmd /c "cd %~dp0..\frontend && npm run dev -- -p 3112"

echo ======================================
echo Servers are starting in separate terminal windows.
echo Close this window when you're done to shut everything down.
echo IMPORTANT: Database insertion may not be working correctly.
echo Crawler will save data to local JSON files but may fail to
echo insert into the database.
echo ======================================

if not "%1"=="silent" pause 