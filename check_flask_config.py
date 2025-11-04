#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证 Flask 应用目录配置
"""
import os
import sys

# 添加 app 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

print("=" * 60)
print("Flask 应用目录配置验证")
print("=" * 60)

# 导入 Flask 应用
try:
    from run import app, PUBLIC_DIR
    print("\n✅ Flask 应用导入成功")
except Exception as e:
    print(f"\n❌ Flask 应用导入失败: {e}")
    sys.exit(1)

# 检查目录配置
print("\n1️⃣  检查目录配置")
print("-" * 60)

print(f"项目根目录: {os.path.dirname(__file__)}")
print(f"PUBLIC_DIR: {PUBLIC_DIR}")
print(f"Static Folder: {app.static_folder}")
print(f"Template Folder: {app.template_folder}")

# 检查目录是否存在
print("\n2️⃣  检查目录是否存在")
print("-" * 60)

dirs_to_check = [
    ("PUBLIC_DIR", PUBLIC_DIR),
    ("Static Folder", app.static_folder),
    ("Template Folder", app.template_folder),
]

all_ok = True
for name, path in dirs_to_check:
    if os.path.exists(path):
        print(f"✅ {name}: {path}")
    else:
        print(f"❌ {name}: {path} (不存在)")
        all_ok = False

# 检查关键文件
print("\n3️⃣  检查关键文件")
print("-" * 60)

files_to_check = [
    ("favicon.ico", os.path.join(app.static_folder, "favicon.ico")),
    ("bootstrap.min.css", os.path.join(app.static_folder, "css", "bootstrap.min.css")),
    ("vue@2.js", os.path.join(app.static_folder, "js", "vue@2.js")),
    ("index.html", os.path.join(app.template_folder, "index.html")),
    ("login.html", os.path.join(app.template_folder, "login.html")),
    ("resources.html", os.path.join(app.template_folder, "resources.html")),
]

for name, path in files_to_check:
    if os.path.exists(path):
        size = os.path.getsize(path)
        print(f"✅ {name}: {size:,} bytes")
    else:
        print(f"❌ {name}: 不存在")
        all_ok = False

# 检查静态文件 URL
print("\n4️⃣  检查静态文件 URL 映射")
print("-" * 60)

with app.app_context():
    try:
        from flask import url_for

        # 测试静态文件 URL
        css_url = url_for('static', filename='css/bootstrap.min.css')
        js_url = url_for('static', filename='js/vue@2.js')

        print(f"✅ CSS URL: {css_url}")
        print(f"✅ JS URL: {js_url}")
    except Exception as e:
        print(f"❌ URL 映射失败: {e}")
        all_ok = False

# 总结
print("\n" + "=" * 60)
if all_ok:
    print("✅ 所有检查通过！Flask 应用配置正确")
    print("\n可以启动应用:")
    print("  cd app && python3 run.py")
    print("  或")
    print("  python3 app/run.py")
else:
    print("❌ 部分检查未通过，请修复上述问题")
    sys.exit(1)

print("=" * 60)
