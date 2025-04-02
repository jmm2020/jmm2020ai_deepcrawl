@echo off
setlocal enabledelayedexpansion

echo Crawl4AI - Available JSON Result Files
echo ======================================
echo.

set "results_dir=..\results"
set "count=0"
set "found=false"

REM Check if results directory exists
if not exist "%results_dir%" (
  echo Results directory not found. No JSON files available.
  echo.
  pause
  goto :EOF
)

REM Look for JSON files in the results directory
echo Available crawl result files:
echo.
echo   ID    Date         Time     Size(KB)  Filename
echo   --------------------------------------------------

REM Loop through all JSON files in the results directory
for /f "tokens=*" %%F in ('dir /b /od "%results_dir%\crawl*.json" 2^>nul') do (
  set /a "count+=1"
  set "found=true"
  
  REM Get file size
  for %%S in ("%results_dir%\%%F") do set "size=%%~zS"
  set /a "size_kb=!size! / 1024"
  
  REM Extract timestamp from filename
  set "filename=%%F"
  if "!filename:~0,13!"=="crawl_results_" (
    set "timestamp=!filename:~13,15!"
    set "date=!timestamp:~0,8!"
    set "time=!timestamp:~9,6!"
    
    REM Format date and time
    set "formatted_date=!date:~0,4!-!date:~4,2!-!date:~6,2!"
    set "formatted_time=!time:~0,2!:!time:~2,2!:!time:~4,2!"
  ) else (
    set "formatted_date=Unknown"
    set "formatted_time=Unknown"
  )
  
  REM Display file information
  echo   !count!    !formatted_date! !formatted_time! !size_kb!       %%F
)

REM If no files were found
if not "!found!"=="true" (
  echo   No JSON result files found in the results directory.
)

echo.
echo To import a file into Supabase:
echo import_json_to_supabase.bat results\filename.json
echo.

pause 