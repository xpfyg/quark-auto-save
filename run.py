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
import threading
from datetime import datetime


from drama_classifier import extract_drama_name, classify_drama
from task_handlers import register_all_handlers
from telegram_queue_manager import add_task
from extensions import scheduler  # 导入共享的 scheduler 实例

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


# 原有的 BackgroundScheduler，用于 quark_auto_save.py 脚本调度
bg_scheduler = BackgroundScheduler()

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
        f">>> 手动运行任务{int(task_index) + 1 if task_index.isdigit() else 'all'}"
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
        if bg_scheduler.state == 1:
            bg_scheduler.pause()  # 暂停调度器
        trigger = CronTrigger.from_crontab(crontab)
        bg_scheduler.remove_all_jobs()
        bg_scheduler.add_job(
            run_python,
            trigger=trigger,
            args=[f"{SCRIPT_PATH} {CONFIG_PATH}"],
            id=SCRIPT_PATH,
        )
        if bg_scheduler.state == 0:
            bg_scheduler.start()
        elif bg_scheduler.state == 2:
            bg_scheduler.resume()
        scheduler_state_map = {0: "停止", 1: "运行", 2: "暂停"}
        logging.info(">>> 重载调度器")
        logging.info(f"调度状态: {scheduler_state_map[bg_scheduler.state]}")
        logging.info(f"定时规则: {crontab}")
        logging.info(f"现有任务: {bg_scheduler.get_jobs()}")
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

        # 在后台事件循环中执行异步任务
        if queue_loop and queue_loop.is_running():
            # 使用 asyncio.run_coroutine_threadsafe 在后台事件循环中执行
            future = asyncio.run_coroutine_threadsafe(
                manager.shareToTgBot(resource_id),
                queue_loop
            )
            # 等待任务完成（设置超时）
            result = future.result(timeout=10)

            if result:
                return jsonify({"success": True, "message": "任务已加入队列"})
            else:
                return jsonify({"error": "任务加入队列失败"}), 500
        else:
            return jsonify({"error": "队列管理器未运行"}), 500

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


