"""测试K线API"""
import requests

# 测试K线数据
print("测试K线数据API...")
response = requests.get(
    'http://localhost:8000/api/kline/data',
    params={
        'symbol': '600519',
        'period': 'daily',
        'limit': 10
    }
)

print(f"状态码: {response.status_code}")
print(f"响应: {response.json()}")

if response.status_code == 200:
    data = response.json()
    if data['success']:
        print(f"\n成功获取{data['count']}条数据")
        if data['data']:
            print(f"第一条数据: {data['data'][0]}")
    else:
        print("获取失败")
else:
    print(f"错误: {response.text}")
