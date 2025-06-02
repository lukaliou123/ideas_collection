"""
标签管理脚本

提供命令行工具来管理标签，包括：
- 填充现有标签的normalized_name字段
- 自动合并相似度高的标签
"""
import sys
import os
import argparse

# 添加项目根目录到Python路径
# 注意：这里的路径可能需要根据实际项目结构调整
# 假设脚本位于 project_root/scripts/
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.append(project_root)
    print(f"Added {project_root} to sys.path")

try:
    from app.core.database import SessionLocal
    # 确保可以导入 TagService，如果路径不同需要调整
    from app.services.tag_service import TagService 
    from app.utils.logger import logger # 假设有logger
except ImportError as e:
    print(f"Import Error: {e}")
    print("Please ensure the script is run from the project root or adjust sys.path.")
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Manage tags in the database.")
    
    parser.add_argument(
        "--populate-normalized",
        action="store_true",
        help="Populate the normalized_name field for all existing tags that lack it."
    )
    
    parser.add_argument(
        "--auto-merge",
        action="store_true",
        help="Automatically find and merge highly similar tags."
    )
    
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.70,
        help="Similarity threshold (0.0 to 1.0) for auto-merging. Default: 0.90"
    )

    args = parser.parse_args()

    if not args.populate_normalized and not args.auto_merge:
        parser.print_help()
        print("\nError: Please specify an action (--populate-normalized or --auto-merge).")
        sys.exit(1)

    if args.threshold < 0.0 or args.threshold > 1.0:
        print(f"Error: Threshold must be between 0.0 and 1.0. Got: {args.threshold}")
        sys.exit(1)

    logger.info("Initializing Tag Management Script...")
    db = SessionLocal()
    try:
        if args.populate_normalized:
            logger.info("Starting: Populate normalized names for existing tags...")
            count = TagService.populate_normalized_names_for_existing_tags(db)
            logger.info(f"Finished: Populated/merged {count} tags.")
            
        if args.auto_merge:
            logger.info(f"Starting: Auto-merge similar tags with threshold >= {args.threshold}...")
            result = TagService.auto_merge_similar_tags(db, threshold=args.threshold)
            logger.info(f"Finished: Auto-merged {result.get('merged_count', 0)} tags.")
            
    except Exception as e:
        logger.error(f"An error occurred during tag management: {e}", exc_info=True)
        db.rollback() # Rollback on any error
    finally:
        logger.info("Closing database session.")
        db.close()

if __name__ == "__main__":
    main()
