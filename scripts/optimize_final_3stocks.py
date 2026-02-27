#!/usr/bin/env python3
"""
EMA V2.1 最后3只股票参数优化
股票: 002714(牧原股份), 300033(同花顺), 601012(隆基绿能)
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


class RealDataSource:
    """真实CSV数据源"""
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            script_dir = Path(__file__).parent
            project_dir = script_dir.parent
            data_dir = project_dir / "data"
        self.data_dir = Path(data_dir)
    
    def get_stock_data(self, symbol: str) -> pd.DataFrame:
        """获取股票数据"""
        csv_path = self.data_dir / f"{symbol}.csv"
        if not csv_path.exists():
            raise FileNotFoundError(f"数据文件不存在: {csv_path}")
        
        df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
        df.attrs['symbol'] = symbol
        
        # 列名标准化
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col not in df.columns:
                for alt_col in df.columns:
                    if alt_col.lower() == col:
                        df.rename(columns={alt_col: col}, inplace=True)
                        break
        
        return df
    
    def get_market_data(self) -> pd.DataFrame:
        """获取沪深300大盘数据"""
        return self.get_stock_data('000300')


def grid_search_optimization(symbol: str, data_source: RealDataSource) -> Dict:
    """网格搜索参数优化 - 288种组合"""
    
    # 标准参数范围 - 共288种组合
    fast_range = [3, 5, 7, 8, 10, 12, 15]
    slow_range = [15, 18, 20, 25, 30, 35, 40]
    atr_range = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0]
    
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
    
    total_combinations = sum(1 for f in fast_range for s in slow_range if f < s) * len(atr_range)
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
                
                try:
                    strategy = EMAV2Strategy(params)
                    result = strategy.run_backtest(stock_data, market_data)
                    
                    # 综合评分: 收益*1.0 + 胜率*0.5 - 回撤*0.8 + 交易次数*0.02
                    score = (result.total_return * 1.0 + 
                            result.win_rate * 0.5 - 
                            abs(result.max_drawdown) * 0.8 +
                            min(result.total_trades, 50) * 0.02)
                    
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
                    
                    if tested % 50 == 0:
                        print(f"  进度: {tested}/{total_combinations} ({100*tested/total_combinations:.1f}%) - 当前最佳收益: {best_result.total_return:.2f}%")
                
                except Exception as e:
                    print(f"  错误 {symbol} EMA{fast}/{slow} ATR×{atr_mult}: {e}")
    
    # 排序显示前20
    results_sorted = sorted(results, key=lambda x: x['score'], reverse=True)
    
    print(f"\n🏆 TOP 10 参数组合:")
    print(f"{'排名':<4} {'快EMA':<5} {'慢EMA':<5} {'ATR':<5} {'收益%':<10} {'胜率%':<6} {'交易':<5} {'回撤%':<8} {'Sharpe':<7} {'评分':<8}")
    print("-" * 80)
    
    for i, r in enumerate(results_sorted[:10], 1):
        p = r['params']
        print(f"{i:<4} {p['fast_ema']:<5} {p['slow_ema']:<5} {p['atr_multiplier']:<5.1f} "
              f"{r['return']:<10.2f} {r['win_rate']:<6.1f} {r['trades']:<5} "
              f"{r['max_dd']:<8.2f} {r['sharpe']:<7.2f} {r['score']:<8.2f}")
    
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
        'all_results': results_sorted[:20],
        'tested_combinations': tested
    }


def save_progress(all_results: dict, progress_file: Path):
    """保存进度到JSON文件"""
    progress_data = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'completed_count': len(all_results),
        'completed_symbols': list(all_results.keys()),
        'results': all_results
    }
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(progress_data, f, ensure_ascii=False, indent=2)
    print(f"  💾 进度已保存: {len(all_results)}只股票完成")


def load_progress(progress_file: Path) -> dict:
    """从进度文件加载已完成的结果"""
    if not progress_file.exists():
        return {}
    try:
        with open(progress_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"📂 从进度文件恢复: {data.get('completed_count', 0)}只股票已完成")
        return data.get('results', {})
    except Exception as e:
        print(f"⚠️ 读取进度文件失败: {e}")
        return {}


def optimize_final_3_stocks():
    """优化最后3只股票"""
    
    print(f"\n{'#'*70}")
    print(f"# EMA V2.1 最后3只股票参数优化")
    print(f"# 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*70}")
    
    data_source = RealDataSource()
    
    # 最后3只股票
    symbols = {
        '002714': '牧原股份',
        '300033': '同花顺',
        '601012': '隆基绿能'
    }
    
    # 设置进度文件路径
    output_dir = Path(__file__).parent.parent / 'results'
    output_dir.mkdir(exist_ok=True)
    progress_file = output_dir / 'ema_v2_optimization_progress.json'
    
    # 加载已有进度
    all_results = load_progress(progress_file)
    
    # 检查哪些还需要优化
    remaining_symbols = {k: v for k, v in symbols.items() if k not in all_results}
    
    if remaining_symbols:
        print(f"\n🎯 待优化: {len(remaining_symbols)}只股票")
        print(f"   列表: {', '.join([f'{k}({v})' for k, v in remaining_symbols.items()])}")
    else:
        print(f"\n✅ 所有3只股票已优化完成！")
        return all_results
    
    for symbol, name in remaining_symbols.items():
        print(f"\n\n{'='*70}")
        print(f"优化股票: {symbol} {name}")
        print(f"{'='*70}")
        
        try:
            result = grid_search_optimization(symbol, data_source)
            all_results[symbol] = result
            
            # 每完成一只就立即保存进度
            save_progress(all_results, progress_file)
            print(f"  ✅ {symbol} {name} 优化完成并保存")
            
        except Exception as e:
            print(f"❌ 优化失败: {symbol} - {e}")
            save_progress(all_results, progress_file)
            continue
    
    return all_results


if __name__ == '__main__':
    optimize_final_3_stocks()
    print("\n✅ 任务完成!")
