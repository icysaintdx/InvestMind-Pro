#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, logging, requests
import pandas as pd
from typing import Dict, List, Optional, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class TDXProviderFull:
    KLINE_TYPES = {
        '1m': 'minute1', '5m': 'minute5', '15m': 'minute15',
        '30m': 'minute30', '60m': 'hour', '1h': 'hour',
        'day': 'day', 'daily': 'day', 'week': 'week', 'weekly': 'week',
        'month': 'month', 'monthly': 'month', 'quarter': 'quarter', 'year': 'year'
    }

    def __init__(self, base_url: str = None):
        self.base_url = (base_url or os.getenv('TDX_API_URL', 'http://127.0.0.1:8080')).rstrip('/')
        self.timeout = 10
        self.long_timeout = 30
        self._available = None

    def reset_availability(self):
        self._available = None

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=3)
            self._available = response.status_code == 200
        except:
            self._available = False
        return self._available

    def _request(self, method, endpoint, params=None, json_data=None, timeout=None):
        if not self.is_available():
            return None
        try:
            url = f"{self.base_url}{endpoint}"
            timeout = timeout or self.timeout
            if method.upper() == 'GET':
                response = requests.get(url, params=params, timeout=timeout)
            else:
                response = requests.post(url, json=json_data, timeout=timeout)
            result = response.json()
            if result.get('code') != 0:
                return None
            return result.get('data')
        except:
            return None

    def _convert_price(self, price_li):
        return price_li / 1000 if price_li else 0.0

    def _parse_kline(self, data_list, updown=False):
        rows = []
        for item in data_list:
            ts = item.get('Time', '')
            ds = ts.split('T')[0] if 'T' in ts else ts
            row = {'time': ds, 'open': self._convert_price(item.get('Open', 0)),
                   'high': self._convert_price(item.get('High', 0)),
                   'low': self._convert_price(item.get('Low', 0)),
                   'close': self._convert_price(item.get('Close', 0)),
                   'volume': item.get('Volume', 0),
                   'amount': self._convert_price(item.get('Amount', 0))}
            if updown:
                row['up_count'] = item.get('UpCount', 0)
                row['down_count'] = item.get('DownCount', 0)
            rows.append(row)
        return rows

    # 1-6 基础接口
    def get_quote(self, codes):
        if isinstance(codes, str): codes = [codes]
        data = self._request('GET', '/api/quote', {'code': ','.join(codes)})
        if not data: return []
        result = []
        for q in data:
            k = q.get('K', {})
            result.append({
                'code': q.get('Code', ''), 'price': self._convert_price(k.get('Close', 0)),
                'open': self._convert_price(k.get('Open', 0)), 'high': self._convert_price(k.get('High', 0)),
                'low': self._convert_price(k.get('Low', 0)), 'pre_close': self._convert_price(k.get('Last', 0)),
                'volume': q.get('TotalHand', 0), 'amount': self._convert_price(q.get('Amount', 0)),
                'buy_levels': [{'price': self._convert_price(b.get('Price', 0)), 'volume': b.get('Number', 0)} for b in q.get('BuyLevel', [])],
                'sell_levels': [{'price': self._convert_price(s.get('Price', 0)), 'volume': s.get('Number', 0)} for s in q.get('SellLevel', [])],
                'source': 'tdx'
            })
        return result

    def get_kline(self, code, kline_type='day', limit=200):
        tdx_type = self.KLINE_TYPES.get(kline_type.lower(), 'day')
        data = self._request('GET', '/api/kline', {'code': code, 'type': tdx_type})
        if not data or not data.get('List'): return None
        df = pd.DataFrame(self._parse_kline(data['List']))
        df['time'] = pd.to_datetime(df['time'])
        df = df.sort_values('time').reset_index(drop=True)
        return df.tail(limit) if len(df) > limit else df

    def get_minute(self, code, date=None):
        params = {'code': code}
        if date: params['date'] = date
        data = self._request('GET', '/api/minute', params)
        if not data or not data.get('List'): return None
        rows = [{'time': i.get('Time', ''), 'price': self._convert_price(i.get('Price', 0)), 'volume': i.get('Number', 0)} for i in data['List']]
        df = pd.DataFrame(rows)
        df['actual_date'] = data.get('date', date or datetime.now().strftime('%Y%m%d'))
        return df

    def get_trade(self, code, date=None):
        params = {'code': code}
        if date: params['date'] = date
        data = self._request('GET', '/api/trade', params)
        if not data or not data.get('List'): return None
        rows = [{'time': i.get('Time', ''), 'price': self._convert_price(i.get('Price', 0)), 'volume': i.get('Volume', 0), 'status': i.get('Status', 0)} for i in data['List']]
        return pd.DataFrame(rows)

    def search(self, keyword):
        data = self._request('GET', '/api/search', {'keyword': keyword})
        return data if data else []

    def get_stock_info(self, code):
        return self._request('GET', '/api/stock-info', {'code': code})

    # 7-13 扩展接口
    def get_codes(self, exchange='all'):
        params = {} if exchange == 'all' else {'exchange': exchange}
        return self._request('GET', '/api/codes', params)

    def batch_quote(self, codes):
        if len(codes) > 50: codes = codes[:50]
        data = self._request('POST', '/api/batch-quote', json_data={'codes': codes})
        return self.get_quote(codes) if data else []

    def get_kline_history(self, code, kline_type='day', start_date=None, end_date=None, limit=100):
        params = {'code': code, 'type': self.KLINE_TYPES.get(kline_type, 'day'), 'limit': min(limit, 800)}
        if start_date: params['start_date'] = start_date
        if end_date: params['end_date'] = end_date
        data = self._request('GET', '/api/kline-history', params)
        if not data or not data.get('List'): return None
        return pd.DataFrame(self._parse_kline(data['List']))

    def get_index(self, code, kline_type='day'):
        params = {'code': code, 'type': self.KLINE_TYPES.get(kline_type, 'day')}
        data = self._request('GET', '/api/index', params)
        if not data or not data.get('List'): return None
        return pd.DataFrame(self._parse_kline(data['List'], updown=True))

    def get_market_stats(self):
        return self._request('GET', '/api/market-stats')

    def get_server_status(self):
        return self._request('GET', '/api/server-status')

    def health_check(self):
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=3)
            return response.status_code == 200
        except: return False

    # 14-18 任务接口
    def create_pull_kline_task(self, codes=None, tables=None, limit=1, start_date=None, directory=None):
        payload = {}
        if codes: payload['codes'] = codes
        if tables: payload['tables'] = tables
        if limit: payload['limit'] = limit
        if start_date: payload['start_date'] = start_date
        if directory: payload['dir'] = directory
        data = self._request('POST', '/api/tasks/pull-kline', json_data=payload)
        return data.get('task_id') if data else None

    def create_pull_trade_task(self, code, start_year=None, end_year=None, directory=None):
        payload = {'code': code}
        if start_year: payload['start_year'] = start_year
        if end_year: payload['end_year'] = end_year
        if directory: payload['dir'] = directory
        data = self._request('POST', '/api/tasks/pull-trade', json_data=payload)
        return data.get('task_id') if data else None

    def list_tasks(self):
        data = self._request('GET', '/api/tasks')
        return data if data else []

    def get_task(self, task_id):
        return self._request('GET', f'/api/tasks/{task_id}')

    def cancel_task(self, task_id):
        data = self._request('POST', f'/api/tasks/{task_id}/cancel')
        return data is not None

    # 19-30 数据服务接口
    def get_etf_list(self, exchange='all', limit=None):
        params = {}
        if exchange != 'all': params['exchange'] = exchange
        if limit: params['limit'] = limit
        return self._request('GET', '/api/etf', params)

    def get_trade_history(self, code, date, start=0, count=2000):
        params = {'code': code, 'date': date, 'start': start, 'count': min(count, 2000)}
        data = self._request('GET', '/api/trade-history', params)
        if not data or not data.get('List'): return None
        rows = [{'time': i.get('Time', ''), 'price': self._convert_price(i.get('Price', 0)), 'volume': i.get('Volume', 0), 'status': i.get('Status', 0)} for i in data['List']]
        return pd.DataFrame(rows)

    def get_minute_trade_all(self, code, date=None):
        params = {'code': code}
        if date: params['date'] = date
        data = self._request('GET', '/api/minute-trade-all', params)
        if not data or not data.get('List'): return None
        rows = [{'time': i.get('Time', ''), 'price': self._convert_price(i.get('Price', 0)), 'volume': i.get('Volume', 0), 'status': i.get('Status', 0)} for i in data['List']]
        return pd.DataFrame(rows)

    def get_workday(self, date=None, count=1):
        params = {'count': min(count, 30)}
        if date: params['date'] = date
        return self._request('GET', '/api/workday', params)

    def get_market_count(self):
        return self._request('GET', '/api/market-count')

    def get_stock_codes(self, limit=None, prefix=True):
        params = {}
        if limit: params['limit'] = limit
        if not prefix: params['prefix'] = 'false'
        return self._request('GET', '/api/stock-codes', params)

    def get_etf_codes(self, limit=None, prefix=True):
        params = {}
        if limit: params['limit'] = limit
        if not prefix: params['prefix'] = 'false'
        return self._request('GET', '/api/etf-codes', params)

    def get_kline_all(self, code, kline_type='day', limit=None):
        params = {'code': code, 'type': self.KLINE_TYPES.get(kline_type, 'day')}
        if limit: params['limit'] = limit
        data = self._request('GET', '/api/kline-all', params, timeout=self.long_timeout)
        if not data or not data.get('list'): return None
        return pd.DataFrame(self._parse_kline(data['list']))

    def get_index_all(self, code, kline_type='day', limit=None):
        params = {'code': code, 'type': self.KLINE_TYPES.get(kline_type, 'day')}
        if limit: params['limit'] = limit
        data = self._request('GET', '/api/index/all', params, timeout=self.long_timeout)
        if not data or not data.get('list'): return None
        return pd.DataFrame(self._parse_kline(data['list'], updown=True))

    def get_trade_history_full(self, code, before=None, limit=None):
        params = {'code': code}
        if before: params['before'] = before
        if limit: params['limit'] = limit
        data = self._request('GET', '/api/trade-history/full', params, timeout=self.long_timeout)
        if not data or not data.get('list'): return None
        rows = [{'time': i.get('Time', ''), 'price': self._convert_price(i.get('Price', 0)), 'volume': i.get('Volume', 0)} for i in data['list']]
        return pd.DataFrame(rows)

    def get_workday_range(self, start, end):
        data = self._request('GET', '/api/workday/range', {'start': start, 'end': end})
        return data.get('list') if data else None

    def get_income(self, code, start_date, days=None):
        params = {'code': code, 'start_date': start_date}
        if days: params['days'] = ','.join(str(d) for d in days)
        return self._request('GET', '/api/income', params)

    # 31-32 全量历史K线接口
    def get_kline_all_tdx(self, code, kline_type='day', limit=None):
        params = {'code': code, 'type': self.KLINE_TYPES.get(kline_type, 'day')}
        if limit: params['limit'] = limit
        data = self._request('GET', '/api/kline-all/tdx', params, timeout=self.long_timeout)
        if not data or not data.get('list'): return None
        df = pd.DataFrame(self._parse_kline(data['list']))
        df['source'] = 'tdx_raw'
        return df

    def get_kline_all_ths(self, code, kline_type='day', limit=None):
        params = {'code': code, 'type': kline_type}
        if limit: params['limit'] = limit
        data = self._request('GET', '/api/kline-all/ths', params, timeout=self.long_timeout)
        if not data or not data.get('list'): return None
        df = pd.DataFrame(self._parse_kline(data['list']))
        df['source'] = 'ths_qfq'
        return df

    # 兼容方法
    def get_realtime_quote(self, codes):
        return self.get_quote(codes)

    def get_minute_data(self, code, date=None):
        return self.get_minute(code, date)

    def search_stock(self, keyword, limit=20):
        results = self.search(keyword)
        return results[:limit] if results else []


# 单例
_tdx_provider_full = None

def get_tdx_provider_full():
    global _tdx_provider_full
    if _tdx_provider_full is None:
        _tdx_provider_full = TDXProviderFull()
    return _tdx_provider_full

def get_tdx_provider():
    return get_tdx_provider_full()
