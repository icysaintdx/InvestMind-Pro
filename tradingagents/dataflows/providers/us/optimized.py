"""
tradingagents.dataflows.providers.us.optimized 兼容层
"""
try:
    from backend.dataflows.providers.us.optimized import *
except ImportError:
    def get_us_stock_data_cached(*args, **kwargs):
        return None
