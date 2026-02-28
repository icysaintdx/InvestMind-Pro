#!/usr/bin/env python3
"""
17策略批量回测执行脚本

对OPTIMIZED_PARAMS中的22只股票分别执行：
1. 纯技术信号回测 (without情绪)
2. 混合信号回测 (with情绪)

使用策略工厂(strategy_factory.py)中的17个策略
"""

import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
import warnings
import time
import importlib.util
warnings.filterwarnings('ignore')

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'strategies'))

# 动态导入策略工厂
def load_strategy_factory():
    """动态加载策略工厂模块"""
    factory_path = PROJECT_ROOT / 'strategies' / 'strategy_factory.py'
    spec = importlib.util.spec_from_file_location('strategy_factory', factory_path)
    factory_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(factory_module)
    return factory_module

# 动态导入ema_v2
def load_ema_v2():
    """动态加载EMA V2模块"""
    ema_path = PROJECT_ROOT / 'strategies' / 'ema_v2.py'
    spec = importlib.util.spec_from_file_location('ema_v2', ema_path)
    ema_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ema_module)
    return ema_module

try:
    factory_mod = load_strategy_factory()
    StrategyFactory = factory_mod.StrategyFactory
    STRATEGY_REGISTRY = factory_mod.STRATEGY_REGISTRY
    
    ema_mod = load_ema_v2()
    EMAV2Strategy = ema_mod.EMAV2Strategy
    BacktestResult = ema_mod.BacktestResult
except Exception as e:
    print(f"导入错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 优化后的22只股票参数
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
    '600887': {'name': '伊利股份', 'fast_ema': 15, 'slow_ema': 40, 'atr_period': 14, 'atr_multiplier': 3.0, 'market_filter': True},
    '600900': {'name': '长江电力', 'fast_ema': 12, 'slow_ema': 20, 'atr_period': 14, 'atr_multiplier': 1.0, 'market_filter': True},
    '601012': {'name': '隆基绿能', 'fast_ema': 12, 'slow_ema': 18, 'atr_period': 14, 'atr_multiplier': 1.5, 'market_filter': True},
    '601288': {'name': '农业银行', 'fast_ema': 12, 'slow_ema': 30, 'atr_period': 14, 'atr_multiplier': 1.0, 'market_filter': True},
    '601318': {'name': '中国平安', 'fast_ema': 10, 'slow_ema': 50, 'atr_period': 14, 'atr_multiplier': 1.5, 'market_filter': True},
    '601888': {'name': '中国中免', 'fast_ema': 15, 'slow_ema': 40, 'atr_period': 14, 'atr_multiplier': 2.0, 'market_filter': True},
}

# 回测配置
BACKTEST_CONFIG = {
    'start_date': '2020-01-01',
    'end_date': '2026-02-27',
    'initial_capital': 1000000.0,  # 100万
}


def generate_sample_data(symbol: str, days: int = 1500) -> pd.DataFrame:
    """生成模拟股票数据 (用于测试)"""
    np.random.seed(hash(symbol) % 2**32)
    
    end_date = datetime.now()
    dates = pd.date_range(end=end_date, periods=days, freq='B')
    actual_days = len(dates)
    
    # 生成价格序列 (随机游走)
    returns = np.random.normal(0.0003, 0.015, actual_days)
    price = 100 * np.exp(np.cumsum(returns))
    
    # 生成OHLC
    data = pd.DataFrame(index=dates)
    data['close'] = price
    data['high'] = price * (1 + np.abs(np.random.normal(0, 0.012, actual_days)))
    data['low'] = price * (1 - np.abs(np.random.normal(0, 0.012, actual_days)))
    data['open'] = price * (1 + np.random.normal(0, 0.005, actual_days))
    data['volume'] = np.random.randint(1000000, 10000000, actual_days)
    
    data.attrs['symbol'] = symbol
    return data


