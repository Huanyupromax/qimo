@echo off
title 停止辩境服务器
echo 正在停止辩论系统服务器...
taskkill /f /im python.exe 2>nul
echo 服务器已停止。
timeout /t 2 /nobreak >nul
