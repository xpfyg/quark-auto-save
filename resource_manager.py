# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
夸克网盘资源管理器
功能：检查资源是否存在，如不存在则转存并获取TMDB信息
"""
import asyncio
import os
import time
from unicodedata import category

import requests
from datetime import datetime

from flask.cli import load_dotenv
from sqlalchemy.util import await_only

from db import db_session
from drama_classifier import DramaClassifier, classify_drama
from llm_sdk import create_client
from model.cloud_resource import CloudResource
from model.tmdb import Tmdb
from quark_auto_save import Quark, download_file
from telegram_sdk.tg import TgClient

# TMDB API配置
TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "")  # 需要在环境变量中设置
# TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_BASE_URL = "http://api.tmdb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"


class TmdbService:
    """TMDB API服务类"""

    def __init__(self, api_key=None):
        self.api_key = api_key or TMDB_API_KEY
        if not self.api_key:
            print("⚠️ 警告: TMDB_API_KEY 未设置，TMDB功能将不可用")

    def search_drama(self, drama_name, category="电影"):
        """
        搜索剧集信息
        :param drama_name: 剧名
        :param category: 类型（'电影' 或 '剧集'），默认为'电影'
        :return: TMDB信息字典或None
        """
        if not self.api_key:
            print("❌ TMDB API Key未配置，跳过查询")
            return None

        try:
            # 根据 category 参数决定查询顺序
            if category == "电影":
                # 先尝试搜索电影
                movie_url = f"{TMDB_BASE_URL}/search/movie"
                movie_params = {
                    "api_key": self.api_key,
                    "query": drama_name,
                    "language": "zh-CN"
                }
                movie_response = requests.get(movie_url, params=movie_params, timeout=10)

                if movie_response.status_code == 200:
                    movie_data = movie_response.json()
                    if movie_data.get("results") and len(movie_data["results"]) > 0:
                        result = movie_data["results"][0]
                        print(f"✅ 在TMDB找到电影: {result.get('title')}")
                        return self._format_tmdb_data(result, "movie")

                # 如果电影没找到，尝试搜索电视剧
                tv_url = f"{TMDB_BASE_URL}/search/tv"
                tv_params = {
                    "api_key": self.api_key,
                    "query": drama_name,
                    "language": "zh-CN"
                }
                tv_response = requests.get(tv_url, params=tv_params, timeout=10)

                if tv_response.status_code == 200:
                    tv_data = tv_response.json()
                    if tv_data.get("results") and len(tv_data["results"]) > 0:
                        result = tv_data["results"][0]
                        print(f"✅ 在TMDB找到电视剧: {result.get('name')}")
                        return self._format_tmdb_data(result, "tv")

            else:  # category == "剧集"
                # 先尝试搜索电视剧
                tv_url = f"{TMDB_BASE_URL}/search/tv"
                tv_params = {
                    "api_key": self.api_key,
                    "query": drama_name,
                    "language": "zh-CN"
                }
                tv_response = requests.get(tv_url, params=tv_params, timeout=10)

                if tv_response.status_code == 200:
                    tv_data = tv_response.json()
                    if tv_data.get("results") and len(tv_data["results"]) > 0:
                        result = tv_data["results"][0]
                        print(f"✅ 在TMDB找到电视剧: {result.get('name')}")
                        return self._format_tmdb_data(result, "tv")

                # 如果电视剧没找到，尝试搜索电影
                movie_url = f"{TMDB_BASE_URL}/search/movie"
                movie_params = {
                    "api_key": self.api_key,
                    "query": drama_name,
                    "language": "zh-CN"
                }
                movie_response = requests.get(movie_url, params=movie_params, timeout=10)

                if movie_response.status_code == 200:
                    movie_data = movie_response.json()
                    if movie_data.get("results") and len(movie_data["results"]) > 0:
                        result = movie_data["results"][0]
                        print(f"✅ 在TMDB找到电影: {result.get('title')}")
                        return self._format_tmdb_data(result, "movie")

            print(f"📢 未在TMDB找到《{drama_name}》相关信息")
            return None

        except Exception as e:
            print(f"❌ 查询TMDB失败: {str(e)}")
            return None

    def _format_tmdb_data(self, result, media_type):
        """
        格式化TMDB数据
        :param result: TMDB API返回的结果
        :param media_type: 类型（tv/movie）
        :return: 格式化后的字典
        """
        title = result.get("name") if media_type == "tv" else result.get("title")
        release_date = result.get("first_air_date") if media_type == "tv" else result.get("release_date")
        year_released = int(release_date[:4]) if release_date else None

        # 获取类型（genres）
        genre_ids = result.get("genre_ids", [])
        category = self._get_genre_names(genre_ids)

        # 构建海报URL
        poster_path = result.get("poster_path")
        poster_url = f"{TMDB_IMAGE_BASE_URL}{poster_path}" if poster_path else None

        return {
            "tmdb_code": str(result.get("id")),
            "title": title,
            "year_released": year_released,
            "category": category,
            "description": result.get("overview", ""),
            "poster_url": poster_url
        }

    def _get_genre_names(self, genre_ids):
        """
        根据genre_id获取类型名称
        :param genre_ids: 类型ID列表
        :return: 类型名称字符串
        """
        # 常见类型映射
        genre_map = {
            28: "动作", 12: "冒险", 16: "动画", 35: "喜剧", 80: "犯罪",
            99: "纪录", 18: "剧情", 10751: "家庭", 14: "奇幻", 36: "历史",
            27: "恐怖", 10402: "音乐", 9648: "悬疑", 10749: "爱情", 878: "科幻",
            10770: "电视电影", 53: "惊悚", 10752: "战争", 37: "西部",
            10759: "动作冒险", 10762: "儿童", 10763: "新闻", 10764: "真人秀",
            10765: "科幻奇幻", 10766: "肥皂剧", 10767: "脱口秀", 10768: "战争政治"
        }

        categories = [genre_map.get(gid, "") for gid in genre_ids if gid in genre_map]
        return "、".join(categories[:3]) if categories else "其他"

    def search_multi(self, query, max_results=10):
        """
        搜索TMDB（同时搜索电影和电视剧）
        :param query: 搜索关键词
        :param max_results: 最大返回结果数，默认10
        :return: 包含电影和电视剧的结果列表
        """
        if not self.api_key:
            print("❌ TMDB API Key未配置")
            return []

        try:
            # 使用multi搜索接口，可以同时搜索电影、电视剧等多种媒体
            url = f"{TMDB_BASE_URL}/search/multi"
            params = {
                "api_key": self.api_key,
                "query": query,
                "language": "zh-CN",
                "page": 1,
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])

                # 过滤出电影和电视剧，排除其他类型（如人物）
                filtered_results = []
                for result in results[:max_results]:
                    media_type = result.get("media_type")
                    if media_type in ["movie", "tv"]:
                        # 获取类型分类
                        genre_ids = result.get("genre_ids", [])
                        category = self._get_genre_names(genre_ids)

                        # 格式化结果，添加必要字段
                        formatted = {
                            "id": result.get("id"),
                            "media_type": media_type,
                            "title": result.get("title") if media_type == "movie" else None,
                            "name": result.get("name") if media_type == "tv" else None,
                            "release_date": result.get("release_date") if media_type == "movie" else None,
                            "first_air_date": result.get("first_air_date") if media_type == "tv" else None,
                            "overview": result.get("overview", ""),
                            "poster_path": result.get("poster_path"),
                            "vote_average": result.get("vote_average", 0),
                            "genre_ids": genre_ids,
                            "category": category
                        }
                        filtered_results.append(formatted)

                print(f"✅ TMDB搜索成功: 找到 {len(filtered_results)} 个结果")
                return filtered_results
            else:
                print(f"❌ TMDB API请求失败: {response.status_code}")
                return []

        except Exception as e:
            print(f"❌ 搜索TMDB失败: {str(e)}")
            return []


class ResourceManager:
    """资源管理器"""

    def __init__(self, drive_type="quark"):
        """
        初始化资源管理器
        :param drive_type: 网盘类型，默认quark
        """
        # 从配置文件或环境变量读取 cookie
        cookie = self._get_cookie()
        if not cookie:
            raise Exception("❌ 未配置夸克Cookie，请设置环境变量 QUARK_COOKIE 或在配置文件中配置")

        self.quark = Quark(cookie, index=0)
        # 不再在初始化时创建 TgClient，而是在需要时动态创建
        # 避免 session 文件锁定问题
        self.drive_type = drive_type
        self.tmdb_service = TmdbService()

        # 验证账号
        if not self.quark.init():
            raise Exception("❌ 夸克账号验证失败，请检查cookie")
        print(f"✅ 账号验证成功: {self.quark.nickname}")

    def _get_cookie(self):
        """
        从环境变量或配置文件读取 cookie
        :return: cookie字符串
        """
        # 优先从环境变量读取
        cookie = os.environ.get("QUARK_COOKIE", "")
        if cookie:
            return cookie

        # 如果环境变量没有，尝试从配置文件读取
        try:
            import json
            config_path = os.environ.get("CONFIG_PATH", "./quark_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    cookie = data.get("quark_cookie", "")
                    if cookie:
                        return cookie
        except Exception as e:
            print(f"⚠️ 读取配置文件失败: {str(e)}")

        return ""

    # 转存资源到自己账号,并生成自己的分享地址，保存到数据库
    def process_resource(self, drama_name, share_link, savepath="/"):
        """
        处理资源：检查是否存在，如不存在则转存并保存信息
        :param drama_name: 剧名
        :param share_link: 分享链接
        :param savepath: 转存目标路径，默认根目录
        :param category: 资源类型（'电影' 或 '剧集'），默认'电影'，用于优化TMDB查询
        :return: 包含资源信息和TMDB信息的字典
        """
        print(f"\n{'=' * 50}")
        print(f"📺 开始处理资源: {drama_name}")
        print(f"🔗 分享链接: {share_link}")
        print(f"{'=' * 50}\n")

        # 1. 检查数据库中是否存在且有效
        existing_resource = db_session.query(CloudResource).filter(
            CloudResource.drama_name == drama_name,
            CloudResource.drive_type == self.drive_type,
            CloudResource.is_expired == 0
        ).first()

        if existing_resource:
            print(f"✅ 资源已存在且有效: {drama_name}")
            # 获取对应的TMDB信息
            tmdb_info = None
            if existing_resource.tmdb_id:
                tmdb_info = db_session.query(Tmdb).filter(
                    Tmdb.id == existing_resource.tmdb_id
                ).first()

            result = {
                "status": "existing",
                "resource": existing_resource.to_dict(),
                "tmdb": tmdb_info.to_dict() if tmdb_info else None
            }
            print(f"📊 资源信息: ID={existing_resource.id}, 热度={existing_resource.hot}")
            return result

        # 2. 资源不存在或已失效，执行转存
        print(f"📥 资源不存在或已失效，开始转存...")
        save_result = self.quark.do_save_check(share_link, savepath)

        if not save_result:
            print(f"❌ 转存失败: {drama_name}")
            return {
                "status": "failed",
                "message": "转存失败",
                "resource": None,
                "tmdb": None
            }

        print(f"✅ 转存成功!")
        # 分类资源类型
        category = classify_drama(drama_name)
        # 3. 查询TMDB信息
        print(f"🎬 正在查询TMDB信息...")
        tmdb_data = self.tmdb_service.search_drama(drama_name, category=category)
        tmdb_id = None
        tmdb_info = None

        if tmdb_data:
            # 检查TMDB是否已存在
            existing_tmdb = db_session.query(Tmdb).filter(
                Tmdb.title == tmdb_data["title"],
                Tmdb.year_released == tmdb_data["year_released"]
            ).first()

            if existing_tmdb:
                print(f"✅ TMDB信息已存在: {existing_tmdb.title}")
                tmdb_id = existing_tmdb.id
                tmdb_info = existing_tmdb
            else:
                # 保存新的TMDB信息
                new_tmdb = Tmdb(**tmdb_data)
                db_session.add(new_tmdb)
                db_session.flush()
                tmdb_id = new_tmdb.id
                tmdb_info = new_tmdb
                print(f"✅ TMDB信息已保存: {new_tmdb.title} ({new_tmdb.year_released})")
        else:
            print(f"⚠️ 未找到TMDB信息")

        print(save_result)
        share = self.quark.share_dir(save_result['save_fids'], drama_name)
        share_link = share['share_url']
        # 4. 保存资源信息到数据库
        if existing_resource:
            # 更新现有资源
            existing_resource.alias = save_result.get('save_file_names').get(0)
            existing_resource.link = share_link
            existing_resource.caategory2 = tmdb_info.category if tmdb_info else "其他",
            existing_resource.is_expired = 0
            existing_resource.tmdb_id = tmdb_id
            existing_resource.update_time = datetime.now()
            resource = existing_resource
            print(f"✅ 资源信息已更新: {drama_name}")
        else:
            # 创建新资源
            new_resource = CloudResource(
                drama_name=drama_name,
                alias=save_result.get('save_file_names')[0],
                drive_type=self.drive_type,
                link=share_link,
                is_expired=0,
                category1="影视资源",
                category2=category if category else "其他",
                tmdb_id=tmdb_id
            )
            db_session.add(new_resource)
            db_session.flush()
            resource = new_resource
            print(f"✅ 资源信息已保存: {drama_name}")

        # 提交事务
        db_session.commit()

        result = {
            "status": "saved",
            "resource": resource.to_dict(),
            "tmdb": tmdb_info.to_dict() if tmdb_info else None
        }

        print(f"\n{'=' * 50}")
        print(f"✅ 处理完成: {drama_name}")
        print(f"{'=' * 50}\n")

        return result

    # 检查分享链接是否有效
    def check_share_link(self, share_link):
        """
        检查分享链接是否有效
        :param share_link: 分享链接
        :return: 如果有效则返回分享信息，否则返回None
        """
        resource = db_session.query(CloudResource).filter(
            CloudResource.link == share_link
        ).first()
        if not resource:
            print("❌ 分享链接不存在")
            return False

        pwd_id, pdir_fid = self.quark.get_id_from_url(share_link)
        is_sharing, stoken = self.quark.get_stoken(pwd_id)
        share_file_list = self.quark.get_detail_v2(pwd_id, stoken, pdir_fid)
        print("share_file_list====: ", share_file_list)
        if not share_file_list:
            resource.is_expired = 1
            db_session.commit()
            print("❌ 分享链接无效或已失效")
            return False
        print("✅ 分享链接有效")
        return True

    async def shareToTgBot(self, id):
        """
        分享资源到Telegram机器人（使用队列管理器）
        :param id: 资源ID
        :return: bool - 是否成功加入队列
        """
        import telegram_queue_manager as qm

        resource = db_session.query(CloudResource).filter(
            CloudResource.id == id
        ).first()
        if not resource:
            print(f"❌ 资源不存在: {id}")
            return False

        # 检查资源是否过期
        if resource.is_expired:
            print(f"❌ 资源已过期: {resource.drama_name}")
            return False

        if not self.check_share_link(resource.link):
            print(f"❌ 资源已失效: {resource.drama_name}")
            return False

        if resource.tmdb_id is None:
            print(f"🎬 正在查询TMDB信息...")
            # 使用资源的 category2 字段（如果存在）来优化 TMDB 查询
            category = resource.category2 if resource.category2 and resource.category2 in ["电影", "剧集"] else "电影"
            tmdb_data = self.tmdb_service.search_drama(resource.drama_name, category=category)
            if tmdb_data:
                # 检查TMDB是否已存在
                existing_tmdb = db_session.query(Tmdb).filter(
                    Tmdb.title == tmdb_data["title"],
                    Tmdb.year_released == tmdb_data["year_released"]
                ).first()

                if not existing_tmdb:
                    # 保存新的TMDB信息
                    new_tmdb = Tmdb(**tmdb_data)
                    db_session.add(new_tmdb)
                    db_session.flush()  # 立即获取 ID
                    db_session.query(CloudResource).filter(
                        CloudResource.id == id
                    ).update({
                        CloudResource.tmdb_id: new_tmdb.id
                    })
                    existing_tmdb = new_tmdb
                    print(f"✅ TMDB信息已保存: {new_tmdb.title} ({new_tmdb.year_released})")
                else:
                    db_session.query(CloudResource).filter(
                        CloudResource.id == id
                    ).update({
                        CloudResource.tmdb_id: existing_tmdb.id
                    })
                    print(f"✅ TMDB信息已关联: {existing_tmdb.title} ({existing_tmdb.year_released})")
                db_session.commit()
            else:
                print(f"⚠️ 未找到TMDB信息: {resource.drama_name}")
                return False
        else:
            existing_tmdb = db_session.query(Tmdb).filter(
                Tmdb.id == resource.tmdb_id
            ).first()

        title = resource.drama_name
        file_path = "./resource/tmdb/" + str(
            existing_tmdb.year_released) + "/" + existing_tmdb.title + "#" + existing_tmdb.tmdb_code + ".jpg"
        # 目录不存在则创建目录
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        # 尝试3次保存文件,
        for i in range(3):
            if not os.path.exists(file_path):
                download_file(existing_tmdb.poster_url, file_path)
                time.sleep(3)
            break

        # 创建任务数据
        task_data = {
            "resource_id": id,
            "title": title,
            "description": existing_tmdb.description.strip(),
            "link": resource.link,
            "category": existing_tmdb.category,
            "file_path": file_path
        }

        # 创建任务对象
        task = qm.Task(
            task_type=qm.TaskType.TELEGRAM_SHARE,
            task_data=task_data
        )

        # 使用模块级别函数添加任务
        success = await qm.add_task(task)

        if success:
            print(f"✅ 任务已成功加入队列: {title}")
            return True
        else:
            print(f"❌ 任务加入队列失败: {title}")
            return False

