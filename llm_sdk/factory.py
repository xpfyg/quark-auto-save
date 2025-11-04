"""
客户端工厂
统一创建不同平台的大模型客户端
"""

from typing import Optional
from .base import BaseLLMClient
from .ark_client import ARKClient
from .openai_client import OpenAIClient
from .anthropic_client import AnthropicClient


class PlatformType:
    """支持的平台类型"""
    ARK = "ark"  # 豆包（字节跳动）
    OPENAI = "openai"  # OpenAI官方
    ANTHROPIC = "anthropic"  # Anthropic Claude
    QWEN = "qwen"  # 通义千问（使用OpenAI格式）
    ERNIE = "ernie"  # 文心一言（使用OpenAI格式）
    ZHIPU = "zhipu"  # 智谱AI（使用OpenAI格式）
    DEEPSEEK = "deepseek"  # DeepSeek（使用OpenAI格式）


# 预设的平台配置
PLATFORM_CONFIGS = {
    PlatformType.OPENAI: {
        "base_url": "https://api.openai.com/v1",
        "client_class": OpenAIClient
    },
    PlatformType.ARK: {
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "client_class": ARKClient
    },
    PlatformType.ANTHROPIC: {
        "base_url": "https://api.anthropic.com/v1",
        "client_class": AnthropicClient
    },
    PlatformType.QWEN: {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "client_class": OpenAIClient
    },
    PlatformType.ERNIE: {
        "base_url": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop",
        "client_class": OpenAIClient
    },
    PlatformType.ZHIPU: {
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "client_class": OpenAIClient
    },
    PlatformType.DEEPSEEK: {
        "base_url": "https://api.deepseek.com/v1",
        "client_class": OpenAIClient
    }
}


def create_client(
    platform: str,
    api_key: str,
    base_url: Optional[str] = None,
    **kwargs
) -> BaseLLMClient:
    """
    创建大模型客户端

    Args:
        platform: 平台类型（ark, openai, anthropic, qwen, ernie, zhipu, deepseek）
        api_key: API密钥
        base_url: 自定义API基础URL（可选，会覆盖默认配置）
        **kwargs: 其他平台特定参数

    Returns:
        BaseLLMClient实例

    Examples:
        >>> # 创建ARK客户端
        >>> client = create_client("ark", api_key="your-ark-key")

        >>> # 创建OpenAI客户端
        >>> client = create_client("openai", api_key="sk-...")

        >>> # 创建通义千问客户端
        >>> client = create_client("qwen", api_key="sk-...")

        >>> # 使用自定义URL
        >>> client = create_client("openai", api_key="sk-...", base_url="https://your-proxy.com/v1")
    """
    platform = platform.lower()

    if platform not in PLATFORM_CONFIGS:
        raise ValueError(
            f"不支持的平台: {platform}. "
            f"支持的平台: {', '.join(PLATFORM_CONFIGS.keys())}"
        )

    config = PLATFORM_CONFIGS[platform]
    client_class = config["client_class"]

    # 使用自定义base_url或默认配置
    final_base_url = base_url or config["base_url"]

    return client_class(
        api_key=api_key,
        base_url=final_base_url,
        **kwargs
    )


def list_platforms():
    """
    列出所有支持的平台

    Returns:
        dict: 平台信息字典
    """
    return {
        platform: {
            "base_url": config["base_url"],
            "client_type": config["client_class"].__name__
        }
        for platform, config in PLATFORM_CONFIGS.items()
    }
