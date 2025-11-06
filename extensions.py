# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask 扩展模块
存放共享的扩展实例，避免循环导入
"""
from flask_apscheduler import APScheduler

# Flask-APScheduler 实例
scheduler = APScheduler()
