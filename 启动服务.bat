@echo off
chcp 65001 > nul 2>&1
echo 正在启动多Agent图书管理系统...
cd /d "C:\Users\liar\miclaw\project\multi-agent-library-system"
python run.py
pause