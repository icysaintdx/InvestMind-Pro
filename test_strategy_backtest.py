"""
策略回测测试脚本
测试10个策略的回测性能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from backend.backtest.strategy_backtester import StrategyBacktester
from backend.backtest.backtest_reporter import BacktestReporter

# 导入所有策略
from backend.strategies.vegas_adx import VegasADXStrategy
from backend.strategies.ema_breakout import EMABreakoutStrategy
from backend.strategies.trident import TridentStrategy
from backend.strategies.macd_crossover import MACDCrossoverStrategy
from backend.strategies.bollinger_breakout import BollingerBreakoutStrategy
from backend.strategies.sentiment_resonance import SentimentResonanceStrategy
from backend.strategies.debate_weighted import DebateWeightedStrategy
from backend.strategies.turtle_trading import TurtleTradingStrategy
from backend.strategies.limit_up_trading import LimitUpTradingStrategy
from backend.strategies.volume_price_surge import VolumePriceSurgeStrategy


def generate_sample_data(days: int = 250) -> pd.DataFrame:
    """
    生成模拟股票数据
    
    Args:
        days: 天数
        
    Returns:
        DataFrame with OHLCV data
    """
    np.random.seed(42)
    
    # 生成日期
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    # 生成价格数据（带趋势）
    base_price = 100
    trend = np.linspace(0, 20, days)  # 上升趋势
    noise = np.random.randn(days) * 2  # 随机波动
    close_prices = base_price + trend + noise
    
    # 生成OHLC
    data = pd.DataFrame({
        'open': close_prices + np.random.randn(days) * 0.5,
        'high': close_prices + np.abs(np.random.randn(days) * 1.5),
        'low': close_prices - np.abs(np.random.randn(days) * 1.5),
        'close': close_prices,
        'volume': np.random.randint(1000000, 5000000, days)
    }, index=dates)
    
    # 确保high是最高，low是最低
    data['high'] = data[['open', 'high', 'close']].max(axis=1)
    data['low'] = data[['open', 'low', 'close']].min(axis=1)
    
    return data


def test_single_strategy():
    """测试单个策略"""
    print("=" * 80)
    print("测试1: 单策略回测")
    print("=" * 80)
    
    # 生成数据
    data = generate_sample_data(250)
    print(f"\n生成了 {len(data)} 天的模拟数据")
    print(f"价格范围: {data['close'].min():.2f} - {data['close'].max():.2f}")
    
    # 创建回测引擎
    backtester = StrategyBacktester(initial_capital=100000)
    
    # 测试Vegas+ADX策略
    strategy = VegasADXStrategy()
    print(f"\n回测策略: {strategy.name}")
    
    result = backtester.run_backtest(strategy, data)
    
    if result["success"]:
        print("\n✅ 回测成功！")
        print(f"\n性能指标:")
        perf = result["performance"]
        print(f"  总收益: ¥{perf['total_return']:,.2f}")
        print(f"  收益率: {perf['total_return_pct']:.2%}")
        print(f"  胜率: {perf['win_rate']:.2%}")
        print(f"  交易次数: {perf['total_trades']}")
        print(f"  夏普比率: {perf['sharpe_ratio']:.2f}")
        print(f"  最大回撤: {perf['max_drawdown']:.2%}")
        
        # 生成报告
        reporter = BacktestReporter()
        report = reporter.generate_single_strategy_report(result)
        
        # 保存报告
        report_file = "docs/回测报告-Vegas+ADX.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n📄 报告已保存: {report_file}")
    else:
        print(f"\n❌ 回测失败: {result.get('error')}")


def test_all_strategies():
    """测试所有10个策略"""
    print("\n" + "=" * 80)
    print("测试2: 全策略对比回测")
    print("=" * 80)
    
    # 生成数据
    data = generate_sample_data(250)
    print(f"\n生成了 {len(data)} 天的模拟数据")
    
    # 创建所有策略实例
    strategies = [
        VegasADXStrategy(),
        EMABreakoutStrategy(),
        TridentStrategy(),
        MACDCrossoverStrategy(),
        BollingerBreakoutStrategy(),
        # AI策略需要智能体数据，暂时跳过
        # SentimentResonanceStrategy(),
        # DebateWeightedStrategy(),
        TurtleTradingStrategy(system=2),  # 长期系统
        # 涨停板和量价齐升需要特殊数据，暂时跳过
        # LimitUpTradingStrategy(),
        # VolumePriceSurgeStrategy(),
    ]
    
    print(f"\n准备回测 {len(strategies)} 个策略...")
    
    # 创建回测引擎
    backtester = StrategyBacktester(initial_capital=100000)
    
    # 对比回测
    comparison_result = backtester.compare_strategies(strategies, data)
    
    if comparison_result["success"]:
        print("\n✅ 对比回测成功！")
        
        comparison = comparison_result["comparison"]
        
        print(f"\n🏆 最佳策略:")
        print(f"  最高收益: {comparison['best_return']['strategy_name']} ({comparison['best_return']['total_return_pct']:.2%})")
        print(f"  最高胜率: {comparison['best_win_rate']['strategy_name']} ({comparison['best_win_rate']['win_rate']:.2%})")
        print(f"  最高夏普: {comparison['best_sharpe']['strategy_name']} ({comparison['best_sharpe']['sharpe_ratio']:.2f})")
        
        print(f"\n📊 收益率排名:")
        for i, s in enumerate(comparison['ranking_by_return'][:5], 1):
            print(f"  {i}. {s['strategy_name']}: {s['total_return_pct']:.2%} (胜率{s['win_rate']:.2%})")
        
        # 生成对比报告
        reporter = BacktestReporter()
        report = reporter.generate_comparison_report(comparison_result)
        
        # 保存报告
        report_file = "docs/策略对比回测报告.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n📄 对比报告已保存: {report_file}")
    else:
        print(f"\n❌ 对比回测失败: {comparison_result.get('error')}")


def test_strategy_with_different_periods():
    """测试不同周期的策略表现"""
    print("\n" + "=" * 80)
    print("测试3: 不同周期策略表现")
    print("=" * 80)
    
    # 生成长期数据
    data = generate_sample_data(500)
    
    strategy = TridentStrategy()
    backtester = StrategyBacktester(initial_capital=100000)
    
    periods = [
        ("短期", 60),
        ("中期", 120),
        ("长期", 250)
    ]
    
    print(f"\n测试策略: {strategy.name}")
    print(f"\n不同周期表现:")
    
    for period_name, days in periods:
        period_data = data.tail(days)
        result = backtester.run_backtest(strategy, period_data)
        
        if result["success"]:
            perf = result["performance"]
            print(f"\n  {period_name}({days}天):")
            print(f"    收益率: {perf['total_return_pct']:.2%}")
            print(f"    胜率: {perf['win_rate']:.2%}")
            print(f"    交易次数: {perf['total_trades']}")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("InvestMind-Pro 策略回测系统测试")
    print("=" * 80)
    
    try:
        # 测试1: 单策略回测
        test_single_strategy()
        
        # 测试2: 全策略对比
        test_all_strategies()
        
        # 测试3: 不同周期
        test_strategy_with_different_periods()
        
        print("\n" + "=" * 80)
        print("✅ 所有测试完成！")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
