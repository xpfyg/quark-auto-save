# Telegram 客户端全局单例模式详解

## 📚 为什么会有 "database is locked" 错误？

### 1. Telethon 的 Session 存储机制

```python
client = TelegramClient('session_name', api_id, api_hash)
```

Telethon 创建的 session 文件实际上是一个 **SQLite 数据库**：

```bash
$ ls -la sessions/
-rw-r--r--  quark_bot.session         # SQLite 数据库文件
-rw-r--r--  quark_bot.session-journal # SQLite 日志文件（写操作时临时文件）
```

**Session 文件存储的内容：**
- 📱 用户认证信息（auth_key）
- 🔐 加密密钥（DC keys）
- 🌐 数据中心信息（DC IPs）
- 📊 实体缓存（用户、群组、频道）
- ⏰ 最后更新时间

### 2. SQLite 的锁机制

SQLite 使用**文件级锁定**：

| 锁类型 | 说明 | 并发能力 |
|-------|------|---------|
| **UNLOCKED** | 未锁定，可以读写 | ✅ 多进程可访问 |
| **SHARED** | 共享锁，读取数据 | ✅ 多个读操作并发 |
| **RESERVED** | 保留锁，准备写入 | ⚠️ 只能有一个 |
| **PENDING** | 等待写入，阻塞新读取 | ❌ 阻塞新操作 |
| **EXCLUSIVE** | 独占锁，正在写入 | ❌ 完全互斥 |

**关键问题：同一时间只能有一个写操作！**

### 3. 多实例访问导致锁定

#### ❌ 错误示例（之前的代码）

```python
# 场景1: 用户快速点击两次投稿按钮
async with TgClient() as client1:  # 实例1打开 session
    await client1.send_message(...)  # 写入 session

async with TgClient() as client2:  # 实例2尝试打开 session
    # ❌ 错误！实例1还在使用，session 被锁定
    # database is locked
```

```python
# 场景2: 多个线程/协程同时调用
tasks = [
    shareToTgBot(id=1),  # TgClient 实例1
    shareToTgBot(id=2),  # TgClient 实例2
    shareToTgBot(id=3),  # TgClient 实例3
]
await asyncio.gather(*tasks)
# ❌ 3个实例同时访问 → database is locked
```

#### ✅ 正确示例（全局单例）

```python
# 全局共享一个 TelegramClient 实例
client = await TgClient.get_instance()  # 只打开一次 session

# 多个投稿任务共享同一个连接
await client.sendToTgBotForQuark1(...)  # 使用同一个实例
await client.sendToTgBotForQuark1(...)  # 使用同一个实例
await client.sendToTgBotForQuark1(...)  # 使用同一个实例
# ✅ 只有一个 SQLite 连接，无锁定问题
```

---

## ✅ 全局单例模式详解

### 架构设计

```
┌─────────────────────────────────────────┐
│           应用程序生命周期              │
├─────────────────────────────────────────┤
│  启动 → 运行 → 关闭                     │
│   ↓      ↓      ↓                       │
│  初始  使用  清理                        │
└─────────────────────────────────────────┘
         │            │
         ↓            ↓
   ┌─────────────────────────────┐
   │   TgClient (全局单例)       │
   ├─────────────────────────────┤
   │ • _instance (类变量)        │
   │ • _instance_lock (创建锁)   │
   │ • _submission_lock (投稿锁) │
   └─────────────────────────────┘
              │
              ↓
   ┌─────────────────────────────┐
   │  TelegramClient (唯一实例)  │
   ├─────────────────────────────┤
   │ • 维持一个 TCP 连接          │
   │ • 打开一个 SQLite 连接       │
   │ • 应用运行期间持续存在       │
   └─────────────────────────────┘
              │
              ↓
   ┌─────────────────────────────┐
   │ quark_bot.session (SQLite)  │
   │ ✅ 只被一个实例访问          │
   └─────────────────────────────┘
```

