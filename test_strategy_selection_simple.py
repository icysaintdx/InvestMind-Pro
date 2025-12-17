"""
策略选择系统简单测试（不依赖pytest）
"""

import sys
import asyncio
from pathlib import Path

# 添加backend到路径
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

print("=" * 60)
print("智能策略选择系统测试")
print("=" * 60)


def test_data_validator():
    """测试数据质量管控"""
    print("\n=== 测试数据质量管控 ===")
    
    try:
        from backend.services.strategy.data_validator import validate_strategy_inputs
        
        stock_analysis = {
            "macroeconomic": {"score": 75},
            "technical": {"score": 80},
            "fundamental": {"score": 85},
            "risk_level": "medium",
            "period_suggestion": 15,
            "fundamental_score": 85,
            "technical_score": 80
        }
        
        market_data = {
            "price": [100, 102, 101, 103],
            "volume": [1000000, 1200000, 1100000, 1300000],
            "trend": "up",
            "volatility": 0.05
        }
        
        news_sentiment = 0.6
        
        result = validate_strategy_inputs(stock_analysis, market_data, news_sentiment)
        
        assert result is not None
        assert "stock_analysis" in result
        assert "market_data" in result
        assert "news_sentiment" in result
        assert result["news_sentiment"] == 0.6
        
        print("✅ 数据验证测试通过")
        print(f"   - 验证时间: {result['validated_at']}")
        print(f"   - 情绪指数: {result['news_sentiment']}")
        return True
        
    except Exception as e:
        print(f"❌ 数据验证测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_scenario_rules():
    """测试场景化规则引擎"""
    print("\n=== 测试场景化规则引擎 ===")
    
    try:
        from backend.services.strategy.scenario_rules import get_scenario_guidance
        
        stock_analysis = {
            "stock_type": "成长股",
            "risk_level": "high",
            "fundamental_score": 75,
            "technical_score": 80
        }
        
        market_data = {
            "volatility": 0.10,  # 10% 高波动
            "trend": "up"
        }
        
        rules = get_scenario_guidance(stock_analysis, market_data)
        
        assert len(rules) > 0
        
        print(f"✅ 场景规则测试通过")
        print(f"   - 生成规则数: {len(rules)}")
        print(f"   - 示例规则: {rules[0][:50]}...")
        return True
        
    except Exception as e:
        print(f"❌ 场景规则测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_strategy_selector():
    """测试混合决策模型"""
    print("\n=== 测试混合决策模型 ===")
    
    try:
        from backend.services.strategy.selector import select_strategy
        
        stock_analysis = {
            "macroeconomic": {"score": 75},
            "technical": {"score": 80},
            "fundamental": {"score": 85},
            "risk_level": "medium",
            "period_suggestion": 14,
            "fundamental_score": 85,
            "technical_score": 80,
            "code": "600519"
        }
        
        market_data = {
            "price": [100, 102, 101, 103],
            "volume": [1000000, 1200000, 1100000, 1300000],
            "trend": "up",
            "volatility": 0.05
        }
        
        news_sentiment = 0.6
        
        result = await select_strategy(
            stock_analysis,
            market_data,
            news_sentiment
        )
        
        assert result is not None
        assert "selected_strategy_id" in result
        assert "selected_strategy_name" in result
        
        print(f"✅ 策略选择测试通过")
        print(f"   - 选择策略: {result['selected_strategy_name']}")
        print(f"   - 策略ID: {result['selected_strategy_id']}")
        print(f"   - 综合得分: {result['rule_matching_details']['priority_score']:.1f}")
        return True
        
    except Exception as e:
        print(f"❌ 策略选择测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rules_configuration():
    """测试规则配置"""
    print("\n=== 测试规则配置 ===")
    
    try:
        from backend.services.strategy.selector import get_strategy_selector
        
        selector = get_strategy_selector()
        rules = selector.rules
        
        assert "mandatory_conditions" in rules
        assert "forbidden_conditions" in rules
        assert "priority_rules" in rules
        
        print(f"✅ 规则配置测试通过")
        print(f"   - 必选条件: {len(rules['mandatory_conditions'])}条")
        print(f"   - 禁止条件: {len(rules['forbidden_conditions'])}条")
        print(f"   - 优先级规则: {len(rules['priority_rules'])}条")
        return True
        
    except Exception as e:
        print(f"❌ 规则配置测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_full_workflow():
    """测试完整工作流程"""
    print("\n=== 测试完整工作流程 ===")
    
    try:
        from backend.services.strategy.selector import select_strategy
        
        # 模拟完整的输入数据
        stock_analysis = {
            "macroeconomic": {
                "score": 75,
                "gdp_growth": 5.2,
                "inflation": 2.1
            },
            "technical": {
                "score": 80,
                "trend": "bullish",
                "momentum": "strong"
            },
            "fundamental": {
                "score": 85,
                "pe_ratio": 22.5,
                "roe": 18.5
            },
            "risk_level": "medium",
            "period_suggestion": 15,
            "fundamental_score": 85,
            "technical_score": 80,
            "code": "600519",
            "stock_type": "成长股"
        }
        
        market_data = {
            "price": [1650, 1660, 1655, 1670, 1665],
            "volume": [1000000, 1200000, 1100000, 1300000, 1150000],
            "trend": "up",
            "volatility": 0.05,
            "volume_trend": "surge"
        }
        
        news_sentiment = 0.6
        
        # 执行策略选择
        result = await select_strategy(
            stock_analysis,
            market_data,
            news_sentiment
        )
        
        # 验证结果
        assert result["selected_strategy_id"] in ["vegas_adx", "ema_breakout"]
        assert result["rule_matching_details"]["mandatory_conditions_met"] is True
        assert result["rule_matching_details"]["forbidden_conditions_violated"] is False
        
        print(f"✅ 完整工作流程测试通过")
        print(f"\n   【策略选择结果】")
        print(f"   策略名称: {result['selected_strategy_name']}")
        print(f"   选择理由: {result['selection_reason'][:80]}...")
        print(f"   风险检查: {result['risk_check_result']}")
        print(f"   备选策略: {len(result['alternative_strategies'])}个")
        return True
        
    except Exception as e:
        print(f"❌ 完整工作流程测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """运行所有测试"""
    results = []
    
    # 同步测试
    results.append(("数据质量管控", test_data_validator()))
    results.append(("场景化规则引擎", test_scenario_rules()))
    results.append(("规则配置", test_rules_configuration()))
    
    # 异步测试
    results.append(("混合决策模型", await test_strategy_selector()))
    results.append(("完整工作流程", await test_full_workflow()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
    else:
        print("\n⚠️ 部分测试失败，请检查相关模块。")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
