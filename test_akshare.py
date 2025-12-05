#!/usr/bin/env python3
"""
测试AKShare数据提供者
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("🧪 测试AKShare数据提供者")
print("=" * 80)
print()

try:
    from backend.dataflows.news.akshare_provider import get_akshare_provider
    
    provider = get_akshare_provider()
    test_stock = "600519"
    
    # 测试1: 股票新闻
    print("📰 测试1: 股票新闻（东方财富）")
    print("-" * 80)
    news = provider.get_stock_news(test_stock, limit=5)
    if news:
        print(f"✅ 成功获取 {len(news)} 条新闻")
        for i, item in enumerate(news[:3], 1):
            print(f"\n{i}. {item['title']}")
            print(f"   时间: {item['publish_time']}")
            print(f"   来源: {item['source']}")
    else:
        print("⚠️ 未获取到新闻")
    
    print("\n")
    
    # 测试2: 市场新闻
    print("📊 测试2: 市场新闻（新浪财经）")
    print("-" * 80)
    market_news = provider.get_market_news(limit=5)
    if market_news:
        print(f"✅ 成功获取 {len(market_news)} 条新闻")
        for i, item in enumerate(market_news[:3], 1):
            print(f"\n{i}. {item['title']}")
            print(f"   时间: {item['publish_time']}")
    else:
        print("⚠️ 未获取到新闻")
    
    print("\n")
    
    # 测试3: 财联社快讯
    print("⚡ 测试3: 财联社快讯")
    print("-" * 80)
    cls_news = provider.get_cls_news(limit=5)
    if cls_news:
        print(f"✅ 成功获取 {len(cls_news)} 条快讯")
        for i, item in enumerate(cls_news[:3], 1):
            print(f"\n{i}. {item['title']}")
            print(f"   时间: {item['publish_time']}")
    else:
        print("⚠️ 未获取到快讯")
    
    print("\n")
    
    # 测试4: 微博股票热议
    print("🔥 测试4: 微博股票热议")
    print("-" * 80)
    weibo_hot = provider.get_weibo_stock_hot()
    if weibo_hot:
        print(f"✅ 成功获取 {len(weibo_hot)} 只热议股票")
        for i, item in enumerate(weibo_hot[:10], 1):
            print(f"{i}. {item['stock_name']}({item['stock_code']}) - 热度: {item['heat_index']}")
    else:
        print("⚠️ 未获取到热议股票")
    
    print("\n")
    
    # 测试5: 获取所有数据
    print("📦 测试5: 获取所有数据")
    print("-" * 80)
    all_data = provider.get_all_news(test_stock)
    print(f"✅ {all_data['summary']}")
    print(f"   股票新闻: {len(all_data.get('stock_news', []))} 条")
    print(f"   市场新闻: {len(all_data.get('market_news', []))} 条")
    print(f"   财联社快讯: {len(all_data.get('cls_news', []))} 条")
    print(f"   微博热议: {len(all_data.get('weibo_hot', []))} 条")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n")
print("=" * 80)
print("📋 测试总结")
print("=" * 80)
print()
print("如果所有测试都通过，说明AKShare工作正常！")
print("下一步：替换现有爬虫，使用AKShare提供者")
print()
