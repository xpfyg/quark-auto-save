# LLM SDK - 统一的大模型调用接口

一个简单易用的Python SDK，提供统一的接口来调用多个大模型平台的API。

## 特性

- 🚀 **统一接口**: 一套API适配多个平台
- 🔌 **多平台支持**: ARK(豆包)、OpenAI、Anthropic Claude、通义千问、DeepSeek等
- 💡 **简单易用**: 简洁的API设计，快速上手
- 🌊 **流式输出**: 支持流式响应
- 🛠 **高度可配置**: 支持自定义URL、参数等

## 支持的平台

| 平台 | 标识符 | 说明 |
|------|--------|------|
| ARK (豆包) | `ark` | 字节跳动火山引擎ARK平台 |
| OpenAI | `openai` | OpenAI官方API |
| Anthropic | `anthropic` | Anthropic Claude |
| 通义千问 | `qwen` | 阿里云通义千问 |
| 文心一言 | `ernie` | 百度文心一言 |
| 智谱AI | `zhipu` | 智谱AI GLM系列 |
| DeepSeek | `deepseek` | DeepSeek |

## 安装

### 依赖

```bash
pip install requests
```

### 使用

将 `llm_sdk` 目录复制到你的项目中即可。

## 快速开始

### 1. 基本使用

```python
from llm_sdk import create_client, Message

# 创建客户端
client = create_client(
    platform="ark",  # 或 "openai", "anthropic" 等
    api_key="your-api-key"
)

# 简单对话
response = client.simple_chat(
    prompt="你好！请介绍一下自己。",
    system_prompt="你是一个友好的AI助手。",
    model="your-model-id"
)
print(response)
```

### 2. 完整接口

```python
from llm_sdk import create_client, Message

client = create_client(platform="openai", api_key="sk-...")

# 构建消息
messages = [
    Message(role="system", content="你是一个Python专家。"),
    Message(role="user", content="写一个快速排序算法")
]

# 调用API
response = client.chat_completion(
    messages=messages,
    model="gpt-3.5-turbo",
    temperature=0.7,
    max_tokens=1000
)

print(f"回复: {response.content}")
print(f"Token使用: {response.usage}")
```

### 3. 流式输出

```python
client = create_client(platform="qwen", api_key="sk-...")

messages = [Message(role="user", content="介绍一下人工智能")]

# 流式输出
for chunk in client.stream_chat_completion(
    messages=messages,
    model="qwen-turbo"
):
    print(chunk, end="", flush=True)
```

## 平台配置示例

### ARK (豆包)

```python
client = create_client(
    platform="ark",
    api_key="your-ark-api-key"
)

response = client.simple_chat(
    prompt="你好",
    model="your-endpoint-id"  # ARK的模型ID
)
```

