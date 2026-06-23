@echo off
chcp 65001 >nul
title 辩境 - AI辩论系统
echo ============================================
echo    辩境 - AI 辩论系统 启动中...
echo ============================================
echo.
:: Check virtual env
if not exist venv\Scripts\activate.bat (
    echo [错误] 未找到虚拟环境，请先运行 setup.bat
    pause
    exit /b 1
)
:: Check .env
if not exist .env (
    echo DEEPSEEK_API_KEY=你的DeepSeek密钥 > .env
    echo [提示] 请编辑 .env 文件填入 DeepSeek API Key
    echo.
)
:: Start
call .\venv\Scripts\activate.bat
echo [信息] 启动辩论系统...
echo [信息] 浏览器访问: http://127.0.0.1:5000
echo [信息] 按 Ctrl+C 停止服务
echo.
python app.py
pause
