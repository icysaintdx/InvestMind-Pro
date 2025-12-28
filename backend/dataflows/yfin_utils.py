#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yahoo Finance 数据获取模块

用于获取美股和港股的行情数据、财务数据等
需要安装 yfinance 库

配置说明：
- 可选配置代理：HTTP_PROXY, HTTPS_PROXY 环境变量
- 数据缓存目录：DATA_CACHE_DIR 环境变量
"""

import os
from datetime import datetime
from typing import Any, Optional, Callable
from functools import wraps

# 导入日志模块
from backend.utils.logging_config import get_logger
logger = get_logger('dataflow')

# 尝试导入 yfinance
try:
    import yfinance as yf
    import pandas as pd
    from pandas import DataFrame
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    logger.warning("[YFinance] yfinance 未安装，Yahoo Finance 功能不可用")
    yf = None
    pd = None
    DataFrame = None

# 默认缓存目录
DEFAULT_CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'cache')


def init_ticker(func: Callable) -> Callable:
    """装饰器：初始化 yf.Ticker 并传递给函数"""
    @wraps(func)
    def wrapper(symbol: str, *args, **kwargs) -> Any:
        if not YFINANCE_AVAILABLE:
            logger.warning("[YFinance] yfinance 未安装")
            return None
        ticker = yf.Ticker(symbol)
        return func(ticker, *args, **kwargs)
    return wrapper


class YFinanceUtils:
    """Yahoo Finance 工具类"""
    
    @staticmethod
    def get_stock_data(
        symbol: str,
        start_date: str,
        end_date: str,
        save_path: str = None
    ) -> Optional[DataFrame]:
        """
        获取股票历史价格数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期，格式 YYYY-MM-DD
            end_date: 结束日期，格式 YYYY-MM-DD
            save_path: 保存路径（可选）
            
        Returns:
            DataFrame: 股票数据
        """
        if not YFINANCE_AVAILABLE:
            logger.warning("[YFinance] yfinance 未安装")
            return None
            
        try:
            ticker = yf.Ticker(symbol)
            # 结束日期加一天，使范围包含结束日期
            end_date_dt = pd.to_datetime(end_date) + pd.DateOffset(days=1)
            end_date_str = end_date_dt.strftime("%Y-%m-%d")
            
            stock_data = ticker.history(start=start_date, end=end_date_str)
            
            if save_path:
                stock_data.to_csv(save_path)
                logger.info(f"[YFinance] 数据已保存到 {save_path}")
                
            return stock_data
            
        except Exception as e:
            logger.error(f"[YFinance] 获取 {symbol} 数据失败: {e}")
            return None
    
    @staticmethod
    def get_stock_info(symbol: str) -> Optional[dict]:
        """
        获取股票基本信息
        
        Args:
            symbol: 股票代码
            
        Returns:
            dict: 股票信息
        """
        if not YFINANCE_AVAILABLE:
            return None
            
        try:
            ticker = yf.Ticker(symbol)
            return ticker.info
        except Exception as e:
            logger.error(f"[YFinance] 获取 {symbol} 信息失败: {e}")
            return None
    
    @staticmethod
    def get_company_info(symbol: str, save_path: str = None) -> Optional[DataFrame]:
        """
        获取公司信息
        
        Args:
            symbol: 股票代码
            save_path: 保存路径（可选）
            
        Returns:
            DataFrame: 公司信息
        """
        if not YFINANCE_AVAILABLE:
            return None
            
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            company_info = {
                "Company Name": info.get("shortName", "N/A"),
                "Industry": info.get("industry", "N/A"),
                "Sector": info.get("sector", "N/A"),
                "Country": info.get("country", "N/A"),
                "Website": info.get("website", "N/A"),
            }
            company_info_df = DataFrame([company_info])
            
            if save_path:
                company_info_df.to_csv(save_path)
                logger.info(f"[YFinance] 公司信息已保存到 {save_path}")
                
            return company_info_df
            
        except Exception as e:
            logger.error(f"[YFinance] 获取 {symbol} 公司信息失败: {e}")
            return None
    
    @staticmethod
    def get_stock_dividends(symbol: str, save_path: str = None) -> Optional[DataFrame]:
        """
        获取股息数据
        
        Args:
            symbol: 股票代码
            save_path: 保存路径（可选）
            
        Returns:
            DataFrame: 股息数据
        """
        if not YFINANCE_AVAILABLE:
            return None
            
        try:
            ticker = yf.Ticker(symbol)
            dividends = ticker.dividends
            
            if save_path:
                dividends.to_csv(save_path)
                logger.info(f"[YFinance] 股息数据已保存到 {save_path}")
                
            return dividends
            
        except Exception as e:
            logger.error(f"[YFinance] 获取 {symbol} 股息数据失败: {e}")
            return None
    
    @staticmethod
    def get_income_stmt(symbol: str) -> Optional[DataFrame]:
        """获取利润表"""
        if not YFINANCE_AVAILABLE:
            return None
        try:
            ticker = yf.Ticker(symbol)
            return ticker.financials
        except Exception as e:
            logger.error(f"[YFinance] 获取 {symbol} 利润表失败: {e}")
            return None
    
    @staticmethod
    def get_balance_sheet(symbol: str) -> Optional[DataFrame]:
        """获取资产负债表"""
        if not YFINANCE_AVAILABLE:
            return None
        try:
            ticker = yf.Ticker(symbol)
            return ticker.balance_sheet
        except Exception as e:
            logger.error(f"[YFinance] 获取 {symbol} 资产负债表失败: {e}")
            return None
    
    @staticmethod
    def get_cash_flow(symbol: str) -> Optional[DataFrame]:
        """获取现金流量表"""
        if not YFINANCE_AVAILABLE:
            return None
        try:
            ticker = yf.Ticker(symbol)
            return ticker.cashflow
        except Exception as e:
            logger.error(f"[YFinance] 获取 {symbol} 现金流量表失败: {e}")
            return None
    
    @staticmethod
    def get_analyst_recommendations(symbol: str) -> tuple:
        """
        获取分析师推荐
        
        Returns:
            tuple: (推荐类型, 票数)
        """
        if not YFINANCE_AVAILABLE:
            return None, 0
            
        try:
            ticker = yf.Ticker(symbol)
            recommendations = ticker.recommendations
            
            if recommendations is None or recommendations.empty:
                return None, 0
            
            # 获取最新的推荐
            row_0 = recommendations.iloc[0, 1:]  # 排除 period 列
            max_votes = row_0.max()
            majority_voting_result = row_0[row_0 == max_votes].index.tolist()
            
            return majority_voting_result[0] if majority_voting_result else None, max_votes
            
        except Exception as e:
            logger.error(f"[YFinance] 获取 {symbol} 分析师推荐失败: {e}")
            return None, 0


def get_stock_data_with_indicators(
    symbol: str,
    start_date: str,
    end_date: str
) -> str:
    """
    获取股票数据（OHLCV）并返回 CSV 格式字符串
    
    Args:
        symbol: 股票代码
        start_date: 开始日期，格式 YYYY-MM-DD
        end_date: 结束日期，格式 YYYY-MM-DD
        
    Returns:
        str: CSV 格式的股票数据
    """
    if not YFINANCE_AVAILABLE:
        return "Error: yfinance not installed"
        
    try:
        # 验证日期格式
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
        
        # 创建 ticker 对象
        ticker = yf.Ticker(symbol.upper())
        
        # 获取历史数据
        data = ticker.history(start=start_date, end=end_date)
        
        if data.empty:
            return f"No data found for symbol '{symbol}' between {start_date} and {end_date}"
        
        # 移除时区信息
        if data.index.tz is not None:
            data.index = data.index.tz_localize(None)
        
        # 数值列保留2位小数
        numeric_columns = ["Open", "High", "Low", "Close", "Adj Close"]
        for col in numeric_columns:
            if col in data.columns:
                data[col] = data[col].round(2)
        
        # 转换为 CSV 字符串
        csv_string = data.to_csv()
        
        # 添加头部信息
        header = f"# Stock data for {symbol.upper()} from {start_date} to {end_date}\n"
        header += f"# Total records: {len(data)}\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        return header + csv_string
        
    except Exception as e:
        logger.error(f"[YFinance] 获取 {symbol} 数据失败: {e}")
        return f"Error retrieving stock data for {symbol}: {str(e)}"


# 检查模块是否可用
def is_available() -> bool:
    """检查 Yahoo Finance 功能是否可用"""
    return YFINANCE_AVAILABLE
