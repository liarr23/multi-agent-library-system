@echo off
chcp 65001 >nul
echo ========================================
echo 多Agent图书管理系统
echo ========================================
echo.
echo 后端地址: http://localhost:8000
echo API文档: http://localhost:8000/docs
echo 前端地址: http://localhost:3000
echo.
echo 按 Ctrl+C 停止所有服务
echo ========================================
echo.

:: 启动后端
start "后端服务" cmd /k "cd /d %~dp0 && python run.py"

:: 等待后端启动
timeout /t 3 /nobreak >nul

:: 启动前端
start "前端服务" cmd /k "cd /d %~dp0\frontend && python server.py"

echo.
echo 系统已启动！
echo 请访问 http://localhost:3000 使用系统
echo.
pause