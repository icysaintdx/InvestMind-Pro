"""
股票搜索模块
使用本地SQLite缓存，定期更新股票列表
"""

from typing import List, Dict, Any
from backend.dataflows.akshare.stock_list_cache import get_stock_cache
from backend.utils.logging_config import get_logger


class AKShareStockSearch:
    """股票搜索类（使用本地缓存）"""
    
    def __init__(self):
        self.cache = get_stock_cache()
        self.logger = get_logger(self.__class__.__name__)
        self.logger.info("✅ AKShareStockSearch 初始化完成")
    
    def search_stock(self, keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        搜索股票（本地数据库）
        
        Args:
            keyword: 搜索关键词（代码或名称）
            limit: 返回数量限制
            
        Returns:
            匹配的股票列表
        """
        return self.cache.search(keyword, limit)
    
    def get_stock_count(self) -> int:
        """获取股票总数"""
        return self.cache.get_stock_count()
    
    def get_last_update_time(self) -> str:
        """获取最后更新时间"""
        return self.cache.get_last_update_time()
    
    def force_update(self) -> bool:
        """强制更新股票列表"""
        return self.cache.update_stock_list()


# 全局实例
_stock_search = None

def get_stock_search():
    """获取股票搜索实例（单例）"""
    global _stock_search
    if _stock_search is None:
        _stock_search = AKShareStockSearch()
    return _stock_search
