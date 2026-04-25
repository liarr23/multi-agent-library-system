"""
Agent协调器 - 负责任务分发、Agent间通信、消息路由和结果汇总
"""
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import logging
import uuid
import traceback
from collections import defaultdict

from app.agents.base_agent import BaseAgent, AgentMessage, MessageType, AgentStatus


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


class Task:
    """任务类"""
    
    def __init__(
        self,
        task_type: str,
        task_data: Any,
        requester: str = "system",
        priority: Union[int, TaskPriority] = TaskPriority.NORMAL,
        timeout: float = 60.0,
        required_agent: Optional[str] = None,
        callback: Optional[Callable] = None
    ):
        self.task_id = str(uuid.uuid4())
        self.task_type = task_type
        self.task_data = task_data
        self.requester = requester
        self.priority = TaskPriority(priority) if isinstance(priority, int) else priority
        self.timeout = timeout
        self.required_agent = required_agent
        self.callback = callback
        
        self.status = TaskStatus.PENDING
        self.assigned_agent: Optional[str] = None
        self.result: Optional[Any] = None
        self.error: Optional[str] = None
        
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.processing_time: Optional[float] = None
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "task_data": self.task_data,
            "requester": self.requester,
            "priority": self.priority.value,
            "status": self.status.value,
            "assigned_agent": self.assigned_agent,
            "timeout": self.timeout,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "processing_time": self.processing_time,
            "result": self.result,
            "error": self.error
        }
    
    def mark_started(self, agent_name: str):
        """标记任务开始"""
        self.status = TaskStatus.RUNNING
        self.assigned_agent = agent_name
        self.started_at = datetime.now()
    
    def mark_completed(self, result: Any):
        """标记任务完成"""
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.now()
        if self.started_at:
            self.processing_time = (self.completed_at - self.started_at).total_seconds()
    
    def mark_failed(self, error: str):
        """标记任务失败"""
        self.status = TaskStatus.FAILED
        self.error = error
        self.completed_at = datetime.now()
        if self.started_at:
            self.processing_time = (self.completed_at - self.started_at).total_seconds()
    
    def mark_timeout(self):
        """标记任务超时"""
        self.status = TaskStatus.TIMEOUT
        self.error = f"任务超时（>{self.timeout}秒）"
        self.completed_at = datetime.now()
        if self.started_at:
            self.processing_time = (self.completed_at - self.started_at).total_seconds()


