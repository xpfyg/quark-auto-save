"""
ARK (豆包) 快速开始示例
直接运行此脚本测试ARK API调用
"""

import os
from llm_sdk import create_client, Message


def main():
    """主函数"""
    # 从环境变量获取配置
    api_key = os.getenv("ARK_API_KEY")
    model_id = os.getenv("ARK_MODEL_ID")

    if not api_key or not model_id:
        print("错误: 请先设置环境变量")
        print("\nexport ARK_API_KEY='your-ark-api-key'")
        print("export ARK_MODEL_ID='your-endpoint-id'")
        print("\n获取API Key和Endpoint ID:")
        print("1. 访问 https://console.volcengine.com/ark")
        print("2. 创建推理接入点，获取Endpoint ID")
        print("3. 在API管理页面获取API Key")
        return

    print("=" * 60)
    print("ARK (豆包) 快速开始")
    print("=" * 60)

    # 创建客户端
    client = create_client(
        platform="ark",
        api_key=api_key
    )

    # 示例1: 简单对话
    print("\n【示例1: 简单对话】")
    print("-" * 60)
    try:
        response = client.simple_chat(
            prompt="你好！请用一句话介绍自己。",
            system_prompt="你是豆包AI助手。",
            model=model_id
        )
        print(f"AI回复: {response}")
    except Exception as e:
        print(f"错误: {e}")

    # 示例2: 多轮对话
    print("\n【示例2: 多轮对话】")
    print("-" * 60)
    try:
        messages = [
            Message(role="system", content="你是一个Python编程专家。"),
            Message(role="user", content="什么是列表推导式？"),
        ]

        response = client.chat_completion(
            messages=messages,
            model=model_id,
            temperature=0.7
        )

        print(f"AI回复: {response.content}")
        print(f"\nToken使用统计:")
        print(f"  - 输入: {response.usage['prompt_tokens']}")
        print(f"  - 输出: {response.usage['completion_tokens']}")
        print(f"  - 总计: {response.usage['total_tokens']}")
    except Exception as e:
        print(f"错误: {e}")

    # 示例3: 流式输出
    print("\n【示例3: 流式输出】")
    print("-" * 60)
    try:
        messages = [
            Message(role="user", content="写一首关于AI的五言绝句")
        ]

        print("AI回复: ", end="", flush=True)
        for chunk in client.stream_chat_completion(
            messages=messages,
            model=model_id,
            temperature=0.9
        ):
            print(chunk, end="", flush=True)
        print()
    except Exception as e:
        print(f"\n错误: {e}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
