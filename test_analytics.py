"""
测试AnalyticsAgent的数据分析功能
"""
import sys
import io
import asyncio

# 设置UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from app.agents.analytics_agent import AnalyticsAgent
from app.agents.base_agent import AgentMessage

async def test_analytics():
    print("=" * 60)
    print("测试AnalyticsAgent")
    print("=" * 60)
    
    # 创建AnalyticsAgent实例
    agent = AnalyticsAgent()
    
    # 创建测试消息
    message = AgentMessage(
        sender="test",
        receiver="AnalyticsAgent",
        content={
            "task_type": "analytics_overview",
            "data": {}
        }
    )
    
    print("1. 测试get_system_overview方法...")
    try:
        result = await agent.get_system_overview({})
        print(f"✅ 调用成功")
        print(f"结果: {result}")
        
        if result.get("status") == "success":
            overview = result.get("overview", {})
            print(f"\n图书统计:")
            books = overview.get("books", {})
            print(f"  总图书数: {books.get('total_titles', 0)}")
            print(f"  总副本数: {books.get('total_copies', 0)}")
            print(f"  可用副本数: {books.get('available_copies', 0)}")
            
            print(f"\n用户统计:")
            users = overview.get("users", {})
            print(f"  总用户数: {users.get('total_users', 0)}")
            print(f"  活跃用户数: {users.get('active_users', 0)}")
            
            print(f"\n借阅统计:")
            borrows = overview.get("borrows", {})
            print(f"  总借阅次数: {borrows.get('total_all_time', 0)}")
            print(f"  当前借出: {borrows.get('current_active', 0)}")
        else:
            print(f"❌ 查询失败: {result}")
    except Exception as e:
        print(f"❌ 调用异常: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n2. 测试process_message方法...")
    try:
        result = await agent.process_message(message)
        print(f"✅ 处理消息成功")
        print(f"结果: {result}")
    except Exception as e:
        print(f"❌ 处理消息异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_analytics())