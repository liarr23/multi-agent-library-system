#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多Agent图书管理系统 - 完整启动脚本
解决依赖问题并启动所有服务
"""
import os
import sys
import time
import subprocess
import threading

# 设置UTF-8编码
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def check_and_install_deps():
    """检查并安装依赖"""
    print("📦 检查依赖...")
    
    required_packages = [
        "fastapi",
        "uvicorn[standard]",
        "sqlalchemy",
        "pydantic",
        "python-multipart",
        "requests"
    ]
    
    for package in required_packages:
        try:
            # 处理特殊包名
            import_name = package.split("[")[0].replace("-", "_")
            if import_name == "pydantic":
                import_name = "pydantic"
            __import__(import_name)
        except ImportError:
            print(f"  安装 {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q"])
    
    print("✅ 依赖检查完成")

def init_database():
    """初始化数据库"""
    print("🗄️  初始化数据库...")
    
    db_path = os.path.join(os.path.dirname(__file__), "library.db")
    
    # 如果数据库已存在，跳过初始化
    if os.path.exists(db_path):
        print("  数据库已存在，跳过初始化")
        return
    
    # 运行初始化脚本
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        from app.database import init_db
        from app.models import book, user, borrow_record
        init_db()
        print("  数据库初始化完成")
    except Exception as e:
        print(f"  ⚠️ 数据库初始化警告: {e}")
        print("  将在首次使用时自动创建")

def start_backend():
    """启动后端服务"""
    print("\n🚀 启动后端服务...")
    print("   地址: http://localhost:8000")
    print("   文档: http://localhost:8000/docs")
    
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # 使用uvicorn启动
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ])

def test_backend():
    """测试后端服务"""
    import requests
    
    print("\n🧪 测试后端服务...")
    
    max_retries = 10
    for i in range(max_retries):
        try:
            response = requests.get("http://localhost:8000/health", timeout=2)
            if response.status_code == 200:
                print("✅ 后端服务启动成功!")
                return True
        except:
            if i < max_retries - 1:
                print(f"  等待后端启动... ({i+1}/{max_retries})")
                time.sleep(1)
            else:
                print("❌ 后端服务启动超时")
                return False
    return False

def show_menu():
    """显示启动菜单"""
    print("\n" + "=" * 60)
    print("📚 多Agent图书管理系统")
    print("=" * 60)
    print()
    print("系统组件:")
    print("  • 后端API服务 (FastAPI)")
    print("  • 多Agent协调器")
    print("  • SQLite数据库")
    print()
    print("访问地址:")
    print("  • 后端API: http://localhost:8000")
    print("  • API文档: http://localhost:8000/docs")
    print("  • ReDoc文档: http://localhost:8000/redoc")
    print()
    print("API端点:")
    print("  • GET  /              - 系统信息")
    print("  • GET  /health        - 健康检查")
    print("  • GET  /api/books     - 图书列表")
    print("  • GET  /api/agents/status - Agent状态")
    print("  • POST /api/agents/test/search - 测试搜索")
    print()
    print("=" * 60)
    print("按 Ctrl+C 停止服务")
    print("=" * 60)

def main():
    """主函数"""
    show_menu()
    
    # 检查依赖
    check_and_install_deps()
    
    # 初始化数据库
    init_database()
    
    # 启动后端
    start_backend()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 服务已停止")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)