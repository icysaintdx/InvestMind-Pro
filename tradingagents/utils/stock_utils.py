"""
tradingagents.utils.stock_utils 兼容层
重定向到 backend.utils.stock_utils
"""
try:
    from backend.utils.stock_utils import *
except ImportError:
    # 如果 backend.utils.stock_utils 不存在，提供基本实现
    class StockUtils:
        @staticmethod
        def get_market_by_code(code: str) -> int:
            """根据股票代码判断市场 (0=深圳, 1=上海)"""
            if code.startswith(('6', '9', '5')):
                return 1  # 上海
            return 0  # 深圳

        @staticmethod
        def normalize_code(code: str) -> str:
            """标准化股票代码"""
            return code.strip().zfill(6)
