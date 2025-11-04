# ResourceManager search_drama 方法优化说明

## 更新内容

对 `resource_manager.py` 中的 `TmdbService.search_drama()` 方法进行了优化，新增 `category` 参数以提高 TMDB 查询的准确性和效率。

## 主要改进

### 1. 新增 `category` 参数

**方法签名更新**：
```python
# 旧版本
def search_drama(self, drama_name):
    ...

# 新版本
def search_drama(self, drama_name, category="电影"):
    ...
```

**参数说明**：
- `drama_name`: 剧名（必需）
- `category`: 资源类型，可选值为 `"电影"` 或 `"剧集"`，默认为 `"电影"`

### 2. 智能查询顺序

根据 `category` 参数优化 TMDB API 调用顺序：

#### 当 `category="电影"` 时
1. **优先**查询 TMDB 电影 API (`/search/movie`)
2. 如果未找到，**回退**到电视剧 API (`/search/tv`)

#### 当 `category="剧集"` 时
1. **优先**查询 TMDB 电视剧 API (`/search/tv`)
2. 如果未找到，**回退**到电影 API (`/search/movie`)

### 3. 更好的日志输出

新增了更详细的日志输出，明确显示匹配的类型：

```python
✅ 在TMDB找到电影: 肖申克的救赎
✅ 在TMDB找到电视剧: 权力的游戏
```

## 使用示例

### 基本用法

```python
from resource_manager import TmdbService

tmdb_service = TmdbService()

# 查询电影（默认）
result = tmdb_service.search_drama("肖申克的救赎")

# 明确指定为电影
result = tmdb_service.search_drama("肖申克的救赎", category="电影")

# 查询剧集
result = tmdb_service.search_drama("权力的游戏", category="剧集")
```

### 结合 classify_drama_type 脚本使用

先使用豆包AI自动分类，然后查询 TMDB：

```python
from resource_manager import ResourceManager

# 假设资源已经通过 classify_drama_type.py 分类
# cloud_resource.category2 = "电影" 或 "剧集"

manager = ResourceManager(cookie)

# 使用已分类的类型优化查询
result = manager.process_resource(
    drama_name="肖申克的救赎",
    share_link="https://pan.quark.cn/s/xxx",
    savepath="/Movies",
    category="电影"  # 使用分类结果
)
```

## 相关方法更新

### 1. `ResourceManager.process_resource()`

**更新签名**：
```python
def process_resource(self, drama_name, share_link, savepath="/", category="电影"):
    ...
```

新增 `category` 参数，传递给 `search_drama` 方法优化 TMDB 查询。

**使用场景**：
```python
# 处理电影资源
manager.process_resource(
    drama_name="盗梦空间",
    share_link="https://pan.quark.cn/s/xxx",
    savepath="/Movies",
    category="电影"
)

# 处理剧集资源
manager.process_resource(
    drama_name="绝命毒师",
    share_link="https://pan.quark.cn/s/xxx",
    savepath="/TVShows",
    category="剧集"
)
```

### 2. `ResourceManager.shareToTgBot()`

自动使用资源的 `category2` 字段优化 TMDB 查询：

```python
async def shareToTgBot(self, id):
    ...
    # 自动读取资源的 category2 字段
    category = resource.category2 if resource.category2 in ["电影", "剧集"] else "电影"
    tmdb_data = self.tmdb_service.search_drama(resource.drama_name, category=category)
    ...
```

## 优势与效果

### 1. 提高准确性

- **精准匹配**：根据已知类型直接查询对应 API，减少误匹配
- **避免混淆**：例如 "终结者" 既是电影又是剧集，通过 category 参数可以准确定位

### 2. 提升效率

- **减少 API 调用**：优先查询正确的类型，减少不必要的回退查询
- **节省时间**：对于明确类型的资源，可以减少 50% 的 API 请求

### 3. 更好的集成

- **与 classify_drama_type 脚本协同**：先用豆包AI分类，再精准查询 TMDB
- **数据一致性**：category2 字段可以在整个系统中保持类型一致

## 完整工作流

```
1. 新增资源
   ↓
2. classify_drama_type.py 自动分类
   → 更新 cloud_resource.category2 = "电影" 或 "剧集"
   ↓
3. process_resource() 或 shareToTgBot()
   → 使用 category2 优化 TMDB 查询
   → 获取更准确的影视信息
   ↓
4. 保存到数据库或分享到 Telegram
```

## 测试

### 运行测试脚本

```bash
# 设置 TMDB API Key
export TMDB_API_KEY='your_api_key'

# 运行测试
python3 test_search_drama.py
```

### 测试用例

测试脚本包含以下用例：

1. **电影类型**：
   - 肖申克的救赎
   - 盗梦空间
   - 流浪地球

2. **剧集类型**：
   - 权力的游戏
   - 绝命毒师

3. **默认参数测试**：验证不指定 category 时默认为 "电影"

### 预期输出

```
============================================================
测试 search_drama 方法的 category 参数功能
============================================================

[测试 1/5] 经典电影
名称: 肖申克的救赎
类型: 电影
----------------------------------------
✅ 在TMDB找到电影: The Shawshank Redemption
✅ 查询成功!
  标题: The Shawshank Redemption
  年份: 1994
  类别: 剧情、犯罪
  TMDB ID: 278

...

============================================================
测试完成!
============================================================
```

## 向后兼容性

✅ **完全兼容**：现有代码无需修改

```python
# 旧代码仍然有效（使用默认 category="电影"）
result = tmdb_service.search_drama("肖申克的救赎")

# 新代码可以指定类型
result = tmdb_service.search_drama("肖申克的救赎", category="电影")
```

## 最佳实践

### 1. 结合自动分类使用

```python
# 先运行分类脚本
python3 classify_drama_type.py

# 然后在代码中使用分类结果
resource = db_session.query(CloudResource).filter(...).first()
category = resource.category2 if resource.category2 else "电影"
tmdb_data = tmdb_service.search_drama(resource.drama_name, category=category)
```

### 2. 批量处理时指定类型

```python
# 处理电影文件夹
for movie in movie_list:
    manager.process_resource(movie['name'], movie['link'], "/Movies", category="电影")

# 处理剧集文件夹
for drama in drama_list:
    manager.process_resource(drama['name'], drama['link'], "/TVShows", category="剧集")
```

### 3. 用户输入时提供选项

```python
# Web UI 或 CLI 中提供类型选择
category = user_input("请选择类型 (1: 电影, 2: 剧集): ")
category = "电影" if category == "1" else "剧集"
manager.process_resource(name, link, path, category=category)
```

## 相关文件

- `resource_manager.py` - 主要修改文件
- `test_search_drama.py` - 测试脚本
- `classify_drama_type.py` - 自动分类脚本
- `model/cloud_resource.py` - 数据模型（包含 category2 字段）

## 注意事项

1. **类型值限制**：`category` 参数仅接受 `"电影"` 或 `"剧集"` 两个值
2. **TMDB API 限制**：仍然受 TMDB API 的速率限制约束
3. **回退机制**：即使指定了类型，如果未找到仍会尝试另一种类型
4. **数据质量**：分类准确性依赖于豆包AI的判断，建议定期检查和修正

## 更新日期

2025-11-04

## 作者

Claude Code + User Collaboration
