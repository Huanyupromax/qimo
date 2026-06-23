@echo off
title 辩境 - AI辩论系统 安装程序
echo ============================================
echo    辩境 - AI 辩论系统 安装程序
echo ============================================
echo.
echo 正在检测 Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装 Python 3.10+
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Python 检测通过
echo.
echo 正在创建虚拟环境(不占用 C 盘)...
if exist venv (
    echo [信息] 虚拟环境已存在，跳过创建
) else (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [错误] 创建虚拟环境失败
        pause
        exit /b 1
    )
    echo [OK] 虚拟环境创建成功
)
echo.
echo 正在安装依赖(第一次安装约 10-20 分钟)...

call .\venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul 2>&1
python -m pip install --default-timeout=300 torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
python -m pip install --default-timeout=300 -r requirements-full.txt

if %errorlevel% neq 0 (
    echo.
    echo [警告] 部分依赖安装可能超时，尝试备用镜像...
    python -m pip install --default-timeout=300 -i https://mirrors.aliyun.com/pypi/simple/ -r requirements-full.txt
)
echo.
echo ============================================
echo    安装完成！
echo    双击 start.bat 即可启动辩论系统
echo ============================================
pause
