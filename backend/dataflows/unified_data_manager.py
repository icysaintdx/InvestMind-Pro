#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一数据源管理器 - 支持多数据源自动降级

数据源优先级（从高到低）：
1. TDX (通达信) - 本地化部署，速度最快
2. AKShare - 免费开源，数据全面
3. Tushare - 需要积分，数据质量高
4. 聚合数据 - 付费API，作为最后备选

不同数据类型的数据源支持：
- 实时行情: TDX > AKShare > Tushare
- K线数据: TDX > AKShare > Tushare
- 分时数据: TDX > AKShare
- 新闻数据: AKShare > Tushare (TDX不支持)
- 财务数据: AKShare > Tushare > 聚合数据
- 股票列表: TDX > AKShare > Tushare
"""

import os
import logging
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime, timedelta
import pandas as pd

logger = logging.getLogger(__name__)


class DataSourcePriority:
    REALTIME_QUOTE = ['tdx', 'akshare', 'tushare']
    KLINE = ['tdx', 'akshare', 'tushare']
    MINUTE = ['tdx', 'akshare']
    NEWS = ['akshare', 'tushare']
    FINANCIAL = ['akshare', 'tushare', 'juhe']
    STOCK_LIST = ['tdx', 'akshare', 'tushare']
    INDEX = ['tdx', 'akshare', 'tushare']
    ETF = ['tdx', 'akshare']
    WORKDAY = ['tdx', 'akshare']


class UnifiedDataManager:
    def __init__(self):
        self._providers = {}
        self._status = {}
        self._init_providers()

    def _init_providers(self):
        # TDX - 优先使用 Native Provider（纯Python，无需Docker）
        try:
            from backend.dataflows.providers.tdx_native_provider import get_tdx_native_provider
            native_provider = get_tdx_native_provider()
            if native_provider.is_available():
                self._providers['tdx'] = native_provider
                self._providers['tdx_type'] = 'native'
                self._status['tdx'] = True
                logger.info("TDX Native Provider initialized successfully")
            else:
                raise Exception("Native Provider not available")
        except Exception as e:
            logger.debug(f"TDX Native init failed: {e}, trying HTTP Provider")
            # 降级到 HTTP Provider
            try:
                from backend.dataflows.providers.tdx_provider_full import get_tdx_provider_full
                self._providers['tdx'] = get_tdx_provider_full()
                self._providers['tdx_type'] = 'http'
                self._status['tdx'] = self._providers['tdx'].is_available()
                if self._status['tdx']:
                    logger.info("TDX HTTP Provider initialized successfully")
            except Exception as e2:
                logger.warning(f"TDX HTTP init failed: {e2}")
                self._status['tdx'] = False

        # AKShare
        try:
            import akshare as ak
            self._providers['akshare'] = ak
            self._status['akshare'] = True
        except Exception as e:
            logger.warning(f"AKShare init failed: {e}")
            self._status['akshare'] = False

        # Tushare
        try:
            import tushare as ts
            token = os.getenv('TUSHARE_TOKEN', '')
            if token:
                ts.set_token(token)
                self._providers['tushare'] = ts.pro_api()
                self._status['tushare'] = True
            else:
                self._status['tushare'] = False
        except Exception as e:
            logger.warning(f"Tushare init failed: {e}")
            self._status['tushare'] = False

        # 聚合数据
        juhe_key = os.getenv('JUHE_API_KEY', '')
        self._status['juhe'] = bool(juhe_key)
        if juhe_key:
            self._providers['juhe'] = {'api_key': juhe_key}

    def get_status(self) -> Dict[str, bool]:
        return self._status.copy()

    def is_available(self, name: str) -> bool:
        return self._status.get(name, False)

    def _fallback(self, priority: List[str], methods: Dict[str, Callable], 
                  data_type: str, **kwargs) -> Optional[Any]:
        errors = []
        for name in priority:
            if not self.is_available(name) or name not in methods:
                continue
            try:
                logger.info(f"Trying {name} for {data_type}")
                result = methods[name](**kwargs)
                if result is not None:
                    if isinstance(result, pd.DataFrame) and result.empty:
                        continue
                    logger.info(f"Got {data_type} from {name}")
                    return result
            except Exception as e:
                errors.append(f"{name}: {e}")
        logger.error(f"All sources failed for {data_type}: {errors}")
        return None

    # ===== 实时行情 =====
    def get_realtime_quote(self, codes: Union[str, List[str]]) -> Optional[List[Dict]]:
        if isinstance(codes, str): codes = [codes]
        methods = {
            'tdx': lambda: self._quote_tdx(codes),
            'akshare': lambda: self._quote_akshare(codes),
            'tushare': lambda: self._quote_tushare(codes),
        }
        return self._fallback(DataSourcePriority.REALTIME_QUOTE, methods, '实时行情')

    def _quote_tdx(self, codes):
        provider = self._providers.get('tdx')
        provider_type = self._providers.get('tdx_type', 'http')

        if provider_type == 'native':
            # Native Provider 使用 get_realtime_quotes
            return provider.get_realtime_quotes(codes)
        else:
            # HTTP Provider 使用 get_quote
            return provider.get_quote(codes)

    def _quote_akshare(self, codes):
        ak = self._providers['akshare']
        df = ak.stock_zh_a_spot_em()
        result = []
        for code in codes:
            clean = code.replace('sh', '').replace('sz', '')
            row = df[df['代码'] == clean]
            if not row.empty:
                r = row.iloc[0]
                result.append({
                    'code': clean, 'name': r.get('名称', ''),
                    'price': float(r.get('最新价', 0) or 0),
                    'open': float(r.get('今开', 0) or 0),
                    'high': float(r.get('最高', 0) or 0),
                    'low': float(r.get('最低', 0) or 0),
                    'pre_close': float(r.get('昨收', 0) or 0),
                    'volume': int(r.get('成交量', 0) or 0),
                    'amount': float(r.get('成交额', 0) or 0),
                    'change_pct': float(r.get('涨跌幅', 0) or 0),
                    'source': 'akshare'
                })
        return result if result else None

    def _quote_tushare(self, codes):
        pro = self._providers['tushare']
        result = []
        for code in codes:
            clean = code.replace('sh', '').replace('sz', '')
            ts_code = f"{clean}.SH" if clean.startswith('6') else f"{clean}.SZ"
            df = pro.daily(ts_code=ts_code, limit=1)
            if df is not None and not df.empty:
                r = df.iloc[0]
                result.append({
                    'code': clean, 'price': float(r.get('close', 0)),
                    'open': float(r.get('open', 0)), 'high': float(r.get('high', 0)),
                    'low': float(r.get('low', 0)), 'pre_close': float(r.get('pre_close', 0)),
                    'volume': int(r.get('vol', 0)), 'amount': float(r.get('amount', 0)) * 1000,
                    'change_pct': float(r.get('pct_chg', 0)), 'source': 'tushare'
                })
        return result if result else None

    # ===== K线数据 =====
    def get_kline(self, code: str, period: str = 'day', limit: int = 200, adjust: str = 'qfq') -> Optional[pd.DataFrame]:
        methods = {
            'tdx': lambda: self._kline_tdx(code, period, limit),
            'akshare': lambda: self._kline_akshare(code, period, adjust, limit),
            'tushare': lambda: self._kline_tushare(code, period, adjust, limit),
        }
        return self._fallback(DataSourcePriority.KLINE, methods, f'K线({period})')

    def _kline_tdx(self, code, period, limit):
        provider = self._providers.get('tdx')
        provider_type = self._providers.get('tdx_type', 'http')

        if provider_type == 'native':
            # Native Provider 使用 get_kline，需要转换 period 到 kline_type
            kline_type_map = {
                '1m': 8, '5m': 0, '15m': 1, '30m': 2, '60m': 3,
                '1': 8, '5': 0, '15': 1, '30': 2, '60': 3,
                'day': 9, 'daily': 9, 'week': 5, 'weekly': 5, 'month': 6, 'monthly': 6
            }
            ktype = kline_type_map.get(period, 9)
            kline_data = provider.get_kline(code, ktype, limit)
            if kline_data:
                import pandas as pd
                df = pd.DataFrame(kline_data)
                df['source'] = 'tdx_native'
                return df
            return None
        else:
            # HTTP Provider 使用 get_kline
            return provider.get_kline(code, period, limit)

    def _kline_akshare(self, code, period, adjust, limit):
        ak = self._providers['akshare']
        clean = code.replace('sh', '').replace('sz', '')
        period_map = {'1': '1', '5': '5', '15': '15', '30': '30', '60': '60',
                      '1m': '1', '5m': '5', '15m': '15', '30m': '30', '60m': '60',
                      'day': 'daily', 'daily': 'daily', 'week': 'weekly', 'month': 'monthly'}
        ak_period = period_map.get(period, 'daily')
        if ak_period in ['1', '5', '15', '30', '60']:
            df = ak.stock_zh_a_hist_min_em(symbol=clean, period=ak_period, adjust=adjust)
        else:
            df = ak.stock_zh_a_hist(symbol=clean, period=ak_period,
                start_date=(datetime.now() - timedelta(days=730)).strftime('%Y%m%d'),
                end_date=datetime.now().strftime('%Y%m%d'), adjust=adjust)
        if df is None or df.empty: return None
        col_map = {'日期': 'time', '时间': 'time', '开盘': 'open', '收盘': 'close',
                   '最高': 'high', '最低': 'low', '成交量': 'volume', '成交额': 'amount'}
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
        df['source'] = 'akshare'
        return df.tail(limit) if len(df) > limit else df

    def _kline_tushare(self, code, period, adjust, limit):
        if period in ['1', '5', '15', '30', '60', '1m', '5m', '15m', '30m', '60m']:
            return None
        pro = self._providers['tushare']
        clean = code.replace('sh', '').replace('sz', '')
        ts_code = f"{clean}.SH" if clean.startswith('6') else f"{clean}.SZ"
        df = pro.daily(ts_code=ts_code, limit=limit)
        if df is None or df.empty: return None
        df = df.rename(columns={'trade_date': 'time', 'vol': 'volume'})
        df['source'] = 'tushare'
        return df

    # ===== 分时数据 =====
    def get_minute_data(self, code: str, date: str = None) -> Optional[pd.DataFrame]:
        methods = {
            'tdx': lambda: self._minute_tdx(code, date),
            'akshare': lambda: self._minute_akshare(code),
        }
        return self._fallback(DataSourcePriority.MINUTE, methods, '分时数据')

    def _minute_tdx(self, code, date):
        provider = self._providers.get('tdx')
        provider_type = self._providers.get('tdx_type', 'http')

        if provider_type == 'native':
            # Native Provider 使用 get_minute_data 或 get_history_minute_data
            if date:
                minute_data = provider.get_history_minute_data(code, date)
            else:
                minute_data = provider.get_minute_data(code)
            if minute_data:
                import pandas as pd
                df = pd.DataFrame(minute_data)
                df['source'] = 'tdx_native'
                return df
            return None
        else:
            # HTTP Provider 使用 get_minute
            return provider.get_minute(code, date)

    def _minute_akshare(self, code):
        ak = self._providers['akshare']
        clean = code.replace('sh', '').replace('sz', '')
        df = ak.stock_zh_a_hist_min_em(symbol=clean, period='1', adjust='qfq')
        if df is not None and not df.empty:
            df['source'] = 'akshare'
        return df

    # ===== 股票列表 =====
    def get_stock_list(self, exchange: str = 'all') -> Optional[List[Dict]]:
        methods = {
            'tdx': lambda: self._stock_list_tdx(exchange),
            'akshare': lambda: self._stock_list_akshare(),
            'tushare': lambda: self._stock_list_tushare(),
        }
        return self._fallback(DataSourcePriority.STOCK_LIST, methods, '股票列表')

    def _stock_list_tdx(self, exchange):
        provider = self._providers.get('tdx')
        provider_type = self._providers.get('tdx_type', 'http')

        if provider_type == 'native':
            # Native Provider 使用 get_all_stock_codes 或 get_stock_list
            all_stocks = provider.get_all_stock_codes()
            if all_stocks:
                result = []
                for s in all_stocks:
                    market = s.get('market', '')
                    # 根据 exchange 过滤
                    if exchange == 'all' or \
                       (exchange == 'sh' and market == '上海') or \
                       (exchange == 'sz' and market == '深圳'):
                        result.append({
                            'code': s.get('code', ''),
                            'name': s.get('name', ''),
                            'exchange': market,
                            'source': 'tdx_native'
                        })
                return result if result else None
            return None
        else:
            # HTTP Provider 使用 get_codes
            data = provider.get_codes(exchange)
            if data and data.get('codes'):
                return [{'code': c['code'], 'name': c['name'], 'exchange': c.get('exchange', ''), 'source': 'tdx_http'} for c in data['codes']]
            return None

    def _stock_list_akshare(self):
        ak = self._providers['akshare']
        df = ak.stock_zh_a_spot_em()
        return [{'code': r['代码'], 'name': r['名称'], 'source': 'akshare'} for _, r in df.iterrows()]

    def _stock_list_tushare(self):
        pro = self._providers['tushare']
        df = pro.stock_basic(exchange='', list_status='L')
        return [{'code': r['ts_code'].split('.')[0], 'name': r['name'], 'source': 'tushare'} for _, r in df.iterrows()]

    # ===== 指数数据 =====
    def get_index_kline(self, code: str, period: str = 'day', limit: int = 200) -> Optional[pd.DataFrame]:
        methods = {
            'tdx': lambda: self._index_tdx(code, period, limit),
            'akshare': lambda: self._index_akshare(code, limit),
        }
        return self._fallback(DataSourcePriority.INDEX, methods, f'指数K线({period})')

    def _index_tdx(self, code, period, limit):
        provider = self._providers.get('tdx')
        provider_type = self._providers.get('tdx_type', 'http')

        if provider_type == 'native':
            # Native Provider 使用 get_index_bars
            kline_type_map = {
                '1m': 8, '5m': 0, '15m': 1, '30m': 2, '60m': 3,
                'day': 9, 'daily': 9, 'week': 5, 'weekly': 5, 'month': 6, 'monthly': 6
            }
            ktype = kline_type_map.get(period, 9)
            index_data = provider.get_index_bars(code, ktype, limit)
            if index_data:
                import pandas as pd
                df = pd.DataFrame(index_data)
                df['source'] = 'tdx_native'
                return df
            return None
        else:
            # HTTP Provider 使用 get_index
            return provider.get_index(code, period)

    def _index_akshare(self, code, limit):
        ak = self._providers['akshare']
        symbol = code[2:] if code.startswith(('sh', 'sz')) else code
        try:
            df = ak.stock_zh_index_daily(symbol=f"sh{symbol}")
        except:
            df = ak.stock_zh_index_daily(symbol=f"sz{symbol}")
        if df is not None and not df.empty:
            df = df.tail(limit)
            df['source'] = 'akshare'
        return df

    # ===== ETF数据 =====
    def get_etf_list(self, exchange: str = 'all', limit: int = None) -> Optional[List[Dict]]:
        methods = {
            'tdx': lambda: self._etf_tdx(exchange, limit),
            'akshare': lambda: self._etf_akshare(limit),
        }
        return self._fallback(DataSourcePriority.ETF, methods, 'ETF列表')

    def _etf_tdx(self, exchange, limit):
        provider = self._providers.get('tdx')
        provider_type = self._providers.get('tdx_type', 'http')

        if provider_type == 'native':
            # Native Provider 暂不支持 ETF 列表，返回 None 让其降级到 AKShare
            return None
        else:
            # HTTP Provider 使用 get_etf_list
            data = provider.get_etf_list(exchange, limit)
            if data and data.get('list'):
                return [{'code': e['code'], 'name': e['name'], 'price': e.get('last_price', 0), 'source': 'tdx_http'} for e in data['list']]
            return None

    def _etf_akshare(self, limit):
        ak = self._providers['akshare']
        df = ak.fund_etf_spot_em()
        result = [{'code': r['代码'], 'name': r['名称'], 'price': float(r.get('最新价', 0) or 0), 'source': 'akshare'} for _, r in df.iterrows()]
        return result[:limit] if limit else result

    # ===== 交易日 =====
    def get_workday(self, date: str = None, count: int = 1) -> Optional[Dict]:
        methods = {
            'tdx': lambda: self._workday_tdx(date, count),
            'akshare': lambda: self._workday_akshare(date),
        }
        return self._fallback(DataSourcePriority.WORKDAY, methods, '交易日信息')

    def _workday_tdx(self, date, count):
        provider = self._providers.get('tdx')
        provider_type = self._providers.get('tdx_type', 'http')

        if provider_type == 'native':
            # Native Provider 使用 is_trading_day
            check_date = date or datetime.now().strftime('%Y%m%d')
            # 转换日期格式
            if '-' in check_date:
                check_date = check_date.replace('-', '')
            is_workday = provider.is_trading_day(check_date)
            return {'date': date or datetime.now().strftime('%Y-%m-%d'), 'is_workday': is_workday, 'source': 'tdx_native'}
        else:
            # HTTP Provider 使用 get_workday
            return provider.get_workday(date, count)

    def _workday_akshare(self, date):
        ak = self._providers['akshare']
        df = ak.tool_trade_date_hist_sina()
        if df is None or df.empty: return None
        trade_dates = df['trade_date'].astype(str).tolist()
        check = date or datetime.now().strftime('%Y-%m-%d')
        check_fmt = check.replace('-', '')
        is_workday = check_fmt in [d.replace('-', '') for d in trade_dates]
        return {'date': check, 'is_workday': is_workday, 'source': 'akshare'}

    # ===== 搜索股票 =====
    def search_stock(self, keyword: str, limit: int = 20) -> List[Dict]:
        if self.is_available('tdx'):
            provider = self._providers.get('tdx')
            provider_type = self._providers.get('tdx_type', 'http')

            if provider_type == 'native':
                # Native Provider 使用 search_stock
                results = provider.search_stock(keyword, limit=limit)
                if results:
                    return [{'code': r.get('code', ''), 'name': r.get('name', ''),
                             'market': r.get('market', ''), 'source': 'tdx_native'} for r in results]
            else:
                # HTTP Provider 使用 search
                results = provider.search(keyword)
                if results:
                    return results[:limit]

        if self.is_available('akshare'):
            stocks = self._stock_list_akshare()
            if stocks:
                matched = [s for s in stocks if keyword in s['code'] or keyword in s['name']]
                return matched[:limit]
        return []


# 单例
_unified_manager = None

def get_unified_data_manager() -> UnifiedDataManager:
    global _unified_manager
    if _unified_manager is None:
        _unified_manager = UnifiedDataManager()
    return _unified_manager
