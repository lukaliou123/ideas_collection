import os
import sys
from sqlalchemy.orm import Session

# 将项目根目录添加到Python路径，以便导入应用模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal # 假设你的数据库引擎和SessionLocal在这里
from app.models.products import Product # 导入Product模型
from app.utils.logger import logger # 使用你的日志记录器

def clear_all_product_image_urls():
    db: Session = SessionLocal()
    try:
        logger.info("开始清除所有产品的 concept_image_url...")
        
        # 更新所有产品的 concept_image_url 为 None
        num_updated = db.query(Product).update({Product.concept_image_url: None}, synchronize_session=False)
        db.commit()
        
        logger.info(f"成功清除了 {num_updated} 个产品的 concept_image_url。")
        
    except Exception as e:
        db.rollback()
        logger.error(f"清除产品图片URL时发生错误: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # 可以在这里添加一些确认步骤，防止误操作
    confirm = input("你确定要清除所有产品记录中的 concept_image_url 吗？这将无法恢复！(yes/no): ")
    if confirm.lower() == 'yes':
        clear_all_product_image_urls()
    else:
        logger.info("操作已取消。") 