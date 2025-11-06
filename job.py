# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务模块
功能：定期检查云盘资源链接的有效性
"""
import os
import time
import random
import logging
import re
import requests
from datetime import datetime

from db import db_session
from model.cloud_resource import CloudResource
from resource_manager import ResourceManager
from extensions import scheduler
from llm_sdk import create_client, Message


# ============================================================================
# 定时任务 1: 资源链接有效性检查
# ============================================================================

@scheduler.task('cron', id='check_resources_links', hour=2, minute=0)
def check_all_resources_links():
    """
    定时任务：检查所有未失效资源的链接有效性

    功能：
    - 遍历所有未失效的资源
    - 调用 check_share_link 检测链接是否失效
    - 每个链接检测后随机间隔 1-3 秒
    - 每检测 10 次后间隔 10 秒
    """
    try:
        logging.info("=" * 60)
        logging.info(f"🔍 开始检查资源链接有效性 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logging.info("=" * 60)

        # 获取 Quark Cookie
        cookie = os.environ.get("QUARK_COOKIE", "")
        if not cookie:
            logging.error("❌ 未配置 QUARK_COOKIE，无法执行检查任务")
            return

        # 创建资源管理器
        manager = ResourceManager(cookie)

        # 查询所有未失效的资源
        resources = db_session.query(CloudResource).filter(
            CloudResource.is_expired == 0,
            CloudResource.link.isnot(None)
        ).all()

        if not resources:
            logging.info("ℹ️  没有需要检查的资源")
            return

        total_count = len(resources)
        valid_count = 0
        invalid_count = 0
        error_count = 0

        logging.info(f"📊 共找到 {total_count} 个未失效资源需要检查")
        logging.info("")

        for index, resource in enumerate(resources, start=1):
            try:
                logging.info(f"[{index}/{total_count}] 检查资源: {resource.drama_name}")
                logging.info(f"  └─ 链接: {resource.link}")

                # 检查链接有效性
                is_valid = manager.check_share_link(resource.link)

                if is_valid:
                    valid_count += 1
                    logging.info(f"  ✅ 链接有效")
                else:
                    invalid_count += 1
                    logging.info(f"  ❌ 链接已失效")

                # 每个链接检测后随机间隔 1-3 秒
                if index < total_count:  # 最后一个不需要等待
                    wait_time = random.uniform(1, 3)
                    logging.info(f"  ⏱️  等待 {wait_time:.1f} 秒...")
                    time.sleep(wait_time)

                # 每检测 10 次后额外间隔 10 秒
                if index % 10 == 0 and index < total_count:
                    logging.info(f"  ⏸️  已检测 {index} 个资源，休息 10 秒...")
                    time.sleep(10)

                logging.info("")

            except Exception as e:
                error_count += 1
                logging.error(f"  ❌ 检查资源失败: {str(e)}")
                import traceback
                traceback.print_exc()
                logging.info("")
                continue

        # 输出统计信息
        logging.info("=" * 60)
        logging.info("📈 检查完成 - 统计结果")
        logging.info("=" * 60)
        logging.info(f"总数量: {total_count}")
        logging.info(f"✅ 有效: {valid_count}")
        logging.info(f"❌ 失效: {invalid_count}")
        logging.info(f"⚠️  错误: {error_count}")
        logging.info(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logging.info("=" * 60)

    except Exception as e:
        logging.error(f"❌ 定时任务执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理数据库会话
        db_session.remove()


# ============================================================================
# 定时任务 2: 自动收集热门资源
# ============================================================================

# 搜索接口配置
SEARCH_API_URL = "http://127.0.0.1:8888/api/search"


def get_hot_movies_from_ai():
    """
    使用豆包大模型获取最近热门的流媒体资源列表

    Returns:
        list: 电影名称列表，最多10部
    """
    try:
        logging.info("🤖 正在使用豆包AI收集热门资源...")

        # 获取 ARK 配置
        api_key = os.getenv("ARK_API_KEY")
        model_id = os.getenv("ARK_MODEL_ID")

        if not api_key or not model_id:
            logging.error("❌ 未配置 ARK_API_KEY 或 ARK_MODEL_ID")
            return []

        # 创建客户端
        client = create_client(platform="ark", api_key=api_key)
        resources = db_session.query(CloudResource).filter(
            CloudResource.category1 == "影视资源",
            CloudResource.is_expired == 0,
        ).all()
        #遍历resources，逗号分割alias
        drama_name_list = [resource.drama_name for resource in resources]
        drama_name_str = ','.join(drama_name_list)





        # 构建提示词
        current_date = datetime.now().strftime("%Y年%m月")
        prompt = f"""请帮我整理{current_date}最近热门的流媒体电影资源，要求：

