# -*- coding: utf-8 -*-
"""
新闻数据收集任务
定时运行，积累历史数据用于回测

Author: 臭宝
Date: 2026-02-19
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from backend.services.news_center.cninfo_crawler import get_cninfo_crawler
from backend.services.news_center.news_storage import get_news_storage, NewsArticle

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def collect_announcements():
    """收集公告数据"""
    logger.info("=" * 60)
    logger.info("开始收集公告数据...")
    logger.info("=" * 60)
    
    try:
        crawler = get_cninfo_crawler()
        storage = get_news_storage()
        
        # 获取今日公告
        announcements = crawler.fetch_by_date()
        logger.info(f"获取到 {len(announcements)} 条公告")
        
        if not announcements:
            logger.warning("没有获取到公告数据")
            return
        
        # 处理并保存
        processed = crawler.process_announcements(announcements)
        
        saved_count = 0
        for ann in processed:
            try:
                # 转换为NewsArticle并保存
                article = NewsArticle(
                    title=ann.title,
                    content=f"类型: {ann.announcement_type}",
                    source="巨潮资讯",
                    source_key="cninfo",
                    publish_time=ann.publish_date,  # 修正字段名
                    crawl_time=datetime.now().isoformat(),
                    priority=ann.priority,
                    category="announcement",
                    sub_category=ann.announcement_type,
                    sentiment=ann.sentiment,
                    sentiment_score=ann.sentiment_score,
                    related_stocks=json.dumps([ann.stock_code]),
                    url=ann.url
                )
                
                if storage.save_news(article):
                    saved_count += 1
                    
            except Exception as e:
                logger.error(f"保存公告失败: {e}")
                continue
        
        logger.info(f"✅ 成功保存 {saved_count}/{len(processed)} 条公告")
        
        # 统计高优先级
        p0_count = sum(1 for a in processed if a.priority == "P0")
        p1_count = sum(1 for a in processed if a.priority == "P1")
        p2_count = sum(1 for a in processed if a.priority == "P2")
        
        logger.info(f"优先级统计: P0={p0_count}, P1={p1_count}, P2={p2_count}")
        
        # 统计情绪
        pos_count = sum(1 for a in processed if a.sentiment == "positive")
        neg_count = sum(1 for a in processed if a.sentiment == "negative")
        neu_count = sum(1 for a in processed if a.sentiment == "neutral")
        
        logger.info(f"情绪统计: 正面={pos_count}, 负面={neg_count}, 中性={neu_count}")
        
    except Exception as e:
        logger.error(f"收集公告失败: {e}", exc_info=True)


def collect_historical_data(days: int = 30):
    """
    收集历史公告数据（用于回测）
    
    Args:
        days: 收集最近多少天的数据
    """
    logger.info(f"开始收集最近 {days} 天的历史数据...")
    
    crawler = get_cninfo_crawler()
    storage = get_news_storage()
    
    total_saved = 0
    
    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y%m%d')
        logger.info(f"收集 {date} 的数据...")
        
        try:
            announcements = crawler.fetch_by_date(date)
            if not announcements:
                continue
            
            processed = crawler.process_announcements(announcements)
            
            for ann in processed:
                try:
                    article = NewsArticle(
                        title=ann.title,
                        content=f"类型: {ann.announcement_type}",
                        source="巨潮资讯",
                        source_key="cninfo",
                        publish_time=ann.publish_date,  # 修正字段名
                        crawl_time=datetime.now().isoformat(),
                        priority=ann.priority,
                        category="announcement",
                        sub_category=ann.announcement_type,
                        sentiment=ann.sentiment,
                        sentiment_score=ann.sentiment_score,
                        related_stocks=json.dumps([ann.stock_code]),
                        url=ann.url
                    )
                    
                    if storage.save_news(article):
                        total_saved += 1
                        
                except Exception as e:
                    logger.error(f"保存历史数据失败: {e}")
                    continue
            
            logger.info(f"  {date}: 保存 {len(processed)} 条")
            
        except Exception as e:
            logger.error(f"收集 {date} 失败: {e}")
            continue
    
    logger.info(f"✅ 历史数据收集完成，共保存 {total_saved} 条")


def show_stats():
    """显示数据收集统计"""
    storage = get_news_storage()
    
    today = datetime.now().strftime('%Y-%m-%d')
    stats = storage.get_stats_by_date(today)
    
    logger.info("=" * 60)
    logger.info("今日数据收集统计")
    logger.info("=" * 60)
    logger.info(f"总新闻数: {stats.get('total', 0)}")
    logger.info(f"P0新闻: {stats.get('p0_count', 0)}")
    logger.info(f"P1新闻: {stats.get('p1_count', 0)}")
    logger.info(f"P2新闻: {stats.get('p2_count', 0)}")
    logger.info(f"正面情绪: {stats.get('positive_count', 0)}")
    logger.info(f"负面情绪: {stats.get('negative_count', 0)}")
    logger.info(f"中性情绪: {stats.get('neutral_count', 0)}")
    logger.info(f"平均情绪: {stats.get('avg_sentiment', 0)}")
    logger.info("=" * 60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='新闻数据收集工具')
    parser.add_argument('--collect', action='store_true', help='收集今日公告')
    parser.add_argument('--history', type=int, help='收集历史数据（天数）')
    parser.add_argument('--stats', action='store_true', help='显示统计')
    
    args = parser.parse_args()
    
    if args.history:
        collect_historical_data(args.history)
    elif args.collect:
        asyncio.run(collect_announcements())
    elif args.stats:
        show_stats()
    else:
        # 默认：收集今日数据
        asyncio.run(collect_announcements())
