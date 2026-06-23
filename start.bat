@echo off
cd /d "%~dp0"
title 辩境 - AI辩论系统
echo ============================================
echo    辩境 - AI 辩论系统 启动中...
echo ============================================
echo.
if not exist venv\Scripts\python.exe (
    echo [错误] 未找到虚拟环境，请先运行 setup.bat
    pause
    exit /b 1
)
if not exist .env (
    copy .env.example .env >nul 2>&1
    echo [提示] 已创建 .env 文件
    echo 请用记事本打开 .env 文件，将密钥改为你的 DeepSeek Key
    pause
    exit /b 1
)
echo [1/3] 正在启动服务器...
echo [2/3] 浏览器访问: http://127.0.0.1:5000
echo [3/3] 请勿关闭本窗口
echo.
"%~dp0venv\Scripts\python.exe" app.py
echo.
echo [信息] 服务器已停止
pause
