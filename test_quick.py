"""快速测试策略初始化"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("快速测试：策略初始化")
print("=" * 60)

try:
    from backend.strategies.base import StrategyConfig
    print("✅ 导入 StrategyConfig 成功")
    
    from backend.strategies.vegas_adx import VegasADXStrategy
    print("✅ 导入 VegasADXStrategy 成功")
    
    # 创建配置
    config = StrategyConfig(
        name="Vegas+ADX",
        parameters={},
        risk_params={}
    )
    print("✅ 创建 StrategyConfig 成功")
    
    # 创建策略
    strategy = VegasADXStrategy(config)
    print(f"✅ 创建策略成功: {strategy.name}")
    
    print("\n" + "=" * 60)
    print("✅ 所有测试通过！")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
