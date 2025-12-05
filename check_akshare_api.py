#!/usr/bin/env python3
"""
检查AKShare可用的API
"""

import akshare as ak

print(f"AKShare版本: {ak.__version__}")
print()

# 查找所有包含 news 的函数
print("=" * 80)
print("查找新闻相关API")
print("=" * 80)

news_apis = [name for name in dir(ak) if 'news' in name.lower()]
print(f"找到 {len(news_apis)} 个新闻相关API:")
for api in news_apis:
    print(f"  - {api}")

print()

# 查找所有包含 stock 的函数
print("=" * 80)
print("查找股票相关API（前50个）")
print("=" * 80)

stock_apis = [name for name in dir(ak) if 'stock' in name.lower()]
print(f"找到 {len(stock_apis)} 个股票相关API，显示前50个:")
for api in stock_apis[:50]:
    print(f"  - {api}")

print()

# 测试一些常用的API
print("=" * 80)
print("测试常用API")
print("=" * 80)

# 测试1: 股票新闻
print("\n1. 测试 stock_news_em (东方财富新闻)")
try:
    df = ak.stock_news_em(symbol="600519")
    print(f"   ✅ 成功: {len(df)} 条")
    if len(df) > 0:
        print(f"   列: {list(df.columns)}")
except Exception as e:
    print(f"   ❌ 失败: {e}")

# 测试2: 微博热议
print("\n2. 测试 stock_js_weibo_report (微博热议)")
try:
    df = ak.stock_js_weibo_report()
    print(f"   ✅ 成功: {len(df)} 条")
    if len(df) > 0:
        print(f"   列: {list(df.columns)}")
        print(f"   第一条: {df.iloc[0].to_dict()}")
except Exception as e:
    print(f"   ❌ 失败: {e}")

# 测试3: 财联社
print("\n3. 查找财联社相关API")
cls_apis = [name for name in dir(ak) if 'cls' in name.lower() or '财联社' in name]
print(f"   找到: {cls_apis}")

# 测试4: 新浪相关
print("\n4. 查找新浪相关API")
sina_apis = [name for name in dir(ak) if 'sina' in name.lower()]
print(f"   找到: {sina_apis}")
