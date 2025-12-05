#!/usr/bin/env python3
"""
AKShare社交媒体数据模块
提供微博热搜、微博股票热议等社交媒体数据

使用场景：
- 社交媒体分析师：分析市场情绪、热点话题
- 新闻面板：社交媒体专区
"""

import akshare as ak
from typing import List, Dict, Any
from .base import AKShareBase


class AKShareSocialMediaData(AKShareBase):
    """AKShare社交媒体数据"""
    
    def __init__(self):
        """初始化"""
        super().__init__()
    
    def get_weibo_hot_search(self) -> List[Dict[str, Any]]:
        """
        获取微博股票热议（作为热搜替代）
        
        Returns:
            微博股票热议列表
            
        应用场景：
            - 发现热门股票
            - 分析市场关注度
        """
        self.logger.info("获取微博股票热议（热搜替代）...")
        
        # AKShare没有通用微博热搜，使用股票热议代替
        df = self.safe_call(ak.stock_js_weibo_report)
        
        if df is None:
            return []
        
        hot_list = self.df_to_dict(df)
        self.logger.info(f"✅ 获取到{len(hot_list)}条微博股票热议")
        
        return hot_list
    
    def get_weibo_stock_hot(self) -> List[Dict[str, Any]]:
        """
        获取微博股票热议
        
        Returns:
            微博股票热议列表
            
        应用场景：
            - 发现热门股票
            - 分析市场情绪
        """
        self.logger.info("获取微博股票热议...")
        
        df = self.safe_call(ak.stock_js_weibo_report)
        
        if df is None:
            return []
        
        hot_list = self.df_to_dict(df)
        self.logger.info(f"✅ 获取到{len(hot_list)}条微博股票热议")
        
        return hot_list
    
    def get_baidu_hot_search(self) -> List[Dict[str, Any]]:
        """
        获取百度热搜股票
        
        Returns:
            百度热搜股票列表
            
        应用场景：
            - 发现热门股票
            - 分析关注趋势
        """
        self.logger.info("获取百度热搜股票...")
        
        df = self.safe_call(ak.stock_hot_search_baidu)
        
        if df is None:
            return []
        
        hot_list = self.df_to_dict(df)
        self.logger.info(f"✅ 获取到{len(hot_list)}条百度热搜股票")
        
        return hot_list
    
    def get_comprehensive_social_media(self) -> Dict[str, Any]:
        """
        获取综合社交媒体数据（为社交媒体分析师提供）
        
        Returns:
            包含多个社交媒体数据的字典
            
        应用场景：
            - 社交媒体分析师：一次性获取所有社媒数据
            - 新闻面板：社交媒体专区
        """
        result = {
            'weibo_hot_search': [],
            'weibo_stock_hot': [],
            'baidu_hot_search': []
        }
        
        # 1. 微博热搜
        try:
            result['weibo_hot_search'] = self.get_weibo_hot_search()
        except Exception as e:
            self.logger.error(f"❌ 获取微博热搜失败: {e}")
        
        # 2. 微博股票热议
        try:
            result['weibo_stock_hot'] = self.get_weibo_stock_hot()
        except Exception as e:
            self.logger.error(f"❌ 获取微博股票热议失败: {e}")
        
        # 3. 百度热搜
        try:
            result['baidu_hot_search'] = self.get_baidu_hot_search()
        except Exception as e:
            self.logger.error(f"❌ 获取百度热搜失败: {e}")
        
        return result


# 全局实例
_social_media_data = None

def get_social_media_data():
    """获取社交媒体数据实例（单例）"""
    global _social_media_data
    if _social_media_data is None:
        _social_media_data = AKShareSocialMediaData()
    return _social_media_data
