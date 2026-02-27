#!/usr/bin/env python3
"""
EMA V2.1 - 20只股票全量回测脚本
使用akshare真实数据
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

# 添加模块路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'strategies'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'data'))

from ema_v2 import EMAV2Strategy, BacktestResult
from akshare_datasource import AkshareDataSource

# 全部20只股票
ALL_STOCKS = {
    # === 高波动 (6只) ===
    '601888': {'name': '中国中免', 'type': 'high_volatility'},
    '300750': {'name': '宁德时代', 'type': 'high_volatility'},
    '002594': {'name': '比亚迪',   'type': 'high_volatility'},
    '300014': {'name': '亿纬锂能', 'type': 'high_volatility'},
    '300124': {'name': '汇川技术', 'type': 'high_volatility'},
    '002460': {'name': '赣锋锂业', 'type': 'high_volatility'},
    # === 中波动 (7只) ===
    '000858': {'name': '五粮液',   'type': 'medium_volatility'},
    '000333': {'name': '美的集团', 'type': 'medium_volatility'},
    '000651': {'name': '格力电器', 'type': 'medium_volatility'},
    '600276': {'name': '恒瑞医药', 'type': 'medium_volatility'},
    '000568': {'name': '泸州老窖', 'type': 'medium_volatility'},
    '600887': {'name': '伊利股份', 'type': 'medium_volatility'},
    '002415': {'name': '海康威视', 'type': 'medium_volatility'},
    # === 低波动 (7只) ===
    '600519': {'name': '贵州茅台', 'type': 'low_volatility'},
    '601318': {'name': '中国平安', 'type': 'low_volatility'},
    '000001': {'name': '平安银行', 'type': 'low_volatility'},
    '600036': {'name': '招商银行', 'type': 'low_volatility'},
    '601398': {'name': '工商银行', 'type': 'low_volatility'},
    '601288': {'name': '农业银行', 'type': 'low_volatility'},
    '600900': {'name': '长江电力', 'type': 'low_volatility'},
}

# 原始4只（需要用真实数据重新回测）
ORIGINAL_4 = ['002594', '600036', '000001', '300750']

# 新增9只
NEW_STOCKS = ['300014', '300124', '002460', '000568', '600887', '002415', '601398', '601288', '600900']


def run_single_backtest(symbol: str, info: Dict, ds: AkshareDataSource, 
                        market_data: pd.DataFrame, initial_capital: float = 100000.0) -> Optional[Dict]:
    """执行单只股票回测"""
    print(f"\n{'='*60}")
    print(f"回测: {symbol} {info['name']} ({info['type']})")
    print(f"{'='*60}")
    
    stock_data = ds.get_stock_data(symbol, start_date="20200101", use_cache=True)
    if stock_data is None or len(stock_data) < 100:
        print(f"[ERROR] 数据不足: {symbol}, 仅 {len(stock_data) if stock_data is not None else 0} 行")
        return None
    
    stock_data.attrs['symbol'] = symbol
    source = stock_data.attrs.get('source', 'unknown')
    print(f"  数据源: {source}, 数据量: {len(stock_data)} 天")
    print(f"  时间范围: {stock_data.index[0].strftime('%Y-%m-%d')} ~ {stock_data.index[-1].strftime('%Y-%m-%d')}")
    
    # 对齐市场数据
    aligned_market = market_data.reindex(stock_data.index, method='ffill') if market_data is not None else None
    
    strategy = EMAV2Strategy(volatility_type=info['type'])
    print(f"  参数: fast_ema={strategy.fast_ema}, slow_ema={strategy.slow_ema}, atr_mult={strategy.atr_multiplier}")
    
    result = strategy.run_backtest(stock_data, aligned_market, initial_capital)
    
    print(f"  总收益: {result.total_return:+.2f}%")
    print(f"  胜率: {result.win_rate:.1f}%  交易: {result.total_trades}次")
    print(f"  最大回撤: {result.max_drawdown:.2f}%  Sharpe: {result.sharpe_ratio:.2f}")
    
    if result.trades:
        sl = sum(1 for t in result.trades if t['exit_reason'] == 'stop_loss')
        sig = sum(1 for t in result.trades if t['exit_reason'] == 'signal')
        print(f"  信号平仓: {sig}次, 止损: {sl}次")
    
    return {
        'symbol': symbol,
        'name': info['name'],
        'type': info['type'],
        'data_source': source,
        'data_rows': len(stock_data),
        'date_range': f"{stock_data.index[0].strftime('%Y-%m-%d')} ~ {stock_data.index[-1].strftime('%Y-%m-%d')}",
        'total_return': float(result.total_return),
        'win_rate': float(result.win_rate),
        'total_trades': int(result.total_trades),
        'max_drawdown': float(result.max_drawdown),
        'sharpe_ratio': float(result.sharpe_ratio),
        'params': result.params,
        'trades': [
            {**t, 'entry_date': str(t['entry_date']), 'exit_date': str(t['exit_date'])}
            for t in result.trades
        ]
    }


def generate_markdown_report(results: List[Dict], timestamp: str) -> str:
    """生成Markdown汇总报告"""
    sorted_results = sorted(results, key=lambda x: x['total_return'], reverse=True)
    
    # 按类型分组
    by_type = {}
    for r in results:
        t = r['type']
        by_type.setdefault(t, []).append(r)
    
    avg_return = np.mean([r['total_return'] for r in results])
    avg_win_rate = np.mean([r['win_rate'] for r in results])
    avg_sharpe = np.mean([r['sharpe_ratio'] for r in results])
    total_trades = sum(r['total_trades'] for r in results)
    positive = sum(1 for r in results if r['total_return'] > 0)
    
    # 检查数据源 (baostock, akshare, cache 都是真实数据)
    real_sources = ('baostock', 'akshare', 'cache')
    real_count = sum(1 for r in results if r.get('data_source') in real_sources)
    cache_count = sum(1 for r in results if r.get('data_source') == 'cache')
    sim_count = sum(1 for r in results if r.get('data_source') == 'simulated')
    
    md = f"""# EMA V2.1 策略 - 20只股票回测报告

