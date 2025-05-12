from typing import List
import re
from difflib import SequenceMatcher

class TagNormalizer:
    @staticmethod
    def normalize_tag_name(tag_name: str) -> str:
        """
        标准化标签名称：
        1. 转换为小写
        2. 移除特殊字符
        3. 将多个空格替换为单个空格
        4. 移除首尾空格
        """
        # 转换为小写
        normalized = tag_name.lower()
        # 将特殊字符替换为空格
        normalized = re.sub(r'[^\w\s\-]', ' ', normalized)
        # 将连字符替换为空格
        normalized = normalized.replace('-', ' ')
        # 将多个空格替换为单个空格
        normalized = re.sub(r'\s+', ' ', normalized)
        # 移除首尾空格
        normalized = normalized.strip()
        return normalized

    @staticmethod
    def calculate_similarity(tag1: str, tag2: str) -> float:
        """
        计算两个标签名称的相似度
        返回0-1之间的相似度分数
        """
        return SequenceMatcher(None, tag1, tag2).ratio()

    @staticmethod
    def find_similar_tags(target_tag: str, tag_list: List[str], threshold: float = 0.85) -> List[str]:
        """
        在标签列表中查找与目标标签相似的标签
        threshold: 相似度阈值，默认0.85
        返回相似标签列表
        """
        normalized_target = TagNormalizer.normalize_tag_name(target_tag)
        similar_tags = []
        
        for tag in tag_list:
            normalized_tag = TagNormalizer.normalize_tag_name(tag)
            if normalized_target == normalized_tag:
                continue
            
            similarity = TagNormalizer.calculate_similarity(normalized_target, normalized_tag)
            if similarity >= threshold:
                similar_tags.append(tag)
                
        return similar_tags 