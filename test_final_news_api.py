#!/usr/bin/env python3
"""
测试最终的新闻API
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("🧪 测试AKShare新闻API")
print("=" * 80)
print()

try:
    from backend.dataflows.news.akshare_news_api import get_akshare_news_api
    
    api = get_akshare_news_api()
    test_stock = "600519"
    
    # 测试1: 个股新闻（核心）
    print("📰 测试1: 个股新闻（最重要）")
    print("-" * 80)
    news = api.get_stock_news(test_stock, limit=10)
    if news:
        print(f"✅ 成功获取 {len(news)} 条新闻")
        for i, item in enumerate(news[:3], 1):
            print(f"\n{i}. {item['title']}")
            print(f"   时间: {item['publish_time']}")
            print(f"   来源: {item['source']}")
    else:
        print("⚠️ 未获取到新闻")
    
    print("\n")
    
    # 测试2: 财经早餐
    print("☕ 测试2: 财经早餐")
    print("-" * 80)
    morning = api.get_morning_news()
    if morning:
        print(f"✅ 成功获取 {len(morning)} 条")
        if morning:
            print(f"第一条: {morning[0]['title']}")
    else:
        print("⚠️ 未获取到财经早餐")
    
    print("\n")
    
    # 测试3: 全球财经新闻
    print("🌍 测试3: 全球财经新闻（东方财富）")
    print("-" * 80)
    global_news = api.get_global_news_em(limit=5)
    if global_news:
        print(f"✅ 成功获取 {len(global_news)} 条")
    else:
        print("⚠️ 未获取到全球新闻")
    
    print("\n")
    
    # 测试4: 财联社快讯
    print("⚡ 测试4: 财联社快讯")
    print("-" * 80)
    cls = api.get_cls_telegraph(limit=5)
    if cls:
        print(f"✅ 成功获取 {len(cls)} 条")
    else:
        print("⚠️ 未获取到财联社快讯")
    
    print("\n")
    
    # 测试5: 微博热议
    print("🔥 测试5: 微博热议")
    print("-" * 80)
    weibo = api.get_weibo_stock_hot()
    if weibo:
        print(f"✅ 成功获取 {len(weibo)} 条")
        if weibo:
            print(f"第一条数据: {weibo[0]}")
    else:
        print("⚠️ 未获取到微博热议")

except Exception as e:
    print(f"❌ AKShare测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n")
print("=" * 80)
print("🧪 测试热搜API")
print("=" * 80)
print()

try:
    from backend.dataflows.news.hot_search_api import get_hot_search_api
    
    hot_api = get_hot_search_api()
    
    # 测试6: 微博热搜
    print("📱 测试6: 微博热搜")
    print("-" * 80)
    weibo_hot = hot_api.get_weibo_hot()
    if weibo_hot:
        print(f"✅ 成功获取 {len(weibo_hot)} 条")
        stock_topics = hot_api.filter_stock_topics(weibo_hot)
        print(f"📊 股票相关: {len(stock_topics)} 条")
        
        if stock_topics:
            print("\n前5条股票相关热搜:")
            for i, topic in enumerate(stock_topics[:5], 1):
                title = topic.get('title', '') or topic.get('word', '')
                keywords = ', '.join(topic.get('matched_keywords', []))
                print(f"{i}. {title}")
                print(f"   匹配关键词: {keywords}")
    else:
        print("⚠️ 未获取到微博热搜")
    
    print("\n")
    
    # 测试7: 百度热搜
    print("🔍 测试7: 百度热搜")
    print("-" * 80)
    baidu_hot = hot_api.get_baidu_hot()
    if baidu_hot:
        print(f"✅ 成功获取 {len(baidu_hot)} 条")
        stock_topics = hot_api.filter_stock_topics(baidu_hot)
        print(f"📊 股票相关: {len(stock_topics)} 条")
    else:
        print("⚠️ 未获取到百度热搜")
    
    print("\n")
    
    # 测试8: 获取所有热搜
    print("📦 测试8: 获取所有平台热搜")
    print("-" * 80)
    all_hot = hot_api.get_all_stock_hot_topics()
    print(f"微博: 总计 {all_hot['weibo']['total']} 条，股票相关 {all_hot['weibo']['stock_related']} 条")
    print(f"百度: 总计 {all_hot['baidu']['total']} 条，股票相关 {all_hot['baidu']['stock_related']} 条")

except Exception as e:
    print(f"❌ 热搜API测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n")
print("=" * 80)
print("📋 测试总结")
print("=" * 80)
print()
print("✅ = 测试通过")
print("⚠️ = 测试通过但无数据")
print("❌ = 测试失败")
print()
print("下一步:")
print("1. 删除不稳定的爬虫文件")
print("2. 集成到统一API接口")
print("3. 前端调用测试")
print()
