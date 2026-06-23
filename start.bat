@echo off
chcp 65001 >nul
title 辩境 - AI辩论系统
echo ============================================
echo    辩境 - AI 辩论系统 启动中...
echo ============================================
echo.
if not exist venv\Scripts\activate.bat (
    echo [错误] 未找到虚拟环境，请先运行 setup.bat
    pause
    exit /b 1
)
if not exist .env (
    copy .env.example .env >nul 2>&1
    echo [提示] 已创建 .env 文件
    echo 请用记事本打开 .env 文件
    echo 将 DEEPSEEK_API_KEY 改为你的 DeepSeek API Key
    echo 然后重新运行 start.bat
    echo.
    pause
    exit /b 1
)
call .\venv\Scripts\activate.bat
echo [信息] 启动辩论系统...
echo [信息] 浏览器访问: http://127.0.0.1:5000
echo [信息] 按 Ctrl+C 停止服务
echo.
python app.py
pause
