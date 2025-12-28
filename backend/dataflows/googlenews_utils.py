#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google News 数据获取模块

用于从 Google News 搜索获取新闻数据
注意：需要能够访问 Google（可能需要代理）

配置说明：
- 可选配置代理：HTTP_PROXY, HTTPS_PROXY 环境变量
- 可选配置延迟：TA_GOOGLE_NEWS_SLEEP_MIN_SECONDS, TA_GOOGLE_NEWS_SLEEP_MAX_SECONDS
"""

import os
import time
import random
from datetime import datetime
from typing import List, Dict, Any, Optional

# 导入日志模块
from backend.utils.logging_config import get_logger
logger = get_logger('dataflow')

# 尝试导入必要的库
try:
    import requests
    from bs4 import BeautifulSoup
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("[GoogleNews] requests 或 beautifulsoup4 未安装，Google News 功能不可用")

try:
    from tenacity import (
        retry,
        stop_after_attempt,
        wait_exponential,
        retry_if_exception_type,
        retry_if_result,
    )
    TENACITY_AVAILABLE = True
except ImportError:
    TENACITY_AVAILABLE = False
    logger.debug("[GoogleNews] tenacity 未安装，将不使用重试机制")

# 配置参数
SLEEP_MIN = float(os.environ.get("TA_GOOGLE_NEWS_SLEEP_MIN_SECONDS", "2.0"))
SLEEP_MAX = float(os.environ.get("TA_GOOGLE_NEWS_SLEEP_MAX_SECONDS", "6.0"))
REQUEST_TIMEOUT = (10, 30)  # 连接超时10秒，读取超时30秒


def is_rate_limited(response) -> bool:
    """检查是否被限流（状态码 429）"""
    if response is None:
        return False
    return response.status_code == 429


def _make_request_simple(url: str, headers: dict) -> Optional[requests.Response]:
    """简单的请求方法（无重试）"""
    if not REQUESTS_AVAILABLE:
        return None
    
    time.sleep(random.uniform(SLEEP_MIN, SLEEP_MAX))
    try:
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        return response
    except Exception as e:
        logger.error(f"[GoogleNews] 请求失败: {e}")
        return None


# 如果 tenacity 可用，使用重试装饰器
if TENACITY_AVAILABLE and REQUESTS_AVAILABLE:
    @retry(
        retry=(
            retry_if_result(is_rate_limited) | 
            retry_if_exception_type(requests.exceptions.ConnectionError) | 
            retry_if_exception_type(requests.exceptions.Timeout)
        ),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(5),
    )
    def make_request(url: str, headers: dict) -> requests.Response:
        """带重试的请求方法"""
        time.sleep(random.uniform(SLEEP_MIN, SLEEP_MAX))
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        return response
else:
    make_request = _make_request_simple


def getNewsData(
    query: str,
    start_date: str,
    end_date: str,
    max_pages: int = 5
) -> List[Dict[str, Any]]:
    """
    从 Google News 搜索获取新闻数据
    
    Args:
        query: 搜索关键词
        start_date: 开始日期，格式 YYYY-MM-DD 或 MM/DD/YYYY
        end_date: 结束日期，格式 YYYY-MM-DD 或 MM/DD/YYYY
        max_pages: 最大页数
        
    Returns:
        list: 新闻列表，每条新闻包含 link, title, snippet, date, source
    """
    if not REQUESTS_AVAILABLE:
        logger.warning("[GoogleNews] 依赖库未安装，无法获取数据")
        return []
    
    # 转换日期格式
    if "-" in start_date:
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        start_date = start_date_obj.strftime("%m/%d/%Y")
    if "-" in end_date:
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
        end_date = end_date_obj.strftime("%m/%d/%Y")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/101.0.4951.54 Safari/537.36"
        )
    }

    news_results = []
    page = 0
    consecutive_errors = 0
    
    while page < max_pages:
        offset = page * 10
        url = (
            f"https://www.google.com/search?q={query}"
            f"&tbs=cdr:1,cd_min:{start_date},cd_max:{end_date}"
            f"&tbm=nws&start={offset}"
        )

        try:
            response = make_request(url, headers)
            
            if response is None:
                consecutive_errors += 1
                if consecutive_errors >= 3:
                    logger.warning("[GoogleNews] 连续多次请求失败，停止获取")
                    break
                page += 1
                continue
                
            soup = BeautifulSoup(response.content, "html.parser")
            results_on_page = soup.select("div.SoaBEf")

            if not results_on_page:
                break  # 没有更多结果

            consecutive_errors = 0  # 重置错误计数
            
            for el in results_on_page:
                try:
                    link = el.find("a")["href"]
                    title = el.select_one("div.MBeuO").get_text()
                    snippet = el.select_one(".GI74Re").get_text()
                    date = el.select_one(".LfVVr").get_text()
                    source = el.select_one(".NUnG9d span").get_text()
                    news_results.append({
                        "link": link,
                        "title": title,
                        "snippet": snippet,
                        "date": date,
                        "source": source,
                    })
                except Exception as e:
                    logger.debug(f"[GoogleNews] 解析单条新闻失败: {e}")
                    continue

            # 检查是否有下一页
            next_link = soup.find("a", id="pnnext")
            if not next_link:
                break

            page += 1

        except requests.exceptions.Timeout as e:
            logger.warning(f"[GoogleNews] 连接超时: {e}")
            consecutive_errors += 1
            if consecutive_errors >= 3:
                logger.error("[GoogleNews] 多次连接超时，停止获取")
                break
            page += 1
            continue
            
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"[GoogleNews] 连接错误: {e}")
            consecutive_errors += 1
            if consecutive_errors >= 3:
                logger.error("[GoogleNews] 多次连接错误，停止获取（可能需要代理）")
                break
            page += 1
            continue
            
        except Exception as e:
            logger.error(f"[GoogleNews] 获取新闻失败: {e}")
            break

    logger.info(f"[GoogleNews] 获取到 {len(news_results)} 条新闻")
    return news_results


def search_stock_news(
    ticker: str,
    company_name: str = None,
    days: int = 7
) -> List[Dict[str, Any]]:
    """
    搜索股票相关新闻
    
    Args:
        ticker: 股票代码
        company_name: 公司名称（可选）
        days: 搜索天数
        
    Returns:
        list: 新闻列表
    """
    from datetime import timedelta
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # 构建搜索词
    if company_name:
        query = f"{ticker} OR {company_name} stock"
    else:
        query = f"{ticker} stock"
    
    return getNewsData(
        query=query,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d")
    )


# 检查模块是否可用
def is_available() -> bool:
    """检查 Google News 功能是否可用"""
    return REQUESTS_AVAILABLE


# 模块可用性标志
GOOGLENEWS_AVAILABLE = REQUESTS_AVAILABLE