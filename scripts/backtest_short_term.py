#!/usr/bin/env python3
"""
短线EMA回测脚本 - 基于最近3个月数据
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime
import os
import sys

# 添加项目路径
sys.path.insert(0, '/home/icysaintdx/.openclaw/workspace-investmindpro/InvestMindPro')

def calculate_ema(prices, period):
    """计算EMA"""
    return prices.ewm(span=period, adjust=False).mean()

def calculate_atr(df, period=14):
    """计算ATR"""
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    return true_range.rolling(period).mean()

def backtest_short_term(stock_code, fast=5, slow=20, atr_period=14):
    """短线回测 - 最近3个月"""
    data_file = f"data/short_term/{stock_code}_short.csv"
    
    if not os.path.exists(data_file):
        return None
    
    df = pd.read_csv(data_file)
    if len(df) < slow + 10:
        return None
    
    # 计算指标
    df['ema_fast'] = calculate_ema(df['close'], fast)
    df['ema_slow'] = calculate_ema(df['close'], slow)
    df['atr'] = calculate_atr(df, atr_period)
    
    # 信号生成
    df['signal'] = 0
    df.loc[df['ema_fast'] > df['ema_slow'], 'signal'] = 1  # 金叉
    df.loc[df['ema_fast'] < df['ema_slow'], 'signal'] = -1  # 死叉
    
    # 简化回测逻辑
    trades = []
    position = 0
    entry_price = 0
    
    for i in range(1, len(df)):
        prev_signal = df['signal'].iloc[i-1]
        curr_signal = df['signal'].iloc[i]
        
        # 金叉买入
        if prev_signal <= 0 and curr_signal == 1 and position == 0:
            position = 1
            entry_price = df['close'].iloc[i]
            trades.append({
                'type': 'buy',
                'date': df['date'].iloc[i],
                'price': entry_price
            })
        
        # 死叉卖出
        elif prev_signal >= 0 and curr_signal == -1 and position == 1:
            exit_price = df['close'].iloc[i]
            profit = (exit_price - entry_price) / entry_price * 100
            position = 0
            trades.append({
                'type': 'sell',
                'date': df['date'].iloc[i],
                'price': exit_price,
                'profit': profit
            })
    
    # 计算统计
    if len(trades) < 2:
        return None
    
    sell_trades = [t for t in trades if t['type'] == 'sell']
    if not sell_trades:
        return None
    
    profits = [t['profit'] for t in sell_trades]
    wins = len([p for p in profits if p > 0])
    
    return {
        'stock_code': stock_code,
        'total_trades': len(sell_trades),
        'win_rate': wins / len(sell_trades) * 100,
        'avg_profit': np.mean(profits),
        'total_profit': sum(profits),
        'trades': trades
    }

def main():
    print("="*60)
    print("📊 EMA V2.1 短线回测 - 最近3个月")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # 读取元数据获取股票列表
    try:
        with open("data/short_term/meta.json") as f:
            meta = json.load(f)
            stocks = meta['stocks']
    except:
        stocks = []
    
    if not stocks:
        print("❌ 未找到股票列表，请先运行 fetch_short_term_data.py")
        return
    
    results = []
    for code in stocks:
        print(f"\n回测 {code} ...", end=" ")
        result = backtest_short_term(code)
        if result:
            print(f"✅ 收益: {result['total_profit']:.2f}% 胜率: {result['win_rate']:.1f}%")
            results.append(result)
        else:
            print("❌ 数据不足或无可交易信号")
    
    if results:
        avg_profit = np.mean([r['total_profit'] for r in results])
        avg_win_rate = np.mean([r['win_rate'] for r in results])
        
        print("\n" + "="*60)
        print("📈 短线回测汇总")
        print(f"回测股票: {len(results)}")
        print(f"平均收益: {avg_profit:.2f}%")
        print(f"平均胜率: {avg_win_rate:.1f}%")
        print("="*60)
        
        # 保存结果
        output = {
            'created_at': datetime.now().isoformat(),
            'data_range': '3_months',
            'summary': {
                'stock_count': len(results),
                'avg_profit': float(avg_profit),
                'avg_win_rate': float(avg_win_rate)
            },
            'results': results
        }
        
        os.makedirs('results/short_term', exist_ok=True)
        with open('results/short_term/backtest_results.json', 'w') as f:
            json.dump(output, f, indent=2, default=str)
        
        print(f"\n✅ 结果已保存: results/short_term/backtest_results.json")

if __name__ == "__main__":
    main()
