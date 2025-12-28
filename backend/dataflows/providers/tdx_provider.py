#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TDX (通达信) 数据源 Provider - 完整版
封装所有32个TDX API接口，提供统一的数据访问层

适用场景：
1. K线图表展示（支持多周期：分钟/日/周/月）
2. 实时行情监控
3. 技术指标计算
4. 虚拟交易模块的行情数据
5. ETF数据获取
6. 指数数据获取
7. 交易日查询
8. 批量数据入库任务

优先级: TDX > AKShare > Tushare > 聚合数据

配置：
在 .env 中设置 TDX_API_URL，默认为 http://127.0.0.1:8080

API接口列表（32个）：
基础接口(1-6): quote, kline, minute, trade, search, stock-info
扩展接口(7-13): codes, batch-quote, kline-history, index, market-stats, server-status, health
任务接口(14-18): tasks/pull-kline, tasks/pull-trade, tasks, tasks/{id}, tasks/{id}/cancel
数据服务(19-30): etf, trade-history, minute-trade-all, workday, market-count, stock-codes,
                 etf-codes, kline-all, index/all, trade-history/full, workday/range, income
全量K线(31-32): kline-all/tdx, kline-all/ths
"""

import os
import logging
import requests
import pandas as pd
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from functools import lru_cache
from enum import Enum

# 导入统一日志系统
try:
    from backend.utils.logging_config import get_logger
    logger = get_logger('tdx_provider')
except ImportError:
    logger = logging.getLogger(__name__)


class KlineType(Enum):
    """K线类型枚举"""
    MINUTE1 = "minute1"
    MINUTE5 = "minute5"
    MINUTE15 = "minute15"
    MINUTE30 = "minute30"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class TDXProvider:
    """
    通达信数据源Provider - 完整版
    封装所有32个TDX API接口
    """

    # K线类型映射
    KLINE_TYPES = {
        '1m': 'minute1',
        '5m': 'minute5',
        '15m': 'minute15',
        '30m': 'minute30',
        '60m': 'hour',
        '1h': 'hour',
        'day': 'day',
        'daily': 'day',
        'week': 'week',
        'weekly': 'week',
        'month': 'month',
        'monthly': 'month',
        'quarter': 'quarter',
        'year': 'year',
        # 直接映射
        'minute1': 'minute1',
        'minute5': 'minute5',
        'minute15': 'minute15',
        'minute30': 'minute30',
        'hour': 'hour'
    }

    # 类级别的可用性缓存（避免重复检测）
    _global_available = None
    _global_check_time = None
    _AVAILABILITY_CACHE_SECONDS = 300  # 5分钟内不重复检测

    def __init__(self, base_url: str = None, timeout: int = 30):
        """
        初始化TDX数据源

        Args:
            base_url: TDX API地址，默认从环境变量读取
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url or os.getenv('TDX_API_URL', 'http://127.0.0.1:8080')
        self.base_url = self.base_url.rstrip('/')
        self.timeout = timeout

        # 只在首次初始化时打印日志
        if TDXProvider._global_available is None:
            logger.info(f"📡 TDX Provider 初始化，API地址: {self.base_url}")

    def _request(self, method: str, endpoint: str, params: Dict = None,
                 json_data: Dict = None, timeout: int = None) -> Optional[Dict]:
        """
        发送HTTP请求的统一方法

        Args:
            method: HTTP方法 (GET/POST)
            endpoint: API端点
            params: URL参数
            json_data: JSON请求体
            timeout: 超时时间

        Returns:
            Dict: API响应数据，失败返回None
        """
        url = f"{self.base_url}{endpoint}"
        timeout = timeout or self.timeout

        try:
            if method.upper() == 'GET':
                response = requests.get(url, params=params, timeout=timeout)
            elif method.upper() == 'POST':
                response = requests.post(url, json=json_data, timeout=timeout)
            else:
                logger.error(f"不支持的HTTP方法: {method}")
                return None

            if response.status_code != 200:
                logger.warning(f"TDX API请求失败: HTTP {response.status_code}")
                return None

            data = response.json()

            if data.get('code') != 0:
                logger.warning(f"TDX API返回错误: {data.get('message', '未知错误')}")
                return None

            return data.get('data')

        except requests.exceptions.Timeout:
            logger.error(f"TDX API请求超时: {url}")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"TDX API连接失败: {url}")
            return None
        except Exception as e:
            logger.error(f"TDX API请求异常: {e}")
            return None

    def is_available(self) -> bool:
        """检查TDX服务是否可用（带5分钟缓存）"""
        now = datetime.now()

        # 检查缓存是否有效
        if TDXProvider._global_available is not None and TDXProvider._global_check_time is not None:
            elapsed = (now - TDXProvider._global_check_time).total_seconds()
            if elapsed < TDXProvider._AVAILABILITY_CACHE_SECONDS:
                # 缓存有效，直接返回
                return TDXProvider._global_available

        try:
            response = requests.get(
                f"{self.base_url}/api/health",
                timeout=1  # 减少超时时间到1秒，本地服务应该快速响应
            )
            TDXProvider._global_available = response.status_code == 200
            TDXProvider._global_check_time = now
            if TDXProvider._global_available:
                logger.info("✅ TDX HTTP服务可用")
            else:
                logger.debug("TDX HTTP服务不可用（HTTP状态码非200）")
        except Exception as e:
            # 只在首次检测失败时打印日志（debug级别，减少噪音）
            if TDXProvider._global_available is None:
                logger.debug(f"TDX HTTP服务不可用: {str(e)[:50]}")
            TDXProvider._global_available = False
            TDXProvider._global_check_time = now

        return TDXProvider._global_available

    def reset_availability(self):
        """重置可用性状态，强制重新检测"""
        TDXProvider._global_available = None
        TDXProvider._global_check_time = None

    # ==================== 基础数据接口 (1-6) ====================

    def get_quote(self, codes: Union[str, List[str]]) -> Optional[List[Dict]]:
        """
        1. 获取五档行情

        Args:
            codes: 股票代码或代码列表

        Returns:
            List[Dict]: 行情数据列表
        """
        if isinstance(codes, list):
            codes = ','.join(codes)

        return self._request('GET', '/api/quote', params={'code': codes})

    def get_realtime_quote(self, codes: List[str]) -> List[Dict]:
        """
        获取实时行情（五档盘口）

        Args:
            codes: 股票代码列表，如 ['000001', '600519']

        Returns:
            行情数据列表
        """
        if not self.is_available():
            logger.warning("TDX服务不可用")
            return []

        try:
            # 支持单个代码或列表
            if isinstance(codes, str):
                codes = [codes]

            code_param = ','.join(codes)
            response = requests.get(
                f"{self.base_url}/api/quote",
                params={'code': code_param},
                timeout=self.timeout
            )

            result = response.json()
            if result.get('code') != 0:
                logger.error(f"TDX获取行情失败: {result.get('message')}")
                return []

            quotes = result.get('data', [])

            # 转换为标准格式
            formatted_quotes = []
            for quote in quotes:
                k_data = quote.get('K', {})
                formatted_quotes.append({
                    'code': quote.get('Code', ''),
                    'name': self._get_stock_name(quote.get('Code', '')),
                    'current_price': k_data.get('Close', 0) / 1000,  # 厘转元
                    'open': k_data.get('Open', 0) / 1000,
                    'high': k_data.get('High', 0) / 1000,
                    'low': k_data.get('Low', 0) / 1000,
                    'pre_close': k_data.get('Last', 0) / 1000,
                    'volume': quote.get('TotalHand', 0),  # 手
                    'amount': quote.get('Amount', 0) / 1000,  # 厘转元
                    'change_pct': self._calc_change_pct(
                        k_data.get('Close', 0),
                        k_data.get('Last', 0)
                    ),
                    'bid_prices': self._extract_bid_prices(quote),
                    'ask_prices': self._extract_ask_prices(quote),
                    'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'data_source': 'tdx'
                })

            return formatted_quotes

        except Exception as e:
            logger.error(f"TDX获取行情异常: {e}")
            return []

    def get_kline(self, code: str, kline_type: str = 'day',
                  limit: int = 200) -> Optional[pd.DataFrame]:
        """
        获取K线数据

        Args:
            code: 股票代码
            kline_type: K线类型 (1m/5m/15m/30m/60m/day/week/month)
            limit: 返回条数

        Returns:
            K线数据DataFrame，包含列：date, open, high, low, close, volume, amount
        """
        if not self.is_available():
            logger.warning("TDX服务不可用")
            return None

        try:
            # 转换K线类型
            tdx_type = self.KLINE_TYPES.get(kline_type.lower(), 'day')

            response = requests.get(
                f"{self.base_url}/api/kline",
                params={'code': code, 'type': tdx_type},
                timeout=self.timeout
            )

            result = response.json()
            if result.get('code') != 0:
                logger.error(f"TDX获取K线失败: {result.get('message')}")
                return None

            kline_list = result.get('data', {}).get('List', [])
            if not kline_list:
                logger.warning(f"TDX未返回 {code} 的K线数据")
                return None

            # 转换为DataFrame
            rows = []
            for item in kline_list:
                time_str = item.get('Time', '')
                if 'T' in time_str:
                    date_str = time_str.split('T')[0]
                else:
                    date_str = time_str

                rows.append({
                    'date': date_str,
                    'open': item.get('Open', 0) / 1000,
                    'high': item.get('High', 0) / 1000,
                    'low': item.get('Low', 0) / 1000,
                    'close': item.get('Close', 0) / 1000,
                    'volume': item.get('Volume', 0),
                    'amount': item.get('Amount', 0) / 1000,
                    'pre_close': item.get('Last', 0) / 1000
                })

            df = pd.DataFrame(rows)

            # 按日期排序（TDX返回的可能是倒序）
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)

            # 限制返回条数
            if len(df) > limit:
                df = df.tail(limit).reset_index(drop=True)

            logger.info(f"TDX获取 {code} K线成功，共{len(df)}条")
            return df

        except Exception as e:
            logger.error(f"TDX获取K线异常: {e}")
            return None

    def get_minute_data(self, code: str, date: str = None) -> Optional[pd.DataFrame]:
        """
        获取分时数据

        Args:
            code: 股票代码
            date: 日期，格式YYYYMMDD，默认今天

        Returns:
            分时数据DataFrame
        """
        if not self.is_available():
            return None

        try:
            params = {'code': code}
            if date:
                params['date'] = date

            response = requests.get(
                f"{self.base_url}/api/minute",
                params=params,
                timeout=self.timeout
            )

            result = response.json()
            if result.get('code') != 0:
                return None

            minute_list = result.get('data', {}).get('List', [])
            if not minute_list:
                return None

            rows = []
            for item in minute_list:
                rows.append({
                    'time': item.get('Time', ''),
                    'price': item.get('Price', 0) / 1000,
                    'avg_price': item.get('AvgPrice', 0) / 1000,
                    'volume': item.get('Volume', 0)
                })

            return pd.DataFrame(rows)

        except Exception as e:
            logger.error(f"TDX获取分时数据异常: {e}")
            return None

    def get_trade_data(self, code: str, date: str = None) -> Optional[pd.DataFrame]:
        """
        获取分时成交数据

        Args:
            code: 股票代码
            date: 日期

        Returns:
            成交数据DataFrame
        """
        if not self.is_available():
            return None

        try:
            params = {'code': code}
            if date:
                params['date'] = date

            response = requests.get(
                f"{self.base_url}/api/trade",
                params=params,
                timeout=self.timeout
            )

            result = response.json()
            if result.get('code') != 0:
                return None

            trade_list = result.get('data', {}).get('List', [])
            if not trade_list:
                return None

            rows = []
            for item in trade_list:
                rows.append({
                    'time': item.get('Time', ''),
                    'price': item.get('Price', 0) / 1000,
                    'volume': item.get('Volume', 0),
                    'direction': item.get('Direction', 0)  # 买卖方向
                })

            return pd.DataFrame(rows)

        except Exception as e:
            logger.error(f"TDX获取成交数据异常: {e}")
            return None

    def search_stock(self, keyword: str, limit: int = 20) -> List[Dict]:
        """
        搜索股票

        Args:
            keyword: 搜索关键词（代码或名称）
            limit: 返回数量限制

        Returns:
            搜索结果列表
        """
        if not self.is_available():
            return []

        try:
            response = requests.get(
                f"{self.base_url}/api/search",
                params={'keyword': keyword},
                timeout=self.timeout
            )

            result = response.json()
            if result.get('code') != 0:
                return []

            results = result.get('data', [])[:limit]
            return [
                {
                    'code': item.get('code', ''),
                    'name': item.get('name', ''),
                    'exchange': item.get('exchange', '')
                }
                for item in results
            ]

        except Exception as e:
            logger.error(f"TDX搜索股票异常: {e}")
            return []

    def get_stock_info(self, code: str) -> Optional[Dict]:
        """
        获取股票综合信息（行情+K线+分时）

        Args:
            code: 股票代码

        Returns:
            综合信息字典
        """
        if not self.is_available():
            return None

        try:
            response = requests.get(
                f"{self.base_url}/api/stock-info",
                params={'code': code},
                timeout=self.timeout
            )

            result = response.json()
            if result.get('code') != 0:
                return None

            return result.get('data', {})

        except Exception as e:
            logger.error(f"TDX获取股票信息异常: {e}")
            return None

    def get_market_stats(self) -> Optional[Dict]:
        """
        获取市场统计数据

        Returns:
            市场统计信息
        """
        if not self.is_available():
            return None

        try:
            response = requests.get(
                f"{self.base_url}/api/market-stats",
                timeout=self.timeout
            )

            result = response.json()
            if result.get('code') != 0:
                return None

            return result.get('data', {})

        except Exception as e:
            logger.error(f"TDX获取市场统计异常: {e}")
            return None

    def get_index_quote(self, index_codes: List[str] = None) -> List[Dict]:
        """
        获取指数行情

        Args:
            index_codes: 指数代码列表，默认获取主要指数

        Returns:
            指数行情列表
        """
        if index_codes is None:
            index_codes = ['000001', '399001', '399006']  # 上证、深成、创业板

        return self.get_realtime_quote(index_codes)

    def calculate_technical_indicators(self, code: str,
                                       kline_type: str = 'day') -> Optional[Dict]:
        """
        计算技术指标

        Args:
            code: 股票代码
            kline_type: K线类型

        Returns:
            技术指标字典
        """
        df = self.get_kline(code, kline_type, limit=200)
        if df is None or len(df) < 60:
            return None

        try:
            # 计算均线
            df['ma5'] = df['close'].rolling(window=5).mean()
            df['ma10'] = df['close'].rolling(window=10).mean()
            df['ma20'] = df['close'].rolling(window=20).mean()
            df['ma60'] = df['close'].rolling(window=60).mean()

            # 计算MACD
            df = self._calculate_macd(df)

            # 计算RSI
            df = self._calculate_rsi(df)

            # 计算KDJ
            df = self._calculate_kdj(df)

            # 计算布林带
            df = self._calculate_bollinger(df)

            # 计算量能均线
            df['vol_ma5'] = df['volume'].rolling(window=5).mean()
            df['vol_ma10'] = df['volume'].rolling(window=10).mean()

            # 取最新数据
            latest = df.iloc[-1]

            # 判断趋势
            current_price = float(latest['close'])
            ma5 = float(latest['ma5']) if pd.notna(latest['ma5']) else current_price
            ma20 = float(latest['ma20']) if pd.notna(latest['ma20']) else current_price
            ma60 = float(latest['ma60']) if pd.notna(latest['ma60']) else current_price

            if current_price > ma5 > ma20 > ma60:
                trend = 'up'
            elif current_price < ma5 < ma20 < ma60:
                trend = 'down'
            else:
                trend = 'sideways'

            return {
                'code': code,
                'ma5': ma5,
                'ma10': float(latest['ma10']) if pd.notna(latest['ma10']) else None,
                'ma20': ma20,
                'ma60': ma60,
                'trend': trend,
                'macd_dif': float(latest['dif']) if pd.notna(latest['dif']) else None,
                'macd_dea': float(latest['dea']) if pd.notna(latest['dea']) else None,
                'macd': float(latest['macd']) if pd.notna(latest['macd']) else None,
                'rsi6': float(latest['rsi6']) if pd.notna(latest['rsi6']) else None,
                'rsi12': float(latest['rsi12']) if pd.notna(latest['rsi12']) else None,
                'rsi24': float(latest['rsi24']) if pd.notna(latest['rsi24']) else None,
                'kdj_k': float(latest['kdj_k']) if pd.notna(latest['kdj_k']) else None,
                'kdj_d': float(latest['kdj_d']) if pd.notna(latest['kdj_d']) else None,
                'kdj_j': float(latest['kdj_j']) if pd.notna(latest['kdj_j']) else None,
                'boll_upper': float(latest['boll_upper']) if pd.notna(latest['boll_upper']) else None,
                'boll_mid': float(latest['boll_mid']) if pd.notna(latest['boll_mid']) else None,
                'boll_lower': float(latest['boll_lower']) if pd.notna(latest['boll_lower']) else None,
                'vol_ma5': float(latest['vol_ma5']) if pd.notna(latest['vol_ma5']) else None,
                'volume_ratio': float(latest['volume']) / float(latest['vol_ma5']) if latest['vol_ma5'] > 0 else 1.0,
                'data_source': 'tdx'
            }

        except Exception as e:
            logger.error(f"计算技术指标失败: {e}")
            return None

    # ========== 私有方法 ==========

    def _get_stock_name(self, code: str) -> str:
        """获取股票名称"""
        results = self.search_stock(code, limit=1)
        if results:
            return results[0].get('name', code)
        return code

    def _calc_change_pct(self, current: float, pre_close: float) -> float:
        """计算涨跌幅"""
        if pre_close == 0:
            return 0.0
        return round((current - pre_close) / pre_close * 100, 2)

    def _extract_bid_prices(self, quote: Dict) -> List[Dict]:
        """提取买盘价格"""
        bids = []
        for i in range(1, 6):
            price_key = f'Bid{i}'
            vol_key = f'BidVol{i}'
            if price_key in quote:
                bids.append({
                    'price': quote.get(price_key, 0) / 1000,
                    'volume': quote.get(vol_key, 0)
                })
        return bids

    def _extract_ask_prices(self, quote: Dict) -> List[Dict]:
        """提取卖盘价格"""
        asks = []
        for i in range(1, 6):
            price_key = f'Ask{i}'
            vol_key = f'AskVol{i}'
            if price_key in quote:
                asks.append({
                    'price': quote.get(price_key, 0) / 1000,
                    'volume': quote.get(vol_key, 0)
                })
        return asks

    def _calculate_macd(self, df: pd.DataFrame,
                        fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """计算MACD"""
        ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
        df['dif'] = ema_fast - ema_slow
        df['dea'] = df['dif'].ewm(span=signal, adjust=False).mean()
        df['macd'] = (df['dif'] - df['dea']) * 2
        return df

    def _calculate_rsi(self, df: pd.DataFrame, periods: List[int] = [6, 12, 24]) -> pd.DataFrame:
        """计算RSI"""
        for period in periods:
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            df[f'rsi{period}'] = 100 - (100 / (1 + rs))
        return df

    def _calculate_kdj(self, df: pd.DataFrame, n: int = 9,
                       m1: int = 3, m2: int = 3) -> pd.DataFrame:
        """计算KDJ"""
        low_list = df['low'].rolling(window=n).min()
        high_list = df['high'].rolling(window=n).max()
        rsv = (df['close'] - low_list) / (high_list - low_list) * 100
        df['kdj_k'] = rsv.ewm(com=m1-1, adjust=False).mean()
        df['kdj_d'] = df['kdj_k'].ewm(com=m2-1, adjust=False).mean()
        df['kdj_j'] = 3 * df['kdj_k'] - 2 * df['kdj_d']
        return df

    def _calculate_bollinger(self, df: pd.DataFrame,
                             period: int = 20, std_num: int = 2) -> pd.DataFrame:
        """计算布林带"""
        df['boll_mid'] = df['close'].rolling(window=period).mean()
        std = df['close'].rolling(window=period).std()
        df['boll_upper'] = df['boll_mid'] + std_num * std
        df['boll_lower'] = df['boll_mid'] - std_num * std
        return df

    # ==================== 扩展接口 (7-13) ====================

    def get_codes(self, exchange: str = 'all') -> Optional[Dict]:
        """
        7. 获取股票代码列表

        Args:
            exchange: 交易所代码 (sh/sz/bj/all)

        Returns:
            Dict: {total, exchanges, codes}
        """
        return self._request('GET', '/api/codes', params={'exchange': exchange})

    def batch_get_quote(self, codes: List[str]) -> Optional[List[Dict]]:
        """
        8. 批量获取行情

        Args:
            codes: 股票代码列表（最多50只）

        Returns:
            List[Dict]: 行情数据列表
        """
        if len(codes) > 50:
            logger.warning("批量查询最多支持50只股票，已截断")
            codes = codes[:50]

        return self._request('POST', '/api/batch-quote', json_data={'codes': codes})

    def get_kline_history(self, code: str, ktype: str = 'day',
                          start_date: str = None, end_date: str = None,
                          limit: int = 100) -> Optional[Dict]:
        """
        9. 获取历史K线

        Args:
            code: 股票代码
            ktype: K线类型
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            limit: 返回条数，默认100，最大800

        Returns:
            Dict: K线数据
        """
        tdx_type = self.KLINE_TYPES.get(ktype.lower(), 'day')
        params = {'code': code, 'type': tdx_type, 'limit': min(limit, 800)}
        if start_date:
            params['start_date'] = start_date.replace('-', '')
        if end_date:
            params['end_date'] = end_date.replace('-', '')

        return self._request('GET', '/api/kline-history', params=params)

    def get_index(self, code: str, ktype: str = 'day') -> Optional[Dict]:
        """
        10. 获取指数数据

        Args:
            code: 指数代码 (如: sh000001, sz399001)
            ktype: K线类型

        Returns:
            Dict: 指数K线数据
        """
        tdx_type = self.KLINE_TYPES.get(ktype.lower(), 'day')
        params = {'code': code, 'type': tdx_type}
        return self._request('GET', '/api/index', params=params)

    def get_server_status(self) -> Optional[Dict]:
        """
        11. 获取服务状态

        Returns:
            Dict: {status, connected, version, uptime}
        """
        return self._request('GET', '/api/server-status', timeout=5)

    def health_check(self) -> bool:
        """
        12. 健康检查

        Returns:
            bool: 服务是否健康
        """
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    # ==================== 任务管理接口 (14-18) ====================

    def create_pull_kline_task(self, codes: List[str] = None, tables: List[str] = None,
                                limit: int = 1, start_date: str = None,
                                directory: str = None) -> Optional[str]:
        """
        14. 创建批量K线入库任务

        Args:
            codes: 股票代码列表，默认全部A股
            tables: K线类型列表，默认['day']
            limit: 并发数量，默认1
            start_date: 起始日期阈值
            directory: 存储目录

        Returns:
            str: 任务ID
        """
        payload = {}
        if codes:
            payload['codes'] = codes
        if tables:
            payload['tables'] = tables
        if limit:
            payload['limit'] = limit
        if start_date:
            payload['start_date'] = start_date
        if directory:
            payload['dir'] = directory

        data = self._request('POST', '/api/tasks/pull-kline', json_data=payload)
        return data.get('task_id') if data else None

    def create_pull_trade_task(self, code: str, start_year: int = None,
                                end_year: int = None, directory: str = None) -> Optional[str]:
        """
        15. 创建分时成交入库任务

        Args:
            code: 股票代码
            start_year: 起始年份，默认2000
            end_year: 结束年份，默认当年
            directory: 输出目录

        Returns:
            str: 任务ID
        """
        payload = {'code': code}
        if start_year:
            payload['start_year'] = start_year
        if end_year:
            payload['end_year'] = end_year
        if directory:
            payload['dir'] = directory

        data = self._request('POST', '/api/tasks/pull-trade', json_data=payload)
        return data.get('task_id') if data else None

    def list_tasks(self) -> Optional[List[Dict]]:
        """
        16. 查询任务列表

        Returns:
            List[Dict]: 任务列表
        """
        return self._request('GET', '/api/tasks')

    def get_task(self, task_id: str) -> Optional[Dict]:
        """
        17. 查询任务详情

        Args:
            task_id: 任务ID

        Returns:
            Dict: 任务详情
        """
        return self._request('GET', f'/api/tasks/{task_id}')

    def cancel_task(self, task_id: str) -> bool:
        """
        18. 取消任务

        Args:
            task_id: 任务ID

        Returns:
            bool: 是否成功
        """
        try:
            response = requests.post(f"{self.base_url}/api/tasks/{task_id}/cancel", timeout=10)
            return response.status_code == 200
        except Exception:
            return False

    # ==================== 新增数据服务接口 (19-30) ====================

    def get_etf_list(self, exchange: str = None, limit: int = None) -> Optional[Dict]:
        """
        19. 获取ETF基金列表

        Args:
            exchange: 交易所 (sh/sz/all)
            limit: 返回条数限制

        Returns:
            Dict: {total, list}
        """
        params = {}
        if exchange:
            params['exchange'] = exchange
        if limit:
            params['limit'] = limit

        return self._request('GET', '/api/etf', params=params)

    def get_trade_history(self, code: str, date: str, start: int = 0,
                          count: int = 2000) -> Optional[Dict]:
        """
        20. 获取历史分时成交（分页）

        Args:
            code: 股票代码
            date: 交易日期 (YYYYMMDD)
            start: 起始游标，默认0
            count: 返回条数，默认2000，最大2000

        Returns:
            Dict: {Count, List}
        """
        params = {
            'code': code,
            'date': date.replace('-', ''),
            'start': start,
            'count': min(count, 2000)
        }
        return self._request('GET', '/api/trade-history', params=params)

    def get_minute_trade_all(self, code: str, date: str = None) -> Optional[Dict]:
        """
        21. 获取全天分时成交

        Args:
            code: 股票代码
            date: 交易日期 (YYYYMMDD)，默认当天

        Returns:
            Dict: {Count, List}
        """
        params = {'code': code}
        if date:
            params['date'] = date.replace('-', '')

        return self._request('GET', '/api/minute-trade-all', params=params)

    def get_workday(self, date: str = None, count: int = 1) -> Optional[Dict]:
        """
        22. 查询交易日信息

        Args:
            date: 查询日期 (YYYYMMDD或YYYY-MM-DD)，默认当天
            count: 返回的前后交易日数量，范围1-30，默认1

        Returns:
            Dict: {date, is_workday, next, previous}
        """
        params = {}
        if date:
            params['date'] = date.replace('-', '')
        if count:
            params['count'] = min(count, 30)

        return self._request('GET', '/api/workday', params=params)

    def get_market_count(self) -> Optional[Dict]:
        """
        23. 获取市场证券数量

        Returns:
            Dict: {total, exchanges}
        """
        return self._request('GET', '/api/market-count')

    def get_stock_codes(self, limit: int = None, prefix: bool = True) -> Optional[Dict]:
        """
        24. 获取全部股票代码

        Args:
            limit: 返回条数限制
            prefix: 是否包含交易所前缀，默认True

        Returns:
            Dict: {count, list}
        """
        params = {}
        if limit:
            params['limit'] = limit
        if not prefix:
            params['prefix'] = 'false'

        return self._request('GET', '/api/stock-codes', params=params)

    def get_etf_codes(self, limit: int = None, prefix: bool = True) -> Optional[Dict]:
        """
        25. 获取全部ETF代码

        Args:
            limit: 返回条数限制
            prefix: 是否包含交易所前缀，默认True

        Returns:
            Dict: {count, list}
        """
        params = {}
        if limit:
            params['limit'] = limit
        if not prefix:
            params['prefix'] = 'false'

        return self._request('GET', '/api/etf-codes', params=params)

    def get_kline_all(self, code: str, ktype: str = 'day', limit: int = None) -> Optional[Dict]:
        """
        26. 获取股票全部历史K线

        Args:
            code: 股票代码
            ktype: K线类型
            limit: 返回条数限制

        Returns:
            Dict: {count, list, meta}
        """
        tdx_type = self.KLINE_TYPES.get(ktype.lower(), 'day')
        params = {'code': code, 'type': tdx_type}
        if limit:
            params['limit'] = limit

        # 全量数据可能较大，增加超时时间
        return self._request('GET', '/api/kline-all', params=params, timeout=60)

    def get_index_all(self, code: str, ktype: str = 'day', limit: int = None) -> Optional[Dict]:
        """
        27. 获取指数全部历史K线

        Args:
            code: 指数代码
            ktype: K线类型
            limit: 返回条数限制

        Returns:
            Dict: {count, list, meta}
        """
        tdx_type = self.KLINE_TYPES.get(ktype.lower(), 'day')
        params = {'code': code, 'type': tdx_type}
        if limit:
            params['limit'] = limit

        return self._request('GET', '/api/index/all', params=params, timeout=60)

    def get_trade_history_full(self, code: str, before: str = None,
                                limit: int = None) -> Optional[Dict]:
        """
        28. 获取上市以来分时成交

        Args:
            code: 股票代码
            before: 截止日期 (YYYYMMDD或YYYY-MM-DD)，默认今日
            limit: 返回条数限制

        Returns:
            Dict: {count, list}
        """
        params = {'code': code}
        if before:
            params['before'] = before.replace('-', '')
        if limit:
            params['limit'] = limit

        return self._request('GET', '/api/trade-history/full', params=params, timeout=120)

    def get_workday_range(self, start: str, end: str) -> Optional[Dict]:
        """
        29. 获取交易日范围

        Args:
            start: 起始日期 (YYYYMMDD或YYYY-MM-DD)
            end: 结束日期 (YYYYMMDD或YYYY-MM-DD)

        Returns:
            Dict: {list}
        """
        params = {
            'start': start.replace('-', ''),
            'end': end.replace('-', '')
        }
        return self._request('GET', '/api/workday/range', params=params)

    def get_income(self, code: str, start_date: str, days: List[int] = None) -> Optional[Dict]:
        """
        30. 计算收益区间指标

        Args:
            code: 股票代码
            start_date: 基准日期 (YYYYMMDD或YYYY-MM-DD)
            days: 天数偏移列表，默认[5,10,20,60,120]

        Returns:
            Dict: {count, list}
        """
        params = {'code': code, 'start_date': start_date.replace('-', '')}
        if days:
            params['days'] = ','.join(str(d) for d in days)

        return self._request('GET', '/api/income', params=params)

    # ==================== 全量历史K线接口 (31-32) ====================

    def get_kline_all_tdx(self, code: str, ktype: str = 'day',
                          limit: int = None) -> Optional[Dict]:
        """
        31. 获取通达信原始历史K线（不复权）

        Args:
            code: 股票代码（6位数字）
            ktype: K线类型
            limit: 结果截断条数

        Returns:
            Dict: {count, list, meta}
        """
        tdx_type = self.KLINE_TYPES.get(ktype.lower(), 'day')
        params = {'code': code, 'type': tdx_type}
        if limit:
            params['limit'] = limit

        return self._request('GET', '/api/kline-all/tdx', params=params, timeout=60)

    def get_kline_all_ths(self, code: str, ktype: str = 'day',
                          limit: int = None) -> Optional[Dict]:
        """
        32. 获取同花顺前复权历史K线

        Args:
            code: 股票代码
            ktype: K线类型 (仅支持day/week/month)
            limit: 结果截断条数

        Returns:
            Dict: {count, list, meta}
        """
        if ktype.lower() not in ['day', 'week', 'month', 'daily', 'weekly', 'monthly']:
            logger.warning(f"同花顺前复权K线仅支持day/week/month，当前: {ktype}")
            return None

        tdx_type = self.KLINE_TYPES.get(ktype.lower(), 'day')
        params = {'code': code, 'type': tdx_type}
        if limit:
            params['limit'] = limit

        return self._request('GET', '/api/kline-all/ths', params=params, timeout=60)

    # ==================== 数据转换辅助方法 ====================

    def convert_price(self, price_li: int) -> float:
        """
        将厘转换为元

        Args:
            price_li: 价格（厘）

        Returns:
            float: 价格（元）
        """
        return price_li / 1000.0

    def convert_volume(self, volume_hand: int) -> int:
        """
        将手转换为股

        Args:
            volume_hand: 成交量（手）

        Returns:
            int: 成交量（股）
        """
        return volume_hand * 100

    def kline_to_dataframe(self, kline_data: Dict) -> Optional[pd.DataFrame]:
        """
        将K线数据转换为DataFrame

        Args:
            kline_data: K线数据 {Count, List}

        Returns:
            pd.DataFrame: K线DataFrame
        """
        if not kline_data or 'List' not in kline_data:
            return None

        df = pd.DataFrame(kline_data['List'])

        if df.empty:
            return None

        # 转换价格单位（厘 -> 元）
        price_cols = ['Open', 'High', 'Low', 'Close', 'Last']
        for col in price_cols:
            if col in df.columns:
                df[col] = df[col] / 1000.0

        # 转换成交额单位（厘 -> 元）
        if 'Amount' in df.columns:
            df['Amount'] = df['Amount'] / 1000.0

        # 转换时间列
        if 'Time' in df.columns:
            df['Time'] = pd.to_datetime(df['Time'])
            df = df.sort_values('Time', ascending=True)

        # 重命名列为标准格式
        column_mapping = {
            'Time': 'date',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume',
            'Amount': 'amount',
            'Last': 'pre_close'
        }
        df = df.rename(columns=column_mapping)

        return df

    def quote_to_dict(self, quote_data: Dict) -> Dict:
        """
        将行情数据转换为标准字典格式

        Args:
            quote_data: 原始行情数据

        Returns:
            Dict: 标准化的行情数据
        """
        if not quote_data:
            return {}

        k = quote_data.get('K', {})

        return {
            'code': quote_data.get('Code', ''),
            'exchange': 'sh' if quote_data.get('Exchange') == 0 else 'sz',
            'last_price': self.convert_price(k.get('Close', 0)),
            'open': self.convert_price(k.get('Open', 0)),
            'high': self.convert_price(k.get('High', 0)),
            'low': self.convert_price(k.get('Low', 0)),
            'prev_close': self.convert_price(k.get('Last', 0)),
            'volume': quote_data.get('TotalHand', 0),
            'amount': self.convert_price(quote_data.get('Amount', 0)),
            'buy_levels': [
                {
                    'price': self.convert_price(level.get('Price', 0)),
                    'volume': level.get('Number', 0) // 100  # 股转手
                }
                for level in quote_data.get('BuyLevel', [])
            ],
            'sell_levels': [
                {
                    'price': self.convert_price(level.get('Price', 0)),
                    'volume': level.get('Number', 0) // 100
                }
                for level in quote_data.get('SellLevel', [])
            ]
        }

    # ==================== 高级数据获取方法（带日期范围） ====================

    def get_kline_by_date_range(self, code: str, start_date: str, end_date: str,
                                 ktype: str = 'day') -> Optional[pd.DataFrame]:
        """
        按日期范围获取K线数据

        Args:
            code: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            ktype: K线类型

        Returns:
            pd.DataFrame: K线数据
        """
        if not self.is_available():
            return None

        try:
            # 使用历史K线接口
            data = self.get_kline_history(code, ktype, start_date, end_date, limit=800)
            if not data:
                # 回退到全量K线接口
                data = self.get_kline_all(code, ktype)

            if not data:
                return None

            df = self.kline_to_dataframe(data)
            if df is None or df.empty:
                return None

            # 按日期过滤
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)

            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df = df[(df['date'] >= start_dt) & (df['date'] <= end_dt)]

            return df.reset_index(drop=True)

        except Exception as e:
            logger.error(f"TDX获取K线数据异常: {e}")
            return None

    def get_stock_data_formatted(self, code: str, start_date: str, end_date: str) -> str:
        """
        获取格式化的股票数据（用于分析）

        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            str: 格式化的股票数据报告
        """
        df = self.get_kline_by_date_range(code, start_date, end_date, 'day')

        if df is None or df.empty:
            return f"❌ 无法从TDX获取{code}的K线数据"

        # 格式化输出
        result = f"## {code} 股票数据 (来源: TDX)\n"
        result += f"时间范围: {start_date} 至 {end_date}\n"
        result += f"数据条数: {len(df)}\n\n"

        # 添加表格数据
        result += "| 日期 | 开盘 | 最高 | 最低 | 收盘 | 成交量 | 成交额 |\n"
        result += "|------|------|------|------|------|--------|--------|\n"

        for _, row in df.tail(30).iterrows():  # 只显示最近30条
            date_str = row['date'].strftime('%Y-%m-%d') if hasattr(row['date'], 'strftime') else str(row['date'])[:10]
            result += f"| {date_str} | {row.get('open', 0):.2f} | {row.get('high', 0):.2f} | "
            result += f"{row.get('low', 0):.2f} | {row.get('close', 0):.2f} | "
            result += f"{row.get('volume', 0):,.0f} | {row.get('amount', 0):,.0f} |\n"

        return result

    def is_trading_day(self, date: str = None) -> bool:
        """
        判断是否为交易日

        Args:
            date: 日期，默认今天

        Returns:
            bool: 是否为交易日
        """
        data = self.get_workday(date)
        if data:
            return data.get('is_workday', False)
        return False

    def get_next_trading_day(self, date: str = None) -> Optional[str]:
        """
        获取下一个交易日

        Args:
            date: 基准日期，默认今天

        Returns:
            str: 下一个交易日 (YYYY-MM-DD)
        """
        data = self.get_workday(date, count=1)
        if data and 'next' in data:
            next_days = data.get('next', [])
            if next_days:
                return next_days[0]
        return None

    def get_prev_trading_day(self, date: str = None) -> Optional[str]:
        """
        获取上一个交易日

        Args:
            date: 基准日期，默认今天

        Returns:
            str: 上一个交易日 (YYYY-MM-DD)
        """
        data = self.get_workday(date, count=1)
        if data and 'previous' in data:
            prev_days = data.get('previous', [])
            if prev_days:
                return prev_days[0]
        return None


