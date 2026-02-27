#!/usr/bin/env python3
"""
测试AI情绪策略V2
验证策略是否正确注册和运行
"""

import sys
from pathlib import Path

# 设置项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

def test_strategy_registration():
    """测试策略是否正确注册"""
    print("=" * 60)
    print("测试AI情绪策略V2注册")
    print("=" * 60)
    
    try:
        from backend.strategies import get_strategy_registry, AISentimentStrategyV2
        registry = get_strategy_registry()
        
        print(f"✅ AISentimentStrategyV2 类已导入")
        
        # 检查注册
        registry_keys = registry.list_strategies()
        if "ai_sentiment_v2" in registry_keys:
            print(f"✅ 策略 'ai_sentiment_v2' 已注册")
            strategy_class = registry.get("ai_sentiment_v2")
            print(f"   类名: {strategy_class.__name__}")
            print(f"   描述: {strategy_class.description}")
        else:
            print(f"❌ 策略 'ai_sentiment_v2' 未注册")
            print(f"   已注册策略: {registry_keys}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_strategy_initialization():
    """测试策略初始化"""
    print("\n" + "=" * 60)
    print("测试AI情绪策略V2初始化")
    print("=" * 60)
    
    try:
        from backend.strategies import AISentimentStrategyV2
        from backend.strategies.base import StrategyConfig
        
        config = StrategyConfig(name="test_ai_v2")
        strategy = AISentimentStrategyV2(config)
        
        print(f"✅ 策略初始化成功")
        print(f"   名称: {strategy.name}")
        print(f"   版本: {strategy.version}")
        print(f"   类别: {strategy.category}")
        print(f"   使用LLM决策: {strategy.use_llm_for_decision}")
        
        return True
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_feature_extraction():
    """测试特征提取"""
    print("\n" + "=" * 60)
    print("测试特征提取")
    print("=" * 60)
    
    try:
        import pandas as pd
        import numpy as np
        from backend.strategies import AISentimentStrategyV2
        from backend.strategies.base import StrategyConfig
        
        # 创建模拟数据
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        np.random.seed(42)
        
        data = pd.DataFrame({
            'open': 100 + np.random.randn(100).cumsum(),
            'high': 102 + np.random.randn(100).cumsum(),
            'low': 98 + np.random.randn(100).cumsum(),
            'close': 100 + np.random.randn(100).cumsum(),
            'volume': np.random.randint(1000000, 5000000, 100),
        }, index=dates)
        
        # 添加情绪数据
        data['sent_smooth'] = np.random.randn(100) * 0.3
        data['sent_momentum'] = np.random.randn(100) * 0.1
        data['has_sentiment'] = True
        data['sent_volume'] = np.random.randint(10, 100, 100)
        
        config = StrategyConfig(name="test_ai_v2")
        strategy = AISentimentStrategyV2(config)
        
        # 测试特征提取
        df = strategy._ensure_indicators(data)
        features = strategy._extract_features(df)
        
        print(f"✅ 特征提取成功")
        print(f"   价格: {features['price']}")
        print(f"   技术指标: {list(features['technical'].keys())}")
        print(f"   情绪特征: {list(features['sentiment'].keys())}")
        print(f"   资金特征: {list(features['fund_flow'].keys())}")
        
        # 检查情绪趋势指标
        if 'sent_ma7' in df.columns:
            print(f"   ✅ 情绪MA7已计算")
        if 'sent_ma30' in df.columns:
            print(f"   ✅ 情绪MA30已计算")
        if 'sent_macd' in df.columns:
            print(f"   ✅ 情绪MACD已计算")
        
        return True
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_llm_prompt_building():
    """测试LLM提示词构建"""
    print("\n" + "=" * 60)
    print("测试LLM提示词构建")
    print("=" * 60)
    
    try:
        import pandas as pd
        import numpy as np
        from backend.strategies import AISentimentStrategyV2
        from backend.strategies.base import StrategyConfig
        
        # 创建模拟特征
        features = {
            'price': 100.5,
            'price_change_pct': 2.5,
            'date': '2024-02-27',
            'technical': {
                'rsi': 65.5,
                'macd': 0.05,
                'bb_position': '上半轨',
                'ma_trend': '多头排列',
                'price_vs_ma20': 5.2,
            },
            'sentiment': {
                'sent_current': 0.35,
                'sent_ma7': 0.25,
                'sent_ma30': 0.15,
                'sent_macd': 0.05,
                'sent_trend': 'up',
                'sent_spike': False,
                'sent_momentum': 0.1,
            },
            'fund_flow': {
                'volume_ratio': 1.5,
                'volume_trend': '明显放量',
            },
            'price_trend_5d': [1.2, -0.5, 2.1, 0.8, 2.5],
            'has_sentiment_data': True,
        }
        
        config = StrategyConfig(name="test_ai_v2")
        strategy = AISentimentStrategyV2(config)
        
        prompt = strategy._build_llm_prompt(features, current_position=0)
        
        print(f"✅ 提示词构建成功")
        print(f"   提示词长度: {len(prompt)} 字符")
        print(f"   包含价格信息: {'当前价格' in prompt}")
        print(f"   包含技术指标: {'RSI' in prompt}")
        print(f"   包含情绪指标: {'情绪分' in prompt}")
        print(f"   包含资金指标: {'量比' in prompt}")
        
        # 显示提示词前500字符
        print(f"\n提示词预览:")
        print("-" * 60)
        print(prompt[:500] + "...")
        
        return True
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("AI情绪策略V2 测试套件")
    print("=" * 60)
    
    results = []
    
    # 运行所有测试
    results.append(("策略注册", test_strategy_registration()))
    results.append(("策略初始化", test_strategy_initialization()))
    results.append(("特征提取", test_feature_extraction()))
    results.append(("LLM提示词", test_llm_prompt_building()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name}: {status}")
    
    print(f"\n总计: {passed}/{total} 项通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！AI情绪策略V2工作正常。")
    else:
        print(f"\n⚠️ {total - passed} 项测试失败，请检查实现。")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