1. 优先选择热度较高的资源（例如在豆瓣、IMDb等平台上有较高评分的电影）
2. 优先选择电影院已下映、流媒体已上映的电影
3. 优先选择续作的前作资源（例如如果有《XX 2》上映，优先收集《XX 1》）
4. 只返回电影，不要剧集
6. 避免重复，且不要包含以下电影名称：{drama_name_str}
5. 返回10部电影即可

请直接返回电影名称列表，每行一个，格式如下：
1. 电影名称1
2. 电影名称2
...

不要有其他说明文字，只返回纯电影名称列表。"""

        # 调用 AI
        messages = [
            Message(role="system", content="你是一个影视资源推荐专家，熟悉最新的流媒体平台上映信息。"),
            Message(role="user", content=prompt)
        ]

        response = client.chat_completion(
            messages=messages,
            model=model_id,
            temperature=0.7
        )

        # 解析结果
        content = response.content.strip()
        logging.info(f"AI 返回内容:\n{content}\n")

        # 提取电影名称
        movies = []
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue

            # 移除序号（1. 2. 3. 或 1、2、3、）
            line = re.sub(r'^\d+[.、]\s*', '', line)
            # 移除其他符号
            line = line.strip('*-• ')

            if line:
                movies.append(line)

        # 限制最多10部
        movies = movies[:10]

        logging.info(f"✅ 成功获取 {len(movies)} 部电影:")
        for i, movie in enumerate(movies, 1):
            logging.info(f"  {i}. {movie}")

        return movies

    except Exception as e:
        logging.error(f"❌ AI 收集失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


def search_resources(keyword):
    """
    调用搜索接口检索资源

    Args:
        keyword: 搜索关键词（电影名）

    Returns:
        list: 资源列表
    """
    try:
        params = {
            "kw": keyword,
            "res": "merge",
            "src": "all",
            "cloud_types": ["quark"]
        }

        response = requests.get(SEARCH_API_URL, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()

        if data.get("code") != 0:
            logging.warning(f"⚠️  搜索 '{keyword}' 失败: {data.get('message')}")
            return []

        # 提取 quark 资源
        quark_resources = data.get("data", {}).get("merged_by_type", {}).get("quark", [])

        logging.info(f"🔍 搜索到 {len(quark_resources)} 个资源")

        return quark_resources

    except Exception as e:
        logging.error(f"❌ 搜索接口调用失败: {str(e)}")
        return []


def is_high_quality_resource(note):
    """
    判断是否为高清资源（4K、杜比等）

    Args:
        note: 资源备注/标题

    Returns:
        int: 质量分数，越高越好
    """
    if not note:
        return 0

    score = 0
    note_lower = note.lower()

    # 高优先级关键词
    if re.search(r'4k|2160p', note_lower):
        score += 100
    if re.search(r'杜比|dolby|atmos|vision', note_lower):
        score += 80
    if re.search(r'hdr|hdr10', note_lower):
        score += 70

    # 中优先级关键词
    if re.search(r'1080p|bluray|蓝光', note_lower):
        score += 50
    if re.search(r'remux', note_lower):
        score += 40

    # 低优先级关键词
    if re.search(r'720p', note_lower):
        score += 20

    return score


def sort_resources_by_quality(resources):
    """
    按照质量排序资源

    Args:
        resources: 资源列表

    Returns:
        list: 排序后的资源列表
    """
    # 为每个资源计算质量分数
    for resource in resources:
        resource['quality_score'] = is_high_quality_resource(resource.get('note', ''))

    # 按分数降序排序
    sorted_resources = sorted(resources, key=lambda x: x['quality_score'], reverse=True)

    return sorted_resources


@scheduler.task('cron', id='collect_hot_movies', hour='10,17', minute=0)
def collect_hot_movies():
    """
    定时任务：自动收集热门电影资源

    执行时间：每天 10:00 和 17:00

    功能：
    1. 使用豆包AI获取10部热门电影
    2. 搜索每部电影的资源
    3. 优先选择4K、杜比等高清资源
    4. 保存到 /TXQ 目录
    """
    try:
        logging.info("=" * 60)
        logging.info(f"🎬 开始收集热门电影资源 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logging.info("=" * 60)

        # 获取 Quark Cookie
        cookie = os.environ.get("QUARK_COOKIE", "")
        if not cookie:
            logging.error("❌ 未配置 QUARK_COOKIE，无法执行收集任务")
            return

        # 创建资源管理器
        manager = ResourceManager(cookie)

        # 1. 使用AI获取热门电影列表
        movies = get_hot_movies_from_ai()

        if not movies:
            logging.warning("⚠️  未获取到电影列表，任务结束")
            return

        # 统计变量
        total_movies = len(movies)
        success_count = 0
        failed_count = 0
        failed_movies = []

        # 2. 遍历每部电影
        for index, movie_name in enumerate(movies, 1):
            try:
                logging.info("")
                logging.info("=" * 60)
                logging.info(f"📽️  [{index}/{total_movies}] 处理电影: {movie_name}")
                logging.info("=" * 60)

                # 2.1 搜索资源
                resources = search_resources(movie_name)

                if not resources:
                    logging.warning(f"⚠️  未找到资源，跳过")
                    failed_count += 1
                    failed_movies.append({"name": movie_name, "reason": "未找到资源"})
                    continue

                # 2.2 排序资源（优先高清）
                sorted_resources = sort_resources_by_quality(resources)

                # 2.3 尝试前10个资源
                max_attempts = min(10, len(sorted_resources))
                saved = False

                for attempt_idx, resource in enumerate(sorted_resources[:max_attempts], 1):
                    url = resource.get('url', '')
                    note = resource.get('note', '')
                    quality_score = resource.get('quality_score', 0)

                    logging.info(f"  [{attempt_idx}/{max_attempts}] 尝试资源:")
                    logging.info(f"    标题: {note}")
                    logging.info(f"    链接: {url}")
                    logging.info(f"    质量分数: {quality_score}")

                    if not url:
                        logging.warning(f"    ⚠️  链接为空，跳过")
                        continue

                    try:
                        # 2.4 调用 process_resource 保存
                        result = manager.process_resource(
                            drama_name=movie_name,
                            share_link=url,
                            savepath="/TXQ"
                        )

                        if result and result.get("status") in ["existing", "saved"]:
                            logging.info(f"    ✅ 保存成功!")
                            success_count += 1
                            saved = True
                            break
                        else:
                            logging.warning(f"    ❌ 保存失败，尝试下一个资源")

                    except Exception as e:
                        logging.error(f"    ❌ 保存异常: {str(e)}")
                        continue

                    # 每次尝试后随机延迟 1-3 秒
                    if attempt_idx < max_attempts:
                        wait_time = random.uniform(1, 3)
                        time.sleep(wait_time)

                if not saved:
                    logging.warning(f"❌ 所有资源尝试失败")
                    failed_count += 1
                    failed_movies.append({"name": movie_name, "reason": "所有资源保存失败"})

                # 每处理完一部电影后延迟 2-4 秒
                if index < total_movies:
                    wait_time = random.uniform(2, 4)
                    logging.info(f"⏱️  等待 {wait_time:.1f} 秒后处理下一部...")
                    time.sleep(wait_time)

            except Exception as e:
                logging.error(f"❌ 处理电影失败: {str(e)}")
                import traceback
                traceback.print_exc()
                failed_count += 1
                failed_movies.append({"name": movie_name, "reason": str(e)})
                continue

        # 3. 输出统计信息
        logging.info("")
        logging.info("=" * 60)
        logging.info("📊 收集任务完成 - 统计结果")
        logging.info("=" * 60)
        logging.info(f"总电影数: {total_movies}")
        logging.info(f"✅ 成功保存: {success_count} 部")
        logging.info(f"❌ 失败: {failed_count} 部")

        if failed_movies:
            logging.info("")
            logging.info("失败列表:")
            for item in failed_movies:
                logging.info(f"  • {item['name']} - {item['reason']}")

        logging.info(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logging.info("=" * 60)

    except Exception as e:
        logging.error(f"❌ 收集任务执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理数据库会话
        db_session.remove()


# ============================================================================
# 更多定时任务示例（取消注释后启用）
# ============================================================================

# 示例 1: 使用 interval 触发器 - 每隔一段时间执行
# @scheduler.task('interval', id='example_interval_task', hours=6)
# def example_interval_task():
#     """每隔 6 小时执行一次"""
#     logging.info("执行间隔任务...")

# 示例 2: 使用 cron 触发器 - 指定时间执行
# @scheduler.task('cron', id='example_daily_task', hour=8, minute=30)
# def example_daily_task():
#     """每天 08:30 执行"""
#     logging.info("执行每日任务...")

# 示例 3: 每周特定时间执行
# @scheduler.task('cron', id='example_weekly_task', day_of_week='mon', hour=9, minute=0)
# def example_weekly_task():
#     """每周一 09:00 执行"""
#     logging.info("执行每周任务...")

# 示例 4: 每月特定日期执行
# @scheduler.task('cron', id='example_monthly_task', day=1, hour=0, minute=0)
# def example_monthly_task():
#     """每月 1 号凌晨 00:00 执行"""
#     logging.info("执行每月任务...")


if __name__ == "__main__":
    # 测试任务
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s][%(levelname)s] %(message)s",
        datefmt="%m-%d %H:%M:%S",
    )

    print("开始测试资源链接检查任务...")
    # check_all_resources_links()
    collect_hot_movies()
