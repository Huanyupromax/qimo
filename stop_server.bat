@echo off
title 停止辩境服务器
echo 正在停止辩论系统服务器...
taskkill /f /fi "WINDOWTITLE eq 辩境*" 2>nul
timeout /t 2 /nobreak >nul
