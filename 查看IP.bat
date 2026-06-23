@echo off
title 辩境 - 查看本机IP
echo ============================================
echo   辩境 - 查看本机局域网IP
echo ============================================
echo.
for /f "tokens=2 delims=:" %%i in ('ipconfig ^| findstr /i "IPv4"') do (
    echo   http://%%i:5000
)
echo.
echo 把上面的地址发给同一个Wi-Fi下的设备即可访问
echo.
pause
