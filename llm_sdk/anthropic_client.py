"""
Anthropic Claude 平台适配器
"""

import requests
from typing import List, Optional
from .base import BaseLLMClient, Message, ChatCompletionResponse


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude客户端"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.anthropic.com/v1",
        **kwargs
    ):
        """
        初始化Anthropic客户端

        Args:
            api_key: Anthropic API密钥
            base_url: API基础URL
            **kwargs: 其他参数
        """
        super().__init__(api_key, base_url, **kwargs)
        self.endpoint = f"{self.base_url}/messages"
        self.api_version = kwargs.get("api_version", "2023-06-01")

    def chat_completion(
        self,
        messages: List[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 1024,
        stream: bool = False,
        **kwargs
    ) -> ChatCompletionResponse:
        """
        执行对话补全

        Args:
            messages: 消息列表
            model: 模型ID（如claude-3-opus-20240229, claude-3-sonnet-20240229等）
            temperature: 温度参数
            max_tokens: 最大生成token数（Claude必需参数）
            stream: 是否流式输出
            **kwargs: 其他参数（top_p, top_k等）

        Returns:
            ChatCompletionResponse对象
        """
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": self.api_version
        }

        # Claude API使用不同的消息格式
        # system消息需要单独提取
        system_message = None
        formatted_messages = []

        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                formatted_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

        # 构建请求体
        payload = {
            "model": model,
            "messages": formatted_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs
        }

        if system_message:
            payload["system"] = system_message

        if stream:
            payload["stream"] = True

        # 发送请求
        response = requests.post(
            self.endpoint,
            headers=headers,
            json=payload,
            timeout=60
        )

        response.raise_for_status()
        result = response.json()

        # 解析响应
        content = result["content"][0]["text"]
        usage = result.get("usage", {})

        return ChatCompletionResponse(
            content=content,
            model=result.get("model", model),
            usage={
                "prompt_tokens": usage.get("input_tokens", 0),
                "completion_tokens": usage.get("output_tokens", 0),
                "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
            },
            raw_response=result
        )

    def stream_chat_completion(
        self,
        messages: List[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 1024,
        **kwargs
    ):
        """
        流式对话补全

        Args:
            messages: 消息列表
            model: 模型ID
            temperature: 温度参数
            max_tokens: 最大生成token数
            **kwargs: 其他参数

        Yields:
            str: 生成的文本片段
        """
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": self.api_version
        }

        system_message = None
        formatted_messages = []

        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                formatted_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

        payload = {
            "model": model,
            "messages": formatted_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
            **kwargs
        }

        if system_message:
            payload["system"] = system_message

        response = requests.post(
            self.endpoint,
            headers=headers,
            json=payload,
            stream=True,
            timeout=60
        )

        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data_str = line_str[6:]
                    try:
                        import json
                        data = json.loads(data_str)
                        if data.get('type') == 'content_block_delta':
                            delta = data.get('delta', {})
                            if delta.get('type') == 'text_delta':
                                yield delta.get('text', '')
                    except json.JSONDecodeError:
                        continue
