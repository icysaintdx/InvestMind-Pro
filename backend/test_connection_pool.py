"""
测试HTTP连接池性能提升效果
"""
import asyncio
import time
import httpx

async def test_without_pool():
    """测试不使用连接池的性能"""
    start_time = time.time()
    
    for i in range(5):
        async with httpx.AsyncClient() as client:
            response = await client.get("https://api.github.com")
            print(f"Request {i+1}: {response.status_code}")
    
    elapsed = time.time() - start_time
    print(f"不使用连接池: {elapsed:.2f}秒")
    return elapsed

async def test_with_pool():
    """测试使用连接池的性能"""
    start_time = time.time()
    
    # 创建一个带连接池的客户端
    async with httpx.AsyncClient(
        limits=httpx.Limits(
            max_keepalive_connections=10,
            max_connections=20
        )
    ) as client:
        for i in range(5):
            response = await client.get("https://api.github.com")
            print(f"Request {i+1}: {response.status_code}")
    
    elapsed = time.time() - start_time
    print(f"使用连接池: {elapsed:.2f}秒")
    return elapsed

async def main():
    print("=" * 50)
    print("HTTP连接池性能测试")
    print("=" * 50)
    
    print("\n1. 测试不使用连接池（每次创建新连接）：")
    time_without_pool = await test_without_pool()
    
    print("\n2. 测试使用连接池（复用连接）：")
    time_with_pool = await test_with_pool()
    
    print("\n" + "=" * 50)
    print("测试结果总结：")
    print(f"不使用连接池: {time_without_pool:.2f}秒")
    print(f"使用连接池: {time_with_pool:.2f}秒")
    improvement = ((time_without_pool - time_with_pool) / time_without_pool) * 100
    print(f"性能提升: {improvement:.1f}%")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
