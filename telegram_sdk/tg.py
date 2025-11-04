"""
Telegram 客户端核心类
"""
import asyncio
import os
import random

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
    def __init__(self, api_id=TG_API_ID, api_hash=TG_API_HASH, session_name=TG_SESSION_NAME, proxy=my_proxy):
        print(f"✅ 初始化 Telegram 客户端: {session_name}")
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

    async def _ensure_started(self):
        """确保客户端已启动"""
        if not self._started:
            self.client = TelegramClient(self.session_name, self.api_id, self.api_hash, proxy=self.proxy)
            await self.client.start()
            self._started = True

    async def sendToTgBotForQuark1(self, title, description, link, tags,file_path):
        """
        向 Quark 机器人发送文件投稿

        Args:
            title: 标题
            description: 描述
            file_path: 文件路径
        """
        print(f"准备发送到 Telegram 机器人: {title}, 文件路径: {file_path}")
        caption_template = """
名称：{name}

描述：{desc}

链接：{link}

📁 大小：{size}
🏷 标签：{tags}
"""
        # 使用示例：
        caption = caption_template.format(
            name=title,
            desc=description[:400] + "..." if len(description) > 400 else description,
            link=link,
            size="N",
            tags='#' +tags.replace("、", " #")
        )
        try:
            # 确保客户端已启动
            await self._ensure_started()

            # 1. 发送快速投稿命令
            await self.client.send_message("@QuarkRobot", "快速投稿")
            await asyncio.sleep(random.uniform(3, 5))

            # 2. 发送标题
            await self.client.send_message("@QuarkRobot", title)
            await asyncio.sleep(random.uniform(3, 5))

            # 3. 发送文件和描述
            await self.client.send_file("@QuarkRobot", file_path, caption=caption)
            await asyncio.sleep(random.uniform(3, 5))

            # 4. 发送结束命令
            await self.client.send_message("@QuarkRobot", "结束发送")
            await asyncio.sleep(random.uniform(3, 5))

            # 5. 确认投稿
            await self.client.send_message("@QuarkRobot", "确认投稿")
            await asyncio.sleep(random.uniform(3, 5))
            msgs = await self.client.get_messages("@QuarkRobot", limit=3)
            print("🤖 机器人最新回复：", msgs[0].text)
            if '投稿成功' in msgs[0].text or '已通过审核' in msgs[0].text:
                print("投稿成功")
                return True
            print(f"投稿失败: {msgs[0].text}")
            return False

        except Exception as e:
            print(f"发送到 Telegram 机器人失败: {e}")
            return False

    async def disconnect(self):
        """断开客户端连接"""
        if self.client and self._started:
            await self.client.disconnect()
            self._started = False

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self._ensure_started()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.disconnect()
