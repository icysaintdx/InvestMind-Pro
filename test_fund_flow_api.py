"""
测试资金流向API
"""
import asyncio
import httpx

async def test_fund_flow_api():
    """测试资金流向API"""
    url = "http://localhost:8000/api/akshare/fund-flow/002451"
    
    print(f"测试URL: {url}")
    print("-" * 60)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=30.0)
            print(f"状态码: {response.status_code}")
            print(f"响应内容:")
            
            if response.status_code == 200:
                result = response.json()
                print(f"success: {result.get('success')}")
                print(f"sources: {result.get('sources')}")
                print(f"data keys: {list(result.get('data', {}).keys())}")
                
                # 打印完整响应
                import json
                print("\n完整响应:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print(response.text)
                
        except Exception as e:
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fund_flow_api())
