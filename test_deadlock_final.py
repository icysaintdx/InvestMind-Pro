#!/usr/bin/env python3
"""
最终测试：确认是否是 httpx 连接池死锁
直接打印到控制台，使用简单的测试
"""
import asyncio
import httpx
import time

# API配置
API_KEY = "sk-gdunxgtyhqokufmvnzjgsxsrqvfrxicigzslhzjrwlwejtyv"
API_URL = "https://api.siliconflow.cn/v1/chat/completions"

print("="*60)
print("Testing httpx Connection Pool Deadlock")
print("="*60)

async def test_shared():
    """Test with shared client (like current backend)"""
    print("\n1. Testing SHARED client (current backend behavior):")
    print("-" * 40)
    
    # Create shared client
    client = httpx.AsyncClient(
        limits=httpx.Limits(max_connections=50, max_keepalive_connections=20),
        timeout=httpx.Timeout(30.0)  # 30 second timeout for testing
    )
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    async def make_request(name, size):
        data = {
            "model": "Qwen/Qwen3-8B",
            "messages": [
                {"role": "user", "content": "test" * size}
            ],
            "max_tokens": 50
        }
        
        print(f"  [{name}] Starting request ({size*4} chars)...")
        start = time.time()
        try:
            response = await client.post(API_URL, headers=headers, json=data)
            elapsed = time.time() - start
            print(f"  [{name}] SUCCESS in {elapsed:.1f}s")
            return True
        except Exception as e:
            elapsed = time.time() - start
            print(f"  [{name}] FAILED after {elapsed:.1f}s: {type(e).__name__}")
            return False
    
    # First wave: 2 requests
    print("\n  Wave 1: 2 concurrent requests (small)")
    results = await asyncio.gather(
        make_request("req1", 500),
        make_request("req2", 500)
    )
    print(f"  Wave 1 result: {sum(results)}/2 succeeded")
    
    # Second wave: 3 requests (this is where it might fail)
    print("\n  Wave 2: 3 concurrent requests (large)")
    try:
        results = await asyncio.wait_for(
            asyncio.gather(
                make_request("req3", 1200),
                make_request("req4", 1200),
                make_request("req5", 1200)
            ),
            timeout=60.0
        )
        print(f"  Wave 2 result: {sum(results)}/3 succeeded")
    except asyncio.TimeoutError:
        print("  Wave 2: TIMEOUT! Requests stuck (deadlock confirmed)")
    
    await client.aclose()

async def test_independent():
    """Test with independent clients (proposed fix)"""
    print("\n2. Testing INDEPENDENT clients (proposed fix):")
    print("-" * 40)
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    async def make_request(name, size):
        # Create new client for each request
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            data = {
                "model": "Qwen/Qwen3-8B",
                "messages": [
                    {"role": "user", "content": "test" * size}
                ],
                "max_tokens": 50
            }
            
            print(f"  [{name}] Starting request ({size*4} chars)...")
            start = time.time()
            try:
                response = await client.post(API_URL, headers=headers, json=data)
                elapsed = time.time() - start
                print(f"  [{name}] SUCCESS in {elapsed:.1f}s")
                return True
            except Exception as e:
                elapsed = time.time() - start
                print(f"  [{name}] FAILED after {elapsed:.1f}s: {type(e).__name__}")
                return False
    
    # First wave: 2 requests
    print("\n  Wave 1: 2 concurrent requests (small)")
    results = await asyncio.gather(
        make_request("req1", 500),
        make_request("req2", 500)
    )
    print(f"  Wave 1 result: {sum(results)}/2 succeeded")
    
    # Second wave: 3 requests
    print("\n  Wave 2: 3 concurrent requests (large)")
    results = await asyncio.gather(
        make_request("req3", 1200),
        make_request("req4", 1200),
        make_request("req5", 1200)
    )
    print(f"  Wave 2 result: {sum(results)}/3 succeeded")

async def main():
    # Test shared client
    await test_shared()
    
    print("\nWaiting 5 seconds before next test...")
    await asyncio.sleep(5)
    
    # Test independent clients
    await test_independent()
    
    print("\n" + "="*60)
    print("CONCLUSION:")
    print("If shared client times out but independent works,")
    print("then it's confirmed: httpx connection pool deadlock!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
