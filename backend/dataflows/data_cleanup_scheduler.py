"""
数据自动清理调度器
定期清理过期的历史数据
"""

import schedule
import time
import threading
from datetime import datetime

from backend.utils.logging_config import get_logger
from backend.database.database import get_db_context
from backend.dataflows.data_persistence import DataPersistenceManager

logger = get_logger("dataflow.cleanup")


class DataCleanupScheduler:
    """数据清理调度器"""
    
    def __init__(self):
        self.running = False
        self.thread = None
        logger.info("💧 数据清理调度器初始化")
    
    def cleanup_job(self):
        """清理任务"""
        try:
            logger.info("🧹 开始执行数据清理任务...")
            
            with get_db_context() as db:
                result = DataPersistenceManager.batch_clean_all_stocks(db)
                
            logger.info(f"✅ 清理完成: 数据{result['data']}条, 新闻{result['news']}条")
            
        except Exception as e:
            logger.error(f"❌ 清理任务失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def run_scheduler(self):
        """运行调度器（在后台线程中）"""
        logger.info("▶️ 清理调度器启动")
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次
        logger.info("⏹️ 清理调度器停止")
    
    def start(self):
        """启动调度器"""
        if self.running:
            logger.warning("清理调度器已在运行")
            return
        
        # 配置定时任务：每天凌晨2点执行
        schedule.every().day.at("02:00").do(self.cleanup_job)
        
        # 也可以每6小时执行一次（可选）
        # schedule.every(6).hours.do(self.cleanup_job)
        
        self.running = True
        self.thread = threading.Thread(target=self.run_scheduler, daemon=True)
        self.thread.start()
        
        logger.info("🚀 数据清理调度器已启动 (每天02:00执行)")
    
    def stop(self):
        """停止调度器"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("⏹️ 数据清理调度器已停止")
    
    def run_now(self):
        """立即执行一次清理"""
        logger.info("⚡ 手动触发清理任务")
        self.cleanup_job()


# 全局调度器实例
_scheduler = None


def get_cleanup_scheduler() -> DataCleanupScheduler:
    """获取清理调度器实例（单例）"""
    global _scheduler
    if _scheduler is None:
        _scheduler = DataCleanupScheduler()
    return _scheduler


def start_cleanup_scheduler():
    """启动清理调度器（便捷函数）"""
    scheduler = get_cleanup_scheduler()
    scheduler.start()


def stop_cleanup_scheduler():
    """停止清理调度器（便捷函数）"""
    scheduler = get_cleanup_scheduler()
    scheduler.stop()


if __name__ == "__main__":
    # 测试清理调度器
    logger.info("测试数据清理调度器")
    
    scheduler = get_cleanup_scheduler()
    
    # 立即执行一次
    scheduler.run_now()
    
    # 启动定时调度
    scheduler.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.stop()
        logger.info("退出测试")
