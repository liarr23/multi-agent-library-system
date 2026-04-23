#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动并验证多Agent系统
"""
import subprocess
import sys
import time
import os

def main():
    print("=" * 60)
    print("多Agent图书管理系统 - 启动验证")
    print("=" * 60)
    
    # 获取项目目录
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    
    # 启动后端服务
    print("\n[1] 启动后端服务...")
    print("    地址: http://localhost:8000")
    print("    文档: http://localhost:8000/docs")
    
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # 等待服务启动
    print("\n[2] 等待服务启动...")
    time.sleep(3)
    
    # 运行验证脚本
    print("\n[3] 运行验证脚本...")
    subprocess.run([sys.executable, "验证系统.py"])
    
    print("\n" + "=" * 60)
    print("系统正在运行!")
    print("  后端地址: http://localhost:8000")
    print("  API文档: http://localhost:8000/docs")
    print("  按 Ctrl+C 停止服务")
    print("=" * 60)
    
    try:
        # 保持运行
        backend_proc.wait()
    except KeyboardInterrupt:
        print("\n正在停止服务...")
        backend_proc.terminate()
        backend_proc.wait()
        print("服务已停止")

if __name__ == "__main__":
    main()
