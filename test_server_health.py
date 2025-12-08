"""
快速测试服务器健康状态
"""
import httpx
import time
import asyncio

async def test_health():
    url = "http://localhost:8000/docs"
    max_retries = 5
    
    for i in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=2)
                if response.status_code == 200:
                    print(f"✅ 服务器运行正常！")
                    return True
        except:
            print(f"⏳ 等待服务器启动... ({i+1}/{max_retries})")
            await asyncio.sleep(2)
    
    print("❌ 服务器未启动或有问题")
    return False

if __name__ == "__main__":
    asyncio.run(test_health())
