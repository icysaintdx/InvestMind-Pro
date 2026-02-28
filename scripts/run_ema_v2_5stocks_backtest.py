#!/usr/bin/env python3
"""
EMA V2 策略 - 5只股票回测脚本
使用akshare获取真实数据
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

import akshare as ak

# 5只目标股票及其优化参数
TARGET_STOCKS = {
    '000651': {
        'name': '格力电器',
        'fast_ema': 10, 'slow_ema': 30, 'atr_period': 14, 'atr_multiplier': 1.5, 'market_filter': True,
        'volatility_type': 'medium_volatility'
    },
    '000858': {
        'name': '五粮液',
        'fast_ema': 8, 'slow_ema': 35, 'atr_period': 14, 'atr_multiplier': 2.5, 'market_filter': True,
        'volatility_type': 'medium_volatility'
    },
    '002415': {
        'name': '海康威视',
        'fast_ema': 12, 'slow_ema': 15, 'atr_period': 14, 'atr_multiplier': 3.0, 'market_filter': True,
        'volatility_type': 'medium_volatility'
    },
    '002460': {
        'name': '赣锋锂业',
        'fast_ema': 3, 'slow_ema': 35, 'atr_period': 14, 'atr_multiplier': 1.5, 'market_filter': True,
        'volatility_type': 'high_volatility'
    },
    '002594': {
        'name': '比亚迪',
        'fast_ema': 7, 'slow_ema': 30, 'atr_period': 14, 'atr_multiplier': 2.5, 'market_filter': True,
        'volatility_type': 'high_volatility'
    },
}


def get_stock_data(symbol: str, start_date: str = "20200101") -> Optional[pd.DataFrame]:
    """使用akshare获取股票数据"""
    try:
        # 格式化代码 (深圳股票加前缀)
        if symbol.startswith('0') or symbol.startswith('3'):
            ak_symbol = f"{symbol}.sz"
        else:
            ak_symbol = f"{symbol}.sh"
        
        print(f"  正在获取 {symbol} 数据...")
        df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start_date, adjust="qfq")
        
        if df is None or len(df) < 100:
            print(f"  [警告] 数据不足: {len(df) if df is not None else 0} 行")
            return None
        
        # 标准化列名
        df.columns = [c.lower() for c in df.columns]
        column_mapping = {
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'amount',
            '振幅': 'amplitude',
            '涨跌幅': 'pct_change',
            '涨跌额': 'change',
            '换手率': 'turnover'
        }
        df.rename(columns=column_mapping, inplace=True)
        
        # 设置日期索引
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
        
        df.attrs['symbol'] = symbol
        df.attrs['source'] = 'akshare'
        
        print(f"  成功获取 {len(df)} 条数据 ({df.index[0].strftime('%Y-%m-%d')} ~ {df.index[-1].strftime('%Y-%m-%d')})")
        return df
        
    except Exception as e:
        print(f"  [错误] 获取数据失败: {e}")
        return None


def get_market_data(start_date: str = "20200101") -> Optional[pd.DataFrame]:
    """获取沪深300指数数据作为市场基准"""
    try:
        print("  正在获取沪深300数据...")
        df = ak.index_zh_a_hist(symbol="000300", period="daily", start_date=start_date)
        
        if df is None or len(df) < 100:
            return None
        
        df.columns = [c.lower() for c in df.columns]
        column_mapping = {
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'amount',
            '振幅': 'amplitude',
            '涨跌幅': 'pct_change',
            '涨跌额': 'change'
        }
        df.rename(columns=column_mapping, inplace=True)
        
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
        
        print(f"  成功获取沪深300 {len(df)} 条数据")
        return df
        
    except Exception as e:
        print(f"  [错误] 获取市场数据失败: {e}")
        return None


def run_single_backtest(symbol: str, info: Dict, market_data: pd.DataFrame) -> Optional[Dict]:
    """执行单只股票回测"""
    print(f"\n{'='*60}")
    print(f"📊 回测: {symbol} {info['name']}")
    print(f"{'='*60}")
    
    # 获取股票数据
    stock_data = get_stock_data(symbol)
    if stock_data is None:
        return None
    
    # 对齐市场数据
    aligned_market = market_data.reindex(stock_data.index, method='ffill') if market_data is not None else None
    
    # 提取参数
    params = {
        'fast_ema': info['fast_ema'],
        'slow_ema': info['slow_ema'],
        'atr_period': info['atr_period'],
        'atr_multiplier': info['atr_multiplier'],
        'market_filter': info['market_filter']
    }
    
    print(f"\n  策略参数:")
    print(f"    快EMA: {params['fast_ema']}")
    print(f"    慢EMA: {params['slow_ema']}")
    print(f"    ATR周期: {params['atr_period']}")
    print(f"    ATR倍数: {params['atr_multiplier']}")
    print(f"    大盘过滤: {'开启' if params['market_filter'] else '关闭'}")
    
    # 创建策略并执行回测
    strategy = EMAV2Strategy(params)
    result = strategy.run_backtest(stock_data, aligned_market)
    
    # 计算额外统计
    if result.trades:
        stop_loss_count = sum(1 for t in result.trades if t.get('exit_reason') == 'stop_loss')
        signal_count = sum(1 for t in result.trades if t.get('exit_reason') == 'signal')
        avg_profit = np.mean([t['pnl_pct'] for t in result.trades]) if result.trades else 0
        max_profit = max([t['pnl_pct'] for t in result.trades]) if result.trades else 0
        min_profit = min([t['pnl_pct'] for t in result.trades]) if result.trades else 0
    else:
        stop_loss_count = signal_count = 0
        avg_profit = max_profit = min_profit = 0
    
    # 打印结果
    print(f"\n  📈 回测结果:")
    print(f"    总收益率: {result.total_return:+.2f}%")
    print(f"    年化收益: {result.total_return / 6:.2f}% (按6年计算)")
    print(f"    胜率: {result.win_rate:.1f}%")
    print(f"    交易次数: {result.total_trades}")
    print(f"      - 信号平仓: {signal_count}次")
    print(f"      - 止损平仓: {stop_loss_count}次")
    print(f"    最大回撤: {result.max_drawdown:.2f}%")
    print(f"    Sharpe比率: {result.sharpe_ratio:.2f}")
    print(f"    平均盈亏: {avg_profit:+.2f}%")
    print(f"    最大单笔盈利: {max_profit:+.2f}%")
    print(f"    最大单笔亏损: {min_profit:+.2f}%")
    
    return {
        'symbol': symbol,
        'name': info['name'],
        'volatility_type': info['volatility_type'],
        'params': params,
        'total_return': float(result.total_return),
        'annual_return': float(result.total_return / 6),
        'win_rate': float(result.win_rate),
        'total_trades': int(result.total_trades),
        'signal_exits': signal_count,
        'stop_loss_exits': stop_loss_count,
        'max_drawdown': float(result.max_drawdown),
        'sharpe_ratio': float(result.sharpe_ratio),
        'avg_profit_per_trade': float(avg_profit),
        'max_profit': float(max_profit),
        'min_profit': float(min_profit),
        'data_start': stock_data.index[0].strftime('%Y-%m-%d'),
        'data_end': stock_data.index[-1].strftime('%Y-%m-%d'),
        'data_points': len(stock_data),
        'trades': [
            {**t, 'entry_date': str(t['entry_date']), 'exit_date': str(t['exit_date'])}
            for t in result.trades
        ]
    }


def generate_summary_report(results: List[Dict], timestamp: str) -> str:
    """生成Markdown汇总报告"""
    
    # 按收益排序
    sorted_results = sorted(results, key=lambda x: x['total_return'], reverse=True)
    
    # 计算统计
    returns = [r['total_return'] for r in results]
    avg_return = np.mean(returns)
    median_return = np.median(returns)
    best_return = max(returns)
    worst_return = min(returns)
    positive_count = sum(1 for r in returns if r > 0)
    
    win_rates = [r['win_rate'] for r in results]
    avg_win_rate = np.mean(win_rates)
    
    sharpes = [r['sharpe_ratio'] for r in results]
    avg_sharpe = np.mean(sharpes)
    
    drawdowns = [r['max_drawdown'] for r in results]
    avg_drawdown = np.mean(drawdowns)
    
    total_trades = sum(r['total_trades'] for r in results)
    
    md = f"""# EMA V2 策略回测报告 - 5只股票

