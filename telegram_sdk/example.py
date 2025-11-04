"""
Telegram SDK 使用示例
"""
import asyncio
from tg import TgClient


async def example_usage():
    """示例：使用上下文管理器（推荐）"""
    async with TgClient() as tg_client:
        result = await tg_client.sendToTgBotForQuark1(
            title="测试标题",
            description="这是一个测试描述",
            file_path="/path/to/your/file.mp4"
        )
        print(f"发送结果: {result}")


async def example_manual():
    """示例：手动管理连接"""
    tg_client = TgClient()
    try:
        result = await tg_client.sendToTgBotForQuark1(
            title="测试标题",
            description="这是一个测试描述",
            file_path="/path/to/your/file.mp4"
        )
        print(f"发送结果: {result}")
    finally:
        await tg_client.disconnect()


if __name__ == "__main__":
    # 运行示例（推荐使用上下文管理器方式）
    asyncio.run(example_usage())

    # 或者使用手动管理方式
    # asyncio.run(example_manual())