def load_stock_data(symbol: str, data_dir: Path, start_date: str = None, end_date: str = None) -> Optional[pd.DataFrame]:
    """加载股票数据并过滤日期范围 - 优先本地，其次模拟"""
    # 尝试多个可能的数据路径
    possible_paths = [
        data_dir / f"{symbol}.csv",
        PROJECT_ROOT / 'data' / f"{symbol}.csv",
        PROJECT_ROOT / 'backend' / 'data' / 'backtest_cache' / f"{symbol}_20200101_20241231.csv",
    ]
    
    df = None
    for csv_path in possible_paths:
        if csv_path.exists():
            try:
                df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
                print(f"    [数据] 从 {csv_path} 加载")
                break
            except Exception as e:
                continue
    
    # 如果没有本地数据，生成模拟数据
    if df is None:
        print(f"    [数据] 使用模拟数据生成")
        df = generate_sample_data(symbol)
    
    # 标准化列名
    df.columns = [c.lower() for c in df.columns]
    if 'close' not in df.columns:
        col_mapping = {
            '收盘价': 'close', '开盘价': 'open', '最高价': 'high', 
            '最低价': 'low', '成交量': 'volume', '成交额': 'amount'
        }
        df.rename(columns={k: v for k, v in col_mapping.items() if k in df.columns}, inplace=True)
    
    # 确保必要的列存在
    required_cols = ['open', 'high', 'low', 'close', 'volume']
    for col in required_cols:
        if col not in df.columns:
            if col == 'volume':
                df[col] = 1000000  # 默认成交量
            else:
                df[col] = df['close']  # 使用收盘价填充
    
    # 日期过滤
    if start_date:
        df = df[df.index >= start_date]
    if end_date:
        df = df[df.index <= end_date]
    
    df.attrs['symbol'] = symbol
    return df


def load_market_data(data_dir: Path, start_date: str = None, end_date: str = None) -> Optional[pd.DataFrame]:
    """加载沪深300指数数据"""
    market_data = load_stock_data('000300', data_dir, start_date, end_date)
    if market_data is None or len(market_data) < 100:
        # 生成模拟大盘数据
        market_data = generate_sample_data('000300')
        if start_date:
            market_data = market_data[market_data.index >= start_date]
        if end_date:
            market_data = market_data[market_data.index <= end_date]
    return market_data


def run_strategy_backtest(
    strategy_name: str, 
    symbol: str, 
    stock_data: pd.DataFrame, 
    market_data: pd.DataFrame,
    use_sentiment: bool = False,
    initial_capital: float = 1000000.0
) -> Optional[Dict]:
    """
    执行单个策略回测
    
    Args:
        strategy_name: 策略名称
        symbol: 股票代码
        stock_data: 股票数据
        market_data: 大盘数据
        use_sentiment: 是否使用情绪增强
        initial_capital: 初始资金
    
    Returns:
        回测结果字典
    """
    try:
        # 创建策略实例
        strategy = StrategyFactory.create_strategy(strategy_name, use_sentiment=use_sentiment)
        
        # 执行回测
        if hasattr(strategy, 'run_backtest'):
            result = strategy.run_backtest(stock_data, market_data, initial_capital)
        else:
            # 如果没有run_backtest方法，尝试generate_signals
            if hasattr(strategy, 'generate_signals'):
                data = strategy.generate_signals(stock_data)
                result = _execute_backtest(data, symbol, initial_capital)
            else:
                return None
        
        return {
            'symbol': symbol,
            'strategy': strategy_name,
            'use_sentiment': use_sentiment,
            'total_return': result.total_return if hasattr(result, 'total_return') else result.get('total_return', 0),
            'win_rate': result.win_rate if hasattr(result, 'win_rate') else result.get('win_rate', 0),
            'total_trades': result.total_trades if hasattr(result, 'total_trades') else result.get('total_trades', 0),
            'max_drawdown': result.max_drawdown if hasattr(result, 'max_drawdown') else result.get('max_drawdown', 0),
            'sharpe_ratio': result.sharpe_ratio if hasattr(result, 'sharpe_ratio') else result.get('sharpe_ratio', 0),
            'trades': result.trades if hasattr(result, 'trades') else result.get('trades', []),
        }
    except Exception as e:
        print(f"  ⚠️  {strategy_name} {'with情绪' if use_sentiment else '纯技术'} 回测失败: {str(e)[:50]}")
        return None


