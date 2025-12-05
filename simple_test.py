#!/usr/bin/env python3
"""
简单测试 - 直接测试API
"""

import requests

print("测试微博热搜API...")
print("=" * 60)

try:
    url = "https://api.aa1.cn/api/weibo-rs"
    print(f"请求: {url}")
    
    response = requests.get(url, timeout=10)
    print(f"状态码: {response.status_code}")
    print(f"内容长度: {len(response.text)}")
    print()
    print("响应内容:")
    print(response.text[:1000])
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
