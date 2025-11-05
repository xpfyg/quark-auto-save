# !/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy import create_engine
from sqlalchemy.exc import DisconnectionError
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool

app = Flask(__name__)

db = SQLAlchemy()
load_dotenv()
# 从环境变量读取数据库配置
DB_USERNAME = os.environ.get('DB_USERNAME', '')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
DB_HOST = os.environ.get('DB_HOST', '')
DB_PORT = os.environ.get('DB_PORT', '3306')
DB_DATABASE = os.environ.get('DB_DATABASE', 'pan_library')

# 构建数据库连接URL
DATABASE_URL = f'mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}'

# 创建连接引擎，添加连接池配置
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,  # 连接池大小
    pool_recycle=3600,  # 连接回收时间（秒）
    pool_pre_ping=True,  # 每次从连接池获取连接时测试连接是否有效
    echo=False,  # 是否打印SQL语句
    connect_args={
        'charset': 'utf8mb4',
        'connect_timeout': 10
    }
)

# 创建线程安全的Session
# 使用 scoped_session 作为代理，每个线程自动获取独立的 session
Session = scoped_session(sessionmaker(bind=engine, autocommit=False, autoflush=False))
db_session = Session  # 直接使用 scoped_session，而不是调用它


def init_db():
    """初始化数据库连接"""
    try:
        # 测试数据库连接
        engine.connect()
        print("✅ 数据库连接成功")
        return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {str(e)}")
        return False


def close_db():
    """关闭数据库连接"""
    try:
        db_session.close()
        engine.dispose()
        print("✅ 数据库连接已关闭")
    except Exception as e:
        print(f"❌ 关闭数据库连接失败: {str(e)}")

