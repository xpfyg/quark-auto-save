#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量匹配 TMDB 脚本
为所有未关联 tmdb 的 cloud_resource 数据匹配 TMDB 信息
"""
import os
import sys
import time
from datetime import datetime


class TmdbMatcher:
    """TMDB 批量匹配器"""

    def __init__(self, delay=1.0, batch_size=10):
        """
        初始化匹配器

        Args:
            delay: 请求间隔（秒），避免 API 限流，默认 1 秒
            batch_size: 批量处理大小，每处理 batch_size 条数据后提交一次，默认 10
        """
        # 延迟导入，避免在显示帮助信息时出现导入错误
        from resource_manager import TmdbService
        from db import db_session

        self.tmdb_service = TmdbService()
        self.db_session = db_session
        self.delay = delay
        self.batch_size = batch_size

        # 统计信息
        self.stats = {
            "total": 0,
            "skipped": 0,
            "matched": 0,
            "not_found": 0,
            "failed": 0
        }

    def match_all(self, limit=None, offset=0):
        """
        批量匹配所有未关联 TMDB 的资源

        Args:
            limit: 限制处理数量，None 表示处理所有
            offset: 跳过前 N 条记录，默认 0
        """
        # 延迟导入模型
        from model.cloud_resource import CloudResource

        print("=" * 60)
        print("🎬 开始批量匹配 TMDB 信息")
        print("=" * 60)
        print()

        # 查询所有未关联 TMDB 的资源，且 category2 不为空
        query = self.db_session.query(CloudResource).filter(
            CloudResource.tmdb_id.is_(None),
            CloudResource.category2.isnot(None),
            CloudResource.category2 != ''
        )

        # 应用 offset 和 limit
        if offset > 0:
            query = query.offset(offset)
            print(f"⏭  跳过前 {offset} 条记录")

        total_count = query.count()
        print(f"📊 查询到 {total_count} 条待匹配的记录")

        if limit:
            query = query.limit(limit)
            print(f"📝 本次处理 {min(limit, total_count)} 条记录")

        resources = query.all()

        if not resources:
            print("✅ 没有需要匹配的资源")
            return

        print()
        print(f"开始处理，每处理 {self.batch_size} 条提交一次...")
        print("-" * 60)
        print()

        # 批量处理
        batch_count = 0
        for idx, resource in enumerate(resources, 1):
            self.stats["total"] += 1

            print(f"[{idx}/{len(resources)}] 处理: {resource.drama_name}")
            print(f"    分类: {resource.category2}")

            try:
                # 匹配 TMDB
                success = self._match_single(resource)

                if success:
                    batch_count += 1

                    # 每处理 batch_size 条提交一次
                    if batch_count >= self.batch_size:
                        self.db_session.commit()
                        print(f"    💾 已提交 {batch_count} 条更新")
                        batch_count = 0

                # 请求间隔，避免 API 限流
                if idx < len(resources):
                    time.sleep(self.delay)

            except Exception as e:
                print(f"    ❌ 处理失败: {str(e)}")
                self.stats["failed"] += 1
                self.db_session.rollback()
                continue

            print()

        # 提交剩余的更新
        if batch_count > 0:
            try:
                self.db_session.commit()
                print(f"💾 提交剩余 {batch_count} 条更新")
            except Exception as e:
                print(f"❌ 提交失败: {str(e)}")
                self.db_session.rollback()

        # 输出统计信息
        self._print_stats()

    def _match_single(self, resource):
        """
        匹配单条资源的 TMDB 信息

        Args:
            resource: CloudResource 对象

        Returns:
            True: 成功匹配并更新
            False: 未匹配或跳过
        """
        # 延迟导入模型
        from model.tmdb import Tmdb

        # 检查 category2 是否为空
        if not resource.category2 or resource.category2.strip() == '':
            print(f"    ⏭  跳过: category2 为空")
            self.stats["skipped"] += 1
            return False

        # 查询 TMDB
        tmdb_data = self.tmdb_service.search_drama(
            resource.drama_name,
            category=resource.category2
        )

        if not tmdb_data:
            print(f"    📢 未找到 TMDB 信息")
            self.stats["not_found"] += 1
            return False

        # 检查 TMDB 是否已存在
        existing_tmdb = self.db_session.query(Tmdb).filter(
            Tmdb.title == tmdb_data["title"],
            Tmdb.year_released == tmdb_data["year_released"]
        ).first()

        if existing_tmdb:
            print(f"    ✅ TMDB 已存在: {existing_tmdb.title} ({existing_tmdb.year_released})")
            tmdb_id = existing_tmdb.id
        else:
            # 保存新的 TMDB 信息
            new_tmdb = Tmdb(**tmdb_data)
            self.db_session.add(new_tmdb)
            self.db_session.flush()  # 立即获取 ID
            tmdb_id = new_tmdb.id
            print(f"    ✅ 新增 TMDB: {new_tmdb.title} ({new_tmdb.year_released})")

        # 更新资源的 tmdb_id
        resource.tmdb_id = tmdb_id
        resource.update_time = datetime.now()

        self.stats["matched"] += 1
        print(f"    🔗 已关联 TMDB ID: {tmdb_id}")

        return True

    def _print_stats(self):
        """输出统计信息"""
        print()
        print("=" * 60)
        print("📊 匹配统计")
        print("=" * 60)
        print(f"总计处理:     {self.stats['total']:>6} 条")
        print(f"成功匹配:     {self.stats['matched']:>6} 条")
        print(f"未找到:       {self.stats['not_found']:>6} 条")
        print(f"跳过 (无分类): {self.stats['skipped']:>6} 条")
        print(f"失败:         {self.stats['failed']:>6} 条")
        print("=" * 60)

        # 计算成功率
        if self.stats["total"] > 0:
            success_rate = (self.stats["matched"] / self.stats["total"]) * 100
            print(f"成功率: {success_rate:.1f}%")
        print()


def main():
    """主函数"""
    # 延迟导入，避免在检查环境变量时就失败
    from dotenv import load_dotenv
    from db import init_db

    # 加载环境变量
    load_dotenv()

    # 检查 TMDB API Key
    if not os.environ.get("TMDB_API_KEY"):
        print("❌ 错误: TMDB_API_KEY 环境变量未设置")
        print("请在 .env 文件中添加: TMDB_API_KEY=your_api_key")
        sys.exit(1)

    # 初始化数据库
    if not init_db():
        print("❌ 数据库连接失败，程序退出")
        sys.exit(1)

    print()

    # 解析命令行参数
    limit = None
    offset = 0
    delay = 1.0
    batch_size = 10

    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
            print(f"限制处理数量: {limit}")
        except ValueError:
            print(f"⚠️  警告: 无效的 limit 参数 '{sys.argv[1]}'，将处理所有记录")

    if len(sys.argv) > 2:
        try:
            offset = int(sys.argv[2])
            print(f"跳过前 {offset} 条记录")
        except ValueError:
            print(f"⚠️  警告: 无效的 offset 参数 '{sys.argv[2]}'")

    if len(sys.argv) > 3:
        try:
            delay = float(sys.argv[3])
            print(f"请求间隔: {delay} 秒")
        except ValueError:
            print(f"⚠️  警告: 无效的 delay 参数 '{sys.argv[3]}'")

    if len(sys.argv) > 4:
        try:
            batch_size = int(sys.argv[4])
            print(f"批量提交大小: {batch_size}")
        except ValueError:
            print(f"⚠️  警告: 无效的 batch_size 参数 '{sys.argv[4]}'")

    print()

    # 创建匹配器并执行
    matcher = TmdbMatcher(delay=delay, batch_size=batch_size)

    try:
        matcher.match_all(limit=limit, offset=offset)
    except KeyboardInterrupt:
        print()
        print("⚠️  用户中断，正在保存已处理的数据...")
        try:
            matcher.db_session.commit()
            print("✅ 数据已保存")
        except Exception as e:
            print(f"❌ 保存失败: {str(e)}")
            matcher.db_session.rollback()
        matcher._print_stats()
    except Exception as e:
        print(f"❌ 发生错误: {str(e)}")
        matcher.db_session.rollback()
        matcher._print_stats()
        sys.exit(1)
    finally:
        matcher.db_session.close()


if __name__ == "__main__":
    # 显示使用说明
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print("=" * 60)
        print("批量匹配 TMDB 脚本")
        print("=" * 60)
        print()
        print("功能: 为所有未关联 TMDB 的 cloud_resource 数据匹配 TMDB 信息")
        print("     (自动跳过 category2 为空的数据)")
        print()
        print("用法:")
        print("  python3 batch_match_tmdb.py [limit] [offset] [delay] [batch_size]")
        print()
        print("参数:")
        print("  limit       - 限制处理数量 (可选，默认处理全部)")
        print("  offset      - 跳过前 N 条记录 (可选，默认 0)")
        print("  delay       - 请求间隔秒数 (可选，默认 1.0)")
        print("  batch_size  - 批量提交大小 (可选，默认 10)")
        print()
        print("示例:")
        print("  python3 batch_match_tmdb.py              # 处理所有记录")
        print("  python3 batch_match_tmdb.py 50           # 只处理 50 条")
        print("  python3 batch_match_tmdb.py 50 100       # 跳过前 100 条，处理 50 条")
        print("  python3 batch_match_tmdb.py 50 0 2.0     # 处理 50 条，间隔 2 秒")
        print("  python3 batch_match_tmdb.py 50 0 1.0 20  # 处理 50 条，每 20 条提交一次")
        print()
        print("环境变量要求:")
        print("  TMDB_API_KEY  - TMDB API 密钥 (必需)")
        print("  DB_USERNAME   - 数据库用户名 (必需)")
        print("  DB_PASSWORD   - 数据库密码 (必需)")
        print("  DB_HOST       - 数据库主机 (必需)")
        print("  DB_DATABASE   - 数据库名称 (必需)")
        print()
        sys.exit(0)

    main()
