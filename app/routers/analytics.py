"""
数据分析API路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, timedelta

from app.database import get_db
from app.agents import coordinator

router = APIRouter(prefix="/analytics", tags=["数据分析"])


class ReportRequest(BaseModel):
    """报表生成请求"""
    report_type: str  # overview, popular, trends, category
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 10


@router.get("/overview")
async def get_system_overview():
    """获取系统概览统计"""
    result = await coordinator.delegate_task(
        task_type="analytics_overview",
        task_data={},
        preferred_agent="AnalyticsAgent"
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result["result"]


@router.get("/popular")
async def get_popular_books(
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    limit: int = Query(10, ge=1, le=50, description="返回数量")
):
    """获取热门图书"""
    result = await coordinator.delegate_task(
        task_type="analytics_popular",
        task_data={
            "days": days,
            "limit": limit
        },
        preferred_agent="AnalyticsAgent"
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result["result"]


@router.get("/trends")
async def get_borrow_trends(
    days: int = Query(30, ge=1, le=365, description="统计天数")
):
    """获取借阅趋势"""
    result = await coordinator.delegate_task(
        task_type="analytics_trends",
        task_data={
            "days": days
        },
        preferred_agent="AnalyticsAgent"
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result["result"]


@router.get("/category-stats")
async def get_category_statistics():
    """获取分类统计"""
    result = await coordinator.delegate_task(
        task_type="category_stats",
        task_data={},
        preferred_agent="AnalyticsAgent"
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result["result"]


@router.post("/report")
async def generate_report(report_request: ReportRequest):
    """生成分析报表"""
    result = await coordinator.delegate_task(
        task_type="generate_report",
        task_data={
            "report_type": report_request.report_type,
            "start_date": report_request.start_date,
            "end_date": report_request.end_date,
            "limit": report_request.limit
        },
        preferred_agent="AnalyticsAgent"
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result["result"]


@router.get("/user-activity")
async def get_user_activity(
    user_id: Optional[int] = Query(None, description="用户ID"),
    days: int = Query(30, ge=1, le=365, description="统计天数")
):
    """获取用户活动统计"""
    result = await coordinator.delegate_task(
        task_type="user_activity",
        task_data={
            "user_id": user_id,
            "days": days
        },
        preferred_agent="AnalyticsAgent"
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result["result"]


@router.get("/agent-status")
async def get_agent_status():
    """获取所有Agent状态"""
    agents_status = {}
    for agent_name, agent in coordinator.agents.items():
        agents_status[agent_name] = agent.get_status()
    
    return {
        "coordinator": {
            "total_agents": len(coordinator.agents),
            "total_messages": len(coordinator._message_history)
        },
        "agents": agents_status
    }
