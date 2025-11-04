# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from flask import (
    Flask,
    url_for,
    session,
    jsonify,
    request,
    redirect,
    Response,
    render_template,
    send_from_directory,
    stream_with_context,
)
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import subprocess
import hashlib
import logging
import json
import os
import sys
import asyncio

# 添加当前目录到系统路径，以便导入模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import db_session
from model.cloud_resource import CloudResource
from model.tmdb import Tmdb
from resource_manager import ResourceManager


def get_app_ver():
    BUILD_SHA = os.environ.get("BUILD_SHA", "")
    BUILD_TAG = os.environ.get("BUILD_TAG", "")
    if BUILD_TAG[:1] == "v":
        return BUILD_TAG
    elif BUILD_SHA:
        return f"{BUILD_TAG}({BUILD_SHA[:7]})"
    else:
        return "dev"


# 文件路径
PYTHON_PATH = "python3" if os.path.exists("/usr/bin/python3") else "python"
SCRIPT_PATH = os.environ.get("SCRIPT_PATH", "./quark_auto_save.py")
CONFIG_PATH = os.environ.get("CONFIG_PATH", "./quark_config.json")
DEBUG = os.environ.get("DEBUG", False)

# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, "public")

# 创建 Flask 应用，指定 public 目录
app = Flask(__name__,
            static_folder=os.path.join(PUBLIC_DIR, "static"),
            template_folder=os.path.join(PUBLIC_DIR, "templates"))
app.config["APP_VERSION"] = get_app_ver()
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "quark_auto_save_secret_key")
app.json.ensure_ascii = False
app.json.sort_keys = False
app.jinja_env.variable_start_string = "[["
app.jinja_env.variable_end_string = "]]"

# 在每个请求结束后清理数据库 session
@app.teardown_appcontext
def shutdown_session(exception=None):
    if exception:
        db_session.rollback()
    db_session.remove()

scheduler = BackgroundScheduler()
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="[%(asctime)s][%(levelname)s] %(message)s",
    datefmt="%m-%d %H:%M:%S",
)
# 过滤werkzeug日志输出
if not DEBUG:
    logging.getLogger("werkzeug").setLevel(logging.ERROR)


def gen_md5(string):
    md5 = hashlib.md5()
    md5.update(string.encode("utf-8"))
    return md5.hexdigest()


# 读取 JSON 文件内容
def read_json():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


# 将数据写入 JSON 文件
def write_json(data):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False, sort_keys=False)


def is_login():
    data = read_json()
    username = data["webui"]["username"]
    password = data["webui"]["password"]
    if session.get("login") == gen_md5(username + password):
        return True
    else:
        return False


# 设置icon
@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        app.static_folder,
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


# 登录页面
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data = read_json()
        username = data["webui"]["username"]
        password = data["webui"]["password"]
        # 验证用户名和密码
        if (username == request.form.get("username")) and (
            password == request.form.get("password")
        ):
            logging.info(f">>> 用户 {username} 登录成功")
            session["login"] = gen_md5(username + password)
            return redirect(url_for("index"))
        else:
            logging.info(f">>> 用户 {username} 登录失败")
            return render_template("login.html", message="登录失败")

    return render_template("login.html", error=None)


# 退出登录
@app.route("/logout")
def logout():
    session.pop("login", None)
    return redirect(url_for("login"))


# 管理页面
@app.route("/")
def index():
    if not is_login():
        return redirect(url_for("login"))
    return render_template("index.html", version=app.config["APP_VERSION"])


# 获取配置数据
@app.route("/data")
def get_data():
    if not is_login():
        return redirect(url_for("login"))
    data = read_json()
    del data["webui"]
    return jsonify(data)


# 更新数据
@app.route("/update", methods=["POST"])
def update():
    if not is_login():
        return "未登录"
    data = read_json()
    webui = data["webui"]
    data = request.json
    data["webui"] = webui
    write_json(data)
    # 重新加载任务
    if reload_tasks():
        logging.info(f">>> 配置更新成功")
        return "配置更新成功"
    else:
        logging.info(f">>> 配置更新失败")
        return "配置更新失败"


# 处理运行脚本请求
@app.route("/run_script_now", methods=["GET"])
def run_script_now():
    if not is_login():
        return "未登录"
    task_index = request.args.get("task_index", "")
    command = [PYTHON_PATH, "-u", SCRIPT_PATH, CONFIG_PATH, task_index]
    logging.info(
        f">>> 手动运行任务{int(task_index)+1 if task_index.isdigit() else 'all'}"
    )

    def generate_output():
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
        )
        try:
            for line in iter(process.stdout.readline, ""):
                logging.info(line.strip())
                yield f"data: {line}\n\n"
            yield "data: [DONE]\n\n"
        finally:
            process.stdout.close()
            process.wait()

    return Response(
        stream_with_context(generate_output()),
        content_type="text/event-stream;charset=utf-8",
    )


