#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EMA V2策略专用回测 - 修复版（每次重新初始化策略）
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

STOCKS = {
    "600519": "贵州茅台",
    "601318": "中国平安",
    "000858": "五粮液",
    "000333": "美的集团",
    "000651": "格力电器",
    "600276": "恒瑞医药",
    "601888": "中国中免"
}

CACHE_DIR = project_root / "backend" / "data" / "backtest_cache"

def load_ohlcv(symbol: str, start: str, end: str):
    """加载K线数据"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{symbol}_{start}_{end}.csv"

    if cache_file.exists():
        logger.info(f"[缓存] 加载 {symbol} K线")
        df = pd.read_csv(cache_file, index_col='date', parse_dates=True)
        return df

    try:
        import akshare as ak
        logger.info(f"[AKShare] 下载 {symbol} K线")
        df = ak.stock_zh_a_hist(
            symbol=symbol, period="daily",
            start_date=start, end_date=end, adjust="qfq"
        )
    except Exception as e:
        logger.error(f"下载 {symbol} 失败: {e}")
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

def run_backtest_for_stock(stock_code: str, data: pd.DataFrame):
    """为单只股票运行回测 - 每次重新初始化策略"""
    from strategies.ema_breakout_v2 import EMABreakoutV2Strategy
    from strategies.base import StrategyConfig, SignalType
    
    cash = INITIAL_CAPITAL
    position = 0
    avg_cost = 0.0
    trades = []
    equity_curve = [{'date': str(data.index[0]), 'value': INITIAL_CAPITAL}]
    
    start_idx = 60  # 预留指标计算期
    if len(data) <= start_idx:
        return None
    
    for idx in range(start_idx, len(data)):
        current_data = data.iloc[:idx + 1]
        bar = data.iloc[idx]
        price = float(bar['close'])
        
        # 每次创建新策略实例并初始化
        config = StrategyConfig(name="ema_breakout_v2", parameters={})
        strategy = EMABreakoutV2Strategy(config)
        strategy.initialize(current_data)
        
        try:
            signal = strategy.generate_signal(current_data, position)
            if signal is None:
                signal_type = "hold"
            else:
                signal_type = signal.signal_type.value if hasattr(signal.signal_type, 'value') else str(signal.signal_type)
        except Exception as e:
            logger.warning(f"信号生成错误: {e}")
            signal_type = "hold"
        
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
                        'shares': shares, 'commission': commission, 'slippage': slippage
                    })
        
        elif signal_type in ("sell", "strong_sell") and position > 0:
            revenue = position * price
            commission = max(revenue * COMMISSION_RATE, 5)
            slippage = revenue * SLIPPAGE_RATE
            stamp_tax = revenue * 0.001
            net = revenue - commission - slippage - stamp_tax
            profit = net - position * avg_cost
            profit_pct = profit / (position * avg_cost) if avg_cost > 0 else 0
            cash += net
            trades.append({
                'date': str(bar.name), 'action': 'SELL', 'price': price,
                'shares': position, 'commission': commission, 'slippage': slippage,
                'stamp_tax': stamp_tax, 'profit': profit, 'profit_pct': profit_pct
            })
            position = 0
            avg_cost = 0.0
        
        portfolio_value = cash + position * price
        equity_curve.append({'date': str(bar.name), 'value': portfolio_value})
    
    final_price = float(data.iloc[-1]['close'])
    final_value = cash + position * final_price
    
    # 计算指标
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
    downside = daily_returns[daily_returns < 0]
    downside_std = downside.std() * np.sqrt(252) if len(downside) > 1 else 0
    sortino = (annual_return - 0.03) / downside_std if downside_std > 0 else 0
    calmar = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
    
    return {
        'total_return': float(total_return),
        'annual_return': float(annual_return),
        'max_drawdown': float(max_drawdown),
        'sharpe_ratio': float(sharpe),
        'sortino_ratio': float(sortino),
        'calmar_ratio': float(calmar),
        'volatility': float(volatility),
        'win_rate': float(win_rate),
        'total_trades': len(trades),
        'buy_trades': len([t for t in trades if t['action'] == 'BUY']),
        'sell_trades': len(sell_trades),
        'win_trades': len(win_trades),
        'lose_trades': len(sell_trades) - len(win_trades),
        'stock_code': stock_code,
        'final_value': float(final_value),
        'trades_detail': trades[:10]
    }

def main():
    logger.info("="*60)
    logger.info("EMA V2 策略回测开始")
    logger.info("="*60)
    
    results = {}
    
    for stock_code, stock_name in STOCKS.items():
        logger.info(f"\n[{stock_code} {stock_name}] 开始回测...")
        data = load_ohlcv(stock_code, START_DATE, END_DATE)
        if data is None or data.empty:
            logger.error(f"  数据加载失败")
            continue
        
        result = run_backtest_for_stock(stock_code, data)
        if result:
            results[stock_code] = result
            logger.info(f"  总收益率: {result['total_return']:.2%}")
            logger.info(f"  年化收益: {result['annual_return']:.2%}")
            logger.info(f"  最大回撤: {result['max_drawdown']:.2%}")
            logger.info(f"  夏普比率: {result['sharpe_ratio']:.2f}")
            logger.info(f"  交易次数: {result['total_trades']}")
    
    # 保存结果
    output_file = 'ema_v2_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    logger.info(f"\n结果已保存到: {output_file}")
    
    # 汇总
    logger.info("\n" + "="*60)
    logger.info("EMA V2 回测汇总")
    logger.info("="*60)
    for code, name in STOCKS.items():
        r = results.get(code, {})
        if r:
            logger.info(f"{code} {name}: 收益{r['total_return']:.2%} 夏普{r['sharpe_ratio']:.2f} 回撤{r['max_drawdown']:.2%}")

if __name__ == '__main__':
    main()
