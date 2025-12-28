"""
市场数据服务
支持多数据源：TDX > AKShare，自动降级
"""

import pandas as pd
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from functools import lru_cache
import asyncio

from backend.utils.logging_config import get_logger

logger = get_logger("services.market_data")


class MarketDataService:
    """市场数据服务（支持TDX优先）"""

    def __init__(self):
        self._cache = {}
        self._cache_time = {}
        self._cache_ttl = 60  # 缓存60秒
        self._tdx_provider = None
        self._tdx_checked = False

    def _get_tdx_provider(self):
        """获取TDX Provider（懒加载）- 优先使用Native Provider"""
        if self._tdx_provider is None and not self._tdx_checked:
            # 1. 优先使用 TDX Native Provider（纯Python，无需外部服务）
            try:
                from backend.dataflows.providers.tdx_native_provider import get_tdx_native_provider
                native_provider = get_tdx_native_provider()
                if native_provider.is_available():
                    self._tdx_provider = native_provider
                    logger.info("✅ MarketDataService: TDX Native Provider可用（纯Python）")
                    self._tdx_checked = True
                    return self._tdx_provider
            except Exception as e:
                logger.debug(f"TDX Native Provider初始化失败: {e}")

            # 2. 降级到旧的 HTTP API Provider（需要Docker服务）
            try:
                from backend.dataflows.providers.tdx_provider import get_tdx_provider
                self._tdx_provider = get_tdx_provider()
                if self._tdx_provider.is_available():
                    logger.info("✅ MarketDataService: TDX HTTP服务可用")
                else:
                    logger.warning("⚠️ MarketDataService: TDX服务不可用，将使用AKShare")
                    self._tdx_provider = None
            except Exception as e:
                logger.warning(f"⚠️ MarketDataService: TDX初始化失败: {e}")
                self._tdx_provider = None
            self._tdx_checked = True
        return self._tdx_provider

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
        获取实时行情（优先级：TDX Native > TDX HTTP > AKShare）

        Args:
            stock_code: 股票代码（如600519、000001）

        Returns:
            实时行情数据
        """
        cache_key = f"quote_{stock_code}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        # 标准化股票代码
        code = stock_code.replace(".SH", "").replace(".SZ", "")

        # 1. 优先使用TDX获取实时行情
        tdx = self._get_tdx_provider()
        if tdx:
            try:
                # 检查是否是 Native Provider（有 get_realtime_quote 方法）
                if hasattr(tdx, 'get_realtime_quote'):
                    quote_data = tdx.get_realtime_quote(code)
                    if quote_data:
                        result = {
                            "stock_code": code,
                            "stock_name": quote_data.get('name', code),
                            "current_price": float(quote_data.get('price', 0)),
                            "open_price": float(quote_data.get('open', 0)),
                            "high_price": float(quote_data.get('high', 0)),
                            "low_price": float(quote_data.get('low', 0)),
                            "pre_close": float(quote_data.get('pre_close', 0)),
                            "change": float(quote_data.get('change', 0)),
                            "change_rate": round(float(quote_data.get('change_pct', 0)), 2),
                            "volume": int(quote_data.get('volume', 0)),
                            "amount": float(quote_data.get('amount', 0)),
                            "turnover_rate": 0,
                            "pe_ratio": 0,
                            "pb_ratio": 0,
                            "total_market_cap": 0,
                            "timestamp": datetime.now().isoformat(),
                            "source": "tdx_native"
                        }
                        self._set_cache(cache_key, result)
                        logger.info(f"✅ TDX Native获取实时行情成功: {stock_code} @ {result['current_price']}")
                        return result

                # 旧的 HTTP API Provider（get_quote 方法）
                elif hasattr(tdx, 'get_quote') and tdx.is_available():
                    quote_data = tdx.get_quote(code)
                    if quote_data and isinstance(quote_data, list) and len(quote_data) > 0:
                        q = quote_data[0]
                        k_data = q.get('K', {})

                        # 计算涨跌
                        current = k_data.get('Close', 0) / 1000
                        pre_close = k_data.get('Last', 0) / 1000
                        change = current - pre_close if pre_close > 0 else 0
                        change_rate = (change / pre_close * 100) if pre_close > 0 else 0

                        result = {
                            "stock_code": code,
                            "stock_name": self._get_stock_name_from_tdx(code),
                            "current_price": current,
                            "open_price": k_data.get('Open', 0) / 1000,
                            "high_price": k_data.get('High', 0) / 1000,
                            "low_price": k_data.get('Low', 0) / 1000,
                            "pre_close": pre_close,
                            "change": change,
                            "change_rate": round(change_rate, 2),
                            "volume": q.get('TotalHand', 0) * 100,
                            "amount": q.get('Amount', 0) / 1000,
                            "turnover_rate": 0,
                            "pe_ratio": 0,
                            "pb_ratio": 0,
                            "total_market_cap": 0,
                            "timestamp": datetime.now().isoformat(),
                            "source": "tdx"
                        }

                        self._set_cache(cache_key, result)
                        logger.info(f"✅ TDX获取实时行情成功: {stock_code} @ {result['current_price']}")
                        return result
            except Exception as e:
                logger.warning(f"⚠️ TDX获取行情失败: {stock_code}, {e}，降级到AKShare")

        # 2. 降级到快速数据源（按速度排序：新浪 > Tushare > 腾讯 > AKShare）
        return self._get_quote_fast_fallback(code)

    def _get_stock_name_from_tdx(self, code: str) -> str:
        """从TDX获取股票名称"""
        try:
            tdx = self._get_tdx_provider()
            if tdx:
                results = tdx.search_stock(code, limit=1)
                if results:
                    return results[0].get('name', code)
        except:
            pass
        return code

    def _get_quote_fast_fallback(self, code: str) -> Dict[str, Any]:
        """
        快速降级获取实时行情
        优先级：新浪(0.37s) > Tushare(0.24s) > 腾讯(1.1s) > AKShare(98s)
        """
        # 1. 新浪财经（最快的HTTP接口）
        result = self._get_quote_from_sina(code)
        if result and result.get('current_price', 0) > 0:
            return result

        # 2. Tushare（免费接口）
        result = self._get_quote_from_tushare(code)
        if result and result.get('current_price', 0) > 0:
            return result

        # 3. 腾讯财经
        result = self._get_quote_from_tencent(code)
        if result and result.get('current_price', 0) > 0:
            return result

        # 4. 最后使用AKShare（最慢）
        return self._get_quote_from_akshare(code)

    def _get_quote_from_sina(self, code: str) -> Dict[str, Any]:
        """从新浪财经获取实时行情（约0.37秒）"""
        try:
            import requests

            # 格式化股票代码
            if code.startswith('6'):
                sina_code = 'sh' + code
            elif code.startswith(('0', '3')):
                sina_code = 'sz' + code
            else:
                sina_code = 'sz' + code

            url = f"https://hq.sinajs.cn/list={sina_code}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://finance.sina.com.cn'
            }

            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200 and f'hq_str_{sina_code}' in resp.text:
                data = resp.text.split('=')[1].strip('";')
                parts = data.split(',')
                if len(parts) >= 32:
                    pre_close = float(parts[2]) if parts[2] else 0
                    current_price = float(parts[3]) if parts[3] else 0
                    change = current_price - pre_close if pre_close > 0 else 0
                    change_rate = (change / pre_close * 100) if pre_close > 0 else 0

                    result = {
                        "stock_code": code,
                        "stock_name": parts[0],
                        "current_price": current_price,
                        "open_price": float(parts[1]) if parts[1] else 0,
                        "high_price": float(parts[4]) if parts[4] else 0,
                        "low_price": float(parts[5]) if parts[5] else 0,
                        "pre_close": pre_close,
                        "change": change,
                        "change_rate": round(change_rate, 2),
                        "volume": float(parts[8]) if parts[8] else 0,
                        "amount": float(parts[9]) if parts[9] else 0,
                        "turnover_rate": 0,
                        "pe_ratio": 0,
                        "pb_ratio": 0,
                        "total_market_cap": 0,
                        "timestamp": datetime.now().isoformat(),
                        "source": "sina"
                    }

                    cache_key = f"quote_{code}"
                    self._set_cache(cache_key, result)
                    logger.info(f"获取实时行情成功(新浪): {code} @ {result['current_price']}")
                    return result
        except Exception as e:
            logger.debug(f"新浪财经获取失败: {code}, {e}")
        return None

    def _get_quote_from_tushare(self, code: str) -> Dict[str, Any]:
        """从Tushare获取实时行情（约0.24秒）"""
        try:
            import tushare as ts

            df = ts.get_realtime_quotes(code)
            if df is not None and not df.empty:
                row = df.iloc[0]
                pre_close = float(row.get('pre_close', 0) or 0)
                current_price = float(row.get('price', 0) or 0)
                change = current_price - pre_close if pre_close > 0 else 0
                change_rate = (change / pre_close * 100) if pre_close > 0 else 0

                result = {
                    "stock_code": code,
                    "stock_name": row.get('name', code),
                    "current_price": current_price,
                    "open_price": float(row.get('open', 0) or 0),
                    "high_price": float(row.get('high', 0) or 0),
                    "low_price": float(row.get('low', 0) or 0),
                    "pre_close": pre_close,
                    "change": change,
                    "change_rate": round(change_rate, 2),
                    "volume": float(row.get('volume', 0) or 0),
                    "amount": float(row.get('amount', 0) or 0),
                    "turnover_rate": 0,
                    "pe_ratio": 0,
                    "pb_ratio": 0,
                    "total_market_cap": 0,
                    "timestamp": datetime.now().isoformat(),
                    "source": "tushare"
                }

                cache_key = f"quote_{code}"
                self._set_cache(cache_key, result)
                logger.info(f"获取实时行情成功(Tushare): {code} @ {result['current_price']}")
                return result
        except Exception as e:
            logger.debug(f"Tushare获取失败: {code}, {e}")
        return None

    def _get_quote_from_tencent(self, code: str) -> Dict[str, Any]:
        """从腾讯财经获取实时行情（约1.1秒）"""
        try:
            import requests

            # 格式化股票代码
            if code.startswith('6'):
                qq_code = 'sh' + code
            elif code.startswith(('0', '3')):
                qq_code = 'sz' + code
            else:
                qq_code = 'sz' + code

            url = f"https://qt.gtimg.cn/q={qq_code}"
            resp = requests.get(url, timeout=5)

            if resp.status_code == 200 and f'v_{qq_code}' in resp.text:
                # 腾讯数据格式：v_sz000001="1~平安银行~000001~11.56~..."
                data = resp.text.split('~')
                if len(data) > 35:
                    pre_close = float(data[4]) if data[4] else 0
                    current_price = float(data[3]) if data[3] else 0
                    change = current_price - pre_close if pre_close > 0 else 0
                    change_rate = float(data[32]) if data[32] else 0

                    result = {
                        "stock_code": code,
                        "stock_name": data[1],
                        "current_price": current_price,
                        "open_price": float(data[5]) if data[5] else 0,
                        "high_price": float(data[33]) if data[33] else 0,
                        "low_price": float(data[34]) if data[34] else 0,
                        "pre_close": pre_close,
                        "change": change,
                        "change_rate": change_rate,
                        "volume": float(data[6]) if data[6] else 0,
                        "amount": float(data[37]) if len(data) > 37 and data[37] else 0,
                        "turnover_rate": float(data[38]) if len(data) > 38 and data[38] else 0,
                        "pe_ratio": float(data[39]) if len(data) > 39 and data[39] else 0,
                        "pb_ratio": 0,
                        "total_market_cap": float(data[45]) if len(data) > 45 and data[45] else 0,
                        "timestamp": datetime.now().isoformat(),
                        "source": "tencent"
                    }

                    cache_key = f"quote_{code}"
                    self._set_cache(cache_key, result)
                    logger.info(f"获取实时行情成功(腾讯): {code} @ {result['current_price']}")
                    return result
        except Exception as e:
            logger.debug(f"腾讯财经获取失败: {code}, {e}")
        return None

    def _get_quote_from_akshare(self, code: str) -> Dict[str, Any]:
        """从AKShare获取实时行情"""
        try:
            import akshare as ak

            # 使用AKShare获取实时行情
            df = ak.stock_zh_a_spot_em()

            # 查找股票
            stock_data = df[df['代码'] == code]

            if stock_data.empty:
                # 尝试带前缀的代码
                stock_data = df[df['代码'].str.contains(code)]

            if stock_data.empty:
                logger.warning(f"未找到股票: {code}")
                return self._get_fallback_quote(code)

            row = stock_data.iloc[0]

            result = {
                "stock_code": code,
                "stock_name": row.get('名称', code),
                "current_price": float(row.get('最新价', 0) or 0),
                "open_price": float(row.get('今开', 0) or 0),
                "high_price": float(row.get('最高', 0) or 0),
                "low_price": float(row.get('最低', 0) or 0),
                "pre_close": float(row.get('昨收', 0) or 0),
                "change": float(row.get('涨跌额', 0) or 0),
                "change_rate": float(row.get('涨跌幅', 0) or 0),
                "volume": float(row.get('成交量', 0) or 0),
                "amount": float(row.get('成交额', 0) or 0),
                "turnover_rate": float(row.get('换手率', 0) or 0) if '换手率' in row else 0,
                "pe_ratio": float(row.get('市盈率-动态', 0) or 0) if '市盈率-动态' in row else 0,
                "pb_ratio": float(row.get('市净率', 0) or 0) if '市净率' in row else 0,
                "total_market_cap": float(row.get('总市值', 0) or 0) if '总市值' in row else 0,
                "timestamp": datetime.now().isoformat(),
                "source": "akshare"
            }

            cache_key = f"quote_{code}"
            self._set_cache(cache_key, result)
            logger.info(f"获取实时行情成功: {code} @ {result['current_price']}")
            return result

        except Exception as e:
            logger.error(f"获取实时行情失败: {code}, {e}")
            return self._get_fallback_quote(code)

    def _get_fallback_quote(self, stock_code: str) -> Dict[str, Any]:
        """获取降级行情（使用历史数据）"""
        try:
            import akshare as ak

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
        获取历史行情数据（优先级：TDX Native > TDX HTTP > AKShare）

        Args:
            stock_code: 股票代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            period: 周期 (daily/weekly/monthly)

        Returns:
            历史数据DataFrame
        """
        code = stock_code.replace(".SH", "").replace(".SZ", "")

        # 1. 优先使用TDX获取历史数据
        tdx = self._get_tdx_provider()
        if tdx:
            try:
                # Native Provider 使用 get_kline_by_date 或 get_kline
                if hasattr(tdx, 'get_kline_by_date'):
                    # 周期映射
                    kline_type_map = {
                        'daily': 9,    # 日K
                        'weekly': 5,   # 周K
                        'monthly': 6   # 月K
                    }
                    kline_type = kline_type_map.get(period, 9)

                    kline_data = tdx.get_kline_by_date(code, start_date, end_date, kline_type)
                    if kline_data:
                        df = pd.DataFrame(kline_data)
                        if not df.empty:
                            df['date'] = pd.to_datetime(df['date'])
                            df = df.set_index('date')
                            # 标准化列名
                            df = df.rename(columns={
                                'open': 'open',
                                'high': 'high',
                                'low': 'low',
                                'close': 'close',
                                'volume': 'volume',
                                'amount': 'amount'
                            })
                            logger.info(f"✅ TDX Native获取历史数据成功: {stock_code}, {len(df)}条")
                            return df

                # 旧的 HTTP API Provider
                elif hasattr(tdx, 'get_kline') and tdx.is_available():
                    tdx_period_map = {
                        'daily': 'day',
                        'weekly': 'week',
                        'monthly': 'month'
                    }
                    tdx_period = tdx_period_map.get(period, 'day')

                    from datetime import datetime as dt
                    start_dt = dt.strptime(start_date, '%Y%m%d')
                    end_dt = dt.strptime(end_date, '%Y%m%d')
                    days_diff = (end_dt - start_dt).days
                    limit = max(days_diff + 30, 500)

                    df = tdx.get_kline(code, tdx_period, limit)
                    if df is not None and not df.empty:
                        df['date'] = pd.to_datetime(df['date'])
                        df = df[(df['date'] >= start_dt) & (df['date'] <= end_dt)]
                        df = df.set_index('date')

                        if not df.empty:
                            logger.info(f"✅ TDX获取历史数据成功: {stock_code}, {len(df)}条")
                            return df
            except Exception as e:
                logger.warning(f"⚠️ TDX获取历史数据失败: {stock_code}, {e}，降级到AKShare")

        # 2. 降级到AKShare
        return self._get_historical_from_akshare(code, start_date, end_date, period)

    def _get_historical_from_akshare(self, code: str, start_date: str, end_date: str, period: str) -> pd.DataFrame:
        """从AKShare获取历史数据"""
        try:
            import akshare as ak

            df = ak.stock_zh_a_hist(
                symbol=code,
                period=period,
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )

            if df.empty:
                logger.warning(f"无历史数据: {code}")
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

            logger.info(f"获取历史数据成功: {code}, {len(df)}条")
            return df

        except Exception as e:
            logger.error(f"获取历史数据失败: {code}, {e}")
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
            import akshare as ak

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
        获取市场概览（优先级：TDX Native > TDX HTTP > AKShare）

        Returns:
            市场概览数据
        """
        # 1. 优先使用TDX获取市场概览
        tdx = self._get_tdx_provider()
        if tdx:
            try:
                indices = {}
                index_names = {
                    '000001': '上证指数',
                    '399001': '深证成指',
                    '399006': '创业板指'
                }

                # Native Provider 使用 get_index_bars
                if hasattr(tdx, 'get_index_bars'):
                    for code, name in index_names.items():
                        try:
                            kline = tdx.get_index_bars(code, 9, 1)  # 获取最新1条日K
                            if kline and len(kline) > 0:
                                latest = kline[-1]
                                indices[name] = {
                                    'price': float(latest.get('close', 0)),
                                    'change_rate': 0  # 需要计算
                                }
                        except:
                            pass

                    if indices:
                        logger.info(f"✅ TDX Native获取市场概览成功: {len(indices)}个指数")
                        return {
                            "indices": indices,
                            "timestamp": datetime.now().isoformat(),
                            "source": "tdx_native"
                        }

                # 旧的 HTTP API Provider
                elif hasattr(tdx, 'get_index_quote') and tdx.is_available():
                    index_codes = ['000001', '399001', '399006']
                    quotes = tdx.get_index_quote(index_codes)
                    if quotes and isinstance(quotes, list):
                        for quote in quotes:
                            code = quote.get('code', '')
                            name = index_names.get(code, code)
                            if quote:
                                indices[name] = {
                                    'price': float(quote.get('price', 0)),
                                    'change_rate': float(quote.get('change_pct', 0))
                                }

                    if indices:
                        logger.info(f"✅ TDX获取市场概览成功: {len(indices)}个指数")
                        return {
                            "indices": indices,
                            "timestamp": datetime.now().isoformat(),
                            "source": "tdx"
                        }
            except Exception as e:
                logger.warning(f"⚠️ TDX获取市场概览失败: {e}，降级到AKShare")

        # 2. 降级到AKShare
        return self._get_market_overview_from_akshare()

    def _get_market_overview_from_akshare(self) -> Dict[str, Any]:
        """从AKShare获取市场概览"""
        try:
            import akshare as ak

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


def get_realtime_quotes_batch(stock_codes: List[str]) -> List[Dict[str, Any]]:
    """
    批量获取实时行情（优化性能，一次请求获取多只股票）

    Args:
        stock_codes: 股票代码列表

    Returns:
        行情数据列表
    """
    if not stock_codes:
        return []

    service = get_market_data_service()

    # 标准化股票代码
    codes = [code.replace(".SH", "").replace(".SZ", "") for code in stock_codes]

    # 1. 优先使用TDX批量获取
    tdx = service._get_tdx_provider()
    if tdx:
        try:
            # Native Provider 使用 get_realtime_quotes
            if hasattr(tdx, 'get_realtime_quotes'):
                quotes = tdx.get_realtime_quotes(codes)
                if quotes:
                    result = []
                    for q in quotes:
                        result.append({
                            "code": q.get("code", ""),
                            "stock_code": q.get("code", ""),
                            "stock_name": q.get("name", ""),
                            "price": float(q.get("price", 0) or 0),
                            "current_price": float(q.get("price", 0) or 0),
                            "open_price": float(q.get("open", 0) or 0),
                            "high_price": float(q.get("high", 0) or 0),
                            "low_price": float(q.get("low", 0) or 0),
                            "pre_close": float(q.get("pre_close", 0) or 0),
                            "change": float(q.get("change", 0) or 0),
                            "change_rate": float(q.get("change_pct", 0) or 0),
                            "volume": int(q.get("volume", 0) or 0),
                            "amount": float(q.get("amount", 0) or 0),
                            "source": "tdx_native"
                        })
                    logger.info(f"✅ TDX Native批量获取行情成功: {len(result)}只股票")
                    return result

            # HTTP Provider
            elif hasattr(tdx, 'get_realtime_quote') and tdx.is_available():
                quotes = tdx.get_realtime_quote(codes)
                if quotes:
                    logger.info(f"✅ TDX HTTP批量获取行情成功: {len(quotes)}只股票")
                    return quotes

        except Exception as e:
            logger.warning(f"⚠️ TDX批量获取行情失败: {e}，降级到单个获取")

    # 2. 降级到单个获取
    result = []
    for code in codes:
        try:
            quote = service.get_realtime_quote(code)
            if quote:
                result.append(quote)
        except Exception as e:
            logger.warning(f"获取{code}行情失败: {e}")

    return result


def get_stock_name(stock_code: str) -> str:
    """获取股票名称"""
    return get_market_data_service().get_stock_name(stock_code)


def get_historical_data(stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """获取历史数据"""
    return get_market_data_service().get_historical_data(stock_code, start_date, end_date)
