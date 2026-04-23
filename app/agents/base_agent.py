"""
Agent基类 - 定义所有Agent的通用接口和功能
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
import asyncio
import logging

from sqlalchemy.orm import Session

from app.database import SessionLocal


class AgentMessage:
    """Agent间通信的消息格式"""
    
    def __init__(
        self,
        sender: str,
        receiver: str,
        content: Any,
        message_type: str = "request",
        message_id: Optional[str] = None
    ):
        self.sender = sender
        self.receiver = receiver
        self.content = content
        self.message_type = message_type
        self.message_id = message_id or f"{sender}_{datetime.now().timestamp()}"
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict:
        return {
            "message_id": self.message_id,
            "sender": self.sender,
            "receiver": self.receiver,
            "content": self.content,
            "message_type": self.message_type,
            "timestamp": self.timestamp.isoformat()
        }


class BaseAgent(ABC):
    """Agent基类"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"Agent.{name}")
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._is_running = False
        self._processed_count = 0
        self._error_count = 0
        self._last_active = None
    
    @abstractmethod
    async def process_message(self, message: AgentMessage) -> Any:
        """处理接收到的消息（子类必须实现）"""
        pass
    
    async def _update_status(self):
        """更新处理状态（由子类在process_message中调用）"""
        self._processed_count += 1
        self._last_active = datetime.now()
    
    async def start(self):
        """启动Agent"""
        self._is_running = True
        self.logger.info(f"Agent {self.name} 已启动")
    
    async def stop(self):
        """停止Agent"""
        self._is_running = False
        self.logger.info(f"Agent {self.name} 已停止")
    
    def get_db_session(self) -> Session:
        """获取数据库会话"""
        return SessionLocal()
    
    async def send_message(self, coordinator, message: AgentMessage):
        """通过协调器发送消息给其他Agent"""
        await coordinator.route_message(message)
    
    def log_action(self, action: str, details: Any = None):
        """记录Agent操作日志"""
        self.logger.info(f"[{self.name}] {action}: {details}")
    
    async def handle_error(self, error: Exception, context: str = ""):
        """错误处理"""
        self.logger.error(f"[{self.name}] 错误 - {context}: {str(error)}")
        return {
            "status": "error",
            "agent": self.name,
            "error": str(error),
            "context": context
        }
    
    def get_status(self) -> Dict:
        """获取Agent状态"""
        return {
            "name": self.name,
            "description": self.description,
            "is_running": self._is_running,
            "queue_size": self._message_queue.qsize()
        }
