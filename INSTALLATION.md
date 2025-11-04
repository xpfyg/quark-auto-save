# 安装依赖指南

## 快速安装

### 方法1: 使用 pip（推荐）

```bash
# 安装所有依赖
pip install -r requirements.txt

# 或使用 pip3
pip3 install -r requirements.txt
```

### 方法2: 使用虚拟环境（推荐用于开发）

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 方法3: 单独安装（如果requirements.txt不可用）

```bash
# 核心依赖
pip install flask==3.0.0
pip install apscheduler==3.10.4
pip install requests==2.31.0
pip install treelib==1.7.0

# 数据库依赖（新增功能需要）
pip install sqlalchemy==2.0.23
pip install pymysql==1.1.0
pip install flask-sqlalchemy==3.1.1
```

## 验证安装

### 检查已安装的包

```bash
pip list | grep -E "flask|sqlalchemy|pymysql|requests|treelib|apscheduler"
```

应该看到：
```
apscheduler       3.10.4
Flask             3.0.0
Flask-SQLAlchemy  3.1.1
PyMySQL           1.1.0
requests          2.31.0
SQLAlchemy        2.0.23
treelib           1.7.0
```

### 测试导入

```bash
python3 -c "from sqlalchemy import create_engine; print('SQLAlchemy OK')"
python3 -c "import pymysql; print('PyMySQL OK')"
python3 -c "from flask_sqlalchemy import SQLAlchemy; print('Flask-SQLAlchemy OK')"
```

## 解决 IDE 警告

### PyCharm

如果PyCharm显示"Cannot find reference 'create_engine'"警告：

1. **配置Python解释器**
   - File → Settings → Project → Python Interpreter
   - 确保选择了正确的Python解释器
   - 点击"+"按钮，搜索并安装 `sqlalchemy`

2. **刷新缓存**
   - File → Invalidate Caches / Restart
   - 选择 "Invalidate and Restart"

3. **标记源代码目录**
   - 右键点击项目根目录
   - Mark Directory as → Sources Root

### VS Code

1. **选择Python解释器**
   - Ctrl+Shift+P (Cmd+Shift+P on Mac)
   - 输入 "Python: Select Interpreter"
   - 选择安装了依赖的Python环境

2. **安装Python扩展**
   - 确保安装了官方的Python扩展
   - 重新加载窗口

## 常见问题

### 问题1: pip install 失败

```bash
# 升级pip
pip install --upgrade pip

# 使用国内镜像（如果网络慢）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题2: 权限错误

```bash
# 使用 --user 参数
pip install --user -r requirements.txt

# 或使用sudo (不推荐)
sudo pip install -r requirements.txt
```

### 问题3: MySQL驱动问题

如果PyMySQL无法工作，可以尝试：

```bash
# 安装额外的MySQL驱动
pip install mysqlclient

# 或者使用cryptography支持
pip install cryptography
```

### 问题4: 版本冲突

```bash
# 创建全新的虚拟环境
python3 -m venv fresh_venv
source fresh_venv/bin/activate
pip install -r requirements.txt
```

## Docker环境

如果使用Docker部署，依赖会自动安装：

```bash
# 构建镜像（会自动安装requirements.txt中的依赖）
docker build -t quark-auto-save .

# 运行容器
docker run -d \
  --name quark-auto-save \
  -p 5005:5005 \
  -v ./config:/app/config \
  quark-auto-save
```

## 依赖说明

| 包名 | 版本 | 用途 |
|------|------|------|
| flask | 3.0.0 | Web框架（WebUI） |
| apscheduler | 3.10.4 | 定时任务调度 |
| requests | 2.31.0 | HTTP客户端（调用Quark API） |
| treelib | 1.7.0 | 树形结构展示 |
| **sqlalchemy** | **2.0.23** | **ORM数据库操作（新增）** |
| **pymysql** | **1.1.0** | **MySQL数据库驱动（新增）** |
| **flask-sqlalchemy** | **3.1.1** | **Flask数据库集成（新增）** |

## 可选依赖

### python-dotenv（推荐）

用于自动加载 `.env` 文件：

```bash
pip install python-dotenv
```

然后在代码中添加：

```python
from dotenv import load_dotenv
load_dotenv()  # 自动加载.env文件
```

### 其他推荐工具

```bash
# 代码格式化
pip install black

# 类型检查
pip install mypy

# 测试框架
pip install pytest
```

## 下一步

安装完依赖后：

1. ✅ 配置环境变量（复制 `.env.example` 到 `.env`）
2. ✅ 初始化数据库（运行 `init_database.sql`）
3. ✅ 测试数据库连接（运行 `python3 test_db.py`）
4. ✅ 开始使用资源管理器

## 升级依赖

定期更新依赖以获取安全补丁：

```bash
# 查看可更新的包
pip list --outdated

# 更新特定包
pip install --upgrade sqlalchemy

# 更新所有包（谨慎使用）
pip install --upgrade -r requirements.txt
```
