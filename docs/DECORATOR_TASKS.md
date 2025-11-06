# 定时任务装饰器使用指南

## 概述

系统使用 **Flask-APScheduler** 的装饰器方式定义定时任务，使代码更简洁、更符合 Python 风格。

## 文件结构

```
.
├── extensions.py          # 共享的 scheduler 实例
├── job.py                 # 定时任务定义（使用装饰器）
└── run.py                 # Flask 应用（初始化 scheduler）
```

## 快速开始

### 1. 定义定时任务

在 `job.py` 中使用装饰器定义任务：

```python
from extensions import scheduler

@scheduler.task('cron', id='my_task', hour=2, minute=0)
def my_task():
    """每天凌晨 02:00 执行"""
    logging.info("执行我的任务...")
    # 你的任务逻辑
```

### 2. 启动应用

```bash
python3 run.py
```

装饰器会自动注册，无需额外配置！

## 装饰器参数

### Cron 触发器 (定时执行)

```python
@scheduler.task('cron', id='task_id', **cron_params)
```

**常用参数**:
- `hour` (int|str): 小时 (0-23)
- `minute` (int|str): 分钟 (0-59)
- `second` (int|str): 秒 (0-59)
- `day` (int|str): 日期 (1-31)
- `month` (int|str): 月份 (1-12)
- `day_of_week` (int|str): 星期 (0-6 或 mon, tue, wed, thu, fri, sat, sun)

**示例**:

```python
# 每天 02:00 执行
@scheduler.task('cron', id='daily_task', hour=2, minute=0)
def daily_task():
    pass

# 每周一 09:00 执行
@scheduler.task('cron', id='weekly_task', day_of_week='mon', hour=9)
def weekly_task():
    pass

# 每月 1 号凌晨执行
@scheduler.task('cron', id='monthly_task', day=1, hour=0, minute=0)
def monthly_task():
    pass

# 每隔 2 小时执行（使用 cron 表达式）
@scheduler.task('cron', id='interval_task', hour='*/2')
def interval_cron_task():
    pass

# 工作日每天 08:30 执行
@scheduler.task('cron', id='weekday_task',
                day_of_week='mon-fri', hour=8, minute=30)
def weekday_task():
    pass
```

### Interval 触发器 (间隔执行)

```python
@scheduler.task('interval', id='task_id', **interval_params)
```

**常用参数**:
- `seconds` (int): 间隔秒数
- `minutes` (int): 间隔分钟数
- `hours` (int): 间隔小时数
- `days` (int): 间隔天数
- `weeks` (int): 间隔周数

**示例**:

```python
# 每隔 10 秒执行
@scheduler.task('interval', id='fast_task', seconds=10)
def fast_task():
    pass

# 每隔 30 分钟执行
@scheduler.task('interval', id='half_hour_task', minutes=30)
def half_hour_task():
    pass

# 每隔 6 小时执行
@scheduler.task('interval', id='six_hour_task', hours=6)
def six_hour_task():
    pass

# 每隔 1 天执行
@scheduler.task('interval', id='daily_interval_task', days=1)
def daily_interval_task():
    pass
```

### Date 触发器 (单次执行)

```python
@scheduler.task('date', id='task_id', run_date='2025-12-31 23:59:59')
def one_time_task():
    """在指定时间执行一次"""
    pass
```

## 已注册的任务

### check_resources_links

**装饰器**:
```python
@scheduler.task('cron', id='check_resources_links', hour=2, minute=0)
```

**功能**: 检查所有云盘资源链接的有效性

**执行时间**: 每天凌晨 02:00

**修改执行时间**:
```python
# 改为每天 03:30 执行
@scheduler.task('cron', id='check_resources_links', hour=3, minute=30)
```

## 添加新任务

### 步骤 1: 在 job.py 中添加装饰器函数

```python
from extensions import scheduler

@scheduler.task('cron', id='cleanup_temp_files', hour=4, minute=0)
def cleanup_temp_files():
    """
    清理临时文件
    每天凌晨 04:00 执行
    """
    try:
        logging.info("🧹 开始清理临时文件...")

        import shutil
        temp_dir = "temp_posters"
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            os.makedirs(temp_dir)

        logging.info("✅ 临时文件清理完成")
    except Exception as e:
        logging.error(f"❌ 清理失败: {str(e)}")
```

### 步骤 2: 重启应用

```bash
# 停止应用 (Ctrl+C)
# 重新启动
python3 run.py
```

