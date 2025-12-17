"""
市场数据服务
使用AKShare获取真实的股票行情数据
"""

import akshare as ak
import pandas as pd
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from functools import lru_cache
import asyncio

from backend.utils.logging_config import get_logger

logger = get_logger("services.market_data")


class MarketDataService:
    """市场数据服务"""

    def __init__(self):
        self._cache = {}
        self._cache_time = {}
        self._cache_ttl = 60  # 缓存60秒

    def _is_cache_valid(self, key: str) -> bool:
        """检查缓存是否有效"""
        if key not in self._cache_time:
            return False
        return (datetime.now() - self._cache_time[key]).seconds < self._cache_ttl

    def _set_cache(self, key: str, value: Any):
        """设置缓存"""
        self._cache[key] = value
        self._cache_time[key] = datetime.now()

    def _get_cache(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if self._is_cache_valid(key):
            return self._cache.get(key)
        return None

    def get_realtime_quote(self, stock_code: str) -> Dict[str, Any]:
        """
        获取实时行情

        Args:
            stock_code: 股票代码（如600519、000001）

        Returns:
            实时行情数据
        """
        cache_key = f"quote_{stock_code}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        try:
            # 标准化股票代码
            code = stock_code.replace(".SH", "").replace(".SZ", "")

            # 使用AKShare获取实时行情
            # 尝试A股实时行情
            df = ak.stock_zh_a_spot_em()

            # 查找股票
            stock_data = df[df['代码'] == code]

            if stock_data.empty:
                # 尝试带前缀的代码
                stock_data = df[df['代码'].str.contains(code)]

            if stock_data.empty:
                logger.warning(f"未找到股票: {stock_code}")
                return self._get_fallback_quote(stock_code)

            row = stock_data.iloc[0]

            result = {
                "stock_code": code,
                "stock_name": row.get('名称', code),
                "current_price": float(row.get('最新价', 0)),
                "open_price": float(row.get('今开', 0)),
                "high_price": float(row.get('最高', 0)),
                "low_price": float(row.get('最低', 0)),
                "pre_close": float(row.get('昨收', 0)),
                "change": float(row.get('涨跌额', 0)),
                "change_rate": float(row.get('涨跌幅', 0)),
                "volume": float(row.get('成交量', 0)),
                "amount": float(row.get('成交额', 0)),
                "turnover_rate": float(row.get('换手率', 0)) if '换手率' in row else 0,
                "pe_ratio": float(row.get('市盈率-动态', 0)) if '市盈率-动态' in row else 0,
                "pb_ratio": float(row.get('市净率', 0)) if '市净率' in row else 0,
                "total_market_cap": float(row.get('总市值', 0)) if '总市值' in row else 0,
                "timestamp": datetime.now().isoformat(),
                "source": "akshare"
            }

            self._set_cache(cache_key, result)
            logger.info(f"获取实时行情成功: {stock_code} @ {result['current_price']}")
            return result

        except Exception as e:
            logger.error(f"获取实时行情失败: {stock_code}, {e}")
            return self._get_fallback_quote(stock_code)

    def _get_fallback_quote(self, stock_code: str) -> Dict[str, Any]:
        """获取降级行情（使用历史数据）"""
        try:
            code = stock_code.replace(".SH", "").replace(".SZ", "")
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=5)).strftime("%Y%m%d")

            # 尝试获取历史数据
            df = ak.stock_zh_a_hist(symbol=code, period="daily",
                                     start_date=start_date, end_date=end_date,
                                     adjust="qfq")

            if df.empty:
                raise ValueError("无历史数据")

            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest

            return {
                "stock_code": code,
                "stock_name": code,
                "current_price": float(latest['收盘']),
                "open_price": float(latest['开盘']),
                "high_price": float(latest['最高']),
                "low_price": float(latest['最低']),
                "pre_close": float(prev['收盘']),
                "change": float(latest['收盘'] - prev['收盘']),
                "change_rate": float((latest['收盘'] - prev['收盘']) / prev['收盘'] * 100),
                "volume": float(latest['成交量']),
                "amount": float(latest['成交额']),
                "turnover_rate": 0,
                "pe_ratio": 0,
                "pb_ratio": 0,
                "total_market_cap": 0,
                "timestamp": datetime.now().isoformat(),
                "source": "akshare_history"
            }

        except Exception as e:
            logger.error(f"获取降级行情也失败: {stock_code}, {e}")
            return {
                "stock_code": stock_code,
                "stock_name": stock_code,
                "current_price": 0,
                "change_rate": 0,
                "volume": 0,
                "timestamp": datetime.now().isoformat(),
                "source": "unavailable",
                "error": str(e)
            }

    def get_stock_name(self, stock_code: str) -> str:
        """
        获取股票名称

        Args:
            stock_code: 股票代码

        Returns:
            股票名称
        """
        quote = self.get_realtime_quote(stock_code)
        return quote.get("stock_name", stock_code)

    def get_historical_data(
        self,
        stock_code: str,
        start_date: str,
        end_date: str,
        period: str = "daily"
    ) -> pd.DataFrame:
        """
        获取历史行情数据

        Args:
            stock_code: 股票代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            period: 周期 (daily/weekly/monthly)

        Returns:
            历史数据DataFrame
        """
        try:
            code = stock_code.replace(".SH", "").replace(".SZ", "")

            df = ak.stock_zh_a_hist(
                symbol=code,
                period=period,
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )

            if df.empty:
                logger.warning(f"无历史数据: {stock_code}")
                return pd.DataFrame()

            # 标准化列名
            df = df.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount',
                '振幅': 'amplitude',
                '涨跌幅': 'change_rate',
                '涨跌额': 'change',
                '换手率': 'turnover_rate'
            })

            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')

            logger.info(f"获取历史数据成功: {stock_code}, {len(df)}条")
            return df

        except Exception as e:
            logger.error(f"获取历史数据失败: {stock_code}, {e}")
            return pd.DataFrame()

    def get_latest_news(self, stock_code: str, limit: int = 5) -> List[Dict]:
        """
        获取股票相关新闻

        Args:
            stock_code: 股票代码
            limit: 返回数量

        Returns:
            新闻列表
        """
        try:
            code = stock_code.replace(".SH", "").replace(".SZ", "")

            # 尝试获取个股新闻
            df = ak.stock_news_em(symbol=code)

            if df.empty:
                return []

            news_list = []
            for _, row in df.head(limit).iterrows():
                news_list.append({
                    "title": row.get('新闻标题', ''),
                    "content": row.get('新闻内容', ''),
                    "source": row.get('新闻来源', ''),
                    "time": row.get('发布时间', ''),
                    "url": row.get('新闻链接', '')
                })

            return news_list

        except Exception as e:
            logger.warning(f"获取新闻失败: {stock_code}, {e}")
            return []

    def get_market_overview(self) -> Dict[str, Any]:
        """
        获取市场概览

        Returns:
            市场概览数据
        """
        try:
            # 获取主要指数
            indices = {}

            # 上证指数
            try:
                sh_df = ak.stock_zh_index_spot_em()
                sh_index = sh_df[sh_df['代码'] == '000001']
                if not sh_index.empty:
                    indices['上证指数'] = {
                        'price': float(sh_index.iloc[0]['最新价']),
                        'change_rate': float(sh_index.iloc[0]['涨跌幅'])
                    }
            except:
                pass

            # 深证成指
            try:
                sz_index = sh_df[sh_df['代码'] == '399001']
                if not sz_index.empty:
                    indices['深证成指'] = {
                        'price': float(sz_index.iloc[0]['最新价']),
                        'change_rate': float(sz_index.iloc[0]['涨跌幅'])
                    }
            except:
                pass

            # 创业板指
            try:
                cy_index = sh_df[sh_df['代码'] == '399006']
                if not cy_index.empty:
                    indices['创业板指'] = {
                        'price': float(cy_index.iloc[0]['最新价']),
                        'change_rate': float(cy_index.iloc[0]['涨跌幅'])
                    }
            except:
                pass

            return {
                "indices": indices,
                "timestamp": datetime.now().isoformat(),
                "source": "akshare"
            }

        except Exception as e:
            logger.error(f"获取市场概览失败: {e}")
            return {
                "indices": {},
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }


# 全局实例
_market_data_service = None


def get_market_data_service() -> MarketDataService:
    """获取市场数据服务实例"""
    global _market_data_service
    if _market_data_service is None:
        _market_data_service = MarketDataService()
    return _market_data_service


# 便捷函数
def get_realtime_quote(stock_code: str) -> Dict[str, Any]:
    """获取实时行情"""
    return get_market_data_service().get_realtime_quote(stock_code)


def get_stock_name(stock_code: str) -> str:
    """获取股票名称"""
    return get_market_data_service().get_stock_name(stock_code)


def get_historical_data(stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """获取历史数据"""
    return get_market_data_service().get_historical_data(stock_code, start_date, end_date)
