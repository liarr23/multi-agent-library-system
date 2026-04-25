"""
Agent基类 - 定义所有Agent的通用接口和功能
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import logging
import uuid
import traceback

from sqlalchemy.orm import Session

from app.database import SessionLocal


class AgentStatus(Enum):
    """Agent状态枚举"""
    IDLE = "idle"
    RUNNING = "running"
    BUSY = "busy"
    ERROR = "error"
    STOPPED = "stopped"


class MessageType(Enum):
    """消息类型枚举"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    BROADCAST = "broadcast"
    ERROR = "error"


class AgentMessage:
    """Agent间通信的消息格式"""
    
    def __init__(
        self,
        sender: str,
        receiver: str,
        content: Any,
        message_type: Union[str, MessageType] = MessageType.REQUEST,
        message_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        priority: int = 0,
        metadata: Optional[Dict] = None
    ):
        self.sender = sender
        self.receiver = receiver
        self.content = content
        self.message_type = MessageType(message_type) if isinstance(message_type, str) else message_type
        self.message_id = message_id or str(uuid.uuid4())
        self.correlation_id = correlation_id
        self.priority = priority
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
        self.processed = False
        self.processing_time: Optional[float] = None
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "message_id": self.message_id,
            "correlation_id": self.correlation_id,
            "sender": self.sender,
            "receiver": self.receiver,
            "content": self.content,
            "message_type": self.message_type.value,
            "priority": self.priority,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "processed": self.processed,
            "processing_time": self.processing_time
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AgentMessage':
        """从字典创建消息"""
        return cls(
            sender=data["sender"],
            receiver=data["receiver"],
            content=data["content"],
            message_type=data.get("message_type", MessageType.REQUEST),
            message_id=data.get("message_id"),
            correlation_id=data.get("correlation_id"),
            priority=data.get("priority", 0),
            metadata=data.get("metadata", {})
        )
    
    def mark_processed(self, processing_time: float):
        """标记消息已处理"""
        self.processed = True
        self.processing_time = processing_time


class AgentMetrics:
    """Agent性能指标"""
    
    def __init__(self):
        self.total_processed = 0
        self.total_errors = 0
        self.total_processing_time = 0.0
        self.last_active: Optional[datetime] = None
        self.message_queue_size = 0
        self.average_processing_time = 0.0
        self.error_rate = 0.0
    
    def update(self, processing_time: float, had_error: bool = False):
        """更新指标"""
        self.total_processed += 1
        if had_error:
            self.total_errors += 1
        self.total_processing_time += processing_time
        self.last_active = datetime.now()
        
        # 计算平均处理时间
        if self.total_processed > 0:
            self.average_processing_time = self.total_processing_time / self.total_processed
        
        # 计算错误率
        if self.total_processed > 0:
            self.error_rate = self.total_errors / self.total_processed
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "total_processed": self.total_processed,
            "total_errors": self.total_errors,
            "total_processing_time": round(self.total_processing_time, 2),
            "average_processing_time": round(self.average_processing_time, 4),
            "error_rate": round(self.error_rate, 4),
            "last_active": self.last_active.isoformat() if self.last_active else None,
            "message_queue_size": self.message_queue_size
        }


