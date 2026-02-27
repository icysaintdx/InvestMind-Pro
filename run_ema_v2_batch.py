#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EMA V2.1 优化版策略 - 逐个股票回测
工作目录: ~/.openclaw/workspace-investmindpro/InvestMindPro
"""

import sys
import os
import json
import time
import logging
from pathlib import Path
from datetime import datetime

# 设置项目路径
project_root = Path(__file__).parent
backend_root = project_root / "backend"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_root))
os.chdir(project_root)

import pandas as pd
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

START_DATE = "20200101"
END_DATE = "20241231"
INITIAL_CAPITAL = 1_000_000.0
COMMISSION_RATE = 0.0003
SLIPPAGE_RATE = 0.0005

# 股票列表 (代码: 名称)
STOCKS = {
    "601318": "中国平安",   # 低波动
    "000858": "五粮液",     # 中波动
    "000333": "美的集团",   # 中波动
    "000651": "格力电器",   # 中波动
    "600276": "恒瑞医药",   # 低波动
    "601888": "中国中免"    # 高波动
}

CACHE_DIR = project_root / "backend" / "data" / "backtest_cache"
RESULTS_DIR = project_root / "backtest_results"
RESULTS_DIR.mkdir(exist_ok=True)

def load_ohlcv(symbol: str, start: str, end: str):
    """加载K线数据"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{symbol}_{start}_{end}.csv"

    if cache_file.exists():
        logger.info(f"[{symbol}] 从缓存加载K线数据")
        df = pd.read_csv(cache_file, index_col='date', parse_dates=True)
        return df

    try:
        import akshare as ak
        logger.info(f"[{symbol}] 从AKShare下载K线数据...")
        df = ak.stock_zh_a_hist(
            symbol=symbol, period="daily",
            start_date=start, end_date=end, adjust="qfq"
        )
    except Exception as e:
        logger.error(f"[{symbol}] 下载失败: {e}")
        return None

    if df is None or df.empty:
        return None

    df = df.rename(columns={
        '日期': 'date', '开盘': 'open', '收盘': 'close',
        '最高': 'high', '最低': 'low', '成交量': 'volume', '成交额': 'amount',
    })
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    for c in ['open', 'high', 'low', 'close', 'volume']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df.sort_index(inplace=True)
    df.to_csv(cache_file)
    return df

def load_market_data(start: str, end: str):
    """加载沪深300大盘数据用于趋势过滤"""
    cache_file = CACHE_DIR / f"sh000300_{start}_{end}.csv"
    
    if cache_file.exists():
        return pd.read_csv(cache_file, index_col='date', parse_dates=True)
    
    try:
        import akshare as ak
        logger.info("[大盘] 下载沪深300数据...")
        df = ak.index_zh_a_hist(symbol="sh000300", period="daily",
                                start_date=start, end_date=end)
        df = df.rename(columns={
            '日期': 'date', '开盘': 'open', '收盘': 'close',
            '最高': 'high', '最低': 'low', '成交量': 'volume'
        })
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df.to_csv(cache_file)
        return df
    except Exception as e:
        logger.warning(f"[大盘] 加载失败: {e}")
        return None

