"""
模型导入集合文件
在此处导入所有模型，确保Alembic能够识别所有模型
"""
# 必须首先导入基类
from backend.app.db.base_class import Base

# 导入所有模型以便Alembic识别
from backend.app.models.associations import product_tag_association  # noqa
from backend.app.models.tag import Tag, TagCategory  # noqa
from backend.app.models.product import Product  # noqa 