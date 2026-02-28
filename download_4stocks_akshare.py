#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用akshare下载缺失股票数据 (2020-2024)
"""

import sys
import os
from pathlib import Path
import pandas as pd

project_root = Path("/home/icysaintdx/.openclaw/workspace-investmindpro/InvestMindPro")
CACHE_DIR = project_root / "backend" / "data" / "backtest_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# 目标股票
TARGET_STOCKS = {
    "300750": "宁德时代",
    "002594": "比亚迪", 
    "002415": "海康威视",
    "601012": "隆基绿能"
}

def download_with_akshare(symbol, name):
    """使用akshare下载数据"""
    try:
        import akshare as ak
        
        print(f"[{symbol} {name}] 开始下载...")
        
        # 使用akshare获取日线数据
        # 格式: 深交所 szXXXXXX, 上交所 shXXXXXX
        if symbol.startswith('6'):
            stock_code = f"sh{symbol}"
        else:
            stock_code = f"sz{symbol}"
        
        # 下载历史数据 (前复权)
        df = ak.stock_zh_a_daily(symbol=stock_code, start_date="20200101", end_date="20241231", adjust="qfq")
        
        if df is None or len(df) == 0:
            print(f"[{symbol}] 无数据返回")
            return None
        
        print(f"[{symbol}] 下载完成: {len(df)} 条记录")
        print(f"[{symbol}] 数据区间: {df.index[0]} ~ {df.index[-1]}")
        
        # 标准化列名
        column_mapping = {
            'open': 'open', 'close': 'close', 
            'high': 'high', 'low': 'low', 
            'volume': 'volume', 'amount': 'amount'
        }
        df = df.rename(columns=column_mapping)
        
        # 确保数值类型
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 计算振幅和涨跌幅
        df['振幅'] = ((df['high'] - df['low']) / df['close'].shift(1) * 100).round(2)
        df['涨跌幅'] = df['close'].pct_change() * 100
        df['涨跌额'] = df['close'].diff()
        df['股票代码'] = symbol
        
        # 保存为CSV (保持与原数据格式一致)
        filename = f"{symbol}_20200101_20241231.csv"
        filepath = CACHE_DIR / filename
        df.to_csv(filepath)
        print(f"[{symbol}] 数据保存成功: {filepath}")
        
        return df
        
    except Exception as e:
        print(f"[{symbol}] 下载失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("=" * 60)
    print("akshare股票数据下载工具")
    print("=" * 60)
    print(f"目标目录: {CACHE_DIR}")
    print()
    
    success_count = 0
    for symbol, name in TARGET_STOCKS.items():
        df = download_with_akshare(symbol, name)
        if df is not None:
            success_count += 1
        print()
    
    print("=" * 60)
    print(f"下载完成: {success_count}/{len(TARGET_STOCKS)} 只股票成功")
    print("=" * 60)

if __name__ == "__main__":
    main()
