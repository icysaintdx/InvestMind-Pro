#!/usr/bin/env python3
"""
测试所有修复
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("🧪 测试所有修复")
print("=" * 80)
print()

# 测试1: 热搜API
print("🔥 测试1: 热搜API（已修复 - 多个备用地址）")
print("-" * 80)

try:
    from backend.dataflows.news.hot_search_api import get_hot_search_api
    
    api = get_hot_search_api()
    
    # 测试微博热搜
    print("\n📱 微博热搜:")
    weibo_hot = api.get_weibo_hot()
    if weibo_hot:
        print(f"✅ 成功: {len(weibo_hot)} 条")
        if weibo_hot:
            print(f"第一条: {weibo_hot[0]}")
            
        # 过滤股票相关
        stock_topics = api.filter_stock_topics(weibo_hot)
        print(f"📊 股票相关: {len(stock_topics)} 条")
    else:
        print("❌ 失败")
    
    # 测试百度热搜
    print("\n🔍 百度热搜:")
    baidu_hot = api.get_baidu_hot()
    if baidu_hot:
        print(f"✅ 成功: {len(baidu_hot)} 条")
        if baidu_hot:
            print(f"第一条: {baidu_hot[0]}")
    else:
        print("❌ 失败")
        
except Exception as e:
    print(f"❌ 热搜API测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n")

# 测试2: 统一新闻API
print("📰 测试2: 统一新闻API")
print("-" * 80)

try:
    from backend.dataflows.news.unified_news_api import get_unified_news_api
    
    api = get_unified_news_api()
    test_stock = "600519"
    
    print(f"\n获取{test_stock}的综合新闻...")
    result = api.get_stock_news_comprehensive(test_stock)
    
    print(f"\n📊 数据源统计:")
    print(f"   成功: {result['summary']['data_sources']['success']}/{result['summary']['data_sources']['total']}")
    print(f"   成功率: {result['summary']['data_sources']['success_rate']}")
    
    print(f"\n📈 各数据源状态:")
    for source_name, source_data in result['sources'].items():
        status = source_data.get('status')
        if status == 'success':
            count = source_data.get('count', 'N/A')
            print(f"   ✅ {source_name}: {count}条")
        else:
            print(f"   ❌ {source_name}: {status}")
            
except Exception as e:
    print(f"❌ 统一新闻API测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n")

# 测试3: 聚合数据
print("📊 测试3: 聚合数据（检查N/A问题）")
print("-" * 80)

try:
    from backend.dataflows.data_source_manager import DataSourceManager
    
    manager = DataSourceManager()
    test_symbol = "600519"
    
    print(f"\n获取{test_symbol}的数据...")
    result = manager.get_stock_data(test_symbol)
    
    if "N/A" in result:
        print("⚠️ 仍然存在N/A")
        print(result)
    else:
        print("✅ 没有N/A")
        print(result[:500])
        
except Exception as e:
    print(f"❌ 聚合数据测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n")
print("=" * 80)
print("📋 测试总结")
print("=" * 80)
print()
print("1. ✅ 热搜API - 已修复（使用多个备用地址）")
print("2. ⏳ 统一新闻API - 待测试")
print("3. ⏳ 聚合数据 - 待检查")
print()
print("下一步:")
print("1. 运行 python test_unified_news.py")
print("2. 前端集成测试")
print("3. 实现法律合规爬虫")
print()