获取API Key和Endpoint ID:
1. 访问 [火山引擎控制台](https://console.volcengine.com/ark)
2. 创建推理接入点，获取Endpoint ID
3. 在API管理页面获取API Key

### OpenAI

```python
client = create_client(
    platform="openai",
    api_key="sk-..."
)

response = client.simple_chat(
    prompt="Hello!",
    model="gpt-3.5-turbo"  # 或 gpt-4
)
```

### 通义千问

```python
client = create_client(
    platform="qwen",
    api_key="sk-..."  # 从阿里云获取
)

response = client.simple_chat(
    prompt="你好",
    model="qwen-turbo"  # 或 qwen-plus, qwen-max
)
```

### DeepSeek

```python
client = create_client(
    platform="deepseek",
    api_key="sk-..."
)

response = client.simple_chat(
    prompt="写一段代码",
    model="deepseek-chat"
)
```

### Anthropic Claude

```python
client = create_client(
    platform="anthropic",
    api_key="sk-ant-..."
)

response = client.chat_completion(
    messages=[Message(role="user", content="Hello")],
    model="claude-3-sonnet-20240229",
    max_tokens=1024  # Claude必需参数
)
```

## 自定义配置

### 使用自定义URL

如果使用代理或中转服务:

```python
client = create_client(
    platform="openai",
    api_key="sk-...",
    base_url="https://your-proxy.com/v1"  # 自定义URL
)
```

### 传递额外参数

```python
response = client.chat_completion(
    messages=messages,
    model="gpt-3.5-turbo",
    temperature=0.8,
    top_p=0.9,
    presence_penalty=0.6,
    frequency_penalty=0.5
)
```

## API参考

### create_client()

创建大模型客户端。

```python
create_client(
    platform: str,        # 平台标识符
    api_key: str,         # API密钥
    base_url: str = None, # 自定义URL（可选）
    **kwargs              # 其他参数
) -> BaseLLMClient
```

### simple_chat()

简化的对话接口。

```python
client.simple_chat(
    prompt: str,                    # 用户提示词
    system_prompt: str = None,      # 系统提示词
    model: str = None,              # 模型ID
    **kwargs                        # 其他参数
) -> str
```

### chat_completion()

完整的对话补全接口。

```python
client.chat_completion(
    messages: List[Message],        # 消息列表
    model: str,                     # 模型ID
    temperature: float = 0.7,       # 温度
    max_tokens: int = None,         # 最大token数
    stream: bool = False,           # 是否流式
    **kwargs                        # 其他参数
) -> ChatCompletionResponse
```

### stream_chat_completion()

流式对话补全。

```python
client.stream_chat_completion(
    messages: List[Message],
    model: str,
    temperature: float = 0.7,
    max_tokens: int = None,
    **kwargs
) -> Iterator[str]
```

## 完整示例

查看 `llm_sdk_examples.py` 文件获取更多示例。

运行示例:

```bash
# 设置环境变量
export ARK_API_KEY='your-ark-key'
export ARK_MODEL_ID='your-model-id'

# 运行示例
python llm_sdk_examples.py
```

## 常见问题

### 1. 如何获取API Key?

- **ARK**: [火山引擎控制台](https://console.volcengine.com/ark)
- **OpenAI**: [OpenAI API Keys](https://platform.openai.com/api-keys)
- **通义千问**: [阿里云控制台](https://dashscope.console.aliyun.com/)
- **DeepSeek**: [DeepSeek平台](https://platform.deepseek.com/)
- **Anthropic**: [Anthropic Console](https://console.anthropic.com/)

### 2. 如何处理错误?

```python
try:
    response = client.simple_chat(prompt="你好", model="gpt-3.5-turbo")
    print(response)
except requests.exceptions.HTTPError as e:
    print(f"HTTP错误: {e}")
except Exception as e:
    print(f"错误: {e}")
```

### 3. 如何使用代理?

```python
# 方法1: 通过自定义URL
client = create_client(
    platform="openai",
    api_key="sk-...",
    base_url="https://your-proxy.com/v1"
)

# 方法2: 使用requests的代理
import os
os.environ['HTTP_PROXY'] = 'http://proxy.example.com:8080'
os.environ['HTTPS_PROXY'] = 'http://proxy.example.com:8080'
```

### 4. 支持异步吗?

当前版本是同步实现。如需异步支持，可以使用 `asyncio` + `aiohttp` 改造客户端。

## 开发

### 项目结构

```
llm_sdk/
├── __init__.py           # 包入口
├── base.py              # 基础接口定义
├── factory.py           # 客户端工厂
├── ark_client.py        # ARK客户端
├── openai_client.py     # OpenAI客户端
└── anthropic_client.py  # Anthropic客户端

llm_sdk_examples.py      # 使用示例
```

### 添加新平台

1. 在 `llm_sdk/` 下创建新的客户端文件
2. 继承 `BaseLLMClient` 并实现接口
3. 在 `factory.py` 中注册新平台

## License

MIT License

## 贡献

欢迎提交Issue和Pull Request！
