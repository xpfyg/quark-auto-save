# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
队列管理器完整使用示例
演示如何注册处理器、添加不同类型的任务、监控队列状态
"""
import asyncio
import os
from datetime import datetime

from telegram_queue_manager import QueueManager, Task, TaskType, TaskStatus
from task_handlers import register_all_handlers


async def example_1_basic_usage():
    """
    示例1: 基础使用 - 注册处理器并添加任务
    """
    print("\n" + "=" * 60)
    print("示例1: 基础使用")
    print("=" * 60 + "\n")

    # 1. 获取队列管理器实例
    queue_manager = await QueueManager.get_instance()

    # 2. 注册处理器（这里使用预定义的处理器）
    await register_all_handlers()

    # 3. 创建并添加任务
    task1 = Task(
        task_type=TaskType.TELEGRAM_SHARE,
        task_data={
            "resource_id": 1,
            "title": "测试电影",
            "description": "这是一部测试电影",
            "link": "https://example.com/share1",
            "category": "动作、科幻",
            "file_path": "./test/poster1.jpg"
        }
    )

    await queue_manager.add_task(task1)

    # 4. 等待一段时间观察处理
    print("\n⏳ 等待5秒观察任务处理...")
    await asyncio.sleep(5)

    # 5. 查看队列状态
    status = queue_manager.get_status(TaskType.TELEGRAM_SHARE)
    print("\n📊 队列状态:")
    print(f"  • 运行中: {status['is_running']}")
    print(f"  • 队列大小: {status['queue_size']}")
    print(f"  • 已完成: {status['completed_count']}")
    print(f"  • 失败: {status['failed_count']}")


async def example_2_batch_tasks():
    """
    示例2: 批量添加不同类型的任务
    """
    print("\n" + "=" * 60)
    print("示例2: 批量添加不同类型的任务")
    print("=" * 60 + "\n")

    queue_manager = await QueueManager.get_instance()

    # 添加多个 Telegram 分享任务
    telegram_tasks = [
        {
            "resource_id": i,
            "title": f"测试资源{i}",
            "description": f"这是测试资源{i}的描述",
            "link": f"https://example.com/share{i}",
            "category": "动作、科幻",
            "file_path": f"./test/poster{i}.jpg"
        }
        for i in range(1, 4)
    ]

    for task_data in telegram_tasks:
        task = Task(task_type=TaskType.TELEGRAM_SHARE, task_data=task_data)
        await queue_manager.add_task(task)

    # 添加 TMDB 更新任务
    tmdb_tasks = [
        {
            "resource_id": i,
            "drama_name": f"测试剧集{i}",
            "category": "剧集"
        }
        for i in range(4, 6)
    ]

    for task_data in tmdb_tasks:
        task = Task(task_type=TaskType.TMDB_UPDATE, task_data=task_data)
        await queue_manager.add_task(task)

    # 添加文件下载任务
    download_tasks = [
        {
            "url": "https://example.com/image1.jpg",
            "save_path": "./downloads/image1.jpg"
        },
        {
            "url": "https://example.com/image2.jpg",
            "save_path": "./downloads/image2.jpg"
        }
    ]

    for task_data in download_tasks:
        task = Task(task_type=TaskType.FILE_DOWNLOAD, task_data=task_data)
        await queue_manager.add_task(task)

    # 查看所有队列状态
    print("\n📊 所有队列状态:")
    all_status = queue_manager.get_status()
    for task_type, status in all_status["task_types"].items():
        print(f"\n[{task_type}]")
        print(f"  • 队列大小: {status['queue_size']}")
        print(f"  • 已完成: {status['completed_count']}")
        print(f"  • 失败: {status['failed_count']}")


async def example_3_monitor_progress():
    """
    示例3: 实时监控任务进度
    """
    print("\n" + "=" * 60)
    print("示例3: 实时监控任务进度")
    print("=" * 60 + "\n")

    queue_manager = await QueueManager.get_instance()

    # 实时监控10秒
    print("🔍 开始监控任务进度 (10秒)...\n")
    for i in range(10):
        all_status = queue_manager.get_status()

        print(f"[{datetime.now().strftime('%H:%M:%S')}] 队列状态:")

        for task_type, status in all_status["task_types"].items():
            # 只显示有任务的队列
            if status['queue_size'] > 0 or status['current_task']:
                print(f"  [{task_type}]")
                print(f"    队列剩余: {status['queue_size']} 个")

                if status['current_task']:
                    current = status['current_task']
                    print(f"    当前任务: {current['task_id']}")
                    print(f"    已运行: {current['elapsed_seconds']} 秒")

                print(f"    已完成/失败: {status['completed_count']}/{status['failed_count']}")

        print()
        await asyncio.sleep(1)


async def example_4_with_resource_manager():
    """
    示例4: 与 ResourceManager 集成使用
    """
    print("\n" + "=" * 60)
    print("示例4: 与 ResourceManager 集成")
    print("=" * 60 + "\n")

    try:
        from resource_manager import ResourceManager
        from dotenv import load_dotenv

        load_dotenv()
        cookie = os.environ.get("QUARK_COOKIE", "")

        if not cookie:
            print("❌ 未配置 QUARK_COOKIE，跳过此示例")
            return

        # 确保处理器已注册
        await register_all_handlers()

        # 初始化资源管理器
        print("🔧 初始化 ResourceManager...")
        manager = ResourceManager(cookie)

        # 批量分享资源（假设数据库中有ID为1-5的资源）
        resource_ids = [1, 2, 3, 4, 5]

        print(f"\n📤 批量分享 {len(resource_ids)} 个资源...")
        for resource_id in resource_ids:
            try:
                result = await manager.shareToTgBot(resource_id)
                if result:
                    print(f"✅ 资源 {resource_id} 已加入队列")
                else:
                    print(f"❌ 资源 {resource_id} 加入队列失败")
            except Exception as e:
                print(f"❌ 资源 {resource_id} 处理异常: {e}")

        # 查看队列状态
        queue_manager = await QueueManager.get_instance()
        status = queue_manager.get_status(TaskType.TELEGRAM_SHARE)
        print(f"\n📊 Telegram分享队列状态:")
        print(f"  • 队列大小: {status['queue_size']}")
        print(f"  • 已完成: {status['completed_count']}")
        print(f"  • 失败: {status['failed_count']}")

        # 等待所有任务完成
        print("\n⏳ 等待所有任务完成...")
        await queue_manager.wait_completion(TaskType.TELEGRAM_SHARE)
        print("✅ 所有任务已处理完毕")

    except ImportError as e:
        print(f"❌ 导入失败: {e}")
    except Exception as e:
        print(f"❌ 示例执行异常: {e}")
        import traceback
        traceback.print_exc()


async def example_5_custom_handler():
    """
    示例5: 注册自定义任务处理器
    """
    print("\n" + "=" * 60)
    print("示例5: 注册自定义任务处理器")
    print("=" * 60 + "\n")

    # 1. 定义自定义任务类型（需要在 TaskType 枚举中添加）
    # 这里使用现有的 RESOURCE_SYNC 类型作为示例

    # 2. 定义自定义处理器函数
    async def custom_handler(task_data):
        """自定义处理器示例"""
        print(f"🔧 处理自定义任务: {task_data}")
        # 模拟耗时操作
        await asyncio.sleep(2)
        print(f"✅ 自定义任务处理完成")
        return True

    # 3. 获取队列管理器并注册处理器
    queue_manager = await QueueManager.get_instance()
    queue_manager.register_handler(TaskType.RESOURCE_SYNC, custom_handler)

    # 4. 启动队列管理器（如果还未启动）
    if not queue_manager.is_running:
        await queue_manager.start()

    # 5. 添加任务
    task = Task(
        task_type=TaskType.RESOURCE_SYNC,
        task_data={
            "custom_field": "自定义数据",
            "value": 12345
        }
    )
    await queue_manager.add_task(task)

    # 6. 等待任务完成
    await asyncio.sleep(5)

    # 7. 查看结果
    completed = queue_manager.get_completed_tasks(TaskType.RESOURCE_SYNC, limit=5)
    print(f"\n📋 已完成的任务: {len(completed)} 个")
    for task_info in completed:
        print(f"  • {task_info['task_id']} - {task_info['status']}")


async def example_6_error_handling():
    """
    示例6: 错误处理和重试机制
    """
    print("\n" + "=" * 60)
    print("示例6: 错误处理和重试机制")
    print("=" * 60 + "\n")

    # 定义一个会失败的处理器
    attempt_count = 0

    async def failing_handler(task_data):
        """模拟失败的处理器"""
        nonlocal attempt_count
        attempt_count += 1
        print(f"🔧 第 {attempt_count} 次尝试处理任务...")

        # 前2次失败，第3次成功
        if attempt_count < 3:
            print(f"❌ 任务失败（模拟）")
            raise Exception("模拟失败")
        else:
            print(f"✅ 任务成功")
            return True

    # 注册处理器
    queue_manager = await QueueManager.get_instance()
    queue_manager.register_handler(TaskType.RESOURCE_SYNC, failing_handler)

    if not queue_manager.is_running:
        await queue_manager.start()

    # 添加任务（设置最大重试次数）
    task = Task(
        task_type=TaskType.RESOURCE_SYNC,
        task_data={"test": "retry_test"},
        max_retries=5  # 允许重试5次
    )
    await queue_manager.add_task(task)

    # 等待任务处理完成
    await asyncio.sleep(15)

    # 查看结果
    completed = queue_manager.get_completed_tasks(TaskType.RESOURCE_SYNC)
    failed = queue_manager.get_failed_tasks(TaskType.RESOURCE_SYNC)

    print(f"\n📊 结果:")
    print(f"  • 已完成: {len(completed)} 个")
    print(f"  • 失败: {len(failed)} 个")

    if completed:
        print(f"\n✅ 任务最终成功，共重试 {attempt_count - 1} 次")


async def main():
    """主函数 - 运行所有示例"""
    print("\n" + "=" * 60)
    print("队列管理器完整使用示例")
    print("=" * 60)

    try:
        # 运行示例1: 基础使用
        await example_1_basic_usage()

        # 运行示例2: 批量任务
        await example_2_batch_tasks()

        # 运行示例3: 监控进度
        await example_3_monitor_progress()

        # 运行示例5: 自定义处理器
        await example_5_custom_handler()

        # 运行示例6: 错误处理
        await example_6_error_handling()

        # 可选：运行示例4（需要配置环境变量）
        # await example_4_with_resource_manager()

    except KeyboardInterrupt:
        print("\n\n⚠️  程序被用户中断")
    except Exception as e:
        print(f"\n\n❌ 程序异常: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理资源
        print("\n🧹 清理资源...")
        queue_manager = await QueueManager.get_instance()
        await queue_manager.stop()
        print("✅ 程序结束")


if __name__ == "__main__":
    asyncio.run(main())
