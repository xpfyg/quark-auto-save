# Telegram "database is locked" 错误修复说明

## 问题描述

在使用"一键投稿"功能时，出现以下错误：

```
发送到 Telegram 机器人失败: database is locked
```

## 根本原因

Telethon 库使用 SQLite 数据库存储 session 信息。当多个进程或线程同时访问同一个 session 文件时，会触发 SQLite 的锁定机制，导致错误。

## 已实施的修复

### 修复 1: 使用异步上下文管理器（resource_manager.py:479-482）

**修改前：**
```python
# 在 ResourceManager.__init__ 中创建单例
self.tg_client = TgClient()

# 在 shareToTgBot 方法中直接使用
rst = await self.tg_client.sendToTgBotForQuark1(...)
```

**修改后：**
```python
# 每次调用时动态创建，使用完自动销毁
async with TgClient() as tg_client:
    rst = await tg_client.sendToTgBotForQuark1(...)
```

**优点：**
- 确保每次使用后连接被正确关闭
- 避免多个实例同时访问 session 文件
- 自动管理资源生命周期

### 修复 2: 添加重试机制（telegram_sdk/tg.py:46-65）

在 `_ensure_started()` 方法中添加了重试逻辑：

```python
async def _ensure_started(self):
    """确保客户端已启动"""
    if not self._started:
        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                self.client = TelegramClient(...)
                await self.client.start()
                self._started = True
                break
            except Exception as e:
                if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                    print(f"⚠️  Session 数据库锁定，等待 {retry_delay} 秒后重试...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避
                else:
                    raise
```

**特性：**
- 最多重试 3 次
- 指数退避策略（2秒 → 4秒 → 8秒）
- 自动检测并处理 "database is locked" 错误

## 其他可能的解决方案

### 方案 1: 检查并发进程

如果问题仍然存在，检查是否有多个程序实例同时运行：

```bash
# 查找正在运行的进程
ps aux | grep "python.*quark"

# 或者检查 session 文件是否被占用
lsof ./sessions/quark_bot.session
```

### 方案 2: 清理旧的 session 文件

如果 session 文件损坏，可以删除后重新认证：

```bash
# 备份并删除 session 文件
cd sessions
mv quark_bot.session quark_bot.session.bak
mv quark_bot.session-journal quark_bot.session-journal.bak
```

重新运行程序时，会提示重新登录 Telegram。

### 方案 3: 设置独立的 session 目录

在 `.env` 文件中配置独立的 session 目录：

```bash
# 使用绝对路径，确保不同进程不会冲突
TG_SESSION_DIR=/path/to/unique/session/dir
```

### 方案 4: 使用不同的 session 名称

如果需要同时运行多个实例，为每个实例配置不同的 session：

```bash
# 实例 1
TG_SESSION_NAME=quark_bot_1

# 实例 2
TG_SESSION_NAME=quark_bot_2
```

## 验证修复

重新运行"一键投稿"功能，应该看到以下输出：

```
✅ 初始化 Telegram 客户端: quark_bot
准备发送到 Telegram 机器人: 目中无人, 文件路径: ./resource/tmdb/2024/目中无人2#1235623.jpg
[INFO] Connecting to 91.108.56.111:443/TcpFull...
[DEBUG] Connection success!
🤖 机器人最新回复：投稿成功
✅ 资源已分享到Telegram机器人: 目中无人
```

## 技术细节

### TgClient 上下文管理器实现

```python
async def __aenter__(self):
    """异步上下文管理器入口"""
    await self._ensure_started()
    return self

async def __aexit__(self, exc_type, exc_val, exc_tb):
    """异步上下文管理器退出"""
    await self.disconnect()
```

这确保了：
1. 进入 `async with` 时自动启动客户端
2. 退出时自动断开连接并释放资源
3. 即使发生异常也能正确清理

## 注意事项

1. **不要同时运行多个使用相同 session 的程序实例**
2. **确保 session 目录有正确的读写权限**
3. **如果使用 Docker，确保 session 目录已正确挂载**
4. **代理设置不正确可能导致连接失败，检查 TG_PROXY_HOST 和 TG_PROXY_PORT**

## 环境变量配置参考

```bash
# Telegram 配置
TG_API_ID=your_api_id
TG_API_HASH=your_api_hash
TG_SESSION_NAME=quark_bot
TG_SESSION_DIR=./sessions

# 可选：代理配置
TG_PROXY_HOST=127.0.0.1
TG_PROXY_PORT=7890
```

## 相关文件

- `resource_manager.py:409-495` - shareToTgBot 方法
- `telegram_sdk/tg.py` - TgClient 核心实现
- `.env.example` - 环境变量配置示例
- `sessions/` - Session 文件存储目录

## 更新日志

- **2025-11-05**: 修复 "database is locked" 错误
  - 实施异步上下文管理器
  - 添加重试机制
  - 更新文档
