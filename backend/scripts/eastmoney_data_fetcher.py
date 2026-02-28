#!/usr/bin/env python3
"""
东方财富数据获取模块 - 使用直接HTTP请求
"""
import requests
import pandas as pd
import json
import time
import random
from datetime import datetime, timedelta

# 禁用代理
import os
for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    if key in os.environ:
        del os.environ[key]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Connection': 'keep-alive',
    'Referer': 'https://quote.eastmoney.com/',
}

def get_stock_data_eastmoney(symbol: str, start_date: str = "20200101", end_date: str = None) -> pd.DataFrame:
    """从东方财富获取股票历史数据"""
    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")
    
    # 确定市场前缀
    if symbol.startswith('6'):
        secid = f"1.{symbol}"  # 上海
    else:
        secid = f"0.{symbol}"  # 深圳
    
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    params = {
        'fields1': 'f1,f2,f3,f4,f5,f6',
        'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f116',
        'ut': '7eea3edcaed734bea9cbfc24409ed989',
        'klt': '101',  # 日线
        'fqt': '1',    # 前复权
        'secid': secid,
        'beg': start_date,
        'end': end_date,
    }
    
    max_retries = 5
    for attempt in range(max_retries):
        try:
            time.sleep(random.uniform(0.3, 1.0))  # 请求间隔
            
            session = requests.Session()
            session.trust_env = False  # 禁用环境代理
            
            response = session.get(url, params=params, headers=HEADERS, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'data' not in data or data['data'] is None or 'klines' not in data['data']:
                raise ValueError(f"无效响应: {data}")
            
            klines = data['data']['klines']
            
            # 解析数据
            rows = []
            for line in klines:
                parts = line.split(',')
                rows.append({
                    'date': parts[0],
                    'open': float(parts[1]),
                    'close': float(parts[2]),
                    'high': float(parts[3]),
                    'low': float(parts[4]),
                    'volume': float(parts[5]),
                    'amount': float(parts[6]),
                    'amplitude': float(parts[7]),
                    'pct_change': float(parts[8]),
                    'change': float(parts[9]),
                    'turnover': float(parts[10]) if parts[10] else 0,
                })
            
            df = pd.DataFrame(rows)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            return df
            
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"  ⚠️ 请求失败，{wait_time:.1f}s后重试... ({attempt+1}/{max_retries})")
                time.sleep(wait_time)
            else:
                raise e
    
    raise Exception("所有重试失败")

def get_index_data_eastmoney(symbol: str = "000300", start_date: str = "20200101", end_date: str = None) -> pd.DataFrame:
    """从东方财富获取指数历史数据"""
    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")
    
    secid = f"1.{symbol}"  # 沪深300是上海指数
    
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    params = {
        'fields1': 'f1,f2,f3,f4,f5,f6',
        'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f116',
        'ut': '7eea3edcaed734bea9cbfc24409ed989',
        'klt': '101',
        'fqt': '0',  # 指数不复权
        'secid': secid,
        'beg': start_date,
        'end': end_date,
    }
    
    max_retries = 5
    for attempt in range(max_retries):
        try:
            time.sleep(random.uniform(0.3, 1.0))
            
            session = requests.Session()
            session.trust_env = False
            
            response = session.get(url, params=params, headers=HEADERS, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'data' not in data or data['data'] is None or 'klines' not in data['data']:
                raise ValueError(f"无效响应: {data}")
            
            klines = data['data']['klines']
            
            rows = []
            for line in klines:
                parts = line.split(',')
                rows.append({
                    'date': parts[0],
                    'open': float(parts[1]),
                    'close': float(parts[2]),
                    'high': float(parts[3]),
                    'low': float(parts[4]),
                    'volume': float(parts[5]),
                    'amount': float(parts[6]),
                    'amplitude': float(parts[7]),
                    'pct_change': float(parts[8]),
                    'change': float(parts[9]),
                    'turnover': float(parts[10]) if parts[10] else 0,
                })
            
            df = pd.DataFrame(rows)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            return df
            
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"  ⚠️ 指数请求失败，{wait_time:.1f}s后重试... ({attempt+1}/{max_retries})")
                time.sleep(wait_time)
            else:
                raise e
    
    raise Exception("所有重试失败")

if __name__ == "__main__":
    print("测试获取股票000002数据...")
    try:
        df = get_stock_data_eastmoney('000002', start_date='20240101')
        print(f"✅ 成功获取数据: {len(df)} 条记录")
        print(df.head(3))
    except Exception as e:
        print(f"❌ 失败: {e}")
    
    print("\n测试获取沪深300数据...")
    try:
        df = get_index_data_eastmoney('000300', start_date='20240101')
        print(f"✅ 成功获取数据: {len(df)} 条记录")
        print(df.head(3))
    except Exception as e:
        print(f"❌ 失败: {e}")
