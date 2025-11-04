"""
LLM SDK - 统一的大模型调用接口
支持多个平台：ARK(豆包)、OpenAI、Anthropic Claude等
"""

from .factory import create_client
from .base import BaseLLMClient, Message, ChatCompletionResponse

__version__ = "1.0.0"
__all__ = ["create_client", "BaseLLMClient", "Message", "ChatCompletionResponse"]
