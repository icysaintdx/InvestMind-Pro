#!/usr/bin/env python3
"""
股票数据获取模块 - 使用新浪财经API
"""
import requests
import pandas as pd
import json
import time
import random
from datetime import datetime
from io import StringIO
import re

# 禁用代理
import os
for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    if key in os.environ:
        del os.environ[key]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': '*/*',
    'Referer': 'https://finance.sina.com.cn',
}

def get_stock_daily_sina(symbol: str, years: int = 5) -> pd.DataFrame:
    """从新浪财经获取股票历史日线数据
    
    使用新浪的日线数据API
    """
    # 转换代码格式
    if symbol.startswith('6'):
        sina_code = f"sh{symbol}"
    else:
        sina_code = f"sz{symbol}"
    
    # 使用腾讯财经数据接口（更稳定）
    url = f"http://web.ifzq.gtimg.cn/appstock/finance/daytrade/daytrade"
    params = {
        'symbol': sina_code,
        '_': int(time.time() * 1000)
    }
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            time.sleep(random.uniform(0.3, 0.8))
            
            session = requests.Session()
            session.trust_env = False
            
            # 尝试腾讯接口
            try:
                url_qq = f"http://web.ifzq.gtimg.cn/appstock/finance/daytrade/daytrade"
                params_qq = {'symbol': sina_code, '_': int(time.time() * 1000)}
                resp = session.get(url_qq, params=params_qq, headers=HEADERS, timeout=10)
                data = resp.json()
                
                if 'data' in data and sina_code in data['data']:
                    day_data = data['data'][sina_code].get('day', [])
                    if day_data:
                        rows = []
                        for item in day_data:
                            if len(item) >= 5:
                                rows.append({
                                    'date': item[0],
                                    'open': float(item[1]),
                                    'close': float(item[2]),
                                    'low': float(item[3]),
                                    'high': float(item[4]),
                                    'volume': float(item[5]) if len(item) > 5 else 0,
                                })
                        
                        df = pd.DataFrame(rows)
                        df['date'] = pd.to_datetime(df['date'])
                        df.set_index('date', inplace=True)
                        df = df.sort_index()
                        
                        # 计算其他字段
                        df['amount'] = df['volume'] * df['close'] * 100
                        df['pct_change'] = df['close'].pct_change() * 100
                        df['change'] = df['close'].diff()
                        df['amplitude'] = ((df['high'] - df['low']) / df['close'].shift(1)) * 100
                        df['turnover'] = 0  # 暂无法获取
                        
                        return df
            except:
                pass
            
            # 备用：使用网易财经
            url_163 = f"http://quotes.money.163.com/service/chddata.html"
            code_163 = f"0{symbol}" if not symbol.startswith('6') else symbol
            params_163 = {
                'code': code_163,
                'start': (datetime.now().replace(year=datetime.now().year - years)).strftime('%Y%m%d'),
                'end': datetime.now().strftime('%Y%m%d'),
                'fields': 'TCLOSE;HIGH;LOW;TOPEN;LCLOSE;CHG;PCHG;VOTURNOVER;VATURNOVER',
            }
            
            resp = session.get(url_163, params=params_163, headers=HEADERS, timeout=15)
            resp.encoding = 'gb2312'
            
            if resp.status_code == 200 and len(resp.text) > 100:
                lines = resp.text.strip().split('\n')
                if len(lines) > 1:
                    rows = []
                    for line in lines[1:]:
                        parts = line.split(',')
                        if len(parts) >= 10:
                            rows.append({
                                'date': parts[0],
                                'code': parts[1],
                                'name': parts[2],
                                'close': float(parts[3]) if parts[3] else 0,
                                'high': float(parts[4]) if parts[4] else 0,
                                'low': float(parts[5]) if parts[5] else 0,
                                'open': float(parts[6]) if parts[6] else 0,
                                'lclose': float(parts[7]) if parts[7] else 0,
                                'change': float(parts[8]) if parts[8] else 0,
                                'pct_change': float(parts[9]) if parts[9] else 0,
                                'volume': float(parts[10]) if len(parts) > 10 and parts[10] else 0,
                                'amount': float(parts[11]) if len(parts) > 11 and parts[11] else 0,
                            })
                    
                    df = pd.DataFrame(rows)
                    df['date'] = pd.to_datetime(df['date'])
                    df.set_index('date', inplace=True)
                    df = df.sort_index()
                    
                    # 重命名列以匹配格式
                    df['amplitude'] = ((df['high'] - df['low']) / df['close'].shift(1)) * 100
                    df['turnover'] = 0
                    
                    return df[['open', 'close', 'high', 'low', 'volume', 'amount', 'amplitude', 'pct_change', 'change', 'turnover']]
                
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = random.uniform(1, 3)
                print(f"  ⚠️ 请求失败，{wait_time:.1f}s后重试... ({attempt+1}/{max_retries})")
                time.sleep(wait_time)
            else:
                raise e
    
    raise Exception("所有数据源都失败")


def get_index_daily_sina(symbol: str = "000300", years: int = 5) -> pd.DataFrame:
    """获取指数历史日线数据"""
    # 沪深300使用sh000300
    if symbol == "000300":
        sina_code = "sh000300"
    elif symbol.startswith("000"):
        sina_code = f"sh{symbol}"
    else:
        sina_code = f"sz{symbol}"
    
    # 使用网易财经
    url = f"http://quotes.money.163.com/service/chddata.html"
    code_163 = f"0{symbol}"  # 指数代码
    params = {
        'code': code_163,
        'start': (datetime.now().replace(year=datetime.now().year - years)).strftime('%Y%m%d'),
        'end': datetime.now().strftime('%Y%m%d'),
        'fields': 'TCLOSE;HIGH;LOW;TOPEN;LCLOSE;CHG;PCHG;VOTURNOVER;VATURNOVER',
    }
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            time.sleep(random.uniform(0.3, 0.8))
            
            session = requests.Session()
            session.trust_env = False
            
            resp = session.get(url, params=params, headers=HEADERS, timeout=15)
            resp.encoding = 'gb2312'
            
            if resp.status_code == 200 and len(resp.text) > 100:
                lines = resp.text.strip().split('\n')
                if len(lines) > 1:
                    rows = []
                    for line in lines[1:]:
                        parts = line.split(',')
                        if len(parts) >= 10:
                            rows.append({
                                'date': parts[0],
                                'close': float(parts[3]) if parts[3] else 0,
                                'high': float(parts[4]) if parts[4] else 0,
                                'low': float(parts[5]) if parts[5] else 0,
                                'open': float(parts[6]) if parts[6] else 0,
                                'pct_change': float(parts[9]) if len(parts) > 9 and parts[9] else 0,
                                'volume': float(parts[10]) if len(parts) > 10 and parts[10] else 0,
                                'amount': float(parts[11]) if len(parts) > 11 and parts[11] else 0,
                            })
                    
                    df = pd.DataFrame(rows)
                    df['date'] = pd.to_datetime(df['date'])
                    df.set_index('date', inplace=True)
                    df = df.sort_index()
                    
                    df['amplitude'] = ((df['high'] - df['low']) / df['close'].shift(1)) * 100
                    df['change'] = df['close'].diff()
                    df['turnover'] = 0
                    
                    return df[['open', 'close', 'high', 'low', 'volume', 'amount', 'amplitude', 'pct_change', 'change', 'turnover']]
                    
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(random.uniform(1, 3))
            else:
                raise e
    
    raise Exception("获取指数数据失败")


if __name__ == "__main__":
    print("测试获取股票000002数据...")
    try:
        df = get_stock_daily_sina('000002')
        print(f"✅ 成功获取数据: {len(df)} 条记录")
        print(df.tail(3))
    except Exception as e:
        print(f"❌ 失败: {e}")
    
    print("\n测试获取沪深300数据...")
    try:
        df = get_index_daily_sina('000300')
        print(f"✅ 成功获取数据: {len(df)} 条记录")
        print(df.tail(3))
    except Exception as e:
        print(f"❌ 失败: {e}")
