@echo off
echo Installing Bishop Bot Voice Dependencies...

REM Check if Python is installed
python --version > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python 3.8 or higher and try again.
    pause
    exit /b 1
)

REM Check if pip is installed
pip --version > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: pip is not installed or not in PATH.
    echo Please make sure pip is properly installed with Python.
    pause
    exit /b 1
)

REM Install ffmpeg if needed
echo Checking for ffmpeg...
where ffmpeg > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo FFmpeg not found. Attempting to install...
    
    REM Try to install using pip
    pip install ffmpeg-python
    
    REM Inform about manual installation if needed
    echo.
    echo If FFmpeg still doesn't work after this installation,
    echo please download it manually from https://ffmpeg.org/download.html
    echo and add it to your system PATH.
    echo.
)

REM Install voice recognition dependencies
echo Installing voice recognition packages...
pip install SpeechRecognition==3.10.0
pip install google-cloud-speech==2.20.0
pip install azure-cognitiveservices-speech==1.29.0
pip install PyAudio==0.2.13

REM Install audio processing dependencies
echo Installing audio processing packages...
pip install PyNaCl==1.5.0
pip install pydub==0.25.1
pip install yt-dlp==2023.7.6

echo.
echo Voice dependencies installation complete.
echo.
echo If you encounter any issues, please try installing the packages
echo manually or check the documentation for more details.
pause