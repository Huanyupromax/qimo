@echo off
setlocal enabledelayedexpansion

set PIP_CACHE_DIR=%~dp0.pip_cache
if not exist "%PIP_CACHE_DIR%" mkdir "%PIP_CACHE_DIR%" >nul

title BianJing Installer
chcp 65001 >nul

echo ============================================
echo    BianJing - AI Debate System Installer
echo ============================================
echo.
echo All packages install in project folder (not C drive).
echo.

:choose
echo [1] Lite  - debate + mic + camera + audio (2 min, ~80MB)
echo [2] Full  - + face emotion + voice analysis (15-30 min, ~3GB)
echo.
set /p M="Enter 1 or 2 (default 1): "
if "%M%"=="" set M=1
if not "%M%"=="1" if not "%M%"=="2" goto choose

echo.
echo --- Step 1: Check Python ---
python --version >nul 2>&1
if !errorlevel! neq 0 (
    echo [FAIL] Install Python 3.10+ from python.org first
    pause
    exit /b 1
)
python --version
echo [OK]
echo.

echo --- Step 2: Create virtual env ---
if not exist venv\Scripts\activate.bat (
    python -m venv venv
    if !errorlevel! neq 0 (
        echo [FAIL] Cannot create virtual env
        pause
        exit /b 1
    )
    echo [OK] Virtual env created
) else (
    echo [OK] Virtual env exists
)
echo.

echo --- Step 3: Install ffmpeg (audio/video) ---
where ffmpeg >nul 2>&1
if !errorlevel! equ 0 (
    echo [OK] ffmpeg already installed
) else if exist "%~dp0ffmpeg.exe" (
    echo [OK] ffmpeg found in project folder
) else (
    where npm.cmd >nul 2>&1
    if !errorlevel! equ 0 (
        echo [INFO] Downloading ffmpeg via npm...
        call npm.cmd install @ffmpeg-installer/ffmpeg 2>nul
        if exist "%~dp0node_modules\@ffmpeg-installer\win32-x64\ffmpeg.exe" (
            copy "%~dp0node_modules\@ffmpeg-installer\win32-x64\ffmpeg.exe" "%~dp0ffmpeg.exe" >nul
            rmdir /s /q "%~dp0node_modules" 2>nul
            echo [OK] ffmpeg installed
        ) else (
            echo [WARN] npm failed. Download ffmpeg.exe manually to this folder
        )
    ) else (
        echo [WARN] Node.js not found. Download ffmpeg.exe manually to this folder
    )
)
echo.

echo --- Step 4: Install Python packages ---
call venv\Scripts\activate.bat
python -m pip install --upgrade pip -q

if "%M%"=="1" (
    echo [Lite mode] Installing packages...
    pip install --default-timeout=120 -r requirements.txt
    if !errorlevel! neq 0 (
        pip install -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt
    )
) else (
    echo [Full mode] Installing PyTorch (for deep learning)...
    pip install --default-timeout=300 torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
    if !errorlevel! neq 0 (
        pip install --default-timeout=600 torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
    )
    echo.
    echo [Full mode] Installing all packages (voice + face analysis)...
    pip install --default-timeout=600 -r requirements-full.txt
    if !errorlevel! neq 0 (
        pip install --default-timeout=600 -i https://mirrors.aliyun.com/pypi/simple/ -r requirements-full.txt
    )
)

echo.
echo --- Step 5: Set DeepSeek API Key ---
if exist "%~dp0.env" (
    findstr /B "DEEPSEEK_API_KEY=" "%~dp0.env" >nul 2>&1
    if !errorlevel! equ 0 (
        echo [OK] API Key found in .env
        goto final
    )
)
echo Enter your DeepSeek API Key (get from https://platform.deepseek.com/):
set /p KEY="API Key: "
echo DEEPSEEK_API_KEY=%KEY%> "%~dp0.env"
echo [OK] Saved

:final
echo.
echo ============================================
echo     INSTALLATION COMPLETE!
echo.
echo  To start: double-click start.bat
echo  Then open: http://127.0.0.1:5000
echo.
echo  To share with others:
echo   Just copy this entire folder and run setup.bat
echo   (everything installs from the internet automatically)
echo ============================================
pause
