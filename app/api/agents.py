"""
多Agent系统API - 提供Agent状态监控和管理接口
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any
from datetime import datetime

from app.agents import coordinator

router = APIRouter(prefix="/agents", tags=["多Agent系统"])

def get_coordinator():
    """获取协调器实例"""
    return coordinator

@router.get("/status")
async def get_agents_status():
    """获取所有Agent状态"""
    coordinator = get_coordinator()

    agents_status = []
    for name, agent in coordinator._agents.items():
        processed_count = agent.metrics.total_processed
        error_count = agent.metrics.total_errors
        last_active = agent.metrics.last_active

        agents_status.append({
            "name": name,
            "description": agent.description,
            "is_running": agent.status.value in ["idle", "running", "busy"],
            "processed_count": processed_count,
            "error_count": error_count,
            "last_active": last_active.isoformat() if last_active else None
        })

    task_stats = coordinator.get_task_statistics()
    return {
        "coordinator": {
            "registered_agents": len(coordinator._agents),
            "message_history_count": 0,
            "task_count": task_stats.get("total_tasks", 0)
        },
        "agents": agents_status
    }

@router.post("/start")
async def start_all_agents():
    """启动所有Agent"""
    coordinator = get_coordinator()

    try:
        await coordinator.start()
        return {"status": "success", "message": "所有Agent已启动"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动失败: {str(e)}")

@router.post("/stop")
async def stop_all_agents():
    """停止所有Agent"""
    coordinator = get_coordinator()

    try:
        await coordinator.stop()
        return {"status": "success", "message": "所有Agent已停止"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止失败: {str(e)}")

@router.get("/messages")
async def get_message_history(limit: int = 50):
    """获取消息历史"""
    coordinator = get_coordinator()

    message_history = getattr(coordinator, "_message_history", [])
    messages = []
    for msg in message_history[-limit:]:
        messages.append({
            "id": msg.message_id,
            "sender": msg.sender,
            "receiver": msg.receiver,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat(),
            "message_type": msg.message_type.value if hasattr(msg.message_type, "value") else str(msg.message_type)
        })

    return {"messages": messages, "total": len(message_history)}

@router.get("/tasks")
async def get_task_list():
    """获取任务列表（模拟数据）"""
    # 这里可以扩展为真实的任务跟踪系统
    tasks = [
        {
            "id": 1001,
            "description": "搜索包含'Python'的图书",
            "assigned_to": "BookAgent",
            "status": "completed",
            "created_at": datetime.now().isoformat()
        },
        {
            "id": 1002,
            "description": "为用户5生成个性化推荐",
            "assigned_to": "RecommendAgent",
            "status": "processing",
            "created_at": datetime.now().isoformat()
        },
        {
            "id": 1003,
            "description": "生成月度借阅报告",
            "assigned_to": "AnalyticsAgent",
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
    ]
    
    return {"tasks": tasks}

@router.post("/test/search")
async def test_book_search(keyword: str):
    """测试图书搜索Agent"""
    coordinator = get_coordinator()
    
    try:
        # 使用协调器的委托任务方法
        result = await coordinator.delegate_task(
            task_type="book_search",
            task_data={"keyword": keyword}
        )
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@router.post("/test/recommend")
async def test_recommend(user_id: int):
    """测试推荐Agent"""
    coordinator = get_coordinator()
    
    try:
        result = await coordinator.delegate_task(
            task_type="recommend",
            task_data={"user_id": user_id}
        )
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"推荐失败: {str(e)}")

@router.post("/test/analytics")
async def test_analytics():
    """测试分析Agent"""
    coordinator = get_coordinator()
    
    try:
        result = await coordinator.delegate_task(
            task_type="analytics_overview",
            task_data={},
            preferred_agent="AnalyticsAgent"
        )
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")
