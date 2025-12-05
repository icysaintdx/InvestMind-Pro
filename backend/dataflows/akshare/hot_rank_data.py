"""
热榜数据模块
整合所有热度榜单数据
"""

import akshare as ak
from typing import List, Dict, Any
from backend.dataflows.akshare.base import AKShareBase


class AKShareHotRankData(AKShareBase):
    """AKShare热榜数据类"""
    
    def __init__(self):
        super().__init__()
        self._eastmoney_cache = None  # 缓存东财数据，避免重复调用
        self.logger.info("✅ AKShareHotRankData 初始化完成")
    
    # ========== 微博热议 ==========
    def get_weibo_stock_hot(self) -> List[Dict[str, Any]]:
        """获取微博股票热议"""
        self.logger.info("获取微博股票热议...")
        df = self.safe_call(ak.stock_js_weibo_report)
        
        if df is None:
            return []
        
        data_list = self.df_to_dict(df)
        self.logger.info(f"✅ 获取到{len(data_list)}条微博热议")
        return data_list
    
    # ========== 百度热搜 ==========
    def get_baidu_hot_search(self) -> List[Dict[str, Any]]:
        """获取百度热搜股票"""
        self.logger.info("获取百度热搜股票...")
        df = self.safe_call(ak.stock_hot_search_baidu)
        
        if df is None:
            return []
        
        data_list = self.df_to_dict(df)
        self.logger.info(f"✅ 获取到{len(data_list)}条百度热搜")
        return data_list
    
    # ========== 东财热门股票 ==========
    def get_eastmoney_hot_rank(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """获取东方财富热门股票"""
        # 如果有缓存且允许使用缓存，直接返回
        if use_cache and self._eastmoney_cache is not None:
            self.logger.info(f"✅ 使用缓存的东财数据: {len(self._eastmoney_cache)}条")
            return self._eastmoney_cache
        
        self.logger.info("获取东方财富热门股票...")
        
        try:
            # 设置超时，避免过长等待
            import socket
            original_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(5)  # 5秒超时
            
            try:
                df = ak.stock_hot_rank_em()
            finally:
                socket.setdefaulttimeout(original_timeout)
            
            if df is not None and not df.empty:
                data_list = self.df_to_dict(df)
                self._eastmoney_cache = data_list  # 缓存数据
                self.logger.info(f"✅ 获取到{len(data_list)}条东财热门股票")
                return data_list
        except Exception as e:
            self.logger.warning(f"⚠️ 东财热门股票接口失败: {e}")
            # 如果有缓存，返回缓存数据
            if self._eastmoney_cache is not None:
                self.logger.info(f"✅ 返回缓存数据: {len(self._eastmoney_cache)}条")
                return self._eastmoney_cache
        
        return []
    
    # ========== 东财热门关键词 ==========
    def get_hot_keywords(self) -> List[Dict[str, Any]]:
        """获取热门关键词"""
        self.logger.info("获取热门关键词...")
        df = self.safe_call(ak.stock_hot_keyword_em)
        
        if df is None:
            return []
        
        data_list = self.df_to_dict(df)
        self.logger.info(f"✅ 获取到{len(data_list)}条热门关键词")
        return data_list
    
    # ========== 个股人气榜 ==========
    def get_stock_popularity_rank(self) -> List[Dict[str, Any]]:
        """获取个股人气榜（与东财热度相同）"""
        # 直接返回东财热度数据，避免重复调用
        return self.get_eastmoney_hot_rank()
    
    # ========== 个股人气榜-飙升榜 ==========
    def get_stock_popularity_soar(self) -> List[Dict[str, Any]]:
        """获取个股人气榜-飙升榜"""
        self.logger.info("获取个股人气榜-飙升榜...")
        # 注意：AKShare可能没有这个接口，使用人气榜代替
        df = self.safe_call(ak.stock_hot_rank_em)
        
        if df is None:
            return []
        
        data_list = self.df_to_dict(df)
        self.logger.info(f"✅ 获取到{len(data_list)}条飙升榜")
        return data_list
    
    # ========== 互动平台 ==========
    def get_interactive_platform(self, symbol: str = None) -> List[Dict[str, Any]]:
        """获取互动平台数据"""
        if symbol:
            self.logger.info(f"获取{symbol}的互动平台数据...")
            # 需要转换格式
            clean_symbol = symbol.replace('.SH', '').replace('.SZ', '')
            if clean_symbol.startswith('6'):
                akshare_symbol = f"SH{clean_symbol}"
            elif clean_symbol.startswith(('0', '3')):
                akshare_symbol = f"SZ{clean_symbol}"
            else:
                akshare_symbol = f"SH{clean_symbol}"
            
            df = self.safe_call(ak.stock_irm_cninfo, symbol=akshare_symbol)
        else:
            self.logger.info("获取互动平台热门数据...")
            # 获取热门互动
            return []
        
        if df is None:
            return []
        
        data_list = self.df_to_dict(df)
        self.logger.info(f"✅ 获取到{len(data_list)}条互动平台数据")
        return data_list
    
    # ========== 雪球热度 ==========
    def get_xueqiu_hot(self) -> List[Dict[str, Any]]:
        """获取雪球热度榜 - 关注排行榜"""
        self.logger.info("获取雪球热度榜...")
        df = self.safe_call(ak.stock_hot_follow_xq, symbol="最热门")
        
        if df is None:
            return []
        
        data_list = self.df_to_dict(df)
        self.logger.info(f"✅ 获取到{len(data_list)}条雪球热度")
        return data_list
    
    # ========== 综合热榜 ==========
    def get_all_hot_ranks(self) -> Dict[str, Any]:
        """获取所有热榜数据（不包括雪球，雪球单独加载）"""
        result = {}
        
        try:
            result['weibo_stock_hot'] = self.get_weibo_stock_hot()
            result['baidu_hot_search'] = self.get_baidu_hot_search()
            result['eastmoney_hot_rank'] = self.get_eastmoney_hot_rank()
            result['hot_keywords'] = self.get_hot_keywords()
            result['popularity_rank'] = self.get_stock_popularity_rank()
            # 雪球热度不在这里加载，由前端单独调用
            result['xueqiu_hot'] = []
        except Exception as e:
            self.logger.error(f"获取综合热榜失败: {e}")
            import traceback
            traceback.print_exc()
        
        return result


# 全局实例
_hot_rank_data = None

def get_hot_rank_data():
    """获取热榜数据实例（单例）"""
    global _hot_rank_data
    if _hot_rank_data is None:
        _hot_rank_data = AKShareHotRankData()
    return _hot_rank_data