# 定时任务执行的函数
def run_python(args):
    logging.info(f">>> 定时运行任务")
    os.system(f"{PYTHON_PATH} {args}")


# 重新加载任务
def reload_tasks():
    # 读取数据
    data = read_json()
    # 添加新任务
    crontab = data.get("crontab")
    if crontab:
        if scheduler.state == 1:
            scheduler.pause()  # 暂停调度器
        trigger = CronTrigger.from_crontab(crontab)
        scheduler.remove_all_jobs()
        scheduler.add_job(
            run_python,
            trigger=trigger,
            args=[f"{SCRIPT_PATH} {CONFIG_PATH}"],
            id=SCRIPT_PATH,
        )
        if scheduler.state == 0:
            scheduler.start()
        elif scheduler.state == 2:
            scheduler.resume()
        scheduler_state_map = {0: "停止", 1: "运行", 2: "暂停"}
        logging.info(">>> 重载调度器")
        logging.info(f"调度状态: {scheduler_state_map[scheduler.state]}")
        logging.info(f"定时规则: {crontab}")
        logging.info(f"现有任务: {scheduler.get_jobs()}")
        return True
    else:
        logging.info(">>> no crontab")
        return False


def init():
    logging.info(f">>> 初始化配置")
    # 检查配置文件是否存在
    if not os.path.exists(CONFIG_PATH):
        if not os.path.exists(os.path.dirname(CONFIG_PATH)):
            os.makedirs(os.path.dirname(CONFIG_PATH))
        with open("quark_config.json", "rb") as src, open(CONFIG_PATH, "wb") as dest:
            dest.write(src.read())
    data = read_json()
    # 默认管理账号
    if not data.get("webui"):
        data["webui"] = {
            "username": "admin",
            "password": "admin123",
        }
    elif os.environ.get("WEBUI_USERNAME") and os.environ.get("WEBUI_PASSWORD"):
        data["webui"] = {
            "username": os.environ.get("WEBUI_USERNAME"),
            "password": os.environ.get("WEBUI_PASSWORD"),
        }
    # 默认定时规则
    if not data.get("crontab"):
        data["crontab"] = "0 8,18,20 * * *"
    write_json(data)


# 资源管理页面
@app.route("/resources")
def resources():
    if not is_login():
        return redirect(url_for("login"))
    return render_template("resources.html", version=app.config["APP_VERSION"])


# 获取资源列表
@app.route("/api/resources")
def get_resources():
    if not is_login():
        return jsonify({"error": "未登录"}), 401

    try:
        # 获取查询参数
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        sort_by = request.args.get("sort_by", "update_time")
        order = request.args.get("order", "desc")
        is_expired = request.args.get("is_expired", "0")
        search = request.args.get("search", "")

        # 构建查询
        query = db_session.query(CloudResource, Tmdb).outerjoin(
            Tmdb, CloudResource.tmdb_id == Tmdb.id
        )

        # 过滤条件
        if is_expired != "all":
            query = query.filter(CloudResource.is_expired == int(is_expired))

        if search:
            query = query.filter(
                (CloudResource.drama_name.like(f"%{search}%")) |
                (CloudResource.alias.like(f"%{search}%"))
            )

        # 排序
        sort_column = getattr(CloudResource, sort_by, CloudResource.update_time)
        if order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # 分页
        total = query.count()
        resources = query.limit(per_page).offset((page - 1) * per_page).all()

        # 格式化结果
        result = []
        for resource, tmdb in resources:
            item = resource.to_dict()
            item["tmdb"] = tmdb.to_dict() if tmdb else None
            result.append(item)

        return jsonify({
            "total": total,
            "page": page,
            "per_page": per_page,
            "data": result
        })
    except Exception as e:
        db_session.rollback()
        logging.error(f"查询资源失败: {str(e)}")
        return jsonify({"error": f"查询失败: {str(e)}"}), 500


