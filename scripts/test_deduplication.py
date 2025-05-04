"""
测试内容去重功能的脚本
"""
import sys
import os
import asyncio
from pprint import pprint

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.services.content_service import ContentService
from app.utils.text import normalize_text, calculate_similarity
from app.utils.logger import logger

async def test_url_normalization():
    """测试URL规范化功能"""
    print("\n测试URL规范化功能:")
    
    test_urls = [
        "https://example.com/path?utm_source=twitter&utm_medium=social",
        "https://example.com/path?fbclid=123456&ref=homepage",
        "https://example.com/path/?",
        "https://example.com/path#section1",
        "https://example.com/path/?utm_campaign=test&valid_param=keep"
    ]
    
    for url in test_urls:
        normalized = ContentService.normalize_url(url)
        print(f"原始URL: {url}")
        print(f"规范化后: {normalized}")
        print("-" * 50)

async def test_text_similarity():
    """测试文本相似度计算功能"""
    print("\n测试文本相似度计算功能:")
    
    test_pairs = [
        (
            "Show HN: My New Product - A tool for developers",
            "Show HN: My New Product - A developer tool"
        ),
        (
            "Show HN: A simple way to track expenses",
            "Show HN: An easy way to monitor your spending"
        ),
        (
            "Show HN: Use AI to analyze your code",
            "Introducing CodeAI - AI powered code analysis"
        ),
        (
            "Show HN: I built a new programming language",
            "Show HN: I built a new programming language"
        )
    ]
    
    for text1, text2 in test_pairs:
        norm1 = normalize_text(text1)
        norm2 = normalize_text(text2)
        similarity = calculate_similarity(norm1, norm2)
        
        print(f"文本1: {text1}")
        print(f"文本2: {text2}")
        print(f"相似度: {similarity:.4f}")
        print("-" * 50)

async def test_content_normalization():
    """测试内容规范化功能"""
    print("\n测试内容规范化功能:")
    
    test_post = {
        "title": "  Show HN: My Project  ",  # 多余空格
        "content": "\n\nThis is a test\n  project description.\n\n",  # 多余换行和空格
        "url": "https://example.com/?utm_source=test",  # 跟踪参数
        "points": None,  # 空值
        "comments_count": None  # 空值
    }
    
    print("原始数据:")
    pprint(test_post)
    
    normalized = ContentService.normalize_post_data("HackerNews", test_post)
    
    print("\n规范化后:")
    pprint(normalized)

async def test_duplicate_detection():
    """测试重复检测功能"""
    print("\n测试内容重复检测 (使用相似的标题):")
    
    db = SessionLocal()
    try:
        # 测试两个相似但不完全相同的标题
        title1 = "Show HN: A New Way to Build Web Applications"
        title2 = "Show HN: New Method for Building Web Apps"
        
        is_duplicate = await ContentService.is_duplicate_content(db, title1, "", 0.6)
        
        if is_duplicate:
            print(f"标题 '{title1}' 被检测为与数据库中的帖子重复")
        else:
            print(f"标题 '{title1}' 不是重复内容")
            
        # 添加第一个标题到数据库(模拟)，然后检测第二个标题
        print(f"\n检查标题 '{title2}' 与 '{title1}' 的相似度:")
        
        # 仅计算相似度而不添加到数据库
        normalized1 = normalize_text(title1)
        normalized2 = normalize_text(title2)
        similarity = calculate_similarity(normalized1, normalized2)
        
        print(f"相似度: {similarity:.4f}")
        if similarity > 0.6:
            print("根据相似度阈值 0.6，这些标题被认为是相似的")
        else:
            print("根据相似度阈值 0.6，这些标题不被认为是相似的")
            
    finally:
        db.close()

async def run_tests():
    """运行所有测试"""
    await test_url_normalization()
    await test_text_similarity()
    await test_content_normalization()
    await test_duplicate_detection()

if __name__ == "__main__":
    asyncio.run(run_tests()) 