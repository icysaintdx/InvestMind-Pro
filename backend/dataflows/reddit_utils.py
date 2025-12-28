#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reddit 数据获取模块

用于从本地存储的 Reddit 数据中获取帖子
需要先下载 Reddit 数据到本地才能使用

配置说明：
- 数据目录配置在 .env 文件中的 REDDIT_DATA_DIR
- 数据格式为 JSONL 文件
"""

import json
import os
import re
from datetime import datetime
from typing import List, Dict, Any, Optional

# 导入日志模块
from backend.utils.logging_config import get_logger
logger = get_logger('dataflow')

# 默认数据目录
DEFAULT_DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'reddit_data')

# 股票代码到公司名称的映射（用于搜索）
TICKER_TO_COMPANY = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "GOOGL": "Google",
    "AMZN": "Amazon",
    "TSLA": "Tesla",
    "NVDA": "Nvidia",
    "TSM": "Taiwan Semiconductor Manufacturing Company OR TSMC",
    "JPM": "JPMorgan Chase OR JP Morgan",
    "JNJ": "Johnson & Johnson OR JNJ",
    "V": "Visa",
    "WMT": "Walmart",
    "META": "Meta OR Facebook",
    "AMD": "AMD",
    "INTC": "Intel",
    "QCOM": "Qualcomm",
    "BABA": "Alibaba",
    "ADBE": "Adobe",
    "NFLX": "Netflix",
    "CRM": "Salesforce",
    "PYPL": "PayPal",
    "PLTR": "Palantir",
    "MU": "Micron",
    "SQ": "Block OR Square",
    "ZM": "Zoom",
    "CSCO": "Cisco",
    "SHOP": "Shopify",
    "ORCL": "Oracle",
    "X": "Twitter OR X",
    "SPOT": "Spotify",
    "AVGO": "Broadcom",
    "ASML": "ASML",
    "TWLO": "Twilio",
    "SNAP": "Snap Inc.",
    "TEAM": "Atlassian",
    "SQSP": "Squarespace",
    "UBER": "Uber",
    "ROKU": "Roku",
    "PINS": "Pinterest",
}


def fetch_top_from_category(
    category: str,
    date: str,
    max_limit: int,
    query: str = None,
    data_path: str = None
) -> List[Dict[str, Any]]:
    """
    从指定分类获取热门帖子
    
    Args:
        category: 分类名称（对应子目录名）
        date: 日期，格式 YYYY-MM-DD
        max_limit: 最大返回数量
        query: 搜索关键词（股票代码）
        data_path: 数据目录路径
        
    Returns:
        list: 帖子列表
    """
    if data_path is None:
        data_path = os.environ.get('REDDIT_DATA_DIR', DEFAULT_DATA_DIR)
    
    category_path = os.path.join(data_path, category)
    
    if not os.path.exists(category_path):
        logger.debug(f"[Reddit] 分类目录不存在: {category_path}")
        return []
    
    all_content = []
    
    try:
        subreddit_files = [f for f in os.listdir(category_path) if f.endswith('.jsonl')]
    except Exception as e:
        logger.error(f"[Reddit] 读取目录失败: {e}")
        return []
    
    if not subreddit_files:
        logger.debug(f"[Reddit] 分类 {category} 中没有数据文件")
        return []
    
    if max_limit < len(subreddit_files):
        logger.warning(f"[Reddit] max_limit ({max_limit}) 小于文件数量 ({len(subreddit_files)})")
    
    limit_per_subreddit = max(1, max_limit // len(subreddit_files))
    
    for data_file in subreddit_files:
        all_content_curr_subreddit = []
        file_path = os.path.join(category_path, data_file)
        
        try:
            with open(file_path, "rb") as f:
                for line in f:
                    # 跳过空行
                    if not line.strip():
                        continue
                    
                    try:
                        parsed_line = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    
                    # 按日期过滤
                    try:
                        post_date = datetime.utcfromtimestamp(
                            parsed_line.get("created_utc", 0)
                        ).strftime("%Y-%m-%d")
                    except (ValueError, TypeError):
                        continue
                        
                    if post_date != date:
                        continue
                    
                    # 如果是公司新闻分类，检查标题或内容是否包含公司名称
                    if "company" in category and query:
                        search_terms = []
                        if query in TICKER_TO_COMPANY:
                            company_name = TICKER_TO_COMPANY[query]
                            if "OR" in company_name:
                                search_terms = company_name.split(" OR ")
                            else:
                                search_terms = [company_name]
                        search_terms.append(query)
                        
                        found = False
                        title = parsed_line.get("title", "")
                        selftext = parsed_line.get("selftext", "")
                        
                        for term in search_terms:
                            if re.search(term, title, re.IGNORECASE) or \
                               re.search(term, selftext, re.IGNORECASE):
                                found = True
                                break
                        
                        if not found:
                            continue
                    
                    post = {
                        "title": parsed_line.get("title", ""),
                        "content": parsed_line.get("selftext", ""),
                        "url": parsed_line.get("url", ""),
                        "upvotes": parsed_line.get("ups", 0),
                        "posted_date": post_date,
                    }
                    
                    all_content_curr_subreddit.append(post)
                    
        except Exception as e:
            logger.warning(f"[Reddit] 读取文件 {data_file} 失败: {e}")
            continue
        
        # 按点赞数排序
        all_content_curr_subreddit.sort(key=lambda x: x["upvotes"], reverse=True)
        
        # 取前 N 条
        all_content.extend(all_content_curr_subreddit[:limit_per_subreddit])
    
    logger.info(f"[Reddit] 从 {category} 获取到 {len(all_content)} 条帖子")
    return all_content


def get_global_news(date: str, max_limit: int = 50, data_path: str = None) -> List[Dict[str, Any]]:
    """
    获取全球新闻（来自 r/worldnews, r/news 等）
    
    Args:
        date: 日期
        max_limit: 最大数量
        data_path: 数据目录
        
    Returns:
        list: 帖子列表
    """
    return fetch_top_from_category("global_news", date, max_limit, data_path=data_path)


def get_company_news(
    ticker: str,
    date: str,
    max_limit: int = 20,
    data_path: str = None
) -> List[Dict[str, Any]]:
    """
    获取公司相关新闻
    
    Args:
        ticker: 股票代码
        date: 日期
        max_limit: 最大数量
        data_path: 数据目录
        
    Returns:
        list: 帖子列表
    """
    return fetch_top_from_category("company_news", date, max_limit, query=ticker, data_path=data_path)


def get_stock_discussion(
    ticker: str = None,
    date: str = None,
    max_limit: int = 30,
    data_path: str = None
) -> List[Dict[str, Any]]:
    """
    获取股票讨论（来自 r/wallstreetbets, r/stocks 等）
    
    Args:
        ticker: 股票代码（可选）
        date: 日期
        max_limit: 最大数量
        data_path: 数据目录
        
    Returns:
        list: 帖子列表
    """
    return fetch_top_from_category("stock_discussion", date, max_limit, query=ticker, data_path=data_path)


# 检查模块是否可用
def is_available() -> bool:
    """检查 Reddit 数据是否可用"""
    data_path = os.environ.get('REDDIT_DATA_DIR', DEFAULT_DATA_DIR)
    return os.path.exists(data_path)


# 模块可用性标志
REDDIT_AVAILABLE = True