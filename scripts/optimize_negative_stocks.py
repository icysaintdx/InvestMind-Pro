#!/usr/bin/env python3
"""
负收益股票参数优化测试
针对603993(洛阳钼业)和603288(海天味业)进行参数微调
"""

import json
import sys
sys.path.insert(0, '/home/icysaintdx/.openclaw/workspace/InvestMindPro')

from strategies.ema_v2 import EMAV2Strategy
import pandas as pd
import numpy as np

def load_stock_data(symbol):
    """加载股票数据"""
    df = pd.read_csv(f'/home/icysaintdx/.openclaw/workspace/InvestMindPro/data/{symbol}.csv')
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    return df

def run_single_backtest(symbol, name, params, volatility_type):
    """运行单次回测"""
    try:
        df = load_stock_data(symbol)
        strategy = EMAV2Strategy(params=params, volatility_type=volatility_type)
        result = strategy.run_backtest(df, initial_capital=100000)
        
        return {
            'symbol': symbol,
            'name': name,
            'params': params,
            'total_return': result.total_return,
            'win_rate': result.win_rate,
            'total_trades': result.total_trades,
            'max_drawdown': result.max_drawdown,
            'sharpe_ratio': result.sharpe_ratio
        }
    except Exception as e:
        return {
            'symbol': symbol,
            'name': name,
            'params': params,
            'error': str(e)
        }

def test_parameter_combinations(symbol, name, base_params, volatility_type):
    """测试多种参数组合"""
    results = []
    
    # 基础参数
    base = base_params.copy()
    
    # 参数变化范围
    fast_ema_options = [5, 8, 10, 12, 15]
    slow_ema_options = [20, 25, 30, 35, 40]
    atr_mult_options = [1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
    
    print(f"\n{'='*60}")
    print(f"测试股票: {symbol} {name}")
    print(f"基础参数: {base}")
    print(f"{'='*60}")
    
    # 1. 测试不同EMA周期组合
    print("\n1. 测试EMA周期组合...")
    for fast in fast_ema_options:
        for slow in slow_ema_options:
            if fast >= slow:
                continue
            params = base.copy()
            params['fast_ema'] = fast
            params['slow_ema'] = slow
            result = run_single_backtest(symbol, name, params, volatility_type)
            results.append(result)
            print(f"  EMA({fast},{slow}): 收益={result.get('total_return', 'N/A'):.2f}%, 胜率={result.get('win_rate', 0):.1f}%, 交易={result.get('total_trades', 0)}")
    
    # 2. 测试不同ATR倍数
    print("\n2. 测试ATR倍数...")
    base_fast = base['fast_ema']
    base_slow = base['slow_ema']
    for atr_mult in atr_mult_options:
        params = base.copy()
        params['fast_ema'] = base_fast
        params['slow_ema'] = base_slow
        params['atr_multiplier'] = atr_mult
        result = run_single_backtest(symbol, name, params, volatility_type)
        results.append(result)
        print(f"  ATR倍数={atr_mult}: 收益={result.get('total_return', 'N/A'):.2f}%, 胜率={result.get('win_rate', 0):.1f}%")
    
    # 3. 测试market_filter开关
    print("\n3. 测试市场过滤开关...")
    for market_filter in [True, False]:
        params = base.copy()
        params['market_filter'] = market_filter
        result = run_single_backtest(symbol, name, params, volatility_type)
        results.append(result)
        status = "开启" if market_filter else "关闭"
        print(f"  市场过滤{status}: 收益={result.get('total_return', 'N/A'):.2f}%, 胜率={result.get('win_rate', 0):.1f}%")
    
    return results

def find_best_params(results):
    """找出最佳参数组合"""
    valid_results = [r for r in results if 'error' not in r and r.get('total_return') is not None]
    if not valid_results:
        return None
    
    # 按总收益排序
    best = max(valid_results, key=lambda x: x['total_return'])
    return best

def main():
    print("="*70)
    print("负收益股票参数优化测试")
    print("="*70)
    
    all_results = {}
    
    # 1. 测试洛阳钼业 (603993) - 高波动
    lymc_base = {
        "fast_ema": 10,
        "slow_ema": 30,
        "atr_period": 14,
        "atr_multiplier": 3.0,
        "market_filter": True
    }
    lymc_results = test_parameter_combinations('603993', '洛阳钼业', lymc_base, 'high_volatility')
    all_results['603993'] = lymc_results
    
    # 2. 测试海天味业 (603288) - 中波动
    htwy_base = {
        "fast_ema": 8,
        "slow_ema": 25,
        "atr_period": 14,
        "atr_multiplier": 2.0,
        "market_filter": True
    }
    htwy_results = test_parameter_combinations('603288', '海天味业', htwy_base, 'medium_volatility')
    all_results['603288'] = htwy_results
    
    # 汇总结果
    print("\n" + "="*70)
    print("优化结果汇总")
    print("="*70)
    
    for symbol, results in all_results.items():
        best = find_best_params(results)
        if best:
            print(f"\n{best['symbol']} {best['name']}:")
            print(f"  最佳收益: {best['total_return']:.2f}%")
            print(f"  最佳参数: {best['params']}")
            print(f"  胜率: {best['win_rate']:.1f}%")
            print(f"  交易次数: {best['total_trades']}")
            print(f"  最大回撤: {best['max_drawdown']:.2f}%")
    
    # 保存结果
    output_path = '/home/icysaintdx/.openclaw/workspace/InvestMindPro/results/negative_stock_optimization.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存到: {output_path}")

if __name__ == '__main__':
    main()
