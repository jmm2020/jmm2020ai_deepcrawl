@echo off
setlocal enabledelayedexpansion

echo Crawl4AI JSON to Supabase Import Tool
echo ====================================
echo.

REM Check if list command was specified
if "%~1"=="list" (
  call list_crawl_results.bat
  goto :EOF
)

REM Check if a file was provided
if "%~1"=="" (
  echo No JSON file specified.
  echo.
  echo Usage: 
  echo   import_json_to_supabase.bat path\to\file.json [batch_size] [retry_count] [delay]
  echo   import_json_to_supabase.bat list
  echo.
  echo Examples:
  echo   import_json_to_supabase.bat results\crawl_results_20250402_123456.json
  echo   import_json_to_supabase.bat results\crawl_results_20250402_123456.json 20 5 2
  echo   import_json_to_supabase.bat list
  echo.
  echo Parameters:
  echo   file.json    - Path to the JSON file to import
  echo   batch_size   - Number of records to process in each batch (default: 10)
  echo   retry_count  - Number of retries for failed insertions (default: 3)
  echo   delay        - Delay in seconds between batches (default: 1.0)
  echo.
  echo Commands:
  echo   list         - List all available JSON result files
  echo.
  goto :EOF
)

REM Parse arguments
set "json_file=%~1"
set "batch_size=10"
set "retry_count=3"
set "delay=1.0"

REM Check for additional arguments
if not "%~2"=="" set "batch_size=%~2"
if not "%~3"=="" set "retry_count=%~3"
if not "%~4"=="" set "delay=%~4"

REM Verify file exists
if not exist "%json_file%" (
  echo Error: File not found - %json_file%
  goto :EOF
)

echo File:        %json_file%
echo Batch Size:  %batch_size%
echo Retry Count: %retry_count%
echo Delay:       %delay% seconds
echo.
echo Starting import process...
echo.

REM Navigate to workbench directory and run the Python script
cd ..
python scripts/process_json_to_supabase.py --input "%json_file%" --batch_size %batch_size% --retry_count %retry_count% --delay %delay%

REM Check exit code
if %ERRORLEVEL% EQU 0 (
  echo.
  echo Import completed successfully!
) else if %ERRORLEVEL% EQU 1 (
  echo.
  echo Import completed with partial success.
) else (
  echo.
  echo Import failed!
)

echo.
pause 