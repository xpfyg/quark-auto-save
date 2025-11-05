# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试队列管理器在 Flask 中是否正常工作
"""
import requests
import time
import json


def test_queue_status(base_url="http://localhost:5005"):
    """测试队列状态 API"""
    print("\n" + "=" * 60)
    print("测试队列管理器状态")
    print("=" * 60 + "\n")

    # 首先需要登录
    session = requests.Session()

    # 这里需要替换为实际的用户名和密码
    login_data = {
        "username": "admin",
        "password": "admin123"
    }

    print("1️⃣  登录系统...")
    login_response = session.post(f"{base_url}/login", data=login_data)

    if login_response.status_code == 200:
        print("✅ 登录成功\n")
    else:
        print("❌ 登录失败")
        return

    # 检查队列状态
    print("2️⃣  获取队列状态...")
    status_response = session.get(f"{base_url}/api/queue_status")

    if status_response.status_code == 200:
        data = status_response.json()
        if data.get("success"):
            print("✅ 队列管理器运行正常\n")
            print("📊 队列状态:")
            print(json.dumps(data["status"], indent=2, ensure_ascii=False))
        else:
            print("❌ 队列管理器未运行")
            print(data)
    else:
        print(f"❌ 请求失败: {status_response.status_code}")
        print(status_response.text)


def test_add_share_task(resource_id, base_url="http://localhost:5005"):
    """测试添加分享任务"""
    print("\n" + "=" * 60)
    print(f"测试添加分享任务 (资源ID: {resource_id})")
    print("=" * 60 + "\n")

    session = requests.Session()

    # 登录
    login_data = {
        "username": "admin",
        "password": "admin123"
    }

    print("1️⃣  登录系统...")
    login_response = session.post(f"{base_url}/login", data=login_data)

    if login_response.status_code != 200:
        print("❌ 登录失败")
        return

    print("✅ 登录成功\n")

    # 添加分享任务
    print(f"2️⃣  添加资源 {resource_id} 到分享队列...")
    share_response = session.post(f"{base_url}/api/share_to_tg/{resource_id}")

    if share_response.status_code == 200:
        data = share_response.json()
        if data.get("success"):
            print("✅ 任务已成功加入队列\n")
            print(f"   消息: {data.get('message')}")
        else:
            print("❌ 任务加入失败")
            print(data)
    else:
        print(f"❌ 请求失败: {share_response.status_code}")
        print(share_response.text)

    # 等待一段时间后查看队列状态
    print("\n3️⃣  等待 5 秒后查看队列状态...")
    time.sleep(5)

    status_response = session.get(f"{base_url}/api/queue_status")
    if status_response.status_code == 200:
        data = status_response.json()
        if data.get("success"):
            print("\n📊 当前队列状态:")
            status = data["status"]
            task_types = status.get("task_types", {})

            for task_type, type_status in task_types.items():
                print(f"\n[{task_type}]")
                print(f"  队列大小: {type_status['queue_size']}")
                print(f"  已完成: {type_status['completed_count']}")
                print(f"  失败: {type_status['failed_count']}")

                if type_status.get('current_task'):
                    current = type_status['current_task']
                    print(f"  当前任务: {current['task_id']}")
                    print(f"  运行时间: {current['elapsed_seconds']} 秒")


def monitor_queue(duration=30, interval=5, base_url="http://localhost:5005"):
    """持续监控队列状态"""
    print("\n" + "=" * 60)
    print(f"持续监控队列状态 ({duration} 秒)")
    print("=" * 60 + "\n")

    session = requests.Session()

    # 登录
    login_data = {
        "username": "admin",
        "password": "admin123"
    }

    session.post(f"{base_url}/login", data=login_data)

    start_time = time.time()

    while time.time() - start_time < duration:
        response = session.get(f"{base_url}/api/queue_status")

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"\n[{time.strftime('%H:%M:%S')}] 队列状态:")

                status = data["status"]
                task_types = status.get("task_types", {})

                for task_type, type_status in task_types.items():
                    if type_status['queue_size'] > 0 or type_status.get('current_task'):
                        print(f"  [{task_type}]")
                        print(f"    队列: {type_status['queue_size']} 个")
                        print(f"    完成/失败: {type_status['completed_count']}/{type_status['failed_count']}")

                        if type_status.get('current_task'):
                            current = type_status['current_task']
                            print(f"    当前: {current['task_id']} ({current['elapsed_seconds']}s)")

        time.sleep(interval)

    print("\n✅ 监控结束")


if __name__ == "__main__":
    import sys

    print("\n队列管理器测试工具\n")
    print("请选择测试项:")
    print("1. 检查队列状态")
    print("2. 添加分享任务 (需要资源ID)")
    print("3. 持续监控队列")
    print()

    choice = input("请输入选项 (1/2/3): ").strip()

    if choice == "1":
        test_queue_status()
    elif choice == "2":
        resource_id = input("请输入资源ID: ").strip()
        if resource_id.isdigit():
            test_add_share_task(int(resource_id))
        else:
            print("❌ 无效的资源ID")
    elif choice == "3":
        duration = input("监控时长（秒，默认30）: ").strip()
        duration = int(duration) if duration.isdigit() else 30
        monitor_queue(duration=duration)
    else:
        print("❌ 无效的选项")
