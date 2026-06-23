@echo off
title 辩境 - 配置防火墙
echo 正在添加防火墙规则，允许其他设备访问辩论系统...
netsh advfirewall firewall add rule name="辩境服务器" dir=in action=allow protocol=TCP localport=5000
if %errorlevel% equ 0 (
    echo.
    echo [OK] 防火墙规则已添加！
    echo.
    echo 局域网其他设备请访问: http://192.168.0.10:5000
    echo.
    echo 如果换了网络，IP 可能变化，请重新查看 IP
) else (
    echo.
    echo [失败] 请右键以管理员身份运行本文件
)
pause
