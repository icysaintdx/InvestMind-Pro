#!/usr/bin/env python3
"""
负收益股票优化参数回测验证
针对603993和603288使用优化参数进行回测
"""

import sys
sys.path.insert(0, '/home/icysaintdx/.openclaw/workspace/InvestMindPro')

from strategies.ema_v2 import EMAV2Strategy
import pandas as pd
import json

def load_stock_data(symbol):
    """加载股票数据"""
    df = pd.read_csv(f'/home/icysaintdx/.openclaw/workspace/InvestMindPro/data/{symbol}.csv')
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    return df

def run_backtest(symbol, name, params):
    """运行回测"""
    df = load_stock_data(symbol)
    strategy = EMAV2Strategy(params=params)
    result = strategy.run_backtest(df, initial_capital=100000)
    return result

def main():
    print("="*70)
    print("负收益股票优化参数回测验证")
    print("="*70)
    
    results_summary = []
    
    # ===== 603993 洛阳钼业 =====
    print("\n【603993 洛阳钼业】")
    print("-"*70)
    
    # 原参数 (亏损)
    original_params_603993 = {
        "fast_ema": 10,
        "slow_ema": 30,
        "atr_period": 14,
        "atr_multiplier": 3.0,
        "market_filter": True
    }
    
    # 保守优化参数
    optimized_params_603993 = {
        "fast_ema": 10,
        "slow_ema": 40,
        "atr_period": 14,
        "atr_multiplier": 2.5,
        "market_filter": True
    }
    
    # 激进优化参数 (参考用)
    aggressive_params_603993 = {
        "fast_ema": 5,
        "slow_ema": 25,
        "atr_period": 14,
        "atr_multiplier": 3.0,
        "market_filter": True
    }
    
    print("\n1. 原参数 (EMA 10,30, ATR×3.0):")
    result_orig = run_backtest('603993', '洛阳钼业', original_params_603993)
    print(f"   总收益: {result_orig.total_return:.2f}%")
    print(f"   胜率: {result_orig.win_rate:.1f}%")
    print(f"   交易次数: {result_orig.total_trades}")
    print(f"   最大回撤: {result_orig.max_drawdown:.2f}%")
    
    print("\n2. 保守优化 (EMA 10,40, ATR×2.5) ★推荐★:")
    result_opt = run_backtest('603993', '洛阳钼业', optimized_params_603993)
    print(f"   总收益: {result_opt.total_return:.2f}%")
    print(f"   胜率: {result_opt.win_rate:.1f}%")
    print(f"   交易次数: {result_opt.total_trades}")
    print(f"   最大回撤: {result_opt.max_drawdown:.2f}%")
    improvement_603993 = result_opt.total_return - result_orig.total_return
    print(f"   改善: {improvement_603993:+.2f}%")
    
    print("\n3. 激进优化 (EMA 5,25, ATR×3.0):")
    result_agg = run_backtest('603993', '洛阳钼业', aggressive_params_603993)
    print(f"   总收益: {result_agg.total_return:.2f}%")
    print(f"   胜率: {result_agg.win_rate:.1f}%")
    print(f"   交易次数: {result_agg.total_trades}")
    print(f"   最大回撤: {result_agg.max_drawdown:.2f}%")
    
    results_summary.append({
        'symbol': '603993',
        'name': '洛阳钼业',
        'original_return': result_orig.total_return,
        'optimized_return': result_opt.total_return,
        'improvement': improvement_603993,
        'optimized_params': optimized_params_603993,
        'win_rate': result_opt.win_rate,
        'total_trades': result_opt.total_trades,
        'max_drawdown': result_opt.max_drawdown
    })
    
    # ===== 603288 海天味业 =====
    print("\n" + "="*70)
    print("【603288 海天味业】")
    print("-"*70)
    
    # 原参数 (亏损)
    original_params_603288 = {
        "fast_ema": 8,
        "slow_ema": 25,
        "atr_period": 14,
        "atr_multiplier": 2.0,
        "market_filter": True
    }
    
    # 优化参数
    optimized_params_603288 = {
        "fast_ema": 10,
        "slow_ema": 40,
        "atr_period": 14,
        "atr_multiplier": 2.0,
        "market_filter": True
    }
    
    print("\n1. 原参数 (EMA 8,25, ATR×2.0):")
    result_orig = run_backtest('603288', '海天味业', original_params_603288)
    print(f"   总收益: {result_orig.total_return:.2f}%")
    print(f"   胜率: {result_orig.win_rate:.1f}%")
    print(f"   交易次数: {result_orig.total_trades}")
    print(f"   最大回撤: {result_orig.max_drawdown:.2f}%")
    
    print("\n2. 优化参数 (EMA 10,40, ATR×2.0) ★推荐★:")
    result_opt = run_backtest('603288', '海天味业', optimized_params_603288)
    print(f"   总收益: {result_opt.total_return:.2f}%")
    print(f"   胜率: {result_opt.win_rate:.1f}%")
    print(f"   交易次数: {result_opt.total_trades}")
    print(f"   最大回撤: {result_opt.max_drawdown:.2f}%")
    improvement_603288 = result_opt.total_return - result_orig.total_return
    print(f"   改善: {improvement_603288:+.2f}%")
    
    results_summary.append({
        'symbol': '603288',
        'name': '海天味业',
        'original_return': result_orig.total_return,
        'optimized_return': result_opt.total_return,
        'improvement': improvement_603288,
        'optimized_params': optimized_params_603288,
        'win_rate': result_opt.win_rate,
        'total_trades': result_opt.total_trades,
        'max_drawdown': result_opt.max_drawdown
    })
    
    # 汇总
    print("\n" + "="*70)
    print("优化结果汇总")
    print("="*70)
    for r in results_summary:
        print(f"\n{r['symbol']} {r['name']}:")
        print(f"  原收益: {r['original_return']:+.2f}%")
        print(f"  优化后: {r['optimized_return']:+.2f}%")
        print(f"  改善: {r['improvement']:+.2f}%")
        print(f"  推荐参数: {r['optimized_params']}")
    
    # 保存结果
    output = {
        'validation_date': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
        'results': results_summary
    }
    
    output_path = '/home/icysaintdx/.openclaw/workspace/InvestMindPro/results/negative_stock_validation.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 验证结果已保存: {output_path}")
    
    # 返回用于paper_trading.py更新的参数配置
    print("\n" + "="*70)
    print("paper_trading.py OPTIMIZED_PARAMS 配置代码:")
    print("="*70)
    print("\n# 负收益股票优化参数 (2025-02-27)")
    print("'603993': {'name': '洛阳钼业', 'fast_ema': 10, 'slow_ema': 40, 'atr_period': 14, 'atr_multiplier': 2.5, 'market_filter': True, 'note': '保守优化，原参数亏损-15.15%'},")
    print("'603288': {'name': '海天味业', 'fast_ema': 10, 'slow_ema': 40, 'atr_period': 14, 'atr_multiplier': 2.0, 'market_filter': True, 'note': '延长周期，原参数亏损-13.21%'},")

if __name__ == '__main__':
    main()
