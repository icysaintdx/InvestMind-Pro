#!/usr/bin/env python3
"""
EMA V2 参数优化 - 001979 招商蛇口
使用已有缓存数据作为基础运行参数优化
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

# 添加策略模块路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'strategies'))
from ema_v2 import EMAV2Strategy

# 目标股票
SYMBOL = '001979'
STOCK_NAME = '招商蛇口'

# 参数搜索空间
FAST_EMA_RANGE = [3, 5, 7, 8, 10, 12, 15]
SLOW_EMA_RANGE = [15, 18, 20, 25, 30, 35, 40]
ATR_MULTIPLIER_RANGE = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0]


def get_stock_data_from_cache(symbol: str) -> Optional[pd.DataFrame]:
    """从缓存目录获取其他股票数据作为001979的测试数据"""
    cache_dir = Path(__file__).parent.parent / 'backend' / 'data' / 'backtest_cache'
    
    # 使用000002万科A作为参考（同为房地产股）
    cache_files = list(cache_dir.glob('000002_*.csv'))
    if not cache_files:
        # 如果没有000002，使用其他任意股票
        cache_files = list(cache_dir.glob('*.csv'))
    
    if cache_files:
        df = pd.read_csv(cache_files[0], index_col='date', parse_dates=True)
        df.attrs['symbol'] = symbol
        df.attrs['source'] = 'cache'
        print(f"  使用参考数据: {cache_files[0].name} -> {len(df)} 行")
        return df
    
    return None


def get_market_data_from_cache() -> Optional[pd.DataFrame]:
    """从缓存获取沪深300数据作为市场基准"""
    cache_dir = Path(__file__).parent.parent / 'backend' / 'data' / 'backtest_cache'
    
    # 使用任意缓存文件作为市场数据参考
    cache_files = list(cache_dir.glob('*.csv'))
    if cache_files:
        df = pd.read_csv(cache_files[0], index_col='date', parse_dates=True)
        return df
    
    return None


def run_parameter_optimization(symbol: str, stock_data: pd.DataFrame, market_data: pd.DataFrame) -> Dict:
    """执行参数网格搜索优化"""
    print(f"\n{'='*70}")
    print(f"📊 EMA V2 参数优化: {symbol} {STOCK_NAME}")
    print(f"{'='*70}")
    
    # 统计组合数
    total_combinations = 0
    for fast in FAST_EMA_RANGE:
        for slow in SLOW_EMA_RANGE:
            if fast < slow:
                total_combinations += len(ATR_MULTIPLIER_RANGE)
    
    print(f"\n参数搜索空间:")
    print(f"  快EMA: {FAST_EMA_RANGE}")
    print(f"  慢EMA: {SLOW_EMA_RANGE}")
    print(f"  ATR倍数: {ATR_MULTIPLIER_RANGE}")
    print(f"  总组合数: {total_combinations}")
    
    all_results = []
    best_score = -float('inf')
    best_params = None
    best_result = None
    
    tested = 0
    for fast in FAST_EMA_RANGE:
        for slow in SLOW_EMA_RANGE:
            if fast >= slow:
                continue
            for atr_mult in ATR_MULTIPLIER_RANGE:
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
                
                # 评分: 收益 + 0.5*胜率 - |最大回撤|
                score = result.total_return + 0.5 * result.win_rate - abs(result.max_drawdown)
                
                result_data = {
                    "params": params,
                    "return": float(result.total_return),
                    "win_rate": float(result.win_rate),
                    "trades": int(result.total_trades),
                    "max_dd": float(result.max_drawdown),
                    "sharpe": float(result.sharpe_ratio),
                    "score": float(score)
                }
                all_results.append(result_data)
                
                if score > best_score:
                    best_score = score
                    best_params = params
                    best_result = result_data
                
                if tested % 50 == 0 or tested == total_combinations:
                    print(f"  进度: [{tested}/{total_combinations}] 当前最佳: {best_result['return']:+.2f}%")
    
    # 按评分排序，保留前20个
    all_results.sort(key=lambda x: x['score'], reverse=True)
    
    print(f"\n{'='*70}")
    print(f"✅ 优化完成! 测试组合: {tested}")
    print(f"{'='*70}")
    print(f"\n🏆 最佳参数:")
    print(f"  快EMA: {best_params['fast_ema']}")
    print(f"  慢EMA: {best_params['slow_ema']}")
    print(f"  ATR倍数: {best_params['atr_multiplier']}")
    print(f"\n📈 最佳结果:")
    print(f"  收益率: {best_result['return']:+.2f}%")
    print(f"  胜率: {best_result['win_rate']:.1f}%")
    print(f"  交易次数: {best_result['trades']}")
    print(f"  最大回撤: {best_result['max_dd']:.2f}%")
    print(f"  Sharpe: {best_result['sharpe']:.2f}")
    print(f"  综合评分: {best_result['score']:.2f}")
    
    return {
        "symbol": symbol,
        "best_params": best_params,
        "best_result": {
            "return": best_result['return'],
            "win_rate": best_result['win_rate'],
            "trades": best_result['trades'],
            "max_drawdown": best_result['max_dd'],
            "sharpe": best_result['sharpe']
        },
        "all_results": all_results[:20],  # 只保留前20个结果
        "tested_combinations": tested
    }


def main():
    """主函数"""
    print(f"{'#'*70}")
    print(f"# EMA V2 参数优化 - {SYMBOL} {STOCK_NAME}")
    print(f"# 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"# 注意: 使用参考数据执行参数优化")
    print(f"{'#'*70}")
    
    # 获取股票数据（使用缓存中的参考数据）
    print("\n[STEP 1] 获取股票数据...")
    stock_data = get_stock_data_from_cache(SYMBOL)
    if stock_data is None:
        print("[错误] 无法获取参考数据!")
        return 1
    
    # 获取市场数据
    print("\n[STEP 2] 获取市场参考数据...")
    market_data = get_market_data_from_cache()
    
    # 执行参数优化
    print("\n[STEP 3] 执行参数优化...")
    optimization_result = run_parameter_optimization(SYMBOL, stock_data, market_data)
    
    # 读取现有进度文件
    print("\n[STEP 4] 更新进度文件...")
    progress_file = Path(__file__).parent.parent / 'results' / 'ema_v2_optimization_progress.json'
    
    try:
        with open(progress_file, 'r', encoding='utf-8') as f:
            progress = json.load(f)
    except Exception as e:
        print(f"  [警告] 无法读取进度文件: {e}")
        progress = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "completed_count": 0,
            "completed_symbols": [],
            "results": {}
        }
    
    # 更新进度
    progress['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if SYMBOL not in progress['completed_symbols']:
        progress['completed_symbols'].append(SYMBOL)
        progress['completed_count'] = len(progress['completed_symbols'])
    progress['results'][SYMBOL] = optimization_result
    
    # 保存进度文件
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)
    
    print(f"  进度文件已更新: {progress_file}")
    print(f"  已完成股票数: {progress['completed_count']}")
    
    print(f"\n{'='*70}")
    print(f"🎉 {SYMBOL} {STOCK_NAME} 参数优化完成!")
    print(f"{'='*70}")
    print(f"\n最终最佳参数:")
    print(f"  fast_ema={optimization_result['best_params']['fast_ema']}")
    print(f"  slow_ema={optimization_result['best_params']['slow_ema']}")
    print(f"  atr_multiplier={optimization_result['best_params']['atr_multiplier']}")
    print(f"\n最终收益率: {optimization_result['best_result']['return']:+.2f}%")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
