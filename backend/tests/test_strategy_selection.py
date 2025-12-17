"""
策略选择系统测试
验证三层规则体系和混合决策模型的功能
"""

import pytest
import asyncio
from typing import Dict, Any


class TestDataValidator:
    """测试数据质量管控模块"""
    
    def test_validate_complete_data(self):
        """测试完整数据验证"""
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
        
    def test_validate_missing_fields(self):
        """测试缺失字段验证"""
        from backend.services.strategy.data_validator import validate_strategy_inputs
        
        stock_analysis = {
            "technical": {"score": 80},
            # 缺少必需字段
        }
        
        market_data = {
            "price": [100, 102],
            "volume": [1000000, 1200000],
            "trend": "up",
            "volatility": 0.05
        }
        
        with pytest.raises(ValueError):
            validate_strategy_inputs(stock_analysis, market_data, 0.5)
    
    def test_sentiment_normalization(self):
        """测试情绪指数标准化"""
        from backend.services.strategy.data_validator import validate_strategy_inputs
        
        stock_analysis = {
            "macroeconomic": {"score": 75},
            "technical": {"score": 80},
            "fundamental": {"score": 85},
            "risk_level": "medium",
            "period_suggestion": 15
        }
        
        market_data = {
            "price": [100],
            "volume": [1000000],
            "trend": "up",
            "volatility": 0.05
        }
        
        # 测试超出范围的情绪指数
        result = validate_strategy_inputs(stock_analysis, market_data, 1.5)
        assert result["news_sentiment"] == 1.0
        
        result = validate_strategy_inputs(stock_analysis, market_data, -1.5)
        assert result["news_sentiment"] == -1.0


class TestScenarioRules:
    """测试场景化规则引擎"""
    
    def test_high_volatility_rules(self):
        """测试高波动率场景规则"""
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
        assert any("高波动率" in rule for rule in rules)
    
    def test_sideways_market_rules(self):
        """测试震荡市场场景规则"""
        from backend.services.strategy.scenario_rules import get_scenario_guidance
        
        stock_analysis = {
            "stock_type": "价值股",
            "risk_level": "medium",
            "fundamental_score": 85,
            "technical_score": 60
        }
        
        market_data = {
            "volatility": 0.04,
            "trend": "sideways"
        }
        
        rules = get_scenario_guidance(stock_analysis, market_data)
        
        assert any("震荡" in rule for rule in rules)
    
    def test_growth_stock_rules(self):
        """测试成长股场景规则"""
        from backend.services.strategy.scenario_rules import get_scenario_guidance
        
        stock_analysis = {
            "stock_type": "成长股",
            "risk_level": "medium",
            "fundamental_score": 80,
            "technical_score": 75
        }
        
        market_data = {
            "volatility": 0.05,
            "trend": "up"
        }
        
        rules = get_scenario_guidance(stock_analysis, market_data)
        
        assert any("成长股" in rule for rule in rules)


class TestStrategySelector:
    """测试混合决策模型"""
    
    @pytest.mark.asyncio
    async def test_rule_based_filter(self):
        """测试规则筛选"""
        from backend.services.strategy.selector import get_strategy_selector
        from backend.services.strategy.data_validator import validate_strategy_inputs
        
        selector = get_strategy_selector()
        
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
            "price": [100],
            "volume": [1000000],
            "trend": "up",
            "volatility": 0.05
        }
        
        validated_inputs = validate_strategy_inputs(
            stock_analysis, market_data, 0.5
        )
        
        candidates = selector._rule_based_filter(validated_inputs)
        
        assert len(candidates) > 0
        assert all("strategy_id" in s for s in candidates)
    
    @pytest.mark.asyncio
    async def test_hybrid_strategy_selection(self):
        """测试完整的混合决策流程"""
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
        assert "selection_reason" in result
        assert "rule_matching_details" in result
        assert result["rule_matching_details"]["mandatory_conditions_met"] is True
    
    @pytest.mark.asyncio
    async def test_decision_consistency(self):
        """测试决策一致性校验"""
        from backend.services.strategy.selector import get_strategy_selector
        from backend.services.strategy.data_validator import validate_strategy_inputs
        
        selector = get_strategy_selector()
        
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
            "price": [100],
            "volume": [1000000],
            "trend": "up",
            "volatility": 0.05
        }
        
        validated_inputs = validate_strategy_inputs(
            stock_analysis, market_data, 0.5
        )
        
        # 执行一致性校验
        strategy_id = await selector.check_decision_consistency(
            "vegas_adx",
            validated_inputs,
            retry_times=2
        )
        
        assert strategy_id is not None
        assert isinstance(strategy_id, str)


class TestRulesConfiguration:
    """测试规则配置"""
    
    def test_load_rules(self):
        """测试加载规则配置"""
        from backend.services.strategy.selector import get_strategy_selector
        
        selector = get_strategy_selector()
        rules = selector.rules
        
        assert "mandatory_conditions" in rules
        assert "forbidden_conditions" in rules
        assert "priority_rules" in rules
        assert "risk_thresholds" in rules
        
        # 验证必选条件数量
        assert len(rules["mandatory_conditions"]) >= 4
        
        # 验证禁止条件数量
        assert len(rules["forbidden_conditions"]) >= 4
        
        # 验证风险阈值
        assert "max_position_by_risk" in rules["risk_thresholds"]
        assert rules["risk_thresholds"]["max_position_by_risk"]["high"] == 0.50
        assert rules["risk_thresholds"]["max_position_by_risk"]["medium"] == 0.30
        assert rules["risk_thresholds"]["max_position_by_risk"]["low"] == 0.15


class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """测试完整工作流程"""
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
        assert len(result["alternative_strategies"]) >= 0
        
        print(f"\n✅ 策略选择成功: {result['selected_strategy_name']}")
        print(f"   选择理由: {result['selection_reason']}")
        print(f"   风险检查: {result['risk_check_result']}")


# 运行测试的便捷函数
def run_all_tests():
    """运行所有测试"""
    pytest.main([__file__, "-v", "-s"])


if __name__ == "__main__":
    run_all_tests()
