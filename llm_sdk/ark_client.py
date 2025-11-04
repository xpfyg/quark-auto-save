"""
ARK (豆包) 平台适配器
字节跳动火山引擎ARK平台
"""

import requests
from typing import List, Optional
from .base import BaseLLMClient, Message, ChatCompletionResponse


class ARKClient(BaseLLMClient):
    """ARK平台客户端"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://ark.cn-beijing.volces.com/api/v3",
        **kwargs
    ):
        """
        初始化ARK客户端

        Args:
            api_key: ARK API密钥
            base_url: API基础URL
            **kwargs: 其他参数
        """
        super().__init__(api_key, base_url, **kwargs)
        self.endpoint = f"{self.base_url}/chat/completions"

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
            model: 模型ID（ARK endpoint ID）
            temperature: 温度参数
            max_tokens: 最大生成token数
            stream: 是否流式输出
            **kwargs: 其他参数

        Returns:
            ChatCompletionResponse对象
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        # 转换消息格式
        formatted_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        # 构建请求体
        payload = {
            "model": model,
            "messages": formatted_messages,
            "temperature": temperature,
            **kwargs
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

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
        content = result["choices"][0]["message"]["content"]
        usage = result.get("usage", {})

        return ChatCompletionResponse(
            content=content,
            model=result.get("model", model),
            usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0)
            },
            raw_response=result
        )

    def stream_chat_completion(
        self,
        messages: List[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
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
            "Authorization": f"Bearer {self.api_key}"
        }

        formatted_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        payload = {
            "model": model,
            "messages": formatted_messages,
            "temperature": temperature,
            "stream": True,
            **kwargs
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

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
                    if data_str == '[DONE]':
                        break
                    try:
                        import json
                        data = json.loads(data_str)
                        if 'choices' in data and len(data['choices']) > 0:
                            delta = data['choices'][0].get('delta', {})
                            if 'content' in delta:
                                yield delta['content']
                    except json.JSONDecodeError:
                        continue