新任务会自动注册并开始运行！

## 查看任务状态

### 方法 1: 查看启动日志

```
✅ 定时任务已注册
```

### 方法 2: 访问 API

```bash
curl http://localhost:5005/scheduler/jobs
```

返回所有已注册任务的 JSON 信息。

### 方法 3: 查看执行日志

```bash
tail -f logs/app.log | grep "check_resources"
```

## 手动触发任务

### 方法 1: API 接口

```bash
curl -X POST http://localhost:5005/api/check_resources_links
```

### 方法 2: 命令行

```bash
python3 -c "from job import check_all_resources_links; check_all_resources_links()"
```

### 方法 3: 直接运行

```bash
python3 job.py
```

## 最佳实践

### 1. 任务命名

使用清晰的函数名和 ID：

```python
# ✅ 好
@scheduler.task('cron', id='sync_tmdb_daily', hour=3)
def sync_tmdb_daily():
    pass

# ❌ 不好
@scheduler.task('cron', id='task1', hour=3)
def t1():
    pass
```

### 2. 错误处理

每个任务都应该有完整的异常处理：

```python
@scheduler.task('cron', id='my_task', hour=2)
def my_task():
    try:
        # 任务逻辑
        pass
    except Exception as e:
        logging.error(f"❌ 任务失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理资源
        db_session.remove()
```

### 3. 数据库会话

始终在 finally 中清理数据库会话：

```python
@scheduler.task('cron', id='db_task', hour=2)
def db_task():
    try:
        resource = db_session.query(...).first()
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        logging.error(f"错误: {e}")
    finally:
        db_session.remove()  # 重要！
```

### 4. 日志记录

使用结构化日志：

```python
@scheduler.task('cron', id='my_task', hour=2)
def my_task():
    logging.info("=" * 60)
    logging.info(f"🚀 任务开始 - {datetime.now()}")
    logging.info("=" * 60)

    # 任务逻辑...

    logging.info("=" * 60)
    logging.info("✅ 任务完成")
    logging.info("=" * 60)
```

### 5. 性能考虑

对于耗时任务，添加进度提示和速率限制：

```python
import time
import random

@scheduler.task('cron', id='bulk_task', hour=2)
def bulk_task():
    items = get_items()

    for i, item in enumerate(items, 1):
        process(item)

        # 进度提示
        if i % 100 == 0:
            logging.info(f"进度: {i}/{len(items)}")

        # 速率限制
        time.sleep(random.uniform(0.5, 1.5))
```

## 常见装饰器模式

### 每天固定时间
```python
@scheduler.task('cron', id='backup', hour=1, minute=30)
def backup():
    """每天 01:30 备份"""
    pass
```

### 每隔几小时
```python
@scheduler.task('interval', id='check', hours=4)
def check():
    """每隔 4 小时检查"""
    pass
```

### 工作日执行
```python
@scheduler.task('cron', id='report',
                day_of_week='mon-fri', hour=9)
def report():
    """工作日 09:00 生成报告"""
    pass
```

### 每周一次
```python
@scheduler.task('cron', id='weekly',
                day_of_week='sun', hour=0, minute=0)
def weekly():
    """每周日凌晨执行"""
    pass
```

### 每月一次
```python
@scheduler.task('cron', id='monthly',
                day=1, hour=0, minute=0)
def monthly():
    """每月 1 号凌晨执行"""
    pass
```

## 调试技巧

### 1. 临时调整执行间隔

测试时可以临时改为频繁执行：

```python
# 生产环境：每天 02:00
@scheduler.task('cron', id='my_task', hour=2, minute=0)

# 测试环境：每分钟
@scheduler.task('interval', id='my_task', minutes=1)
```

### 2. 添加调试日志

```python
@scheduler.task('cron', id='my_task', hour=2)
def my_task():
    logging.debug(f"任务启动时间: {datetime.now()}")
    # 任务逻辑...
    logging.debug("任务执行完成")
```

### 3. 查看下次执行时间

```bash
curl http://localhost:5005/scheduler/jobs | python3 -m json.tool
```

查看 `next_run_time` 字段。

## 参考资料

- [Flask-APScheduler 文档](https://github.com/viniciuschiele/flask-apscheduler)
- [APScheduler 装饰器](https://apscheduler.readthedocs.io/en/stable/userguide.html#adding-jobs)
- [Cron 表达式参考](https://crontab.guru/)

---

**更新时间**: 2025-11-05
**版本**: v2.0.0 (装饰器版本)
