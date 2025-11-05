# 网盘资源管理功能说明

## 功能概述

新增的"网盘资源"功能允许你直接浏览夸克网盘中的文件，并一键分享、保存到数据库，同时自动获取 TMDB 信息。

## 功能特点

### 1. 浏览网盘文件
- 📁 支持目录导航，可进入子目录查看
- 🔍 显示文件详细信息（大小、创建时间）
- 🎨 文件类型图标识别（视频、音频、图片、压缩包等）

### 2. 批量操作
- ✅ 支持多选文件
- 📦 批量分享并保存到数据库
- 🔄 自动添加 TMDB 更新任务到队列

### 3. 自动化流程
```
选择文件 → 创建分享链接 → 保存到数据库 → 队列更新 TMDB 信息
```

## 使用方法

### 方法一：从资源管理页面进入

1. 登录系统
2. 进入"资源管理"页面
3. 点击右上角的"网盘资源"按钮
4. 浏览并选择要分享的文件

### 方法二：直接访问

访问：`http://your-domain:5005/quark_files`

## 操作流程

### 单个文件分享

1. **浏览文件**
   - 进入网盘资源页面
   - 导航到目标目录

2. **分享文件**
   - 点击文件右侧的"分享并保存"按钮
   - 确认操作

3. **自动处理**
   - ✅ 创建分享链接
   - ✅ 保存到数据库（cloud_resource 表）
   - ✅ 添加 TMDB 更新任务到队列
   - ✅ 后台自动获取 TMDB 信息

### 批量文件分享

1. **选择多个文件**
   - 勾选要分享的文件/文件夹
   - 已选文件数量会显示在顶部

2. **批量分享**
   - 点击"批量分享并保存"按钮
   - 确认批量操作

3. **查看结果**
   - 操作完成后显示成功/失败统计
   - 失败的文件会在控制台输出错误信息

## 技术细节

### 前端页面
**文件位置**: `public/templates/quark_files.html`

**主要功能**:
- Vue.js 驱动的单页应用
- 面包屑导航
- 文件类型识别和图标显示
- 批量选择和操作

### 后端 API

#### 1. 获取文件列表
```
GET /api/quark/ls_dir?pdir_fid={fid}
```

**参数**:
- `pdir_fid`: 父目录 fid，默认 "0"（根目录）

**响应**:
```json
{
  "success": true,
  "files": [
    {
      "fid": "文件ID",
      "file_name": "文件名",
      "size": 1234567,
      "created_at": 1234567890,
      "dir": false
    }
  ]
}
```

#### 2. 分享并保存
```
POST /api/quark/share_and_save
```

**请求体**:
```json
{
  "fid": "文件ID",
  "file_name": "文件名"
}
```

**处理流程**:
1. 调用 `quark.share_dir()` 创建分享链接
2. 检查数据库是否已存在该资源
   - 存在：更新分享链接和过期状态
   - 不存在：创建新资源记录
3. 提交数据库事务
4. 创建 TMDB 更新任务并添加到队列

**响应**:
```json
{
  "success": true,
  "message": "分享并保存成功！已添加 TMDB 更新任务",
  "resource_id": 123,
  "share_url": "https://pan.quark.cn/s/xxx"
}
```

### 队列任务集成

分享成功后，系统会自动创建 TMDB 更新任务：

```python
Task(
    task_type=TaskType.TMDB_UPDATE,
    task_data={
        "resource_id": 123,
        "drama_name": "文件名",
        "category": "电影"
    }
)
```

任务会被添加到队列管理器，由 `handle_tmdb_update` 处理器异步执行：
1. 搜索 TMDB 信息
2. 保存/更新 TMDB 记录
3. 关联资源和 TMDB 信息

## 数据库表结构

### cloud_resource 表

创建的资源记录包含以下字段：
- `drama_name`: 文件名
- `drive_type`: "quark"
- `link`: 分享链接
- `is_expired`: 0（有效）
- `category1`: "影视资源"
- `category2`: "待分类"（可后续更新为具体分类）
- `tmdb_id`: NULL（由队列任务更新）

## 注意事项

### 1. Cookie 配置

确保已配置夸克网盘 Cookie：
- 环境变量：`QUARK_COOKIE`
- 或配置文件：`quark_config.json` 中的 `quark_cookie`

### 2. 文件类型识别

系统会根据文件扩展名自动识别类型：
- 视频：mp4, mkv, avi, mov, wmv
- 音频：mp3, wav, flac
- 图片：jpg, jpeg, png, gif, bmp
- 压缩包：zip, rar, 7z, tar, gz

### 3. TMDB 自动匹配

- 默认类型为"电影"
- 如果文件名包含特定关键词，可考虑增强分类逻辑
- TMDB 更新任务在后台异步执行
- 可在队列状态页面查看任务进度

### 4. 性能优化

- 批量操作时逐个处理，避免并发问题
- 大量文件建议分批次处理
- 队列管理器确保任务顺序执行

## 故障排查

### 问题1：无法加载文件列表

**可能原因**:
- Cookie 失效
- 网络连接问题
- fid 参数错误

**解决方法**:
1. 检查 Cookie 配置
2. 查看后端日志
3. 尝试重新登录夸克网盘

### 问题2：分享失败

**可能原因**:
- 文件不存在
- 权限不足
- 分享配额用尽

**解决方法**:
1. 确认文件存在
2. 检查夸克账号状态
3. 查看后端错误日志

### 问题3：TMDB 未更新

**可能原因**:
- TMDB API Key 未配置
- 队列管理器未运行
- 文件名无法匹配 TMDB

**解决方法**:
1. 配置 `TMDB_API_KEY` 环境变量
2. 检查队列管理器状态：`/api/queue_status`
3. 手动在资源管理页面匹配 TMDB

## 扩展功能建议

### 1. 智能分类
根据文件名关键词自动识别类型：
- 包含"S01E01"等 → 剧集
- 包含"EP"等 → 动漫
- 其他 → 电影

### 2. 批量重命名
提供文件重命名功能，统一命名规范

### 3. 目录同步
支持监控特定目录，自动同步新增文件

### 4. 分享管理
管理所有创建的分享链接，支持刷新过期链接

## API 测试示例

### 使用 curl 测试

```bash
# 1. 登录
curl -X POST http://localhost:5005/login \
  -d "username=admin&password=admin123" \
  -c cookies.txt

# 2. 获取根目录文件列表
curl -X GET "http://localhost:5005/api/quark/ls_dir?pdir_fid=0" \
  -b cookies.txt

# 3. 分享并保存文件
curl -X POST http://localhost:5005/api/quark/share_and_save \
  -H "Content-Type: application/json" \
  -d '{"fid":"xxx","file_name":"电影名称"}' \
  -b cookies.txt
```

### 使用 Python 测试

```python
import requests

# 登录
session = requests.Session()
session.post("http://localhost:5005/login", data={
    "username": "admin",
    "password": "admin123"
})

# 获取文件列表
response = session.get("http://localhost:5005/api/quark/ls_dir", params={
    "pdir_fid": "0"
})
files = response.json()["files"]

# 分享第一个文件
if files:
    response = session.post("http://localhost:5005/api/quark/share_and_save", json={
        "fid": files[0]["fid"],
        "file_name": files[0]["file_name"]
    })
    print(response.json())
```

---

**更新时间**: 2025-01-05
**版本**: v1.0.0
