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
from datetime import datetime

from db import db_session
from model.cloud_resource import CloudResource
from resource_manager import ResourceManager
from drama_classifier import get_classifier
from resource_searcher import get_searcher
from extensions import scheduler
import notify


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

        # 创建资源管理器（内部会自动读取cookie）
        manager = ResourceManager()

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

        # 发送通知
        try:
            title = "资源链接有效性检查完成"
            content = f"""📊 检查统计：
总数量：{total_count}
✅ 有效：{valid_count}
❌ 失效：{invalid_count}
⚠️  错误：{error_count}

完成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

            notify.send(title, content)
            logging.info("✅ 通知发送成功")
        except Exception as e:
            logging.error(f"❌ 发送通知失败: {str(e)}")

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

#


# @scheduler.task('cron', id='collect_hot_movies', hour='10,17', minute=0)
def collect_hot_movies():
    """
    定时任务：自动收集热门电影资源

    执行时间：每天 10:00 和 17:00

    功能：
    1. 使用DramaClassifier获取热门电影列表（排除已存在的）
    2. 使用ResourceSearcher搜索并按质量排序资源
    3. 优先选择4K、杜比等高清资源
    4. 保存到 /TXQ 目录
    """
    try:
        logging.info("=" * 60)
        logging.info(f"🎬 开始收集热门电影资源 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logging.info("=" * 60)

        # 创建资源管理器（内部会自动读取cookie）
        manager = ResourceManager()

        # 创建分类器和搜索器
        classifier = get_classifier()
        searcher = get_searcher()

        # 1. 获取已存在的电影名称列表（用于排除）
        resources = db_session.query(CloudResource).filter(
            CloudResource.category1 == "影视资源",
            CloudResource.is_expired == 0,
        ).all()
        exclude_names = [resource.drama_name for resource in resources]

        # 2. 使用AI获取热门电影列表
        movies = classifier.get_hot_movies(max_count=1, exclude_names=exclude_names)

        if not movies:
            logging.warning("⚠️  未获取到电影列表，任务结束")
            return

        # 统计变量
        total_movies = len(movies)
        success_count = 0
        failed_count = 0
        success_movies = []  # 成功的电影列表
        failed_movies = []   # 失败的电影列表

        # 3. 遍历每部电影
        for index, movie_name in enumerate(movies, 1):
            try:
                logging.info("")
                logging.info("=" * 60)
                logging.info(f"📽️  [{index}/{total_movies}] 处理电影: {movie_name}")
                logging.info("=" * 60)

                # 3.1 搜索资源并按质量排序
                sorted_resources = searcher.search_and_sort(movie_name)

                if not sorted_resources:
                    logging.warning(f"⚠️  未找到资源，跳过")
                    failed_count += 1
                    failed_movies.append({"name": movie_name, "reason": "未找到资源"})
                    continue

                # 3.2 尝试前10个资源
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
                        # 3.3 调用 process_resource 保存
                        result = manager.process_resource(
                            drama_name=movie_name,
                            share_link=url,
                            savepath="/全网自动收集"
                        )

                        if result and result.get("status") in ["existing", "saved"]:
                            logging.info(f"    ✅ 保存成功!")
                            success_count += 1
                            success_movies.append(movie_name)
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

        # 4. 输出统计信息
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

        # 5. 发送通知
        try:
            title = "热门电影收集任务完成"

            # 构建通知内容
            content_parts = [
                "📊 收集统计：",
                f"总电影数：{total_movies}",
                f"✅ 成功保存：{success_count} 部",
                f"❌ 失败：{failed_count} 部",
                ""
            ]

            # 添加成功列表
            if success_movies:
                content_parts.append("✅ 成功保存的电影：")
                for i, movie in enumerate(success_movies, 1):
                    content_parts.append(f"{i}. {movie}")
                content_parts.append("")

            # 添加失败列表
            if failed_movies:
                content_parts.append("❌ 失败的电影：")
                for i, item in enumerate(failed_movies, 1):
                    content_parts.append(f"{i}. {item['name']} - {item['reason']}")
                content_parts.append("")

            content_parts.append(f"完成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            content = "\n".join(content_parts)
            notify.send(title, content)
            logging.info("✅ 通知发送成功")
        except Exception as e:
            logging.error(f"❌ 发送通知失败: {str(e)}")

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
