#!/usr/bin/env python3
"""
AKShare新闻接口封装
使用稳定的AKShare接口
"""

import akshare as ak
from typing import List, Dict, Any
from backend.utils.logging_config import get_logger

logger = get_logger("akshare_news")


class AKShareNewsAPI:
    """AKShare新闻API封装"""
    
    def __init__(self):
        logger.info(f"初始化AKShare新闻API，版本: {ak.__version__}")
    
    # ========== 核心接口 ==========
    
    def get_stock_news(self, symbol: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取个股新闻（最重要）
        接口: stock_news_em
        数据量: 100条/次
        
        Args:
            symbol: 股票代码
            limit: 限制数量
            
        Returns:
            新闻列表
        """
        try:
            logger.info(f"获取{symbol}的个股新闻...")
            clean_symbol = symbol.replace('.SH', '').replace('.SZ', '').replace('.HK', '')
            
            df = ak.stock_news_em(symbol=clean_symbol)
            
            if df is None or len(df) == 0:
                logger.warning(f"未获取到{symbol}的新闻")
                return []
            
            # 限制数量
            df = df.head(limit)
            
            # 转换为标准格式
            news_list = []
            for _, row in df.iterrows():
                news_list.append({
                    'title': str(row.get('新闻标题', '')),
                    'content': str(row.get('新闻内容', '')),
                    'publish_time': str(row.get('发布时间', '')),
                    'source': str(row.get('文章来源', '东方财富')),
                    'url': str(row.get('新闻链接', ''))
                })
            
            logger.info(f"✅ 获取{symbol}新闻 {len(news_list)} 条")
            return news_list
            
        except Exception as e:
            logger.error(f"❌ 获取个股新闻失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    # ========== 综合新闻 ==========
    
    def get_morning_news(self) -> List[Dict[str, Any]]:
        """
        获取财经早餐
        接口: stock_info_cjzc_em
        
        Returns:
            新闻列表
        """
        try:
            logger.info("获取财经早餐...")
            df = ak.stock_info_cjzc_em()
            
            if df is None or len(df) == 0:
                logger.warning("未获取到财经早餐")
                return []
            
            news_list = []
            for _, row in df.iterrows():
                news_list.append({
                    'title': str(row.get('标题', '')),
                    'content': str(row.get('内容', '')),
                    'publish_time': str(row.get('发布时间', '')),
                    'source': '东方财富',
                    'url': ''
                })
            
            logger.info(f"✅ 获取财经早餐 {len(news_list)} 条")
            return news_list
            
        except Exception as e:
            logger.error(f"❌ 获取财经早餐失败: {e}")
            return []
    
    def get_global_news_em(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取全球财经新闻（东方财富）
        接口: stock_info_global_em
        
        Args:
            limit: 限制数量
            
        Returns:
            新闻列表
        """
        try:
            logger.info("获取全球财经新闻（东方财富）...")
            df = ak.stock_info_global_em()
            
            if df is None or len(df) == 0:
                logger.warning("未获取到全球财经新闻")
                return []
            
            df = df.head(limit)
            
            news_list = []
            for _, row in df.iterrows():
                news_list.append({
                    'title': str(row.get('标题', '')),
                    'content': str(row.get('内容', '')),
                    'publish_time': str(row.get('发布时间', '')),
                    'source': '东方财富',
                    'url': str(row.get('链接', ''))
                })
            
            logger.info(f"✅ 获取全球财经新闻 {len(news_list)} 条")
            return news_list
            
        except Exception as e:
            logger.error(f"❌ 获取全球财经新闻失败: {e}")
            return []
    
    def get_global_news_sina(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取全球财经新闻（新浪）
        接口: stock_info_global_sina
        
        Args:
            limit: 限制数量
            
        Returns:
            新闻列表
        """
        try:
            logger.info("获取全球财经新闻（新浪）...")
            df = ak.stock_info_global_sina()
            
            if df is None or len(df) == 0:
                logger.warning("未获取到全球财经新闻（新浪）")
                return []
            
            df = df.head(limit)
            
            news_list = []
            for _, row in df.iterrows():
                news_list.append({
                    'title': str(row.get('标题', '')),
                    'content': str(row.get('内容', '')),
                    'publish_time': str(row.get('发布时间', '')),
                    'source': '新浪财经',
                    'url': str(row.get('链接', ''))
                })
            
            logger.info(f"✅ 获取全球财经新闻（新浪） {len(news_list)} 条")
            return news_list
            
        except Exception as e:
            logger.error(f"❌ 获取全球财经新闻（新浪）失败: {e}")
            return []
    
    # ========== 快讯 ==========
    
    def get_cls_telegraph(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取财联社电报快讯
        接口: stock_info_global_cls
        数据量: 20条/次
        
        Args:
            limit: 限制数量
            
        Returns:
            快讯列表
        """
        try:
            logger.info("获取财联社电报快讯...")
            df = ak.stock_info_global_cls()
            
            if df is None or len(df) == 0:
                logger.warning("未获取到财联社快讯")
                return []
            
            df = df.head(limit)
            
            news_list = []
            for _, row in df.iterrows():
                news_list.append({
                    'title': str(row.get('标题', '')),
                    'content': str(row.get('内容', '')),
                    'publish_time': str(row.get('发布时间', '')),
                    'source': '财联社',
                    'url': ''
                })
            
            logger.info(f"✅ 获取财联社快讯 {len(news_list)} 条")
            return news_list
            
        except Exception as e:
            logger.error(f"❌ 获取财联社快讯失败: {e}")
            return []
    
    # ========== 富途牛牛全球财经 ==========
    
    def get_futu_global_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取富途牛牛全球财经新闻
        接口: stock_info_global_futu
        数据量: 20条/次
        
        Args:
            limit: 限制数量
            
        Returns:
            新闻列表
        """
        try:
            logger.info("获取富途牛牛全球财经新闻...")
            df = ak.stock_info_global_futu()
            
            if df is None or len(df) == 0:
                logger.warning("未获取到富途牛牛新闻")
                return []
            
            df = df.head(limit)
            
            news_list = []
            for _, row in df.iterrows():
                news_list.append({
                    'title': str(row.get('标题', '')),
                    'content': str(row.get('内容', ''))[:200],
                    'publish_time': str(row.get('发布时间', '')),
                    'source': '富途牛牛',
                    'url': str(row.get('链接', ''))
                })
            
            logger.info(f"✅ 获取富途牛牛新闻 {len(news_list)} 条")
            return news_list
            
        except Exception as e:
            logger.error(f"❌ 获取富途牛牛新闻失败: {e}")
            return []
    
    def get_ths_global_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取同花顺全球财经新闻
        接口: stock_info_global_ths
        数据量: 20条/次
        
        Args:
            limit: 限制数量
            
        Returns:
            新闻列表
        """
        try:
            logger.info("获取同花顺全球财经新闻...")
            df = ak.stock_info_global_ths()
            
            if df is None or len(df) == 0:
                logger.warning("未获取到同花顺新闻")
                return []
            
            df = df.head(limit)
            
            news_list = []
            for _, row in df.iterrows():
                news_list.append({
                    'title': str(row.get('标题', '')),
                    'content': str(row.get('内容', ''))[:200],
                    'publish_time': str(row.get('发布时间', '')),
                    'source': '同花顺',
                    'url': str(row.get('链接', ''))
                })
            
            logger.info(f"✅ 获取同花顺新闻 {len(news_list)} 条")
            return news_list
            
        except Exception as e:
            logger.error(f"❌ 获取同花顺新闻失败: {e}")
            return []
    
    # ========== 微博热议 ==========
    
    def get_weibo_stock_hot(self) -> List[Dict[str, Any]]:
        """
        获取微博股票热议
        接口: stock_js_weibo_report
        
        Returns:
            热议股票列表
        """
        try:
            logger.info("获取微博股票热议...")
            df = ak.stock_js_weibo_report()
            
            if df is None or len(df) == 0:
                logger.warning("未获取到微博热议")
                return []
            
            # 打印列名用于调试
            logger.info(f"微博热议数据列: {list(df.columns)}")
            
            hot_list = df.to_dict('records')
            
            logger.info(f"✅ 获取微博热议 {len(hot_list)} 条")
            return hot_list
            
        except Exception as e:
            logger.error(f"❌ 获取微博热议失败: {e}")
            return []


# 全局实例
_akshare_news_api = None

def get_akshare_news_api():
    """获取AKShare新闻API实例（单例）"""
    global _akshare_news_api
    if _akshare_news_api is None:
        _akshare_news_api = AKShareNewsAPI()
    return _akshare_news_api
