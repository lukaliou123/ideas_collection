"""
数据模型包
"""
from app.models.base import BaseModel
from app.models.sources import Source
from app.models.posts import Post
from app.models.products import Product
from app.models.tag import Tag
from app.models.tag import TagCategory
from app.models.associations import product_tag_association

# 在添加其他模型后从这里导入
# from app.models.products import Product, Tag, ProductTag
