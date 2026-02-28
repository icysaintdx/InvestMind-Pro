#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
尝试使用baostock下载缺失股票数据
"""

import sys
import os
from pathlib import Path
import pandas as pd

project_root = Path("/home/icysaintdx/.openclaw/workspace-investmindpro/InvestMindPro")
CACHE_DIR = project_root / "backend" / "data" / "backtest_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# 缺失的股票
MISSING_STOCKS = {
    "300750": "宁德时代",
    "002594": "比亚迪",
    "002415": "海康威视",
    "601012": "隆基绿能"
}

def download_with_baostock(symbol, name):
    """使用baostock下载数据"""
    try:
        import baostock as bs
        
        print(f"[{symbol}] 尝试使用baostock下载...")
        
        # 登录
        lg = bs.login()
        if lg.error_code != '0':
            print(f"[{symbol}] baostock登录失败: {lg.error_msg}")
            return None
        
        # 调整股票代码格式
        if symbol.startswith('6'):
            bs_code = f"sh.{symbol}"
        else:
            bs_code = f"sz.{symbol}"
        
        # 查询历史数据
        rs = bs.query_history_k_data_plus(
            bs_code,
            "date,open,high,low,close,volume,amount",
            start_date="2024-01-01",
            end_date="2024-12-31",
            frequency="d",
            adjustflag="3"  # 前复权
        )
        
        data_list = []
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())
        
        bs.logout()
        
        if len(data_list) == 0:
            print(f"[{symbol}] 无数据返回")
            return None
        
        # 创建DataFrame
        df = pd.DataFrame(data_list, columns=['date', 'open', 'high', 'low', 'close', 'volume', 'amount'])
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # 转换数值类型
        for col in ['open', 'high', 'low', 'close', 'volume', 'amount']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 添加股票代码列
        df['股票代码'] = symbol
        
        # 计算其他列
        df['振幅'] = ((df['high'] - df['low']) / df['close'].shift(1) * 100).round(2)
        df['涨跌幅'] = df['close'].pct_change() * 100
        df['涨跌额'] = df['close'].diff()
        
        # 保存
        filename = f"{symbol}_20240101_20241231.csv"
        filepath = CACHE_DIR / filename
        df.to_csv(filepath)
        print(f"[{symbol}] 数据下载成功: {len(df)} 条记录 -> {filepath}")
        return df
        
    except Exception as e:
        print(f"[{symbol}] baostock下载失败: {e}")
        return None

def main():
    print("=" * 60)
    print("尝试下载缺失股票数据")
    print("=" * 60)
    
    success_count = 0
    for symbol, name in MISSING_STOCKS.items():
        df = download_with_baostock(symbol, name)
        if df is not None:
            success_count += 1
    
    print(f"\n下载完成: {success_count}/{len(MISSING_STOCKS)} 只股票成功")

if __name__ == "__main__":
    main()
