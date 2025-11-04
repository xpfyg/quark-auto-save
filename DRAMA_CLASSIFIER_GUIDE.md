# DramaClassifier 工具类使用指南

## 简介

`DramaClassifier` 是一个封装好的影视作品分类工具类，使用豆包AI自动识别作品是"电影"还是"剧集"。它提供了简洁的 API，方便在业务代码中集成使用。

## 特性

- ✅ **简单易用**：一行代码即可完成分类
- ✅ **批量处理**：支持批量分类多个作品
- ✅ **自动重试**：内置失败重试机制
- ✅ **置信度评估**：可获取分类的置信度
- ✅ **统计功能**：自动记录分类统计信息
- ✅ **单例模式**：支持全局单例，避免重复初始化
- ✅ **灵活配置**：支持自定义参数和环境变量

## 安装依赖

确保已安装以下依赖：

```bash
pip install python-dotenv
```

## 配置

### 方式1：环境变量

在 `.env` 文件中配置：

```bash
ARK_API_KEY=your_ark_api_key
ARK_MODEL_ID=your_model_endpoint_id
```

### 方式2：代码中传入

```python
classifier = DramaClassifier(
    api_key="your_api_key",
    model_id="your_model_id"
)
```

## 快速开始

### 方式1：使用类实例

```python
from drama_classifier import DramaClassifier

# 创建分类器（从环境变量读取配置）
classifier = DramaClassifier()

# 分类单个作品
result = classifier.classify("肖申克的救赎")
print(result)  # 输出: 电影

result = classifier.classify("权力的游戏")
print(result)  # 输出: 剧集
```

### 方式2：使用便捷函数

```python
from drama_classifier import classify_drama

# 直接分类
result = classify_drama("盗梦空间")
print(result)  # 输出: 电影
```

## 详细用法

### 1. 基本分类

```python
from drama_classifier import DramaClassifier

classifier = DramaClassifier()

# 分类单个作品
category = classifier.classify("流浪地球")
if category:
    print(f"分类结果: {category}")  # 电影
else:
    print("分类失败")
```

### 2. 批量分类

```python
# 准备作品列表
dramas = ["盗梦空间", "绝命毒师", "星际穿越", "黑镜"]

# 批量分类
results = classifier.classify_batch(dramas, show_progress=True)

# 处理结果
for drama_name, category in results:
    print(f"{drama_name}: {category}")
```

### 3. 带重试机制

```python
# 分类时自动重试（失败后重试2次）
result = classifier.classify("沙丘", retry=2)
```

### 4. 获取置信度

```python
# 获取分类及置信度（内部会查询3次取一致结果）
category, confidence = classifier.classify_with_confidence("哈利波特")
print(f"分类: {category}, 置信度: {confidence:.2%}")
```

### 5. 查看统计信息

```python
# 进行一些分类操作
classifier.classify("蜘蛛侠")
classifier.classify("生活大爆炸")

# 获取统计信息（编程方式）
stats = classifier.get_statistics()
print(f"总计: {stats['total']}")
print(f"成功: {stats['success']}")
print(f"电影: {stats['movie']}")
print(f"剧集: {stats['drama']}")

# 或者直接打印
classifier.print_statistics()

# 重置统计
classifier.reset_statistics()
```

### 6. 自定义参数

```python
# 创建自定义配置的分类器
classifier = DramaClassifier(
    api_key="your_api_key",
    model_id="your_model_id",
    temperature=0.1,      # 更低的温度，更稳定
    sleep_interval=0.5    # 请求间隔0.5秒
)
```

### 7. 使用全局单例

```python
from drama_classifier import get_classifier

# 获取全局单例（首次调用会创建实例）
classifier = get_classifier()

# 之后的调用会返回同一个实例
classifier2 = get_classifier()
assert classifier is classifier2  # True

# 强制创建新实例
new_classifier = get_classifier(force_new=True)
```

## 业务集成示例

### 示例1：在资源处理中使用

