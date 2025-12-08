#!/usr/bin/env python3
"""
简单测试 - 查看具体的错误信息
"""

import requests
import json

url = "http://localhost:8000/api/analyze"

# 简单的测试数据
payload = {
    "agent_id": "test_agent",
    "stock_code": "600547",
    "stock_data": {
        "symbol": "600547",
        "name": "山东黄金",
        "price": 10.50,
        "change": 2.5,
        "volume": 1000000
    },
    "previous_outputs": {
        "agent_1": "这是一段测试内容" * 100  # 约1000字符
    },
    "custom_instruction": "请给出分析"
}

print("发送测试请求...")
print(f"URL: {url}")
print(f"Payload keys: {payload.keys()}")
print(f"前序输出长度: {len(payload['previous_outputs']['agent_1'])} 字符")
print()

try:
    response = requests.post(url, json=payload, timeout=30)
    
    print(f"状态码: {response.status_code}")
    print(f"响应头: {dict(response.headers)}")
    print()
    print("响应内容:")
    print(response.text)
    
    if response.status_code == 200:
        result = response.json()
        print()
        print("解析后的JSON:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