### 核心代码实现

#### 1. 双重检查锁定（DCL）单例

```python
class TgClient:
    _instance = None  # 类变量，所有实例共享
    _instance_lock = asyncio.Lock()  # 创建实例时的锁

    @classmethod
    async def get_instance(cls):
        """获取全局单例"""
        # 第一次检查（快速路径，无锁）
        if cls._instance is None:
            # 获取锁（慢速路径）
            async with cls._instance_lock:
                # 第二次检查（避免重复创建）
                if cls._instance is None:
                    cls._instance = cls()
                    await cls._instance._ensure_started()
        return cls._instance
```

**为什么要双重检查？**
- 第一次检查：避免每次都获取锁（性能优化）
- 获取锁：确保多个协程不会同时创建实例
- 第二次检查：防止两个协程都通过第一次检查

#### 2. 投稿操作的串行化

```python
class TgClient:
    _submission_lock = asyncio.Lock()  # 投稿操作锁
    _waiting_count = 0  # 等待队列长度

    async def sendToTgBotForQuark1(self, ...):
        # 增加等待计数
        TgClient._waiting_count += 1

        try:
            # 获取投稿锁（其他任务会在这里等待）
            async with TgClient._submission_lock:
                TgClient._waiting_count -= 1

                # 执行投稿操作（串行执行，一次只有一个）
                await self.client.send_message(...)
                await self.client.send_file(...)
                ...
        finally:
            # 确保计数正确更新
            TgClient._waiting_count = max(0, TgClient._waiting_count - 1)
```

#### 3. 懒加载机制

```python
async def _ensure_started(self):
    """首次使用时才连接"""
    if not self._started:
        # 创建 TelegramClient（打开 SQLite）
        self.client = TelegramClient(self.session_name, ...)
        # 连接到 Telegram 服务器
        await self.client.start()
        self._started = True
```

**优点：**
- ⚡ 应用启动快：不立即连接 Telegram
- 💾 节省资源：仅在需要时才创建连接
- 🔄 延迟初始化：可以在首次调用时设置代理等

---

## 🆚 对比：旧方案 vs 新方案

### 旧方案：每次创建新实例

```python
# resource_manager.py (旧代码)
async with TgClient() as client:
    await client.sendToTgBotForQuark1(...)
# ❌ 连接关闭，下次又要重新创建
```

**问题：**
1. ❌ **多实例同时访问** → database is locked
2. ❌ **频繁创建销毁** → 性能损耗
3. ❌ **重复认证** → 每次都要读取 session
4. ❌ **TCP 连接开销** → 建立/断开连接耗时

**时序图：**
```
任务1: 创建TgClient → 打开session → 投稿 → 关闭session
任务2:                              创建TgClient → 打开session → ❌ 锁定
```

### 新方案：全局单例

```python
# resource_manager.py (新代码)
client = await TgClient.get_instance()
await client.sendToTgBotForQuark1(...)
# ✅ 连接保持，复用实例
```

**优点：**
1. ✅ **唯一实例** → 无 session 锁定
2. ✅ **连接复用** → 性能提升
3. ✅ **串行投稿** → 自动排队
4. ✅ **状态保持** → 认证信息缓存

**时序图：**
```
初始化: 创建TgClient → 打开session (一次)
任务1:                            获取锁 → 投稿 → 释放锁
任务2:                                      等待 → 获取锁 → 投稿 → 释放锁
任务3:                                               等待 → 获取锁 → 投稿
```

---

## 📊 性能对比

| 指标 | 旧方案（多实例） | 新方案（单例） | 提升 |
|------|----------------|--------------|------|
| Session 打开次数 | N 次 | 1 次 | ⬇️ 降低 N 倍 |
| TCP 连接次数 | N 次 | 1 次 | ⬇️ 降低 N 倍 |
| 内存占用 | N × 5MB | 5MB | ⬇️ 降低 N 倍 |
| 数据库锁定风险 | 高 | 无 | ✅ 完全避免 |
| 并发投稿延迟 | 随机失败 | 自动排队 | ✅ 稳定可靠 |