def _execute_backtest(data: pd.DataFrame, symbol: str, initial_capital: float) -> Dict:
    """通用回测执行逻辑"""
    position = 0
    entry_price = 0.0
    entry_date = None
    trades = []
    equity_curve = [initial_capital]
    current_capital = initial_capital
    
    for i in range(1, len(data)):
        date = data.index[i]
        price = data['close'].iloc[i]
        
        buy_signal = data.get('buy_signal', pd.Series([False]*len(data))).iloc[i]
        sell_signal = data.get('sell_signal', pd.Series([False]*len(data))).iloc[i]
        stop_loss = data.get('stop_loss', pd.Series([price*0.9]*len(data))).iloc[i]
        
        if position == 0 and buy_signal:
            position = 1
            entry_price = price
            entry_date = date
            shares = current_capital / price
            
        elif position == 1:
            exit_reason = None
            if sell_signal:
                exit_reason = "signal"
            elif price < stop_loss:
                exit_reason = "stop_loss"
            
            if exit_reason:
                pnl = (price - entry_price) * shares
                pnl_pct = (price / entry_price - 1) * 100
                trades.append({
                    'entry_date': entry_date, 'exit_date': date,
                    'entry_price': entry_price, 'exit_price': price,
                    'pnl': pnl, 'pnl_pct': pnl_pct, 'exit_reason': exit_reason
                })
                current_capital += pnl
                position = 0
        
        equity_curve.append(current_capital)
    
    # 计算指标
    total_return = (current_capital - initial_capital) / initial_capital * 100
    win_rate = len([t for t in trades if t['pnl'] > 0]) / len(trades) * 100 if trades else 0
    
    equity_series = pd.Series(equity_curve)
    rolling_max = equity_series.expanding().max()
    drawdown = (equity_series - rolling_max) / rolling_max * 100
    max_drawdown = drawdown.min() if len(drawdown) > 0 else 0
    
    returns = equity_series.pct_change().dropna()
    sharpe = (returns.mean() / returns.std() * np.sqrt(252)) if returns.std() != 0 and len(returns) > 1 else 0
    
    return {
        'symbol': symbol,
        'total_return': total_return,
        'win_rate': win_rate,
        'total_trades': len(trades),
        'max_drawdown': max_drawdown,
        'sharpe_ratio': sharpe,
        'trades': trades,
    }


def run_all_backtests(
    symbols: List[str],
    strategies: List[str],
    data_dir: Path,
    output_dir: Path
) -> Dict:
    """
    执行所有策略和所有股票的批量回测
    
    Returns:
        包含所有回测结果的字典
    """
    all_results = []
    summary_by_strategy = {}
    summary_by_stock = {}
    
    start_date = BACKTEST_CONFIG['start_date']
    end_date = BACKTEST_CONFIG['end_date']
    initial_capital = BACKTEST_CONFIG['initial_capital']
    
    total_tasks = len(symbols) * len(strategies) * 2  # 每只股票每个策略两种模式
    completed = 0
    
    print(f"\n{'='*80}")
    print(f"🚀 开始17策略批量回测")
    print(f"{'='*80}")
    print(f"股票数量: {len(symbols)}")
    print(f"策略数量: {len(strategies)}")
    print(f"回测模式: 纯技术信号 + 混合信号(with情绪)")
    print(f"回测期间: {start_date} ~ {end_date}")
    print(f"初始资金: {initial_capital:,.0f}元")
    print(f"总任务数: {total_tasks}")
    print(f"{'='*80}\n")
    
    start_time = time.time()
    
    for symbol in symbols:
        stock_name = OPTIMIZED_PARAMS.get(symbol, {}).get('name', symbol)
        print(f"\n📊 正在回测: {symbol} - {stock_name}")
        print(f"{'-'*60}")
        
        # 加载数据
        stock_data = load_stock_data(symbol, data_dir, start_date, end_date)
        if stock_data is None or len(stock_data) < 100:
            print(f"  ⚠️ 数据不足，跳过")
            continue
        
        market_data = load_market_data(data_dir, start_date, end_date)
        
        stock_results = []
        
        for strategy_name in strategies:
            strategy_info = STRATEGY_REGISTRY.get(strategy_name, {})
            category = getattr(strategy_info, 'category', 'unknown')
            
            # 1. 纯技术信号回测
            completed += 1
            print(f"  [{completed}/{total_tasks}] {strategy_name} (纯技术)...", end=' ')
            result_pure = run_strategy_backtest(
                strategy_name, symbol, stock_data, market_data, 
                use_sentiment=False, initial_capital=initial_capital
            )
            
            if result_pure:
                print(f"✓ 收益: {result_pure['total_return']:+.2f}%")
                all_results.append(result_pure)
                stock_results.append(result_pure)
            else:
                print(f"✗ 失败")
            
            # 2. 混合信号回测 (带情绪)
            # 情绪策略本身已经有情绪，不需要再次增强
            if category != 'sentiment':
                completed += 1
                print(f"  [{completed}/{total_tasks}] {strategy_name} (with情绪)...", end=' ')
                result_mixed = run_strategy_backtest(
                    strategy_name, symbol, stock_data, market_data, 
                    use_sentiment=True, initial_capital=initial_capital
                )
                
                if result_mixed:
                    print(f"✓ 收益: {result_mixed['total_return']:+.2f}%")
                    all_results.append(result_mixed)
                    stock_results.append(result_mixed)
                else:
                    print(f"✗ 失败")
            else:
                completed += 1
                print(f"  [{completed}/{total_tasks}] {strategy_name} (情绪策略，跳过重复回测)")
        
        summary_by_stock[symbol] = {
            'name': stock_name,
            'results': stock_results
        }
    
    elapsed = time.time() - start_time
    print(f"\n{'='*80}")
    print(f"✅ 批量回测完成! 耗时: {elapsed:.1f}秒")
    print(f"{'='*80}\n")
    
    return {
        'all_results': all_results,
        'by_stock': summary_by_stock,
        'config': BACKTEST_CONFIG,
        'elapsed_time': elapsed
    }


