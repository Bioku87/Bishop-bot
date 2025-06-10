@echo off
echo Creating Bishop project structure on desktop...

set BISHOP_DIR=%USERPROFILE%\Desktop\Bishop

REM Create main folder
mkdir "%BISHOP_DIR%"

REM Create data directory and subdirectories
mkdir "%BISHOP_DIR%\data"
mkdir "%BISHOP_DIR%\data\characters"
mkdir "%BISHOP_DIR%\data\voice"
mkdir "%BISHOP_DIR%\data\voice\profiles"
mkdir "%BISHOP_DIR%\data\voice\samples"
mkdir "%BISHOP_DIR%\data\voice\sessions"
mkdir "%BISHOP_DIR%\data\audio"
mkdir "%BISHOP_DIR%\data\audio\soundboard"
mkdir "%BISHOP_DIR%\data\audio\soundboard\Default"
mkdir "%BISHOP_DIR%\data\audio\soundboard\Combat"
mkdir "%BISHOP_DIR%\data\exports"
mkdir "%BISHOP_DIR%\data\temp"

REM Create logs directory
mkdir "%BISHOP_DIR%\logs"

REM Create src directory and subdirectories
mkdir "%BISHOP_DIR%\src"
mkdir "%BISHOP_DIR%\src\bot"
mkdir "%BISHOP_DIR%\src\bot\commands"
mkdir "%BISHOP_DIR%\src\characters"
mkdir "%BISHOP_DIR%\src\database"
mkdir "%BISHOP_DIR%\src\voice"

REM Create assets directory
mkdir "%BISHOP_DIR%\assets"
mkdir "%BISHOP_DIR%\assets\images"

echo Bishop project structure has been created on your desktop.
echo You can now start adding files to the structure.
pause