> 生成时间: {timestamp}
> 数据源: baostock真实数据 (实时获取: {real_count}, 缓存: {cache_count}, 模拟: {sim_count})
> 回测区间: 2020-01-01 ~ 2026-02-27
> 初始资金: ¥100,000

---

## 📊 总体表现

| 指标 | 值 |
|------|-----|
| 股票数量 | {len(results)} |
| 平均总收益 | {avg_return:+.2f}% |
| 平均胜率 | {avg_win_rate:.1f}% |
| 平均Sharpe | {avg_sharpe:.2f} |
| 总交易次数 | {total_trades} |
| 盈利股票数 | {positive}/{len(results)} |

---

## 🏆 收益排行榜

| 排名 | 代码 | 名称 | 类型 | 总收益 | 胜率 | 交易次数 | 最大回撤 | Sharpe | 数据源 |
|:----:|:----:|:----:|:----:|------:|-----:|--------:|--------:|------:|:------:|
"""
    
    type_labels = {
        'high_volatility': '🔴高波',
        'medium_volatility': '🟡中波',
        'low_volatility': '🟢低波'
    }
    
    for i, r in enumerate(sorted_results, 1):
        tl = type_labels.get(r['type'], r['type'])
        src = '✅真实' if r.get('data_source') in ('baostock', 'akshare', 'cache') else '⚠️模拟'
        md += f"| {i} | {r['symbol']} | {r['name']} | {tl} | {r['total_return']:+.2f}% | {r['win_rate']:.1f}% | {r['total_trades']} | {r['max_drawdown']:.2f}% | {r['sharpe_ratio']:.2f} | {src} |\n"
    
    md += f"""
---

## 📈 按波动率分类统计

"""
    
    type_order = ['high_volatility', 'medium_volatility', 'low_volatility']
    type_names = {'high_volatility': '高波动', 'medium_volatility': '中波动', 'low_volatility': '低波动'}
    
    for t in type_order:
        if t not in by_type:
            continue
        group = by_type[t]
        g_avg_ret = np.mean([r['total_return'] for r in group])
        g_avg_wr = np.mean([r['win_rate'] for r in group])
        g_avg_sh = np.mean([r['sharpe_ratio'] for r in group])
        g_avg_dd = np.mean([r['max_drawdown'] for r in group])
        g_trades = sum(r['total_trades'] for r in group)
        
        md += f"""### {type_labels.get(t, t)} {type_names[t]} ({len(group)}只)

| 指标 | 值 |
|------|-----|
| 平均收益 | {g_avg_ret:+.2f}% |
| 平均胜率 | {g_avg_wr:.1f}% |
| 平均Sharpe | {g_avg_sh:.2f} |
| 平均最大回撤 | {g_avg_dd:.2f}% |
| 总交易次数 | {g_trades} |

| 代码 | 名称 | 总收益 | 胜率 | 交易 | 最大回撤 | Sharpe |
|:----:|:----:|------:|-----:|-----:|--------:|------:|
"""
        for r in sorted(group, key=lambda x: x['total_return'], reverse=True):
            md += f"| {r['symbol']} | {r['name']} | {r['total_return']:+.2f}% | {r['win_rate']:.1f}% | {r['total_trades']} | {r['max_drawdown']:.2f}% | {r['sharpe_ratio']:.2f} |\n"
        md += "\n"
    
    # 策略参数
    md += """---

