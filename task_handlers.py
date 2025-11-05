# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务处理器实现
定义各种任务类型的具体处理逻辑
"""
import asyncio
import os
import time
from datetime import datetime
from typing import Dict, Any

from telegram_queue_manager import QueueManager, TaskType


# ============================================================================
# Telegram 分享任务处理器
# ============================================================================

async def handle_telegram_share(task_data: Dict[str, Any]) -> bool:
    """
    处理 Telegram 分享任务

    Args:
        task_data: 包含以下字段的字典
            - resource_id: int - 资源ID
            - title: str - 标题
            - description: str - 描述
            - link: str - 分享链接
            - category: str - 分类
            - file_path: str - 文件路径

    Returns:
        bool: 是否成功
    """
    from telegram_sdk.tg import TgClient
    from db import db_session
    from model.cloud_resource import CloudResource

    try:
        resource_id = task_data["resource_id"]
        title = task_data["title"]
        description = task_data["description"]
        link = task_data["link"]
        category = task_data["category"]
        file_path = task_data["file_path"]

        print(f"📤 开始发送到 Telegram: {title}")

        # 获取 TgClient 单例
        tg_client = await TgClient.get_instance()

        # 发送到 Telegram
        result = await tg_client.sendToTgBotForQuark1(
            title, description, link, category, file_path
        )

        if result:
            # 更新数据库
            resource = db_session.query(CloudResource).filter(
                CloudResource.id == resource_id
            ).first()

            if resource:
                resource.share_count = (resource.share_count or 0) + 1
                resource.last_share_time = datetime.now()
                resource.update_time = datetime.now()
                db_session.commit()
                print(f"💾 数据库已更新: 资源ID {resource_id}, 分享次数 {resource.share_count}")
            else:
                print(f"⚠️  未找到资源ID: {resource_id}")

            return True
        else:
            print(f"❌ Telegram 发送失败: {title}")
            return False

    except KeyError as e:
        print(f"❌ 任务数据缺少必需字段: {e}")
        return False
    except Exception as e:
        print(f"❌ Telegram 分享任务处理异常: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# 资源同步任务处理器
# ============================================================================

async def handle_resource_sync(task_data: Dict[str, Any]) -> bool:
    """
    处理资源同步任务

    Args:
        task_data: 包含以下字段的字典
            - drama_name: str - 剧名
            - share_link: str - 分享链接
            - savepath: str - 保存路径

    Returns:
        bool: 是否成功
    """
    try:
        drama_name = task_data["drama_name"]
        share_link = task_data["share_link"]
        savepath = task_data.get("savepath", "/")

        print(f"🔄 开始同步��源: {drama_name}")
        print(f"🔗 分享链接: {share_link}")
        print(f"📁 保存路径: {savepath}")

        # 这里可以调用 ResourceManager 的 process_resource 方法
        # 为了演示，这里简化实现
        from resource_manager import ResourceManager
        from dotenv import load_dotenv

        load_dotenv()
        cookie = os.environ.get("QUARK_COOKIE", "")

        if not cookie:
            print("❌ 未配置 QUARK_COOKIE")
            return False

        manager = ResourceManager(cookie)
        result = manager.process_resource(drama_name, share_link, savepath)

        if result and result["status"] in ["existing", "saved"]:
            print(f"✅ 资源同步成功: {drama_name}")
            return True
        else:
            print(f"❌ 资源同步失败: {drama_name}")
            return False

    except KeyError as e:
        print(f"❌ 任务数据缺少必需字段: {e}")
        return False
    except Exception as e:
        print(f"❌ 资源同步任务处理异常: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# TMDB 更新任务处理器
# ============================================================================

async def handle_tmdb_update(task_data: Dict[str, Any]) -> bool:
    """
    处理 TMDB 信息更新任务

    Args:
        task_data: 包含以下字段的字典
            - resource_id: int - 资源ID
            - drama_name: str - 剧名
            - category: str - 类型（电影/剧集）

    Returns:
        bool: 是否成功
    """
    try:
        resource_id = task_data["resource_id"]
        drama_name = task_data["drama_name"]
        category = task_data.get("category", "电影")

        print(f"🎬 开始更新 TMDB 信息: {drama_name}")

        from resource_manager import TmdbService
        from db import db_session
        from model.cloud_resource import CloudResource
        from model.tmdb import Tmdb

        # 查询 TMDB 信息
        tmdb_service = TmdbService()
        tmdb_data = tmdb_service.search_drama(drama_name, category=category)

        if not tmdb_data:
            print(f"⚠️  未找到 TMDB 信息: {drama_name}")
            return False

        # 检查 TMDB 是否已存在
        existing_tmdb = db_session.query(Tmdb).filter(
            Tmdb.title == tmdb_data["title"],
            Tmdb.year_released == tmdb_data["year_released"]
        ).first()

        if not existing_tmdb:
            # 保存新的 TMDB 信息
            new_tmdb = Tmdb(**tmdb_data)
            db_session.add(new_tmdb)
            db_session.flush()
            tmdb_id = new_tmdb.id
            print(f"✅ TMDB 信息已保存: {new_tmdb.title} ({new_tmdb.year_released})")
        else:
            tmdb_id = existing_tmdb.id
            print(f"✅ TMDB 信息已存在: {existing_tmdb.title}")

        # 更新资源关联
        db_session.query(CloudResource).filter(
            CloudResource.id == resource_id
        ).update({
            CloudResource.tmdb_id: tmdb_id
        })
        db_session.commit()

        print(f"✅ 资源 {resource_id} 已关联 TMDB 信息")
        return True

    except KeyError as e:
        print(f"❌ 任务数据缺少必需字段: {e}")
        return False
    except Exception as e:
        print(f"❌ TMDB 更新任务处理异常: {e}")
        import traceback
        traceback.print_exc()
        db_session.rollback()
        return False


# ============================================================================
# 文件下载任务处理器
# ============================================================================

async def handle_file_download(task_data: Dict[str, Any]) -> bool:
    """
    处理文件下载任务

    Args:
        task_data: 包含以下字段的字典
            - url: str - 下载链接
            - save_path: str - 保存路径

    Returns:
        bool: 是否成功
    """
    try:
        url = task_data["url"]
        save_path = task_data["save_path"]

        print(f"📥 开始下载文件: {url}")
        print(f"💾 保存到: {save_path}")

        from quark_auto_save import download_file

        # 确保目录存在
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        # 下载文件
        download_file(url, save_path)

        # 检查文件是否存在
        if os.path.exists(save_path):
            file_size = os.path.getsize(save_path)
            print(f"✅ 文件下载成功: {save_path} ({file_size} 字节)")
            return True
        else:
            print(f"❌ 文件下载失败: {save_path}")
            return False

    except KeyError as e:
        print(f"❌ 任务数据缺少必需字段: {e}")
        return False
    except Exception as e:
        print(f"❌ 文件下载任务处理异常: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# 注册所有任务处理器
# ============================================================================

async def register_all_handlers():
    """
    注册所有任务处理器到队列管理器
    """
    print("\n" + "=" * 60)
    print("注册任务处理器")
    print("=" * 60)

    # 获取队列管理器实例
    queue_manager = await QueueManager.get_instance()

    # 注册各种任务处理器
    queue_manager.register_handler(TaskType.TELEGRAM_SHARE, handle_telegram_share)
    queue_manager.register_handler(TaskType.RESOURCE_SYNC, handle_resource_sync)
    queue_manager.register_handler(TaskType.TMDB_UPDATE, handle_tmdb_update)
    queue_manager.register_handler(TaskType.FILE_DOWNLOAD, handle_file_download)

    # 启动队列管理器
    await queue_manager.start()

    print("\n✅ 所有任务处理器已注册并启动")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    # 测试：注册所有处理器
    asyncio.run(register_all_handlers())
