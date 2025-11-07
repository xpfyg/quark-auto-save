#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资源搜索器
功能：搜索和评估资源质量
"""
import os
import re
import logging
import requests
from typing import List, Dict, Optional


class ResourceSearcher:
    """
    资源搜索器
    用于搜索资源和评估资源质量
    """

    def __init__(self, search_api_url: str = "http://127.0.0.1:8888/api/search"):
        """
        初始化资源搜索器

        Args:
            search_api_url: 搜索API地址
        """
        self.search_api_url = search_api_url

    def search_resources(self, keyword: str, cloud_types: List[str] = None) -> List[Dict]:
        """
        调用搜索接口检索资源

        Args:
            keyword: 搜索关键词（电影名）
            cloud_types: 云盘类型列表，默认为 ["quark"]

        Returns:
            资源列表
        """
        if cloud_types is None:
            cloud_types = ["quark"]

        try:
            params = {
                "kw": keyword,
                "res": "merge",
                "src": "all",
                "cloud_types": cloud_types
            }

            response = requests.get(self.search_api_url + "/api/search", params=params, timeout=30)
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

    def calculate_quality_score(self, note: str) -> int:
        """
        计算资源质量分数（基于标题/备注关键词）

        Args:
            note: 资源备注/标题

        Returns:
            质量分数，越高越好
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

    def sort_by_quality(self, resources: List[Dict]) -> List[Dict]:
        """
        按照质量排序资源

        Args:
            resources: 资源列表

        Returns:
            排序后的资源列表（从高到低）
        """
        # 为每个资源计算质量分数
        for resource in resources:
            resource['quality_score'] = self.calculate_quality_score(resource.get('note', ''))

        # 按分数降序排序
        sorted_resources = sorted(resources, key=lambda x: x['quality_score'], reverse=True)

        return sorted_resources

    def search_and_sort(self, keyword: str, cloud_types: List[str] = None) -> List[Dict]:
        """
        搜索资源并按质量排序（便捷方法）

        Args:
            keyword: 搜索关键词
            cloud_types: 云盘类型列表

        Returns:
            排序后的资源列表
        """
        resources = self.search_resources(keyword, cloud_types)
        if not resources:
            return []

        return self.sort_by_quality(resources)


# 全局单例
_searcher_instance: Optional[ResourceSearcher] = None


def get_searcher(search_api_url: str = None) -> ResourceSearcher:
    """
    获取搜索器单例

    Args:
        search_api_url: 搜索API地址，如果为None则使用默认值

    Returns:
        ResourceSearcher 实例
    """
    global _searcher_instance

    if _searcher_instance is None:
        if search_api_url:
            _searcher_instance = ResourceSearcher(search_api_url)
        else:

            _searcher_instance = ResourceSearcher(search_api_url = os.environ.get("SEARCH_API_URL", "http://127.0.0.1:8888/api/search"))

    return _searcher_instance
