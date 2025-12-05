"""
定时更新股票列表任务
每天自动更新一次股票列表
"""

import schedule
import time
from backend.dataflows.akshare.stock_list_cache import get_stock_cache
from backend.utils.logging_config import get_logger

logger = get_logger("StockListUpdater")


def update_stock_list():
    """更新股票列表"""
    logger.info("开始定时更新股票列表...")
    cache = get_stock_cache()
    success = cache.update_stock_list()
    if success:
        logger.info("✅ 股票列表更新成功")
    else:
        logger.error("❌ 股票列表更新失败")


def run_scheduler():
    """运行定时任务"""
    # 每天凌晨2点更新
    schedule.every().day.at("02:00").do(update_stock_list)
    
    logger.info("✅ 股票列表定时更新任务已启动")
    logger.info("📅 更新时间: 每天凌晨2:00")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # 每分钟检查一次


if __name__ == "__main__":
    # 立即执行一次
    logger.info("首次启动，立即更新股票列表...")
    update_stock_list()
    
    # 启动定时任务
    run_scheduler()
