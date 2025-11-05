# 队列任务管理器使用文档

## 概述

`QueueManager` 是一个通用的异步队列任务管理器，支持多种任务类型，每种任务有独立的队列和处理逻辑。

## 核心特性

- ✅ **多任务类型支持**：每种任务类型有独立的队列
- ✅ **独立处理逻辑**：每种任务由独立的消费者协程处理
- ✅ **动态注册处理器**：支持运行时注册新的任务处理器
- ✅ **任意任务数据**：任务数据可以是任意类型（字典、对象等）
- ✅ **自动重试机制**：任务失败后自动重试，可配置重试次数
- ✅ **单例模式**：全局共享一个队列管理器实例
- ✅ **状态监控**：实时查看队列状态、任务进度
- ✅ **历史记录**：记录已完成和失败的任务

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                      QueueManager                           │
│                      (全局单例)                              │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ TaskType 1   │  │ TaskType 2   │  │ TaskType N   │     │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤     │
│  │  独立队列     │  │  独立队列     │  │  独立队列     │     │
│  │  独立消费者   │  │  独立消费者   │  │  独立消费者   │     │
│  │  独立处理器   │  │  独立处理器   │  │  独立处理器   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## 快速开始

### 1. 基础使用

```python
import asyncio
from telegram_queue_manager import QueueManager, Task, TaskType

# 定义任务处理器
async def my_handler(task_data):
    """处理任务的函数"""
    print(f"处理任务: {task_data}")
    # 执行具体业务逻辑
    await asyncio.sleep(1)
    return True  # 返回 True 表示成功，False 表示失败

async def main():
    # 1. 获取队列管理器实例
    queue_manager = await QueueManager.get_instance()

    # 2. 注册任务处理器
    queue_manager.register_handler(TaskType.TELEGRAM_SHARE, my_handler)

    # 3. 启动队列管理器
    await queue_manager.start()

    # 4. 添加任务
    task = Task(
        task_type=TaskType.TELEGRAM_SHARE,
        task_data={"id": 1, "name": "测试任务"}
    )
    await queue_manager.add_task(task)

    # 5. 等待任务完成
    await queue_manager.wait_completion()

    # 6. 停止队列管理器
    await queue_manager.stop()

asyncio.run(main())
```

### 2. 使用预定义的处理器

```python
from task_handlers import register_all_handlers

async def main():
    # 注册所有预定义的处理器并启动
    await register_all_handlers()

    # 获取队列管理器
    queue_manager = await QueueManager.get_instance()

    # 添加 Telegram 分享任务
    task = Task(
        task_type=TaskType.TELEGRAM_SHARE,
        task_data={
            "resource_id": 1,
            "title": "电影名称",
            "description": "电影描述",
            "link": "分享链接",
            "category": "动作、科幻",
            "file_path": "./poster.jpg"
        }
    )
    await queue_manager.add_task(task)
```

## 核心组件

### 1. TaskType (任务类型枚举)

```python
class TaskType(Enum):
    TELEGRAM_SHARE = "telegram_share"       # Telegram分享任务
    RESOURCE_SYNC = "resource_sync"         # 资源同步任务
    TMDB_UPDATE = "tmdb_update"             # TMDB信息更新任务
    FILE_DOWNLOAD = "file_download"         # 文件下载任务
```

**扩展方式**：在 `TaskType` 枚举中添加新的类型即可。

### 2. Task (任务数据类)

```python
@dataclass
class Task:
    task_type: TaskType          # 任务类型
    task_data: Any              # 任务数据（任意类型）
    task_id: Optional[str]      # 任务ID（可选，自动生成）
    priority: int = 0           # 优先级
    max_retries: int = 3        # 最大重试次数
```

### 3. QueueManager (队列管理器)

#### 主要方法

| 方法 | 说明 |
|------|------|
| `get_instance()` | 获取全局单例实例 |
| `register_handler(task_type, handler)` | 注册任务处理器 |
| `start()` | 启动所有队列处理 |
| `stop()` | 停止所有队列处理 |
| `add_task(task)` | 添加任务到队列 |
| `get_status(task_type)` | 获取队列状态 |
| `wait_completion(task_type)` | 等待任务完成 |
| `get_completed_tasks(task_type)` | 获取已完成任务列表 |
| `get_failed_tasks(task_type)` | 获取失败任务列表 |

## 使用场景

### 场景1：批量分享资源到 Telegram

```python
from resource_manager import ResourceManager

async def batch_share():
    # 初始化资源管理器（会自动使用队列管理器）
    manager = ResourceManager(cookie)

    # 批量分享（任务会自动加入队列顺序执行）
    resource_ids = [1, 2, 3, 4, 5]
    for resource_id in resource_ids:
        await manager.shareToTgBot(resource_id)

    # 等待所有任务完成
    queue_manager = await QueueManager.get_instance()
    await queue_manager.wait_completion(TaskType.TELEGRAM_SHARE)
```

### 场景2：监控任务进度

