#!/usr/bin/env python
"""
数据迁移脚本：从 SQLite 迁移到 PostgreSQL

使用方法：
    python scripts/migrate_to_postgresql.py --source sqlite:///./data/app.db --target postgresql://user:pass@host:5432/dbname

注意：
    1. 运行前请确保已安装 psycopg2-binary: pip install psycopg2-binary
    2. 建议先备份 SQLite 数据库
    3. 目标 PostgreSQL 数据库应该已经创建但表为空
"""

import argparse
import sys
import os
from datetime import datetime
from sqlalchemy import create_engine, inspect, MetaData, Table
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.base import Base
from app.models.sources import Source
from app.models.posts import Post
from app.models.products import Product
from app.models.tag import Tag, TagCategory
from app.models.associations import product_tags


def create_connection(database_url: str):
    """创建数据库连接"""
    try:
        if database_url.startswith("sqlite"):
            engine = create_engine(database_url, connect_args={"check_same_thread": False})
        else:
            engine = create_engine(
                database_url,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10
            )
        return engine
    except Exception as e:
        print(f"❌ 连接数据库失败: {e}")
        sys.exit(1)


def verify_source_db(engine):
    """验证源数据库"""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    required_tables = ['sources', 'posts', 'products']
    missing_tables = [t for t in required_tables if t not in tables]
    
    if missing_tables:
        print(f"❌ 源数据库缺少表: {', '.join(missing_tables)}")
        return False
    
    print(f"✅ 源数据库验证成功，找到 {len(tables)} 个表")
    return True


def create_target_schema(engine):
    """在目标数据库中创建表结构"""
    try:
        print("📋 创建目标数据库表结构...")
        Base.metadata.create_all(bind=engine)
        print("✅ 表结构创建成功")
        return True
    except Exception as e:
        print(f"❌ 创建表结构失败: {e}")
        return False


def count_records(session: Session, model):
    """统计记录数"""
    try:
        return session.query(model).count()
    except:
        return 0


def migrate_table(source_session: Session, target_session: Session, model, model_name: str):
    """迁移单个表的数据"""
    try:
        print(f"\n📦 开始迁移 {model_name}...")
        
        # 获取源数据
        records = source_session.query(model).all()
        total = len(records)
        
        if total == 0:
            print(f"   ℹ️  {model_name} 表为空，跳过")
            return True
        
        print(f"   发现 {total} 条记录")
        
        # 批量插入目标数据库
        batch_size = 100
        success_count = 0
        
        for i in range(0, total, batch_size):
            batch = records[i:i + batch_size]
            try:
                # 为每个记录创建一个新的实例，避免session冲突
                for record in batch:
                    # 获取记录的所有列值
                    record_dict = {
                        column.name: getattr(record, column.name)
                        for column in record.__table__.columns
                    }
                    
                    # 创建新实例并添加到目标session
                    new_record = model(**record_dict)
                    target_session.merge(new_record)
                
                target_session.commit()
                success_count += len(batch)
                print(f"   进度: {success_count}/{total} ({success_count*100//total}%)")
                
            except Exception as e:
                target_session.rollback()
                print(f"   ⚠️  批次 {i//batch_size + 1} 失败: {e}")
                # 尝试逐条插入
                for record in batch:
                    try:
                        record_dict = {
                            column.name: getattr(record, column.name)
                            for column in record.__table__.columns
                        }
                        new_record = model(**record_dict)
                        target_session.merge(new_record)
                        target_session.commit()
                        success_count += 1
                    except Exception as e2:
                        target_session.rollback()
                        print(f"   ⚠️  记录迁移失败: {e2}")
        
        print(f"✅ {model_name} 迁移完成: {success_count}/{total} 条记录")
        return True
        
    except Exception as e:
        print(f"❌ {model_name} 迁移失败: {e}")
        target_session.rollback()
        return False


