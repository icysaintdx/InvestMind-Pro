"""
股票工具类
提供股票代码识别、市场判断等功能
"""

import re
from typing import Dict, Any
from backend.utils.logging_config import get_logger

logger = get_logger("stock_utils")

class StockUtils:
    """股票工具类"""
    
    @staticmethod
    def get_market_info(ticker: str) -> Dict[str, Any]:
        """
        根据股票代码判断市场类型
        
        Args:
            ticker: 股票代码
            
        Returns:
            市场信息字典，包含:
            - market: 市场代码 (CN/HK/US)
            - market_name: 市场名称
            - is_china: 是否为A股
            - is_hk: 是否为港股
            - is_us: 是否为美股
            - clean_ticker: 清理后的股票代码
        """
        ticker = str(ticker).strip().upper()
        
        # 默认结果
        result = {
            "market": "UNKNOWN",
            "market_name": "未知市场",
            "is_china": False,
            "is_hk": False,
            "is_us": False,
            "clean_ticker": ticker
        }
        
        # 判断港股
        if ticker.endswith('.HK') or '.HK' in ticker:
            result.update({
                "market": "HK",
                "market_name": "港股",
                "is_hk": True,
                "clean_ticker": ticker.replace('.HK', '')
            })
            logger.debug(f"识别为港股: {ticker}")
            return result
            
        # 判断A股 - 6位数字
        if re.match(r'^\d{6}$', ticker):
            # 上证
            if ticker.startswith(('60', '68')):
                result.update({
                    "market": "CN",
                    "market_name": "A股-上证",
                    "is_china": True,
                    "clean_ticker": ticker
                })
            # 深证
            elif ticker.startswith(('00', '30')):
                result.update({
                    "market": "CN", 
                    "market_name": "A股-深证",
                    "is_china": True,
                    "clean_ticker": ticker
                })
            # 北交所
            elif ticker.startswith(('43', '83', '87', '88')):
                result.update({
                    "market": "CN",
                    "market_name": "A股-北交所",
                    "is_china": True,
                    "clean_ticker": ticker
                })
            else:
                # 其他6位数字默认为A股
                result.update({
                    "market": "CN",
                    "market_name": "A股",
                    "is_china": True,
                    "clean_ticker": ticker
                })
            logger.debug(f"识别为A股: {ticker}")
            return result
            
        # 判断美股 - 英文字母组成
        if re.match(r'^[A-Z]+$', ticker):
            result.update({
                "market": "US",
                "market_name": "美股",
                "is_us": True,
                "clean_ticker": ticker
            })
            logger.debug(f"识别为美股: {ticker}")
            return result
            
        # 特殊处理：带有后缀的股票代码
        if '.' in ticker:
            prefix = ticker.split('.')[0]
            suffix = ticker.split('.')[1]
            
            if suffix in ['SH', 'SZ', 'BJ']:
                # A股带后缀
                result.update({
                    "market": "CN",
                    "market_name": f"A股-{suffix}",
                    "is_china": True,
                    "clean_ticker": prefix
                })
                logger.debug(f"识别为A股(带后缀): {ticker}")
                return result
                
        # 默认返回
        logger.warning(f"无法识别的股票代码: {ticker}")
        return result
    
    @staticmethod
    def normalize_ticker(ticker: str, market: str = None) -> str:
        """
        标准化股票代码
        
        Args:
            ticker: 原始股票代码
            market: 市场类型 (可选)
            
        Returns:
            标准化后的股票代码
        """
        ticker = str(ticker).strip().upper()
        
        if market:
            market = market.upper()
            if market == 'HK' and not ticker.endswith('.HK'):
                return f"{ticker}.HK"
            elif market == 'CN':
                # 移除A股可能的后缀
                return ticker.replace('.SH', '').replace('.SZ', '').replace('.BJ', '')
            elif market == 'US':
                # 美股保持原样
                return ticker.replace('.', '')
                
        return ticker
    
    @staticmethod
    def is_valid_ticker(ticker: str) -> bool:
        """
        验证股票代码是否有效
        
        Args:
            ticker: 股票代码
            
        Returns:
            是否有效
        """
        if not ticker or not isinstance(ticker, str):
            return False
            
        ticker = ticker.strip()
        if not ticker:
            return False
            
        # A股: 6位数字
        if re.match(r'^\d{6}$', ticker):
            return True
            
        # 港股: 1-5位数字，可能带.HK后缀
        if re.match(r'^\d{1,5}(\.HK)?$', ticker, re.IGNORECASE):
            return True
            
        # 美股: 1-5位字母
        if re.match(r'^[A-Z]{1,5}$', ticker):
            return True
            
        return False
    
    @staticmethod
    def get_exchange_suffix(ticker: str) -> str:
        """
        获取交易所后缀
        
        Args:
            ticker: 股票代码
            
        Returns:
            交易所后缀 (.SH/.SZ/.BJ/.HK 或空字符串)
        """
        market_info = StockUtils.get_market_info(ticker)
        
        if market_info['is_china']:
            clean_ticker = market_info['clean_ticker']
            # 上证
            if clean_ticker.startswith(('60', '68')):
                return '.SH'
            # 深证
            elif clean_ticker.startswith(('00', '30')):
                return '.SZ'
            # 北交所
            elif clean_ticker.startswith(('43', '83', '87', '88')):
                return '.BJ'
                
        elif market_info['is_hk']:
            return '.HK'
            
        return ''
    
    @staticmethod
    def format_ticker_display(ticker: str) -> str:
        """
        格式化股票代码用于显示
        
        Args:
            ticker: 股票代码
            
        Returns:
            格式化后的显示字符串
        """
        market_info = StockUtils.get_market_info(ticker)
        
        if market_info['is_china']:
            suffix = StockUtils.get_exchange_suffix(ticker)
            return f"{market_info['clean_ticker']}{suffix}"
        elif market_info['is_hk']:
            return f"{market_info['clean_ticker']}.HK"
        elif market_info['is_us']:
            return market_info['clean_ticker']
        else:
            return ticker

# 测试代码
if __name__ == "__main__":
    # 测试不同类型的股票代码
    test_tickers = [
        "000001",  # 深证A股
        "600519",  # 上证A股
        "688001",  # 科创板
        "300001",  # 创业板
        "430001",  # 北交所
        "0700.HK", # 港股
        "9988.HK", # 港股
        "AAPL",    # 美股
        "TSLA",    # 美股
        "000001.SZ", # 带后缀的A股
        "600519.SH", # 带后缀的A股
    ]
    
    print("股票代码市场识别测试:")
    print("-" * 60)
    
    for ticker in test_tickers:
        info = StockUtils.get_market_info(ticker)
        display = StockUtils.format_ticker_display(ticker)
        valid = StockUtils.is_valid_ticker(ticker)
        
        print(f"股票代码: {ticker}")
        print(f"  市场: {info['market_name']}")
        print(f"  清理后: {info['clean_ticker']}")
        print(f"  显示格式: {display}")
        print(f"  是否有效: {valid}")
        print()
