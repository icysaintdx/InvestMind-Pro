#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻数据每日定时抓取系统
基于 AKShare 接口，采集个股新闻、财联社电报、全球财经新闻
存储到 SQLite (InvestMindPro.db) 的 news_articles 表

用法:
    # 单次采集
    python backend/news_collector.py

    # 指定股票采集
    python backend/news_collector.py --stocks 600519,000858,601318

    # 守护模式（每小时采集一次）
    python backend/news_collector.py --daemon --interval 3600

    # 仅采集市场新闻（不采集个股）
    python backend/news_collector.py --market-only

Author: InvestMindPro
Date: 2026-02-20
"""

import sys
import os
import time
import hashlib
import argparse
from datetime import datetime, timezone
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

import akshare as ak
from backend.database.database import get_db_context, init_database
from backend.database.models import NewsArticle
from backend.utils.logging_config import get_logger

logger = get_logger("news_collector")

# 默认监控的热门A股
DEFAULT_STOCKS = [
    "600519",  # 贵州茅台
    "000858",  # 五粮液
    "601318",  # 中国平安
    "600036",  # 招商银行
    "000001",  # 平安银行
    "601012",  # 隆基绿能
    "600900",  # 长江电力
    "000333",  # 美的集团
]


def _make_hash(title: str, content: str, source: str, publish_time: str) -> str:
    """生成新闻去重hash（标题+内容前100字+来源+时间）"""
    raw = f"{title}|{(content or '')[:100]}|{source}|{publish_time}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _parse_time(time_str: str) -> datetime | None:
    """尝试解析多种时间格式"""
    if not time_str or time_str == "nan":
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%Y%m%d %H:%M:%S"):
        try:
            return datetime.strptime(str(time_str).strip(), fmt)
        except (ValueError, TypeError):
            continue
    return None


def _save_articles(articles: list[dict]) -> int:
    """批量保存新闻到数据库，返回新增条数"""
    if not articles:
        return 0

    saved = 0
    with get_db_context() as db:
        for art in articles:
            news_hash = _make_hash(art["title"], art.get("content", ""), art["source"], str(art.get("publish_time", "")))
            # 去重检查
            exists = db.query(NewsArticle).filter_by(news_hash=news_hash).first()
            if exists:
                continue

            record = NewsArticle(
                title=art["title"],
                content=art.get("content"),
                source=art["source"],
                stock_code=art.get("stock_code"),
                publish_time=_parse_time(str(art.get("publish_time", ""))),
                crawl_time=datetime.now(timezone.utc),
                sentiment_score=art.get("sentiment_score"),
                news_hash=news_hash,
            )
            db.add(record)
            saved += 1

        db.flush()
    return saved


# ==================== 采集函数 ====================


def collect_stock_news(stock_codes: list[str]) -> int:
    """采集个股新闻"""
    total = 0
    for code in stock_codes:
        try:
            logger.info(f"采集个股新闻: {code}")
            df = ak.stock_news_em(symbol=code)
            if df is None or df.empty:
                logger.warning(f"  {code}: 无数据")
                continue

            articles = []
            for _, row in df.iterrows():
                articles.append({
                    "title": str(row.get("新闻标题", "")),
                    "content": str(row.get("新闻内容", ""))[:2000],
                    "source": str(row.get("文章来源", "东方财富")),
                    "stock_code": code,
                    "publish_time": str(row.get("发布时间", "")),
                })

            saved = _save_articles(articles)
            total += saved
            logger.info(f"  {code}: 获取 {len(articles)} 条，新增 {saved} 条")

        except Exception as e:
            logger.error(f"  {code} 采集失败: {e}")
    return total


def collect_cls_telegraph() -> int:
    """采集财联社电报快讯"""
    try:
        logger.info("采集财联社电报...")
        df = ak.stock_info_global_cls()
        if df is None or df.empty:
            logger.warning("  财联社电报: 无数据")
            return 0

        articles = []
        for _, row in df.iterrows():
            articles.append({
                "title": str(row.get("标题", "")),
                "content": str(row.get("内容", ""))[:2000],
                "source": "财联社",
                "publish_time": str(row.get("发布时间", "")),
            })

        saved = _save_articles(articles)
        logger.info(f"  财联社电报: 获取 {len(articles)} 条，新增 {saved} 条")
        return saved

    except Exception as e:
        logger.error(f"  财联社电报采集失败: {e}")
        return 0


def collect_global_news() -> int:
    """采集全球财经新闻（东方财富 + 新浪）"""
    total = 0

    # 东方财富全球新闻
    try:
        logger.info("采集全球财经新闻（东方财富）...")
        df = ak.stock_info_global_em()
        if df is not None and not df.empty:
            articles = []
            for _, row in df.iterrows():
                articles.append({
                    "title": str(row.get("标题", "")),
                    "content": str(row.get("内容", ""))[:2000],
                    "source": "东方财富",
                    "publish_time": str(row.get("发布时间", "")),
                })
            saved = _save_articles(articles)
            total += saved
            logger.info(f"  东方财富全球: 获取 {len(articles)} 条，新增 {saved} 条")
    except Exception as e:
        logger.error(f"  东方财富全球新闻采集失败: {e}")

    # 新浪财经全球新闻
    try:
        logger.info("采集全球财经新闻（新浪）...")
        df = ak.stock_info_global_sina()
        if df is not None and not df.empty:
            articles = []
            for _, row in df.iterrows():
                articles.append({
                    "title": str(row.get("标题", "")),
                    "content": str(row.get("内容", ""))[:2000],
                    "source": "新浪财经",
                    "publish_time": str(row.get("发布时间", "")),
                })
            saved = _save_articles(articles)
            total += saved
            logger.info(f"  新浪全球: 获取 {len(articles)} 条，新增 {saved} 条")
    except Exception as e:
        logger.error(f"  新浪全球新闻采集失败: {e}")

    return total


# ==================== 主流程 ====================


def run_collection(stock_codes: list[str] | None = None, market_only: bool = False) -> dict:
    """
    执行一轮完整采集

    Returns:
        采集统计 {stock_news, cls_telegraph, global_news, total, time_cost}
    """
    start = time.time()
    stats = {"stock_news": 0, "cls_telegraph": 0, "global_news": 0}

    logger.info("=" * 60)
    logger.info(f"开始新闻采集 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    # 确保表已创建
    init_database()

    # 1. 财联社电报
    stats["cls_telegraph"] = collect_cls_telegraph()

    # 2. 全球财经新闻
    stats["global_news"] = collect_global_news()

    # 3. 个股新闻
    if not market_only:
        codes = stock_codes or DEFAULT_STOCKS
        stats["stock_news"] = collect_stock_news(codes)

    stats["total"] = sum(stats.values())
    stats["time_cost"] = round(time.time() - start, 1)

    logger.info("=" * 60)
    logger.info(
        f"采集完成: 个股 {stats['stock_news']} + 财联社 {stats['cls_telegraph']} "
        f"+ 全球 {stats['global_news']} = {stats['total']} 条新增 "
        f"(耗时 {stats['time_cost']}s)"
    )
    logger.info("=" * 60)
    return stats


def daemon_loop(interval: int, stock_codes: list[str] | None = None, market_only: bool = False):
    """守护模式：定时循环采集"""
    logger.info(f"进入守护模式，采集间隔 {interval} 秒")
    while True:
        try:
            run_collection(stock_codes=stock_codes, market_only=market_only)
        except Exception as e:
            logger.error(f"采集异常: {e}", exc_info=True)

        logger.info(f"下次采集: {interval} 秒后")
        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description="InvestMindPro 新闻数据定时采集系统")
    parser.add_argument("--stocks", type=str, help="股票代码列表，逗号分隔 (如 600519,000858)")
    parser.add_argument("--market-only", action="store_true", help="仅采集市场新闻，不采集个股")
    parser.add_argument("--daemon", action="store_true", help="守护模式，持续定时采集")
    parser.add_argument("--interval", type=int, default=3600, help="守护模式采集间隔（秒），默认3600")
    args = parser.parse_args()

    stock_codes = args.stocks.split(",") if args.stocks else None

    if args.daemon:
        daemon_loop(interval=args.interval, stock_codes=stock_codes, market_only=args.market_only)
    else:
        run_collection(stock_codes=stock_codes, market_only=args.market_only)


if __name__ == "__main__":
    main()
