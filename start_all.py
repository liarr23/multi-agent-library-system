"""
一键启动脚本 - 同时启动后端和前端服务
"""
import subprocess
import sys
import os
import time
import threading

def start_backend():
    """启动后端服务"""
    print("🚀 启动后端服务...")
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    subprocess.run([sys.executable, "run.py"])

def start_frontend():
    """启动前端服务"""
    print("🌐 启动前端服务...")
    time.sleep(2)  # 等待后端启动
    frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
    os.chdir(frontend_dir)
    subprocess.run([sys.executable, "server.py"])

if __name__ == "__main__":
    print("=" * 50)
    print("多Agent图书管理系统")
    print("=" * 50)
    print()
    print("后端地址: http://localhost:8000")
    print("API文档: http://localhost:8000/docs")
    print("前端地址: http://localhost:3000")
    print()
    print("按 Ctrl+C 停止所有服务")
    print("=" * 50)
    
    # 启动后端线程
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()
    
    # 启动前端线程
    frontend_thread = threading.Thread(target=start_frontend, daemon=True)
    frontend_thread.start()
    
    try:
        # 保持主线程运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n👋 正在停止所有服务...")
        sys.exit(0)
