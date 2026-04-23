"""
测试多Agent API是否正常工作
"""
import requests
import time
import sys

def test_api():
    base_url = "http://localhost:8000"
    
    print("测试多Agent图书管理系统API...")
    print("=" * 50)
    
    try:
        # 测试健康检查
        print("1. 健康检查...")
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
        
        # 测试根路径
        print("\n2. 根路径...")
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
        
        # 测试Agent状态
        print("\n3. Agent状态...")
        response = requests.get(f"{base_url}/api/agents/status", timeout=5)
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   协调器: {data['coordinator']}")
            print(f"   Agent数量: {len(data['agents'])}")
            for agent in data['agents']:
                print(f"   - {agent['name']}: {agent['description']}")
        else:
            print(f"   错误: {response.text}")
        
        # 测试图书列表
        print("\n4. 图书列表...")
        response = requests.get(f"{base_url}/api/books/", timeout=5)
        print(f"   状态码: {response.status_code}")
        
        # 测试Agent搜索
        print("\n5. Agent搜索测试...")
        response = requests.post(f"{base_url}/api/agents/test/search?keyword=Python", timeout=5)
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"   结果: {response.json()}")
        else:
            print(f"   错误: {response.text}")
        
        print("\n" + "=" * 50)
        print("测试完成！")
        
    except requests.exceptions.ConnectionError:
        print("错误: 无法连接到后端服务，请确保服务已启动")
        return False
    except Exception as e:
        print(f"测试失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    # 等待服务启动
    print("等待后端服务启动...")
    time.sleep(2)
    
    success = test_api()
    sys.exit(0 if success else 1)