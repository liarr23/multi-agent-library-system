@echo off
chcp 65001 >nul
echo ========================================
echo 多Agent图书管理系统 - 完整启动
echo ========================================
echo.
echo 启动中...
echo.

:: 设置UTF-8环境
set PYTHONIOENCODING=utf-8

:: 启动系统
python 启动完整系统.py

pause
