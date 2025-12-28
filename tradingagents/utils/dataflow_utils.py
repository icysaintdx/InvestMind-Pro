"""
tradingagents.utils.dataflow_utils 兼容层
重定向到 backend.utils.dataflow_utils
"""
try:
    from backend.utils.dataflow_utils import *
except ImportError:
    # 如果不存在，提供基本实现
    from datetime import datetime, timedelta

    def get_trading_date_range(days: int = 30):
        """获取交易日期范围"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
