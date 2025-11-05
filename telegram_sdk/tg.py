"""
Telegram 客户端核心类（全局单例模式）
"""
import asyncio
import os
import random
import time
from datetime import datetime

import socks
from dotenv import load_dotenv
from telethon import TelegramClient

load_dotenv()
TG_API_ID = os.environ.get("TG_API_ID", "")
TG_API_HASH = os.environ.get("TG_API_HASH", "")
TG_SESSION_NAME = os.environ.get("TG_SESSION_NAME", "quark_bot")  # 默认值
proxy_host = os.environ.get("TG_PROXY_HOST", "127.0.0.1")
proxy_port = os.environ.get("TG_PROXY_PORT", 7890)
my_proxy = (socks.SOCKS5, proxy_host, proxy_port)

# 设置 session 文件保存目录
SESSION_DIR = os.environ.get("TG_SESSION_DIR", "./sessions")

# 确保 session 目录存在
if not os.path.exists(SESSION_DIR):
    os.makedirs(SESSION_DIR, exist_ok=True)
    print(f"✅ 创建 Telegram Session 目录: {SESSION_DIR}")

class TgClient:
    """
    Telegram 客户端（单例模式）

    设计原则：
    1. 全局共享一个 TelegramClient 实例，避免多次连接同一个 session 文件
    2. 使用异步锁确保投稿操作串行执行
    3. 懒加载：首次使用时才初始化连接
    4. 连接复用：避免频繁创建和销毁连接
    """

    # 类级别的单例实例
    _instance = None
    _instance_lock = asyncio.Lock()  # 保护单例创建过程

    # 类级别的异步锁，确保全局只有一个投稿操作在执行
    _submission_lock = asyncio.Lock()
    _waiting_count = 0  # 等待的任务数量
    def __init__(self, api_id=TG_API_ID, api_hash=TG_API_HASH, session_name=TG_SESSION_NAME, proxy=my_proxy):
        """
        私有构造函数，不应直接调用
        请使用 TgClient.get_instance() 获取单例
        """
        print(f"✅ 初始化 Telegram 客户端单例: {session_name}")
        self.api_id = api_id
        self.api_hash = api_hash
        # 确保 session 文件保存在指定目录
        if not session_name:
            session_name = "quark_bot"
        # 如果 session_name 不包含路径，添加目录前缀
        if os.path.dirname(session_name) == "":
            self.session_name = os.path.join(SESSION_DIR, session_name)
        else:
            self.session_name = session_name
        self.proxy = proxy
        self.client = None
        self._started = False

    @classmethod
    async def get_instance(cls):
        """
        获取全局单例实例（异步安全）

        Returns:
            TgClient: 全局唯一的 TgClient 实例
        """
        if cls._instance is None:
            async with cls._instance_lock:
                # 双重检查锁定模式
                if cls._instance is None:
                    print("🔧 创建 Telegram 客户端全局单例...")
                    cls._instance = cls()
                    await cls._instance._ensure_started()
        return cls._instance

    @classmethod
    async def close_instance(cls):
        """
        关闭并清理全局单例（应用退出时调用）
        """
        if cls._instance is not None:
            async with cls._instance_lock:
                if cls._instance is not None:
                    print("🔌 关闭 Telegram 客户端全局单例...")
                    await cls._instance.disconnect()
                    cls._instance = None

    async def _ensure_started(self):
        """确保客户端已启动"""
        if not self._started:
            # 添加重试机制处理 database locked 错误
            max_retries = 3
            retry_delay = 2

            for attempt in range(max_retries):
                try:
                    self.client = TelegramClient(self.session_name, self.api_id, self.api_hash, proxy=self.proxy)
                    await self.client.start()
                    self._started = True
                    break
                except Exception as e:
                    if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                        print(f"⚠️  Session 数据库锁定，等待 {retry_delay} 秒后重试 ({attempt + 1}/{max_retries})...")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # 指数退避
                    else:
                        raise

    async def sendToTgBotForQuark1(self, title, description, link, tags, file_path):
        """
        向 Quark 机器人发送文件投稿（单线程模式，全局互斥）

        Args:
            title: 标题
            description: 描述
            link: 分享链接
            tags: 标签
            file_path: 文件路径

        Returns:
            bool: 投稿是否成功
        """
        # 检查是否有其他任务在等待
        if TgClient._waiting_count > 0:
            print(f"⏳ 当前有 {TgClient._waiting_count} 个投稿任务在排队...")

        # 增加等待计数
        TgClient._waiting_count += 1
        start_time = datetime.now()

        try:
            # 使用类级别的锁，确保同一时间只有一个投稿操作
            print(f"🔒 [{title}] 等待获取投稿锁...")

            async with TgClient._submission_lock:
                # 减少等待计数（已获得锁）
                TgClient._waiting_count -= 1

                wait_time = (datetime.now() - start_time).total_seconds()
                if wait_time > 1:
                    print(f"✅ [{title}] 获取锁成功，等待了 {wait_time:.1f} 秒")
                else:
                    print(f"✅ [{title}] 获取锁成功")

                print(f"📤 开始投稿: {title}")
                print(f"📁 文件路径: {file_path}")

                caption_template = """
名称：{name}

描述：{desc}

链接：{link}

📁 大小：{size}
🏷 标签：{tags}
"""
                # 格式化投稿内容
                caption = caption_template.format(
                    name=title,
                    desc=description[:400] + "..." if len(description) > 400 else description,
                    link=link,
                    size="N",
                    tags='#' + tags.replace("、", " #")
                )

                try:
                    # 确保客户端已启动
                    await self._ensure_started()

                    # 1. 发送快速投稿命令
                    print(f"📝 [{title}] 步骤 1/5: 发送快速投稿命令")
                    await self.client.send_message("@QuarkRobot", "快速投稿")
                    await asyncio.sleep(random.uniform(3, 5))

                    # 2. 发送标题
                    print(f"📝 [{title}] 步骤 2/5: 发送标题")
                    await self.client.send_message("@QuarkRobot", title)
                    await asyncio.sleep(random.uniform(3, 5))

                    # 3. 发送文件和描述
                    print(f"📝 [{title}] 步骤 3/5: 发送文件和描述")
                    await self.client.send_file("@QuarkRobot", file_path, caption=caption)
                    await asyncio.sleep(random.uniform(3, 5))

                    # 4. 发送结束命令
                    print(f"📝 [{title}] 步骤 4/5: 发送结束命令")
                    await self.client.send_message("@QuarkRobot", "结束发送")
                    await asyncio.sleep(random.uniform(3, 5))

                    # 5. 确认投稿
                    print(f"📝 [{title}] 步骤 5/5: 确认投稿")
                    await self.client.send_message("@QuarkRobot", "确认投稿")
                    await asyncio.sleep(random.uniform(3, 5))

                    # 获取机器人回复
                    msgs = await self.client.get_messages("@QuarkRobot", limit=3)
                    print(f"🤖 机器人最新回复: {msgs[0].text}")

                    # 判断是否成功
                    if '投稿成功' in msgs[0].text or '已通过审核' in msgs[0].text:
                        total_time = (datetime.now() - start_time).total_seconds()
                        print(f"✅ [{title}] 投稿成功！耗时 {total_time:.1f} 秒")
                        return True
                    else:
                        print(f"❌ [{title}] 投稿失败: {msgs[0].text}")
                        return False

                except Exception as e:
                    print(f"❌ [{title}] 发送过程中出错: {e}")
                    return False

        except asyncio.CancelledError:
            # 处理任务被取消的情况
            TgClient._waiting_count = max(0, TgClient._waiting_count - 1)
            print(f"⚠️  [{title}] 投稿任务被取消")
            raise
        except Exception as e:
            # 处理其他异常
            TgClient._waiting_count = max(0, TgClient._waiting_count - 1)
            print(f"❌ [{title}] 投稿异常: {e}")
            return False

    async def disconnect(self):
        """断开客户端连接"""
        if self.client and self._started:
            await self.client.disconnect()
            self._started = False

    async def __aenter__(self):
        """
        异步上下文管理器入口
        注意：使用单例模式后，不推荐使用 async with，
        应该使用 await TgClient.get_instance() 获取实例
        """
        print("⚠️  警告: 使用单例模式时不推荐使用 async with，建议使用 TgClient.get_instance()")
        await self._ensure_started()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        异步上下文管理器退出
        注意：单例模式下不应该在这里关闭连接
        """
        # 单例模式下不关闭连接，保持连接复用
        pass
