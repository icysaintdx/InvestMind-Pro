#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EMA V2.2 策略回测验证脚本
对比V2.1和V2.2策略的表现
"""

import sys
import os
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

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

# 测试股票列表（覆盖高、中、低波动）
TEST_STOCKS = {
    "600519": "贵州茅台",   # 低波动
    "601318": "中国平安",   # 低波动
    "000858": "五粮液",     # 中波动
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
        logger.info("[沪深300] 从缓存加载")
        return pd.read_csv(cache_file, index_col='date', parse_dates=True)
    
    try:
        import akshare as ak
        logger.info("[沪深300] 下载数据...")
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
        logger.warning(f"[沪深300] 加载失败: {e}")
        return None


def run_backtest_v22(stock_code: str, stock_name: str) -> Dict[str, Any]:
    """使用EMA V2.2策略执行回测"""
    from strategies.ema_breakout_v2_2 import EMABreakoutV22Strategy
    from strategies.base import StrategyConfig
    
    logger.info(f"\n{'='*60}")
    logger.info(f"EMA V2.2 回测: {stock_code} {stock_name}")
    logger.info(f"{'='*60}")
    
    # 加载数据
    data = load_ohlcv(stock_code, START_DATE, END_DATE)
    if data is None or len(data) < 100:
        logger.error(f"[{stock_code}] 数据不足")
        return None
    
    market_data = load_market_data(START_DATE, END_DATE)
    
    # 初始化策略
    config = StrategyConfig(name="ema_breakout_v2_2", parameters={'symbol': stock_code})
    strategy = EMABreakoutV22Strategy(config)
    strategy.initialize(data, market_data)
    
    # 输出策略信息
    info = strategy.get_strategy_info()
    logger.info(f"策略配置: {info['volatility_description']}")
    logger.info(f"EMA周期: {info['ema_fast']}/{info['ema_slow']}")
    logger.info(f"ATR倍数: {info['atr_multiplier']}")
    logger.info(f"最大仓位: {info['max_position']:.0%}")
    logger.info(f"大盘过滤: {'启用' if info['market_filter_enabled'] else '禁用'} ({info['market_symbol']})")
    
    # 回测循环
    cash = INITIAL_CAPITAL
    position = 0
    avg_cost = 0.0
    trades = []
    equity_curve = [{'date': str(data.index[0]), 'value': INITIAL_CAPITAL}]
    stoploss_count = 0
    highest_value = INITIAL_CAPITAL
    max_drawdown = 0.0
    
    start_idx = 60
    if len(data) <= start_idx:
        return None
    
    for idx in range(start_idx, len(data)):
        current_data = data.iloc[:idx + 1]
        bar = data.iloc[idx]
        price = float(bar['close'])
        
        strategy.initialize(current_data, market_data)
        
        try:
            signal = strategy.generate_signal(current_data, position)
            if signal is None:
                signal_type = "hold"
                reason = "无信号"
            else:
                from strategies.base import SignalType
                signal_type = signal.signal_type.value if hasattr(signal.signal_type, 'value') else str(signal.signal_type)
                reason = getattr(signal, 'reason', '')
        except Exception as e:
            logger.warning(f"信号生成错误: {e}")
            signal_type = "hold"
            reason = "错误"
        
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
                        'reason': reason
                    })
                    logger.info(f"  [买入] {bar.name.date()}: {price:.2f}元 × {shares}股")
        
        # 卖出逻辑
        elif signal_type in ("sell", "strong_sell") and position > 0:
            revenue = position * price
            commission = max(revenue * COMMISSION_RATE, 5)
            slippage = revenue * SLIPPAGE_RATE
            stamp_tax = revenue * 0.001
            net = revenue - commission - slippage - stamp_tax
            profit = net - position * avg_cost
            profit_pct = profit / (position * avg_cost) if avg_cost > 0 else 0
            cash += net
            
            is_stoploss = '止损' in reason
            if is_stoploss:
                stoploss_count += 1
            
            trades.append({
                'date': str(bar.name), 'action': 'SELL', 'price': price,
                'shares': position, 'commission': commission, 'slippage': slippage,
                'stamp_tax': stamp_tax, 'profit': profit, 'profit_pct': profit_pct,
                'is_stoploss': is_stoploss, 'reason': reason
            })
            
            emoji = "📉" if profit < 0 else "📈"
            logger.info(f"  [{emoji}卖出] {bar.name.date()}: {price:.2f}元 | 盈亏: {profit:,.0f}元 ({profit_pct:+.2%})")
            logger.info(f"        原因: {reason[:80]}...")
            position = 0
            avg_cost = 0.0
        
        # 计算权益和回撤
        total_value = cash + position * price
        equity_curve.append({'date': str(bar.name), 'value': total_value})
        
        if total_value > highest_value:
            highest_value = total_value
        drawdown = (highest_value - total_value) / highest_value
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    
    # 计算最终统计
    final_value = cash + position * float(data['close'].iloc[-1])
    total_return = (final_value - INITIAL_CAPITAL) / INITIAL_CAPITAL
    
    # 计算年化收益
    days = (data.index[-1] - data.index[0]).days
    years = max(days / 365.25, 0.1)
    annual_return = (final_value / INITIAL_CAPITAL) ** (1/years) - 1
    
    # 计算夏普比率
    equity_df = pd.DataFrame(equity_curve)
    equity_df['returns'] = equity_df['value'].pct_change()
    volatility = equity_df['returns'].std() * np.sqrt(252)
    sharpe_ratio = (annual_return - 0.03) / volatility if volatility > 0 else 0
    
    # 计算胜率
    if trades:
        sell_trades = [t for t in trades if t['action'] == 'SELL']
        win_trades = [t for t in sell_trades if t.get('profit', 0) > 0]
        win_rate = len(win_trades) / len(sell_trades) if sell_trades else 0
    else:
        win_rate = 0
        sell_trades = []
    
    result = {
        'stock_code': stock_code,
        'stock_name': stock_name,
        'strategy_version': '2.2',
        'volatility_class': info['volatility_description'],
        'atr_multiplier': info['atr_multiplier'],
        'total_return': round(total_return, 4),
        'annual_return': round(annual_return, 4),
        'max_drawdown': round(max_drawdown, 4),
        'sharpe_ratio': round(sharpe_ratio, 4),
        'volatility': round(volatility, 4),
        'win_rate': round(win_rate, 4),
        'total_trades': len(sell_trades),
        'stoploss_count': stoploss_count,
        'final_value': round(final_value, 2),
        'trades': trades,
        'equity_curve': equity_curve,
        'strategy_info': info
    }
    
    logger.info(f"\n{'='*60}")
    logger.info(f"回测结果: {stock_code} {stock_name}")
    logger.info(f"{'='*60}")
    logger.info(f"总收益率: {total_return:.2%}")
    logger.info(f"年化收益: {annual_return:.2%}")
    logger.info(f"最大回撤: {max_drawdown:.2%}")
    logger.info(f"夏普比率: {sharpe_ratio:.3f}")
    logger.info(f"胜率: {win_rate:.2%}")
    logger.info(f"交易次数: {len(sell_trades)}")
    logger.info(f"止损次数: {stoploss_count}")
    logger.info(f"期末资金: {final_value:,.2f}")
    
    return result


def compare_with_v21(stock_code: str, v22_result: Dict[str, Any]) -> Dict[str, Any]:
    """对比V2.1和V2.2的结果"""
    # 加载V2.1结果
    v21_file = RESULTS_DIR / f"ema_v2_{stock_code}_optimized_results_20260227_083837.json"
    
    comparison = {
        'stock_code': stock_code,
        'stock_name': v22_result['stock_name'],
        'v2_1': {},
        'v2_2': {
            'total_return': v22_result['total_return'],
            'annual_return': v22_result['annual_return'],
            'max_drawdown': v22_result['max_drawdown'],
            'sharpe_ratio': v22_result['sharpe_ratio'],
            'win_rate': v22_result['win_rate'],
            'total_trades': v22_result['total_trades'],
            'atr_multiplier': v22_result['atr_multiplier']
        },
        'improvement': {}
    }
    
    if v21_file.exists():
        with open(v21_file, 'r', encoding='utf-8') as f:
            v21_data = json.load(f)
        
        comparison['v2_1'] = {
            'total_return': v21_data.get('total_return', 0),
            'annual_return': v21_data.get('annual_return', 0),
            'max_drawdown': v21_data.get('max_drawdown', 0),
            'sharpe_ratio': v21_data.get('sharpe_ratio', 0),
            'win_rate': v21_data.get('win_rate', 0),
            'total_trades': v21_data.get('total_trades', 0)
        }
        
        # 计算改进幅度
        comparison['improvement'] = {
            'return_diff': round(v22_result['total_return'] - comparison['v2_1']['total_return'], 4),
            'sharpe_diff': round(v22_result['sharpe_ratio'] - comparison['v2_1']['sharpe_ratio'], 4),
            'drawdown_diff': round(v22_result['max_drawdown'] - comparison['v2_1']['max_drawdown'], 4),
            'winrate_diff': round(v22_result['win_rate'] - comparison['v2_1']['win_rate'], 4)
        }
    else:
        comparison['v2_1'] = {'error': 'V2.1结果文件不存在'}
    
    return comparison


def main():
    """主函数"""
    logger.info("="*70)
    logger.info("EMA V2.2 策略回测验证")
    logger.info("="*70)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    all_results = {}
    all_comparisons = {}
    
    for stock_code, stock_name in TEST_STOCKS.items():
        # 运行V2.2回测
        result = run_backtest_v22(stock_code, stock_name)
        if result:
            all_results[stock_code] = result
            
            # 对比V2.1
            comparison = compare_with_v21(stock_code, result)
            all_comparisons[stock_code] = comparison
            
            # 保存单个结果
            result_file = RESULTS_DIR / f"ema_v2_2_{stock_code}_results_{timestamp}.json"
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            logger.info(f"结果已保存: {result_file}")
        
        time.sleep(1)  # 避免请求过快
    
    # 保存汇总结果
    batch_results = {
        'timestamp': timestamp,
        'strategy_version': '2.2',
        'stocks': all_results,
        'comparisons': all_comparisons
    }
    
    batch_file = RESULTS_DIR / f"ema_v2_2_batch_results_{timestamp}.json"
    with open(batch_file, 'w', encoding='utf-8') as f:
        json.dump(batch_results, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n{'='*70}")
    logger.info("EMA V2.2 回测完成")
    logger.info(f"汇总结果: {batch_file}")
    logger.info(f"测试股票数: {len(all_results)}")
    logger.info("="*70)
    
    # 生成对比报告
    logger.info("\n" + "="*70)
    logger.info("V2.1 vs V2.2 对比结果")
    logger.info("="*70)
    for code, comp in all_comparisons.items():
        logger.info(f"\n{code} {comp['stock_name']}:")
        if 'error' not in comp['v2_1']:
            logger.info(f"  收益率: V2.1={comp['v2_1']['total_return']:+.2%} -> V2.2={comp['v2_2']['total_return']:+.2%} ({comp['improvement']['return_diff']:+.2%})")
            logger.info(f"  夏普比: V2.1={comp['v2_1']['sharpe_ratio']:.3f} -> V2.2={comp['v2_2']['sharpe_ratio']:.3f} ({comp['improvement']['sharpe_diff']:+.3f})")
            logger.info(f"  最大回撤: V2.1={comp['v2_1']['max_drawdown']:.2%} -> V2.2={comp['v2_2']['max_drawdown']:.2%} ({comp['improvement']['drawdown_diff']:+.2%})")
    
    return batch_results


if __name__ == "__main__":
    results = main()
