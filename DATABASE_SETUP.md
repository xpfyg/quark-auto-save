# 数据库配置修复说明

## 已完成的改进

### 1. ✅ 修复 db.py 文件

**改进内容：**
- 移除硬编码的数据库凭证
- 改用环境变量配置（支持 .env 文件）
- 添加连接池配置（QueuePool）
- 添加线程安全的 Session（scoped_session）
- 添加连接健康检查（pool_pre_ping）
- 添加字符集配置（utf8mb4）
- 提供 `init_db()` 和 `close_db()` 工具函数

**主要配置：**
```python
# 连接池配置
pool_size=5          # 连接池大小
pool_recycle=3600    # 连接回收时间（1小时）
pool_pre_ping=True   # 连接前测试
charset='utf8mb4'    # 支持中文和emoji
```

### 2. ✅ 创建环境变量配置文件

**新增文件：**
- `.env.example` - 环境变量配置模板

**支持的环境变量：**
```bash
DB_USERNAME      # 数据库用户名
DB_PASSWORD      # 数据库密码
DB_HOST          # 数据库主机
DB_PORT          # 数据库端口
DB_DATABASE      # 数据库名称
QUARK_COOKIE     # 夸克网盘Cookie
TMDB_API_KEY     # TMDB API密钥（可选）
```

### 3. ✅ 更新 .gitignore

**新增忽略规则：**
- `.env` 和 `.env.local` - 防止敏感信息泄露
- Python 相关文件（.pyc, .pyo, __pycache__ 等）
- IDE 配置文件（.vscode, .idea）
- 数据库文件（.db, .sqlite）
- 日志文件（.log）
- macOS 系统文件（.DS_Store）

### 4. ✅ 创建数据库初始化脚本

**新增文件：**
- `init_database.sql` - MySQL 数据库和表创建脚本

**包含内容：**
- 创建 `pan_library` 数据库
- 创建 `cloud_resource` 表（包含索引和约束）
- 创建 `tmdb` 表（包含索引和约束）
- 表结构查看和验证

**使用方法：**
```bash
mysql -u root -p < init_database.sql
```

### 5. ✅ 创建数据库连接测试脚本

**新增文件：**
- `test_db.py` - 数据库连接和模型测试工具

**功能：**
- 显示当前数据库配置
- 测试数据库连接
- 检查必需的表是否存在
- 测试数据库模型（CloudResource 和 Tmdb）
- 显示现有数据示例

**使用方法：**
```bash
python3 test_db.py
```

### 6. ✅ 更新文档

**更新的文件：**
- `RESOURCE_MANAGER_README.md` - 添加数据库配置说明

**新增内容：**
- 数据库初始化步骤
- 环境变量配置方法（.env 和 export）
- 数据库连接测试说明

## 使用流程

### 步骤1: 创建数据库

```bash
# 执行 SQL 脚本创建数据库和表
mysql -u root -p < init_database.sql
```

### 步骤2: 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置文件
vim .env

# 填入真实的数据库配置
DB_USERNAME=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306
DB_DATABASE=pan_library
```

### 步骤3: 测试数据库连接

```bash
# 测试连接是否正常
python3 test_db.py

# 应该看到：
# ✅ 数据库连接成功
# 📋 数据库中的表 (2 个)
# ✅ 所有必需的表都存在
```

### 步骤4: 使用资源管理器

```python
from resource_manager import ResourceManager

# 创建管理器
manager = ResourceManager(cookie="your_quark_cookie")

# 处理资源
result = manager.process_resource(
    drama_name="权力的游戏",
    share_link="https://pan.quark.cn/s/xxxxx",
    savepath="/电视剧/权力的游戏"
)
```

## 安全改进

### 之前的问题：
❌ 数据库凭证硬编码在代码中
❌ 敏感信息可能被提交到 Git
❌ 无法灵活切换不同环境的配置

### 现在的方案：
✅ 使用环境变量管理敏感信息
✅ .gitignore 防止 .env 文件被提交
✅ 提供 .env.example 作为配置模板
✅ 支持不同环境使用不同配置

## 性能优化

### 连接池管理：
- 使用 QueuePool 管理数据库连接
- 最多保持 5 个活跃连接
- 连接超过 1 小时自动回收
- 连接前自动测试有效性

### 线程安全：
- 使用 scoped_session 确保线程安全
- 支持多线程并发访问

## 故障排查

### 如果连接失败，请检查：

1. **数据库服务是否启动**
   ```bash
   # MySQL
   systemctl status mysql
   # 或
   brew services list | grep mysql
   ```

2. **环境变量是否正确设置**
   ```bash
   python3 test_db.py  # 会显示当前配置
   ```

3. **数据库是否存在**
   ```bash
   mysql -u root -p -e "SHOW DATABASES;"
   ```

4. **用户权限是否足够**
   ```bash
   mysql -u root -p -e "SHOW GRANTS FOR 'your_username'@'%';"
   ```

5. **防火墙是否允许连接**
   ```bash
   # 检查端口
   telnet localhost 3306
   ```

## 文件清单

```
quark-auto-save/
├── db.py                          # ✅ 已修复的数据库连接
├── .env.example                   # ✅ 新增：环境变量模板
├── .gitignore                     # ✅ 已更新：添加敏感文件忽略规则
├── init_database.sql              # ✅ 新增：数据库初始化脚本
├── test_db.py                     # ✅ 新增：数据库测试工具
├── resource_manager.py            # 资源管理器
├── RESOURCE_MANAGER_README.md     # ✅ 已更新：添加数据库配置说明
└── model/
    ├── cloud_resource.py          # CloudResource 模型
    └── tmdb.py                    # Tmdb 模型
```

## 下一步建议

1. **创建 .env 文件并配置真实凭证**
2. **运行 test_db.py 验证连接**
3. **开始使用 resource_manager.py**
4. **定期备份数据库**
5. **监控连接池状态**

## 注意事项

⚠️ **重要：**
- 永远不要将 `.env` 文件提交到 Git
- 定期更换数据库密码
- 使用强密码
- 限制数据库用户权限
- 启用数据库访问日志
- 定期备份数据

🔒 **安全：**
- .env 文件已被 .gitignore 忽略
- 仅 .env.example 会被提交（不含真实凭证）
- 建议使用专用数据库用户（非 root）
- 建议启用 SSL 连接（生产环境）
