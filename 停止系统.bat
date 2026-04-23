@echo off
chcp 65001 >nul
echo ========================================
echo 正在停止多Agent图书管理系统...
echo ========================================
echo.

:: 停止所有Python进程
taskkill /f /im python.exe >nul 2>&1

echo.
echo 系统已停止！
echo.
pause