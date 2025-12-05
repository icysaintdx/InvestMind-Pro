#!/usr/bin/env python3
"""
测试API端点
"""

import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 80)
print("🧪 测试统一新闻API端点")
print("=" * 80)
print()
print("⚠️ 请确保后端服务器正在运行: python backend/server.py")
print()

# 测试1: 健康检查
print("🏥 测试1: 健康检查")
print("-" * 80)

try:
    response = requests.get(f"{BASE_URL}/api/unified-news/health", timeout=5)
    if response.status_code == 200:
        data = response.json()
        print("✅ 健康检查成功")
        print(f"状态: {data.get('status')}")
        print(f"端点: {data.get('endpoints')}")
    else:
        print(f"❌ 健康检查失败: {response.status_code}")
except Exception as e:
    print(f"❌ 连接失败: {e}")
    print("请确保后端服务器正在运行")

print("\n")

# 测试2: 股票综合新闻
print("📰 测试2: 股票综合新闻")
print("-" * 80)

try:
    response = requests.post(
        f"{BASE_URL}/api/unified-news/stock",
        json={"ticker": "600519"},
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ 获取成功")
        print(f"股票: {data.get('ticker')}")
        print(f"时间: {data.get('timestamp')}")
        
        result = data.get('data', {})
        summary = result.get('summary', {})
        sources = summary.get('data_sources', {})
        
        print(f"\n数据源统计:")
        print(f"  成功: {sources.get('success')}/{sources.get('total')}")
        print(f"  成功率: {sources.get('success_rate')}")
        
        print(f"\n各数据源:")
        for source_name, source_data in result.get('sources', {}).items():
            status = source_data.get('status')
            if status == 'success':
                count = source_data.get('count', 'N/A')
                print(f"  ✅ {source_name}: {count}条")
            else:
                print(f"  ❌ {source_name}: {status}")
                
    else:
        print(f"❌ 获取失败: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"❌ 请求失败: {e}")

print("\n")

# 测试3: 市场新闻
print("🌍 测试3: 市场新闻")
print("-" * 80)

try:
    response = requests.get(f"{BASE_URL}/api/unified-news/market", timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ 获取成功")
        
        result = data.get('data', {})
        for source_name, source_data in result.get('sources', {}).items():
            status = source_data.get('status')
            if status == 'success':
                count = source_data.get('count', 'N/A')
                print(f"  ✅ {source_name}: {count}条")
            else:
                print(f"  ❌ {source_name}: {status}")
                
    else:
        print(f"❌ 获取失败: {response.status_code}")
        
except Exception as e:
    print(f"❌ 请求失败: {e}")

print("\n")

# 测试4: 热搜
print("🔥 测试4: 热搜")
print("-" * 80)

try:
    response = requests.get(f"{BASE_URL}/api/unified-news/hot-search", timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ 获取成功")
        
        result = data.get('data', {})
        weibo = result.get('weibo', {})
        baidu = result.get('baidu', {})
        
        print(f"  微博: 总计 {weibo.get('total')} 条，股票相关 {weibo.get('stock_related')} 条")
        print(f"  百度: 总计 {baidu.get('total')} 条，股票相关 {baidu.get('stock_related')} 条")
        
    else:
        print(f"❌ 获取失败: {response.status_code}")
        
except Exception as e:
    print(f"❌ 请求失败: {e}")

print("\n")
print("=" * 80)
print("📋 测试总结")
print("=" * 80)
print()
print("API端点:")
print("1. GET  /api/unified-news/health - 健康检查")
print("2. POST /api/unified-news/stock - 股票综合新闻")
print("3. GET  /api/unified-news/market - 市场新闻")
print("4. GET  /api/unified-news/hot-search - 热搜")
print()
print("API文档: http://localhost:8000/docs")
print()
