"""
测试回测系统是否正常工作
"""

import asyncio
import sys
from pathlib import Path
import json
from datetime import datetime, timedelta

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from backend.backtest.engine import BacktestEngine, BacktestConfig
from backend.backtest.data_loader import DataLoader, DataSource
from backend.strategies.vegas_adx import create_vegas_adx_strategy
from backend.strategies.ema_breakout import create_ema_breakout_strategy


async def test_data_loader():
    """测试数据加载器"""
    print("\n=== 测试数据加载器 ===")
    
    loader = DataLoader(DataSource.AKSHARE)
    
    # 测试加载股票数据
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=100)).strftime("%Y%m%d")
    
    print(f"加载数据: 600519（贵州茅台）")
    print(f"时间范围: {start_date} - {end_date}")
    
    data = loader.load_stock_data("600519", start_date, end_date)
    
    if data is not None and not data.empty:
        print(f"✅ 成功加载 {len(data)} 条数据")
        print(f"数据列: {data.columns.tolist()}")
        print(f"最新5条数据:")
        print(data.tail())
        
        # 添加技术指标
        data_with_indicators = loader.add_technical_indicators(data)
        print(f"\n添加技术指标后列数: {len(data_with_indicators.columns)}")
        return True
    else:
        print("❌ 数据加载失败")
        return False


def test_vegas_adx_strategy():
    """测试Vegas+ADX策略"""
    print("\n=== 测试Vegas+ADX策略 ===")
    
    strategy = create_vegas_adx_strategy()
    print(f"策略名称: {strategy.name}")
    print(f"策略类别: {strategy.category}")
    print(f"策略参数: {strategy.parameters}")
    print(f"风险参数: {strategy.risk_params}")
    print(f"所需指标: {strategy.get_required_indicators()}")
    
    return True


def test_ema_breakout_strategy():
    """测试均线突破策略"""
    print("\n=== 测试均线突破策略 ===")
    
    strategy = create_ema_breakout_strategy()
    print(f"策略名称: {strategy.name}")
    print(f"策略类别: {strategy.category}")
    print(f"策略参数: {strategy.parameters}")
    print(f"风险参数: {strategy.risk_params}")
    print(f"所需指标: {strategy.get_required_indicators()}")
    
    return True


def test_backtest_engine():
    """测试回测引擎"""
    print("\n=== 测试回测引擎 ===")
    
    # 创建配置
    config = BacktestConfig(
        initial_capital=100000,
        commission_rate=0.0003,
        slippage_rate=0.0005,
        max_position_pct=0.3
    )
    
    # 创建引擎
    engine = BacktestEngine(config)
    
    print(f"初始资金: {config.initial_capital}")
    print(f"手续费率: {config.commission_rate}")
    print(f"滑点率: {config.slippage_rate}")
    print(f"最大仓位: {config.max_position_pct}")
    print("✅ 回测引擎创建成功")
    
    return True


async def test_simple_backtest():
    """运行简单回测测试"""
    print("\n=== 运行简单回测 ===")
    
    try:
        # 加载数据
        loader = DataLoader(DataSource.AKSHARE)
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=60)).strftime("%Y%m%d")
        
        print(f"加载 600519 最近60天数据...")
        data = loader.load_stock_data("600519", start_date, end_date)
        
        if data is None or data.empty:
            print("❌ 无法加载数据，跳过回测")
            return False
        
        print(f"✅ 加载 {len(data)} 条数据")
        
        # 添加技术指标
        data = loader.add_technical_indicators(data)
        
        # 创建策略
        strategy = create_vegas_adx_strategy()
        print(f"使用策略: {strategy.name}")
        
        # 创建回测引擎
        config = BacktestConfig(
            initial_capital=100000,
            start_date=start_date,
            end_date=end_date
        )
        engine = BacktestEngine(config)
        
        # 运行回测
        print("开始回测...")
        result = engine.run(strategy, data, "600519")
        
        # 显示结果
        print("\n=== 回测结果 ===")
        print(f"初始资金: ¥{result.initial_capital:,.2f}")
        print(f"最终资金: ¥{result.final_capital:,.2f}")
        print(f"总收益率: {result.metrics.total_return:.2%}")
        print(f"年化收益率: {result.metrics.annual_return:.2%}")
        print(f"最大回撤: {result.metrics.max_drawdown:.2%}")
        print(f"夏普比率: {result.metrics.sharpe_ratio:.2f}")
        print(f"总交易次数: {result.metrics.total_trades}")
        print(f"胜率: {result.metrics.win_rate:.2%}")
        print(f"盈亏比: {result.metrics.profit_factor:.2f}")
        
        print("\n✅ 回测完成")
        return True
        
    except Exception as e:
        print(f"❌ 回测失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_market_rules():
    """测试市场规则引擎"""
    print("\n=== 测试市场规则引擎 ===")
    
    from backend.trading.market_rules import market_rule_engine, MarketType
    
    # 测试市场检测
    test_codes = [
        ("600519", MarketType.CN, "A股"),
        ("000001", MarketType.CN, "A股"),
        ("0700", MarketType.HK, "港股"),
        ("AAPL", MarketType.US, "美股"),
        ("TSLA", MarketType.US, "美股")
    ]
    
    print("\n股票代码识别测试:")
    for code, expected, name in test_codes:
        detected = market_rule_engine.detect_market(code)
        status = "✅" if detected == expected else "❌"
        print(f"{status} {code} -> {detected.value} ({name})")
    
    # 测试手续费计算
    print("\n手续费计算测试:")
    test_cases = [
        (MarketType.CN, "buy", 10000, "A股买入1万元"),
        (MarketType.CN, "sell", 10000, "A股卖出1万元"),
        (MarketType.HK, "buy", 10000, "港股买入1万元"),
        (MarketType.US, "sell", 10000, "美股卖出1万元")
    ]
    
    for market, side, amount, desc in test_cases:
        fee = market_rule_engine.calculate_commission(market, side, amount)
        fee_rate = fee / amount * 100
        print(f"{desc}: ¥{fee:.2f} ({fee_rate:.3f}%)")
    
    # 测试T+1规则
    print("\nT+1规则测试:")
    from datetime import datetime, timedelta
    
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    
    # A股T+1
    can_sell = market_rule_engine.can_sell_today(
        MarketType.CN,
        yesterday,
        today
    )
    print(f"A股昨天买入今天{'可以' if can_sell else '不可以'}卖出: {can_sell}")
    
    # 美股T+0
    can_sell = market_rule_engine.can_sell_today(
        MarketType.US,
        today,
        today
    )
    print(f"美股今天买入今天{'可以' if can_sell else '不可以'}卖出: {can_sell}")
    
    return True


async def main():
    """主测试函数"""
    print("=" * 50)
    print("模拟交易与回测系统测试")
    print("=" * 50)
    
    results = []
    
    # 测试各个模块
    results.append(("市场规则引擎", test_market_rules()))
    results.append(("Vegas+ADX策略", test_vegas_adx_strategy()))
    results.append(("均线突破策略", test_ema_breakout_strategy()))
    results.append(("回测引擎", test_backtest_engine()))
    results.append(("数据加载器", await test_data_loader()))
    
    # 如果基础测试都通过，运行简单回测
    if all(r[1] for r in results):
        results.append(("简单回测", await test_simple_backtest()))
    
    # 显示测试结果
    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！回测系统工作正常。")
    else:
        print("\n⚠️ 部分测试失败，请检查相关模块。")
    
    return passed == total


if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