def run_backtest_optimized(stock_code: str, stock_name: str):
    """使用EMA V2.1优化版策略执行回测"""
    from strategies.ema_breakout_v2_optimized import EMABreakoutV2OptimizedStrategy
    from strategies.base import StrategyConfig, SignalType
    
    logger.info(f"\n{'='*60}")
    logger.info(f"开始回测: {stock_code} {stock_name}")
    logger.info(f"{'='*60}")
    
    # 加载数据
    data = load_ohlcv(stock_code, START_DATE, END_DATE)
    if data is None or len(data) < 100:
        logger.error(f"[{stock_code}] 数据不足，无法回测")
        return None
    
    market_data = load_market_data(START_DATE, END_DATE)
    
    # 初始化策略
    config = StrategyConfig(name="ema_breakout_v2_optimized", 
                           parameters={'symbol': stock_code})
    strategy = EMABreakoutV2OptimizedStrategy(config)
    strategy.initialize(data, market_data)
    
    # 回测参数
    cash = INITIAL_CAPITAL
    position = 0
    avg_cost = 0.0
    trades = []
    equity_curve = [{'date': str(data.index[0]), 'value': INITIAL_CAPITAL}]
    stoploss_count = 0
    
    start_idx = 60
    if len(data) <= start_idx:
        return None
    
    for idx in range(start_idx, len(data)):
        current_data = data.iloc[:idx + 1]
        bar = data.iloc[idx]
        price = float(bar['close'])
        
        # 重新初始化策略以获取最新指标
        strategy.initialize(current_data, market_data)
        
        try:
            signal = strategy.generate_signal(current_data, position)
            if signal is None:
                signal_type = "hold"
            else:
                signal_type = signal.signal_type.value if hasattr(signal.signal_type, 'value') else str(signal.signal_type)
                reason = getattr(signal, 'reason', '')
        except Exception as e:
            logger.warning(f"信号生成错误: {e}")
            signal_type = "hold"
        
        # 买入逻辑
        if signal_type in ("buy", "strong_buy") and position == 0:
            max_value = cash * 0.95
            shares = int(max_value / price / 100) * 100
            if shares >= 100:
                cost = shares * price
                commission = max(cost * COMMISSION_RATE, 5)
                slippage = cost * SLIPPAGE_RATE
                total = cost + commission + slippage
                if total <= cash:
                    cash -= total
                    position = shares
                    avg_cost = price
                    trades.append({
                        'date': str(bar.name), 'action': 'BUY', 'price': price,
                        'shares': shares, 'commission': commission, 'slippage': slippage,
                        'reason': reason if 'reason' in locals() else ''
                    })
                    logger.info(f"  [买入] {bar.name.date()}: {price:.2f}元 × {shares}股")
        
        # 卖出逻辑（信号或止损）
        elif signal_type in ("sell", "strong_sell") and position > 0:
            revenue = position * price
            commission = max(revenue * COMMISSION_RATE, 5)
            slippage = revenue * SLIPPAGE_RATE
            stamp_tax = revenue * 0.001
            net = revenue - commission - slippage - stamp_tax
            profit = net - position * avg_cost
            profit_pct = profit / (position * avg_cost) if avg_cost > 0 else 0
            cash += net
            
            is_stoploss = 'stoploss' in signal_type or ('reason' in locals() and '止损' in reason)
            if is_stoploss:
                stoploss_count += 1
            
            trades.append({
                'date': str(bar.name), 'action': 'SELL', 'price': price,
                'shares': position, 'commission': commission, 'slippage': slippage,
                'stamp_tax': stamp_tax, 'profit': profit, 'profit_pct': profit_pct,
                'is_stoploss': is_stoploss
            })
            logger.info(f"  [卖出] {bar.name.date()}: {price:.2f}元, 盈亏: {profit_pct:+.2%} {'[止损]' if is_stoploss else ''}")
            position = 0
            avg_cost = 0.0
        
        portfolio_value = cash + position * price
        equity_curve.append({'date': str(bar.name), 'value': portfolio_value})
    
    # 计算最终指标
    final_price = float(data.iloc[-1]['close'])
    final_value = cash + position * final_price
    
    values = pd.Series([e['value'] for e in equity_curve])
    dates = pd.to_datetime([e['date'] for e in equity_curve])
    total_return = (final_value / INITIAL_CAPITAL) - 1
    days = (dates[-1] - dates[0]).days
    years = max(days / 365.25, 0.01)
    annual_return = (1 + total_return) ** (1 / years) - 1
    daily_returns = values.pct_change().dropna()
    volatility = daily_returns.std() * np.sqrt(252) if len(daily_returns) > 1 else 0
    sharpe = (annual_return - 0.03) / volatility if volatility > 0 else 0
    cummax = values.expanding().max()
    drawdown = (values - cummax) / cummax
    max_drawdown = drawdown.min()
    sell_trades = [t for t in trades if t['action'] == 'SELL']
    win_trades = [t for t in sell_trades if t.get('profit', 0) > 0]
    win_rate = len(win_trades) / len(sell_trades) if sell_trades else 0
    
    result = {
        'stock_code': stock_code,
        'stock_name': stock_name,
        'total_return': float(total_return),
        'annual_return': float(annual_return),
        'max_drawdown': float(max_drawdown),
        'sharpe_ratio': float(sharpe),
        'volatility': float(volatility),
        'win_rate': float(win_rate),
        'total_trades': len(trades),
        'buy_trades': len([t for t in trades if t['action'] == 'BUY']),
        'sell_trades': len(sell_trades),
        'stoploss_count': stoploss_count,
        'final_value': float(final_value),
        'trades': trades
    }
    
    logger.info(f"\n[{stock_code} 结果]")
    logger.info(f"  总收益: {total_return:+.2%}")
    logger.info(f"  年化收益: {annual_return:+.2%}")
    logger.info(f"  最大回撤: {max_drawdown:.2%}")
    logger.info(f"  夏普比率: {sharpe:.2f}")
    logger.info(f"  胜率: {win_rate:.1%}")
    logger.info(f"  交易次数: {len(sell_trades)}")
    logger.info(f"  止损次数: {stoploss_count}")
    
    return result

