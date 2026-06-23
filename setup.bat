@echo off
setlocal enabledelayedexpansion

:: Redirect pip cache to project folder (not C drive)
set PIP_CACHE_DIR=%~dp0.pip_cache
if not exist "%PIP_CACHE_DIR%" mkdir "%PIP_CACHE_DIR%" >nul

title BianJing Installer
chcp 65001 >nul

echo ============================================
echo    BianJing - AI Debate System Installer
echo ============================================
echo.
echo You need a DeepSeek API Key.
echo Get one: https://platform.deepseek.com/
echo.
echo All packages will be installed in the project folder.
echo No C drive space will be used.
echo.

:choose
echo [1] Lite  - debate + scoring + report + camera (2 min, ~50MB)
echo [2] Full  - + face emotion + voice analysis (15-30 min, ~3GB)
echo.
set /p M="Enter 1 or 2 (default 1): "
if "%M%"=="" set M=1
if not "%M%"=="1" if not "%M%"=="2" goto choose

echo.
echo --- Step 1: Check Python ---
python --version >nul 2>&1
if !errorlevel! neq 0 (
    echo [FAIL] Python not found. Install Python 3.10+ first.
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo [OK]
echo.

echo --- Step 2: Create virtual env in project folder ---
if not exist venv\Scripts\activate.bat (
    python -m venv venv
    if !errorlevel! neq 0 (
        echo [FAIL] Cannot create virtual env
        pause
        exit /b 1
    )
    echo [OK] Virtual env created at .\venv\ (not on C drive)
) else (
    echo [OK] Virtual env exists
)
echo.

echo --- Step 3: Install packages (downloading to .\pip_cache\) ---
call venv\Scripts\activate.bat
python -m pip install --upgrade pip -q

if "%M%"=="1" (
    echo [Lite mode] Installing core packages...
    pip install --default-timeout=120 -r requirements.txt
    if !errorlevel! neq 0 (
        echo [RETRY] Using China mirror...
        pip install -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt
    )
    goto done
)

echo [Full mode] Installing PyTorch...
pip install --default-timeout=300 torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
if !errorlevel! neq 0 (
    timeout /t 3
    pip install --default-timeout=600 torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
)

echo.
echo [Full mode] Installing DeepFace + TensorFlow (~500MB)...
pip install --default-timeout=600 deepface
if !errorlevel! neq 0 (
    pip install --default-timeout=600 -i https://mirrors.aliyun.com/pypi/simple/ deepface
)

echo.
echo [Full mode] Installing audio packages...
pip install --default-timeout=300 -r requirements-full.txt
if !errorlevel! neq 0 (
    pip install --default-timeout=600 -i https://mirrors.aliyun.com/pypi/simple/ -r requirements-full.txt
)

:done
echo.
echo ============================================
echo     DONE!
echo.
echo  Packages installed in: .\venv\
echo  Download cache in:     .\pip_cache\ (can delete after install)
echo.
echo  Next steps:
echo   1. Open .env, set DEEPSEEK_API_KEY
echo   2. Double-click start.bat
echo   3. Open http://127.0.0.1:5000
echo ============================================
pause