# 获取队列状态
@app.route("/api/queue_status", methods=["GET"])
def get_queue_status():
    if not is_login():
        return jsonify({"error": "未登录"}), 401

    try:
        import telegram_queue_manager as qm

        # 在后台事件循环中获取状态
        async def get_status():
            return qm.get_status()

        if queue_loop and queue_loop.is_running():
            future = asyncio.run_coroutine_threadsafe(get_status(), queue_loop)
            status = future.result(timeout=5)
            return jsonify({"success": True, "status": status})
        else:
            return jsonify({"error": "队列管理器未运行"}), 500

    except Exception as e:
        logging.error(f"获取队列状态失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# 夸克网盘资源页面
@app.route("/quark_files")
def quark_files():
    if not is_login():
        return redirect(url_for("login"))
    return render_template("quark_files.html", version=app.config["APP_VERSION"])


# 获取夸克网盘文件列表
@app.route("/api/quark/ls_dir", methods=["GET"])
def quark_ls_dir():
    if not is_login():
        return jsonify({"error": "未登录"}), 401

    try:
        pdir_fid = request.args.get("pdir_fid", "0")

        # 获取cookie
        cookie = os.environ.get("QUARK_COOKIE", "")
        if not cookie:
            data = read_json()
            cookie = data.get("quark_cookie", "")
        if not cookie:
            return jsonify({"error": "未配置夸克Cookie"}), 400

        # 创建 Quark 实例
        from quark_auto_save import Quark
        quark = Quark(cookie, index=0)

        if not quark.init():
            return jsonify({"error": "夸克账号验证失败"}), 400

        # 获取文件列表
        files = quark.ls_dir(pdir_fid)

        if files is None:
            return jsonify({"error": "获取文件列表失败"}), 500

        return jsonify({"success": True, "files": files})

    except Exception as e:
        logging.error(f"获取文件列表失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# 分享并保存资源到数据库
@app.route("/api/quark/share_and_save", methods=["POST"])
def quark_share_and_save():
    if not is_login():
        return jsonify({"error": "未登录"}), 401

    try:
        data = request.json
        fid = data.get("fid")
        file_name = data.get("file_name")
        is_dir = data.get("is_dir", False)

        if not fid or not file_name:
            return jsonify({"error": "缺少必要参数"}), 400

        item_type = "文件夹" if is_dir else "文件"
        logging.info(f"开始处理{item_type}: {file_name} (fid: {fid})")

        # 获取cookie
        cookie = os.environ.get("QUARK_COOKIE", "")
        if not cookie:
            config_data = read_json()
            cookie = config_data.get("quark_cookie", "")
        if not cookie:
            return jsonify({"error": "未配置夸克Cookie"}), 400

        # 创建 Quark 实例
        from quark_auto_save import Quark
        quark = Quark(cookie, index=0)

        if not quark.init():
            return jsonify({"error": "夸克账号验证失败"}), 400

        drama_name = extract_drama_name(file_name)
        existing_resource = db_session.query(CloudResource).filter(
            CloudResource.drama_name == drama_name,
            CloudResource.drive_type == "quark"
        ).first()
        if existing_resource:
            return jsonify({"error": f"{item_type}已存在: {file_name}"}), 400

        # 创建分享
        logging.info(f"正在分享{item_type}: {file_name}")
        share_result = quark.share_dir([fid], file_name)

        if not share_result or not share_result.get("share_url"):
            return jsonify({"error": f"创建{item_type}分享失败"}), 500

        share_url = share_result["share_url"]
        logging.info(f"✅ {item_type}分享成功: {share_url}")

        # 创建新资源
        # 根据是否为文件夹设置分类
        category2 = classify_drama(file_name)
        new_resource = CloudResource(
            drama_name=drama_name,
            alias=file_name,
            drive_type="quark",
            link=share_url,
            is_expired=0,
            category1="影视资源",
            category2=category2
        )
        db_session.add(new_resource)
        db_session.flush()
        resource_id = new_resource.id
        action = "创建"
        logging.info(f"创建新资源: {file_name} (ID: {resource_id})")

        db_session.commit()
        success_message = f"{item_type}{action}成功！"
        logging.info(f"✅ {success_message}")

        # 添加 TMDB 更新任务到队列
        try:
            import telegram_queue_manager as qm

            # 准备任务数据
            task_data = {
                "resource_id": resource_id,
                "drama_name": drama_name,
                "category": category2 if category2 in ["电影", "剧集"] else "电影"
            }

            # 创建任务
            task = qm.Task(
                task_type=qm.TaskType.TMDB_UPDATE,
                task_data=task_data
            )

            # 在后台事件循环中添加任务
            if queue_loop and queue_loop.is_running():
                async def add_tmdb_task():
                    return await qm.add_task(task)

                future = asyncio.run_coroutine_threadsafe(add_tmdb_task(), queue_loop)
                task_added = future.result(timeout=5)

                if task_added:
                    logging.info(f"✅ 已添加 TMDB 更新任务: {drama_name}")
                else:
                    logging.warning(f"⚠️  TMDB 更新任务添加失败: {drama_name}")
            else:
                logging.warning("⚠️  队列管理器未运行，跳过 TMDB 更新任务")

        except Exception as e:
            logging.error(f"添加 TMDB 更新任务失败: {str(e)}")
            import traceback
            traceback.print_exc()
            # 不影响主流程，继续返回成功

        return jsonify({
            "success": True,
            "message": success_message,
            "resource_id": resource_id,
            "share_url": share_url,
            "item_type": item_type,
            "action": action})
    except Exception as e:
        db_session.rollback()
        logging.error(f"处理失败: {str(e)}")
        import traceback
        traceback.print_exc()
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
        results = tmdb_service.search_multi(query, max_results=20)

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


# 手动触发资源链接检查任务
@app.route("/api/check_resources_links", methods=["POST"])
def trigger_check_resources_links():
    if not is_login():
        return jsonify({"error": "未登录"}), 401

    try:
        # 在后台线程中执行任务，避免阻塞请求
        import threading
        from job import check_all_resources_links

        def run_check():
            try:
                check_all_resources_links()
            except Exception as e:
                logging.error(f"资源链接检查任务执行失败: {str(e)}")
                import traceback
                traceback.print_exc()

        check_thread = threading.Thread(target=run_check, daemon=True)
        check_thread.start()

        return jsonify({
            "success": True,
            "message": "资源链接检查任务已启动，请查看日志了解进度"
        })

    except Exception as e:
        logging.error(f"启动资源链接检查任务失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# 后台事件循环线程
queue_loop = None
queue_thread = None


def start_queue_manager_thread():
    """在后台线程中启动队列管理器"""
    global queue_loop, queue_thread

    def run_event_loop():
        """在新线程中运行事件循环"""
        global queue_loop
        try:
            # 创建新的事件循环
            queue_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(queue_loop)

            # 注册所有处理器并启动队列管理器
            queue_loop.run_until_complete(register_all_handlers())

            logging.info("✅ 队列管理器已在后台线程启动")

            # 保持事件循环运行
            queue_loop.run_forever()

        except Exception as e:
            logging.error(f"❌ 队列管理器启动失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if queue_loop:
                queue_loop.close()
                logging.info("🔌 队列管理器事件循环已关闭")

    # 创建并启动后台线程
    queue_thread = threading.Thread(target=run_event_loop, daemon=True)
    queue_thread.start()
    logging.info("🚀 队列管理器后台线程已启动")


def stop_queue_manager():
    """停止队列管理器"""
    global queue_loop

    if queue_loop and queue_loop.is_running():
        logging.info("🛑 正在停止队列管理器...")
        queue_loop.call_soon_threadsafe(queue_loop.stop)


if __name__ == "__main__":
    init()
    reload_tasks()

    # 配置并初始化 Flask-APScheduler
    app.config['SCHEDULER_API_ENABLED'] = True  # 启用 API
    scheduler.init_app(app)
    scheduler.start()

    # 导入 job 模块以注册装饰器任务
    import job
    logging.info("✅ 定时任务已注册")

    # 启动队列管理器后台线程
    start_queue_manager_thread()

    try:
        app.run(debug=DEBUG, host="0.0.0.0", port=5005)
    finally:
        # 程序退出时停止队列管理器
        stop_queue_manager()
        # 停止 Flask-APScheduler
        if scheduler.running:
            scheduler.shutdown()
