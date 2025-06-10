@echo off
title Bishop Bot Launcher

REM Configuration
set PYTHON_CMD=python
set MAIN_SCRIPT=src\main.py
set VENV_DIR=venv
set LOG_DIR=logs
set DATA_DIR=data

echo Bishop Bot Launcher
echo ==================
echo Current Date and Time: %date% %time%
echo.

REM Create required directories
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"
if not exist "%DATA_DIR%\characters" mkdir "%DATA_DIR%\characters"
if not exist "%DATA_DIR%\voice\profiles" mkdir "%DATA_DIR%\voice\profiles"
if not exist "%DATA_DIR%\voice\samples" mkdir "%DATA_DIR%\voice\samples"
if not exist "%DATA_DIR%\voice\sessions" mkdir "%DATA_DIR%\voice\sessions"
if not exist "%DATA_DIR%\audio\soundboard\Default" mkdir "%DATA_DIR%\audio\soundboard\Default"
if not exist "%DATA_DIR%\audio\soundboard\Combat" mkdir "%DATA_DIR%\audio\soundboard\Combat"
if not exist "%DATA_DIR%\exports" mkdir "%DATA_DIR%\exports"
if not exist "%DATA_DIR%\temp" mkdir "%DATA_DIR%\temp"

REM Check if Python is installed
%PYTHON_CMD% --version > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.9 or newer and make sure it's in your PATH.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if exist "%VENV_DIR%\Scripts\activate.bat" (
    echo Activating virtual environment...
    call "%VENV_DIR%\Scripts\activate.bat"
    echo Virtual environment activated.
) else (
    echo No virtual environment found. Using system Python.
    echo To create a virtual environment, run: python -m venv venv
)

REM Check for essential files
if not exist "%MAIN_SCRIPT%" (
    echo ERROR: Main script not found: %MAIN_SCRIPT%
    echo Please make sure you're running this from the Bishop project root directory.
    pause
    exit /b 1
)

REM Check if .env file exists - FIXED VERSION
if not exist ".env" (
    echo WARNING: No .env file found.
    echo Creating a template .env file. Please edit it with your credentials.
    
    REM Write template .env file with > to create/overwrite instead of >> to append
    (
        echo # Bishop Bot Configuration
        echo # Created on: %date% %time%
        echo.
        echo # Discord Bot Token (KEEP SECRET!)
        echo DISCORD_TOKEN=your_discord_token_here
        echo.
        echo # Voice API Keys
        echo VOICE_API_KEY=your_voice_api_key_here
        echo ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
        echo VOICE_REGION=us-east-1
        echo.
        echo # Database configuration
        echo DB_TYPE=sqlite
        echo DB_PATH=data/bishop.db
        echo.
        echo # Logging
        echo LOG_LEVEL=INFO
        echo.
        echo # Optional: OpenAI API Key for advanced features
        echo OPENAI_API_KEY=
    ) > .env
    
    echo Created template .env file. Please edit it with your API keys.
    echo Press any key to continue...
    pause > nul
)

echo Checking if tkinter is available...
%PYTHON_CMD% -c "import tkinter; print('Tkinter version:', tkinter.TkVersion)" || (
    echo ERROR: Tkinter is not available. Control window will not work.
    echo On Windows, reinstall Python and make sure to check "tcl/tk and IDLE" during installation.
    echo Press any key to continue anyway...
    pause > nul
)

echo Starting Bishop Bot...
echo.

REM IMPORTANT: Launch the bot without redirecting stderr so we can see errors immediately
%PYTHON_CMD% -u "%MAIN_SCRIPT%"

REM Check for errors
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Bishop Bot exited with error code %ERRORLEVEL%.
) else (
    echo.
    echo Bishop Bot has exited normally.
)

REM If using virtual environment, deactivate it
if exist "%VENV_DIR%\Scripts\activate.bat" (
    call deactivate
)

echo.
echo Press any key to exit...
pause > nul