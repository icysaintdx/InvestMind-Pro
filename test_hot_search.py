#!/usr/bin/env python3
"""
测试热搜API
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("🔥 测试热搜API")
print("=" * 80)
print()

# 测试1: 微博热搜
print("📱 测试1: 微博热搜API")
print("-" * 80)

try:
    from backend.dataflows.news.weibo_hot_search import get_weibo_hot_search_api
    
    api = get_weibo_hot_search_api()
    
    # 获取完整结果
    result = api.get_stock_hot_topics()
    
    if result['success']:
        print(f"✅ {result['summary']}")
        print(f"📊 股票话题占比: {result['stock_ratio']:.1%}")
        print(f"🔥 总热度: {result['total_heat']:,}")
        print()
        
        if result['topics']:
            print("🔝 股票相关热搜话题:")
            for i, topic in enumerate(result['topics'][:10], 1):
                title = topic.get('title', '') or topic.get('word', '') or topic.get('query', '')
                heat = topic.get('热度', '') or topic.get('heat', '') or 'N/A'
                rank = topic.get('排名', '') or topic.get('rank', '') or i
                keywords = ', '.join(topic.get('matched_keywords', []))
                
                print(f"\n{i}. [{rank}] {title}")
                print(f"   🔥 热度: {heat}")
                print(f"   🏷️ 匹配关键词: {keywords}")
        else:
            print("⚠️ 当前没有股票相关热搜")
    else:
        print(f"❌ 获取失败: {result.get('message')}")
        
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
print("📋 测试总结")
print("=" * 80)
print()
print("下一步:")
print("1. 集成百度热搜API")
print("2. 集成知乎热搜API")
print("3. 统一热搜数据接口")
print()