# 全局单例
_tdx_provider = None


def get_tdx_provider() -> TDXProvider:
    """获取TDX Provider单例"""
    global _tdx_provider
    if _tdx_provider is None:
        _tdx_provider = TDXProvider()
    return _tdx_provider


def is_tdx_available() -> bool:
    """检查TDX服务是否可用"""
    try:
        provider = get_tdx_provider()
        return provider.is_available()
    except Exception:
        return False


if __name__ == '__main__':
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    provider = get_tdx_provider()

    if provider.is_available():
        print("✅ TDX服务可用")

        # 测试获取行情
        quotes = provider.get_realtime_quote(['000001', '600519'])
        print(f"行情数据: {quotes}")

        # 测试获取K线
        kline = provider.get_kline('000001', 'day', 30)
        if kline is not None:
            print(f"K线数据: {len(kline)}条")
            print(kline.tail())

        # 测试技术指标
        indicators = provider.calculate_technical_indicators('000001')
        if indicators:
            print(f"技术指标: {indicators}")

        # 测试ETF列表
        etf_list = provider.get_etf_list()
        if etf_list:
            print(f"ETF数量: {etf_list.get('total', 0)}")

        # 测试交易日查询
        workday = provider.get_workday()
        if workday:
            print(f"交易日信息: {workday}")

        # 测试指数数据
        index_data = provider.get_index('sh000001', 'day')
        if index_data:
            print(f"上证指数数据条数: {index_data.get('Count', 0)}")
    else:
        print("⚠️ TDX服务不可用")
