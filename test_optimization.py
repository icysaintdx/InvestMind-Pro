"""
参数优化和组合策略测试脚本
测试参数优化系统和组合策略功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 导入优化器
from backend.backtest.parameter_optimizer import ParameterOptimizer, PortfolioOptimizer
from backend.backtest.engine import BacktestEngine, BacktestConfig

# 导入策略
from backend.strategies.base import StrategyConfig
from backend.strategies.vegas_adx import VegasADXStrategy
from backend.strategies.trident import TridentStrategy
from backend.strategies.macd_crossover import MACDCrossoverStrategy


def generate_sample_data(days: int = 250) -> pd.DataFrame:
    """生成模拟股票数据"""
    np.random.seed(42)
    
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    base_price = 100
    trend = np.linspace(0, 20, days)
    noise = np.random.randn(days) * 2
    close_prices = base_price + trend + noise
    
    data = pd.DataFrame({
        'open': close_prices + np.random.randn(days) * 0.5,
        'high': close_prices + np.abs(np.random.randn(days) * 1.5),
        'low': close_prices - np.abs(np.random.randn(days) * 1.5),
        'close': close_prices,
        'volume': np.random.randint(1000000, 5000000, days)
    }, index=dates)
    
    data['high'] = data[['open', 'high', 'close']].max(axis=1)
    data['low'] = data[['open', 'low', 'close']].min(axis=1)
    
    return data


def test_grid_search():
    """测试网格搜索优化"""
    print("=" * 80)
    print("测试1: 网格搜索参数优化")
    print("=" * 80)
    
    # 生成数据
    data = generate_sample_data(250)
    print(f"\n✅ 生成了 {len(data)} 天的模拟数据")
    
    # 定义参数网格（简化版，实际可以更复杂）
    param_grid = {
        'ema_fast': [10, 12, 15],
        'adx_threshold': [25, 30, 35]
    }
    
    print(f"\n📊 参数网格:")
    for param, values in param_grid.items():
        print(f"   {param}: {values}")
    
    # 创建优化器
    optimizer = ParameterOptimizer(initial_capital=100000)
    
    print(f"\n🔍 开始网格搜索优化...")
    
    try:
        # 运行优化
        result = optimizer.grid_search(
            strategy_class=VegasADXStrategy,
            param_grid=param_grid,
            data=data,
            metric="sharpe_ratio",
            max_combinations=10
        )
        
        print(f"\n✅ 优化完成！")
        print(f"\n🏆 最优参数:")
        for param, value in result["best_params"].items():
            print(f"   {param}: {value}")
        
        print(f"\n📈 最优表现:")
        print(f"   夏普比率: {result['best_score']:.4f}")
        print(f"   测试组合数: {result['total_tested']}")
        
        # 生成报告
        report = optimizer.generate_optimization_report(result, "Vegas+ADX")
        
        # 保存报告
        report_file = "docs/参数优化报告-Vegas+ADX.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n📄 优化报告已保存: {report_file}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ 优化失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_portfolio_optimization():
    """测试组合策略优化"""
    print("\n" + "=" * 80)
    print("测试2: 组合策略优化")
    print("=" * 80)
    
    # 生成数据
    data = generate_sample_data(250)
    
    # 创建策略列表
    strategies = [
        ("Vegas+ADX", VegasADXStrategy(StrategyConfig(name="Vegas+ADX"))),
        ("三叉戟", TridentStrategy(StrategyConfig(name="三叉戟"))),
        ("MACD交叉", MACDCrossoverStrategy(StrategyConfig(name="MACD交叉"))),
    ]
    
    print(f"\n准备优化 {len(strategies)} 个策略的组合...")
    
    # 创建组合优化器
    portfolio_optimizer = PortfolioOptimizer(initial_capital=100000)
    
    try:
        # 运行优化
        result = portfolio_optimizer.optimize_weights(
            strategies=strategies,
            data=data,
            objective="sharpe_ratio"
        )
        
        print(f"\n✅ 组合优化完成！")
        print(f"\n🏆 最优权重配置:")
        for name, weight in result["optimal_weights"].items():
            print(f"   {name}: {weight:.2%}")
        
        print(f"\n📈 组合表现:")
        print(f"   组合收益率: {result['portfolio_return']:.2%}")
        print(f"   组合夏普比率: {result['portfolio_sharpe']:.4f}")
        
        print(f"\n📊 各策略表现:")
        for name, strategy_result in result["individual_results"].items():
            print(f"   {name}:")
            print(f"      收益率: {strategy_result.metrics.total_return:.2%}")
            print(f"      夏普比率: {strategy_result.metrics.sharpe_ratio:.4f}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ 组合优化失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_random_search():
    """测试随机搜索优化"""
    print("\n" + "=" * 80)
    print("测试3: 随机搜索优化")
    print("=" * 80)
    
    # 生成数据
    data = generate_sample_data(250)
    
    # 定义参数范围
    param_ranges = {
        'ema_fast': (8, 20),
        'adx_threshold': (20, 40)
    }
    
    print(f"\n📊 参数范围:")
    for param, (min_val, max_val) in param_ranges.items():
        print(f"   {param}: [{min_val}, {max_val}]")
    
    # 创建优化器
    optimizer = ParameterOptimizer(initial_capital=100000)
    
    print(f"\n🔍 开始随机搜索优化（20次迭代）...")
    
    try:
        # 运行优化
        result = optimizer.random_search(
            strategy_class=VegasADXStrategy,
            param_ranges=param_ranges,
            data=data,
            n_iterations=20,
            metric="sharpe_ratio"
        )
        
        print(f"\n✅ 优化完成！")
        print(f"\n🏆 最优参数:")
        for param, value in result["best_params"].items():
            if isinstance(value, float):
                print(f"   {param}: {value:.2f}")
            else:
                print(f"   {param}: {value}")
        
        print(f"\n📈 最优表现:")
        print(f"   夏普比率: {result['best_score']:.4f}")
        print(f"   测试次数: {result['total_tested']}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ 优化失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("InvestMind-Pro 参数优化与组合策略测试")
    print("=" * 80)
    
    try:
        # 测试1: 网格搜索
        grid_result = test_grid_search()
        
        # 测试2: 组合策略优化
        portfolio_result = test_portfolio_optimization()
        
        # 测试3: 随机搜索
        random_result = test_random_search()
        
        print("\n" + "=" * 80)
        print("✅ 所有测试完成！")
        print("=" * 80)
        
        print("\n📊 测试总结:")
        if grid_result:
            print(f"   ✅ 网格搜索: 成功")
        if portfolio_result:
            print(f"   ✅ 组合优化: 成功")
        if random_result:
            print(f"   ✅ 随机搜索: 成功")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
