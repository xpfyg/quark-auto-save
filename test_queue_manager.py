# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Telegram 队列管理器
演示如何使用队列管理器批量处理分享任务
"""
import asyncio
from datetime import datetime
from telegram_queue_manager import TelegramQueueManager, ShareTask


async def test_basic_queue():
    """测试基础队列功能"""
    print("=" * 60)
    print("测试1: 基础队列功能")
    print("=" * 60)

    # 获取队列管理器实例
    queue_manager = await TelegramQueueManager.get_instance()

    # 创建测试任务（模拟数据）
    test_tasks = [
        ShareTask(
            resource_id=1,
            title="测试电影1",
            description="这是一部测试电影的描述信息",
            link="https://example.com/share1",
            category="动作、科幻",
            file_path="/tmp/test1.jpg"
        ),
        ShareTask(
            resource_id=2,
            title="测试剧集2",
            description="这是一部测试剧集的描述信息",
            link="https://example.com/share2",
            category="剧情、爱情",
            file_path="/tmp/test2.jpg"
        ),
        ShareTask(
            resource_id=3,
            title="测试动漫3",
            description="这是一部测试动漫的描述信息",
            link="https://example.com/share3",
            category="动画、冒险",
            file_path="/tmp/test3.jpg"
        ),
    ]

    # 批量添加任务
    print("\n📦 批量添加任务到队列...")
    for task in test_tasks:
        await queue_manager.add_task(task)

    # 查看队列状态
    print("\n📊 队列状态:")
    status = queue_manager.get_status()
    print(f"  • 运行状态: {'运行中' if status['is_running'] else '已停止'}")
    print(f"  • 队列大小: {status['queue_size']}")
    print(f"  • 已完成: {status['completed_count']}")
    print(f"  • 失败: {status['failed_count']}")

    # 等待所有任务完成（这里只是演示，实际使用中会真正执行）
    print("\n⏳ 等待任务处理...(按 Ctrl+C 停止)")
    try:
        # 等待一段时间，观察队列处理
        await asyncio.sleep(10)
    except KeyboardInterrupt:
        print("\n⚠️  用户中断")

    # 最终状态
    print("\n📊 最终状态:")
    final_status = queue_manager.get_status()
    print(f"  • 队列大小: {final_status['queue_size']}")
    print(f"  • 已完成: {final_status['completed_count']}")
    print(f"  • 失败: {final_status['failed_count']}")


async def test_status_monitoring():
    """测试状态监控功能"""
    print("\n" + "=" * 60)
    print("测试2: 状态监控")
    print("=" * 60)

    queue_manager = await TelegramQueueManager.get_instance()

    # 实时监控队列状态
    print("\n🔍 开始监控队列状态 (10秒)...")
    for i in range(10):
        status = queue_manager.get_status()

        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 队列状态:")
        print(f"  • 队列剩余: {status['queue_size']} 个任务")

        if status['current_task']:
            current = status['current_task']
            print(f"  • 当前任务: {current['title']}")
            print(f"  • 已运行: {current['elapsed_seconds']} 秒")

        print(f"  • 已完成: {status['completed_count']} 个")
        print(f"  • 失败: {status['failed_count']} 个")

        await asyncio.sleep(1)


async def test_with_resource_manager():
    """测试与 ResourceManager 集成"""
    print("\n" + "=" * 60)
    print("测试3: 与 ResourceManager 集成")
    print("=" * 60)

    try:
        from resource_manager import ResourceManager
        from dotenv import load_dotenv
        import os

        load_dotenv()
        cookie = os.environ.get("QUARK_COOKIE", "")

        if not cookie:
            print("❌ 未配置 QUARK_COOKIE 环境变量，跳过此测试")
            return

        # 初始化资源管理器
        print("\n🔧 初始化 ResourceManager...")
        manager = ResourceManager(cookie)

        # 模拟批量分享资源（这里使用假的资源ID）
        # 实际使用时，应该从数据库查询真实的资源ID
        test_resource_ids = [1, 2, 3]  # 替换为真实的资源ID

        print(f"\n📤 批量分享 {len(test_resource_ids)} 个资源...")
        for resource_id in test_resource_ids:
            try:
                result = await manager.shareToTgBot(resource_id)
                if result:
                    print(f"✅ 资源 {resource_id} 已加入队列")
                else:
                    print(f"❌ 资源 {resource_id} 加入队列失败")
            except Exception as e:
                print(f"❌ 资源 {resource_id} 处理异常: {e}")

        # 查看队列状态
        queue_manager = await TelegramQueueManager.get_instance()
        status = queue_manager.get_status()
        print(f"\n📊 队列状态: {status['queue_size']} 个任务等待处理")

    except ImportError as e:
        print(f"❌ 导入失败: {e}")
    except Exception as e:
        print(f"❌ 测试异常: {e}")


async def test_queue_operations():
    """测试队列操作"""
    print("\n" + "=" * 60)
    print("测试4: 队列操作")
    print("=" * 60)

    queue_manager = await TelegramQueueManager.get_instance()

    # 测试获取已完成任务
    print("\n📋 已完成的任务:")
    completed = queue_manager.get_completed_tasks(limit=5)
    if completed:
        for task in completed:
            print(f"  • {task['title']} - {task['status']} - {task['complete_time']}")
    else:
        print("  (暂无已完成任务)")

    # 测试获取失败任务
    print("\n❌ 失败的任务:")
    failed = queue_manager.get_failed_tasks(limit=5)
    if failed:
        for task in failed:
            print(f"  • {task['title']} - {task['error_message']}")
    else:
        print("  (暂无失败任务)")


async def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("Telegram 队列管理器测试程序")
    print("=" * 60)

    try:
        # 运行各项测试
        await test_basic_queue()
        await test_status_monitoring()
        await test_queue_operations()

        # 可选：测试与 ResourceManager 集成
        # await test_with_resource_manager()

    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理资源
        print("\n🧹 清理资源...")
        queue_manager = await TelegramQueueManager.get_instance()
        await queue_manager.stop()
        print("✅ 测试完成")


if __name__ == "__main__":
    asyncio.run(main())
