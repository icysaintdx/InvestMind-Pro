"""快速测试策略选择系统"""
import sys
from pathlib import Path

backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

print("="*60)
print("策略选择系统快速测试")
print("="*60)

# 测试1：导入模块
print("\n【测试1】导入模块")
try:
    from backend.services.strategy.data_validator import validate_strategy_inputs
    from backend.services.strategy.scenario_rules import get_scenario_guidance  
    from backend.services.strategy.selector import get_strategy_selector
    print("✅ 所有模块导入成功")
except Exception as e:
    print(f"❌ 模块导入失败: {e}")
    sys.exit(1)

# 测试2：加载规则配置
print("\n【测试2】加载规则配置")
try:
    selector = get_strategy_selector()
    rules = selector.rules
    print(f"✅ 规则配置加载成功")
    print(f"   版本: {rules.get('version')}")
    print(f"   必选条件: {len(rules.get('mandatory_conditions', []))}条")
    print(f"   禁止条件: {len(rules.get('forbidden_conditions', []))}条")
    print(f"   可用策略: {len(selector.strategies)}个")
except Exception as e:
    print(f"❌ 规则配置加载失败: {e}")
    sys.exit(1)

# 测试3：数据验证
print("\n【测试3】数据验证")
try:
    stock_analysis = {
        "macroeconomic": {"score": 75},
        "technical": {"score": 80},
        "fundamental": {"score": 85},
        "risk_level": "medium",
        "period_suggestion": 15
    }
    market_data = {
        "price": [100, 102],
        "volume": [1000000, 1200000],
        "trend": "up",
        "volatility": 0.05
    }
    result = validate_strategy_inputs(stock_analysis, market_data, 0.6)
    print(f"✅ 数据验证成功")
    print(f"   情绪指数: {result['news_sentiment']}")
except Exception as e:
    print(f"❌ 数据验证失败: {e}")
    sys.exit(1)

# 测试4：场景规则
print("\n【测试4】场景规则生成")
try:
    rules = get_scenario_guidance(stock_analysis, market_data)
    print(f"✅ 场景规则生成成功")
    print(f"   生成规则数: {len(rules)}")
    if rules:
        print(f"   示例: {rules[0][:50]}...")
except Exception as e:
    print(f"❌ 场景规则生成失败: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("🎉 所有测试通过！系统运行正常")
print("="*60)