## ⚙️ 策略参数

| 波动类型 | 快EMA | 慢EMA | ATR周期 | ATR倍数 | 大盘过滤 |
|:--------:|:-----:|:-----:|:-------:|:-------:|:--------:|
| 高波动 | 10 | 30 | 14 | 3.0 | ✅ |
| 中波动 | 8 | 25 | 14 | 2.0 | ✅ |
| 低波动 | 5 | 20 | 14 | 1.5 | ✅ |

---

## 📝 结论与观察

"""
    
    # 自动生成一些观察
    best = sorted_results[0]
    worst = sorted_results[-1]
    
    md += f"- **最佳表现**: {best['symbol']} {best['name']} ({best['total_return']:+.2f}%)\n"
    md += f"- **最差表现**: {worst['symbol']} {worst['name']} ({worst['total_return']:+.2f}%)\n"
    
    for t in type_order:
        if t in by_type:
            g = by_type[t]
            g_avg = np.mean([r['total_return'] for r in g])
            md += f"- **{type_names[t]}平均收益**: {g_avg:+.2f}% ({len(g)}只)\n"
    
    md += f"\n> 本报告基于EMA V2.1策略回测生成，仅供研究参考，不构成投资建议。\n"
    
    return md


def main():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_dir = Path(__file__).parent.parent / 'results'
    results_dir.mkdir(exist_ok=True)
    
    print(f"{'#'*70}")
    print(f"# EMA V2.1 - 20只股票全量回测")
    print(f"# 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"# 股票数: {len(ALL_STOCKS)}")
    print(f"{'#'*70}")
    
    # 初始化数据源
    ds = AkshareDataSource(data_dir=str(Path(__file__).parent.parent / 'data'))
    
    # 先获取大盘数据
    print("\n[STEP 1] 获取沪深300大盘数据...")
    market_data = ds.get_market_data(start_date="20200101")
    if market_data is not None:
        print(f"  沪深300: {len(market_data)} 天, {market_data.index[0]} ~ {market_data.index[-1]}")
    
    # 清除原始4只的缓存，强制重新获取
    print("\n[STEP 2] 清除原始4只股票缓存，强制使用真实数据...")
    data_dir = Path(__file__).parent.parent / 'data'
    for sym in ORIGINAL_4:
        cache_file = data_dir / f"{sym}.csv"
        if cache_file.exists():
            cache_file.unlink()
            print(f"  已删除缓存: {cache_file.name}")
    # 也清除沪深300缓存
    market_cache = data_dir / "000300.csv"
    if market_cache.exists():
        market_cache.unlink()
        print(f"  已删除缓存: 000300.csv")
        market_data = ds.get_market_data(start_date="20200101")
    
    # 执行回测
    print(f"\n[STEP 3] 开始回测 {len(ALL_STOCKS)} 只股票...")
    results = []
    failed = []
    
    for i, (symbol, info) in enumerate(ALL_STOCKS.items(), 1):
        print(f"\n--- 进度: [{i}/{len(ALL_STOCKS)}] ---")
        try:
            result = run_single_backtest(symbol, info, ds, market_data)
            if result:
                results.append(result)
            else:
                failed.append(symbol)
        except Exception as e:
            print(f"[ERROR] {symbol} 回测失败: {e}")
            failed.append(symbol)
    
    if not results:
        print("\n[FATAL] 无有效回测结果!")
        return
    
    # 保存JSON结果
    print(f"\n[STEP 4] 保存结果...")
    
    summary = {
        'timestamp': timestamp,
        'total_stocks': len(ALL_STOCKS),
        'successful': len(results),
        'failed': failed,
        'avg_return': float(np.mean([r['total_return'] for r in results])),
        'avg_win_rate': float(np.mean([r['win_rate'] for r in results])),
        'total_trades': int(sum(r['total_trades'] for r in results)),
        'results': results
    }
    
    json_file = results_dir / f"ema_v2_backtest_real_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2, default=str)
    print(f"  JSON: {json_file}")
    
    # 生成Markdown报告
    report_ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    md_content = generate_markdown_report(results, report_ts)
    
    md_file = results_dir / "EMA_V2_20STOCK_REPORT.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(md_content)
    print(f"  报告: {md_file}")
    
    # 打印汇总
    print(f"\n{'='*70}")
    print(f"回测完成!")
    print(f"  成功: {len(results)}/{len(ALL_STOCKS)}")
    if failed:
        print(f"  失败: {failed}")
    print(f"  平均收益: {summary['avg_return']:+.2f}%")
    print(f"  平均胜率: {summary['avg_win_rate']:.1f}%")
    print(f"  总交易: {summary['total_trades']}次")
    print(f"{'='*70}")


if __name__ == '__main__':
    main()