def generate_comparison_report(results: Dict, output_dir: Path) -> Path:
    """
    生成对比报告
    
    Returns:
        报告文件路径
    """
    all_results = results['all_results']
    by_stock = results['by_stock']
    
    # 创建报告目录
    report_dir = output_dir / f"batch_17strategies_{datetime.now().strftime('%Y%m%d')}"
    report_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. 保存原始JSON数据
    json_file = report_dir / "detailed_results.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2, default=str)
    
    # 2. 生成Markdown对比报告
    md_file = report_dir / "comparison_report.md"
    
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write("# 📊 17策略批量回测对比报告\n\n")
        f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**回测期间**: {BACKTEST_CONFIG['start_date']} ~ {BACKTEST_CONFIG['end_date']}\n\n")
        f.write(f"**初始资金**: {BACKTEST_CONFIG['initial_capital']:,.0f}元\n\n")
        f.write(f"**股票数量**: {len(by_stock)}只\n\n")
        f.write(f"**策略数量**: 17个\n\n")
        f.write("---\n\n")
        
        # 汇总统计
        f.write("## 📈 整体汇总统计\n\n")
        
        pure_results = [r for r in all_results if not r['use_sentiment']]
        mixed_results = [r for r in all_results if r['use_sentiment']]
        
        if pure_results:
            pure_returns = [r['total_return'] for r in pure_results]
            f.write(f"### 纯技术信号回测\n")
            f.write(f"- 总回测次数: {len(pure_results)}\n")
            f.write(f"- 平均收益率: {np.mean(pure_returns):+.2f}%\n")
            f.write(f"- 中位数收益率: {np.median(pure_returns):+.2f}%\n")
            f.write(f"- 最佳收益: {max(pure_returns):+.2f}%\n")
            f.write(f"- 最差收益: {min(pure_returns):+.2f}%\n")
            f.write(f"- 正收益比例: {sum(1 for r in pure_returns if r > 0)/len(pure_returns)*100:.1f}%\n\n")
        
        if mixed_results:
            mixed_returns = [r['total_return'] for r in mixed_results]
            f.write(f"### 混合信号回测(with情绪)\n")
            f.write(f"- 总回测次数: {len(mixed_results)}\n")
            f.write(f"- 平均收益率: {np.mean(mixed_returns):+.2f}%\n")
            f.write(f"- 中位数收益率: {np.median(mixed_returns):+.2f}%\n")
            f.write(f"- 最佳收益: {max(mixed_returns):+.2f}%\n")
            f.write(f"- 最差收益: {min(mixed_returns):+.2f}%\n")
            f.write(f"- 正收益比例: {sum(1 for r in mixed_returns if r > 0)/len(mixed_returns)*100:.1f}%\n\n")
        
        # 按股票分类统计
        f.write("## 📋 按股票分类结果\n\n")
        f.write("| 股票代码 | 股票名称 | 策略 | 模式 | 收益率 | 胜率 | 交易次数 | 最大回撤 | Sharpe |\n")
        f.write("|---------|---------|------|------|--------|------|---------|---------|--------|\n")
        
        for symbol, data in sorted(by_stock.items()):
            name = data['name']
            for r in sorted(data['results'], key=lambda x: x['strategy']):
                mode = "with情绪" if r['use_sentiment'] else "纯技术"
                f.write(f"| {symbol} | {name} | {r['strategy']} | {mode} | ")
                f.write(f"{r['total_return']:+.2f}% | {r['win_rate']:.1f}% | {r['total_trades']} | ")
                f.write(f"{r['max_drawdown']:.2f}% | {r['sharpe_ratio']:.2f} |\n")
        
        f.write("\n")
        
        # 按策略分类统计
        f.write("## 📊 按策略分类统计\n\n")
        
        from collections import defaultdict
        strategy_stats = defaultdict(lambda: {'pure': [], 'mixed': []})
        
        for r in all_results:
            key = 'mixed' if r['use_sentiment'] else 'pure'
            strategy_stats[r['strategy']][key].append(r['total_return'])
        
        f.write("| 策略名称 | 类别 | 纯技术-平均收益 | 纯技术-胜率 | with情绪-平均收益 | with情绪-胜率 | 情绪增强效果 |\n")
        f.write("|---------|------|----------------|------------|------------------|--------------|-------------|\n")
        
        for strategy_name in sorted(strategy_stats.keys()):
            stats = strategy_stats[strategy_name]
            info = STRATEGY_REGISTRY.get(strategy_name)
            category = info.category if info else 'unknown'
            
            pure_avg = np.mean(stats['pure']) if stats['pure'] else 0
            mixed_avg = np.mean(stats['mixed']) if stats['mixed'] else 0
            
            pure_win = sum(1 for r in stats['pure'] if r > 0) / len(stats['pure']) * 100 if stats['pure'] else 0
            mixed_win = sum(1 for r in stats['mixed'] if r > 0) / len(stats['mixed']) * 100 if stats['mixed'] else 0
            
            enhancement = mixed_avg - pure_avg if stats['mixed'] else 0
            
            f.write(f"| {strategy_name} | {category} | {pure_avg:+.2f}% | {pure_win:.1f}% | ")
            f.write(f"{mixed_avg:+.2f}% | {mixed_win:.1f}% | {enhancement:+.2f}% |\n")
        
        f.write("\n")
        
        # 最佳/最差排名
        f.write("## 🏆 最佳表现排名\n\n")
        f.write("### Top 10 最佳组合 (纯技术)\n\n")
        pure_sorted = sorted([r for r in all_results if not r['use_sentiment']], 
                            key=lambda x: x['total_return'], reverse=True)[:10]
        
        for i, r in enumerate(pure_sorted, 1):
            name = OPTIMIZED_PARAMS.get(r['symbol'], {}).get('name', r['symbol'])
            f.write(f"{i}. **{r['symbol']}** ({name}) - {r['strategy']}: {r['total_return']:+.2f}%\n")
        
        f.write("\n### Top 10 最佳组合 (with情绪)\n\n")
        mixed_sorted = sorted([r for r in all_results if r['use_sentiment']], 
                             key=lambda x: x['total_return'], reverse=True)[:10]
        
        for i, r in enumerate(mixed_sorted, 1):
            name = OPTIMIZED_PARAMS.get(r['symbol'], {}).get('name', r['symbol'])
            f.write(f"{i}. **{r['symbol']}** ({name}) - {r['strategy']}: {r['total_return']:+.2f}%\n")
        
        f.write("\n---\n\n")
        f.write(f"*报告生成耗时: {results['elapsed_time']:.1f}秒*\n")
    
    print(f"📄 对比报告已保存: {md_file}")
    print(f"📄 详细数据已保存: {json_file}")
    
    return report_dir


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='17策略批量回测')
    parser.add_argument('--symbols', '-s', type=str, help='指定股票列表(逗号分隔)，默认使用全部22只')
    parser.add_argument('--strategies', '-t', type=str, help='指定策略列表(逗号分隔)，默认使用全部17个')
    parser.add_argument('--quick', '-q', action='store_true', help='快速模式(仅回测前3只股票)')
    
    args = parser.parse_args()
    
    # 设置路径
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / 'data'
    output_dir = base_dir / 'results'
    output_dir.mkdir(exist_ok=True)
    
    # 确定股票列表
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(',')]
    elif args.quick:
        symbols = list(OPTIMIZED_PARAMS.keys())[:3]
        print(f"⚡ 快速模式: 仅回测前3只股票 {symbols}")
    else:
        symbols = list(OPTIMIZED_PARAMS.keys())
    
    # 确定策略列表
    if args.strategies:
        strategies = [s.strip() for s in args.strategies.split(',')]
    else:
        strategies = StrategyFactory.get_all_strategies()
    
    print(f"\n🎯 回测配置:")
    print(f"   股票: {len(symbols)}只")
    print(f"   策略: {len(strategies)}个 ({', '.join(strategies[:5])}{'...' if len(strategies) > 5 else ''})")
    print(f"   数据目录: {data_dir}")
    print(f"   输出目录: {output_dir}")
    
    # 执行批量回测
    results = run_all_backtests(symbols, strategies, data_dir, output_dir)
    
    # 生成对比报告
    if results['all_results']:
        report_dir = generate_comparison_report(results, output_dir)
        
        print(f"\n{'='*80}")
        print(f"✅ 批量回测完成!")
        print(f"📁 报告目录: {report_dir}")
        print(f"{'='*80}\n")
    else:
        print(f"\n⚠️ 没有生成任何回测结果，请检查数据文件是否存在")


if __name__ == '__main__':
    main()