# 一键投稿到Telegram
@app.route("/api/share_to_tg/<int:resource_id>", methods=["POST"])
def share_to_tg(resource_id):
    if not is_login():
        return jsonify({"error": "未登录"}), 401

    try:
        # 获取第一个cookie
        cookie = os.environ.get("QUARK_COOKIE", "")
        if not cookie:
            data = read_json()
            cookie = data.get("quark_cookie", "")
        if not cookie:
            return jsonify({"error": "未配置夸克Cookie"}), 400

        # 创建资源管理器
        manager = ResourceManager(cookie)

        # 执行分享（异步）
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(manager.shareToTgBot(resource_id))
            db_session.commit()  # 确保更新已提交
            return jsonify({"success": True, "message": "投稿成功"})
        finally:
            loop.close()

    except Exception as e:
        db_session.rollback()
        logging.error(f"投稿失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# 更新资源状态
@app.route("/api/resources/<int:resource_id>/status", methods=["PUT"])
def update_resource_status(resource_id):
    if not is_login():
        return jsonify({"error": "未登录"}), 401

    try:
        data = request.json
        is_expired = data.get("is_expired")

        resource = db_session.query(CloudResource).filter(
            CloudResource.id == resource_id
        ).first()

        if not resource:
            return jsonify({"error": "资源不存在"}), 404

        resource.is_expired = is_expired
        db_session.commit()

        return jsonify({"success": True, "message": "更新成功"})
    except Exception as e:
        db_session.rollback()
        logging.error(f"更新失败: {str(e)}")
        return jsonify({"error": str(e)}), 500


# 搜索TMDB
@app.route("/api/search_tmdb", methods=["GET"])
def search_tmdb():
    if not is_login():
        return jsonify({"error": "未登录"}), 401

    try:
        query = request.args.get("query", "").strip()
        if not query:
            return jsonify({"error": "请提供搜索关键词"}), 400

        # 导入TmdbService
        from resource_manager import TmdbService

        # 创建服务实例并搜索
        tmdb_service = TmdbService()
        results = tmdb_service.search_multi(query, max_results=10)

        return jsonify({
            "success": True,
            "query": query,
            "results": results
        })

    except Exception as e:
        logging.error(f"搜索TMDB失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# 匹配TMDB到资源
@app.route("/api/match_tmdb", methods=["POST"])
def match_tmdb():
    if not is_login():
        return jsonify({"error": "未登录"}), 401

    try:
        data = request.json
        resource_id = data.get("resource_id")
        tmdb_id = data.get("tmdb_id")
        media_type = data.get("media_type")
        title = data.get("title")
        year_released = data.get("year_released")
        poster_path = data.get("poster_path")
        overview = data.get("overview")
        vote_average = data.get("vote_average")
        category = data.get("category")

        # 验证必要参数
        if not all([resource_id, tmdb_id, media_type, title]):
            return jsonify({"error": "缺少必要参数"}), 400

        # 查找资源
        resource = db_session.query(CloudResource).filter(
            CloudResource.id == resource_id
        ).first()

        if not resource:
            return jsonify({"error": "资源不存在"}), 404

        # 构建海报URL
        poster_url = None
        if poster_path:
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"

        # 解析年份
        year = None
        if year_released:
            try:
                year = int(year_released)
            except (ValueError, TypeError):
                pass

        # 查找或创建TMDB记录
        existing_tmdb = db_session.query(Tmdb).filter(
            Tmdb.tmdb_code == str(tmdb_id)
        ).first()

        if existing_tmdb:
            # 更新现有记录
            existing_tmdb.title = title
            existing_tmdb.year_released = year
            existing_tmdb.description = overview or ""
            existing_tmdb.poster_url = poster_url
            existing_tmdb.category = category
            tmdb_record_id = existing_tmdb.id
            logging.info(f"更新TMDB记录: {title}")
        else:
            # 创建新记录
            new_tmdb = Tmdb(
                tmdb_code=str(tmdb_id),
                title=title,
                year_released=year,
                category=category,
                description=overview or "",
                poster_url=poster_url
            )
            db_session.add(new_tmdb)
            db_session.flush()
            tmdb_record_id = new_tmdb.id
            logging.info(f"创建TMDB记录: {title}")

        # 关联资源和TMDB
        resource.tmdb_id = tmdb_record_id
        db_session.commit()

        logging.info(f"✅ 资源 '{resource.drama_name}' 已匹配到TMDB: {title}")

        return jsonify({
            "success": True,
            "message": "匹配成功",
            "tmdb_id": tmdb_record_id
        })

    except Exception as e:
        db_session.rollback()
        logging.error(f"匹配TMDB失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    init()
    reload_tasks()
    app.run(debug=DEBUG, host="0.0.0.0", port=5005)
