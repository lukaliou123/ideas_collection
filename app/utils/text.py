"""
文本处理工具模块
"""
import re
import string
from typing import List, Set, Dict, Tuple, Optional
from difflib import SequenceMatcher

def normalize_text(text: str) -> str:
    """
    规范化文本：转小写，移除标点符号，清理多余空白
    
    Args:
        text: 原始文本
        
    Returns:
        规范化后的文本
    """
    if not text:
        return ""
    
    # 转换为小写
    text = text.lower()
    
    # 移除标点符号
    text = text.translate(str.maketrans('', '', string.punctuation))
    
    # 清理多余空白
    text = ' '.join(text.split())
    
    return text

def calculate_similarity(text1: str, text2: str) -> float:
    """
    计算两个文本之间的相似度
    
    Args:
        text1: 第一个文本
        text2: 第二个文本
        
    Returns:
        相似度，0-1之间的浮点数，1表示完全相同
    """
    # 使用SequenceMatcher计算相似度
    return SequenceMatcher(None, text1, text2).ratio()

def extract_keywords(text: str, max_words: int = 10) -> List[str]:
    """
    从文本中提取关键词
    
    Args:
        text: 要分析的文本
        max_words: 最大关键词数量
        
    Returns:
        关键词列表
    """
    # 简单实现：移除停用词并返回最常见的单词
    if not text:
        return []
    
    # 规范化文本
    normalized = normalize_text(text)
    
    # 英文常见停用词列表
    stop_words = {
        'a', 'an', 'the', 'and', 'or', 'but', 'if', 'because', 'as', 'what',
        'when', 'where', 'how', 'who', 'which', 'this', 'that', 'these', 'those',
        'then', 'just', 'so', 'than', 'such', 'both', 'through', 'about', 'for',
        'is', 'of', 'while', 'during', 'to', 'from', 'in', 'out', 'on', 'off',
        'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there',
        'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some',
        'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'too', 'very',
        'can', 'will', 'should', 'now', 'be', 'have', 'has', 'had', 'do', 'does',
        'did', 'doing', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'their',
        'your', 'my', 'his', 'her', 'its', 'our', 'am', 'are', 'was', 'were'
    }
    
    # 分词
    words = normalized.split()
    
    # 移除停用词
    filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
    
    # 计算词频
    word_counts = {}
    for word in filtered_words:
        word_counts[word] = word_counts.get(word, 0) + 1
    
    # 按频率排序并返回前N个单词
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    keywords = [word for word, _ in sorted_words[:max_words]]
    
    return keywords 