#!/usr/bin/env python3
"""
EMA V2.1 真实数据参数优化脚本
针对表现不佳的中波动股票进行参数优化
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
            # 自动检测数据目录路径
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
                # 尝试大小写变体
                for alt_col in df.columns:
                    if alt_col.lower() == col:
                        df.rename(columns={alt_col: col}, inplace=True)
                        break
        
        return df
    
    def get_market_data(self) -> pd.DataFrame:
        """获取沪深300大盘数据"""
        return self.get_stock_data('000300')


def grid_search_optimization(symbol: str, data_source: RealDataSource,
                             fast_range: List[int] = None,
                             slow_range: List[int] = None,
                             atr_range: List[float] = None) -> Dict:
    """网格搜索参数优化"""
    
    # 扩展参数范围
    if fast_range is None:
        fast_range = [3, 5, 7, 8, 10, 12, 15]
    if slow_range is None:
        slow_range = [15, 18, 20, 25, 30, 35, 40]
    if atr_range is None:
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
    
    # 排序显示前10
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
        print(f"   已完成: {', '.join(data.get('completed_symbols', []))}")
        return data.get('results', {})
    except Exception as e:
        print(f"⚠️ 读取进度文件失败: {e}")
        return {}


def optimize_all_stocks():
    """优化所有20只股票"""
    
    print(f"\n{'#'*70}")
    print(f"# EMA V2.1 全股票参数优化 (真实数据)")
    print(f"# 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*70}")
    
    data_source = RealDataSource()
    
    # 20只待优化股票
    symbols = {
        '000001': '平安银行',
        '000333': '美的集团',
        '000568': '泸州老窖',
        '000651': '格力电器',
        '000858': '五粮液',
        '002415': '海康威视',
        '002460': '赣锋锂业',
        '002594': '比亚迪',
        '300014': '亿纬锂能',
        '300124': '汇川技术',
        '300750': '宁德时代',
        '600036': '招商银行',
        '600276': '恒瑞医药',
        '600519': '贵州茅台',
        '600887': '伊利股份',
        '600900': '长江电力',
        '601288': '农业银行',
        '601318': '中国平安',
        '601398': '工商银行',
        '601888': '中国中免'
    }
    
    # 设置进度文件路径
    output_dir = Path(__file__).parent.parent / 'results'
    output_dir.mkdir(exist_ok=True)
    progress_file = output_dir / 'ema_v2_optimization_progress.json'
    
    # 尝试从进度文件恢复
    all_results = load_progress(progress_file)
    
    remaining_symbols = {k: v for k, v in symbols.items() if k not in all_results}
    
    if remaining_symbols:
        print(f"\n🎯 剩余待优化: {len(remaining_symbols)}只股票")
        print(f"   列表: {', '.join(remaining_symbols.keys())}")
    else:
        print(f"\n✅ 所有股票已优化完成！")
    
    for symbol, name in remaining_symbols.items():
        print(f"\n\n{'='*70}")
        print(f"优化股票: {symbol} {name}")
        print(f"进度: {len(all_results)+1}/{len(symbols)}")
        print(f"{'='*70}")
        
        try:
            result = grid_search_optimization(symbol, data_source)
            all_results[symbol] = result
            
            # 每完成一只就立即保存进度
            save_progress(all_results, progress_file)
            print(f"  ✅ {symbol} {name} 优化完成并保存")
            
        except Exception as e:
            print(f"❌ 优化失败: {symbol} - {e}")
            # 即使失败也保存当前进度
            save_progress(all_results, progress_file)
            continue
    
    # 汇总报告
    print(f"\n\n{'='*70}")
    print(f"优化汇总报告 - 共完成 {len(all_results)}/{len(symbols)} 只股票")
    print(f"{'='*70}")
    
    print(f"\n| 代码 | 名称 | 优化收益 | 胜率 | 交易数 | 最大回撤 | Sharpe | 最佳参数 |")
    print(f"|:---:|:---:|------:|-----:|-----:|--------:|------:|:--------|")
    
    for symbol, name in symbols.items():
        if symbol in all_results:
            r = all_results[symbol]['best_result']
            bp = all_results[symbol]['best_params']
            param_str = f"EMA{bp['fast_ema']}/{bp['slow_ema']},ATR×{bp['atr_multiplier']}"
            
            print(f"| {symbol} | {name} | {r['return']:+.2f}% | {r['win_rate']:.1f}% | "
                  f"{r['trades']} | {r['max_drawdown']:.2f}% | {r['sharpe']:.2f} | {param_str} |")
    
    # 保存最终结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    result_file = output_dir / f'param_optimization_full_{timestamp}.json'
    
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 最终结果已保存: {result_file}")
    print(f"✅ 进度文件: {progress_file}")
    
    # 生成Markdown报告
    report_file = output_dir / f'PARAM_OPTIMIZATION_REPORT_{timestamp}.md'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"# EMA V2.1 参数优化报告\n\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"优化股票数量: {len(all_results)}/{len(symbols)}\n\n")
        f.write(f"## 优化结果汇总\n\n")
        f.write(f"| 代码 | 名称 | 优化收益 | 胜率 | 交易数 | 最大回撤 | Sharpe | 最佳参数 |\n")
        f.write(f"|:---:|:---:|------:|-----:|-----:|--------:|------:|:--------|\n")
        
        for symbol, name in symbols.items():
            if symbol in all_results:
                r = all_results[symbol]['best_result']
                bp = all_results[symbol]['best_params']
                param_str = f"EMA{bp['fast_ema']}/{bp['slow_ema']},ATR×{bp['atr_multiplier']}"
                
                f.write(f"| {symbol} | {name} | {r['return']:+.2f}% | {r['win_rate']:.1f}% | "
                      f"{r['trades']} | {r['max_drawdown']:.2f}% | {r['sharpe']:.2f} | {param_str} |\n")
        
        # 添加详细参数配置（可直接复制到配置文件）
        f.write(f"\n\n## 最佳参数配置 (可直接使用)\n\n")
        f.write(f"```python\n")
        f.write(f"OPTIMIZED_PARAMS = {{\n")
        for symbol, name in symbols.items():
            if symbol in all_results:
                bp = all_results[symbol]['best_params']
                f.write(f"    '{symbol}': {{\n")
                f.write(f"        'name': '{name}',\n")
                f.write(f"        'fast_ema': {bp['fast_ema']},\n")
                f.write(f"        'slow_ema': {bp['slow_ema']},\n")
                f.write(f"        'atr_period': {bp['atr_period']},\n")
                f.write(f"        'atr_multiplier': {bp['atr_multiplier']},\n")
                f.write(f"        'market_filter': {bp['market_filter']}\n")
                f.write(f"    }},\n")
        f.write(f"}}\n")
        f.write(f"```\n")
    
    print(f"✅ 报告已保存: {report_file}")
    
    return all_results


if __name__ == '__main__':
    optimize_all_stocks()
