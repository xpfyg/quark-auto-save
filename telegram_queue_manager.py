# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用队列任务管理器
功能：支持多种任务类型，每种任务有独立队列和处理逻辑
"""
import asyncio
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List, Callable, Awaitable
from dataclasses import dataclass, field


class TaskType(Enum):
    """任务类型枚举"""
    TELEGRAM_SHARE = "telegram_share"       # Telegram分享任务
    RESOURCE_SYNC = "resource_sync"         # 资源同步任务
    TMDB_UPDATE = "tmdb_update"             # TMDB信息更新任务
    FILE_DOWNLOAD = "file_download"         # 文件下载任务
    # 可以继续添加其他任务类型...


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"        # 待处理
    PROCESSING = "processing"  # 处理中
    COMPLETED = "completed"    # 已完成
    FAILED = "failed"          # 失败


@dataclass
class Task:
    """通用任务数据类"""
    task_type: TaskType                    # 任务类型
    task_data: Any                         # 任务数据（可以是任意类型）
    task_id: Optional[str] = None          # 任务ID（可选，自动生成）
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 0                      # 优先级（数字越大优先级越高）
    max_retries: int = 3                   # 最大重试次数
    retry_count: int = 0                   # 当前重试次数
    error_message: Optional[str] = None    # 错误信息
    create_time: datetime = field(default_factory=datetime.now)
    start_time: Optional[datetime] = None
    complete_time: Optional[datetime] = None

    def __post_init__(self):
        """初始化后处理"""
        if self.task_id is None:
            # 自动生成任务ID
            self.task_id = f"{self.task_type.value}_{self.create_time.strftime('%Y%m%d%H%M%S%f')}"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type.value,
            "status": self.status.value,
            "priority": self.priority,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "start_time": self.start_time.strftime("%Y-%m-%d %H:%M:%S") if self.start_time else None,
            "complete_time": self.complete_time.strftime("%Y-%m-%d %H:%M:%S") if self.complete_time else None,
            "error_message": self.error_message
        }


# 任务处理器类型定义：async function(task_data: Any) -> bool
TaskHandler = Callable[[Any], Awaitable[bool]]


class QueueManager:
    """
    通用队列任务管理器（单例模式）

    功能：
    1. 支持多种任务类型，每种任务有独立队列
    2. 每种任务类型由独立的消费者协程处理
    3. 支持动态注册任务处理器
    4. 任务数据可以是任意类型
    5. 支持任务优先级、重试机制
    """

    # 单例相关
    _instance = None
    _lock = asyncio.Lock()

    def __init__(self):
        """
        私有构造函数，不应直接调用
        请使用 QueueManager.get_instance() 获取单例
        """
        # 每种任务类型的队列：{TaskType: asyncio.Queue}
        self.queues: Dict[TaskType, asyncio.Queue] = {}

        # 每种任务类型的处理器：{TaskType: TaskHandler}
        self.handlers: Dict[TaskType, TaskHandler] = {}

        # 每种任务类型的消费者协程：{TaskType: asyncio.Task}
        self.workers: Dict[TaskType, asyncio.Task] = {}

        # 每种任务类型的当前任务：{TaskType: Task}
        self.current_tasks: Dict[TaskType, Optional[Task]] = {}

        # 历史任务记录
        self.completed_tasks: Dict[TaskType, List[Task]] = {}
        self.failed_tasks: Dict[TaskType, List[Task]] = {}

        # 运行状态
        self.is_running: bool = False

        print("✅ 通用队列管理器已初始化")

    @classmethod
    async def get_instance(cls):
        """
        获取全局单例实例（异步安全）

        Returns:
            QueueManager: 全局唯一的队列管理器实例
        """
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    print("🔧 创建队列管理器全局单例...")
                    cls._instance = cls()
        return cls._instance

    def register_handler(self, task_type: TaskType, handler: TaskHandler):
        """
        注册任务处理器

        Args:
            task_type: 任务类型
            handler: 任务处理函数，接收 task_data，返回 bool（成功/失败）
        """
        if task_type in self.handlers:
            print(f"⚠️  任务类型 {task_type.value} 的处理器已存在，将被覆盖")

        self.handlers[task_type] = handler

        # 创建队列和初始化状态
        if task_type not in self.queues:
            self.queues[task_type] = asyncio.Queue()
            self.current_tasks[task_type] = None
            self.completed_tasks[task_type] = []
            self.failed_tasks[task_type] = []

        print(f"✅ 已注册任务处理器: {task_type.value}")

        # 如果队列管理器已启动，立即启动该任务类型的消费者
        if self.is_running and task_type not in self.workers:
            self._start_worker(task_type)

    def _start_worker(self, task_type: TaskType):
        """
        启动指定任务类型的消费者协程

        Args:
            task_type: 任务类型
        """
        if task_type not in self.handlers:
            print(f"❌ 任务类型 {task_type.value} 未注册处理器，无法启动消费者")
            return

        worker_task = asyncio.create_task(self._process_queue(task_type))
        self.workers[task_type] = worker_task
        print(f"🚀 已启动消费者: {task_type.value}")

    async def start(self):
        """启动所有队列处理"""
        if self.is_running:
            print("⚠️  队列管理器已在运行")
            return

        self.is_running = True

        # 为所有已注册的任务类型启动消费者
        for task_type in self.handlers.keys():
            self._start_worker(task_type)

        print(f"✅ 队列管理器已启动，共 {len(self.workers)} 个消费者")

    async def stop(self):
        """停止所有队列处理"""
        if not self.is_running:
            print("⚠️  队列管理器未运行")
            return

        self.is_running = False

        # 取消所有消费者协程
        for task_type, worker in self.workers.items():
            worker.cancel()
            try:
                await worker
            except asyncio.CancelledError:
                pass
            print(f"🛑 已停止消费者: {task_type.value}")

        self.workers.clear()
        print("✅ 队列管理器已停止")

    async def add_task(self, task: Task) -> bool:
        """
        添加任务到对应类型的队列

        Args:
            task: Task 对象

        Returns:
            bool: 是否成功添加
        """
        task_type = task.task_type

        # 检查任务类型是否已注册
        if task_type not in self.handlers:
            print(f"❌ 任务类型 {task_type.value} 未注册处理器")
            return False

        try:
            await self.queues[task_type].put(task)
            queue_size = self.queues[task_type].qsize()
            print(f"➕ 任务已加入队列 [{task_type.value}]: {task.task_id}")
            print(f"📊 队列 [{task_type.value}] 大小: {queue_size} 个任务")
            return True
        except Exception as e:
            print(f"❌ 添加任务失败: {e}")
            return False

    async def _process_queue(self, task_type: TaskType):
        """
        队列处理主循环（每个任务类型独立的消费者）

        Args:
            task_type: 任务类型
        """
        print(f"🔄 [{task_type.value}] 消费者已启动")

        handler = self.handlers[task_type]
        queue = self.queues[task_type]

        while self.is_running:
            try:
                # 从队列获取任务（带超时，避免阻塞）
                try:
                    task = await asyncio.wait_for(queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                # 开始处理任务
                self.current_tasks[task_type] = task
                task.status = TaskStatus.PROCESSING
                task.start_time = datetime.now()

                print(f"\n{'=' * 60}")
                print(f"📤 [{task_type.value}] 开始处理任务: {task.task_id}")
                print(f"📊 队列剩余: {queue.qsize()} 个任务")
                print(f"{'=' * 60}\n")

                try:
                    # 调用对应的处理器
                    result = await handler(task.task_data)

                    if result:
                        # 任务成功
                        task.status = TaskStatus.COMPLETED
                        task.complete_time = datetime.now()
                        self.completed_tasks[task_type].append(task)

                        elapsed = (task.complete_time - task.start_time).total_seconds()
                        print(f"\n✅ [{task_type.value}] 任务完成: {task.task_id} (耗时 {elapsed:.1f}秒)")
                    else:
                        raise Exception("处理器返回 False")

                except Exception as e:
                    # 任务失败处理
                    task.retry_count += 1
                    task.error_message = str(e)

                    # 判断是否需要重试
                    if task.retry_count < task.max_retries:
                        print(f"⚠️  [{task_type.value}] 任务失败，准备重试 ({task.retry_count}/{task.max_retries})")
                        print(f"❌ 错误信息: {e}")

                        # 重新加入队列
                        task.status = TaskStatus.PENDING
                        await queue.put(task)
                        print(f"🔄 任务已重新加入队列: {task.task_id}")
                    else:
                        # 超过最大重试次数，标记为失败
                        task.status = TaskStatus.FAILED
                        task.complete_time = datetime.now()
                        self.failed_tasks[task_type].append(task)

                        print(f"\n❌ [{task_type.value}] 任务最终失败: {task.task_id}")
                        print(f"❌ 错误信息: {e}")
                        print(f"🔄 已重试 {task.retry_count} 次")

                finally:
                    # 清理当前任务
                    self.current_tasks[task_type] = None
                    queue.task_done()

            except asyncio.CancelledError:
                print(f"⚠️  [{task_type.value}] 消费者被取消")
                break
            except Exception as e:
                print(f"❌ [{task_type.value}] 消费者异常: {e}")
                import traceback
                traceback.print_exc()

        print(f"🔄 [{task_type.value}] 消费者已退出")

    def get_status(self, task_type: Optional[TaskType] = None) -> Dict[str, Any]:
        """
        获取队列状态

        Args:
            task_type: 任务类型（可选，None 表示获取所有类型的状态）

        Returns:
            Dict: 包含队列状态信息的字典
        """
        if task_type:
            # 获取单个任务类型的状态
            current_task_info = None
            current = self.current_tasks.get(task_type)
            if current:
                elapsed = (datetime.now() - current.start_time).total_seconds() if current.start_time else 0
                current_task_info = {
                    "task_id": current.task_id,
                    "status": current.status.value,
                    "start_time": current.start_time.strftime("%Y-%m-%d %H:%M:%S") if current.start_time else None,
                    "elapsed_seconds": round(elapsed, 1)
                }

            return {
                "task_type": task_type.value,
                "is_running": self.is_running and task_type in self.workers,
                "queue_size": self.queues.get(task_type, asyncio.Queue()).qsize(),
                "current_task": current_task_info,
                "completed_count": len(self.completed_tasks.get(task_type, [])),
                "failed_count": len(self.failed_tasks.get(task_type, [])),
            }
        else:
            # 获取所有任务类型的状态
            all_status = {
                "is_running": self.is_running,
                "task_types": {}
            }

            for task_type in self.handlers.keys():
                all_status["task_types"][task_type.value] = self.get_status(task_type)

            return all_status

    def get_completed_tasks(self, task_type: TaskType, limit: int = 10) -> List[Dict]:
        """
        获取已完成的任务列表

        Args:
            task_type: 任务类型
            limit: 返回的最大数量

        Returns:
            List[Dict]: 任务信息列表
        """
        tasks = self.completed_tasks.get(task_type, [])
        return [task.to_dict() for task in tasks[-limit:]]

    def get_failed_tasks(self, task_type: TaskType, limit: int = 10) -> List[Dict]:
        """
        获取失败的任务列表

        Args:
            task_type: 任务类型
            limit: 返回的最大数量

        Returns:
            List[Dict]: 任务信息列表
        """
        tasks = self.failed_tasks.get(task_type, [])
        return [task.to_dict() for task in tasks[-limit:]]

    async def wait_completion(self, task_type: Optional[TaskType] = None):
        """
        等待任务完成

        Args:
            task_type: 任务类型（可选，None 表示等待所有类型的任务完成）
        """
        if task_type:
            # 等待指定类型的任务完成
            print(f"⏳ 等待 [{task_type.value}] 所有任务完成...")
            if task_type in self.queues:
                await self.queues[task_type].join()
                # 等待当前任务完成
                while self.current_tasks.get(task_type) is not None:
                    await asyncio.sleep(0.5)
            print(f"✅ [{task_type.value}] 所有任务已完成")
        else:
            # 等待所有任务类型完成
            print("⏳ 等待所有任务完成...")
            for task_type in self.queues.keys():
                await self.wait_completion(task_type)
            print("✅ 所有任务已完成")

    def clear_history(self, task_type: Optional[TaskType] = None):
        """
        清空历史记录

        Args:
            task_type: 任务类型（可选，None 表示清空所有类型的历史记录）
        """
        if task_type:
            completed_count = len(self.completed_tasks.get(task_type, []))
            failed_count = len(self.failed_tasks.get(task_type, []))
            self.completed_tasks[task_type] = []
            self.failed_tasks[task_type] = []
            print(f"🗑️  [{task_type.value}] 已清空历史: {completed_count} 个已完成, {failed_count} 个失败")
        else:
            for task_type in self.handlers.keys():
                self.clear_history(task_type)