```python
from drama_classifier import get_classifier

def process_resource(drama_name, share_link):
    """处理资源"""
    # 获取分类器
    classifier = get_classifier()

    # 分类
    category = classifier.classify(drama_name)

    if not category:
        print(f"分类失败，跳过: {drama_name}")
        return None

    # 根据分类决定保存路径
    savepath = "/Movies" if category == "电影" else "/TVShows"

    # 返回处理结果
    return {
        "name": drama_name,
        "category": category,
        "savepath": savepath,
        "link": share_link
    }

# 使用
result = process_resource("泰坦尼克号", "https://pan.quark.cn/s/xxx")
```

### 示例2：批量更新数据库

```python
from drama_classifier import DramaClassifier
from db import db_session
from model.cloud_resource import CloudResource

def update_all_categories():
    """更新所有未分类的资源"""
    classifier = DramaClassifier()

    # 查询未分类的资源
    resources = db_session.query(CloudResource).filter(
        CloudResource.category2 == None
    ).all()

    for resource in resources:
        # 分类
        category = classifier.classify(resource.drama_name)

        if category:
            # 更新数据库
            resource.category2 = category
            db_session.commit()
            print(f"✓ {resource.drama_name}: {category}")
        else:
            print(f"✗ {resource.drama_name}: 分类失败")

    # 显示统计
    classifier.print_statistics()

# 运行
update_all_categories()
```

### 示例3：与 ResourceManager 集成

```python
from resource_manager import ResourceManager
from drama_classifier import get_classifier

class EnhancedResourceManager(ResourceManager):
    """增强的资源管理器，集成自动分类功能"""

    def __init__(self, cookie, drive_type="quark"):
        super().__init__(cookie, drive_type)
        self.classifier = get_classifier()

    def process_resource(self, drama_name, share_link, savepath=None):
        """处理资源，自动分类并优化路径"""
        # 自动分类
        category = self.classifier.classify(drama_name)

        if not category:
            print(f"⚠️ 无法分类，使用默认值")
            category = "电影"

        # 自动决定保存路径
        if not savepath:
            savepath = "/Movies" if category == "电影" else "/TVShows"

        print(f"✓ 分类为 {category}，保存到 {savepath}")

        # 调用父类方法，传入 category 参数优化 TMDB 查询
        return super().process_resource(
            drama_name=drama_name,
            share_link=share_link,
            savepath=savepath,
            category=category
        )

# 使用
manager = EnhancedResourceManager(cookie)
result = manager.process_resource("教父", "https://pan.quark.cn/s/xxx")
```

## API 参考

### DramaClassifier 类

#### 初始化

```python
DramaClassifier(
    api_key: Optional[str] = None,
    model_id: Optional[str] = None,
    temperature: float = 0.3,
    sleep_interval: float = 1.0
)
```

**参数说明**：
- `api_key`: 豆包AI API Key，默认从环境变量 `ARK_API_KEY` 读取
- `model_id`: 豆包AI模型ID，默认从环境变量 `ARK_MODEL_ID` 读取
- `temperature`: 温度参数(0-1)，越低越稳定，默认0.3
- `sleep_interval`: 批量处理时的请求间隔（秒），默认1秒

#### 方法

##### classify()

分类单个作品

```python
classify(drama_name: str, retry: int = 1) -> Optional[str]
```

**返回**: `"电影"` 或 `"剧集"`，失败返回 `None`

##### classify_batch()

批量分类作品

```python
classify_batch(
    drama_names: List[str],
    show_progress: bool = True
) -> List[Tuple[str, Optional[str]]]
```

**返回**: 列表，每个元素为 `(作品名, 分类结果)`

##### classify_with_confidence()

分类并返回置信度

```python
classify_with_confidence(drama_name: str) -> Tuple[Optional[str], float]
```

**返回**: `(分类结果, 置信度)`，置信度范围0-1

##### get_statistics()

获取统计信息

```python
get_statistics() -> Dict[str, int]
```

**返回**: 包含统计数据的字典

##### print_statistics()

打印统计信息到控制台

```python
print_statistics() -> None
```

##### reset_statistics()

重置统计信息

```python
reset_statistics() -> None
```

### 便捷函数

#### classify_drama()

分类单个作品（便捷函数）

```python
classify_drama(drama_name: str, **kwargs) -> Optional[str]
```

#### classify_dramas()

