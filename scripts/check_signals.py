#!/usr/bin/env python3
"""
交易信号预检脚本
检查所有监控股票的当前EMA状态，预测明日可能的交易信号
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from strategies.ema_v2 import EMAV2Strategy

# 优化参数配置 (34只股票完整配置)
OPTIMIZED_PARAMS = {
    # === 原始22只 ===
    '000001': {'name': '平安银行', 'fast_ema': 7, 'slow_ema': 20, 'atr_multiplier': 1.0},
    '000333': {'name': '美的集团', 'fast_ema': 3, 'slow_ema': 40, 'atr_multiplier': 1.5},
    '000568': {'name': '泸州老窖', 'fast_ema': 15, 'slow_ema': 40, 'atr_multiplier': 2.5},
    '000651': {'name': '格力电器', 'fast_ema': 10, 'slow_ema': 30, 'atr_multiplier': 1.5},
    '000858': {'name': '五粮液', 'fast_ema': 8, 'slow_ema': 35, 'atr_multiplier': 2.5},
    '002415': {'name': '海康威视', 'fast_ema': 12, 'slow_ema': 15, 'atr_multiplier': 3.0},
    '002460': {'name': '赣锋锂业', 'fast_ema': 3, 'slow_ema': 35, 'atr_multiplier': 1.5},
    '002594': {'name': '比亚迪', 'fast_ema': 7, 'slow_ema': 30, 'atr_multiplier': 2.5},
    '002714': {'name': '牧原股份', 'fast_ema': 12, 'slow_ema': 20, 'atr_multiplier': 2.0},
    '300014': {'name': '亿纬锂能', 'fast_ema': 5, 'slow_ema': 40, 'atr_multiplier': 2.0},
    '300033': {'name': '同花顺', 'fast_ema': 15, 'slow_ema': 35, 'atr_multiplier': 1.0},
    '300124': {'name': '汇川技术', 'fast_ema': 3, 'slow_ema': 40, 'atr_multiplier': 1.5},
    '300274': {'name': '阳光电源', 'fast_ema': 10, 'slow_ema': 30, 'atr_multiplier': 3.0},
    '300750': {'name': '宁德时代', 'fast_ema': 3, 'slow_ema': 35, 'atr_multiplier': 2.0},
    '600036': {'name': '招商银行', 'fast_ema': 7, 'slow_ema': 25, 'atr_multiplier': 1.0},
    '600276': {'name': '恒瑞医药', 'fast_ema': 7, 'slow_ema': 40, 'atr_multiplier': 1.5},
    '600438': {'name': '通威股份', 'fast_ema': 12, 'slow_ema': 25, 'atr_multiplier': 2.0},
    '600519': {'name': '贵州茅台', 'fast_ema': 15, 'slow_ema': 40, 'atr_multiplier': 1.5},
    '600887': {'name': '伊利股份', 'fast_ema': 15, 'slow_ema': 40, 'atr_multiplier': 3.0},
    '600900': {'name': '长江电力', 'fast_ema': 12, 'slow_ema': 20, 'atr_multiplier': 1.0},
    '601012': {'name': '隆基绿能', 'fast_ema': 12, 'slow_ema': 18, 'atr_multiplier': 1.5},
    '601288': {'name': '农业银行', 'fast_ema': 12, 'slow_ema': 30, 'atr_multiplier': 1.0},
    '601318': {'name': '中国平安', 'fast_ema': 10, 'slow_ema': 50, 'atr_multiplier': 1.5},
    '601888': {'name': '中国中免', 'fast_ema': 15, 'slow_ema': 40, 'atr_multiplier': 2.0},
    # === 扩展12只 ===
    '002475': {'name': '立讯精密', 'fast_ema': 5, 'slow_ema': 35, 'atr_multiplier': 1.5},
    '300760': {'name': '迈瑞医疗', 'fast_ema': 12, 'slow_ema': 35, 'atr_multiplier': 2.0},
    '600760': {'name': '中航沈飞', 'fast_ema': 10, 'slow_ema': 30, 'atr_multiplier': 2.0},
    '600893': {'name': '航发动力', 'fast_ema': 15, 'slow_ema': 40, 'atr_multiplier': 1.5},
    '601899': {'name': '紫金矿业', 'fast_ema': 10, 'slow_ema': 25, 'atr_multiplier': 2.0},
    '603259': {'name': '药明康德', 'fast_ema': 8, 'slow_ema': 30, 'atr_multiplier': 2.0},
    '603288': {'name': '海天味业', 'fast_ema': 10, 'slow_ema': 40, 'atr_multiplier': 2.0},
    '603501': {'name': '韦尔股份', 'fast_ema': 10, 'slow_ema': 40, 'atr_multiplier': 2.5},
    '603993': {'name': '洛阳钼业', 'fast_ema': 10, 'slow_ema': 40, 'atr_multiplier': 2.5},
    '688981': {'name': '中芯国际', 'fast_ema': 12, 'slow_ema': 35, 'atr_multiplier': 2.0},
}

def load_stock_data(symbol, data_dir):
    """加载股票数据"""
    file_path = data_dir / f"{symbol}.csv"
    if not file_path.exists():
        return None
    
    df = pd.read_csv(file_path)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    return df

def check_signal_status(symbol, params, data_dir):
    """检查股票当前EMA状态和潜在信号"""
    df = load_stock_data(symbol, data_dir)
    if df is None or len(df) < 60:
        return None
    
    # 计算EMA
    df['fast_ema'] = df['close'].ewm(span=params['fast_ema'], adjust=False).mean()
    df['slow_ema'] = df['close'].ewm(span=params['slow_ema'], adjust=False).mean()
    
    # 获取最近3天数据
    recent = df.tail(3)
    
    if len(recent) < 3:
        return None
    
    curr = recent.iloc[-1]
    prev = recent.iloc[-2]
    prev2 = recent.iloc[-3]
    
    # 判断EMA状态
    curr_fast = curr['fast_ema']
    curr_slow = curr['slow_ema']
    prev_fast = prev['fast_ema']
    prev_slow = prev['slow_ema']
    
    status = {}
    status['symbol'] = symbol
    status['name'] = params['name']
    status['date'] = curr['date'].strftime('%Y-%m-%d')
    status['close'] = round(curr['close'], 2)
    status['fast_ema'] = round(curr_fast, 2)
    status['slow_ema'] = round(curr_slow, 2)
    status['ema_diff'] = round(curr_fast - curr_slow, 2)
    status['trend'] = 'UP' if curr_fast > curr_slow else 'DOWN'
    
    # 检查金叉/死叉
    golden_cross = prev_fast <= prev_slow and curr_fast > curr_slow
    death_cross = prev_fast >= prev_slow and curr_fast < curr_slow
    
    if golden_cross:
        status['signal'] = 'BUY'
        status['signal_date'] = status['date']
    elif death_cross:
        status['signal'] = 'SELL'
        status['signal_date'] = status['date']
    else:
        status['signal'] = None
        # 计算距离交叉的距离
        if curr_fast < curr_slow:
            # 在下方，计算潜在金叉条件
            status['next_signal'] = 'potential_buy'
            status['distance_pct'] = round((curr_slow - curr_fast) / curr_slow * 100, 2)
        else:
            # 在上方，计算潜在死叉条件
            status['next_signal'] = 'potential_sell'
            status['distance_pct'] = round((curr_fast - curr_slow) / curr_slow * 100, 2)
    
    return status

def main():
    print("=" * 80)
    print("📊 EMA V2.1 交易信号预检报告")
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    data_dir = Path(__file__).parent.parent / "data"
    
    # 检查所有股票
    buy_signals = []
    sell_signals = []
    potential_signals = []
    holding = []
    
    for symbol, params in OPTIMIZED_PARAMS.items():
        status = check_signal_status(symbol, params, data_dir)
        if status:
            if status['signal'] == 'BUY':
                buy_signals.append(status)
            elif status['signal'] == 'SELL':
                sell_signals.append(status)
            elif status.get('next_signal'):
                potential_signals.append(status)
            
            if status['trend'] == 'UP':
                holding.append(status)
    
    # 打印结果
    print(f"\n🟢 买入信号 ({len(buy_signals)}只):")
    print("-" * 80)
    if buy_signals:
        for s in buy_signals:
            print(f"  {s['symbol']} {s['name']}: 金叉确认 @ {s['close']}")
            print(f"    快EMA({s['fast_ema']}) > 慢EMA({s['slow_ema']})")
    else:
        print("  暂无买入信号")
    
    print(f"\n🔴 卖出信号 ({len(sell_signals)}只):")
    print("-" * 80)
    if sell_signals:
        for s in sell_signals:
            print(f"  {s['symbol']} {s['name']}: 死叉确认 @ {s['close']}")
    else:
        print("  暂无卖出信号")
    
    print(f"\n📈 多头排列中 ({len(holding)}只):")
    print("-" * 80)
    for s in holding[:10]:  # 只显示前10只
        diff_pct = (s['close'] - s['slow_ema']) / s['slow_ema'] * 100
        print(f"  {s['symbol']} {s['name']}: {s['close']} | 偏离慢EMA: {diff_pct:+.1f}%")
    if len(holding) > 10:
        print(f"  ... 还有 {len(holding) - 10} 只")
    
    print(f"\n⚡ 潜在信号 ({len(potential_signals)}只距离交叉<5%):")
    print("-" * 80)
    close_signals = [s for s in potential_signals if s.get('distance_pct', 100) < 5]
    for s in close_signals[:10]:
        signal_type = "潜在金叉" if s['next_signal'] == 'potential_buy' else "潜在死叉"
        print(f"  {s['symbol']} {s['name']}: {signal_type} | 距离: {s['distance_pct']}%")
    
    print("\n" + "=" * 80)
    print("💡 明日(2月28日)交易监控提示:")
    print("-" * 80)
    if buy_signals:
        print(f"  • 有 {len(buy_signals)} 只股票触发买入信号，明日开盘后需执行买入")
    else:
        print("  • 暂无买入信号，继续观望")
    
    print(f"  • 当前 {len(holding)} 只股票处于多头排列，持有观望")
    
    if close_signals:
        print(f"  • 有 {len(close_signals)} 只股票接近EMA交叉，建议重点监控")
    
    print("\n" + "=" * 80)
    
    # 保存结果
    results = {
        'generated_at': datetime.now().isoformat(),
        'buy_signals': buy_signals,
        'sell_signals': sell_signals,
        'potential_signals': potential_signals,
        'holding': holding
    }
    
    results_dir = Path(__file__).parent.parent / "results" / "paper_trading"
    results_dir.mkdir(exist_ok=True)
    
    with open(results_dir / 'signal_check.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n📁 结果已保存: results/paper_trading/signal_check.json")

if __name__ == "__main__":
    main()
