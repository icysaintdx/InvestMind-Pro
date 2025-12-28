"""
tradingagents.dataflows.cache.mongodb_cache_adapter 兼容层
"""
try:
    from backend.dataflows.cache.mongodb_cache_adapter import *
except ImportError:
    def get_mongodb_cache_adapter():
        return None
