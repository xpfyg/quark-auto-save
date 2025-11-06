# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务模块
功能：定期检查云盘资源链接的有效性
"""
import os
import time
import random
import logging
from datetime import datetime

from db import db_session
from model.cloud_resource import CloudResource
from resource_manager import ResourceManager


def check_all_resources_links():
    """
    定时任务：检查所有未失效资源的链接有效性

    功能：
    - 遍历所有未失效的资源
    - 调用 check_share_link 检测链接是否失效
    - 每个链接检测后随机间隔 1-3 秒
    - 每检测 10 次后间隔 10 秒
    """
    try:
        logging.info("=" * 60)
        logging.info(f"🔍 开始检查资源链接有效性 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logging.info("=" * 60)

        # 获取 Quark Cookie
        cookie = os.environ.get("QUARK_COOKIE", "")
        if not cookie:
            logging.error("❌ 未配置 QUARK_COOKIE，无法执行检查任务")
            return

        # 创建资源管理器
        manager = ResourceManager(cookie)

        # 查询所有未失效的资源
        resources = db_session.query(CloudResource).filter(
            CloudResource.is_expired == 0,
            CloudResource.link.isnot(None)
        ).all()

        if not resources:
            logging.info("ℹ️  没有需要检查的资源")
            return

        total_count = len(resources)
        valid_count = 0
        invalid_count = 0
        error_count = 0

        logging.info(f"📊 共找到 {total_count} 个未失效资源需要检查")
        logging.info("")

        for index, resource in enumerate(resources, start=1):
            try:
                logging.info(f"[{index}/{total_count}] 检查资源: {resource.drama_name}")
                logging.info(f"  └─ 链接: {resource.link}")

                # 检查链接有效性
                is_valid = manager.check_share_link(resource.link)

                if is_valid:
                    valid_count += 1
                    logging.info(f"  ✅ 链接有效")
                else:
                    invalid_count += 1
                    logging.info(f"  ❌ 链接已失效")

                # 每个链接检测后随机间隔 1-3 秒
                if index < total_count:  # 最后一个不需要等待
                    wait_time = random.uniform(1, 3)
                    logging.info(f"  ⏱️  等待 {wait_time:.1f} 秒...")
                    time.sleep(wait_time)

                # 每检测 10 次后额外间隔 10 秒
                if index % 10 == 0 and index < total_count:
                    logging.info(f"  ⏸️  已检测 {index} 个资源，休息 10 秒...")
                    time.sleep(10)

                logging.info("")

            except Exception as e:
                error_count += 1
                logging.error(f"  ❌ 检查资源失败: {str(e)}")
                import traceback
                traceback.print_exc()
                logging.info("")
                continue

        # 输出统计信息
        logging.info("=" * 60)
        logging.info("📈 检查完成 - 统计结果")
        logging.info("=" * 60)
        logging.info(f"总数量: {total_count}")
        logging.info(f"✅ 有效: {valid_count}")
        logging.info(f"❌ 失效: {invalid_count}")
        logging.info(f"⚠️  错误: {error_count}")
        logging.info(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logging.info("=" * 60)

    except Exception as e:
        logging.error(f"❌ 定时任务执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理数据库会话
        db_session.remove()


def register_jobs(scheduler):
    """
    注册所有定时任务

    Args:
        scheduler: APScheduler 实例
    """
    # 添加资源链接检查任务
    # 每天凌晨 2 点执行
    scheduler.add_job(
        id='check_resources_links',
        func=check_all_resources_links,
        trigger='cron',
        hour=2,
        minute=0,
        replace_existing=True
    )

    logging.info("✅ 定时任务已注册:")
    logging.info("  - check_resources_links: 每天 02:00 检查资源链接有效性")


if __name__ == "__main__":
    # 测试任务
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s][%(levelname)s] %(message)s",
        datefmt="%m-%d %H:%M:%S",
    )

    print("开始测试资源链接检查任务...")
    check_all_resources_links()
