#!/usr/bin/env python
"""
简单的应用监控脚本
运行此脚本可以检查应用的状态、数据库统计信息，并生成基本的监控报告
"""
import sys
import os
import time
import sqlite3
import argparse
import requests
from datetime import datetime, timedelta
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def get_db_path():
    """获取数据库路径"""
    # 默认数据库位置
    default_path = os.path.join(os.getcwd(), "app.db")
    
    # 尝试从环境变量获取
    db_url = os.environ.get("DATABASE_URL", "")
    if db_url.startswith("sqlite:///"):
        path = db_url.replace("sqlite:///", "")
        if path.startswith("./"):
            path = path[2:]
        return os.path.join(os.getcwd(), path)
    
    return default_path

def check_api_health(base_url="http://localhost:8000"):
    """检查API健康状态"""
    try:
        response = requests.get(f"{base_url}/api", timeout=5)
        if response.status_code == 200:
            logger.info(f"✅ API响应正常: {response.status_code}")
            return True
        else:
            logger.error(f"❌ API响应异常: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ 无法连接到API: {e}")
        return False

def get_db_stats():
    """获取数据库统计信息"""
    db_path = get_db_path()
    
    if not os.path.exists(db_path):
        logger.error(f"❌ 数据库文件不存在: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取表总数
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        logger.info(f"📊 数据库包含 {len(tables)} 个表")
        
        # 获取各表的行数
        stats = {}
        for table in tables:
            table_name = table[0]
            if table_name.startswith("sqlite_"):
                continue
            
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            stats[table_name] = count
        
        # 显示统计信息
        for table, count in stats.items():
            logger.info(f"  - {table}: {count} 行")
        
        # 获取最近收集的帖子
        try:
            cursor.execute("""
                SELECT COUNT(*) FROM posts 
                WHERE collected_at > datetime('now', '-1 day');
            """)
            recent_posts = cursor.fetchone()[0]
            logger.info(f"📈 过去24小时内收集了 {recent_posts} 个帖子")
        except:
            pass
        
        # 获取未处理的帖子数量
        try:
            cursor.execute("SELECT COUNT(*) FROM posts WHERE processed = 0;")
            unprocessed = cursor.fetchone()[0]
            logger.info(f"⏳ 当前有 {unprocessed} 个帖子待处理")
        except:
            pass
        
        conn.close()
        return stats
    except Exception as e:
        logger.error(f"❌ 读取数据库时出错: {e}")
        return None

def check_system_resources():
    """检查系统资源使用情况"""
    try:
        import psutil
        
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        logger.info(f"🖥️ CPU使用率: {cpu_percent}%")
        
        # 内存使用情况
        memory = psutil.virtual_memory()
        mem_percent = memory.percent
        mem_used_gb = memory.used / (1024 ** 3)
        mem_total_gb = memory.total / (1024 ** 3)
        logger.info(f"💾 内存使用: {mem_percent}% ({mem_used_gb:.2f}GB/{mem_total_gb:.2f}GB)")
        
        # 磁盘使用情况
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        disk_used_gb = disk.used / (1024 ** 3)
        disk_total_gb = disk.total / (1024 ** 3)
        logger.info(f"💽 磁盘使用: {disk_percent}% ({disk_used_gb:.2f}GB/{disk_total_gb:.2f}GB)")
        
        return {
            "cpu_percent": cpu_percent,
            "mem_percent": mem_percent,
            "disk_percent": disk_percent
        }
    except ImportError:
        logger.warning("⚠️ 未安装psutil模块，无法获取系统资源信息")
        logger.info("  安装命令: pip install psutil")
        return None
    except Exception as e:
        logger.error(f"❌ 获取系统资源信息时出错: {e}")
        return None

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="创业产品信息收集系统监控工具")
    parser.add_argument("--url", default="http://localhost:8000", help="应用基础URL")
    parser.add_argument("--db", default=None, help="数据库文件路径")
    parser.add_argument("--no-api", action="store_true", help="跳过API健康检查")
    parser.add_argument("--no-resources", action="store_true", help="跳过系统资源检查")
    
    args = parser.parse_args()
    
    logger.info("=" * 50)
    logger.info("创业产品信息收集系统监控报告")
    logger.info(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)
    
    # 检查API健康状态
    if not args.no_api:
        api_healthy = check_api_health(args.url)
    
    # 获取数据库统计信息
    if args.db:
        os.environ["DATABASE_URL"] = f"sqlite:///{args.db}"
    db_stats = get_db_stats()
    
    # 检查系统资源
    if not args.no_resources:
        resources = check_system_resources()
    
    logger.info("=" * 50)
    logger.info("监控完成")

if __name__ == "__main__":
    main() 