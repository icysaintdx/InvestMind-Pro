#!/usr/bin/env python3
"""
负收益股票新参数回测验证
测试伊利股份、中国平安、工商银行的新参数效果
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

# 负收益股票新参数配置
NEW_PARAMS = {
    '600887': {
        'name': '伊利股份', 
        'old_params': {'fast_ema': 3, 'slow_ema': 35, 'atr_multiplier': 2.0},
        'new_params': {'fast_ema': 15, 'slow_ema': 40, 'atr_multiplier': 3.0},
    },
    '601318': {
        'name': '中国平安', 
        'old_params': {'fast_ema': 7, 'slow_ema': 20, 'atr_multiplier': 1.0},
        'new_params': {'fast_ema': 12, 'slow_ema': 35, 'atr_multiplier': 2.5},
    },
    '601398': {
        'name': '工商银行', 
        'old_params': {'fast_ema': 10, 'slow_ema': 35, 'atr_multiplier': 1.0},
        'new_params': {'fast_ema': 20, 'slow_ema': 50, 'atr_multiplier': 2.0},  # 极长周期
    },
}


def load_stock_data(symbol: str, data_dir: Path) -> Optional[pd.DataFrame]:
    """从本地CSV加载股票数据"""
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


def run_backtest_with_params(symbol: str, params: Dict, data_dir: Path) -> Optional[Dict]:
    """使用指定参数运行回测"""
    stock_data = load_stock_data(symbol, data_dir)
    if stock_data is None:
        return None
    
    market_data = load_market_data(data_dir)
    
    # 构建完整参数字典
    full_params = {
        'name': NEW_PARAMS[symbol]['name'],
        'atr_period': 14,
        'market_filter': True,
        **params
    }
    
    # 创建策略并运行回测
    strategy = EMAV2Strategy(full_params)
    result = strategy.run_backtest(stock_data, market_data)
    
    return {
        'symbol': symbol,
        'name': full_params['name'],
        'params': params,
        'total_return': result.total_return,
        'win_rate': result.win_rate,
        'total_trades': result.total_trades,
        'max_drawdown': result.max_drawdown,
        'sharpe_ratio': result.sharpe_ratio,
        'trades': result.trades
    }


def compare_params(symbol: str, data_dir: Path) -> Dict:
    """对比新旧参数效果"""
    config = NEW_PARAMS[symbol]
    print(f"\n{'='*60}")
    print(f"股票: {symbol} - {config['name']}")
    print(f"{'='*60}")
    
    # 旧参数回测
    print("\n📊 旧参数回测:")
    print(f"   参数: EMA{config['old_params']['fast_ema']}/{config['old_params']['slow_ema']}, ATR×{config['old_params']['atr_multiplier']}")
    old_result = run_backtest_with_params(symbol, config['old_params'], data_dir)
    if old_result:
        print(f"   收益率: {old_result['total_return']:+.2f}% | 胜率: {old_result['win_rate']:.1f}% | 交易次数: {old_result['total_trades']}")
    
    # 新参数回测
    print("\n📈 新参数回测:")
    print(f"   参数: EMA{config['new_params']['fast_ema']}/{config['new_params']['slow_ema']}, ATR×{config['new_params']['atr_multiplier']}")
    new_result = run_backtest_with_params(symbol, config['new_params'], data_dir)
    if new_result:
        print(f"   收益率: {new_result['total_return']:+.2f}% | 胜率: {new_result['win_rate']:.1f}% | 交易次数: {new_result['total_trades']}")
    
    # 对比结果
    if old_result and new_result:
        improvement = new_result['total_return'] - old_result['total_return']
        trade_reduction = old_result['total_trades'] - new_result['total_trades']
        print(f"\n🎯 对比结果:")
        print(f"   收益改善: {improvement:+.2f}%")
        print(f"   交易次数减少: {trade_reduction}次 ({trade_reduction/old_result['total_trades']*100:.1f}%)")
        
        return {
            'symbol': symbol,
            'name': config['name'],
            'old': old_result,
            'new': new_result,
            'improvement': improvement,
            'trade_reduction': trade_reduction
        }
    
    return None


def generate_comparison_report(results: List[Dict], output_file: Path):
    """生成对比报告"""
    report = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'summary': {
            'stocks_tested': len(results),
            'avg_improvement': np.mean([r['improvement'] for r in results]),
            'positive_improvement': sum(1 for r in results if r['improvement'] > 0),
        },
        'details': results
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n{'='*60}")
    print(f"📋 对比报告已保存: {output_file}")
    print(f"{'='*60}")
    print(f"测试股票数: {report['summary']['stocks_tested']}")
    print(f"平均改善: {report['summary']['avg_improvement']:+.2f}%")
    print(f"正向改善: {report['summary']['positive_improvement']}/{report['summary']['stocks_tested']}")


def main():
    """主函数"""
    # 路径设置
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / 'data'
    output_dir = base_dir / 'results' / 'individual_backtests'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("="*60)
    print("负收益股票新参数回测验证")
    print("="*60)
    
    results = []
    for symbol in NEW_PARAMS.keys():
        result = compare_params(symbol, data_dir)
        if result:
            results.append(result)
    
    # 生成报告
    report_file = output_dir / f"param_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    generate_comparison_report(results, report_file)
    
    # 打印摘要
    print(f"\n📊 最终摘要:")
    for r in results:
        status = "✅ 改善" if r['improvement'] > 0 else "❌ 恶化"
        print(f"   {r['symbol']} {r['name']}: {r['old']['total_return']:+.2f}% → {r['new']['total_return']:+.2f}% ({r['improvement']:+.2f}%) {status}")


if __name__ == '__main__':
    main()