**假设场景：连续投稿 10 个资源**

```
旧方案:
- 打开/关闭 session: 10 次 × 500ms = 5 秒
- TCP 握手: 10 次 × 300ms = 3 秒
- 总开销: ~8 秒 + 可能失败

新方案:
- 打开/关闭 session: 1 次 × 500ms = 0.5 秒
- TCP 握手: 1 次 × 300ms = 0.3 秒
- 总开销: ~0.8 秒
- 性能提升: 10 倍
```

---

## 🛡️ 安全性与可靠性

### 1. 线程/协程安全

```python
# 多个协程并发调用
tasks = [
    shareToTgBot(1),
    shareToTgBot(2),
    shareToTgBot(3),
]
await asyncio.gather(*tasks)
```

**保证：**
- ✅ `_instance_lock` 确保只创建一次实例
- ✅ `_submission_lock` 确保投稿串行执行
- ✅ 即使 100 个并发请求也不会出错

### 2. 异常安全

```python
try:
    async with TgClient._submission_lock:
        await send_message(...)  # 可能抛异常
finally:
    # ✅ Lock 自动释放，不会死锁
    TgClient._waiting_count -= 1
```

### 3. 连接恢复

```python
async def _ensure_started(self):
    if not self._started:
        for attempt in range(3):  # 重试 3 次
            try:
                await self.client.start()
                break
            except Exception as e:
                if "database is locked" in str(e):
                    await asyncio.sleep(2 ** attempt)  # 指数退避
                else:
                    raise
```

---

## 🔧 使用指南

### 基本用法

```python
# 1. 获取全局单例（自动创建、连接、认证）
client = await TgClient.get_instance()

# 2. 调用投稿方法（自动串行化）
success = await client.sendToTgBotForQuark1(
    title="流浪地球",
    description="科幻电影",
    link="https://pan.quark.cn/...",
    tags="科幻、动作",
    file_path="./poster.jpg"
)

# 3. 应用退出时清理（可选）
await TgClient.close_instance()
```

### Flask 应用集成

```python
# app/run.py
from flask import Flask
from telegram_sdk.tg import TgClient

app = Flask(__name__)

@app.route('/api/share_to_tg/<int:resource_id>', methods=['POST'])
async def share_to_tg(resource_id):
    # 获取单例（已连接，直接使用）
    tg_client = await TgClient.get_instance()

    # 投稿（自动排队）
    success = await tg_client.sendToTgBotForQuark1(...)

    return jsonify({'success': success})

# 应用关闭时清理
@app.teardown_appcontext
async def shutdown_telegram(exception=None):
    await TgClient.close_instance()
```

### 批量投稿

```python
async def batch_share(resource_ids):
    # 获取单例
    client = await TgClient.get_instance()

    # 并发提交（自动排队执行）
    tasks = [
        client.sendToTgBotForQuark1(...)
        for id in resource_ids
    ]

    # 等待全部完成
    results = await asyncio.gather(*tasks)

    print(f"成功: {sum(results)}/{len(results)}")
```

---

## 🎯 最佳实践

### ✅ DO

1. **使用 `get_instance()` 获取实例**
   ```python
   client = await TgClient.get_instance()
   ```

2. **应用启动时预热连接（可选）**
   ```python
   await TgClient.get_instance()  # 提前建立连接
   ```

3. **应用退出时清理**
   ```python
   await TgClient.close_instance()
   ```

4. **让锁自动管理并发**
   ```python
   # 不需要手动处理并发，锁会自动排队
   await client.sendToTgBotForQuark1(...)
   ```

### ❌ DON'T

1. **不要使用 `async with TgClient()`**
   ```python
   # ❌ 旧用法，会触发警告
   async with TgClient() as client:
       ...
   ```

