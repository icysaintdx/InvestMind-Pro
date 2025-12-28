#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Finnhub 数据获取模块

用于获取 Finnhub 保存在本地的数据（内幕交易、SEC文件、新闻等）
需要先下载数据到本地才能使用

配置说明：
- 需要 Finnhub API Key（可选，用于在线获取）
- 数据目录配置在 .env 文件中的 FINNHUB_DATA_DIR
"""

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime

# 导入日志模块
from backend.utils.logging_config import get_logger
logger = get_logger('dataflow')

# 默认数据目录
DEFAULT_DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'finnhub_data')


def get_data_in_range(
    ticker: str,
    start_date: str,
    end_date: str,
    data_type: str,
    data_dir: str = None,
    period: str = None
) -> Dict[str, Any]:
    """
    获取指定日期范围内的 Finnhub 数据
    
    Args:
        ticker: 股票代码
        start_date: 开始日期，格式 YYYY-MM-DD
        end_date: 结束日期，格式 YYYY-MM-DD
        data_type: 数据类型，可选值：
            - insider_trans: 内幕交易
            - SEC_filings: SEC文件
            - news_data: 新闻数据
            - insider_senti: 内幕情绪
            - fin_as_reported: 财务报告
        data_dir: 数据目录，默认使用配置的目录
        period: 周期，可选 'annual' 或 'quarterly'
        
    Returns:
        dict: 按日期过滤后的数据
    """
    if data_dir is None:
        data_dir = os.environ.get('FINNHUB_DATA_DIR', DEFAULT_DATA_DIR)
    
    # 构建数据文件路径
    if period:
        data_path = os.path.join(
            data_dir,
            "finnhub_data",
            data_type,
            f"{ticker}_{period}_data_formatted.json",
        )
    else:
        data_path = os.path.join(
            data_dir, 
            "finnhub_data", 
            data_type, 
            f"{ticker}_data_formatted.json"
        )

    try:
        if not os.path.exists(data_path):
            logger.debug(f"[Finnhub] 数据文件不存在: {data_path}")
            logger.debug(f"[Finnhub] 请确保已下载相关数据或检查数据目录配置")
            return {}
        
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
    except FileNotFoundError:
        logger.warning(f"[Finnhub] 文件未找到: {data_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"[Finnhub] JSON解析错误: {e}")
        return {}
    except Exception as e:
        logger.error(f"[Finnhub] 读取数据文件时发生错误: {e}")
        return {}

    # 按日期范围过滤数据
    filtered_data = {}
    for key, value in data.items():
        if start_date <= key <= end_date and len(value) > 0:
            filtered_data[key] = value
            
    return filtered_data


def get_insider_transactions(
    ticker: str,
    start_date: str,
    end_date: str,
    data_dir: str = None
) -> Dict[str, Any]:
    """
    获取内幕交易数据
    
    Args:
        ticker: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        data_dir: 数据目录
        
    Returns:
        dict: 内幕交易数据
    """
    return get_data_in_range(ticker, start_date, end_date, "insider_trans", data_dir)


def get_sec_filings(
    ticker: str,
    start_date: str,
    end_date: str,
    data_dir: str = None
) -> Dict[str, Any]:
    """
    获取 SEC 文件数据
    
    Args:
        ticker: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        data_dir: 数据目录
        
    Returns:
        dict: SEC 文件数据
    """
    return get_data_in_range(ticker, start_date, end_date, "SEC_filings", data_dir)


def get_news_data(
    ticker: str,
    start_date: str,
    end_date: str,
    data_dir: str = None
) -> Dict[str, Any]:
    """
    获取新闻数据
    
    Args:
        ticker: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        data_dir: 数据目录
        
    Returns:
        dict: 新闻数据
    """
    return get_data_in_range(ticker, start_date, end_date, "news_data", data_dir)


def get_insider_sentiment(
    ticker: str,
    start_date: str,
    end_date: str,
    data_dir: str = None
) -> Dict[str, Any]:
    """
    获取内幕情绪数据
    
    Args:
        ticker: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        data_dir: 数据目录
        
    Returns:
        dict: 内幕情绪数据
    """
    return get_data_in_range(ticker, start_date, end_date, "insider_senti", data_dir)


def get_financial_reports(
    ticker: str,
    start_date: str,
    end_date: str,
    period: str = "annual",
    data_dir: str = None
) -> Dict[str, Any]:
    """
    获取财务报告数据
    
    Args:
        ticker: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        period: 周期，'annual' 或 'quarterly'
        data_dir: 数据目录
        
    Returns:
        dict: 财务报告数据
    """
    return get_data_in_range(ticker, start_date, end_date, "fin_as_reported", data_dir, period)


# 检查 Finnhub 是否可用
def is_available() -> bool:
    """检查 Finnhub 数据是否可用"""
    data_dir = os.environ.get('FINNHUB_DATA_DIR', DEFAULT_DATA_DIR)
    return os.path.exists(data_dir)


# 模块可用性标志
FINNHUB_AVAILABLE = True