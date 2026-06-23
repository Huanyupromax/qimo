@echo off
chcp 65001 >nul
title 查看本机IP
echo 本机局域网 IP 地址：
ipconfig | findstr /i "IPv4"
echo.
echo 其他设备可以通过 http://上面显示的IP:5000 访问本机
echo 注意：需要先运行 开放端口.bat 配置防火墙
timeout /t 8 /nobreak >nul
