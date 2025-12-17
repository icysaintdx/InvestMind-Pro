"""
测试策略列表API
"""
import requests
import json

def test_strategies_api():
    """测试获取策略列表API"""
    print("=" * 60)
    print("测试策略列表API")
    print("=" * 60)
    
    url = "http://localhost:8000/api/backtest/strategies"
    
    try:
        print(f"\n请求URL: {url}")
        response = requests.get(url)
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ 成功获取策略列表！")
            print(f"策略总数: {data['total']}")
            print(f"\n策略列表:")
            print("-" * 60)
            
            for i, strategy in enumerate(data['strategies'], 1):
                print(f"\n{i}. {strategy['icon']} {strategy['name']}")
                print(f"   ID: {strategy['id']}")
                print(f"   类别: {strategy['category']}")
                print(f"   描述: {strategy['description']}")
                if strategy.get('avgWinRate'):
                    print(f"   平均胜率: {strategy['avgWinRate']:.1%}")
                print(f"   参数: {list(strategy['parameters'].keys())}")
            
            print("\n" + "=" * 60)
            print(f"✅ 测试通过！共{data['total']}个策略")
            print("=" * 60)
            
        else:
            print(f"\n❌ 请求失败")
            print(f"响应: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到服务器")
        print("请确保后端服务器正在运行: python -m uvicorn backend.server:app --reload")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_strategies_api()
