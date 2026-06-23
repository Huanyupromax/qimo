@echo off
chcp 65001 >nul
title 辩境 - 配置防火墙
echo 正在添加防火墙规则，允许其他设备访问辩论系统...
netsh advfirewall firewall add rule name="辩境服务器" dir=in action=allow protocol=tcp localport=5000 >nul 2>&1
echo [OK] 防火墙规则已添加（如果未提示错误）
echo 其他设备现在可以通过 http://你的IP:5000 访问
echo 查看本机IP请运行 查看IP.bat
timeout /t 5 /nobreak >nul
