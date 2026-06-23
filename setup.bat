@echo off
title 辩境 - AI辩论系统 安装程序
chcp 65001 >nul

echo ============================================
echo    辩境 - AI 辩论系统 安装程序
echo ============================================
echo.
echo 你需要 DeepSeek API Key 才能使用 AI 辩论功能。
echo 如果还没有，请先申请：https://platform.deepseek.com/
echo.
echo [1] 精简安装（核心功能：辩论 + 打分 + 报告，约 2 分钟）
echo [2] 完整安装（全部功能 + 面部/语音分析，约 15 分钟）
echo.
set /p choice="请选择 [1/2]（默认 1）："
if "%choice%"=="" set choice=1

echo.
echo 检测 Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python！请先安装 Python 3.10+：
    echo 下载：https://www.python.org/downloads/
    echo 安装时记得勾选 "Add Python to PATH"
    pause
    exit /b 1
)
python --version
echo [OK] Python 检测通过
echo.

echo 创建虚拟环境...
if exist venv (
    echo [信息] 虚拟环境已存在，跳过
) else (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [错误] 创建虚拟环境失败
        pause
        exit /b 1
    )
    echo [OK] 虚拟环境创建成功
)

call .\venv\Scripts\activate.bat
python -m pip install --upgrade pip -q

if "%choice%"=="2" (
    echo.
    echo 安装完整依赖（含面部/语音分析），需要下载约 3GB...
    echo 如果下载慢可以按 Ctrl+C 取消，改选精简安装
    timeout /t 3
    python -m pip install --default-timeout=300 torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
    python -m pip install --default-timeout=300 -r requirements-full.txt
) else (
    echo 安装核心依赖...
    python -m pip install --default-timeout=300 -r requirements.txt
    if !errorlevel! neq 0 (
        echo [警告] 下载慢，换国内镜像重试...
        python -m pip install -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt
    )
)

echo.
echo ============================================
echo    安装完成！
echo.
echo  下一步：
echo    1. 在项目文件夹新建 .env 文件
echo       写入：DEEPSEEK_API_KEY=你的key
echo    2. 双击 start.bat 启动
echo    3. 浏览器打开 http://127.0.0.1:5000
echo ============================================
pause