def migrate_many_to_many(source_session: Session, target_session: Session):
    """迁移多对多关系表"""
    try:
        print(f"\n📦 开始迁移 product_tags 关联关系...")
        
        # 使用原始SQL查询关联表
        source_engine = source_session.get_bind()
        
        # 检查表是否存在
        inspector = inspect(source_engine)
        if 'product_tags' not in inspector.get_table_names():
            print(f"   ℹ️  product_tags 表不存在，跳过")
            return True
        
        result = source_engine.execute("SELECT * FROM product_tags")
        records = result.fetchall()
        
        if not records:
            print(f"   ℹ️  product_tags 表为空，跳过")
            return True
        
        print(f"   发现 {len(records)} 条关联记录")
        
        # 批量插入
        target_engine = target_session.get_bind()
        success_count = 0
        
        for record in records:
            try:
                target_engine.execute(
                    product_tags.insert().values(
                        product_id=record[0],
                        tag_id=record[1]
                    )
                )
                success_count += 1
            except Exception as e:
                print(f"   ⚠️  关联记录插入失败: {e}")
        
        target_session.commit()
        print(f"✅ product_tags 迁移完成: {success_count}/{len(records)} 条记录")
        return True
        
    except Exception as e:
        print(f"❌ product_tags 迁移失败: {e}")
        target_session.rollback()
        return False


def verify_migration(source_session: Session, target_session: Session):
    """验证迁移结果"""
    print("\n🔍 验证迁移结果...")
    
    models = [
        (Source, "sources"),
        (Post, "posts"),
        (Product, "products"),
        (Tag, "tags"),
        (TagCategory, "tag_categories"),
    ]
    
    all_match = True
    
    for model, name in models:
        source_count = count_records(source_session, model)
        target_count = count_records(target_session, model)
        
        status = "✅" if source_count == target_count else "⚠️"
        print(f"   {status} {name}: 源={source_count}, 目标={target_count}")
        
        if source_count != target_count:
            all_match = False
    
    return all_match


def main():
    parser = argparse.ArgumentParser(description="将数据从 SQLite 迁移到 PostgreSQL")
    parser.add_argument(
        "--source",
        default="sqlite:///./data/app.db",
        help="源数据库 URL (默认: sqlite:///./data/app.db)"
    )
    parser.add_argument(
        "--target",
        required=True,
        help="目标 PostgreSQL 数据库 URL (例如: postgresql://user:pass@host:5432/dbname)"
    )
    parser.add_argument(
        "--skip-verify",
        action="store_true",
        help="跳过迁移后的验证步骤"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🚀 数据库迁移工具 - SQLite to PostgreSQL")
    print("=" * 60)
    print(f"\n源数据库: {args.source}")
    print(f"目标数据库: {args.target.split('@')[1] if '@' in args.target else args.target}")
    print()
    
    # 创建数据库连接
    print("📡 连接数据库...")
    source_engine = create_connection(args.source)
    target_engine = create_connection(args.target)
    
    # 验证源数据库
    if not verify_source_db(source_engine):
        sys.exit(1)
    
    # 创建目标数据库表结构
    if not create_target_schema(target_engine):
        sys.exit(1)
    
    # 创建会话
    SourceSession = sessionmaker(bind=source_engine)
    TargetSession = sessionmaker(bind=target_engine)
    
    source_session = SourceSession()
    target_session = TargetSession()
    
    try:
        # 迁移数据（注意迁移顺序，遵循外键依赖）
        migration_steps = [
            (Source, "sources"),
            (TagCategory, "tag_categories"),
            (Tag, "tags"),
            (Post, "posts"),
            (Product, "products"),
        ]
        
        for model, name in migration_steps:
            if not migrate_table(source_session, target_session, model, name):
                print(f"\n❌ 迁移在 {name} 步骤失败")
                sys.exit(1)
        
        # 迁移多对多关系
        if not migrate_many_to_many(source_session, target_session):
            print(f"\n❌ 关联关系迁移失败")
            sys.exit(1)
        
        # 验证迁移
        if not args.skip_verify:
            if verify_migration(source_session, target_session):
                print("\n✅ 迁移验证成功！所有记录数量匹配")
            else:
                print("\n⚠️  迁移完成，但部分表记录数量不匹配，请检查")
        
        print("\n" + "=" * 60)
        print("🎉 迁移完成！")
        print("=" * 60)
        print("\n下一步操作：")
        print("1. 更新 .env 文件中的 DATABASE_URL 为新的 PostgreSQL 连接")
        print("2. 测试应用是否能正常连接和运行")
        print("3. 备份原 SQLite 数据库文件")
        print()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  迁移被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 迁移过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        source_session.close()
        target_session.close()


if __name__ == "__main__":
    main()

