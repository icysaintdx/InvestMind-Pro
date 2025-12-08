"""
测试 /api/analyze 端点
"""
import asyncio
import httpx
import json

async def test_analyze_endpoint():
    """测试 /api/analyze 端点"""
    url = "http://localhost:8000/api/analyze"
    
    # 构建测试数据（模拟最小请求）
    data = {
        "agent_id": "test_agent",
        "stock_code": "600177",
        "stock_data": {
            "name": "测试股票",
            "price": 10.0,
            "change": 0.5
        },
        "previous_outputs": [],
        "custom_instruction": ""
    }
    
    print(f"测试URL: {url}")
    print(f"请求数据:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print("-" * 60)
    
    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
        try:
            print("发送请求...")
            response = await client.post(
                url,
                json=data,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"响应成功:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print(f"响应错误:")
                print(response.text)
                
        except httpx.ConnectError as e:
            print(f"❌ 连接错误: 后端服务未启动或端口不对")
            print(f"   错误: {e}")
        except httpx.TimeoutException as e:
            print(f"❌ 超时错误: {e}")
        except Exception as e:
            print(f"❌ 其他错误: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_analyze_endpoint())