def generate_report(results: dict, timestamp: str):
    """生成Markdown报告"""
    lines = [
        f"# EMA V2.1 优化版回测报告",
        f"",
        f"**生成时间**: {timestamp}",
        f"",
        f"**回测区间**: {START_DATE} - {END_DATE}",
        f"",
        f"## 参数配置",
        f"",
        f"| 波动率分类 | ATR倍数 | EMA周期 | 股票示例 |",
        f"|:---|:---:|:---:|:---|",
        f"| 高波动 | 3.0 | 10/30 | 中国中免 |",
        f"| 中波动 | 2.0 | 8/25 | 五粮液、美的、格力 |",
        f"| 低波动 | 1.5 | 5/20 | 平安、恒瑞 |",
        f"",
        f"## 回测结果汇总",
        f"",
        f"| 排名 | 股票代码 | 股票名称 | 总收益 | 年化收益 | 最大回撤 | 胜率 | 交易次数 | 止损次数 |",
        f"|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]
    
    sorted_results = sorted(results.items(), key=lambda x: x[1]['total_return'], reverse=True)
    for rank, (code, r) in enumerate(sorted_results, 1):
        lines.append(f"| {rank} | {code} | {r['stock_name']} | {r['total_return']:+.2%} | {r['annual_return']:+.2%} | {r['max_drawdown']:.2%} | {r['win_rate']:.1%} | {r['sell_trades']} | {r['stoploss_count']} |")
    
    avg_return = sum(r['total_return'] for r in results.values()) / len(results)
    lines.extend([
        f"",
        f"## 统计摘要",
        f"",
        f"- **平均总收益**: {avg_return:+.2%}",
        f"- **股票数量**: {len(results)}",
        f"- **总交易次数**: {sum(r['sell_trades'] for r in results.values())}",
        f"- **总止损次数**: {sum(r['stoploss_count'] for r in results.values())}",
        f""
    ])
    
    return '\n'.join(lines)

def main():
    """主函数 - 逐个执行回测"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    all_results = {}
    
    logger.info(f"\n{'#'*70}")
    logger.info(f"# EMA V2.1 优化版批量回测")
    logger.info(f"# 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"# 股票数量: {len(STOCKS)}")
    logger.info(f"{'#'*70}\n")
    
    for stock_code, stock_name in STOCKS.items():
        try:
            result = run_backtest_optimized(stock_code, stock_name)
            if result:
                all_results[stock_code] = result
                
                # 保存单个股票结果
                single_result_file = RESULTS_DIR / f"ema_v2_{stock_code}_optimized_results_{timestamp}.json"
                with open(single_result_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                logger.info(f"  结果已保存: {single_result_file.name}")
                
                # 生成单个股票报告
                single_report = generate_report({stock_code: result}, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                single_report_file = RESULTS_DIR / f"ema_v2_{stock_code}_optimized_report_{timestamp}.md"
                with open(single_report_file, 'w', encoding='utf-8') as f:
                    f.write(single_report)
                logger.info(f"  报告已保存: {single_report_file.name}")
            
            time.sleep(1)  # 避免请求过快
        except Exception as e:
            logger.error(f"[{stock_code}] 回测失败: {e}")
            import traceback
            traceback.print_exc()
    
    # 保存汇总结果
    if all_results:
        summary_file = RESULTS_DIR / f"ema_v2_batch_optimized_results_{timestamp}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        
        # 生成汇总报告
        report = generate_report(all_results, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        report_file = RESULTS_DIR / f"ema_v2_batch_optimized_report_{timestamp}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"\n{'='*60}")
        logger.info("批量回测完成!")
        logger.info(f"汇总结果: {summary_file.name}")
        logger.info(f"汇总报告: {report_file.name}")
        logger.info(f"平均收益: {sum(r['total_return'] for r in all_results.values()) / len(all_results):+.2%}")
        logger.info(f"{'='*60}")

if __name__ == "__main__":
    main()
