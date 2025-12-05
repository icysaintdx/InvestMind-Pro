#!/usr/bin/env python3
"""测试热榜数据"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from dataflows.akshare.hot_rank_data import get_hot_rank_data

print("="*60)
print("测试热榜数据")
print("="*60)

hot_rank = get_hot_rank_data()

print("\n1. 测试东财热门股票:")
data = hot_rank.get_eastmoney_hot_rank()
if data:
    print(f"   ✅ 获取到 {len(data)} 条")
    print(f"   示例: {data[0]}")
    print(f"   字段: {list(data[0].keys())}")
else:
    print("   ❌ 无数据")

print("\n2. 测试个股人气榜:")
data = hot_rank.get_stock_popularity_rank()
if data:
    print(f"   ✅ 获取到 {len(data)} 条")
    print(f"   示例: {data[0]}")
    print(f"   字段: {list(data[0].keys())}")
else:
    print("   ❌ 无数据")

print("\n3. 测试热门关键词:")
data = hot_rank.get_hot_keywords()
if data:
    print(f"   ✅ 获取到 {len(data)} 条")
    print(f"   示例: {data[0]}")
    print(f"   字段: {list(data[0].keys())}")
else:
    print("   ❌ 无数据")

print("\n4. 测试综合热榜:")
data = hot_rank.get_all_hot_ranks()
for key, value in data.items():
    if value:
        print(f"   ✅ {key}: {len(value)} 条")
    else:
        print(f"   ⚠️  {key}: 无数据")

print("\n" + "="*60)
print("测试完成")
print("="*60)
