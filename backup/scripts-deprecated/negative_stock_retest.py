#!/usr/bin/env python3
"""
负收益股票参数优化回测验证脚本
为5只负收益股票使用优化参数进行回测
"""

import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# 添加项目路径
sys.path.insert(0, '/home/icysaintdx/.openclaw/workspace/InvestMindPro/strategies')
sys.path.insert(0, '/home/icysaintdx/.openclaw/workspace/InvestMindPro/data')

from ema_v2 import EMAV2Strategy, BacktestResult

# 负收益股票优化参数配置
OPTIMIZED_STOCKS = {
    '603288': {
        'name': '海天味业',
        'category': '消费股',
        'old_params': {'fast_ema': 5, 'slow_ema': 20, 'atr_period': 14, 'atr_multiplier': 2.0, 'market_filter': True},
        'new_params': {'fast_ema': 10, 'slow_ema': 40, 'atr_period': 14, 'atr_multiplier': 2.0, 'market_filter': True},
        'expected_return': 27.27,
    },
    '002714': {
        'name': '牧原股份',
        'category': '猪周期股',
        'old_params': {'fast_ema': 5, 'slow_ema': 20, 'atr_period': 14, 'atr_multiplier': 2.0, 'market_filter': True},
        'new_params': {'fast_ema': 3, 'slow_ema': 30, 'atr_period': 14, 'atr_multiplier': 2.5, 'market_filter': True},
        'expected_return': None,
    },
    '688981': {
        'name': '中芯国际',
        'category': '科技股',
        'old_params': {'fast_ema': 5, 'slow_ema': 20, 'atr_period': 14, 'atr_multiplier': 2.0, 'market_filter': True},
        'new_params': {'fast_ema': 5, 'slow_ema': 35, 'atr_period': 14, 'atr_multiplier': 3.0, 'market_filter': True},
        'expected_return': None,
    },
    '000651': {
        'name': '格力电器',
        'category': '家电股',
        'old_params': {'fast_ema': 10, 'slow_ema': 30, 'atr_period': 14, 'atr_multiplier': 1.5, 'market_filter': True},
        'new_params': {'fast_ema': 15, 'slow_ema': 60, 'atr_period': 14, 'atr_multiplier': 2.0, 'market_filter': True},
        'expected_return': None,
    },
    '300033': {
        'name': '同花顺',
        'category': '券商股',
        'old_params': {'fast_ema': 5, 'slow_ema': 20, 'atr_period': 14, 'atr_multiplier': 2.0, 'market_filter': True},
        'new_params': {'fast_ema': 3, 'slow_ema': 15, 'atr_period': 14, 'atr_multiplier': 2.5, 'market_filter': True},
        'expected_return': None,
    }
}

# 回测区间
START_DATE = '2020-01-01'
END_DATE = '2026-02-27'


