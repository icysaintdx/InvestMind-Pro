#!/usr/bin/env python3
"""
测试数据源优先级和新闻API
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("🧪 测试数据源优先级和新闻API")
print("=" * 80)
print()

# 测试1: 数据源优先级
print("📊 测试1: 数据源优先级")
print("-" * 80)

try:
    from backend.dataflows.data_source_manager import get_data_source_manager
    
    manager = get_data_source_manager()
    
    print(f"默认数据源: {manager.default_source.value}")
    print(f"当前数据源: {manager.current_source.value}")
    print(f"可用数据源: {[s.value for s in manager.available_sources]}")
    print()
    
    # 测试获取股票数据
    symbol = "600519"
    print(f"测试股票: {symbol}")
    print()
    
    # 测试AKShare
    print("1. 测试AKShare:")
    try:
        from backend.dataflows.stock.akshare_utils import get_akshare_provider
        provider = get_akshare_provider()
        data = provider.get_stock_data(symbol, "2024-11-01", "2024-12-01")
        if data is not None and not data.empty:
            print(f"   ✅ AKShare成功: {len(data)}条数据")
            print(f"   数据列: {list(data.columns)}")
            print(f"   最新价格: {data.iloc[-1]['close']:.2f}" if 'close' in data.columns else "")
        else:
            print(f"   ❌ AKShare失败: 无数据")
    except Exception as e:
        print(f"   ❌ AKShare失败: {e}")
        import traceback
        traceback.print_exc()
    print()
    
    # 测试新浪财经
    print("2. 测试新浪财经:")
    try:
        result = manager._get_sina_data(symbol, "2024-11-01", "2024-12-01")
        if result and "❌" not in result:
            print(f"   ✅ 新浪财经成功")
            print(f"   {result[:200]}...")
        else:
            print(f"   ❌ 新浪财经失败")
            print(f"   {result[:200]}")
    except Exception as e:
        print(f"   ❌ 新浪财经失败: {e}")
    print()
    
    # 测试聚合数据
    print("3. 测试聚合数据:")
    try:
        result = manager._get_juhe_data(symbol, "2024-11-01", "2024-12-01")
        if result and "❌" not in result:
            print(f"   ✅ 聚合数据成功")
            print(f"   {result[:200]}...")
        else:
            print(f"   ❌ 聚合数据失败")
            print(f"   {result[:200]}")
    except Exception as e:
        print(f"   ❌ 聚合数据失败: {e}")
    print()
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n")

# 测试2: 新闻API
print("📰 测试2: 新闻API")
print("-" * 80)

try:
    from backend.dataflows.news.unified_news_api import get_unified_news_api
    
    api = get_unified_news_api()
    symbol = "600519"
    
    print(f"测试股票: {symbol}")
    print()
    
    result = api.get_stock_news_comprehensive(symbol)
    
    print(f"数据源统计:")
    summary = result.get('summary', {})
    sources = summary.get('data_sources', {})
    print(f"  总数: {sources.get('total')}")
    print(f"  成功: {sources.get('success')}")
    print(f"  成功率: {sources.get('success_rate')}")
    print()
    
    print(f"各数据源:")
    for source_name, source_data in result.get('sources', {}).items():
        status = source_data.get('status')
        if status == 'success':
            count = source_data.get('count', 'N/A')
            print(f"  ✅ {source_name}: {count}条")
        else:
            print(f"  ❌ {source_name}: {status}")
    print()
    
    # 情绪分析
    sentiment = summary.get('sentiment', {})
    if sentiment:
        print(f"情绪分析:")
        print(f"  情绪: {sentiment.get('sentiment_label')}")
        print(f"  评分: {sentiment.get('sentiment_score')}")
        print(f"  置信度: {sentiment.get('confidence')}")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n")
print("=" * 80)
print("📋 诊断总结")
print("=" * 80)
print()
print("如果AKShare和新浪财经都失败，系统会降级到聚合数据。")
print("请检查：")
print("1. AKShare是否正确安装")
print("2. 网络连接是否正常")
print("3. API Key是否配置正确")
print()
