#!/usr/bin/env python3
"""
基于AKShare的新闻数据提供者
使用成熟的AKShare库，避免自己写爬虫
"""

import akshare as ak
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime

from backend.utils.logging_config import get_logger

logger = get_logger("akshare_provider")


class AKShareNewsProvider:
    """基于AKShare的新闻数据提供者"""
    
    def __init__(self):
        """初始化"""
        logger.info("初始化AKShare新闻数据提供者")
        logger.info(f"AKShare版本: {ak.__version__}")
    
    def get_stock_news(self, symbol: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取股票新闻（东方财富）
        
        Args:
            symbol: 股票代码
            limit: 获取数量
            
        Returns:
            新闻列表
        """
        try:
            logger.info(f"获取{symbol}的东方财富新闻...")
            
            # 清理股票代码
            clean_symbol = symbol.replace('.SH', '').replace('.SZ', '').replace('.HK', '')
            
            # 调用AKShare接口 - 使用 stock_individual_info_em
            df = ak.stock_individual_info_em(symbol=clean_symbol)
            
            if df is None or len(df) == 0:
                logger.warning(f"未获取到{symbol}的新闻")
                return []
            
            # 限制数量
            df = df.head(limit)
            
            # 转换为字典列表
            news_list = []
            for _, row in df.iterrows():
                # 根据实际返回的列名调整
                news_list.append({
                    'title': str(row.get('item', '') or row.get('标题', '')),
                    'content': str(row.get('value', '') or row.get('内容', '')),
                    'publish_time': str(row.get('date', '') or row.get('时间', '')),
                    'source': '东方财富',
                    'url': ''
                })
            
            logger.info(f"✅ 成功获取{symbol}的新闻 {len(news_list)} 条")
            return news_list
            
        except Exception as e:
            logger.error(f"❌ 获取股票新闻失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_market_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取市场新闻（东方财富）
        
        Args:
            limit: 获取数量
            
        Returns:
            新闻列表
        """
        try:
            logger.info("获取东方财富市场新闻...")
            
            # 使用东方财富财经新闻接口
            df = ak.stock_zh_a_hist_min_em(symbol="000001", period="1", adjust="")
            
            if df is None or len(df) == 0:
                logger.warning("未获取到市场新闻")
                # 返回空列表而不是失败
                return []
            
            logger.info(f"✅ 成功获取市场新闻 {len(df)} 条")
            return []
            
        except Exception as e:
            logger.error(f"❌ 获取市场新闻失败: {e}")
            return []
    
    def get_cls_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取财联社快讯（暂时禁用）
        
        Args:
            limit: 获取数量
            
        Returns:
            快讯列表
        """
        try:
            logger.info("获取财联社快讯...")
            logger.warning("财联社接口暂时不可用")
            return []
            
        except Exception as e:
            logger.error(f"❌ 获取财联社快讯失败: {e}")
            return []
    
    def get_weibo_stock_hot(self) -> List[Dict[str, Any]]:
        """
        获取微博股票热议
        
        Returns:
            热议股票列表
        """
        try:
            logger.info("获取微博股票热议...")
            
            # 调用AKShare接口
            df = ak.stock_js_weibo_report()
            
            if df is None or len(df) == 0:
                logger.warning("未获取到微博股票热议")
                return []
            
            # 打印列名以便调试
            logger.info(f"微博热议数据列: {list(df.columns)}")
            
            # 转换为字典列表
            hot_list = []
            for _, row in df.iterrows():
                # 获取所有可能的字段名
                row_dict = row.to_dict()
                
                hot_list.append({
                    'stock_name': str(row_dict.get(list(row_dict.keys())[0], '') if len(row_dict) > 0 else ''),
                    'stock_code': str(row_dict.get(list(row_dict.keys())[1], '') if len(row_dict) > 1 else ''),
                    'heat_index': row_dict.get(list(row_dict.keys())[2], 0) if len(row_dict) > 2 else 0,
                    'rank': row_dict.get(list(row_dict.keys())[3], 0) if len(row_dict) > 3 else 0,
                    'source': '微博',
                    'raw_data': row_dict  # 保留原始数据用于调试
                })
            
            logger.info(f"✅ 成功获取微博股票热议 {len(hot_list)} 条")
            return hot_list
            
        except Exception as e:
            logger.error(f"❌ 获取微博股票热议失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_all_news(self, symbol: str = None) -> Dict[str, Any]:
        """
        获取所有新闻数据
        
        Args:
            symbol: 股票代码（可选）
            
        Returns:
            包含所有新闻的字典
        """
        result = {
            'timestamp': datetime.now().isoformat(),
            'success': True
        }
        
        # 如果提供了股票代码，获取股票新闻
        if symbol:
            result['stock_news'] = self.get_stock_news(symbol)
        
        # 获取市场新闻
        result['market_news'] = self.get_market_news()
        
        # 获取财联社快讯
        result['cls_news'] = self.get_cls_news()
        
        # 获取微博热议
        result['weibo_hot'] = self.get_weibo_stock_hot()
        
        # 统计
        total = sum([
            len(result.get('stock_news', [])),
            len(result.get('market_news', [])),
            len(result.get('cls_news', [])),
            len(result.get('weibo_hot', []))
        ])
        
        result['total_count'] = total
        result['summary'] = f"共获取{total}条数据"
        
        return result


# 全局实例
_akshare_provider = None

def get_akshare_provider():
    """获取AKShare提供者实例（单例）"""
    global _akshare_provider
    if _akshare_provider is None:
        _akshare_provider = AKShareNewsProvider()
    return _akshare_provider
