"""
测试股票API端点
"""

import requests
import json

# 测试配置
API_BASE = "http://localhost:8000"
test_symbol = "000001"

print("="*60)
print("测试股票API端点")
print("="*60)

# 1. 测试GET请求
print("\n1. 测试GET请求:")
print(f"   URL: {API_BASE}/api/stock/{test_symbol}")
try:
    response = requests.get(f"{API_BASE}/api/stock/{test_symbol}", timeout=10)
    print(f"   状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print(f"   ✅ 成功")
            print(f"   数据源: {data.get('data_source')}")
            print(f"   股票名: {data.get('name')}")
            print(f"   价格: ¥{data.get('price')}")
            print(f"   涨跌幅: {data.get('change')}%")
        else:
            print(f"   ❌ 失败: {data.get('error')}")
    elif response.status_code == 405:
        print(f"   ❌ 方法不允许 (405) - GET方法未启用")
    else:
        print(f"   ❌ HTTP错误: {response.status_code}")
        print(f"   响应: {response.text[:200]}")
except Exception as e:
    print(f"   ❌ 请求失败: {str(e)}")
    print(f"   请确保后端服务已启动: python backend/server.py")

# 2. 测试POST请求
print("\n2. 测试POST请求:")
print(f"   URL: {API_BASE}/api/stock/{test_symbol}")
try:
    payload = {"symbol": test_symbol}
    response = requests.post(
        f"{API_BASE}/api/stock/{test_symbol}", 
        json=payload,
        timeout=10
    )
    print(f"   状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print(f"   ✅ 成功")
            print(f"   数据源: {data.get('data_source')}")
            print(f"   股票名: {data.get('name')}")
            print(f"   价格: ¥{data.get('price')}")
            print(f"   涨跌幅: {data.get('change')}%")
        else:
            print(f"   ❌ 失败: {data.get('error')}")
    else:
        print(f"   ❌ HTTP错误: {response.status_code}")
        print(f"   响应: {response.text[:200]}")
except Exception as e:
    print(f"   ❌ 请求失败: {str(e)}")

# 3. 测试多个股票
print("\n3. 测试多个股票代码:")
test_codes = {
    "000001": "平安银行",
    "600519": "贵州茅台", 
    "002230": "科大讯飞",
    "300750": "宁德时代"
}

for code, name in test_codes.items():
    try:
        response = requests.get(f"{API_BASE}/api/stock/{code}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"   {code} ({name}): ¥{data.get('price')} [{data.get('data_source')}]")
            else:
                print(f"   {code} ({name}): 获取失败")
        else:
            print(f"   {code} ({name}): HTTP {response.status_code}")
    except Exception as e:
        print(f"   {code} ({name}): 异常 - {str(e)[:50]}")

print("\n" + "="*60)
print("测试完成！")
print("="*60)