批量分类作品（便捷函数）

```python
classify_dramas(drama_names: List[str], **kwargs) -> List[Tuple[str, Optional[str]]]
```

#### get_classifier()

获取全局单例分类器

```python
get_classifier(
    api_key: Optional[str] = None,
    model_id: Optional[str] = None,
    force_new: bool = False
) -> DramaClassifier
```

## 完整示例

运行示例脚本：

```bash
# 设置环境变量
export ARK_API_KEY='your-api-key'
export ARK_MODEL_ID='your-model-id'

# 运行示例
python3 example_drama_classifier.py
```

或者使用 `.env` 文件：

```bash
# .env 文件内容
ARK_API_KEY=your-api-key
ARK_MODEL_ID=your-model-id

# 运行示例
python3 example_drama_classifier.py
```

## 与原脚本的关系

### classify_drama_type.py

原有的命令行脚本仍然可用，现在它内部使用 `DramaClassifier` 类：

```bash
# 查看统计
python3 classify_drama_type.py --stats

# 更新所有未分类记录
python3 classify_drama_type.py

# 测试10条
python3 classify_drama_type.py --limit 10
```

### 向后兼容

所有原有功能保持不变，只是底层实现使用了新的工具类。

## 最佳实践

### 1. 使用单例模式

在整个应用中使用全局单例，避免重复初始化：

```python
from drama_classifier import get_classifier

# 在应用启动时初始化
classifier = get_classifier()

# 在各个模块中使用
def my_function():
    classifier = get_classifier()  # 返回同一个实例
    return classifier.classify("some drama")
```

### 2. 错误处理

```python
try:
    classifier = DramaClassifier()
except ValueError as e:
    print(f"初始化失败: {e}")
    # 检查环境变量配置
    sys.exit(1)

result = classifier.classify("drama name")
if result:
    # 处理成功的分类
    process(result)
else:
    # 处理失败的情况
    handle_failure()
```

### 3. 性能优化

```python
# 批量处理时使用 classify_batch 而不是循环调用 classify
dramas = ["drama1", "drama2", "drama3", ...]

# 好的做法
results = classifier.classify_batch(dramas)

# 避免这样（效率低）
results = [classifier.classify(d) for d in dramas]
```

### 4. 配置管理

```python
# 开发环境
dev_classifier = DramaClassifier(
    temperature=0.5,  # 更高的温度，更多样化
    sleep_interval=0.5
)

# 生产环境
prod_classifier = DramaClassifier(
    temperature=0.1,  # 更低的温度，更稳定
    sleep_interval=1.0
)
```

## 故障排查

### 问题1：初始化失败

**错误信息**：`ValueError: ARK_API_KEY 未设置`

**解决方法**：
```bash
export ARK_API_KEY='your-api-key'
export ARK_MODEL_ID='your-model-id'
```

### 问题2：分类总是返回 None

**可能原因**：
- API Key 无效
- 网络连接问题
- API 额度不足

**解决方法**：
- 检查 API Key 是否正确
- 检查网络连接
- 查看豆包AI控制台的额度

### 问题3：分类不准确

**优化方法**：
```python
# 降低 temperature 提高稳定性
classifier = DramaClassifier(temperature=0.1)

# 使用置信度评估
category, confidence = classifier.classify_with_confidence("drama")
if confidence < 0.7:
    # 置信度低，可能需要人工确认
    manual_review(drama)
```

## 相关文件

- `drama_classifier.py` - 工具类主文件
- `classify_drama_type.py` - 命令行脚本（使用工具类）
- `example_drama_classifier.py` - 使用示例
- `DRAMA_CLASSIFIER_GUIDE.md` - 本文档
- `.env.example` - 环境变量配置模板

## 更新日志

### v1.0.0 (2025-11-04)

- ✨ 首次发布
- ✅ 封装 DramaClassifier 工具类
- ✅ 支持单例模式
- ✅ 提供便捷函数
- ✅ 支持批量处理
- ✅ 支持置信度评估
- ✅ 内置统计功能
- ✅ 完善的错误处理

## 许可证

与项目保持一致

## 联系方式

如有问题，请提交 Issue 或联系项目维护者。
