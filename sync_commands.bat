@echo off
echo Syncing Bishop Bot Discord commands...

REM Check if Python is installed
python --version > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python 3.8 or higher and try again.
    pause
    exit /b 1
)

REM Run the command sync script
python -c "from src.bot.commands import sync_commands; sync_commands.main()"

REM Check for errors
if %ERRORLEVEL% neq 0 (
    echo.
    echo Command sync encountered an error.
    echo Check the logs for more information.
    echo.
) else (
    echo.
    echo Discord commands have been successfully synchronized.
    echo.
)
pause