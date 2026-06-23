@echo off
title 辩境 - 后台静默启动
echo 正在启动辩论系统服务器(后台模式)...
echo 启动后浏览器访问: http://127.0.0.1:5000
echo 关闭本窗口不影响服务器运行
echo.
cd /d "%~dp0"
start /min cmd /c "title 辩境服务器 && .\venv\Scripts\python.exe -X utf8 app.py"
echo 服务器已在后台启动，等待15秒后可用...
echo.
echo 如需停止服务器，请运行 stop_server.bat
echo.
timeout /t 5 /nobreak >nul
start http://127.0.0.1:5000
