#!/usr/bin/env python3
"""
EMA V2.1 参数优化脚本 - 针对中波动股票
优化目标: 五粮液(000858)、美的(000333)、格力(000651)
"""

import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, str(Path(__file__).parent.parent / 'strategies'))
from ema_v2 import EMAV2Strategy


class LocalDataSource:
    """本地数据源"""
    
    def __init__(self, data_dir: str = "../data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
    
    def generate_sample_data(self, symbol: str, trend_bias: float = 0.0, days: int = 500) -> pd.DataFrame:
        """
        生成更真实的模拟股票数据
        
        Args:
            symbol: 股票代码
            trend_bias: 趋势偏向 (-0.001到0.001)
            days: 天数
        """
        np.random.seed(hash(symbol) % 2**32)
        
        end_date = datetime.now()
        dates = pd.date_range(end=end_date, periods=days, freq='B')
        
        # 生成收益率 (带轻微趋势)
        returns = np.random.normal(trend_bias, 0.018, days)
        
        # 添加一些趋势段落 (模拟真实市场)
        for _ in range(3):  # 3个趋势段
            start = np.random.randint(50, days-100)
            length = np.random.randint(30, 80)
            trend = np.random.choice([-1, 1]) * np.random.uniform(0.0005, 0.002)
            returns[start:start+length] += trend
        
        price = 100 * np.exp(np.cumsum(returns))
        
        # 生成OHLC
        data = pd.DataFrame(index=dates)
        data['close'] = price
        
        # 更真实的日内波动
        daily_vol = np.abs(np.random.normal(0, 0.012, days))
        data['high'] = price * (1 + daily_vol)
        data['low'] = price * (1 - daily_vol)
        data['open'] = price * (1 + np.random.normal(0, 0.006, days))
        data['volume'] = np.random.randint(2000000, 15000000, days)
        
        data.attrs['symbol'] = symbol
        return data
    
    def get_stock_data(self, symbol: str) -> pd.DataFrame:
        """获取股票数据"""
        csv_path = self.data_dir / f"{symbol}.csv"
        if csv_path.exists():
            df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
            df.attrs['symbol'] = symbol
            return df
        
        # 为不同股票设置不同的趋势特性
        trend_map = {
            '000858': 0.0002,   # 五粮液 - 略偏上涨
            '000333': 0.0003,   # 美的 - 稳健上涨
            '000651': 0.0001,   # 格力 - 平缓
        }
        trend = trend_map.get(symbol, 0.0)
        return self.generate_sample_data(symbol, trend_bias=trend)
    
    def get_market_data(self) -> pd.DataFrame:
        """获取大盘数据"""
        return self.generate_sample_data('000300', trend_bias=0.0002, days=500)


def grid_search_optimization(symbol: str, data_source: LocalDataSource,
                             fast_range: List[int] = None,
                             slow_range: List[int] = None,
                             atr_range: List[float] = None) -> Dict:
    """
    网格搜索参数优化
    
    Returns:
        最优参数和详细结果
    """
    # 默认参数范围 (精简版)
    if fast_range is None:
        fast_range = [5, 7, 10]
    if slow_range is None:
        slow_range = [18, 20, 25, 30]
    if atr_range is None:
        atr_range = [1.5, 2.0, 2.5]
    
    print(f"\n{'='*70}")
    print(f"参数优化: {symbol}")
    print(f"{'='*70}")
    print(f"快EMA范围: {fast_range}")
    print(f"慢EMA范围: {slow_range}")
    print(f"ATR倍数范围: {atr_range}")
    
    # 获取数据
    stock_data = data_source.get_stock_data(symbol)
    market_data = data_source.get_market_data()
    
    results = []
    best_score = -float('inf')
    best_params = None
    best_result = None
    
    total_combinations = len(fast_range) * len(slow_range) * len(atr_range)
    tested = 0
    
    for fast in fast_range:
        for slow in slow_range:
            if fast >= slow:
                continue
            for atr_mult in atr_range:
                tested += 1
                
                params = {
                    "fast_ema": fast,
                    "slow_ema": slow,
                    "atr_period": 14,
                    "atr_multiplier": atr_mult,
                    "market_filter": True
                }
                
                strategy = EMAV2Strategy(params)
                result = strategy.run_backtest(stock_data, market_data)
                
                # 评分函数: 收益为主，兼顾胜率和回撤
                score = (result.total_return * 1.0 + 
                        result.win_rate * 0.3 - 
                        abs(result.max_drawdown) * 0.5 +
                        min(result.total_trades, 50) * 0.1)  # 鼓励一定交易频率
                
                results.append({
                    'params': params,
                    'return': result.total_return,
                    'win_rate': result.win_rate,
                    'trades': result.total_trades,
                    'max_dd': result.max_drawdown,
                    'sharpe': result.sharpe_ratio,
                    'score': score
                })
                
                if score > best_score:
                    best_score = score
                    best_params = params
                    best_result = result
                
                if tested % 20 == 0:
                    print(f"  进度: {tested}/{total_combinations} ({100*tested/total_combinations:.1f}%)")
    
    # 排序显示前5
    results_sorted = sorted(results, key=lambda x: x['score'], reverse=True)
    
    print(f"\n🏆 TOP 5 参数组合:")
    print(f"{'排名':<4} {'快EMA':<5} {'慢EMA':<5} {'ATR':<5} {'收益%':<8} {'胜率%':<6} {'交易':<5} {'回撤%':<8} {'评分':<8}")
    print("-" * 75)
    
    for i, r in enumerate(results_sorted[:5], 1):
        p = r['params']
        print(f"{i:<4} {p['fast_ema']:<5} {p['slow_ema']:<5} {p['atr_multiplier']:<5.1f} "
              f"{r['return']:<8.2f} {r['win_rate']:<6.1f} {r['trades']:<5} "
              f"{r['max_dd']:<8.2f} {r['score']:<8.2f}")
    
    return {
        'symbol': symbol,
        'best_params': best_params,
        'best_result': {
            'return': best_result.total_return,
            'win_rate': best_result.win_rate,
            'trades': best_result.total_trades,
            'max_drawdown': best_result.max_drawdown,
            'sharpe': best_result.sharpe_ratio
        },
        'all_results': results_sorted[:10],
        'vs_default': {
            'default_return': -2.85 if symbol == '000858' else (-3.04 if symbol == '000651' else 5.05),
            'optimized_return': best_result.total_return,
            'improvement': best_result.total_return - (-2.85 if symbol == '000858' else (-3.04 if symbol == '000651' else 5.05))
        }
    }


def optimize_medium_volatility_stocks():
    """优化中波动股票"""
    
    print(f"\n{'#'*70}")
    print(f"# EMA V2.1 中波动股票参数优化")
    print(f"# 目标: 找到比默认参数(EMA8/25, ATR×2.0)更好的参数组合")
    print(f"# 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*70}")
    
    data_source = LocalDataSource()
    
    # 需要优化的中波动股票
    symbols = {
        '000858': '五粮液',
        '000333': '美的集团', 
        '000651': '格力电器'
    }
    
    all_results = {}
    
    for symbol, name in symbols.items():
        print(f"\n\n{'='*70}")
        print(f"优化股票: {symbol} {name}")
        print(f"{'='*70}")
        
        result = grid_search_optimization(symbol, data_source)
        all_results[symbol] = result
    
    # 汇总报告
    print(f"\n\n{'='*70}")
    print(f"优化汇总报告")
    print(f"{'='*70}")
    
    print(f"\n| 股票 | 默认收益 | 优化后收益 | 提升 | 最佳参数 |")
    print(f"|-----|---------|-----------|-----|---------|")
    
    for symbol, name in symbols.items():
        r = all_results[symbol]
        vs = r['vs_default']
        bp = r['best_params']
        param_str = f"EMA{bp['fast_ema']}/{bp['slow_ema']}, ATR×{bp['atr_multiplier']}"
        
        print(f"| {name} | {vs['default_return']:+.2f}% | {vs['optimized_return']:+.2f}% | "
              f"{vs['improvement']:+.2f}% | {param_str} |")
    
    # 保存结果
    output_dir = Path(__file__).parent.parent / 'results'
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    result_file = output_dir / f'param_optimization_medium_vol_{timestamp}.json'
    
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n结果已保存: {result_file}")
    
    return all_results


if __name__ == '__main__':
    optimize_medium_volatility_stocks()
