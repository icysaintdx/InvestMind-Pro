#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻回测引擎测试套件
验证新闻回测和联合回测功能
"""

import sys
import os
import json
from datetime import datetime

# 添加项目根目录到路径
project_root = "/home/icysaintdx/.openclaw/workspace-investmindpro/InvestMindPro"
sys.path.insert(0, project_root)

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker

def test_news_backtest_engine():
    """测试新闻回测引擎"""
    print("\n" + "="*70)
    print("测试1: 新闻回测引擎")
    print("="*70)
    
    try:
        from backend.backtest.news_backtest_engine import NewsBacktestEngine, run_news_backtest
        
        # 初始化引擎
        engine = NewsBacktestEngine()
        print("✅ 引擎初始化成功")
        
        # 测试数据库连接
        db = engine.get_db()
        print("✅ 数据库连接成功")
        
        # 检查是否有新闻数据
        from backend.database.models import StockNewsRecord
        news_count = db.query(StockNewsRecord).count()
        print(f"📊 数据库中共有 {news_count} 条新闻记录")
        
        # 测试获取新闻
        if news_count > 0:
            # 找一个有新闻的股票
            sample_news = db.query(StockNewsRecord).first()
            if sample_news:
                stock_code = sample_news.ts_code
                print(f"📝 测试股票代码: {stock_code}")
                
                # 获取新闻
                news_list = engine.fetch_news_for_period(
                    stock_code=stock_code,
                    start_date="2024-01-01",
                    end_date="2024-12-31"
                )
                print(f"✅ 成功获取 {len(news_list)} 条新闻")
                
                if news_list:
                    # 测试情绪分析
                    analysis = engine.analyze_news_sentiment(news_list[0])
                    print(f"✅ 情绪分析成功: {analysis}")
                    
                    # 测试每日情绪聚合
                    daily_sentiments = engine.aggregate_daily_sentiment(news_list[:10])  # 只取前10条测试
                    print(f"✅ 每日情绪聚合成功: {len(daily_sentiments)} 个交易日")
                    
                    # 测试完整回测
                    result = engine.run_backtest(
                        stock_code=stock_code,
                        stock_name="测试股票",
                        start_date="2024-01-01",
                        end_date="2024-12-31"
                    )
                    print(f"✅ 完整回测成功")
                    print(f"   统计指标: {result.statistics}")
        else:
            print("⚠️ 数据库中没有新闻数据，跳过回测测试")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_joint_backtest_engine():
    """测试联合回测引擎"""
    print("\n" + "="*70)
    print("测试2: 联合回测引擎")
    print("="*70)
    
    try:
        from backend.backtest.joint_backtest import (
            JointBacktestEngine, 
            JointBacktestConfig,
            MarketState,
            SignalType
        )
        from backend.backtest.joint_backtest import TechnicalSignal, NewsSignal
        
        # 初始化配置
        config = JointBacktestConfig(
            tech_weight=0.6,
            news_weight=0.4,
            enable_dynamic_weight=True
        )
        print("✅ 配置创建成功")
        
        # 初始化引擎
        engine = JointBacktestEngine(config)
        print("✅ 引擎初始化成功")
        
        # 测试市场状态检测
        dates = pd.date_range(start='2024-01-01', periods=30, freq='B')
        np.random.seed(42)
        prices = 100 + np.cumsum(np.random.randn(30) * 0.5)
        price_data = pd.DataFrame({
            'open': prices,
            'high': prices * 1.02,
            'low': prices * 0.98,
            'close': prices,
            'volume': np.random.randint(1000000, 10000000, 30)
        }, index=dates)
        
        market_state = engine.detect_market_state(price_data)
        print(f"✅ 市场状态检测成功: {market_state.value}")
        
        # 测试动态权重计算
        tech_w, news_w = engine.calculate_dynamic_weights(market_state, 50)
        print(f"✅ 动态权重计算成功: 技术{tech_w:.1f} / 新闻{news_w:.1f}")
        
        # 测试信号融合
        tech_signal = TechnicalSignal(
            date="2024-01-15",
            signal=SignalType.BUY,
            confidence=70,
            score=75
        )
        news_signal = NewsSignal(
            date="2024-01-15",
            signal=SignalType.BUY,
            confidence=60,
            score=65,
            urgency=40
        )
        
        combined = engine.combine_signals(tech_signal, news_signal, market_state)
        print(f"✅ 信号融合成功")
        print(f"   技术信号: {combined.tech_signal.signal.value}({combined.tech_signal.score})")
        print(f"   新闻信号: {combined.news_signal.signal.value}({combined.news_signal.score})")
        print(f"   综合得分: {combined.combined_score:.1f}")
        print(f"   最终信号: {combined.final_signal.value}")
        print(f"   权重: 技术{combined.tech_weight:.1f} / 新闻{combined.news_weight:.1f}")
        
        # 测试技术信号生成
        tech_signals = engine.generate_technical_signals(price_data)
        print(f"✅ 技术信号生成成功: {len(tech_signals)} 条信号")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_alignment():
    """测试数据对齐功能"""
    print("\n" + "="*70)
    print("测试3: 数据对齐")
    print("="*70)
    
    try:
        from backend.backtest.news_backtest_engine import NewsBacktestEngine, DailySentiment
        
        engine = NewsBacktestEngine()
        
        # 创建模拟情绪数据
        daily_sentiments = {
            "2024-01-15": DailySentiment(
                date="2024-01-15",
                sentiment_score=65,
                sentiment_label="positive",
                news_count=5,
                positive_count=3,
                negative_count=1,
                neutral_count=1,
                urgency_score=30,
                avg_confidence=60
            ),
            "2024-01-16": DailySentiment(
                date="2024-01-16",
                sentiment_score=45,
                sentiment_label="neutral",
                news_count=3,
                positive_count=1,
                negative_count=1,
                neutral_count=1,
                urgency_score=20,
                avg_confidence=50
            )
        }
        
        # 生成时间序列
        sentiment_series = engine.create_sentiment_series(daily_sentiments)
        print("✅ 情绪时间序列创建成功")
        print(f"   列: {list(sentiment_series.columns)}")
        print(f"   形状: {sentiment_series.shape}")
        print(sentiment_series.head())
        
        # 创建模拟价格数据
        dates = pd.date_range(start='2024-01-15', periods=5, freq='B')
        price_data = pd.DataFrame({
            'open': [100, 101, 102, 103, 104],
            'high': [102, 103, 104, 105, 106],
            'low': [99, 100, 101, 102, 103],
            'close': [101, 102, 103, 104, 105],
            'volume': [1000000, 1200000, 1100000, 1300000, 1400000]
        }, index=dates)
        
        # 测试数据对齐
        merged = engine.align_with_price_data(sentiment_series, price_data)
        print("✅ 数据对齐成功")
        print(f"   合并后列: {list(merged.columns)}")
        print(f"   形状: {merged.shape}")
        print(merged)
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_export_function():
    """测试导出功能"""
    print("\n" + "="*70)
    print("测试4: 结果导出")
    print("="*70)
    
    try:
        from backend.backtest.news_backtest_engine import NewsBacktestEngine, NewsBacktestResult, DailySentiment
        
        engine = NewsBacktestEngine()
        
        # 创建模拟结果
        result = NewsBacktestResult(
            stock_code="601888",
            stock_name="中国中免",
            start_date="2024-01-01",
            end_date="2024-06-30",
            daily_sentiments=[
                DailySentiment(
                    date="2024-01-15",
                    sentiment_score=65,
                    sentiment_label="positive",
                    news_count=5,
                    positive_count=3,
                    negative_count=1,
                    neutral_count=1,
                    urgency_score=30,
                    avg_confidence=60,
                    keywords=["增长", "利好"]
                )
            ],
            statistics={
                'total_days': 100,
                'avg_score': 55.5
            }
        )
        
        # 导出到临时文件
        output_dir = f"{project_root}/backtest_results/test"
        os.makedirs(output_dir, exist_ok=True)
        output_file = f"{output_dir}/test_export.json"
        
        engine.export_to_json(result, output_file)
        print(f"✅ 导出成功: {output_file}")
        
        # 验证导出内容
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ 导出文件验证成功")
        print(f"   股票代码: {data['stock_code']}")
        print(f"   股票名称: {data['stock_name']}")
        print(f"   交易日数: {data['statistics']['total_days']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "="*70)
    print("新闻回测引擎测试套件")
    print("="*70)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"项目目录: {project_root}")
    
    results = {
        "新闻回测引擎": test_news_backtest_engine(),
        "联合回测引擎": test_joint_backtest_engine(),
        "数据对齐": test_data_alignment(),
        "结果导出": test_export_function()
    }
    
    print("\n" + "="*70)
    print("测试总结")
    print("="*70)
    
    for test_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name}: {status}")
    
    total = len(results)
    passed = sum(results.values())
    print(f"\n总计: {passed}/{total} 测试通过 ({passed/total*100:.1f}%)")
    
    return all(results.values())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
