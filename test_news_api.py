#!/usr/bin/env python3
"""
测试新闻API端点
"""

import requests
import json
from datetime import datetime

print("=" * 80)
print("🧪 测试新闻API端点")
print("=" * 80)
print()

# 测试参数
test_ticker = "600519"
test_date = datetime.now().strftime('%Y-%m-%d')

print(f"测试股票: {test_ticker}")
print(f"测试日期: {test_date}")
print()

# 测试API
print("📡 发送请求到 http://localhost:8000/api/news/realtime")
print()

try:
    response = requests.post(
        'http://localhost:8000/api/news/realtime',
        json={
            'ticker': test_ticker,
            'curr_date': test_date,
            'hours_back': 6
        },
        timeout=30
    )
    
    print(f"响应状态码: {response.status_code}")
    print()
    
    if response.status_code == 200:
        result = response.json()
        
        print("✅ API调用成功!")
        print()
        print("📊 返回数据:")
        print(f"  - success: {result.get('success')}")
        print(f"  - ticker: {result.get('ticker')}")
        print(f"  - date: {result.get('date')}")
        print(f"  - source: {result.get('source')}")
        print(f"  - news_count: {result.get('news_count')}")
        print(f"  - fetch_time: {result.get('fetch_time')}秒")
        print(f"  - report_length: {len(result.get('report', ''))}字符")
        print()
        
        # 显示报告前500字符
        report = result.get('report', '')
        if report:
            print("📰 新闻报告预览 (前500字符):")
            print("-" * 80)
            print(report[:500])
            print("-" * 80)
        else:
            print("⚠️ 报告为空")
            
    else:
        print(f"❌ API调用失败: HTTP {response.status_code}")
        print(f"响应内容: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("❌ 连接失败: 无法连接到后端服务器")
    print("   请确保后端服务器正在运行:")
    print("   python backend/server.py")
    
except requests.exceptions.Timeout:
    print("❌ 请求超时")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
print("测试完成")
print("=" * 80)
