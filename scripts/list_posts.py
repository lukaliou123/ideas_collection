"""
列出已收集的帖子脚本
"""
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.models.posts import Post

def list_posts():
    """列出已收集的帖子"""
    db = SessionLocal()
    try:
        posts = db.query(Post).order_by(Post.collected_at.desc()).all()
        
        print(f"\n找到 {len(posts)} 条帖子:\n")
        for post in posts:
            print(f"标题: {post.title}")
            print(f"来源: {post.source.name}")
            print(f"作者: {post.author}")
            print(f"发布时间: {post.published_at}")
            print(f"分数: {post.points}")
            print(f"评论数: {post.comments_count}")
            print(f"URL: {post.url}")
            print(f"收集时间: {post.collected_at}")
            print("-" * 80)
    finally:
        db.close()

if __name__ == "__main__":
    list_posts() 