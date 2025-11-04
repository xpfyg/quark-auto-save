#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用豆包AI识别drama_name属于'电影'还是'剧集'，并更新数据库category2字段
"""

import os
import sys
import logging
from typing import Optional

from dotenv import load_dotenv

# 添加当前目录到系统路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import db_session
from model.cloud_resource import CloudResource
from drama_classifier import DramaClassifier

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s][%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
load_dotenv()


def update_category2(limit: Optional[int] = None, force_update: bool = False):
    """
    批量更新cloud_resource表的category2字段

    Args:
        limit: 限制处理的数量，None表示处理全部
        force_update: 是否强制更新已有category2的记录
    """
    # 创建分类器（会自动从环境变量读取配置）
    try:
        classifier = DramaClassifier()
        logging.info(f"✅ 初始化豆包AI分类器成功")
    except ValueError as e:
        logging.error(f"❌ 初始化失败: {str(e)}")
        sys.exit(1)

    # 查询需要处理的记录
    query = db_session.query(CloudResource)

    if not force_update:
        # 只处理category2为空的记录
        query = query.filter(
            (CloudResource.category2 == None) |
            (CloudResource.category2 == '')
        )

    if limit:
        query = query.limit(limit)

    resources = query.all()
    total = len(resources)

    if total == 0:
        logging.info("没有需要处理的记录")
        return

    logging.info(f"共找到 {total} 条记录需要处理")
    logging.info("=" * 60)

    # 批量处理
    for idx, resource in enumerate(resources, 1):
        drama_name = resource.drama_name

        logging.info(f"[{idx}/{total}] 处理: {drama_name}")

        # 调用分类器
        category_type = classifier.classify(drama_name)

        if category_type:
            # 更新数据库
            try:
                resource.category2 = category_type
                db_session.commit()
                logging.info(f"  ✓ 识别为: {category_type}")

            except Exception as e:
                db_session.rollback()
                logging.error(f"  ✗ 更新数据库失败: {str(e)}")
        else:
            logging.warning(f"  ✗ 识别失败")

    # 输出统计结果
    logging.info("=" * 60)
    logging.info("处理完成！")
    classifier.print_statistics()


def show_statistics():
    """显示当前数据库中的分类统计"""
    logging.info("=" * 60)
    logging.info("当前数据库分类统计")
    logging.info("=" * 60)

    # 总记录数
    total = db_session.query(CloudResource).count()
    logging.info(f"总记录数: {total}")

    # 已分类数量
    classified = db_session.query(CloudResource).filter(
        (CloudResource.category2 != None) &
        (CloudResource.category2 != '')
    ).count()
    logging.info(f"已分类: {classified}")

    # 未分类数量
    unclassified = db_session.query(CloudResource).filter(
        (CloudResource.category2 == None) |
        (CloudResource.category2 == '')
    ).count()
    logging.info(f"未分类: {unclassified}")

    # 电影数量
    movies = db_session.query(CloudResource).filter(
        CloudResource.category2 == "电影"
    ).count()
    logging.info(f"电影: {movies}")

    # 剧集数量
    dramas = db_session.query(CloudResource).filter(
        CloudResource.category2 == "剧集"
    ).count()
    logging.info(f"剧集: {dramas}")

    logging.info("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="使用豆包AI识别并更新cloud_resource表的category2字段"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="限制处理的记录数量（用于测试）"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制更新所有记录（包括已有category2的）"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="仅显示统计信息，不进行更新"
    )

    args = parser.parse_args()

    try:
        if args.stats:
            # 仅显示统计信息
            show_statistics()
        else:
            # 显示当前统计
            show_statistics()
            print()

            # 执行更新
            update_category2(limit=args.limit, force_update=args.force)

            # 显示更新后的统计
            print()
            show_statistics()

    except KeyboardInterrupt:
        logging.info("\n用户中断操作")
        sys.exit(0)
    except Exception as e:
        logging.error(f"发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # 清理数据库连接
        db_session.remove()
