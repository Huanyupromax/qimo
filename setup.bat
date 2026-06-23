@echo off
setlocal enabledelayedexpansion
title BianJing Installer
chcp 65001 >nul

echo ============================================
echo    BianJing - AI Debate System Installer
echo ============================================
echo.
echo You need a DeepSeek API Key.
echo Get one: https://platform.deepseek.com/
echo.

:choose
echo.
echo [1] Lite  - debate + scoring + report + camera
echo [2] Full  - + face emotion + voice analysis
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

echo --- Step 3: Install packages ---
call venv\Scripts\activate.bat
python -m pip install --upgrade pip -q

if "%M%"=="1" (
    echo [Lite mode] Installing...
    pip install --default-timeout=120 -r requirements.txt
    if !errorlevel! neq 0 (
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
echo [Full mode] Installing DeepFace + TensorFlow...
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
echo     DONE! Next steps:
echo.
echo  1. Open .env file, set DEEPSEEK_API_KEY
echo  2. Double-click start.bat
echo  3. Open http://127.0.0.1:5000
echo ============================================
pause