> 生成时间: {timestamp}
> 数据源: AKShare (真实数据)
> 回测区间: 2020-01-01 至 {datetime.now().strftime('%Y-%m-%d')}
> 初始资金: ¥100,000

---

## 📊 总体表现

| 指标 | 数值 |
|------|------|
| 回测股票数 | {len(results)} |
| 平均总收益 | {avg_return:+.2f}% |
| 中位数收益 | {median_return:+.2f}% |
| 最佳收益 | {best_return:+.2f}% |
| 最差收益 | {worst_return:+.2f}% |
| 正收益股票数 | {positive_count}/{len(results)} |
| 平均胜率 | {avg_win_rate:.1f}% |
| 平均Sharpe | {avg_sharpe:.2f} |
| 平均最大回撤 | {avg_drawdown:.2f}% |
| 总交易次数 | {total_trades} |

---

## 🏆 收益排行榜

| 排名 | 代码 | 名称 | 波动类型 | 总收益 | 年化收益 | 胜率 | 交易次数 | 最大回撤 | Sharpe |
|:----:|:----:|:----:|:--------:|-------:|---------:|-----:|---------:|---------:|-------:|
"""
    
    type_labels = {
        'high_volatility': '高波动',
        'medium_volatility': '中波动',
        'low_volatility': '低波动'
    }
    
    for i, r in enumerate(sorted_results, 1):
        vol_type = type_labels.get(r['volatility_type'], r['volatility_type'])
        md += f"| {i} | {r['symbol']} | {r['name']} | {vol_type} | {r['total_return']:+.2f}% | {r['annual_return']:+.2f}% | {r['win_rate']:.1f}% | {r['total_trades']} | {r['max_drawdown']:.2f}% | {r['sharpe_ratio']:.2f} |\n"
    
    md += """
