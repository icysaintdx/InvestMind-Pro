#!/usr/bin/env python3
"""
AKShare股票数据模块
提供实时行情、历史行情、分钟数据等
优先使用TDX Native Provider获取数据，AKShare作为降级方案
"""

import akshare as ak
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from .base import AKShareBase


class AKShareStockData(AKShareBase):
    """AKShare股票数据"""

    def __init__(self):
        """初始化"""
        super().__init__()
        self._tdx_provider = None

    def _get_tdx_provider(self):
        """获取TDX Native Provider（懒加载）"""
        if self._tdx_provider is None:
            try:
                from backend.dataflows.providers.tdx_native_provider import get_tdx_native_provider
                self._tdx_provider = get_tdx_native_provider()
            except Exception as e:
                self.logger.debug(f"TDX Native Provider初始化失败: {e}")
        return self._tdx_provider

    def get_realtime_quotes(self) -> List[Dict[str, Any]]:
        """
        获取A股实时行情
        优先使用TDX Native Provider，降级到AKShare

        Returns:
            实时行情列表
        """
        self.logger.info("获取A股实时行情...")

        # 1. 优先使用TDX Native Provider
        tdx = self._get_tdx_provider()
        if tdx and tdx.is_available():
            try:
                # TDX Native不支持获取全部股票列表，跳过
                pass
            except Exception as e:
                self.logger.debug(f"TDX Native获取全部行情失败: {e}")

        # 2. 降级到AKShare（注意：这会获取5000+股票，较慢）
        df = self.safe_call(ak.stock_zh_a_spot_em)

        if df is None:
            return []

        # 转换为字典
        quotes = self.df_to_dict(df)
        self.logger.info(f"✅ 获取到{len(quotes)}条实时行情")

        return quotes

    def get_stock_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取个股实时行情
        优先使用TDX Native Provider获取单只股票，避免获取全部5000+股票

        Args:
            symbol: 股票代码（如：000001）

        Returns:
            个股行情
        """
        # 清理股票代码
        clean_symbol = symbol.replace('.SH', '').replace('.SZ', '')
        self.logger.info(f"获取{clean_symbol}实时行情...")

        # 1. 优先使用TDX Native Provider（只获取单只股票，非常快）
        tdx = self._get_tdx_provider()
        if tdx and tdx.is_available():
            try:
                quote = tdx.get_realtime_quote(clean_symbol)
                if quote:
                    self.logger.info(f"✅ TDX Native获取{clean_symbol}行情成功")
                    # 转换为AKShare格式以保持兼容
                    return {
                        '代码': clean_symbol,
                        '名称': quote.get('name', ''),
                        '最新价': quote.get('price', 0),
                        '涨跌幅': quote.get('change_pct', 0),
                        '涨跌额': quote.get('change', 0),
                        '成交量': quote.get('volume', 0),
                        '成交额': quote.get('amount', 0),
                        '今开': quote.get('open', 0),
                        '最高': quote.get('high', 0),
                        '最低': quote.get('low', 0),
                        '昨收': quote.get('pre_close', 0),
                        '换手率': 0,
                        '市盈率-动态': 0,
                        '市净率': 0,
                        '总市值': 0,
                        '流通市值': 0,
                    }
            except Exception as e:
                self.logger.debug(f"TDX Native获取{clean_symbol}行情失败: {e}")

        # 2. 降级到AKShare（注意：这会获取全部5000+股票，较慢）
        self.logger.warning(f"⚠️ TDX不可用，降级到AKShare获取{clean_symbol}行情（较慢）")
        df = self.safe_call(ak.stock_zh_a_spot_em)

        if df is None:
            return None

        # 过滤指定股票
        stock_df = df[df['代码'] == clean_symbol]

        if stock_df.empty:
            self.logger.warning(f"⚠️ 未找到{symbol}的行情数据")
            return None

        # 转换为字典
        quote = self.df_to_dict(stock_df)[0]
        self.logger.info(f"✅ 获取{symbol}行情成功")

        return quote
    
    def get_stock_hist(
        self,
        symbol: str,
        period: str = "daily",
        start_date: str = None,
        end_date: str = None,
        adjust: str = ""
    ) -> List[Dict[str, Any]]:
        """
        获取个股历史行情
        
        Args:
            symbol: 股票代码（如：000001）
            period: 周期（daily/weekly/monthly）
            start_date: 开始日期（YYYYMMDD）
            end_date: 结束日期（YYYYMMDD）
            adjust: 复权类型（qfq前复权/hfq后复权/空字符串不复权）
            
        Returns:
            历史行情列表
        """
        # 清理股票代码
        clean_symbol = symbol.replace('.SH', '').replace('.SZ', '')
        
        # 默认日期范围
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
        
        self.logger.info(f"获取{clean_symbol}历史行情: {start_date} ~ {end_date}, 周期={period}")
        
        df = self.safe_call(
            ak.stock_zh_a_hist,
            symbol=clean_symbol,
            period=period,
            start_date=start_date,
            end_date=end_date,
            adjust=adjust
        )
        
        if df is None:
            return []
        
        # 转换为字典
        hist_data = self.df_to_dict(df)
        self.logger.info(f"✅ 获取到{len(hist_data)}条历史数据")
        
        return hist_data
    
    def get_stock_hist_min(
        self,
        symbol: str,
        period: str = "5",
        adjust: str = ""
    ) -> List[Dict[str, Any]]:
        """
        获取个股分钟级行情
        
        Args:
            symbol: 股票代码（如：000001）
            period: 周期（1/5/15/30/60）
            adjust: 复权类型
            
        Returns:
            分钟行情列表
        """
        # 清理股票代码
        clean_symbol = symbol.replace('.SH', '').replace('.SZ', '')
        
        self.logger.info(f"获取{clean_symbol}分钟行情: {period}分钟")
        
        df = self.safe_call(
            ak.stock_zh_a_hist_min_em,
            symbol=clean_symbol,
            period=period,
            adjust=adjust
        )
        
        if df is None:
            return []
        
        # 转换为字典
        min_data = self.df_to_dict(df)
        self.logger.info(f"✅ 获取到{len(min_data)}条分钟数据")
        
        return min_data
    
    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取个股基本信息
        
        Args:
            symbol: 股票代码
            
        Returns:
            股票基本信息
        """
        # 清理股票代码
        clean_symbol = symbol.replace('.SH', '').replace('.SZ', '')
        
        self.logger.info(f"获取{clean_symbol}基本信息...")
        
        # 从实时行情中获取基本信息
        quote = self.get_stock_quote(clean_symbol)
        
        if not quote:
            return None
        
        # 提取关键信息
        info = {
            'code': quote.get('代码', ''),
            'name': quote.get('名称', ''),
            'price': quote.get('最新价', 0),
            'change_pct': quote.get('涨跌幅', 0),
            'change': quote.get('涨跌额', 0),
            'volume': quote.get('成交量', 0),
            'amount': quote.get('成交额', 0),
            'turnover': quote.get('换手率', 0),
            'pe': quote.get('市盈率-动态', 0),
            'pb': quote.get('市净率', 0),
            'market_cap': quote.get('总市值', 0),
            'circulating_cap': quote.get('流通市值', 0),
        }
        
        return info
    
    def search_stock(self, keyword: str) -> List[Dict[str, Any]]:
        """
        搜索股票
        优先使用本地股票列表缓存，避免每次都获取全部5000+股票

        Args:
            keyword: 关键词（股票代码或名称）

        Returns:
            匹配的股票列表
        """
        self.logger.info(f"搜索股票: {keyword}")

        # 1. 优先使用本地股票列表缓存
        try:
            from backend.dataflows.akshare.stock_list_cache import get_stock_list_cache
            cache = get_stock_list_cache()
            cached_list = cache.get_stock_list()
            if cached_list:
                import pandas as pd
                df = pd.DataFrame(cached_list)
                # 搜索匹配
                mask = (
                    df['代码'].astype(str).str.contains(keyword, na=False) |
                    df['名称'].astype(str).str.contains(keyword, na=False)
                )
                result_df = df[mask]
                if not result_df.empty:
                    results = result_df.to_dict('records')
                    self.logger.info(f"✅ 从缓存找到{len(results)}个匹配结果")
                    return results
        except Exception as e:
            self.logger.debug(f"股票列表缓存搜索失败: {e}")

        # 2. 降级到AKShare（注意：这会获取全部5000+股票，较慢）
        self.logger.warning(f"⚠️ 缓存不可用，降级到AKShare搜索（较慢）")
        df = self.safe_call(ak.stock_zh_a_spot_em)

        if df is None:
            return []

        # 搜索匹配
        mask = (
            df['代码'].str.contains(keyword, na=False) |
            df['名称'].str.contains(keyword, na=False)
        )

        result_df = df[mask]

        if result_df.empty:
            self.logger.warning(f"⚠️ 未找到匹配的股票: {keyword}")
            return []

        # 转换为字典
        results = self.df_to_dict(result_df)
        self.logger.info(f"✅ 找到{len(results)}个匹配结果")

        return results


# 全局实例
_stock_data = None

def get_stock_data():
    """获取股票数据实例（单例）"""
    global _stock_data
    if _stock_data is None:
        _stock_data = AKShareStockData()
    return _stock_data
