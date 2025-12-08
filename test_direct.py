"""
直接测试并输出结果
"""
import asyncio
import httpx
import time
import sys

# 确保输出可见
sys.stdout.reconfigure(encoding='utf-8')

KEY = "sk-gdunxgtyhqokufmvnzjgsxsrqvfrxicigzslhzjrwlwejtyv"
URL = "https://api.siliconflow.cn/v1/chat/completions"

async def test():
    print("Starting test...")
    
    # 共享客户端
    client = httpx.AsyncClient(
        limits=httpx.Limits(max_connections=50, max_keepalive_connections=20),
        timeout=httpx.Timeout(15.0)
    )
    
    async def req(n):
        data = {
            "model": "Qwen/Qwen3-8B",
            "messages": [{"role": "user", "content": "test" * 500}],
            "max_tokens": 30
        }
        print(f"Request {n} starting...")
        try:
            r = await client.post(URL, 
                headers={"Authorization": f"Bearer {KEY}"},
                json=data)
            print(f"Request {n}: SUCCESS")
            return True
        except Exception as e:
            print(f"Request {n}: FAILED - {e}")
            return False
    
    # 测试3个并发
    print("\nTesting 3 concurrent requests with shared client:")
    start = time.time()
    
    try:
        results = await asyncio.wait_for(
            asyncio.gather(req(1), req(2), req(3)),
            timeout=30.0
        )
        elapsed = time.time() - start
        print(f"Completed: {sum(results)}/3 in {elapsed:.1f}s")
    except asyncio.TimeoutError:
        elapsed = time.time() - start
        print(f"TIMEOUT after {elapsed:.1f}s - DEADLOCK!")
    
    await client.aclose()
    
    print("\nDone!")

asyncio.run(test())