```python
async def monitor_progress():
    queue_manager = await QueueManager.get_instance()

    while True:
        status = queue_manager.get_status(TaskType.TELEGRAM_SHARE)

        print(f"队列大小: {status['queue_size']}")
        print(f"已完成: {status['completed_count']}")
        print(f"失败: {status['failed_count']}")

        if status['current_task']:
            print(f"当前任务: {status['current_task']['task_id']}")

        await asyncio.sleep(5)
```

### 场景3：自定义任务处理器

```python
async def custom_handler(task_data):
    """自定义处理逻辑"""
    try:
        # 执行业务逻辑
        result = do_something(task_data)
        return True
    except Exception as e:
        print(f"处理失败: {e}")
        return False

# 注册自定义处理器
queue_manager = await QueueManager.get_instance()
queue_manager.register_handler(TaskType.RESOURCE_SYNC, custom_handler)
```

## 预定义的任务处理器

项目提供了以下预定义处理器（在 `task_handlers.py` 中）:

### 1. Telegram 分享处理器

```python
task_data = {
    "resource_id": 1,
    "title": "标题",
    "description": "描述",
    "link": "分享链接",
    "category": "分类",
    "file_path": "图片路径"
}
```

### 2. 资源同步处理器

```python
task_data = {
    "drama_name": "剧名",
    "share_link": "分享链接",
    "savepath": "保存路径"
}
```

### 3. TMDB 更新处理器

```python
task_data = {
    "resource_id": 1,
    "drama_name": "剧名",
    "category": "电影/剧集"
}
```

### 4. 文件下载处理器

```python
task_data = {
    "url": "下载链接",
    "save_path": "保存路径"
}
```

## 配置选项

### 任务重试配置

```python
task = Task(
    task_type=TaskType.TELEGRAM_SHARE,
    task_data=...,
    max_retries=5  # 设置最大重试次数
)
```

### 任务优先级（未来功能）

```python
task = Task(
    task_type=TaskType.TELEGRAM_SHARE,
    task_data=...,
    priority=10  # 优先级（数字越大优先级越高）
)
```

## 测试

### 快速测试

```bash
python3 test_simple_queue.py
```

### 完整示例

```bash
python3 example_queue_usage.py
```

### 测试特定处理器

```bash
python3 task_handlers.py
```

## 项目文件说明

| 文件 | 说明 |
|------|------|
| `telegram_queue_manager.py` | 队列管理器核心实现 |
| `task_handlers.py` | 预定义任务处理器实现 |
| `resource_manager.py` | 资源管理器（已集成队列管理器） |
| `test_simple_queue.py` | 简化测试脚本 |
| `example_queue_usage.py` | 完整使用示例 |

## 注意事项

1. **单例模式**: `QueueManager` 使用单例模式，全局共享一个实例
2. **异步安全**: 所有操作都是异步安全的，使用 `asyncio.Lock` 保护
3. **处理器注册**: 必须在添加任务前注册对应的处理器
4. **自动启动**: 使用 `register_all_handlers()` 会自动启动队列管理器
5. **错误处理**: 任务失败会自动重试，超过最大重试次数后标记为失败
6. **资源清理**: 程序退出前应调用 `queue_manager.stop()` 清理资源

## 常见问题

### Q1: 任务没有被处理？

**A**: 检查是否：
1. 已注册对应任务类型的处理器
2. 已启动队列管理器 (`await queue_manager.start()`)
3. 任务数据格式正确

### Q2: 如何添加新的任务类型？

**A**:
1. 在 `TaskType` 枚举中添加新类型
2. 实现对应的处理器函数
3. 注册处理器: `queue_manager.register_handler(new_type, handler)`

### Q3: 如何查看任务失败原因？

**A**:
```python
failed_tasks = queue_manager.get_failed_tasks(TaskType.TELEGRAM_SHARE)
for task in failed_tasks:
    print(f"任务 {task['task_id']} 失败: {task['error_message']}")
```

### Q4: 多个任务类型会并行处理吗？

**A**: 是的！每种任��类型有独立的消费者协程，不同类型的任务会并行处理，但同一类型的任务会顺序执行。

## 高级用法

### 动态调整任务处理

```python
# 暂停特定任务类型的处理（未来功能）
# await queue_manager.pause(TaskType.TELEGRAM_SHARE)

# 恢复处理
# await queue_manager.resume(TaskType.TELEGRAM_SHARE)
```

### 任务优先级队列（未来功能）

```python
# 使用 PriorityQueue 替代普通 Queue
# 高优先级任务会先被处理
```

## 性能优化建议

1. **批量添加任务**: 一次性添加多个任务，避免频繁调用
2. **合理设置重试次数**: 根据任务特点设置合理的重试次数
3. **监控队列大小**: 避免队列积压过多任务
4. **定期清理历史**: 使用 `clear_history()` 清理历史记录

## 更新日志

### v1.0.0 (2025-01-XX)
- ✨ 初始版本
- ✅ 支持多任务类型
- ✅ 独立队列和处理逻辑
- ✅ 自动重试机制
- ✅ 状态监控功能

---

**作者**: Claude Code
**更新时间**: 2025-01-05
