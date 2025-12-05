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
            - currency_name: 货币名称
            - currency_symbol: 货币符号
        """
        ticker = str(ticker).strip().upper()
        
        # 默认返回值
        result = {
            'market': 'UNKNOWN',
            'market_name': '未知市场',
            'is_china': False,
            'is_hk': False,
            'is_us': False,
            'clean_ticker': ticker,
            'currency_name': '未知货币',
            'currency_symbol': '?'
        }
        
        # 港股判断
        if '.HK' in ticker or ticker.startswith('0') and len(ticker) == 4:
            result.update({
                'market': 'HK',
                'market_name': '香港市场',
                'is_hk': True,
                'clean_ticker': ticker.replace('.HK', ''),
                'currency_name': '港币',
                'currency_symbol': 'HK$'
            })
            return result
        
        # A股判断（6位纯数字）
        if re.match(r'^\d{6}$', ticker):
            result.update({
                'market': 'CN',
                'market_name': '中国A股',
                'is_china': True,
                'clean_ticker': ticker,
                'currency_name': '人民币',
                'currency_symbol': '¥'
            })
            return result
        
        # A股判断（带后缀）
        if any(suffix in ticker for suffix in ['.SH', '.SZ', '.SS', '.XSHG', '.XSHE']):
            clean = ticker.replace('.SH', '').replace('.SZ', '').replace('.SS', '')\
                         .replace('.XSHG', '').replace('.XSHE', '')
            result.update({
                'market': 'CN',
                'market_name': '中国A股',
                'is_china': True,
                'clean_ticker': clean,
                'currency_name': '人民币',
                'currency_symbol': '¥'
            })
            return result
        
        # 美股判断（字母代码）
        if re.match(r'^[A-Z]+$', ticker):
            result.update({
                'market': 'US',
                'market_name': '美国市场',
                'is_us': True,
                'clean_ticker': ticker,
                'currency_name': '美元',
                'currency_symbol': '$'
            })
            return result
        
        logger.warning(f"无法识别股票代码: {ticker}")
        return result
