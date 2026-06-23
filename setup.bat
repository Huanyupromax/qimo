@echo off
title 辩境 - AI辩论系统 安装程序
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================
echo    辩境 - AI 辩论系统 安装程序
echo ============================================
echo.
echo 你需要 DeepSeek API Key 才能使用 AI 辩论功能。
echo 如果还没有，请先申请：https://platform.deepseek.com/
echo.

:choose_mode
echo 请选择安装模式：
echo.
echo [1] 精简安装（核心功能可用：辩论+打分+报告+摄像头+语音）
echo     只需 2 分钟，约 50MB 下载
echo.
echo [2] 完整安装（额外加：面部表情识别+语音深度分析+音频处理）
echo     约 15-30 分钟，需下载约 3GB（安装过程网络要求较高）
echo.
set /p choice="请输入 [1/2]（直接回车默认 1）："
if "%choice%"=="" set choice=1
if "%choice%" neq "1" if "%choice%" neq "2" goto choose_mode

echo.
echo ===== 第 1 步：检测 Python =====
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python！
    echo 请先安装 Python 3.10 或更高版本：
    echo 下载地址：https://www.python.org/downloads/
    echo.
    echo 安装时务必勾选底部 "Add Python to PATH"
    pause
    exit /b 1
)
python --version
echo [OK] Python 检测通过
echo.

echo ===== 第 2 步：创建虚拟环境 =====
if exist venv\Scripts\activate.bat (
    echo [信息] 虚拟环境已存在，跳过创建
) else (
    echo 正在创建虚拟环境（不会占用 C 盘系统空间）...
    python -m venv venv
    if !errorlevel! neq 0 (
        echo [错误] 创建虚拟环境失败
        echo 可能是 Python 安装有问题，尝试修复安装
        pause
        exit /b 1
    )
    echo [OK] 虚拟环境创建成功
)
echo.

echo ===== 第 3 步：安装依赖 =====
call .\venv\Scripts\activate.bat

:: 升级 pip
python -m pip install --upgrade pip -q

if "%choice%"=="1" (
    echo [模式] 精简安装
    echo 正在安装核心依赖（约 2 分钟）...
    pip install --default-timeout=120 -r requirements.txt
    if !errorlevel! neq 0 (
        echo [警告] 下载超时，切换到国内镜像重试...
        pip install -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt
    )
    goto install_done
)

:: ===== 完整安装 =====
echo [模式] 完整安装（含面部/语音分析）
echo.
echo 正在安装 PyTorch（CPU 版，约 5 分钟）...
echo 如果卡住超过 10 分钟，可以关掉重试，完整安装支持断点续传
echo.

pip install --default-timeout=300 torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
if !errorlevel! neq 0 (
    echo [警告] PyTorch 下载失败，重试中（使用国内镜像，可能慢一些）...
    timeout /t 3
    pip install --default-timeout=600 torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
)
if !errorlevel! neq 0 (
    echo [警告] PyTorch 安装失败。你可以：
    echo   1. 检查网络连接
    echo   2. 手动执行：pip install torch torchvision torchaudio
    echo   3. 或者改选精简安装（重新运行 setup.bat）
    echo.
    echo 继续安装其他依赖...
)

echo.
echo 正在安装 TensorFlow + DeepFace（约 8 分钟）...
echo 这是最大的组件，约 500MB，请耐心等待...
pip install --default-timeout=600 deepface
if !errorlevel! neq 0 (
    echo [重试] 使用国内镜像...
    pip install --default-timeout=600 -i https://mirrors.aliyun.com/pypi/simple/ deepface
)

echo.
echo 正在安装其余依赖（librosa + funasr + 工具包）...
pip install --default-timeout=300 -r requirements-full.txt
if !errorlevel! neq 0 (
    echo [重试] 使用国内镜像...
    pip install --default-timeout=600 -i https://mirrors.aliyun.com/pypi/simple/ -r requirements-full.txt
)

:install_done
echo.
echo ============================================
echo           安装完成！
echo ============================================
echo.
echo 下一步操作：
echo.
echo   [1] 设置 API Key
echo       用记事本打开项目里的 .env 文件
echo       将 DEEPSEEK_API_KEY=你的DeepSeek密钥
echo       改为 DEEPSEEK_API_KEY=sk-你的实际key
echo.
echo   [2] 启动系统
echo       双击 start.bat
echo.
echo   [3] 使用
echo       浏览器打开 http://127.0.0.1:5000
echo.
echo ============================================
pause