---

## 📋 详细结果

"""
    
    for r in sorted_results:
        md += f"""### {r['symbol']} {r['name']}

| 指标 | 数值 |
|------|------|
| 总收益 | {r['total_return']:+.2f}% |
| 年化收益 | {r['annual_return']:+.2f}% |
| 胜率 | {r['win_rate']:.1f}% |
| 交易次数 | {r['total_trades']} |
| 信号平仓 | {r['signal_exits']}次 |
| 止损平仓 | {r['stop_loss_exits']}次 |
| 最大回撤 | {r['max_drawdown']:.2f}% |
| Sharpe比率 | {r['sharpe_ratio']:.2f} |
| 平均盈亏 | {r['avg_profit_per_trade']:+.2f}% |
| 最大单笔盈利 | {r['max_profit']:+.2f}% |
| 最大单笔亏损 | {r['min_profit']:+.2f}% |
| 数据时间范围 | {r['data_start']} ~ {r['data_end']} |

**策略参数:**
- 快EMA: {r['params']['fast_ema']}
- 慢EMA: {r['params']['slow_ema']}
- ATR周期: {r['params']['atr_period']}
- ATR倍数: {r['params']['atr_multiplier']}
- 大盘过滤: {'开启' if r['params']['market_filter'] else '关闭'}

---

"""
    
    md += f"""## ⚙️ 策略说明

**EMA V2 策略核心逻辑:**
1. **买入信号**: 快EMA上穿慢EMA (金叉) + 大盘环境允许
2. **卖出信号**: 快EMA下穿慢EMA (死叉) 或 价格跌破ATR止损线
3. **动态止损**: 基于ATR计算止损位置，根据波动率自动调整
4. **大盘过滤**: 使用沪深300指数判断市场环境，熊市暂停新开仓

**参数说明:**
| 股票 | 波动类型 | 快EMA | 慢EMA | ATR倍数 |
|------|----------|-------|-------|---------|
"""
    
    for r in sorted_results:
        vol_type = type_labels.get(r['volatility_type'], r['volatility_type'])
        md += f"| {r['symbol']} {r['name']} | {vol_type} | {r['params']['fast_ema']} | {r['params']['slow_ema']} | {r['params']['atr_multiplier']:.1f} |\n"
    
    md += f"""
