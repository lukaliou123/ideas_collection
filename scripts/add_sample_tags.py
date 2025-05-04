"""
添加示例标签脚本
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.models.tags import Tag

def add_sample_tags():
    """添加一组示例标签"""
    db = SessionLocal()
    try:
        # 检查是否已存在标签
        if db.query(Tag).count() > 0:
            print("标签已存在，跳过添加。")
            return
        
        # 创建常用产品标签
        tags = [
            # 产品类型
            Tag(name="SaaS"),
            Tag(name="工具"),
            Tag(name="API"),
            Tag(name="移动应用"),
            Tag(name="桌面应用"),
            Tag(name="网站"),
            Tag(name="浏览器扩展"),
            Tag(name="开源项目"),
            
            # 技术领域
            Tag(name="人工智能"),
            Tag(name="机器学习"),
            Tag(name="数据分析"),
            Tag(name="区块链"),
            Tag(name="云计算"),
            Tag(name="安全"),
            Tag(name="开发工具"),
            
            # 目标市场
            Tag(name="B2B"),
            Tag(name="B2C"),
            Tag(name="企业级"),
            Tag(name="个人用户"),
            Tag(name="开发者"),
            
            # 产品状态
            Tag(name="原型"),
            Tag(name="测试版"),
            Tag(name="正式版"),
            
            # 商业模式
            Tag(name="免费"),
            Tag(name="订阅制"),
            Tag(name="一次性付费"),
            Tag(name="开源")
        ]
        
        # 添加到数据库
        db.add_all(tags)
        db.commit()
        
        print(f"成功添加 {len(tags)} 个标签。")
    finally:
        db.close()

if __name__ == "__main__":
    add_sample_tags() 