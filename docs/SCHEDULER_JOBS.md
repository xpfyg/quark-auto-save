# 定时任务系统说明

## 概述

系统使用 **Flask-APScheduler** 实现定时任务管理，所有定时任务逻辑在 `job.py` 中实现，与 Flask 应用主逻辑（`run.py`）分离。

## 架构设计

### 文件结构

```
.
├── run.py                    # Flask 应用主文件
│   ├── 导入 job 模块
│   ├── 初始化 Flask-APScheduler
│   └── 调用 job.register_jobs() 注册任务
│
├── job.py                    # 定时任务逻辑文件
│   ├── check_all_resources_links()  # 资源链接检查任务
│   └── register_jobs()              # 注册所有定时任务
│
└── resource_manager.py       # 资源管理模块
    └── check_share_link()    # 链接有效性检查函数
```

### 调度器类型

系统中存在两个调度器：

1. **BackgroundScheduler** (`scheduler`)
   - 用途：调度 `quark_auto_save.py` 脚本执行
   - 场景：通过 WebUI 配置的 crontab 定时转存任务

2. **Flask-APScheduler** (`flask_scheduler`)
   - 用途：应用内定时任务（如资源链接检查）
   - 场景：需要访问数据库和应用上下文的后台任务

## 已实现的定时任务

### 1. 资源链接有效性检查 (check_resources_links)

**功能描述**:
- 遍历所有未失效的云盘资源
- 检测分享链接是否仍然有效
- 自动更新失效资源的状态

**执行时间**: 每天凌晨 02:00

**执行逻辑**:
```python
1. 查询所有 is_expired=0 的资源
2. 对每个资源调用 check_share_link()
3. 每个链接检测后随机间隔 1-3 秒
4. 每检测 10 个链接后额外间隔 10 秒
5. 自动更新失效资源的 is_expired 状态
6. 输出统计报告
```

**日志示例**:
```
============================================================
🔍 开始检查资源链接有效性 - 2025-11-05 02:00:00
============================================================
📊 共找到 50 个未失效资源需要检查

[1/50] 检查资源: 电影名称
  └─ 链接: https://pan.quark.cn/s/xxx
  ✅ 链接有效
  ⏱️  等待 2.3 秒...

[10/50] 检查资源: 剧集名称
  └─ 链接: https://pan.quark.cn/s/yyy
  ❌ 链接已失效
  ⏸️  已检测 10 个资源，休息 10 秒...

...

============================================================
📈 检查完成 - 统计结果
============================================================
总数量: 50
✅ 有效: 45
❌ 失效: 4
⚠️  错误: 1
完成时间: 2025-11-05 02:15:30
============================================================
```

## 使用方法

### 1. 自动执行（定时任务）

任务会按照配置的 cron 表达式自动执行，无需手动干预。

**默认配置**:
- `check_resources_links`: 每天 02:00 执行

**修改执行时间**:

编辑 `job.py` 中的 `register_jobs()` 函数：

```python
def register_jobs(scheduler):
    scheduler.add_job(
        id='check_resources_links',
        func=check_all_resources_links,
        trigger='cron',
        hour=2,        # 修改小时
        minute=0,      # 修改分钟
        replace_existing=True
    )
```

支持的 cron 参数：
- `hour`: 小时 (0-23)
- `minute`: 分钟 (0-59)
- `day`: 日期 (1-31)
- `month`: 月份 (1-12)
- `day_of_week`: 星期 (0-6, 0=周一)

示例：
```python
# 每周一凌晨 3 点执行
trigger='cron', hour=3, minute=0, day_of_week=0

# 每月 1 号凌晨 2 点执行
trigger='cron', hour=2, minute=0, day=1

# 每天每隔 6 小时执行
trigger='cron', hour='*/6'
```

### 2. 手动触发（API 接口）

**接口**: `POST /api/check_resources_links`

**认证**: 需要登录

**请求**:
```bash
curl -X POST http://localhost:5005/api/check_resources_links \
  -H "Cookie: session=your_session_cookie"
```

**响应**:
```json
{
  "success": true,
  "message": "资源链接检查任务已启动，请查看日志了解进度"
}
```

**说明**:
- 任务在后台线程中执行，不会阻塞 HTTP 请求
- 立即返回成功响应
- 任务执行进度和结果在服务器日志中查看

### 3. 命令行测试

**直接运行 job.py**:
```bash
python3 job.py
```

这会立即执行资源链接检查任务，适合开发测试使用。

## 添加新的定时任务

### 步骤 1: 在 job.py 中定义任务函数

```python
def your_new_task():
    """
    新的定时任务
    """
    try:
        logging.info("🚀 开始执行新任务...")

        # 你的任务逻辑
        # ...

        logging.info("✅ 任务执行完成")
    except Exception as e:
        logging.error(f"❌ 任务执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理资源
        db_session.remove()
```

