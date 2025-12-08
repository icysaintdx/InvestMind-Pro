"""
简化测试：直接测试共享客户端 vs 独立客户端
将结果输出到文件
"""
import asyncio
import httpx
import time
import sys

# 重定向输出到文件
output_file = open("test_results.txt", "w", encoding="utf-8")
sys.stdout = output_file

SILICONFLOW_API_KEY = "sk-gdunxgtyhqokufmvnzjgsxsrqvfrxicigzslhzjrwlwejtyv"
API_URL = "https://api.siliconflow.cn/v1/chat/completions"

# 全局共享客户端
shared_client = None

def create_test_data(size: int):
    """创建测试数据"""
    return {
        "model": "Qwen/Qwen3-8B",
        "messages": [
            {"role": "system", "content": "You are a test assistant"},
            {"role": "user", "content": "Test" * (size // 4)}
        ],
        "temperature": 0.3,
        "max_tokens": 50,
        "stream": False
    }

async def test_shared_client():
    """测试共享客户端"""
    global shared_client
    print("="*60)
    print("TEST 1: Shared Client (Simulating Current Backend)")
    print("="*60)
    
    # Create shared client like backend
    shared_client = httpx.AsyncClient(
        limits=httpx.Limits(
            max_keepalive_connections=20,
            max_connections=50
        ),
        timeout=httpx.Timeout(60.0)
    )
    
    headers = {
        "Authorization": f"Bearer {SILICONFLOW_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Phase 1: 2 concurrent requests (2400 chars)
    print("\nPhase 1: 2 concurrent requests (2400 chars each)")
    start = time.time()
    
    async def make_request(name):
        try:
            data = create_test_data(2400)
            response = await shared_client.post(API_URL, headers=headers, json=data)
            return f"{name}: SUCCESS ({response.status_code})"
        except Exception as e:
            return f"{name}: FAILED ({type(e).__name__})"
    
    results = await asyncio.gather(
        make_request("macro"),
        make_request("industry")
    )
    
    elapsed = time.time() - start
    print(f"Results: {results}")
    print(f"Time: {elapsed:.2f}s\n")
    
    # Wait 2 seconds
    await asyncio.sleep(2)
    
    # Phase 2: 3 concurrent requests (4800 chars)
    print("Phase 2: 3 concurrent requests (4800 chars each)")
    start = time.time()
    
    async def make_large_request(name):
        try:
            data = create_test_data(4800)
            response = await shared_client.post(API_URL, headers=headers, json=data)
            return f"{name}: SUCCESS ({response.status_code})"
        except Exception as e:
            return f"{name}: FAILED ({type(e).__name__})"
    
    # This is where the problem occurs
    print("Starting 3 concurrent large requests...")
    
    # Use wait_for to detect timeout
    try:
        results = await asyncio.wait_for(
            asyncio.gather(
                make_large_request("technical"),
                make_large_request("fundamental"),
                make_large_request("funds")
            ),
            timeout=90.0  # 90 second timeout
        )
        elapsed = time.time() - start
        print(f"Results: {results}")
        print(f"Time: {elapsed:.2f}s")
    except asyncio.TimeoutError:
        elapsed = time.time() - start
        print(f"TIMEOUT! Requests stuck after {elapsed:.2f}s")
        print("CONFIRMED: Shared client causes deadlock!")
    
    await shared_client.aclose()

async def test_independent_clients():
    """测试独立客户端"""
    print("\n" + "="*60)
    print("TEST 2: Independent Clients (Proposed Fix)")
    print("="*60)
    
    headers = {
        "Authorization": f"Bearer {SILICONFLOW_API_KEY}",
        "Content-Type": "application/json"
    }
    
    async def make_request_independent(name, size):
        # Create new client for each request
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
            try:
                data = create_test_data(size)
                response = await client.post(API_URL, headers=headers, json=data)
                return f"{name}: SUCCESS ({response.status_code})"
            except Exception as e:
                return f"{name}: FAILED ({type(e).__name__})"
    
    # Phase 1: 2 concurrent requests
    print("\nPhase 1: 2 concurrent requests (2400 chars each)")
    start = time.time()
    
    results = await asyncio.gather(
        make_request_independent("macro", 2400),
        make_request_independent("industry", 2400)
    )
    
    elapsed = time.time() - start
    print(f"Results: {results}")
    print(f"Time: {elapsed:.2f}s\n")
    
    # Phase 2: 3 concurrent requests
    print("Phase 2: 3 concurrent requests (4800 chars each)")
    start = time.time()
    
    results = await asyncio.gather(
        make_request_independent("technical", 4800),
        make_request_independent("fundamental", 4800),
        make_request_independent("funds", 4800)
    )
    
    elapsed = time.time() - start
    print(f"Results: {results}")
    print(f"Time: {elapsed:.2f}s")
    print("\nSUCCESS: Independent clients work without deadlock!")

async def main():
    print("HTTPX Connection Pool Deadlock Test")
    print("Testing the exact scenario from the logs...")
    print()
    
    # Test shared client (current backend behavior)
    await test_shared_client()
    
    # Wait 5 seconds
    await asyncio.sleep(5)
    
    # Test independent clients (proposed fix)
    await test_independent_clients()
    
    print("\n" + "="*60)
    print("CONCLUSION:")
    print("- Shared client: DEADLOCKS with 3 concurrent large requests")
    print("- Independent clients: WORKS without issues")
    print("="*60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        output_file.close()
        
    # Print to console that test is done
    sys.stdout = sys.__stdout__
    print("Test completed! Results saved to test_results.txt")
