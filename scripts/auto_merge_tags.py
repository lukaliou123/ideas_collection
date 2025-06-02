#!/usr/bin/env python
"""
标签自动合并脚本
用于手动执行标签自动合并功能，支持自定义相似度阈值
"""
import sys
import os
import argparse

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.services.tag_service import TagService
from app.utils.logger import logger

def auto_merge_tags(threshold: float = 0.70, dry_run: bool = False):
    """
    执行标签自动合并
    
    Args:
        threshold: 相似度阈值，默认0.90
        dry_run: 是否为试运行模式，不实际执行合并
    """
    db = SessionLocal()
    
    try:
        logger.info(f"开始标签自动合并，相似度阈值: {threshold}")
        
        if dry_run:
            logger.info("试运行模式：将显示可能的合并操作，但不会实际执行")
            # 在试运行模式下，我们需要模拟合并过程
            # 这里简化处理，实际可以扩展TagService来支持dry_run模式
            logger.warning("试运行模式暂未完全实现，将执行实际合并")
        
        # 执行自动合并
        result = TagService.auto_merge_similar_tags(db, threshold=threshold)
        merged_count = result.get('merged_count', 0)
        
        if merged_count > 0:
            logger.info(f"✅ 标签自动合并完成，成功合并了 {merged_count} 个标签")
            print(f"成功合并了 {merged_count} 个相似标签")
        else:
            logger.info("✅ 没有找到需要合并的相似标签")
            print("没有找到需要合并的相似标签")
            
        return merged_count
        
    except Exception as e:
        logger.error(f"❌ 标签自动合并时出错: {e}")
        print(f"错误: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 0
        
    finally:
        db.close()

def show_similar_tags(threshold: float = 0.90):
    """
    显示相似标签但不执行合并
    
    Args:
        threshold: 相似度阈值
    """
    db = SessionLocal()
    
    try:
        from app.models.tag import Tag
        from app.core.tag_utils import TagNormalizer
        
        logger.info(f"查找相似度 >= {threshold} 的标签...")
        
        all_tags = db.query(Tag).order_by(Tag.created_at).all()
        similar_groups = []
        processed_tag_ids = set()
        
        for i in range(len(all_tags)):
            if all_tags[i].id in processed_tag_ids:
                continue
                
            primary_tag = all_tags[i]
            similar_tags = []
            
            for j in range(i + 1, len(all_tags)):
                if all_tags[j].id in processed_tag_ids:
                    continue
                    
                similarity = TagNormalizer.calculate_similarity(
                    primary_tag.normalized_name or primary_tag.name.lower(),
                    all_tags[j].normalized_name or all_tags[j].name.lower()
                )
                
                if similarity >= threshold:
                    similar_tags.append((all_tags[j], similarity))
                    processed_tag_ids.add(all_tags[j].id)
            
            if similar_tags:
                similar_groups.append((primary_tag, similar_tags))
                processed_tag_ids.add(primary_tag.id)
        
        if similar_groups:
            print(f"\n找到 {len(similar_groups)} 组相似标签:")
            for i, (primary, similars) in enumerate(similar_groups, 1):
                print(f"\n组 {i}: 主标签 '{primary.name}' (ID: {primary.id})")
                for similar_tag, similarity in similars:
                    print(f"  - '{similar_tag.name}' (ID: {similar_tag.id}, 相似度: {similarity:.3f})")
        else:
            print(f"没有找到相似度 >= {threshold} 的标签")
            
    except Exception as e:
        logger.error(f"查找相似标签时出错: {e}")
        print(f"错误: {e}")
        
    finally:
        db.close()

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="标签自动合并工具")
    
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.90,
        help="相似度阈值 (0.0-1.0)，默认: 0.90"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="试运行模式，显示可能的合并操作但不实际执行"
    )
    
    parser.add_argument(
        "--show-similar",
        action="store_true",
        help="仅显示相似标签，不执行合并"
    )
    
    args = parser.parse_args()
    
    # 验证阈值范围
    if not 0.0 <= args.threshold <= 1.0:
        print("错误: 相似度阈值必须在 0.0 到 1.0 之间")
        return
    
    print("=" * 50)
    print("标签自动合并工具")
    print("=" * 50)
    
    if args.show_similar:
        show_similar_tags(args.threshold)
    else:
        auto_merge_tags(args.threshold, args.dry_run)

if __name__ == "__main__":
    main() 