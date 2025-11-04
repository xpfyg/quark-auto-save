# 资源管理功能使用说明

## 功能概览

新增的资源管理页面提供了一个可视化的界面来管理和查看所有 `cloud_resource` 表中的资源，并关联 TMDB 影视信息。

## 主要功能

### 1. 资源列表展示
- **卡片式布局**：每个资源以卡片形式展示，包含海报、标题、描述等信息
- **TMDB 集成**：自动显示关联的 TMDB 影视信息（海报、年份、分类、描述）
- **状态标识**：清晰标识资源是否失效

### 2. 多维度排序
支持以下排序方式：
- **更新时间**（默认）：按资源最后更新时间排序
- **创建时间**：按资源创建时间排序
- **热度**：按资源热度值排序
- **浏览次数**：按 view_count 排序
- **分享次数**：按 share_count 排序

每种排序都支持升序/降序切换。

### 3. 智能过滤
- **资源状态过滤**：
  - 仅有效资源（默认）：is_expired = 0
  - 仅失效资源：is_expired = 1
  - 全部资源：显示所有资源
- **搜索功能**：支持按资源名称（drama_name）或别名（alias）模糊搜索
- **防抖优化**：输入 500ms 后自动搜索，避免频繁请求

### 4. 分页浏览
- 支持 12/24/48 条每页的分页显示
- 智能分页控件，显示前后 2 页
- 点击页码快速跳转

### 5. 一键投稿到 Telegram
- **自动检查**：投稿前自动验证资源链接是否有效
- **TMDB 关联**：如果资源未关联 TMDB，会自动查询并关联
- **海报下载**：自动下载 TMDB 海报到本地 `./resource/tmdb/年份/标题#编号.jpg`
- **格式化消息**：按照模板格式化投稿内容，包括：
  - 名称
  - 描述（限制 400 字符）
  - 分享链接
  - 标签（从 TMDB category 转换）

### 6. 统计信息
页面顶部显示实时统计：
- 总资源数
- 有效资源数
- 失效资源数

## 访问方式

### 方式一：直接访问
在浏览器中访问：`http://your-host:5005/resources`

### 方式二：从首页导航
在首页右上角点击 "资源管理" 按钮

## API 接口

### 1. 获取资源列表
```
GET /api/resources
```

参数：
- `page`: 页码（默认 1）
- `per_page`: 每页数量（默认 20）
- `sort_by`: 排序字段（默认 update_time）
- `order`: 排序方向 asc/desc（默认 desc）
- `is_expired`: 过滤状态 0/1/all（默认 0）
- `search`: 搜索关键词

响应：
```json
{
  "total": 100,
  "page": 1,
  "per_page": 20,
  "data": [
    {
      "id": 1,
      "drama_name": "资源名称",
      "link": "https://pan.quark.cn/s/xxx",
      "is_expired": 0,
      "view_count": 10,
      "share_count": 5,
      "hot": 100,
      "tmdb": {
        "title": "影视名称",
        "year_released": 2024,
        "category": "剧情、动作",
        "description": "影视描述",
        "poster_url": "https://image.tmdb.org/..."
      }
    }
  ]
}
```

### 2. 一键投稿
```
POST /api/share_to_tg/{resource_id}
```

响应：
```json
{
  "success": true,
  "message": "投稿成功"
}
```

### 3. 更新资源状态
```
PUT /api/resources/{resource_id}/status
```

请求体：
```json
{
  "is_expired": 1
}
```

## 使用场景

### 场景一：批量管理资源
1. 打开资源管理页面
2. 选择"全部资源"查看所有资源
3. 按热度排序，找出最受欢迎的资源
4. 对失效资源进行标记

### 场景二：定期分享到 Telegram
1. 筛选有效资源
2. 按更新时间降序排列，查看最新资源
3. 逐个点击"一键投稿"分享到 Telegram 频道
4. 系统自动更新 share_count 和 last_share_time

### 场景三：搜索特定资源
1. 在搜索框输入资源名称
2. 系统自动模糊匹配 drama_name 和 alias
3. 查看搜索结果
4. 点击"打开链接"访问资源

## 技术细节

### 前端技术
- **Vue.js 2.x**：响应式数据绑定
- **Bootstrap 4**：UI 组件和样式
- **Axios**：HTTP 请求
- **Bootstrap Icons**：图标库

### 后端技术
- **Flask**：Web 框架
- **SQLAlchemy**：ORM 数据库操作
- **ResourceManager**：资源管理器类
- **TgClient**：Telegram 客户端（异步）

### 数据库表
- `cloud_resource`：云盘资源表
- `tmdb`：TMDB 影视信息表

### 关键设计
1. **延迟初始化**：TelegramClient 在首次调用时才初始化，避免事件循环冲突
2. **异步处理**：使用 `asyncio.new_event_loop()` 在 Flask 同步环境中执行异步操作
3. **数据关联**：通过 LEFT JOIN 关联 cloud_resource 和 tmdb 表
4. **防抖搜索**：避免频繁请求，提升性能

## 注意事项

1. **环境变量配置**
   确保已配置以下环境变量：
   - `QUARK_COOKIE`：夸克网盘 Cookie
   - `TG_API_ID`：Telegram API ID
   - `TG_API_HASH`：Telegram API Hash
   - `TG_SESSION_NAME`：Telegram Session 名称
   - `TMDB_API_KEY`（可选）：TMDB API Key

2. **数据库连接**
   确保数据库连接正常，参考 `db.py` 和 `.env.example`

3. **海报存储**
   海报文件会保存在 `./resource/tmdb/年份/` 目录下，请确保该目录有写权限

4. **投稿限制**
   - 只能投稿有效资源（is_expired = 0）
   - 投稿前会自动检查链接有效性
   - 必须有关联的 TMDB 信息

## 常见问题

### Q: 为什么有些资源没有海报？
A: 可能是以下原因：
1. 资源未关联 TMDB（tmdb_id 为 NULL）
2. TMDB API Key 未配置
3. TMDB 上找不到对应的影视信息

### Q: 投稿失败怎么办？
A: 检查以下几点：
1. Telegram 环境变量是否正确配置
2. 资源链接是否有效
3. 是否有 TMDB 信息
4. 查看服务器日志获取详细错误信息

### Q: 如何批量导入资源？
A: 参考 `resource_manager.py` 中的 `process_resource()` 方法，可以编写脚本批量处理。

## 未来优化方向

1. **批量操作**：支持批量投稿、批量标记失效
2. **预览功能**：投稿前预览格式化后的消息
3. **投稿历史**：记录投稿历史和结果
4. **自动检测**：定期自动检测链接有效性
5. **标签管理**：自定义资源标签和分类
6. **导出功能**：导出资源列表为 Excel/CSV

## 相关文件

- `app/run.py`：Flask 路由定义（资源管理相关路由：272-390 行）
- `app/templates/resources.html`：资源管理页面模板
- `resource_manager.py`：ResourceManager 类定义
- `telegram_sdk/tg.py`：TgClient 类定义
- `model/cloud_resource.py`：CloudResource 模型
- `model/tmdb.py`：Tmdb 模型
