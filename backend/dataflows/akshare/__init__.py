"""
AKShare数据接口模块
提供股票、新闻、资金、财务、社交媒体等多维度数据
"""

from .stock_data import get_stock_data, AKShareStockData
from .fund_flow_data import get_fund_flow_data, AKShareFundFlowData
from .financial_data import get_financial_data, AKShareFinancialData
from .social_media_data import get_social_media_data, AKShareSocialMediaData

__all__ = [
    'get_stock_data',
    'AKShareStockData',
    'get_fund_flow_data',
    'AKShareFundFlowData',
    'get_financial_data',
    'AKShareFinancialData',
    'get_social_media_data',
    'AKShareSocialMediaData',
]
