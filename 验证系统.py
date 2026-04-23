#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证多Agent系统是否正常工作
"""
import requests
import json
import time
import sys
import io

# 强制UTF-8输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def print_json(data, indent=2):
    """打印JSON数据"""
    print(json.dumps(data, indent=indent, ensure_ascii=False))

def test_system():
    """测试系统功能"""
    base_url = "http://localhost:8000"
    
    print("=" * 60)
    print("[多Agent图书管理系统] - 功能测试")
    print("=" * 60)
    
    # 1. 健康检查
    print("\n[1] 健康检查")
    try:
        resp = requests.get(f"{base_url}/health", timeout=5)
        print(f"   状态: {resp.status_code}")
        print_json(resp.json())
    except Exception as e:
        print(f"   失败: {e}")
        return False
    
    # 2. 系统信息
    print("\n[2] 系统信息")
    try:
        resp = requests.get(f"{base_url}/", timeout=5)
        print(f"   状态: {resp.status_code}")
        print_json(resp.json())
    except Exception as e:
        print(f"   失败: {e}")
    
    # 3. Agent状态
    print("\n[3] Agent状态")
    try:
        resp = requests.get(f"{base_url}/api/agents/status", timeout=5)
        print(f"   状态: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"   协调器: {data['coordinator']}")
            print(f"   Agent列表:")
            for agent in data['agents']:
                print(f"     - {agent['name']}: {agent['description']}")
        else:
            print(f"   响应: {resp.text}")
    except Exception as e:
        print(f"   失败: {e}")
    
    # 4. 图书列表
    print("\n[4] 图书列表")
    try:
        resp = requests.get(f"{base_url}/api/books/", timeout=5)
        print(f"   状态: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"   图书总数: {data.get('total', 0)}")
        else:
            print(f"   响应: {resp.text}")
    except Exception as e:
        print(f"   失败: {e}")
    
    # 5. 测试Agent搜索
    print("\n[5] Agent搜索测试")
    try:
        resp = requests.post(f"{base_url}/api/agents/test/search?keyword=Python", timeout=5)
        print(f"   状态: {resp.status_code}")
        if resp.status_code == 200:
            print_json(resp.json())
        else:
            print(f"   响应: {resp.text}")
    except Exception as e:
        print(f"   失败: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    print("等待服务启动...")
    time.sleep(2)
    test_system()
