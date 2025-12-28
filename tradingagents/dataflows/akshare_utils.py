"""
tradingagents.dataflows.akshare_utils 兼容层
"""
try:
    from backend.dataflows.providers.china.akshare_utils import *
except ImportError:
    pass
