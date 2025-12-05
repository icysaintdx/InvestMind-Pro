#!/usr/bin/env python3
"""检查热榜数据字段"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from dataflows.akshare.hot_rank_data import get_hot_rank_data

print("="*60)
print("检查热榜数据字段")
print("="*60)

hot_rank = get_hot_rank_data()

print("\n1. 东财热门股票字段:")
data = hot_rank.get_eastmoney_hot_rank()
if data and len(data) > 0:
    print(f"   数量: {len(data)}")
    print(f"   字段: {list(data[0].keys())}")
    print(f"   第1条: {data[0]}")
    print(f"   第2条: {data[1]}")
else:
    print("   ❌ 无数据")

print("\n2. 个股人气榜字段:")
data = hot_rank.get_stock_popularity_rank()
if data and len(data) > 0:
    print(f"   数量: {len(data)}")
    print(f"   字段: {list(data[0].keys())}")
    print(f"   第1条: {data[0]}")
    print(f"   第2条: {data[1]}")
else:
    print("   ❌ 无数据")

print("\n" + "="*60)
