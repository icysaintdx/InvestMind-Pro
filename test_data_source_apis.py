#!/usr/bin/env python3
"""
测试前端调用的数据源API响应时间
"""

import requests
import time

APIs = [
    ("新闻数据", "GET", "http://localhost:8000/api/news/unified/600547"),
    ("社交媒体", "GET", "http://localhost:8000/api/akshare/social-media/all"),
    ("宏观数据", "GET", "http://localhost:8000/api/akshare/macro/comprehensive"),
    ("资金流向", "GET", "http://localhost:8000/api/akshare/fund-flow/600547"),
    ("板块数据", "GET", "http://localhost:8000/api/akshare/sector/comprehensive"),
]

print("="*70)
print("测试数据源API响应时间")
print("="*70)
print()

results = []

for name, method, url in APIs:
    print(f"测试: {name}")
    print(f"URL: {url}")
    
    start_time = time.time()
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=60)
        else:
            response = requests.post(url, timeout=60)
        
        elapsed = time.time() - start_time
        
        print(f"状态码: {response.status_code}")
        print(f"耗时: {elapsed:.1f}秒")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"成功: {result.get('success', 'N/A')}")
                if 'sources' in result:
                    print(f"数据源数量: {len(result['sources'])}")
                print("✅ 成功")
            except:
                print("⚠️ 响应不是JSON")
        else:
            print(f"❌ 失败: HTTP {response.status_code}")
        
        results.append({
            "name": name,
            "elapsed": elapsed,
            "status": response.status_code,
            "success": response.status_code == 200
        })
        
    except requests.Timeout:
        elapsed = time.time() - start_time
        print(f"⏱️ 超时 ({elapsed:.1f}秒)")
        results.append({
            "name": name,
            "elapsed": elapsed,
            "status": 0,
            "success": False
        })
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ 错误: {e}")
        results.append({
            "name": name,
            "elapsed": elapsed,
            "status": 0,
            "success": False
        })
    
    print()

# 总结
print("="*70)
print("总结")
print("="*70)
print()

print(f"{'API名称':<15} {'耗时':<10} {'状态':<10}")
print("-" * 40)

for r in results:
    status = "✅ 成功" if r['success'] else "❌ 失败"
    print(f"{r['name']:<15} {r['elapsed']:.1f}秒{'':<5} {status}")

print()

# 计算总耗时
total_time = sum(r['elapsed'] for r in results)
avg_time = total_time / len(results)

print(f"总耗时: {total_time:.1f}秒")
print(f"平均耗时: {avg_time:.1f}秒")
print()

# 找出最慢的
slowest = max(results, key=lambda x: x['elapsed'])
print(f"最慢的API: {slowest['name']} ({slowest['elapsed']:.1f}秒)")

print()
print("🎯 如果某个API超过10秒，它就是导致卡顿的原因！")
