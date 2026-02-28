#!/usr/bin/env python3
"""
新浪财经数据获取模块
"""
import requests
import pandas as pd
import json
import time
import random
from datetime import datetime
from io import StringIO

# 禁用代理
import os
for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    if key in os.environ:
        del os.environ[key]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

def get_stock_data_sina(symbol: str) -> pd.DataFrame:
    """从新浪财经获取股票历史数据"""
    # 转换代码格式
    if symbol.startswith('6'):
        sina_code = f"sh{symbol}"
    else:
        sina_code = f"sz{symbol}"
    
    url = f"https://quotes.money.163.com/service/chddata.html"
    params = {
        'code': f"0{symbol}" if not symbol.startswith('6') else symbol,
        'start': '20200101',
        'end': datetime.now().strftime('%Y%m%d'),
        'fields': 'TCLOSE;HIGH;LOW;TOPEN;LCLOSE;CHG;PCHG;VOTURNOVER;VATURNOVER',
    }
    
    # 尝试网易财经
    try:
        time.sleep(random.uniform(0.5, 1.5))
        session = requests.Session()
        session.trust_env = False
        
        response = session.get(url, params=params, headers=HEADERS, timeout=30)
        response.encoding = 'gb2312'
        
        if response.status_code == 200 and len(response.text) > 100:
            # 解析CSV数据
            df = pd.read_csv(StringIO(response.text), skiprows=1, 
                           names=['date', 'code', 'name', 'close', 'high', 'low', 'open', 
                                  'lclose', 'change', 'pct_change', 'volume', 'amount'])
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            df = df.sort_index()
            
            # 重命名列以匹配我们的格式
            df = df.rename(columns={
                'open': 'open',
                'close': 'close',
                'high': 'high',
                'low': 'low',
                'volume': 'volume',
                'amount': 'amount',
                'pct_change': 'pct_change'
            })
            
            # 确保数值类型
            for col in ['open', 'close', 'high', 'low', 'volume', 'amount']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            return df
    except Exception as e:
        print(f"网易财经失败: {e}")
    
    raise Exception("所有数据源都失败")

def get_index_data_sina(symbol: str = "000300") -> pd.DataFrame:
    """获取指数数据"""
    # 使用网易财经获取指数数据
    url = f"https://quotes.money.163.com/service/chddata.html"
    params = {
        'code': f"0{symbol}",
        'start': '20200101',
        'end': datetime.now().strftime('%Y%m%d'),
        'fields': 'TCLOSE;HIGH;LOW;TOPEN;LCLOSE;CHG;PCHG;VOTURNOVER;VATURNOVER',
    }
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            time.sleep(random.uniform(0.5, 1.5))
            session = requests.Session()
            session.trust_env = False
            
            response = session.get(url, params=params, headers=HEADERS, timeout=30)
            response.encoding = 'gb2312'
            
            if response.status_code == 200:
                df = pd.read_csv(StringIO(response.text), skiprows=1,
                               names=['date', 'code', 'name', 'close', 'high', 'low', 'open',
                                      'lclose', 'change', 'pct_change', 'volume', 'amount'])
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                df = df.sort_index()
                
                for col in ['open', 'close', 'high', 'low', 'volume', 'amount']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                
                return df
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(random.uniform(1, 3))
            else:
                raise e
    
    raise Exception("获取指数数据失败")

if __name__ == "__main__":
    print("测试使用网易财经获取股票000002数据...")
    try:
        df = get_stock_data_sina('000002')
        print(f"✅ 成功获取数据: {len(df)} 条记录")
        print(df.tail(3))
    except Exception as e:
        print(f"❌ 失败: {e}")
    
    print("\n测试获取沪深300数据...")
    try:
        df = get_index_data_sina('000300')
        print(f"✅ 成功获取数据: {len(df)} 条记录")
        print(df.tail(3))
    except Exception as e:
        print(f"❌ 失败: {e}")
