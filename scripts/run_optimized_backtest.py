#!/usr/bin/env python3
"""
EMA V2.1 优化参数回测执行器
使用已优化的参数逐个股票执行回测
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
from ema_v2 import EMAV2Strategy, BacktestResult

# 优化后的参数配置 (23只股票)
OPTIMIZED_PARAMS = {
    '000001': {'name': '平安银行', 'fast_ema': 7, 'slow_ema': 20, 'atr_period': 14, 'atr_multiplier': 1.0, 'market_filter': True},
    '000333': {'name': '美的集团', 'fast_ema': 3, 'slow_ema': 40, 'atr_period': 14, 'atr_multiplier': 1.5, 'market_filter': True},
    '000568': {'name': '泸州老窖', 'fast_ema': 15, 'slow_ema': 40, 'atr_period': 14, 'atr_multiplier': 2.5, 'market_filter': True},
    '000651': {'name': '格力电器', 'fast_ema': 10, 'slow_ema': 30, 'atr_period': 14, 'atr_multiplier': 1.5, 'market_filter': True},
    '000858': {'name': '五粮液', 'fast_ema': 8, 'slow_ema': 35, 'atr_period': 14, 'atr_multiplier': 2.5, 'market_filter': True},
    '002415': {'name': '海康威视', 'fast_ema': 12, 'slow_ema': 15, 'atr_period': 14, 'atr_multiplier': 3.0, 'market_filter': True},
    '002460': {'name': '赣锋锂业', 'fast_ema': 3, 'slow_ema': 35, 'atr_period': 14, 'atr_multiplier': 1.5, 'market_filter': True},
    '002594': {'name': '比亚迪', 'fast_ema': 7, 'slow_ema': 30, 'atr_period': 14, 'atr_multiplier': 2.5, 'market_filter': True},
    '002714': {'name': '牧原股份', 'fast_ema': 12, 'slow_ema': 20, 'atr_period': 14, 'atr_multiplier': 2.0, 'market_filter': True},
    '300014': {'name': '亿纬锂能', 'fast_ema': 5, 'slow_ema': 40, 'atr_period': 14, 'atr_multiplier': 2.0, 'market_filter': True},
    '300033': {'name': '同花顺', 'fast_ema': 15, 'slow_ema': 35, 'atr_period': 14, 'atr_multiplier': 1.0, 'market_filter': True},
    '300124': {'name': '汇川技术', 'fast_ema': 3, 'slow_ema': 40, 'atr_period': 14, 'atr_multiplier': 1.5, 'market_filter': True},
    '300750': {'name': '宁德时代', 'fast_ema': 3, 'slow_ema': 35, 'atr_period': 14, 'atr_multiplier': 2.0, 'market_filter': True},
    '600036': {'name': '招商银行', 'fast_ema': 7, 'slow_ema': 25, 'atr_period': 14, 'atr_multiplier': 1.0, 'market_filter': True},
    '600276': {'name': '恒瑞医药', 'fast_ema': 7, 'slow_ema': 40, 'atr_period': 14, 'atr_multiplier': 1.5, 'market_filter': True},
    '600519': {'name': '贵州茅台', 'fast_ema': 15, 'slow_ema': 40, 'atr_period': 14, 'atr_multiplier': 1.5, 'market_filter': True},
    '600887': {'name': '伊利股份', 'fast_ema': 15, 'slow_ema': 40, 'atr_period': 14, 'atr_multiplier': 3.0, 'market_filter': True},  # 优化后: +12.86% (原-3.76%)
    '600900': {'name': '长江电力', 'fast_ema': 12, 'slow_ema': 20, 'atr_period': 14, 'atr_multiplier': 1.0, 'market_filter': True},
    '601012': {'name': '隆基绿能', 'fast_ema': 12, 'slow_ema': 18, 'atr_period': 14, 'atr_multiplier': 1.5, 'market_filter': True},
    '601288': {'name': '农业银行', 'fast_ema': 12, 'slow_ema': 30, 'atr_period': 14, 'atr_multiplier': 1.0, 'market_filter': True},
    '601318': {'name': '中国平安', 'fast_ema': 10, 'slow_ema': 50, 'atr_period': 14, 'atr_multiplier': 1.5, 'market_filter': True, 'note': '加长周期版本: EMA10/50，回测收益+55.14% (vs原参数-1.65%)'},
    # '601398': {'name': '工商银行', 'fast_ema': 10, 'slow_ema': 35, 'atr_period': 14, 'atr_multiplier': 1.0, 'market_filter': True},  # REMOVED: 低波动银行股不适合EMA趋势策略
    '601888': {'name': '中国中免', 'fast_ema': 15, 'slow_ema': 40, 'atr_period': 14, 'atr_multiplier': 2.0, 'market_filter': True},
}


def load_stock_data(symbol: str, data_dir: Path) -> Optional[pd.DataFrame]:
    """从本地CSV加载股票数据"""
    csv_path = data_dir / f"{symbol}.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
        # 确保列名统一
        df.columns = [c.lower() for c in df.columns]
        if 'close' not in df.columns and '收盘价' in df.columns:
            df.rename(columns={'收盘价': 'close', '开盘价': 'open', '最高价': 'high', '最低价': 'low', '成交量': 'volume'}, inplace=True)
        df.attrs['symbol'] = symbol
        return df
    return None


def load_market_data(data_dir: Path) -> Optional[pd.DataFrame]:
    """加载沪深300指数数据"""
    return load_stock_data('000300', data_dir)


def run_single_backtest(symbol: str, data_dir: Path, output_dir: Path) -> Optional[Dict]:
    """对单只股票执行回测"""
    if symbol not in OPTIMIZED_PARAMS:
        print(f"[ERROR] 未找到 {symbol} 的优化参数")
        return None
    
    params = OPTIMIZED_PARAMS[symbol]
    stock_data = load_stock_data(symbol, data_dir)
    
    if stock_data is None:
        print(f"[ERROR] 未找到 {symbol} 的数据文件")
        return None
    
    market_data = load_market_data(data_dir)
    
    print(f"\n{'='*60}")
    print(f"开始回测: {symbol} - {params['name']}")
    print(f"{'='*60}")
    print(f"数据时间范围: {stock_data.index[0].strftime('%Y-%m-%d')} ~ {stock_data.index[-1].strftime('%Y-%m-%d')}")
    print(f"数据条数: {len(stock_data)}")
    print(f"策略参数: 快EMA={params['fast_ema']}, 慢EMA={params['slow_ema']}, ATR倍数={params['atr_multiplier']}")
    
    # 创建策略并运行回测
    strategy = EMAV2Strategy(params)
    result = strategy.run_backtest(stock_data, market_data)
    
    # 打印结果
    print(f"\n📊 回测结果:")
    print(f"  总收益率: {result.total_return:+.2f}%")
    print(f"  胜率: {result.win_rate:.1f}%")
    print(f"  交易次数: {result.total_trades}")
    print(f"  最大回撤: {result.max_drawdown:.2f}%")
    print(f"  Sharpe比率: {result.sharpe_ratio:.2f}")
    
    # 保存详细结果
    result_dict = {
        'symbol': symbol,
        'name': params['name'],
        'params': params,
        'total_return': result.total_return,
        'win_rate': result.win_rate,
        'total_trades': result.total_trades,
        'max_drawdown': result.max_drawdown,
        'sharpe_ratio': result.sharpe_ratio,
        'data_start': stock_data.index[0].strftime('%Y-%m-%d'),
        'data_end': stock_data.index[-1].strftime('%Y-%m-%d'),
        'data_points': len(stock_data),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # 保存交易记录
    trades_file = output_dir / f"{symbol}_trades.json"
    with open(trades_file, 'w', encoding='utf-8') as f:
        json.dump(result.trades, f, ensure_ascii=False, indent=2, default=str)
    
    return result_dict


def run_batch_backtest(symbols: List[str], data_dir: Path, output_dir: Path) -> List[Dict]:
    """批量回测多只股票"""
    results = []
    
    for symbol in symbols:
        result = run_single_backtest(symbol, data_dir, output_dir)
        if result:
            results.append(result)
    
    return results


def generate_summary_report(results: List[Dict], output_dir: Path):
    """生成汇总报告"""
    if not results:
        print("[WARNING] 没有结果可生成报告")
        return
    
    report_file = output_dir / f"backtest_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # 计算统计指标
    returns = [r['total_return'] for r in results]
    win_rates = [r['win_rate'] for r in results]
    sharpes = [r['sharpe_ratio'] for r in results]
    
    summary = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_stocks': len(results),
        'avg_return': np.mean(returns),
        'median_return': np.median(returns),
        'best_return': max(returns),
        'worst_return': min(returns),
        'positive_count': sum(1 for r in returns if r > 0),
        'avg_win_rate': np.mean(win_rates),
        'avg_sharpe': np.mean(sharpes),
        'results': results
    }
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*60}")
    print(f"📋 汇总报告已保存: {report_file}")
    print(f"{'='*60}")
    print(f"回测股票数: {summary['total_stocks']}")
    print(f"平均收益: {summary['avg_return']:+.2f}%")
    print(f"正收益股票: {summary['positive_count']}/{summary['total_stocks']}")
    print(f"最佳收益: {summary['best_return']:+.2f}%")
    print(f"最差收益: {summary['worst_return']:+.2f}%")
    print(f"平均胜率: {summary['avg_win_rate']:.1f}%")
    print(f"平均Sharpe: {summary['avg_sharpe']:.2f}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='EMA V2.1 优化参数回测')
    parser.add_argument('--symbol', '-s', type=str, help='单个股票代码')
    parser.add_argument('--batch', '-b', action='store_true', help='批量回测所有股票')
    parser.add_argument('--list', '-l', type=str, help='股票列表 (逗号分隔)')
    
    args = parser.parse_args()
    
    # 路径设置
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / 'data'
    output_dir = base_dir / 'results' / 'individual_backtests'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if args.symbol:
        # 单只股票回测
        result = run_single_backtest(args.symbol, data_dir, output_dir)
        if result:
            generate_summary_report([result], output_dir)
    
    elif args.batch:
        # 批量回测所有股票
        symbols = list(OPTIMIZED_PARAMS.keys())
        print(f"开始批量回测 {len(symbols)} 只股票...")
        results = run_batch_backtest(symbols, data_dir, output_dir)
        generate_summary_report(results, output_dir)
    
    elif args.list:
        # 自定义股票列表
        symbols = [s.strip() for s in args.list.split(',')]
        print(f"开始回测 {len(symbols)} 只股票: {symbols}")
        results = run_batch_backtest(symbols, data_dir, output_dir)
        generate_summary_report(results, output_dir)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