### 步骤 2: 在 register_jobs() 中注册任务

```python
def register_jobs(scheduler):
    # 已有任务
    scheduler.add_job(
        id='check_resources_links',
        func=check_all_resources_links,
        trigger='cron',
        hour=2,
        minute=0,
        replace_existing=True
    )

    # 新增任务
    scheduler.add_job(
        id='your_new_task',
        func=your_new_task,
        trigger='cron',
        hour=10,              # 每天 10:00 执行
        minute=0,
        replace_existing=True
    )

    logging.info("✅ 定时任务已注册:")
    logging.info("  - check_resources_links: 每天 02:00")
    logging.info("  - your_new_task: 每天 10:00")
```

### 步骤 3: 重启应用

```bash
# 如果使用 systemd
sudo systemctl restart quark-auto-save

# 如果手动运行
# 按 Ctrl+C 停止，然后重新运行
python3 run.py
```

## 监控和调试

### 查看任务状态

**方法 1: 查看日志**

```bash
# 实时查看日志
tail -f logs/app.log

# 过滤定时任务日志
tail -f logs/app.log | grep "check_resources"
```

**方法 2: Flask-APScheduler API**

访问: `http://localhost:5005/scheduler/jobs`

返回所有已注册的任务信息（JSON格式）。

### 常见问题

#### 1. 任务没有执行

**检查项**:
- 确认 Flask-APScheduler 已启动: 查看启动日志 "✅ 定时任务已注册"
- 确认任务已注册: 访问 `/scheduler/jobs` 查看
- 检查系统时间是否正确: `date`
- 查看错误日志: 搜索 "❌"

#### 2. 任务执行报错

**常见原因**:
- 数据库连接失败: 检查 `.env` 配置
- QUARK_COOKIE 未配置: 设置环境变量
- 资源不存在: 确认数据库中有未失效资源

#### 3. 任务执行时间过长

**优化建议**:
- 减少每次检查的资源数量
- 增加间隔时间
- 分批次执行（例如每次只检查 100 个）

**示例**:
```python
# 限制每次检查的数量
resources = db_session.query(CloudResource).filter(
    CloudResource.is_expired == 0,
    CloudResource.link.isnot(None)
).limit(100).all()  # 每次最多 100 个
```

## 最佳实践

### 1. 错误处理

每个任务函数都应该包含完整的异常处理：

```python
def my_task():
    try:
        # 任务逻辑
        pass
    except Exception as e:
        logging.error(f"❌ 任务失败: {str(e)}")
        traceback.print_exc()
    finally:
        # 清理资源
        db_session.remove()
```

### 2. 日志记录

使用结构化的日志输出：

```python
logging.info("=" * 60)
logging.info(f"🚀 任务开始 - {datetime.now()}")
logging.info("=" * 60)
# ... 任务逻辑 ...
logging.info("=" * 60)
logging.info(f"✅ 任务完成 - 统计信息")
logging.info("=" * 60)
```

### 3. 速率限制

避免对外部 API 造成压力：

```python
import time
import random

for item in items:
    process(item)

    # 随机延迟
    time.sleep(random.uniform(1, 3))

    # 每 N 次额外休息
    if index % 10 == 0:
        time.sleep(10)
```

### 4. 数据库会话管理

始终在 `finally` 块中清理数据库会话：

```python
try:
    # 数据库操作
    resource = db_session.query(...).first()
    db_session.commit()
except Exception as e:
    db_session.rollback()
    raise
finally:
    db_session.remove()
```

## 配置文件

### 环境变量

```bash
# .env 文件

# 必需
QUARK_COOKIE=your_cookie_here

# 可选
DB_HOST=localhost
DB_PORT=3306
DB_USERNAME=root
DB_PASSWORD=password
DB_DATABASE=quark_db
```

### Flask 配置

```python
# run.py

app.config['SCHEDULER_API_ENABLED'] = True  # 启用 API
app.config['SCHEDULER_TIMEZONE'] = 'Asia/Shanghai'  # 时区
```

## 性能优化

### 批量处理

```python
# 分批查询
batch_size = 100
offset = 0

while True:
    resources = db_session.query(CloudResource).filter(
        CloudResource.is_expired == 0
    ).limit(batch_size).offset(offset).all()

    if not resources:
        break

    for resource in resources:
        check_resource(resource)

    offset += batch_size
```

### 并发执行

```python
from concurrent.futures import ThreadPoolExecutor

def check_resources_concurrent():
    resources = get_resources()

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(check_resource, res)
            for res in resources
        ]

        for future in futures:
            future.result()
```

## 参考资料

- [Flask-APScheduler 文档](https://github.com/viniciuschiele/flask-apscheduler)
- [APScheduler 文档](https://apscheduler.readthedocs.io/)
- [Cron 表达式说明](https://crontab.guru/)

---

**更新时间**: 2025-11-05
**版本**: v1.0.0
