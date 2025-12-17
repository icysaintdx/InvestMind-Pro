"""
测试API修复
"""
import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 80)
print("测试API修复")
print("=" * 80)

# 测试1: 策略列表API
print("\n[测试1] 策略列表API")
try:
    response = requests.get(f"{BASE_URL}/api/backtest/strategies")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 成功获取 {data['total']} 个策略")
        # 检查VegasADXStrategy
        vegas_strategy = next((s for s in data['strategies'] if s['id'] == 'vegas_adx'), None)
        if vegas_strategy:
            print(f"✅ VegasADXStrategy 包含 description: {vegas_strategy.get('description', 'N/A')}")
        else:
            print("❌ 未找到 VegasADXStrategy")
    else:
        print(f"❌ 失败: {response.text}")
except Exception as e:
    print(f"❌ 错误: {e}")

# 测试2: 交易账户列表API
print("\n[测试2] 交易账户列表API")
try:
    response = requests.get(f"{BASE_URL}/api/trading/accounts")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 成功获取账户列表")
        print(f"   账户数量: {data.get('total', 0)}")
        if data.get('accounts'):
            print(f"   第一个账户: {data['accounts'][0].get('name', 'N/A')}")
    else:
        print(f"❌ 失败: {response.text}")
except Exception as e:
    print(f"❌ 错误: {e}")

# 测试3: 创建账户API
print("\n[测试3] 创建账户API")
try:
    response = requests.post(f"{BASE_URL}/api/trading/account/create")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 成功: {data.get('message', 'N/A')}")
    else:
        print(f"❌ 失败: {response.text}")
except Exception as e:
    print(f"❌ 错误: {e}")

# 测试4: 快速回测API（使用strategy_id）
print("\n[测试4] 快速回测API（使用strategy_id）")
try:
    payload = {
        "stock_code": "600519",
        "strategy_id": "vegas_adx",  # 使用strategy_id
        "start_date": "2024-01-01",
        "end_date": "2024-12-01",
        "initial_capital": 100000
    }
    response = requests.post(f"{BASE_URL}/api/backtest/quick", json=payload)
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 回测成功")
        print(f"   股票代码: {data.get('summary', {}).get('stock_code', 'N/A')}")
        print(f"   策略: {data.get('summary', {}).get('strategy', 'N/A')}")
    elif response.status_code == 422:
        print(f"❌ 参数验证失败: {response.json()}")
    else:
        print(f"❌ 失败: {response.text}")
except Exception as e:
    print(f"❌ 错误: {e}")

# 测试5: 快速回测API（使用strategy_name）
print("\n[测试5] 快速回测API（使用strategy_name）")
try:
    payload = {
        "stock_code": "600519",
        "strategy_name": "vegas_adx",  # 使用strategy_name
        "start_date": "2024-01-01",
        "end_date": "2024-12-01",
        "initial_capital": 100000
    }
    response = requests.post(f"{BASE_URL}/api/backtest/quick", json=payload)
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 回测成功")
        print(f"   总收益: {data.get('summary', {}).get('total_return', 'N/A')}")
    elif response.status_code == 422:
        print(f"❌ 参数验证失败: {response.json()}")
    else:
        print(f"❌ 失败: {response.text}")
except Exception as e:
    print(f"❌ 错误: {e}")

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)
