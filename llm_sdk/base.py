"""
基础接口定义
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class Message:
    """消息对象"""
    role: str  # system, user, assistant
    content: str


@dataclass
class ChatCompletionResponse:
    """统一的响应格式"""
    content: str
    model: str
    usage: Dict[str, int]
    raw_response: Any = None


class BaseLLMClient(ABC):
    """大模型客户端基类"""

    def __init__(self, api_key: str, base_url: Optional[str] = None, **kwargs):
        """
        初始化客户端

        Args:
            api_key: API密钥
            base_url: API基础URL（可选）
            **kwargs: 其他平台特定参数
        """
        self.api_key = api_key
        self.base_url = base_url
        self.extra_params = kwargs

    @abstractmethod
    def chat_completion(
        self,
        messages: List[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> ChatCompletionResponse:
        """
        执行对话补全

        Args:
            messages: 消息列表
            model: 模型ID
            temperature: 温度参数
            max_tokens: 最大生成token数
            stream: 是否流式输出
            **kwargs: 其他参数

        Returns:
            ChatCompletionResponse对象
        """
        pass

    def simple_chat(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: str = None,
        **kwargs
    ) -> str:
        """
        简化的对话接口

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词（可选）
            model: 模型ID
            **kwargs: 其他参数

        Returns:
            模型回复内容
        """
        messages = []
        if system_prompt:
            messages.append(Message(role="system", content=system_prompt))
        messages.append(Message(role="user", content=prompt))

        response = self.chat_completion(messages=messages, model=model, **kwargs)
        return response.content