def load_stock_data(symbol: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """
    从本地CSV或生成模拟数据加载股票数据
    """
    data_dir = Path('/home/icysaintdx/.openclaw/workspace/InvestMindPro/data')
    csv_path = data_dir / f"{symbol}.csv"
    
    if csv_path.exists():
        df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
        # 筛选日期范围
        if start_date:
            df = df[df.index >= start_date]
        if end_date:
            df = df[df.index <= end_date]
        df.attrs['symbol'] = symbol
        return df
    else:
        print(f"[WARNING] 未找到 {symbol} 的本地数据，生成模拟数据")
        return generate_sample_data(symbol, start_date, end_date)


def generate_sample_data(symbol: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """生成模拟股票数据用于回测"""
    np.random.seed(int(symbol))
    
    # 设置日期范围
    if start_date is None:
        start = pd.Timestamp('2020-01-01')
    else:
        start = pd.Timestamp(start_date)
    
    if end_date is None:
        end = pd.Timestamp.now()
    else:
        end = pd.Timestamp(end_date)
    
    # 生成交易日历 (约252个交易日/年)
    days = (end - start).days
    n_periods = int(days * 252 / 365)
    
    dates = pd.date_range(start=start, periods=n_periods, freq='B')
    
    # 生成价格序列 - 根据股票特性调整
    base_returns = 0.0003  # 基础日收益率
    volatility = 0.025     # 基础波动率
    
    # 根据股票类型调整参数
    if symbol in ['300033', '688981']:  # 科技股/券商股 - 高波动
        volatility = 0.035
    elif symbol in ['002714']:  # 周期股
        base_returns = 0.0001
        volatility = 0.03
    elif symbol in ['603288', '000651']:  # 消费/家电 - 低波动
        volatility = 0.02
    
    returns = np.random.normal(base_returns, volatility, len(dates))
    
    # 添加一些趋势特征
    for i in range(1, len(returns)):
        # 动量效应
        returns[i] += returns[i-1] * 0.1
    
    price = 100 * np.exp(np.cumsum(returns))
    
    # 生成OHLC数据
    data = pd.DataFrame(index=dates)
    data['close'] = price
    data['high'] = price * (1 + np.abs(np.random.normal(0, volatility * 0.3, len(dates))))
    data['low'] = price * (1 - np.abs(np.random.normal(0, volatility * 0.3, len(dates))))
    data['open'] = price * (1 + np.random.normal(0, volatility * 0.15, len(dates)))
    data['volume'] = np.random.randint(1000000, 50000000, len(dates))
    
    data.attrs['symbol'] = symbol
    return data


def load_market_data(start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """加载或生成沪深300大盘数据"""
    data_dir = Path('/home/icysaintdx/.openclaw/workspace/InvestMindPro/data')
    csv_path = data_dir / "000300.csv"
    
    if csv_path.exists():
        df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
        if start_date:
            df = df[df.index >= start_date]
        if end_date:
            df = df[df.index <= end_date]
        return df
    else:
        return generate_sample_data('000300', start_date, end_date)


def run_backtest_with_params(symbol: str, params: Dict, stock_data: pd.DataFrame, 
                             market_data: pd.DataFrame) -> Dict:
    """使用指定参数运行回测"""
    strategy = EMAV2Strategy(params=params)
    result = strategy.run_backtest(stock_data, market_data, initial_capital=100000.0)
    
    return {
        'symbol': symbol,
        'total_return': result.total_return,
        'win_rate': result.win_rate,
        'total_trades': result.total_trades,
        'max_drawdown': result.max_drawdown,
        'sharpe_ratio': result.sharpe_ratio,
        'params': params,
        'trades': result.trades
    }


def run_negative_stock_retest():
    """
    执行负收益股票优化参数回测验证
    """
    print("="*80)
    print("负收益股票参数优化回测验证")
    print("="*80)
    print(f"回测区间: {START_DATE} 至 {END_DATE}")
    print(f"股票数量: {len(OPTIMIZED_STOCKS)}")
    print("="*80)
    
    results = []
    market_data = load_market_data(START_DATE, END_DATE)
    
    for symbol, config in OPTIMIZED_STOCKS.items():
        print(f"\n\n{'='*60}")
        print(f"处理股票: {symbol} - {config['name']} ({config['category']})")
        print(f"{'='*60}")
        
        # 加载股票数据
        stock_data = load_stock_data(symbol, START_DATE, END_DATE)
        if stock_data is None or len(stock_data) < 100:
            print(f"[ERROR] 数据不足: {symbol}")
            continue
        
        print(f"数据长度: {len(stock_data)} 天")
        print(f"数据起始: {stock_data.index[0].strftime('%Y-%m-%d')}")
        print(f"数据结束: {stock_data.index[-1].strftime('%Y-%m-%d')}")
        
        # 1. 使用原参数回测
        print(f"\n[原参数回测] fast={config['old_params']['fast_ema']}, "
              f"slow={config['old_params']['slow_ema']}, "
              f"atr={config['old_params']['atr_multiplier']}")
        old_result = run_backtest_with_params(symbol, config['old_params'], stock_data, market_data)
        print(f"  收益率: {old_result['total_return']:+.2f}%")
        print(f"  胜率: {old_result['win_rate']:.1f}%")
        print(f"  交易次数: {old_result['total_trades']}")
        print(f"  最大回撤: {old_result['max_drawdown']:.2f}%")
        
        # 2. 使用新参数回测
        print(f"\n[新参数回测] fast={config['new_params']['fast_ema']}, "
              f"slow={config['new_params']['slow_ema']}, "
              f"atr={config['new_params']['atr_multiplier']}")
        new_result = run_backtest_with_params(symbol, config['new_params'], stock_data, market_data)
        print(f"  收益率: {new_result['total_return']:+.2f}%")
        print(f"  胜率: {new_result['win_rate']:.1f}%")
        print(f"  交易次数: {new_result['total_trades']}")
        print(f"  最大回撤: {new_result['max_drawdown']:.2f}%")
        
        # 3. 计算改进
        improvement = new_result['total_return'] - old_result['total_return']
        print(f"\n[参数优化效果]")
        print(f"  收益改进: {improvement:+.2f}%")
        
        if old_result['total_return'] < 0 and new_result['total_return'] > 0:
            status = "✅ 负收益转正收益"
        elif old_result['total_return'] < 0 and new_result['total_return'] < 0:
            status = "⚠️ 仍为负收益"
        elif improvement > 0:
            status = "✅ 收益提升"
        else:
            status = "⚠️ 收益下降"
        print(f"  状态: {status}")
        
        # 保存结果
        result_entry = {
            'symbol': symbol,
            'name': config['name'],
            'category': config['category'],
            'old_return': old_result['total_return'],
            'old_win_rate': old_result['win_rate'],
            'old_trades': old_result['total_trades'],
            'old_max_drawdown': old_result['max_drawdown'],
            'old_sharpe': old_result['sharpe_ratio'],
            'old_params': config['old_params'],
            'new_return': new_result['total_return'],
            'new_win_rate': new_result['win_rate'],
            'new_trades': new_result['total_trades'],
            'new_max_drawdown': new_result['max_drawdown'],
            'new_sharpe': new_result['sharpe_ratio'],
            'new_params': config['new_params'],
            'improvement': improvement,
            'status': status,
            'data_length': len(stock_data)
        }
        results.append(result_entry)
    
    return results


def generate_json_report(results: List[Dict]) -> Dict:
    """生成JSON格式的报告数据"""
    # 统计信息
    total_stocks = len(results)
    positive_count = sum(1 for r in results if r['new_return'] > 0)
    negative_to_positive = sum(1 for r in results 
                               if r['old_return'] < 0 and r['new_return'] > 0)
    improved_count = sum(1 for r in results if r['improvement'] > 0)
    
    avg_old_return = np.mean([r['old_return'] for r in results])
    avg_new_return = np.mean([r['new_return'] for r in results])
    avg_improvement = np.mean([r['improvement'] for r in results])
    
    report = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'backtest_period': {'start': START_DATE, 'end': END_DATE},
        'summary': {
            'total_stocks': total_stocks,
            'positive_count': positive_count,
            'negative_to_positive': negative_to_positive,
            'improved_count': improved_count,
            'avg_old_return': round(avg_old_return, 2),
            'avg_new_return': round(avg_new_return, 2),
            'avg_improvement': round(avg_improvement, 2)
        },
        'stocks': results
    }
    
    return report


def generate_markdown_report(results: List[Dict]) -> str:
    """生成Markdown格式的报告"""
    
    # 统计信息
    total_stocks = len(results)
    positive_count = sum(1 for r in results if r['new_return'] > 0)
    negative_to_positive = sum(1 for r in results 
                               if r['old_return'] < 0 and r['new_return'] > 0)
    improved_count = sum(1 for r in results if r['improvement'] > 0)
    
    avg_old_return = np.mean([r['old_return'] for r in results])
    avg_new_return = np.mean([r['new_return'] for r in results])
    avg_improvement = np.mean([r['improvement'] for r in results])
    
    report = f"""# 负收益股票参数优化回测报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**回测区间**: {START_DATE} 至 {END_DATE}

---

## 执行摘要

| 指标 | 数值 |
|------|------|
| 回测股票数 | {total_stocks} |
| 原参数平均收益 | {avg_old_return:+.2f}% |
| 新参数平均收益 | {avg_new_return:+.2f}% |
| 平均收益改进 | {avg_improvement:+.2f}% |
| 收益转正股票数 | {negative_to_positive}/{total_stocks} |
| 收益提升股票数 | {improved_count}/{total_stocks} |

---

## 股票明细对比

| 代码 | 名称 | 类别 | 原收益 | 新收益 | 改进 | 状态 |
|------|------|------|--------|--------|------|------|
"""
    
    for r in results:
        status_icon = "✅" if r['status'].startswith("✅") else "⚠️"
        report += f"| {r['symbol']} | {r['name']} | {r['category']} | " \
                  f"{r['old_return']:+.2f}% | {r['new_return']:+.2f}% | " \
                  f"{r['improvement']:+.2f}% | {status_icon} |\n"
    
    report += f"""

---

## 详细回测结果

"""
    
    for r in results:
        report += f"""### {r['symbol']} {r['name']}

**股票类别**: {r['category']}

| 指标 | 原参数 | 新参数 | 变化 |
|------|--------|--------|------|
| **总收益率** | {r['old_return']:+.2f}% | {r['new_return']:+.2f}% | {r['improvement']:+.2f}% |
| **胜率** | {r['old_win_rate']:.1f}% | {r['new_win_rate']:.1f}% | {r['new_win_rate']-r['old_win_rate']:+.1f}% |
| **交易次数** | {r['old_trades']} | {r['new_trades']} | {r['new_trades']-r['old_trades']:+d} |
| **最大回撤** | {r['old_max_drawdown']:.2f}% | {r['new_max_drawdown']:.2f}% | {r['new_max_drawdown']-r['old_max_drawdown']:+.2f}% |
| **Sharpe比率** | {r['old_sharpe']:.2f} | {r['new_sharpe']:.2f} | {r['new_sharpe']-r['old_sharpe']:+.2f} |

**参数对比**:
- 原参数: fast_ema={r['old_params']['fast_ema']}, slow_ema={r['old_params']['slow_ema']}, atr_multiplier={r['old_params']['atr_multiplier']}
- 新参数: fast_ema={r['new_params']['fast_ema']}, slow_ema={r['new_params']['slow_ema']}, atr_multiplier={r['new_params']['atr_multiplier']}

**状态**: {r['status']}

---

"""
    
    # 结论和建议
    report += f"""## 结论与建议

### 回测总结

1. **总体效果**: 新参数方案将平均收益从 {avg_old_return:+.2f}% 提升至 {avg_new_return:+.2f}%，平均改进 {avg_improvement:+.2f}%

2. **负转正效果**: 共有 **{negative_to_positive}** 只股票从负收益转为正收益，成功率 {negative_to_positive/total_stocks*100:.1f}%

3. **收益提升**: 共有 **{improved_count}** 只股票实现收益提升

### 参数优化建议

"""
    
    for r in results:
        if r['status'].startswith("✅"):
            report += f"- ✅ **{r['symbol']} {r['name']}**: 建议采用新参数 (收益改进 {r['improvement']:+.2f}%)\n"
        else:
            report += f"- ⚠️ **{r['symbol']} {r['name']}**: 新参数效果不理想，建议重新优化\n"
    
    report += f"""

### 下一步行动

1. 对于收益转正或显著提升的股票，更新主参数配置文件
2. 对效果不理想的股票进行进一步分析，可能需要调整策略逻辑
3. 在模拟盘观察至少1个月后再考虑实盘部署

---

*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    return report


def save_results(results: List[Dict]):
    """保存回测结果到文件"""
    results_dir = Path('/home/icysaintdx/.openclaw/workspace/InvestMindPro/results')
    results_dir.mkdir(exist_ok=True)
    
    # 保存JSON报告
    json_report = generate_json_report(results)
    json_path = results_dir / 'negative_stock_retest_20260228.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_report, f, ensure_ascii=False, indent=2)
    print(f"\n✅ JSON报告已保存: {json_path}")
    
    # 保存Markdown报告
    md_report = generate_markdown_report(results)
    md_path = results_dir / 'NEGATIVE_STOCK_RETEST_REPORT.md'
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_report)
    print(f"✅ Markdown报告已保存: {md_path}")
    
    return json_path, md_path


def print_summary(results: List[Dict]):
    """打印汇总统计"""
    print("\n" + "="*80)
    print("回测汇总统计")
    print("="*80)
    
    total_stocks = len(results)
    negative_to_positive = sum(1 for r in results 
                               if r['old_return'] < 0 and r['new_return'] > 0)
    improved_count = sum(1 for r in results if r['improvement'] > 0)
    
    avg_old_return = np.mean([r['old_return'] for r in results])
    avg_new_return = np.mean([r['new_return'] for r in results])
    avg_improvement = np.mean([r['improvement'] for r in results])
    
    print(f"\n股票总数: {total_stocks}")
    print(f"原参数平均收益: {avg_old_return:+.2f}%")
    print(f"新参数平均收益: {avg_new_return:+.2f}%")
    print(f"平均收益改进: {avg_improvement:+.2f}%")
    print(f"\n负收益转正收益: {negative_to_positive}/{total_stocks} ({negative_to_positive/total_stocks*100:.1f}%)")
    print(f"收益提升股票: {improved_count}/{total_stocks} ({improved_count/total_stocks*100:.1f}%)")
    
    print("\n" + "="*80)
    print("股票明细")
    print("="*80)
    print(f"{'代码':<10} {'名称':<10} {'原收益':>10} {'新收益':>10} {'改进':>10} {'状态':<15}")
    print("-"*70)
    
    for r in results:
        status = "✅ 转正" if r['old_return'] < 0 and r['new_return'] > 0 else \
                 ("✅ 提升" if r['improvement'] > 0 else "⚠️ 下降")
        print(f"{r['symbol']:<10} {r['name']:<10} {r['old_return']:>+9.2f}% {r['new_return']:>+9.2f}% "
              f"{r['improvement']:>+9.2f}% {status:<15}")


def main():
    """主函数"""
    print("\n" + "#"*80)
    print("# 负收益股票参数优化回测验证")
    print("#"*80)
    
    # 执行回测
    results = run_negative_stock_retest()
    
    # 打印汇总
    print_summary(results)
    
    # 保存结果
    json_path, md_path = save_results(results)
    
    print("\n" + "="*80)
    print("✅ 回测验证完成!")
    print(f"📄 JSON报告: {json_path}")
    print(f"📄 Markdown报告: {md_path}")
    print("="*80)
    
    return results


if __name__ == '__main__':
    main()
