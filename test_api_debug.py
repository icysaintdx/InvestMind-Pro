"""
调试API返回数据
"""
import requests
import json

url = "http://localhost:8000/api/backtest/strategies"

try:
    response = requests.get(url)
    print(f"状态码: {response.status_code}")
    print(f"\n原始响应文本:")
    print(response.text[:500])  # 只显示前500字符
    
    print(f"\n响应类型: {type(response.json())}")
    data = response.json()
    
    if isinstance(data, list):
        print(f"\n❌ 返回的是列表，长度: {len(data)}")
        print(f"第一个元素: {data[0] if data else 'empty'}")
    elif isinstance(data, dict):
        print(f"\n✅ 返回的是字典")
        print(f"键: {list(data.keys())}")
        print(f"total: {data.get('total')}")
        print(f"success: {data.get('success')}")
        print(f"strategies数量: {len(data.get('strategies', []))}")
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
