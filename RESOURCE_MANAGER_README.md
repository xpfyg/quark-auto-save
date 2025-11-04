# 资源管理器使用说明

## 文件说明

已创建以下文件来实现资源管理功能：

1. **model/cloud_resource.py** - 云盘资源数据库模型
2. **model/tmdb.py** - TMDB影视信息数据库模型
3. **resource_manager.py** - 资源管理核心逻辑

## 功能说明

`resource_manager.py` 实现了以下功能：

1. ✅ 检查剧名是否在 `cloud_resource` 表中且为有效状态
   - 如果存在且有效，直接返回资源信息和对应的 TMDB 信息
   - 如果不存在或已失效，执行后续转存流程

2. ✅ 调用 `do_save_check` 函数转存到自己账号

3. ✅ 调用 TMDB API 查询影视信息（海报、描述等）

4. ✅ 保存资源信息到数据库

## 快速开始

### 0. 数据库初始化

首先需要创建数据库和表：

```bash
# 方法1: 使用提供的 SQL 脚本
mysql -u root -p < init_database.sql

# 方法2: 手动创建（如果已有数据库）
mysql -u root -p pan_library < init_database.sql
```

### 1. 环境变量配置

推荐使用 `.env` 文件管理环境变量（已有 `.env.example` 模板）：

```bash
# 复制示例配置文件
cp .env.example .env

# 编辑 .env 文件，填入真实配置
vim .env
```

或者直接设置环境变量：

```bash
# 必需：数据库配置
export DB_USERNAME="root"
export DB_PASSWORD="your_password"
export DB_HOST="localhost"
export DB_PORT="3306"
export DB_DATABASE="pan_library"

# 必需：夸克网盘Cookie
export QUARK_COOKIE="your_quark_cookie_here"

# 可选：TMDB API Key（用于获取影视信息）
export TMDB_API_KEY="your_tmdb_api_key_here"
```

### 2. 测试数据库连接

配置完成后，测试数据库连接是否正常：

```bash
python3 test_db.py
```

如果配置正确，你会看到：
- ✅ 数据库连接成功
- 📋 数据库中的表列表
- ✅ 所有必需的表都存在

### 3. Python代码调用

```python
from resource_manager import ResourceManager

# 初始化资源管理器
cookie = "your_quark_cookie"
manager = ResourceManager(cookie, drive_type="quark")

# 处理资源
drama_name = "权力的游戏"
share_link = "https://pan.quark.cn/s/xxxxx"
savepath = "/电视剧/权力的游戏"

result = manager.process_resource(drama_name, share_link, savepath)

# 检查结果
if result["status"] == "existing":
    print("资源已存在")
    print(f"资源信息: {result['resource']}")
    print(f"TMDB信息: {result['tmdb']}")

elif result["status"] == "saved":
    print("资源已转存并保存")
    print(f"资源信息: {result['resource']}")
    print(f"TMDB信息: {result['tmdb']}")

else:
    print(f"处理失败: {result['message']}")
```

### 4. 直接运行测试

```bash
# 设置环境变量后直接运行
python3 resource_manager.py
```

## 主要类说明

### TmdbService

TMDB API服务类，负责查询影视信息。

**方法：**
- `search_drama(drama_name)`: 搜索剧集信息，自动尝试电视剧和电影

### ResourceManager

资源管理器主类。

**方法：**
- `__init__(cookie, drive_type="quark")`: 初始化，验证账号
- `process_resource(drama_name, share_link, savepath="/")`: 处理资源的主要方法

**返回值格式：**
```python
{
    "status": "existing|saved|failed",
    "resource": {
        "id": 1,
        "drama_name": "权力的游戏",
        "link": "https://...",
        "is_expired": 0,
        "tmdb_id": 10,
        # ... 其他字段
    },
    "tmdb": {
        "id": 10,
        "title": "权力的游戏",
        "year_released": 2011,
        "category": "剧情、奇幻、冒险",
        "description": "...",
        "poster_url": "https://image.tmdb.org/t/p/w500/...",
        # ... 其他字段
    }
}
```

## 获取 TMDB API Key

1. 访问 https://www.themoviedb.org/
2. 注册账号并登录
3. 进入 Settings → API
4. 申请 API Key（选择 Developer）
5. 复制 API Key (v3 auth) 并设置到环境变量

## 数据库表结构

### cloud_resource 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键ID |
| drama_name | varchar(255) | 剧名 |
| drive_type | varchar(50) | 网盘类型（quark等） |
| link | text | 分享链接 |
| is_expired | tinyint | 是否失效（0有效，1失效） |
| tmdb_id | int | 关联的TMDB信息ID |
| ... | ... | 其他字段 |

### tmdb 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键ID |
| tmdb_code | varchar(255) | TMDB编号 |
| title | varchar(255) | 剧名 |
| year_released | int | 上映年份 |
| category | varchar(100) | 分类 |
| description | text | 剧情描述 |
| poster_url | varchar(500) | 海报URL |
| ... | ... | 其他字段 |

## 注意事项

1. 确保数据库中已创建 `cloud_resource` 和 `tmdb` 表
2. Cookie 需要包含完整的认证信息
3. TMDB API 有请求频率限制，建议合理使用
4. 转存功能依赖 `quark_auto_save.py` 中的 `Quark` 类
