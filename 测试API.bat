@echo off
chcp 65001 > nul 2>&1
echo ========================================
echo   多Agent图书管理系统 - API文档
echo ========================================
echo.
echo 启动后，请在浏览器中访问：
echo   http://localhost:8000/docs
echo.
echo 按任意键测试API连接...
pause > nul
echo.
echo 测试健康检查...
curl -s http://localhost:8000/health
echo.
echo.
echo 测试图书列表...
curl -s http://localhost:8000/api/books/
echo.
echo.
echo 按任意键退出...
pause > nul