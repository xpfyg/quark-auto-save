# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资源管理器使用示例
演示如何使用 ResourceManager 处理资源
"""
import os
import sys
from resource_manager import ResourceManager


def example_1():
    """示例1: 处理单个资源"""
    print("\n" + "="*60)
    print("示例1: 处理单个资源")
    print("="*60)

    # 从环境变量或配置文件读取cookie
    cookie = os.environ.get("QUARK_COOKIE", "")
    if not cookie:
        print("❌ 错误: 请设置环境变量 QUARK_COOKIE")
        print("   export QUARK_COOKIE='your_cookie_here'")
        return

    try:
        # 创建资源管理器
        manager = ResourceManager(cookie)

        # 处理资源
        drama_name = "斗罗大陆"
        share_link = "https://pan.quark.cn/s/xxxxx"
        savepath = "/动漫/斗罗大陆"

        result = manager.process_resource(drama_name, share_link, savepath)

        # 打印结果
        print_result(result)

    except Exception as e:
        print(f"❌ 错误: {str(e)}")


def example_2():
    """示例2: 批量处理多个资源"""
    print("\n" + "="*60)
    print("示例2: 批量处理多个资源")
    print("="*60)

    cookie = os.environ.get("QUARK_COOKIE", "")
    if not cookie:
        print("❌ 错误: 请设置环境变量 QUARK_COOKIE")
        return

    # 资源列表
    resources = [
        {
            "drama_name": "权力的游戏",
            "share_link": "https://pan.quark.cn/s/xxxxx1",
            "savepath": "/电视剧/权力的游戏"
        },
        {
            "drama_name": "绝命毒师",
            "share_link": "https://pan.quark.cn/s/xxxxx2",
            "savepath": "/电视剧/绝命毒师"
        },
        {
            "drama_name": "复仇者联盟",
            "share_link": "https://pan.quark.cn/s/xxxxx3",
            "savepath": "/电影/复仇者联盟"
        }
    ]

    try:
        manager = ResourceManager(cookie)

        # 批量处理
        for idx, resource in enumerate(resources, 1):
            print(f"\n--- 处理第 {idx}/{len(resources)} 个资源 ---")
            result = manager.process_resource(
                resource["drama_name"],
                resource["share_link"],
                resource["savepath"]
            )
            print_result(result)

    except Exception as e:
        print(f"❌ 错误: {str(e)}")


def example_3():
    """示例3: 仅查询已存在的资源"""
    print("\n" + "="*60)
    print("示例3: 查询已存在的资源")
    print("="*60)

    cookie = os.environ.get("QUARK_COOKIE", "")
    if not cookie:
        print("❌ 错误: 请设置环境变量 QUARK_COOKIE")
        return

    try:
        from db import db_session
        from model.cloud_resource import CloudResource
        from model.tmdb import Tmdb

        # 查询所有有效资源
        resources = db_session.query(CloudResource).filter(
            CloudResource.is_expired == 0
        ).all()

        print(f"\n找到 {len(resources)} 个有效资源:\n")

        for resource in resources:
            print(f"📺 {resource.drama_name}")
            print(f"   链接: {resource.link}")
            print(f"   热度: {resource.hot}")

            if resource.tmdb_id:
                tmdb = db_session.query(Tmdb).filter(Tmdb.id == resource.tmdb_id).first()
                if tmdb:
                    print(f"   TMDB: {tmdb.title} ({tmdb.year_released})")
                    print(f"   分类: {tmdb.category}")
            print()

    except Exception as e:
        print(f"❌ 错误: {str(e)}")


def example_4():
    """示例4: 从命令行参数读取"""
    print("\n" + "="*60)
    print("示例4: 从命令行参数读取")
    print("="*60)

    if len(sys.argv) < 3:
        print("用法: python example_usage.py <剧名> <分享链接> [保存路径]")
        print("示例: python example_usage.py '权力的游戏' 'https://pan.quark.cn/s/xxxxx' '/电视剧/权力的游戏'")
        return

    drama_name = sys.argv[1]
    share_link = sys.argv[2]
    savepath = sys.argv[3] if len(sys.argv) > 3 else f"/{drama_name}"

    cookie = os.environ.get("QUARK_COOKIE", "")
    if not cookie:
        print("❌ 错误: 请设置环境变量 QUARK_COOKIE")
        return

    try:
        manager = ResourceManager(cookie)
        result = manager.process_resource(drama_name, share_link, savepath)
        print_result(result)

    except Exception as e:
        print(f"❌ 错误: {str(e)}")


def print_result(result):
    """打印处理结果"""
    if result["status"] == "existing":
        print("\n✅ 资源已存在且有效")
        print(f"   ID: {result['resource']['id']}")
        print(f"   剧名: {result['resource']['drama_name']}")
        print(f"   热度: {result['resource']['hot']}")

    elif result["status"] == "saved":
        print("\n✅ 资源已成功转存并保存")
        print(f"   ID: {result['resource']['id']}")
        print(f"   剧名: {result['resource']['drama_name']}")

    else:
        print(f"\n❌ 处理失败: {result.get('message', '未知错误')}")
        return

    # 打印TMDB信息
    if result.get("tmdb"):
        tmdb = result["tmdb"]
        print(f"\n🎬 TMDB信息:")
        print(f"   标题: {tmdb['title']} ({tmdb['year_released']})")
        print(f"   分类: {tmdb['category']}")
        print(f"   描述: {tmdb['description'][:100]}..." if len(tmdb['description']) > 100 else f"   描述: {tmdb['description']}")
        if tmdb['poster_url']:
            print(f"   海报: {tmdb['poster_url']}")
    else:
        print("\n⚠️ 未找到TMDB信息")


def main():
    """主菜单"""
    print("\n" + "="*60)
    print("资源管理器使用示例")
    print("="*60)
    print("\n请选择示例:")
    print("1. 处理单个资源")
    print("2. 批量处理多个资源")
    print("3. 查询已存在的资源")
    print("4. 从命令行参数读取")
    print("0. 退出")

    choice = input("\n请输入选项 (0-4): ").strip()

    if choice == "1":
        example_1()
    elif choice == "2":
        example_2()
    elif choice == "3":
        example_3()
    elif choice == "4":
        example_4()
    elif choice == "0":
        print("再见!")
    else:
        print("无效选项")


if __name__ == "__main__":
    # 如果有命令行参数，直接执行示例4
    if len(sys.argv) > 1:
        example_4()
    else:
        # 否则显示菜单
        main()
