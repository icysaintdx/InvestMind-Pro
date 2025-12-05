#!/usr/bin/env python3
"""测试修复后的社交媒体数据"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from dataflows.akshare.social_media_data import get_social_media_data

print("\n" + "="*60)
print("测试修复后的社交媒体数据模块")
print("="*60)

social = get_social_media_data()

# 测试1: 微博股票热议
print("\n测试1: 微博股票热议")
print("-"*60)
try:
    data = social.get_weibo_stock_hot()
    print(f"✅ 成功！获取到 {len(data)} 条数据")
    if data:
        print(f"示例: {data[0]}")
except Exception as e:
    print(f"❌ 失败: {e}")

# 测试2: 微博热搜（实际是股票热议）
print("\n测试2: 微博热搜（股票热议替代）")
print("-"*60)
try:
    data = social.get_weibo_hot_search()
    print(f"✅ 成功！获取到 {len(data)} 条数据")
    if data:
        print(f"示例: {data[0]}")
except Exception as e:
    print(f"❌ 失败: {e}")

# 测试3: 百度热搜股票
print("\n测试3: 百度热搜股票")
print("-"*60)
try:
    data = social.get_baidu_hot_search()
    print(f"✅ 成功！获取到 {len(data)} 条数据")
    if data:
        print(f"示例: {data[0]}")
except Exception as e:
    print(f"❌ 失败: {e}")

# 测试4: 综合数据
print("\n测试4: 综合社交媒体数据")
print("-"*60)
try:
    data = social.get_comprehensive_social_media()
    print(f"✅ 成功！")
    print(f"  - 微博热搜: {len(data.get('weibo_hot_search', []))} 条")
    print(f"  - 微博股票热议: {len(data.get('weibo_stock_hot', []))} 条")
    print(f"  - 百度热搜: {len(data.get('baidu_hot_search', []))} 条")
except Exception as e:
    print(f"❌ 失败: {e}")

print("\n" + "="*60)
print("✅ 测试完成")
print("="*60)
