"""
直接验证：是否真的是连接池死锁
"""
import asyncio
import httpx
import time
import json

# 写入结果到文件
def log(msg):
    print(msg)
    with open("deadlock_test_result.txt", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

async def main():
    # 清空结果文件
    open("deadlock_test_result.txt", "w").close()
    
    log("HTTPX CONNECTION POOL DEADLOCK VERIFICATION")
    log("=" * 60)
    
    API_KEY = "sk-gdunxgtyhqokufmvnzjgsxsrqvfrxicigzslhzjrwlwejtyv"
    API_URL = "https://api.siliconflow.cn/v1/chat/completions"
    
    # Test 1: Shared Client (Backend Current Behavior)
    log("\nTEST 1: SHARED CLIENT (like backend)")
    log("-" * 40)
    
    shared_client = httpx.AsyncClient(
        limits=httpx.Limits(
            max_connections=50,
            max_keepalive_connections=20
        ),
        timeout=httpx.Timeout(20.0)  # 20s timeout for testing
    )
    
    async def test_shared(name):
        try:
            start = time.time()
            response = await shared_client.post(
                API_URL,
                headers={"Authorization": f"Bearer {API_KEY}"},
                json={
                    "model": "Qwen/Qwen3-8B",
                    "messages": [{"role": "user", "content": "test" * 1000}],
                    "max_tokens": 50
                }
            )
            elapsed = time.time() - start
            log(f"  {name}: OK ({elapsed:.1f}s)")
            return True
        except Exception as e:
            elapsed = time.time() - start
            log(f"  {name}: FAIL ({elapsed:.1f}s) - {type(e).__name__}")
            return False
    
    # Run 3 concurrent requests
    log("Running 3 concurrent requests with shared client...")
    start = time.time()
    
    try:
        results = await asyncio.wait_for(
            asyncio.gather(
                test_shared("Request1"),
                test_shared("Request2"),
                test_shared("Request3")
            ),
            timeout=40.0  # 40s total timeout
        )
        total = time.time() - start
        success = sum(results)
        log(f"Result: {success}/3 succeeded in {total:.1f}s")
        
        if success < 3:
            log("WARNING: Some requests failed with shared client!")
    except asyncio.TimeoutError:
        total = time.time() - start
        log(f"TIMEOUT: Requests stuck after {total:.1f}s")
        log("DEADLOCK CONFIRMED: Shared client causes deadlock!")
    
    await shared_client.aclose()
    
    # Wait before next test
    await asyncio.sleep(3)
    
    # Test 2: Independent Clients
    log("\nTEST 2: INDEPENDENT CLIENTS (proposed fix)")
    log("-" * 40)
    
    async def test_independent(name):
        async with httpx.AsyncClient(timeout=httpx.Timeout(20.0)) as client:
            try:
                start = time.time()
                response = await client.post(
                    API_URL,
                    headers={"Authorization": f"Bearer {API_KEY}"},
                    json={
                        "model": "Qwen/Qwen3-8B",
                        "messages": [{"role": "user", "content": "test" * 1000}],
                        "max_tokens": 50
                    }
                )
                elapsed = time.time() - start
                log(f"  {name}: OK ({elapsed:.1f}s)")
                return True
            except Exception as e:
                elapsed = time.time() - start
                log(f"  {name}: FAIL ({elapsed:.1f}s) - {type(e).__name__}")
                return False
    
    log("Running 3 concurrent requests with independent clients...")
    start = time.time()
    
    results = await asyncio.gather(
        test_independent("Request1"),
        test_independent("Request2"),
        test_independent("Request3")
    )
    
    total = time.time() - start
    success = sum(results)
    log(f"Result: {success}/3 succeeded in {total:.1f}s")
    
    if success == 3:
        log("SUCCESS: All requests completed with independent clients!")
    
    # Conclusion
    log("\n" + "=" * 60)
    log("CONCLUSION:")
    
    with open("deadlock_test_result.txt", "r", encoding="utf-8") as f:
        content = f.read()
        
    if "DEADLOCK CONFIRMED" in content:
        log("✅ CONFIRMED: The problem IS httpx connection pool deadlock!")
        log("✅ SOLUTION: Use independent clients for each request")
    elif "WARNING" in content:
        log("⚠️  PARTIAL ISSUE: Shared client has problems but not full deadlock")
        log("✅ SOLUTION: Still recommend independent clients")
    else:
        log("❌ NOT CONFIRMED: The problem might be something else")
    
    log("=" * 60)
    log("\nTest complete! Check deadlock_test_result.txt for details.")

if __name__ == "__main__":
    asyncio.run(main())
