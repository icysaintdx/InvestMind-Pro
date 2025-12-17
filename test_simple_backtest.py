"""
简化的策略回测测试脚本
使用现有的BacktestEngine进行测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 使用现有的回测引擎
from backend.backtest.engine import BacktestEngine, BacktestConfig
from backend.backtest.data_loader import DataLoader

# 导入策略和配置
from backend.strategies.base import StrategyConfig
from backend.strategies.vegas_adx import VegasADXStrategy
from backend.strategies.ema_breakout import EMABreakoutStrategy
from backend.strategies.trident import TridentStrategy
from backend.strategies.macd_crossover import MACDCrossoverStrategy
from backend.strategies.bollinger_breakout import BollingerBreakoutStrategy


def generate_sample_data(days: int = 250) -> pd.DataFrame:
    """生成模拟股票数据"""
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


async def test_single_strategy():
    """测试单个策略"""
    print("=" * 80)
    print("测试1: 使用现有BacktestEngine测试单策略")
    print("=" * 80)
    
    # 生成数据
    data = generate_sample_data(250)
    print(f"\n✅ 生成了 {len(data)} 天的模拟数据")
    print(f"   价格范围: {data['close'].min():.2f} - {data['close'].max():.2f}")
    
    # 创建策略配置
    config = StrategyConfig(
        name="Vegas+ADX",
        parameters={},
        risk_params={}
    )
    
    # 创建策略
    strategy = VegasADXStrategy(config)
    print(f"\n📊 测试策略: {strategy.name}")
    
    # 创建回测配置
    backtest_config = BacktestConfig(
        initial_capital=100000,
        commission_rate=0.0003,
        slippage_rate=0.0001
    )
    
    # 创建回测引擎
    engine = BacktestEngine(backtest_config)
    
    try:
        # 运行回测
        result = engine.run(
            strategy=strategy,
            data=data,
            stock_code="TEST001"
        )
        
        # 获取性能指标
        perf = result.metrics
        
        print("\n✅ 回测完成！")
        print(f"\n📈 性能指标:")
        print(f"   总收益率: {perf.total_return:.2%}")
        print(f"   年化收益率: {perf.annual_return:.2%}")
        print(f"   最大回撤: {perf.max_drawdown:.2%}")
        print(f"   夏普比率: {perf.sharpe_ratio:.2f}")
        print(f"   胜率: {perf.win_rate:.2%}")
        print(f"   总交易次数: {perf.total_trades}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ 回测失败: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_multiple_strategies():
    """测试多个策略对比"""
    print("\n" + "=" * 80)
    print("测试2: 多策略对比")
    print("=" * 80)
    
    # 生成数据
    data = generate_sample_data(250)
    
    # 创建策略列表
    strategies = [
        ("Vegas+ADX", VegasADXStrategy(StrategyConfig(name="Vegas+ADX"))),
        ("EMA突破", EMABreakoutStrategy(StrategyConfig(name="EMA突破"))),
        ("三叉戟", TridentStrategy(StrategyConfig(name="三叉戟"))),
        ("MACD交叉", MACDCrossoverStrategy(StrategyConfig(name="MACD交叉"))),
        ("布林带突破", BollingerBreakoutStrategy(StrategyConfig(name="布林带突破"))),
    ]
    
    print(f"\n准备测试 {len(strategies)} 个策略...")
    
    results = []
    
    for name, strategy in strategies:
        print(f"\n📊 测试: {name}")
        
        backtest_config = BacktestConfig(
            initial_capital=100000,
            commission_rate=0.0003,
            slippage_rate=0.0001
        )
        engine = BacktestEngine(backtest_config)
        
        try:
            result = engine.run(
                strategy=strategy,
                data=data,
                stock_code="TEST001"
            )
            
            results.append({
                "name": name,
                "return": result.metrics.total_return,
                "win_rate": result.metrics.win_rate,
                "sharpe": result.metrics.sharpe_ratio,
                "max_dd": result.metrics.max_drawdown,
                "trades": result.metrics.total_trades
            })
            
            print(f"   ✅ 收益率: {result.metrics.total_return:.2%}, 胜率: {result.metrics.win_rate:.2%}")
            
        except Exception as e:
            print(f"   ❌ 失败: {e}")
    
    # 显示对比结果
    if results:
        print("\n" + "=" * 80)
        print("📊 策略对比结果")
        print("=" * 80)
        
        # 按收益率排序
        results.sort(key=lambda x: x['return'], reverse=True)
        
        print(f"\n🏆 收益率排名:")
        for i, r in enumerate(results, 1):
            print(f"   {i}. {r['name']}: {r['return']:.2%} (胜率{r['win_rate']:.2%}, 夏普{r['sharpe']:.2f})")
        
        # 按胜率排序
        results.sort(key=lambda x: x['win_rate'], reverse=True)
        
        print(f"\n🎯 胜率排名:")
        for i, r in enumerate(results, 1):
            print(f"   {i}. {r['name']}: {r['win_rate']:.2%} (收益{r['return']:.2%})")
        
        # 按夏普比率排序
        results.sort(key=lambda x: x['sharpe'], reverse=True)
        
        print(f"\n⚖️ 夏普比率排名:")
        for i, r in enumerate(results, 1):
            print(f"   {i}. {r['name']}: {r['sharpe']:.2f} (收益{r['return']:.2%})")


async def test_with_real_data():
    """使用真实数据测试（如果可用）"""
    print("\n" + "=" * 80)
    print("测试3: 使用真实历史数据")
    print("=" * 80)
    
    try:
        # 尝试加载真实数据
        loader = DataLoader()
        
        # 计算日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        print(f"\n📥 尝试加载真实数据...")
        print(f"   股票代码: 600519 (贵州茅台)")
        print(f"   时间范围: {start_date.date()} 至 {end_date.date()}")
        
        data = await loader.load_stock_data(
            stock_code="600519",
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d")
        )
        
        if data is not None and len(data) > 50:
            print(f"\n✅ 成功加载 {len(data)} 天的真实数据")
            
            # 使用真实数据回测
            config = StrategyConfig(name="三叉戟")
            strategy = TridentStrategy(config)
            print(f"\n📊 使用真实数据测试: {strategy.name}")
            
            backtest_config = BacktestConfig(
                initial_capital=100000,
                commission_rate=0.0003,
                slippage_rate=0.0001
            )
            engine = BacktestEngine(backtest_config)
            
            result = engine.run(
                strategy=strategy,
                data=data,
                stock_code="600519"
            )
            
            print(f"\n✅ 真实数据回测完成！")
            print(f"\n📈 性能指标:")
            print(f"   总收益率: {result.metrics.total_return:.2%}")
            print(f"   年化收益率: {result.metrics.annual_return:.2%}")
            print(f"   最大回撤: {result.metrics.max_drawdown:.2%}")
            print(f"   夏普比率: {result.metrics.sharpe_ratio:.2f}")
            print(f"   胜率: {result.metrics.win_rate:.2%}")
            print(f"   总交易次数: {result.metrics.total_trades}")
            
        else:
            print(f"\n⚠️ 数据不足或加载失败，跳过真实数据测试")
            
    except Exception as e:
        print(f"\n⚠️ 无法加载真实数据: {e}")
        print("   使用模拟数据继续测试...")


async def main():
    """主测试函数"""
    print("\n" + "=" * 80)
    print("InvestMind-Pro 策略回测系统测试")
    print("=" * 80)
    
    try:
        # 测试1: 单策略
        await test_single_strategy()
        
        # 测试2: 多策略对比
        await test_multiple_strategies()
        
        # 测试3: 真实数据（如果可用）
        await test_with_real_data()
        
        print("\n" + "=" * 80)
        print("✅ 所有测试完成！")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 运行异步测试
    asyncio.run(main())
