# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版测试脚本 - 快速测试队列管理器功能
"""
import asyncio
from telegram_queue_manager import QueueManager, Task, TaskType


# 定义一个简单的测试处理器
async def test_handler(task_data):
    """测试处理器 - 打印任务数据并模拟处理"""
    print(f"  ➡️  处理任务数据: {task_data}")
    await asyncio.sleep(2)  # 模拟耗时操作
    print(f"  ✅ 任务处理完成")
    return True


async def quick_test():
    """快速测试"""
    print("=" * 60)
    print("队列管理器快速测试")
    print("=" * 60 + "\n")

    # 1. 获取队列管理器实例
    print("1️⃣  获取队列管理器实例...")
    queue_manager = await QueueManager.get_instance()

    # 2. 注册测试处理器
    print("2️⃣  注册测试处理器...")
    queue_manager.register_handler(TaskType.TELEGRAM_SHARE, test_handler)
    queue_manager.register_handler(TaskType.RESOURCE_SYNC, test_handler)

    # 3. 启动队列管理器
    print("3️⃣  启动队列管理器...")
    await queue_manager.start()

    # 4. 添加测试任务
    print("\n4️⃣  添加测试任务...\n")

    # 添加3个 Telegram 分享任务
    for i in range(1, 4):
        task = Task(
            task_type=TaskType.TELEGRAM_SHARE,
            task_data={
                "id": i,
                "name": f"测试任务 {i}",
                "type": "telegram_share"
            }
        )
        await queue_manager.add_task(task)

    # 添加2个资源同步任务
    for i in range(4, 6):
        task = Task(
            task_type=TaskType.RESOURCE_SYNC,
            task_data={
                "id": i,
                "name": f"测试任务 {i}",
                "type": "resource_sync"
            }
        )
        await queue_manager.add_task(task)

    # 5. 监控队列状态
    print("\n5️⃣  监控队列状态（15秒）...\n")
    for _ in range(15):
        status = queue_manager.get_status()

        if status["is_running"]:
            print(f"��� 队列状态:")
            for task_type, type_status in status["task_types"].items():
                if type_status["queue_size"] > 0 or type_status["current_task"]:
                    print(f"  [{task_type}]")
                    print(f"    队列: {type_status['queue_size']} 个")
                    print(f"    完成/失败: {type_status['completed_count']}/{type_status['failed_count']}")
                    if type_status["current_task"]:
                        print(f"    当前任务: {type_status['current_task']['task_id']}")
            print()

        await asyncio.sleep(1)

    # 6. 等待所有任务完成
    print("6️⃣  等待所有任务完成...")
    await queue_manager.wait_completion()

    # 7. 查看最终结果
    print("\n7️⃣  最终结果:\n")
    final_status = queue_manager.get_status()

    for task_type, type_status in final_status["task_types"].items():
        print(f"[{task_type}]")
        print(f"  ✅ 已完成: {type_status['completed_count']} 个")
        print(f"  ❌ 失败: {type_status['failed_count']} 个")
        print()

    # 8. 停止队列管理器
    print("8️⃣  停止队列管理器...")
    await queue_manager.stop()

    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(quick_test())
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被中断")
    except Exception as e:
        print(f"\n\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
