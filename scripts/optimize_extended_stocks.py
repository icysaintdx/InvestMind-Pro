#!/usr/bin/env python3
"""
EMA V2.1 扩展股票池参数优化
为新增股票进行参数优化
"""

import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, str(Path(__file__).parent.parent / 'strategies'))
from ema_v2 import EMAV2Strategy

# 新增股票列表（8只）
NEW_STOCKS = {
    '603501': {'name': '韦尔股份', 'volatility': 'high_volatility'},    # 半导体，高波动
    '603259': {'name': '药明康德', 'volatility': 'medium_volatility'},  # CXO，中波动
    '002475': {'name': '立讯精密', 'volatility': 'medium_volatility'},  # 消费电子，中波动
    '300274': {'name': '阳光电源', 'volatility': 'high_volatility'},    # 新能源，高波动
    '300760': {'name': '迈瑞医疗', 'volatility': 'medium_volatility'},  # 医疗器械，中波动
    '600438': {'name': '通威股份', 'volatility': 'high_volatility'},    # 硅料，高波动
    '601899': {'name': '紫金矿业', 'volatility': 'medium_volatility'},  # 有色，中波动
    '603288': {'name': '海天味业', 'volatility': 'low_volatility'},     # 消费，低波动
}

def load_stock_data(symbol: str, data_dir: Path) -> Optional[pd.DataFrame]:
    """加载股票数据"""
    csv_path = data_dir / f"{symbol}.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
        df.columns = [c.lower() for c in df.columns]
        if 'close' not in df.columns and '收盘价' in df.columns:
            df.rename(columns={'收盘价': 'close', '开盘价': 'open', '最高价': 'high', '最低价': 'low', '成交量': 'volume'}, inplace=True)
        df.attrs['symbol'] = symbol
        return df
    return None

def load_market_data(data_dir: Path) -> Optional[pd.DataFrame]:
    """加载沪深300指数数据"""
    return load_stock_data('000300', data_dir)

def optimize_stock_params(symbol: str, stock_info: dict, data_dir: Path) -> Dict:
    """为单只股票优化参数"""
    print(f"\n{'='*60}")
    print(f"优化参数: {symbol} - {stock_info['name']}")
    print(f"波动率类型: {stock_info['volatility']}")
    print(f"{'='*60}")
    
    stock_data = load_stock_data(symbol, data_dir)
    if stock_data is None:
        print(f"[ERROR] 未找到 {symbol} 的数据")
        return None
    
    market_data = load_market_data(data_dir)
    
    print(f"数据范围: {stock_data.index[0].strftime('%Y-%m-%d')} ~ {stock_data.index[-1].strftime('%Y-%m-%d')}")
    print(f"数据条数: {len(stock_data)}")
    
    # 根据波动率类型选择参数范围
    if stock_info['volatility'] == 'high_volatility':
        fast_range = [3, 5, 7, 10]
        slow_range = [20, 25, 30, 35, 40]
        atr_range = [2.0, 2.5, 3.0]
    elif stock_info['volatility'] == 'medium_volatility':
        fast_range = [5, 7, 8, 10, 12]
        slow_range = [20, 25, 30, 35]
        atr_range = [1.5, 2.0, 2.5]
    else:  # low_volatility
        fast_range = [5, 7, 8, 10]
        slow_range = [20, 25, 30]
        atr_range = [1.0, 1.5, 2.0]
    
    best_score = -float('inf')
    best_params = None
    best_result = None
    
    total_combinations = len(fast_range) * len(slow_range) * len(atr_range)
    current = 0
    
    for fast in fast_range:
        for slow in slow_range:
            if fast >= slow:
                continue
            for atr_mult in atr_range:
                current += 1
                params = {
                    "fast_ema": fast,
                    "slow_ema": slow,
                    "atr_period": 14,
                    "atr_multiplier": atr_mult,
                    "market_filter": True
                }
                
                strategy = EMAV2Strategy(params)
                result = strategy.run_backtest(stock_data, market_data)
                
                # 评分公式: 收益 + 0.5*胜率 - |最大回撤|
                score = result.total_return + 0.5 * result.win_rate - abs(result.max_drawdown)
                
                if score > best_score:
                    best_score = score
                    best_params = params
                    best_result = result
                    
                if current % 10 == 0:
                    print(f"  进度: {current}/{total_combinations} - 当前最佳: {best_result.total_return:+.2f}%")
    
    print(f"\n✓ 优化完成!")
    print(f"  最佳参数: 快EMA={best_params['fast_ema']}, 慢EMA={best_params['slow_ema']}, ATR倍数={best_params['atr_multiplier']}")
    print(f"  总收益率: {best_result.total_return:+.2f}%")
    print(f"  胜率: {best_result.win_rate:.1f}%")
    print(f"  交易次数: {best_result.total_trades}")
    print(f"  最大回撤: {best_result.max_drawdown:.2f}%")
    
    return {
        'symbol': symbol,
        'name': stock_info['name'],
        'volatility_type': stock_info['volatility'],
        'best_params': best_params,
        'total_return': best_result.total_return,
        'win_rate': best_result.win_rate,
        'total_trades': best_result.total_trades,
        'max_drawdown': best_result.max_drawdown,
        'sharpe_ratio': best_result.sharpe_ratio,
        'score': best_score
    }

def main():
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / 'data'
    output_dir = base_dir / 'results'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    all_results = []
    optimized_params = {}
    
    print("\n" + "="*60)
    print("EMA V2.1 扩展股票池参数优化")
    print("="*60)
    print(f"共 {len(NEW_STOCKS)} 只股票待优化\n")
    
    for symbol, info in NEW_STOCKS.items():
        result = optimize_stock_params(symbol, info, data_dir)
        if result:
            all_results.append(result)
            optimized_params[symbol] = {
                'name': info['name'],
                **result['best_params']
            }
    
    # 保存优化结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 保存详细结果
    results_file = output_dir / f'extended_optimization_{timestamp}.json'
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'stocks_count': len(all_results),
            'results': all_results
        }, f, ensure_ascii=False, indent=2)
    
    # 保存优化后的参数配置
    params_file = output_dir / f'extended_optimized_params_{timestamp}.json'
    with open(params_file, 'w', encoding='utf-8') as f:
        json.dump(optimized_params, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*60}")
    print("参数优化完成!")
    print(f"{'='*60}")
    print(f"结果保存: {results_file}")
    print(f"参数配置: {params_file}")
    print(f"\n汇总:")
    print(f"  平均收益率: {np.mean([r['total_return'] for r in all_results]):+.2f}%")
    print(f"  正收益股票: {sum(1 for r in all_results if r['total_return'] > 0)}/{len(all_results)}")
    print(f"  最佳收益: {max(r['total_return'] for r in all_results):+.2f}%")
    print(f"  最差收益: {min(r['total_return'] for r in all_results):+.2f}%")
    
    # 打印Python代码格式的参数配置
    print(f"\n参数配置代码 (可直接复制到 run_optimized_backtest.py):")
    print("-" * 60)
    for symbol, params in optimized_params.items():
        print(f"    '{symbol}': {{'name': '{params['name']}', 'fast_ema': {params['fast_ema']}, 'slow_ema': {params['slow_ema']}, 'atr_period': 14, 'atr_multiplier': {params['atr_multiplier']}, 'market_filter': True}},")

if __name__ == '__main__':
    main()
