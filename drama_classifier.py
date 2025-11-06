#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
影视作品分类工具类
使用豆包AI识别作品是"电影"还是"剧集"
"""

import os
import re
import time
import logging
from typing import Optional, List, Dict, Tuple
from datetime import datetime

from llm_sdk import create_client, Message


class DramaClassifier:
    """
    影视作品分类器
    使用豆包AI识别作品类型（电影/剧集）
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_id: Optional[str] = None,
        temperature: float = 0.3,
        sleep_interval: float = 1.0
    ):
        """
        初始化分类器

        Args:
            api_key: 豆包AI API Key，如果为None则从环境变量读取
            model_id: 豆包AI模型ID，如果为None则从环境变量读取
            temperature: 温度参数，控制输出稳定性（0-1），默认0.3
            sleep_interval: 批量处理时的请求间隔（秒），默认1秒
        """
        self.api_key = api_key or os.environ.get("ARK_API_KEY")
        self.model_id = model_id or os.environ.get("ARK_MODEL_ID")
        self.temperature = temperature
        self.sleep_interval = sleep_interval

        # 验证配置
        if not self.api_key:
            raise ValueError(
                "ARK_API_KEY 未设置。请通过参数传入或设置环境变量: "
                "export ARK_API_KEY='your-api-key'"
            )

        if not self.model_id:
            raise ValueError(
                "ARK_MODEL_ID 未设置。请通过参数传入或设置环境变量: "
                "export ARK_MODEL_ID='your-model-id'"
            )

        # 创建客户端
        self.client = create_client(
            platform="ark",
            api_key=self.api_key
        )

        # 分类提示词
        self.system_prompt = """你是一个专业的影视作品分类专家。
你的任务是判断给定的作品名称属于"电影"还是"剧集"（包括电视剧、网剧、综艺、动漫剧等）。

判断规则：
1. 电影：通常是单部完整的影视作品，时长在90-180分钟左右
2. 剧集：包括电视剧、网剧、动漫、综艺节目等，有多集内容

请只回复"电影"或"剧集"，不要输出其他内容。"""

        # 统计信息
        self._stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "movie": 0,
            "drama": 0
        }

    def classify(self, drama_name: str, retry: int = 1) -> Optional[str]:
        """
        分类单个作品

        Args:
            drama_name: 作品名称
            retry: 失败重试次数，默认1次

        Returns:
            "电影" 或 "剧集"，识别失败返回 None
        """
        for attempt in range(retry + 1):
            try:
                user_prompt = f'请判断以下作品属于"电影"还是"剧集"：\n\n作品名：{drama_name}'

                # 调用豆包AI
                response = self.client.simple_chat(
                    prompt=user_prompt,
                    system_prompt=self.system_prompt,
                    model=self.model_id,
                    temperature=self.temperature
                )

                # 清理响应
                result = response.strip()

                # 判断返回结果
                category = self._parse_result(result)

                if category:
                    self._update_stats(category)
                    logging.debug(f"✓ '{drama_name}' 识别为: {category}")
                    return category
                else:
                    logging.warning(
                        f"无法明确识别'{drama_name}'的类型，AI返回: {result}"
                    )
                    if attempt < retry:
                        logging.info(f"第 {attempt + 1}/{retry} 次重试...")
                        time.sleep(1)
                        continue
                    return None

            except Exception as e:
                logging.error(f"识别'{drama_name}'时出错: {str(e)}")
                if attempt < retry:
                    logging.info(f"第 {attempt + 1}/{retry} 次重试...")
                    time.sleep(1)
                    continue
                return None

        return None


    def classify_with_confidence(
        self,
        drama_name: str
    ) -> Tuple[Optional[str], float]:
        """
        分类并返回置信度（通过多次查询取一致结果）

        Args:
            drama_name: 作品名称

        Returns:
            (分类结果, 置信度)，置信度为0-1之间的值
        """
        # 查询3次
        results = []
        for _ in range(3):
            result = self.classify(drama_name)
            if result:
                results.append(result)
            time.sleep(0.5)

        if not results:
            return None, 0.0

        # 统计最多的结果
        movie_count = results.count("电影")
        drama_count = results.count("剧集")

        if movie_count > drama_count:
            confidence = movie_count / len(results)
            return "电影", confidence
        else:
            confidence = drama_count / len(results)
            return "剧集", confidence

    def extract_drama_name(self, resource_name: str, retry: int = 1) -> Optional[str]:
        """
        从资源名称中提取影视作品名称

        Args:
            resource_name: 资源名称（可能包含季数、画质、年份等信息）
            retry: 失败重试次数，默认1次

        Returns:
            提取的影视作品名称，提取失败返回原始输入
        """
        extract_system_prompt = """你是一个专业影视资源分析助手，我提供你一个命名不是很规范的资源名称，你需要分析这个资源是否是影视资源，如果是，你需要返回影视资源的名称(要求只输出名称，不要带任何其他符号，不要带季数，画质，年份等其他信息)，如果不是影视资源，固定输出用户的输入，严格按照我的要求"""

        for attempt in range(retry + 1):
            try:
                user_prompt = f'请提取以下资源的影视作品名称：\n\n资源名：{resource_name}'

                # 调用豆包AI
                response = self.client.simple_chat(
                    prompt=user_prompt,
                    system_prompt=extract_system_prompt,
                    model=self.model_id,
                    temperature=self.temperature
                )

                # 清理响应
                result = response.strip()

                if result:
                    logging.debug(f"✓ 从'{resource_name}'提取剧名: {result}")
                    return result
                else:
                    logging.warning(f"无法提取'{resource_name}'的剧名，AI返回为空")
                    if attempt < retry:
                        logging.info(f"第 {attempt + 1}/{retry} 次重试...")
                        time.sleep(1)
                        continue
                    return resource_name

            except Exception as e:
                logging.error(f"提取'{resource_name}'的剧名时出错: {str(e)}")
                if attempt < retry:
                    logging.info(f"第 {attempt + 1}/{retry} 次重试...")
                    time.sleep(1)
                    continue
                return resource_name

        return resource_name

    def get_hot_movies(self, max_count: int = 10, exclude_names: List[str] = None) -> List[str]:
        """
        使用豆包AI获取最近热门的流媒体电影资源列表

        Args:
            max_count: 最多返回电影数量，默认10部
            exclude_names: 需要排除的电影名称列表，默认None

        Returns:
            电影名称列表
        """
        try:
            logging.info("🤖 正在使用豆包AI收集热门资源...")

            # 构建排除列表字符串
            exclude_str = ""
            if exclude_names:
                exclude_str = f"\n6. 避免重复，且不要包含以下电影名称：{','.join(exclude_names)}"

            # 构建提示词
            current_date = datetime.now().strftime("%Y年%m月")
            prompt = f"""请帮我整理{current_date}最近热门的流媒体电影资源，要求：

1. 优先选择热度较高的资源（例如在豆瓣、IMDb等平台上有较高评分的电影）
2. 优先选择电影院已下映、流媒体已上映的电影
3. 优先选择续作的前作资源（例如如果有《XX 2》上映，优先收集《XX 1》）
4. 只返回电影，不要剧集
5. 返回{max_count}部电影即可{exclude_str}

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

            response = self.client.chat_completion(
                messages=messages,
                model=self.model_id,
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

            # 限制最多max_count部
            movies = movies[:max_count]

            logging.info(f"✅ 成功获取 {len(movies)} 部电影:")
            for i, movie in enumerate(movies, 1):
                logging.info(f"  {i}. {movie}")

            return movies

        except Exception as e:
            logging.error(f"❌ AI 收集失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

    def _parse_result(self, result: str) -> Optional[str]:
        """
        解析AI返回结果

        Args:
            result: AI返回的原始文本

        Returns:
            "电影" 或 "剧集"，无法识别返回 None
        """
        if "电影" in result and "剧集" not in result:
            return "电影"
        elif "剧集" in result and "电影" not in result:
            return "剧集"
        elif "电视剧" in result or "网剧" in result or "动漫" in result or "综艺" in result:
            return "剧集"
        else:
            return None

    def _update_stats(self, category: str):
        """
        更新统计信息

        Args:
            category: 分类结果（"电影" 或 "剧集"）
        """
        self._stats["total"] += 1
        self._stats["success"] += 1

        if category == "电影":
            self._stats["movie"] += 1
        elif category == "剧集":
            self._stats["drama"] += 1

    def get_stats(self) -> Dict[str, int]:
        """
        获取统计信息

        Returns:
            包含统计数据的字典
        """
        return self._stats.copy()

    def reset_stats(self):
        """重置统计信息"""
        self._stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "movie": 0,
            "drama": 0
        }


# 全局单例
_classifier_instance: Optional[DramaClassifier] = None


def get_classifier(
    api_key: Optional[str] = None,
    model_id: Optional[str] = None,
    force_new: bool = False
) -> DramaClassifier:
    """
    获取分类器单例

    Args:
        api_key: API Key，如果为None则使用环境变量
        model_id: 模型ID，如果为None则使用环境变量
        force_new: 是否强制创建新实例，默认False

    Returns:
        DramaClassifier 实例
    """
    global _classifier_instance

    if force_new or _classifier_instance is None:
        _classifier_instance = DramaClassifier(
            api_key=api_key,
            model_id=model_id
        )

    return _classifier_instance


# 便捷函数
def classify_drama(drama_name: str, **kwargs) -> Optional[str]:
    """
    分类单个作品（便捷函数）

    Args:
        drama_name: 作品名称
        **kwargs: 传递给 DramaClassifier 的参数

    Returns:
        "电影" 或 "剧集"，识别失败返回 None
    """
    classifier = get_classifier(**kwargs)
    return classifier.classify(drama_name)


def extract_drama_name(resource_name: str, **kwargs) -> Optional[str]:
    """
    从资源名称中提取影视作品名称（便捷函数）

    Args:
        resource_name: 资源名称（可能包含季数、画质、年份等信息）
        **kwargs: 传递给 DramaClassifier 的参数

    Returns:
        提取的影视作品名称，提取失败返回原始输入
    """
    classifier = get_classifier(**kwargs)
    return classifier.extract_drama_name(resource_name)