---

## 📝 结论

- **平均收益**: {avg_return:+.2f}%，{positive_count}/{len(results)}只股票实现正收益
- **最佳表现**: {sorted_results[0]['symbol']} {sorted_results[0]['name']} ({sorted_results[0]['total_return']:+.2f}%)
- **最差表现**: {sorted_results[-1]['symbol']} {sorted_results[-1]['name']} ({sorted_results[-1]['total_return']:+.2f}%)
- **平均胜率**: {avg_win_rate:.1f}%
- **平均Sharpe**: {avg_sharpe:.2f}

> ⚠️ **免责声明**: 本报告基于历史数据回测生成，仅供研究参考，不构成投资建议。过往表现不代表未来收益。
"""
    
    return md


def main():
    """主函数"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    print(f"{'#'*70}")
    print(f"# EMA V2 策略 - 5只股票回测")
    print(f"# 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"# 股票: {', '.join(TARGET_STOCKS.keys())}")
    print(f"{'#'*70}")
    
    # 获取市场数据
    print("\n[STEP 1] 获取沪深300大盘数据...")
    market_data = get_market_data()
    if market_data is None:
        print("[警告] 无法获取市场数据，将禁用大盘过滤")
    
    # 执行回测
    print(f"\n[STEP 2] 开始回测 {len(TARGET_STOCKS)} 只股票...")
    results = []
    failed = []
    
    for i, (symbol, info) in enumerate(TARGET_STOCKS.items(), 1):
        print(f"\n--- 进度: [{i}/{len(TARGET_STOCKS)}] ---")
        try:
            result = run_single_backtest(symbol, info, market_data)
            if result:
                results.append(result)
            else:
                failed.append(symbol)
        except Exception as e:
            print(f"[错误] {symbol} 回测失败: {e}")
            import traceback
            traceback.print_exc()
            failed.append(symbol)
    
    if not results:
        print("\n[致命错误] 无有效回测结果!")
        return 1
    
    # 保存结果
    print(f"\n[STEP 3] 保存结果...")
    
    # 创建结果目录
    results_dir = Path(__file__).parent.parent / 'results'
    results_dir.mkdir(exist_ok=True)
    
    # 保存JSON结果
    summary = {
        'timestamp': timestamp,
        'total_stocks': len(TARGET_STOCKS),
        'successful': len(results),
        'failed': failed,
        'avg_return': float(np.mean([r['total_return'] for r in results])),
        'avg_win_rate': float(np.mean([r['win_rate'] for r in results])),
        'avg_sharpe': float(np.mean([r['sharpe_ratio'] for r in results])),
        'total_trades': int(sum(r['total_trades'] for r in results)),
        'results': results
    }
    
    json_file = results_dir / f"ema_v2_5stocks_backtest_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2, default=str)
    print(f"  JSON文件: {json_file}")
    
    # 生成Markdown报告
    report_ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    md_content = generate_summary_report(results, report_ts)
    
    md_file = results_dir / f"EMA_V2_5STOCKS_REPORT_{timestamp}.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(md_content)
    print(f"  报告文件: {md_file}")
    
    # 打印汇总
    print(f"\n{'='*70}")
    print(f"✅ 回测完成!")
    print(f"{'='*70}")
    print(f"  成功: {len(results)}/{len(TARGET_STOCKS)}")
    if failed:
        print(f"  失败: {failed}")
    print(f"  平均收益: {summary['avg_return']:+.2f}%")
    print(f"  平均胜率: {summary['avg_win_rate']:.1f}%")
    print(f"  总交易: {summary['total_trades']}次")
    print(f"  结果文件: {json_file}")
    print(f"{'='*70}")
    
    # 打印排行榜
    print("\n📊 收益排行榜:")
    sorted_results = sorted(results, key=lambda x: x['total_return'], reverse=True)
    for i, r in enumerate(sorted_results, 1):
        status = "✅" if r['total_return'] > 0 else "❌"
        print(f"  {i}. {r['symbol']} {r['name']}: {r['total_return']:+.2f}% {status}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