class AgentCoordinator:
    """Agent协调器"""
    
    def __init__(self, name: str = "Coordinator"):
        self.name = name
        self.logger = logging.getLogger(f"Coordinator.{name}")
        self._started = False
        
        # Agent注册表
        self._agents: Dict[str, BaseAgent] = {}
        self._agent_capabilities: Dict[str, List[str]] = defaultdict(list)
        
        # 任务管理
        self._pending_tasks: Dict[str, Task] = {}
        self._running_tasks: Dict[str, Task] = {}
        self._completed_tasks: Dict[str, Task] = {}
        self._task_history: List[Task] = []
        
        # 消息路由
        self._message_handlers: Dict[str, List[Callable]] = defaultdict(list)
        self._broadcast_handlers: List[Callable] = []
        
        # 统计
        self._total_tasks = 0
        self._completed_task_count = 0
        self._failed_task_count = 0
        self._total_processing_time = 0.0
        
        # 配置
        self.max_history_size = 1000
        self.task_cleanup_interval = 3600  # 1小时
        self.max_concurrent_tasks = 10
        
        # 后台任务
        self._cleanup_task: Optional[asyncio.Task] = None
        self._task_processor: Optional[asyncio.Task] = None

        # 任务结果future，按task_id关联Agent真实返回
        self._task_futures: Dict[str, asyncio.Future] = {}
        
        # 事件
        self._shutdown_event = asyncio.Event()
    
    async def start(self):
        """启动协调器"""
        if self._started:
            self.logger.info(f"协调器 {self.name} 已启动，跳过重复启动")
            return

        self.logger.info(f"协调器 {self.name} 启动中...")
        
        # 启动所有已注册的Agent
        for agent_name, agent in self._agents.items():
            try:
                await agent.start()
            except Exception as e:
                self.logger.error(f"启动Agent {agent_name} 失败: {e}")
        
        # 启动后台任务
        self._cleanup_task = asyncio.create_task(self._cleanup_old_tasks())
        self._task_processor = asyncio.create_task(self._process_pending_tasks())
        self._started = True
        
        self.logger.info(f"协调器 {self.name} 已启动，管理 {len(self._agents)} 个Agent")
    
    async def stop(self):
        """停止协调器"""
        if not self._started:
            return

        self.logger.info(f"协调器 {self.name} 停止中...")
        
        self._shutdown_event.set()
        
        # 停止所有Agent
        for agent_name, agent in self._agents.items():
            try:
                await agent.stop()
            except Exception as e:
                self.logger.error(f"停止Agent {agent_name} 失败: {e}")
        
        # 停止后台任务
        if self._cleanup_task:
            self._cleanup_task.cancel()
        if self._task_processor:
            self._task_processor.cancel()
        
        # 清理待处理任务
        for task in self._pending_tasks.values():
            task.mark_failed("协调器关闭")

        self._started = False
        
        self.logger.info(f"协调器 {self.name} 已停止")
    
    def register_agent(self, agent: BaseAgent) -> bool:
        """注册Agent"""
        if agent.name in self._agents:
            self.logger.warning(f"Agent {agent.name} 已注册")
            return False
        
        self._agents[agent.name] = agent
        
        # 记录Agent能力
        for capability in agent.capabilities:
            self._agent_capabilities[capability].append(agent.name)
        
        self.logger.info(f"注册Agent: {agent.name} - {agent.description}")
        return True
    
    def unregister_agent(self, agent_name: str) -> bool:
        """注销Agent"""
        if agent_name not in self._agents:
            return False
        
        agent = self._agents.pop(agent_name)
        
        # 清理能力映射
        for capability in agent.capabilities:
            if agent_name in self._agent_capabilities[capability]:
                self._agent_capabilities[capability].remove(agent_name)
        
        self.logger.info(f"注销Agent: {agent_name}")
        return True
    
    async def route_message(self, message: AgentMessage) -> Optional[Any]:
        """路由消息到目标Agent"""
        receiver = message.receiver
        
        # 广播消息
        if receiver == "broadcast":
            return await self._broadcast_message(message)
        
        # 单播消息
        if receiver not in self._agents:
            self.logger.error(f"目标Agent不存在: {receiver}")
            return {
                "status": "error",
                "error": f"目标Agent不存在: {receiver}"
            }
        
        agent = self._agents[receiver]
        
        # 检查Agent状态
        if agent.status == AgentStatus.STOPPED:
            return {
                "status": "error",
                "error": f"Agent {receiver} 已停止"
            }
        
        # 将消息加入Agent队列
        success = await agent.enqueue_message(message)
        if not success:
            return {
                "status": "error",
                "error": f"Agent {receiver} 消息队列已满"
            }
        
        return {"status": "queued", "agent": receiver}
    
    async def _broadcast_message(self, message: AgentMessage) -> Dict:
        """广播消息到所有Agent"""
        results = {}
        
        for agent_name, agent in self._agents.items():
            if agent_name == message.sender:
                continue  # 不发送给自己
            
            try:
                # 创建广播消息副本
                broadcast_msg = AgentMessage(
                    sender=message.sender,
                    receiver=agent_name,
                    content=message.content,
                    message_type=MessageType.BROADCAST,
                    metadata=message.metadata
                )
                
                success = await agent.enqueue_message(broadcast_msg)
                results[agent_name] = {
                    "status": "queued" if success else "queue_full"
                }
            except Exception as e:
                results[agent_name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return results
    
    async def delegate_task(
        self,
        task_type: str,
        task_data: Any,
        requester: str = "system",
        priority: Union[int, TaskPriority] = TaskPriority.NORMAL,
        timeout: float = 60.0,
        preferred_agent: Optional[str] = None,
        required_capability: Optional[str] = None
    ) -> Dict:
        """委托任务给合适的Agent"""
        # 检查并发任务限制
        if len(self._running_tasks) >= self.max_concurrent_tasks:
            return {
                "status": "error",
                "error": f"已达到最大并发任务数 ({self.max_concurrent_tasks})"
            }
        
        # 选择Agent
        agent_name = self._select_agent(task_type, preferred_agent, required_capability)
        if not agent_name:
            return {
                "status": "error",
                "error": f"没有可用的Agent处理任务类型: {task_type}"
            }
        
        # 创建任务
        task = Task(
            task_type=task_type,
            task_data=task_data,
            requester=requester,
            priority=priority,
            timeout=timeout,
            required_agent=agent_name
        )
        
        # 添加到待处理队列
        self._pending_tasks[task.task_id] = task
        self._total_tasks += 1
        
        self.logger.info(f"创建任务 {task.task_id[:8]}... -> {agent_name} ({task_type})")
        
        # 等待任务完成
        try:
            result = await self._wait_for_task(task.task_id, timeout)
            return result
        except asyncio.TimeoutError:
            task.mark_timeout()
            return {
                "status": "timeout",
                "task_id": task.task_id,
                "error": f"任务超时（>{timeout}秒）"
            }
    
    def _select_agent(
        self,
        task_type: str,
        preferred_agent: Optional[str] = None,
        required_capability: Optional[str] = None
    ) -> Optional[str]:
        """选择合适的Agent"""
        # 1. 如果指定了首选Agent
        if preferred_agent and preferred_agent in self._agents:
            agent = self._agents[preferred_agent]
            if agent.status != AgentStatus.STOPPED:
                return preferred_agent
        
        # 2. 如果指定了能力要求
        if required_capability and required_capability in self._agent_capabilities:
            capable_agents = self._agent_capabilities[required_capability]
            for agent_name in capable_agents:
                agent = self._agents[agent_name]
                if agent.status != AgentStatus.STOPPED:
                    return agent_name
        
        # 3. 根据任务类型选择
        agent_mapping = {
            "book_": "BookAgent",
            "recommend": "RecommendAgent",
            "analytics": "AnalyticsAgent",
            "user_": "BookAgent",  # 用户管理也由BookAgent处理
            "borrow": "BookAgent",
            "rating": "BookAgent"
        }
        
        for prefix, agent_name in agent_mapping.items():
            if task_type.startswith(prefix) and agent_name in self._agents:
                agent = self._agents[agent_name]
                if agent.status != AgentStatus.STOPPED:
                    return agent_name
        
        # 4. 选择任意空闲的Agent
        for agent_name, agent in self._agents.items():
            if agent.status in [AgentStatus.IDLE, AgentStatus.RUNNING]:
                return agent_name
        
        return None
    
    async def _wait_for_task(self, task_id: str, timeout: float) -> Dict:
        """等待任务完成"""
        start_time = datetime.now()
        
        while True:
            # 检查超时
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > timeout:
                raise asyncio.TimeoutError()
            
            # 检查任务状态
            if task_id in self._completed_tasks:
                task = self._completed_tasks.pop(task_id)
                
                # 记录历史
                self._task_history.append(task)
                if len(self._task_history) > self.max_history_size:
                    self._task_history = self._task_history[-self.max_history_size:]
                
                # 更新统计
                if task.status == TaskStatus.COMPLETED:
                    self._completed_task_count += 1
                elif task.status in [TaskStatus.FAILED, TaskStatus.TIMEOUT]:
                    self._failed_task_count += 1
                
                if task.processing_time:
                    self._total_processing_time += task.processing_time
                
                # 返回结果
                if task.status == TaskStatus.COMPLETED:
                    return {
                        "status": "success",
                        "task_id": task.task_id,
                        "result": task.result,
                        "processing_time": task.processing_time
                    }
                else:
                    return {
                        "status": task.status.value,
                        "task_id": task.task_id,
                        "error": task.error,
                        "processing_time": task.processing_time
                    }
            
            # 短暂等待后继续检查
            await asyncio.sleep(0.1)
    
    async def _process_pending_tasks(self):
        """处理待处理任务队列"""
        while not self._shutdown_event.is_set():
            try:
                # 按优先级排序待处理任务
                pending_list = sorted(
                    self._pending_tasks.values(),
                    key=lambda t: (t.priority.value, t.created_at),
                    reverse=True
                )
                
                for task in pending_list:
                    if task.status != TaskStatus.PENDING:
                        continue
                    
                    # 检查是否超时
                    elapsed = (datetime.now() - task.created_at).total_seconds()
                    if elapsed > task.timeout:
                        task.mark_timeout()
                        self._completed_tasks[task.task_id] = task
                        self._pending_tasks.pop(task.task_id, None)
                        continue
                    
                    # 检查并发限制
                    if len(self._running_tasks) >= self.max_concurrent_tasks:
                        break
                    
                    # 分配任务
                    agent_name = task.required_agent
                    if not agent_name:
                        agent_name = self._select_agent(task.task_type)
                    
                    if not agent_name or agent_name not in self._agents:
                        continue
                    
                    agent = self._agents[agent_name]
                    if agent.status == AgentStatus.STOPPED:
                        continue
                    
                    # 标记任务开始
                    task.mark_started(agent_name)
                    self._running_tasks[task.task_id] = task
                    self._pending_tasks.pop(task.task_id, None)
                    
                    # 创建消息
                    response_future = asyncio.get_running_loop().create_future()
                    self._task_futures[task.task_id] = response_future
                    agent._response_queue[task.task_id] = response_future

                    message = AgentMessage(
                        sender=self.name,
                        receiver=agent_name,
                        content={
                            "task_type": task.task_type,
                            "data": task.task_data,
                            "task_id": task.task_id
                        },
                        message_type=MessageType.REQUEST,
                        correlation_id=task.task_id,
                        priority=task.priority.value
                    )
                    
                    # 发送消息
                    await agent.enqueue_message(message)
                    
                    # 启动监控任务
                    asyncio.create_task(self._monitor_task(task, agent, agent_name, response_future))
                
                # 短暂等待
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"任务处理循环异常: {e}")
                self.logger.error(traceback.format_exc())
                await asyncio.sleep(1.0)
    
    async def _monitor_task(
        self,
        task: Task,
        agent: BaseAgent,
        agent_name: str,
        response_future: asyncio.Future
    ):
        """监控任务执行"""
        try:
            # 等待Agent真实响应结果
            result = await asyncio.wait_for(response_future, timeout=task.timeout)
            task.mark_completed(result)
            self._completed_tasks[task.task_id] = task
            self._running_tasks.pop(task.task_id, None)

        except asyncio.TimeoutError:
            task.mark_timeout()
            self._completed_tasks[task.task_id] = task
            self._running_tasks.pop(task.task_id, None)

        except Exception as e:
            task.mark_failed(f"监控异常: {str(e)}")
            self._completed_tasks[task.task_id] = task
            self._running_tasks.pop(task.task_id, None)
        finally:
            self._task_futures.pop(task.task_id, None)
            agent._response_queue.pop(task.task_id, None)
    
    async def _cleanup_old_tasks(self):
        """清理旧任务"""
        while not self._shutdown_event.is_set():
            try:
                # 清理已完成任务
                cutoff_time = datetime.now() - timedelta(seconds=self.task_cleanup_interval)
                
                tasks_to_remove = []
                for task_id, task in self._completed_tasks.items():
                    if task.completed_at and task.completed_at < cutoff_time:
                        tasks_to_remove.append(task_id)
                
                for task_id in tasks_to_remove:
                    self._completed_tasks.pop(task_id, None)
                
                if tasks_to_remove:
                    self.logger.debug(f"清理了 {len(tasks_to_remove)} 个旧任务")
                
                # 等待下次清理
                await asyncio.sleep(self.task_cleanup_interval)
                
            except Exception as e:
                self.logger.error(f"任务清理异常: {e}")
                await asyncio.sleep(60.0)
    
    def get_agent_status(self) -> Dict[str, Dict]:
        """获取所有Agent状态"""
        return {
            agent_name: agent.get_status()
            for agent_name, agent in self._agents.items()
        }
    
    def get_task_statistics(self) -> Dict:
        """获取任务统计"""
        return {
            "total_tasks": self._total_tasks,
            "pending_tasks": len(self._pending_tasks),
            "running_tasks": len(self._running_tasks),
            "completed_tasks": len(self._completed_tasks),
            "successful_tasks": self._completed_task_count,
            "failed_tasks": self._failed_task_count,
            "average_processing_time": (
                self._total_processing_time / self._completed_task_count
                if self._completed_task_count > 0 else 0
            ),
            "total_processing_time": self._total_processing_time
        }
    
    def get_coordinator_status(self) -> Dict:
        """获取协调器状态"""
        return {
            "name": self.name,
            "agent_count": len(self._agents),
            "agents": list(self._agents.keys()),
            "statistics": self.get_task_statistics(),
            "capabilities": {
                capability: agents
                for capability, agents in self._agent_capabilities.items()
            }
        }
    
    async def health_check(self) -> Dict:
        """健康检查"""
        agent_health = {}
        all_healthy = True
        
        for agent_name, agent in self._agents.items():
            health = await agent.health_check()
            agent_health[agent_name] = health
            if not health["healthy"]:
                all_healthy = False
        
        return {
            "coordinator": self.name,
            "healthy": all_healthy,
            "agents": agent_health,
            "statistics": self.get_task_statistics()
        }
    
    def register_message_handler(self, message_type: str, handler: Callable):
        """注册消息处理器"""
        self._message_handlers[message_type].append(handler)
    
    def register_broadcast_handler(self, handler: Callable):
        """注册广播消息处理器"""
        self._broadcast_handlers.append(handler)
    
    async def send_notification(
        self,
        title: str,
        message: str,
        target_agents: Optional[List[str]] = None
    ):
        """发送通知给Agent"""
        notification = {
            "type": "notification",
            "title": title,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        if target_agents:
            for agent_name in target_agents:
                if agent_name in self._agents:
                    msg = AgentMessage(
                        sender=self.name,
                        receiver=agent_name,
                        content=notification,
                        message_type=MessageType.NOTIFICATION
                    )
                    await self.route_message(msg)
        else:
            # 广播给所有Agent
            msg = AgentMessage(
                sender=self.name,
                receiver="broadcast",
                content=notification,
                message_type=MessageType.NOTIFICATION
            )
            await self.route_message(msg)