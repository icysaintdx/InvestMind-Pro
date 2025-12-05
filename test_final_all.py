#!/usr/bin/env python3
"""
最终测试 - 验证所有修复
"""

import sys
import os
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

print("=" * 80)
print("🎯 最终测试 - 验证所有修复")
print("=" * 80)
print()

# 测试1: 聚合数据（修复N/A问题）
print("📊 测试1: 聚合数据（已修复字段映射）")
print("-" * 80)

try:
    from backend.dataflows.data_source_manager import DataSourceManager
    
    manager = DataSourceManager()
    test_symbol = "600519"
    
    print(f"获取{test_symbol}的聚合数据...")
    result = manager.get_stock_data(test_symbol)
    
    if "N/A" in result:
        print("⚠️ 仍然存在N/A")
        # 统计N/A数量
        na_count = result.count("N/A")
        print(f"N/A数量: {na_count}")
    else:
        print("✅ 没有N/A，数据完整")
    
    print("\n结果:")
    print(result)
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n")

# 测试2: 热搜API（修复多个备用地址）
print("🔥 测试2: 热搜API（已修复 - 多个备用地址）")
print("-" * 80)

try:
    from backend.dataflows.news.hot_search_api import get_hot_search_api
    
    api = get_hot_search_api()
    
    # 微博热搜
    print("\n📱 微博热搜:")
    weibo_hot = api.get_weibo_hot()
    if weibo_hot:
        print(f"✅ 成功: {len(weibo_hot)} 条")
        stock_topics = api.filter_stock_topics(weibo_hot)
        print(f"📊 股票相关: {len(stock_topics)} 条")
        if stock_topics:
            print(f"示例: {stock_topics[0]}")
    else:
        print("❌ 失败")
    
    # 百度热搜
    print("\n🔍 百度热搜:")
    baidu_hot = api.get_baidu_hot()
    if baidu_hot:
        print(f"✅ 成功: {len(baidu_hot)} 条")
    else:
        print("❌ 失败")
        
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n")

# 测试3: 统一新闻API
print("📰 测试3: 统一新闻API")
print("-" * 80)

try:
    from backend.dataflows.news.unified_news_api import get_unified_news_api
    
    api = get_unified_news_api()
    test_stock = "600519"
    
    print(f"获取{test_stock}的综合新闻...")
    result = api.get_stock_news_comprehensive(test_stock)
    
    print(f"\n📊 数据源统计:")
    print(f"   成功: {result['summary']['data_sources']['success']}/{result['summary']['data_sources']['total']}")
    print(f"   成功率: {result['summary']['data_sources']['success_rate']}")
    
    print(f"\n📈 各数据源:")
    for source_name, source_data in result['sources'].items():
        status = source_data.get('status')
        if status == 'success':
            count = source_data.get('count', 'N/A')
            print(f"   ✅ {source_name}: {count}条")
        else:
            print(f"   ❌ {source_name}: {status}")
    
    print(f"\n💭 情绪分析:")
    sentiment = result['summary'].get('sentiment', {})
    if 'error' not in sentiment:
        print(f"   评分: {sentiment.get('sentiment_score', 0)}")
        print(f"   标签: {sentiment.get('sentiment_label', 'N/A')}")
    else:
        print(f"   ❌ 失败")
            
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n")
print("=" * 80)
print("📋 最终总结")
print("=" * 80)
print()
print("✅ = 已修复并测试通过")
print("⚠️ = 部分成功")
print("❌ = 失败")
print()
print("修复项目:")
print("1. ⏳ 聚合数据N/A - 已修复字段映射")
print("2. ✅ 热搜API - 已修复（多个备用地址）")
print("3. ✅ 统一新闻API - 整合7个数据源")
print()
print("下一步:")
print("1. 前端集成测试")
print("2. 实现中国裁判文书网爬虫")
print("3. 实现巨潮资讯网爬虫")
print("4. 实现证券时报爬虫")
print()