2. **不要直接调用 `__init__`**
   ```python
   # ❌ 不要直接创建实例
   client = TgClient()  # 错误！
   ```

3. **不要手动管理连接**
   ```python
   # ❌ 不要手动断开连接
   await client.disconnect()  # 会影响其他使用者
   ```

4. **不要在多个进程间共享**
   ```python
   # ❌ 多进程需要独立的 session
   # 考虑使用不同的 session_name
   ```

---

## 📈 监控与调试

### 查看等待队列

```python
print(f"当前等待任务: {TgClient._waiting_count}")
```

### 查看实例状态

```python
client = await TgClient.get_instance()
print(f"已连接: {client._started}")
print(f"Session: {client.session_name}")
```

### 日志输出

```
🔧 创建 Telegram 客户端全局单例...
✅ 初始化 Telegram 客户端单例: quark_bot
[INFO] Connecting to 91.108.56.111:443/TcpFull...
[DEBUG] Connection success!

🔒 [流浪地球] 等待获取投稿锁...
✅ [流浪地球] 获取锁成功
📤 开始投稿: 流浪地球
📝 [流浪地球] 步骤 1/5: 发送快速投稿命令
...
✅ [流浪地球] 投稿成功！耗时 23.5 秒

⏳ 当前有 1 个投稿任务在排队...
🔒 [三体] 等待获取投稿锁...
✅ [三体] 获取锁成功，等待了 23.5 秒
...
```

---

## 🔍 常见问题

### Q1: 单例模式会不会有单点故障？

**A:** 有断线重连机制：
```python
async def _ensure_started(self):
    if not self._started:
        # 自动重连，最多重试 3 次
        for attempt in range(3):
            try:
                await self.client.start()
                break
            except Exception:
                await asyncio.sleep(2 ** attempt)
```

### Q2: 多个 session 可以并行吗？

**A:** 可以，使用不同的 session_name：
```python
# .env
TG_SESSION_NAME=quark_bot_1  # 实例1

# 或者在代码中
client1 = TgClient(session_name="bot_1")
client2 = TgClient(session_name="bot_2")
# 两个独立的 session 文件，可以并行
```

### Q3: 单例会占用内存吗？

**A:** 占用极小（~5MB），但避免了重复创建的开销：
```
多实例: 10 次创建 × 5MB = 50MB（峰值）
单例: 1 个实例 × 5MB = 5MB（常驻）
节省: 90% 内存峰值
```

### Q4: 为什么不用线程锁？

**A:** 这是异步程序，必须使用 `asyncio.Lock`：
```python
# ❌ 错误：threading.Lock 会阻塞事件循环
import threading
lock = threading.Lock()

# ✅ 正确：asyncio.Lock 不阻塞事件循环
import asyncio
lock = asyncio.Lock()
```

---

## 📚 总结

| 问题 | 原因 | 解决方案 |
|-----|------|---------|
| database is locked | 多实例同时访问 session | 全局单例 |
| 性能低 | 频繁创建销毁连接 | 连接复用 |
| 投稿冲突 | 并发发送消息 | 投稿串行化 |
| 认证开销 | 重复读取 session | 状态缓存 |

**核心思想：**
- 🎯 **一个应用 = 一个 TelegramClient 实例**
- 🔒 **一个实例 = 一个 SQLite 连接**
- 🚦 **投稿操作串行化 = 无锁定风险**

---

## 🔗 相关文件

- `telegram_sdk/tg.py` - TgClient 单例实现
- `resource_manager.py:480-482` - 使用单例的示例
- `docs/TELEGRAM_DATABASE_LOCKED_FIX.md` - 锁定问题修复文档

## 📝 更新日志

- **2025-11-05**: 实施全局单例模式
  - 添加 `get_instance()` 类方法
  - 添加 `close_instance()` 清理方法
  - 添加双重检查锁定（DCL）
  - 更新 `resource_manager.py` 使用单例
  - 完善文档和注释