class BaseAgent(ABC):
    """Agent基类"""
    
    def __init__(
        self,
        name: str,
        description: str = "",
        version: str = "1.0.0",
        capabilities: Optional[List[str]] = None
    ):
        self.name = name
        self.description = description
        self.version = version
        self.capabilities = capabilities or []
        self.status = AgentStatus.IDLE
        self.logger = logging.getLogger(f"Agent.{name}")
        
        # 消息队列
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._response_queue: Dict[str, asyncio.Future] = {}
        
        # 性能指标
        self.metrics = AgentMetrics()
        
        # 配置
        self.max_queue_size = 100
        self.processing_timeout = 30.0  # 秒
        
        # 事件
        self._shutdown_event = asyncio.Event()
        
        # 启动后台任务
        self._processing_task: Optional[asyncio.Task] = None
    
    @abstractmethod
    async def process_message(self, message: AgentMessage) -> Any:
        """处理接收到的消息（子类必须实现）"""
        pass
    
    async def start(self):
        """启动Agent"""
        if self.status == AgentStatus.RUNNING:
            self.logger.warning(f"Agent {self.name} 已经在运行中")
            return
        
        self.status = AgentStatus.RUNNING
        self._shutdown_event.clear()
        
        # 启动消息处理任务
        self._processing_task = asyncio.create_task(self._process_queue())
        
        self.logger.info(f"Agent {self.name} v{self.version} 已启动")
        self.logger.info(f"  描述: {self.description}")
        self.logger.info(f"  能力: {', '.join(self.capabilities) if self.capabilities else '无'}")
    
    async def stop(self):
        """停止Agent"""
        if self.status == AgentStatus.STOPPED:
            return
        
        self.status = AgentStatus.STOPPED
        self._shutdown_event.set()
        
        # 等待处理任务完成
        if self._processing_task:
            try:
                await asyncio.wait_for(self._processing_task, timeout=5.0)
            except asyncio.TimeoutError:
                self._processing_task.cancel()
        
        self.logger.info(f"Agent {self.name} 已停止")
    
    async def _process_queue(self):
        """处理消息队列"""
        while not self._shutdown_event.is_set():
            try:
                # 等待消息，带超时
                try:
                    message = await asyncio.wait_for(
                        self._message_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # 处理消息
                await self._handle_message(message)
                
            except Exception as e:
                self.logger.error(f"消息处理循环异常: {e}")
                self.logger.error(traceback.format_exc())
    
    async def _handle_message(self, message: AgentMessage):
        """处理单个消息"""
        start_time = datetime.now()
        had_error = False
        
        try:
            self.status = AgentStatus.BUSY
            self.metrics.message_queue_size = self._message_queue.qsize()
            
            # 设置超时
            try:
                result = await asyncio.wait_for(
                    self.process_message(message),
                    timeout=self.processing_timeout
                )
            except asyncio.TimeoutError:
                result = {
                    "status": "error",
                    "error": f"处理超时（>{self.processing_timeout}秒）",
                    "agent": self.name
                }
                had_error = True
            
            # 计算处理时间
            processing_time = (datetime.now() - start_time).total_seconds()
            message.mark_processed(processing_time)
            
            # 更新指标
            self.metrics.update(processing_time, had_error)
            
            # 如果有等待的响应，设置结果
            if message.correlation_id and message.correlation_id in self._response_queue:
                future = self._response_queue.pop(message.correlation_id)
                if not future.done():
                    future.set_result(result)
            
            self.logger.debug(f"处理消息 {message.message_id} 完成，耗时 {processing_time:.3f}秒")
            
        except Exception as e:
            had_error = True
            processing_time = (datetime.now() - start_time).total_seconds()
            self.metrics.update(processing_time, had_error)
            
            error_result = {
                "status": "error",
                "error": str(e),
                "traceback": traceback.format_exc(),
                "agent": self.name
            }
            
            # 如果有等待的响应，设置错误
            if message.correlation_id and message.correlation_id in self._response_queue:
                future = self._response_queue.pop(message.correlation_id)
                if not future.done():
                    future.set_exception(e)
            
            self.logger.error(f"处理消息 {message.message_id} 失败: {e}")
            self.logger.error(traceback.format_exc())
        
        finally:
            self.status = AgentStatus.RUNNING if not self._shutdown_event.is_set() else AgentStatus.STOPPED
    
    async def send_message(
        self,
        coordinator,
        receiver: str,
        content: Any,
        message_type: Union[str, MessageType] = MessageType.REQUEST,
        priority: int = 0,
        wait_response: bool = False,
        timeout: float = 30.0
    ) -> Optional[Any]:
        """通过协调器发送消息给其他Agent"""
        correlation_id = str(uuid.uuid4()) if wait_response else None
        
        message = AgentMessage(
            sender=self.name,
            receiver=receiver,
            content=content,
            message_type=message_type,
            correlation_id=correlation_id,
            priority=priority
        )
        
        if wait_response:
            # 创建等待的Future
            future = asyncio.Future()
            self._response_queue[correlation_id] = future
            
            # 发送消息
            await coordinator.route_message(message)
            
            # 等待响应
            try:
                result = await asyncio.wait_for(future, timeout=timeout)
                return result
            except asyncio.TimeoutError:
                # 清理
                self._response_queue.pop(correlation_id, None)
                raise asyncio.TimeoutError(f"等待 {receiver} 响应超时")
        else:
            # 直接发送，不等待响应
            await coordinator.route_message(message)
            return None
    
    def get_db_session(self) -> Session:
        """获取数据库会话"""
        return SessionLocal()

    async def _update_status(self):
        """更新运行状态与基础指标。"""
        if self.status != AgentStatus.STOPPED:
            self.status = AgentStatus.BUSY
        self.metrics.last_active = datetime.now()
        self.metrics.message_queue_size = self._message_queue.qsize()
    
    def log_action(self, action: str, details: Any = None):
        """记录Agent操作日志"""
        self.logger.info(f"[{self.name}] {action}: {details}")
    
    async def handle_error(self, error: Exception, context: str = "") -> Dict:
        """错误处理"""
        error_info = {
            "status": "error",
            "agent": self.name,
            "error": str(error),
            "error_type": type(error).__name__,
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        
        self.logger.error(f"[{self.name}] 错误 - {context}: {str(error)}")
        self.logger.error(traceback.format_exc())
        
        return error_info
    
    def get_status(self) -> Dict:
        """获取Agent状态"""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "status": self.status.value,
            "capabilities": self.capabilities,
            "metrics": self.metrics.to_dict(),
            "queue_size": self._message_queue.qsize(),
            "max_queue_size": self.max_queue_size,
            "processing_timeout": self.processing_timeout
        }
    
    async def enqueue_message(self, message: AgentMessage) -> bool:
        """将消息加入队列"""
        if self._message_queue.qsize() >= self.max_queue_size:
            self.logger.warning(f"消息队列已满，拒绝新消息")
            return False
        
        await self._message_queue.put(message)
        return True
    
    def clear_queue(self):
        """清空消息队列"""
        while not self._message_queue.empty():
            try:
                self._message_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        
        # 清理等待的响应
        for future in self._response_queue.values():
            if not future.done():
                future.cancel()
        self._response_queue.clear()
        
        self.logger.info(f"已清空 {self.name} 的消息队列")
    
    async def health_check(self) -> Dict:
        """健康检查"""
        is_healthy = (
            self.status in [AgentStatus.IDLE, AgentStatus.RUNNING, AgentStatus.BUSY] and
            self.metrics.error_rate < 0.5  # 错误率低于50%
        )
        
        return {
            "agent": self.name,
            "healthy": is_healthy,
            "status": self.status.value,
            "uptime": self.metrics.to_dict(),
            "issues": [] if is_healthy else ["Agent状态异常或错误率过高"]
        }