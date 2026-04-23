"""
多Agent系统模块
"""
from app.agents.base_agent import BaseAgent, AgentMessage
from app.agents.coordinator import AgentCoordinator
from app.agents.book_agent import BookAgent
from app.agents.recommend_agent import RecommendAgent
from app.agents.analytics_agent import AnalyticsAgent

# 创建全局协调器实例
coordinator = AgentCoordinator()

# 注册所有Agent
book_agent = BookAgent()
recommend_agent = RecommendAgent()
analytics_agent = AnalyticsAgent()

coordinator.register_agent(book_agent)
coordinator.register_agent(recommend_agent)
coordinator.register_agent(analytics_agent)

__all__ = [
    "BaseAgent",
    "AgentMessage",
    "AgentCoordinator",
    "BookAgent",
    "RecommendAgent",
    "AnalyticsAgent",
    "coordinator"
]
