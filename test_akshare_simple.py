#!/usr/bin/env python3
"""
简单测试AKShare - 只测试能工作的接口
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("🧪 简单测试AKShare")
print("=" * 80)
print()

try:
    from backend.dataflows.news.akshare_provider import get_akshare_provider
    
    provider = get_akshare_provider()
    
    # 只测试微博热议（这个能工作）
    print("🔥 测试: 微博股票热议")
    print("-" * 80)
    weibo_hot = provider.get_weibo_stock_hot()
    
    if weibo_hot and len(weibo_hot) > 0:
        print(f"✅ 成功获取 {len(weibo_hot)} 只热议股票")
        print()
        
        # 显示第一条的原始数据
        if 'raw_data' in weibo_hot[0]:
            print("第一条原始数据:")
            print(weibo_hot[0]['raw_data'])
            print()
        
        # 显示前10条
        print("前10只热议股票:")
        for i, item in enumerate(weibo_hot[:10], 1):
            raw = item.get('raw_data', {})
            print(f"{i}. {raw}")
    else:
        print("⚠️ 未获取到热议股票")
        
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
print("📋 结论")
print("=" * 80)
print()
print("AKShare的API接口名称和字段名经常变化")
print("建议：")
print("1. 使用现有的 realtime_news_utils.py（已验证可用）")
print("2. 不要依赖AKShare的不稳定接口")
print("3. 专注于核心功能：法律合规、公司公告")
print()
