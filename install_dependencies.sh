#!/bin/bash
# 快速安装依赖脚本

set -e  # 遇到错误时退出

echo "======================================"
echo "夸克自动转存 - 依赖安装脚本"
echo "======================================"
echo ""

# 检查Python版本
echo "🔍 检查Python版本..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
    PIP_CMD=pip3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
    PIP_CMD=pip
else
    echo "❌ 错误: 未找到Python，请先安装Python 3.x"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
echo "✅ 找到Python: $PYTHON_VERSION"
echo ""

# 升级pip
echo "📦 升级pip..."
$PIP_CMD install --upgrade pip --quiet
echo "✅ pip已升级到最新版本"
echo ""

# 安装依赖
echo "📥 安装依赖包..."
echo ""

if [ -f "requirements.txt" ]; then
    echo "从 requirements.txt 安装依赖..."
    $PIP_CMD install -r requirements.txt
    echo ""
    echo "✅ 所有依赖安装完成！"
else
    echo "⚠️  未找到 requirements.txt，手动安装依赖..."
    $PIP_CMD install flask==3.0.0
    $PIP_CMD install apscheduler==3.10.4
    $PIP_CMD install requests==2.31.0
    $PIP_CMD install treelib==1.7.0
    $PIP_CMD install sqlalchemy==2.0.23
    $PIP_CMD install pymysql==1.1.0
    $PIP_CMD install flask-sqlalchemy==3.1.1
    echo "✅ 所有依赖安装完成！"
fi

echo ""
echo "======================================"
echo "验证安装"
echo "======================================"
echo ""

# 验证安装
echo "🔍 验证SQLAlchemy..."
$PYTHON_CMD -c "from sqlalchemy import create_engine; print('  ✅ SQLAlchemy 正常')" 2>&1

echo "🔍 验证PyMySQL..."
$PYTHON_CMD -c "import pymysql; print('  ✅ PyMySQL 正常')" 2>&1

echo "🔍 验证Flask-SQLAlchemy..."
$PYTHON_CMD -c "from flask_sqlalchemy import SQLAlchemy; print('  ✅ Flask-SQLAlchemy 正常')" 2>&1

echo "🔍 验证其他依赖..."
$PYTHON_CMD -c "import flask, requests, treelib, apscheduler; print('  ✅ 其他依赖正常')" 2>&1

echo ""
echo "======================================"
echo "已安装的包"
echo "======================================"
echo ""
$PIP_CMD list | grep -E "Flask|SQLAlchemy|PyMySQL|requests|treelib|APScheduler" || true

echo ""
echo "======================================"
echo "✅ 安装完成！"
echo "======================================"
echo ""
echo "下一步："
echo "1. 配置环境变量: cp .env.example .env && vim .env"
echo "2. 初始化数据库: mysql -u root -p < init_database.sql"
echo "3. 测试数据库连接: python3 test_db.py"
echo "4. 运行程序: python3 resource_manager.py"
echo ""
