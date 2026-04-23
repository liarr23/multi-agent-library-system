"""
Agent协调器 - 负责Agent间通信、任务分发、结果汇总
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
import asyncio
import logging

from app.agents.base_agent import BaseAgent, AgentMessage


class AgentCoordinator:
    """Agent协调器"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.logger = logging.getLogger("Coordinator")
        self._message_history: List[AgentMessage] = []
        self._task_counter = 0
    
    def register_agent(self, agent: BaseAgent):
        """注册Agent"""
        self.agents[agent.name] = agent
        self.logger.info(f"已注册Agent: {agent.name}")
    
    def unregister_agent(self, agent_name: str):
        """注销Agent"""
        if agent_name in self.agents:
            del self.agents[agent_name]
            self.logger.info(f"已注销Agent: {agent_name}")
    
    async def route_message(self, message: AgentMessage) -> Any:
        """路由消息到目标Agent"""
        receiver = message.receiver
        
        if receiver not in self.agents:
            raise ValueError(f"目标Agent不存在: {receiver}")
        
        self._message_history.append(message)
        self.logger.info(f"消息路由: {message.sender} -> {receiver}")
        
        agent = self.agents[receiver]
        return await agent.process_message(message)
    
    async def broadcast(self, message: AgentMessage) -> Dict[str, Any]:
        """广播消息给所有Agent"""
        results = {}
        
        for agent_name, agent in self.agents.items():
            if agent_name != message.sender:
                try:
                    result = await agent.process_message(message)
                    results[agent_name] = result
                except Exception as e:
                    results[agent_name] = {"error": str(e)}
        
        return results
    
    async def delegate_task(
        self,
        task_type: str,
        task_data: Any,
        preferred_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """委托任务给合适的Agent"""
        self._task_counter += 1
        task_id = f"task_{self._task_counter}_{datetime.now().timestamp()}"
        
        # 根据任务类型选择Agent
        target_agent = preferred_agent or self._select_agent_for_task(task_type)
        
        if not target_agent:
            return {
                "task_id": task_id,
                "status": "error",
                "error": f"没有找到处理任务类型 '{task_type}' 的Agent"
            }
        
        message = AgentMessage(
            sender="coordinator",
            receiver=target_agent,
            content={
                "task_id": task_id,
                "task_type": task_type,
                "data": task_data
            },
            message_type="task"
        )
        
        try:
            result = await self.route_message(message)
            return {
                "task_id": task_id,
                "status": "success",
                "agent": target_agent,
                "result": result
            }
        except Exception as e:
            return {
                "task_id": task_id,
                "status": "error",
                "agent": target_agent,
                "error": str(e)
            }
    
    def _select_agent_for_task(self, task_type: str) -> Optional[str]:
        """根据任务类型选择Agent"""
        # 任务类型到Agent的映射
        task_mapping = {
            # 图书管理任务
            "book_search": "BookAgent",
            "book_create": "BookAgent",
            "book_update": "BookAgent",
            "book_delete": "BookAgent",
            "book_detail": "BookAgent",
            
            # 借阅管理任务
            "borrow_book": "BookAgent",
            "return_book": "BookAgent",
            "renew_book": "BookAgent",
            "check_overdue": "BookAgent",
            
            # 推荐任务
            "recommend": "RecommendAgent",
            "update_user_profile": "RecommendAgent",
            "calculate_similarity": "RecommendAgent",
            
            # 分析任务
            "analytics_overview": "AnalyticsAgent",
            "analytics_popular": "AnalyticsAgent",
            "analytics_trends": "AnalyticsAgent",
            "generate_report": "AnalyticsAgent",
            "user_activity": "AnalyticsAgent",
            "category_stats": "AnalyticsAgent"
        }
        
        return task_mapping.get(task_type)
    
    async def start_all_agents(self):
        """启动所有Agent"""
        for agent in self.agents.values():
            await agent.start()
    
    async def stop_all_agents(self):
        """停止所有Agent"""
        for agent in self.agents.values():
            await agent.stop()
    
    def get_system_status(self) -> Dict:
        """获取系统状态"""
        return {
            "coordinator": {
                "registered_agents": len(self.agents),
                "message_history_count": len(self._message_history),
                "task_count": self._task_counter
            },
            "agents": {
                name: agent.get_status()
                for name, agent in self.agents.items()
            }
        }
    
    def get_agent_list(self) -> List[Dict]:
        """获取Agent列表"""
        return [
            {
                "name": name,
                "description": agent.description,
                "is_running": agent._is_running
            }
            for name, agent in self.agents.items()
        ]
