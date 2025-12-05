#!/usr/bin/env python3
"""测试微博相关API"""

import akshare as ak

print("测试AKShare微博相关接口...")
print("="*60)

# 查找所有包含weibo、hot、social的函数
all_funcs = dir(ak)
weibo_funcs = [f for f in all_funcs if 'weibo' in f.lower()]
hot_funcs = [f for f in all_funcs if 'hot' in f.lower()]
social_funcs = [f for f in all_funcs if 'social' in f.lower()]

print("\n微博相关函数:")
for f in weibo_funcs:
    print(f"  - {f}")

print("\n热搜相关函数:")
for f in hot_funcs[:10]:  # 只显示前10个
    print(f"  - {f}")

print("\n社交相关函数:")
for f in social_funcs:
    print(f"  - {f}")

# 测试已知的函数
print("\n" + "="*60)
print("测试已知函数...")

try:
    print("\n1. stock_js_weibo_report (微博股票热议):")
    df = ak.stock_js_weibo_report()
    print(f"   ✅ 成功！获取到 {len(df)} 条数据")
    if len(df) > 0:
        print(f"   示例: {df.iloc[0].to_dict()}")
except Exception as e:
    print(f"   ❌ 失败: {e}")

try:
    print("\n2. weibo_hot_search (微博热搜):")
    df = ak.weibo_hot_search()
    print(f"   ✅ 成功！获取到 {len(df)} 条数据")
    if len(df) > 0:
        print(f"   示例: {df.iloc[0].to_dict()}")
except Exception as e:
    print(f"   ❌ 失败: {e}")

try:
    print("\n3. stock_hot_search_baidu (百度热搜股票):")
    df = ak.stock_hot_search_baidu()
    print(f"   ✅ 成功！获取到 {len(df)} 条数据")
    if len(df) > 0:
        print(f"   示例: {df.iloc[0].to_dict()}")
except Exception as e:
    print(f"   ❌ 失败: {e}")

print("\n" + "="*60)
print("测试完成！")
