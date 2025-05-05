@echo off
:: Chrome CDP Launcher (Reuses existing user profile)
:: Chrome Path: C:\Program Files\Google\Chrome\Application\chrome.exe

setlocal enabledelayedexpansion

:: Configure paths
set "CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe"
set DEFAULT_PORT=9222
set "DEFAULT_DATA_DIR=%LOCALAPPDATA%\Google\Chrome\User Data"

:: Verify Chrome exists
if not exist "%CHROME_PATH%" (
    echo [ERROR] Chrome not found at:
    echo %CHROME_PATH%
    pause
    exit /b 1
)

:: Get command line arguments
set PORT=%1
if "%PORT%"=="" set PORT=%DEFAULT_PORT%
set DATA_DIR=%2
if "%DATA_DIR%"=="" set DATA_DIR=%DEFAULT_DATA_DIR%

:: Verify profile directory exists
if not exist "%DATA_DIR%" (
    echo [ERROR] Profile directory not found:
    echo %DATA_DIR%
    pause
    exit /b 1
)

:: Display launch info
echo.
echo ====================================
echo  Chrome CDP Launcher (Port: %PORT%)
echo  Using profile: %DATA_DIR%
echo ====================================
echo.
echo Chrome Path: %CHROME_PATH%
echo Debug URL: http://localhost:%PORT%/json/version
echo.

:: Launch Chrome with existing profile
start "" "%CHROME_PATH%" ^
    --remote-debugging-port=%PORT% ^
    --user-data-dir="%DATA_DIR%" ^
    --no-first-run ^
    --no-default-browser-check

:: Wait for Chrome to initialize
timeout /t 2 >nul

:: Usage instructions
echo.
echo [Important Notes]
echo 1. Using Chrome's default profile directory
echo 2. Closing this window won't terminate Chrome
echo 3. To kill manually: taskkill /f /im chrome.exe
echo.

pause