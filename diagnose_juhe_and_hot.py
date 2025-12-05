#!/usr/bin/env python3
"""
诊断聚合数据和热搜API
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 80)
print("🔍 诊断聚合数据和热搜API")
print("=" * 80)
print()

# 测试1: 聚合数据API
print("📊 测试1: 聚合数据API")
print("-" * 80)

juhe_key = os.getenv('JUHE_API_KEY')
if juhe_key:
    print(f"API Key: {juhe_key[:10]}...")
    
    url = "http://web.juhe.cn:8080/finance/stock/hs"
    params = {
        'gid': '600519',  # 贵州茅台
        'key': juhe_key
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应长度: {len(response.text)}")
        print()
        
        data = response.json()
        print("JSON结构:")
        print(json.dumps(data, ensure_ascii=False, indent=2)[:1000])
        
        if data.get('result'):
            result = data['result'][0] if isinstance(data['result'], list) else data['result']
            print("\n实际字段:")
            for key in result.keys():
                print(f"  - {key}: {result[key]}")
                
    except Exception as e:
        print(f"错误: {e}")
else:
    print("❌ 未配置 JUHE_API_KEY")

print("\n")

# 测试2: 微博热搜API
print("📱 测试2: 微博热搜API")
print("-" * 80)

urls = [
    "https://api.aa1.cn/api/weibo-rs",
    "https://api.vvhan.com/api/hotlist/wbHot",
    "https://tenapi.cn/v2/wbhot"
]

for url in urls:
    print(f"\n尝试: {url}")
    try:
        response = requests.get(url, timeout=10)
        print(f"  状态码: {response.status_code}")
        print(f"  Content-Type: {response.headers.get('Content-Type')}")
        print(f"  响应长度: {len(response.text)}")
        print(f"  前200字符: {response.text[:200]}")
        
        # 尝试解析JSON
        try:
            data = response.json()
            print(f"  ✅ JSON解析成功")
            print(f"  数据类型: {type(data)}")
            if isinstance(data, dict):
                print(f"  字典键: {list(data.keys())}")
            elif isinstance(data, list):
                print(f"  列表长度: {len(data)}")
                if data:
                    print(f"  第一项: {data[0]}")
        except:
            print(f"  ❌ JSON解析失败")
            
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")

print("\n")

# 测试3: 百度热搜API
print("🔍 测试3: 百度热搜API")
print("-" * 80)

urls = [
    "https://api.aa1.cn/api/baidu-rs",
    "https://api.vvhan.com/api/hotlist/baiduRD",
    "https://tenapi.cn/v2/baiduhot"
]

for url in urls:
    print(f"\n尝试: {url}")
    try:
        response = requests.get(url, timeout=10)
        print(f"  状态码: {response.status_code}")
        print(f"  Content-Type: {response.headers.get('Content-Type')}")
        print(f"  响应长度: {len(response.text)}")
        print(f"  前200字符: {response.text[:200]}")
        
        # 尝试解析JSON
        try:
            data = response.json()
            print(f"  ✅ JSON解析成功")
            print(f"  数据类型: {type(data)}")
            if isinstance(data, dict):
                print(f"  字典键: {list(data.keys())}")
            elif isinstance(data, list):
                print(f"  列表长度: {len(data)}")
        except:
            print(f"  ❌ JSON解析失败")
            
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")

print("\n")
print("=" * 80)
print("📋 诊断完成")
print("=" * 80)
