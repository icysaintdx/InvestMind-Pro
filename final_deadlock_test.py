"""
最终测试：将结果直接写入文件
"""
import asyncio
import httpx
import time
from datetime import datetime

# 结果文件
RESULT_FILE = "deadlock_verification.txt"

def write_result(msg):
    """写入结果到文件"""
    with open(RESULT_FILE, "a", encoding="utf-8") as f:
        timestamp = datetime.now().strftime("%H:%M:%S")
        f.write(f"[{timestamp}] {msg}\n")
        f.flush()
    print(msg)  # 同时打印到控制台

async def main():
    # 清空结果文件
    with open(RESULT_FILE, "w", encoding="utf-8") as f:
        f.write("=== HTTPX Connection Pool Deadlock Test ===\n")
        f.write(f"Test started at {datetime.now()}\n\n")
    
    KEY = "sk-gdunxgtyhqokufmvnzjgsxsrqvfrxicigzslhzjrwlwejtyv"
    URL = "https://api.siliconflow.cn/v1/chat/completions"
    
    # ========== TEST 1: Shared Client ==========
    write_result("TEST 1: SHARED CLIENT (simulating backend)")
    write_result("-" * 40)
    
    shared_client = httpx.AsyncClient(
        limits=httpx.Limits(
            max_connections=50,
            max_keepalive_connections=20,
            keepalive_expiry=30
        ),
        timeout=httpx.Timeout(
            connect=5.0,
            read=180.0,  # Same as backend
            write=10.0,
            pool=5.0
        )
    )
    
    async def test_with_shared(name, size):
        """使用共享客户端测试"""
        write_result(f"  {name} starting ({size} chars)...")
        start = time.time()
        
        try:
            response = await shared_client.post(
                URL,
                headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
                json={
                    "model": "Qwen/Qwen3-8B",
                    "messages": [
                        {"role": "system", "content": "You are an analyst"},
                        {"role": "user", "content": "Analyze" + "X" * size}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 100
                }
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                write_result(f"  {name} SUCCESS in {elapsed:.1f}s")
                return True
            else:
                write_result(f"  {name} HTTP {response.status_code} in {elapsed:.1f}s")
                return False
                
        except asyncio.TimeoutError:
            elapsed = time.time() - start
            write_result(f"  {name} TIMEOUT after {elapsed:.1f}s")
            return False
        except Exception as e:
            elapsed = time.time() - start
            write_result(f"  {name} ERROR: {type(e).__name__} after {elapsed:.1f}s")
            return False
    
    # Phase 1: 2 small requests
    write_result("\nPhase 1: 2 concurrent requests (2400 chars)")
    phase1_start = time.time()
    
    results1 = await asyncio.gather(
        test_with_shared("macro", 2400),
        test_with_shared("industry", 2400)
    )
    
    phase1_time = time.time() - phase1_start
    write_result(f"Phase 1 completed: {sum(results1)}/2 succeeded in {phase1_time:.1f}s")
    
    await asyncio.sleep(2)
    
    # Phase 2: 3 large requests (THIS IS WHERE IT FAILS)
    write_result("\nPhase 2: 3 concurrent requests (4800 chars)")
    write_result("⚠️  This is where the actual problem occurs")
    phase2_start = time.time()
    
    try:
        results2 = await asyncio.wait_for(
            asyncio.gather(
                test_with_shared("technical", 4800),
                test_with_shared("fundamental", 4800),
                test_with_shared("funds", 4800)
            ),
            timeout=60.0  # 60 second timeout
        )
        phase2_time = time.time() - phase2_start
        write_result(f"Phase 2 completed: {sum(results2)}/3 succeeded in {phase2_time:.1f}s")
        
    except asyncio.TimeoutError:
        phase2_time = time.time() - phase2_start
        write_result(f"Phase 2 TIMEOUT after {phase2_time:.1f}s")
        write_result("🔴 DEADLOCK CONFIRMED with shared client!")
    
    await shared_client.aclose()
    write_result("Shared client closed")
    
    # Wait before next test
    write_result("\nWaiting 5 seconds before next test...")
    await asyncio.sleep(5)
    
    # ========== TEST 2: Independent Clients ==========
    write_result("\nTEST 2: INDEPENDENT CLIENTS (proposed fix)")
    write_result("-" * 40)
    
    async def test_with_independent(name, size):
        """使用独立客户端测试"""
        write_result(f"  {name} starting ({size} chars)...")
        start = time.time()
        
        # Create new client for this request
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=10.0,
                read=120.0,
                write=10.0,
                pool=10.0
            ),
            limits=httpx.Limits(
                max_connections=10,
                max_keepalive_connections=5
            )
        ) as client:
            try:
                response = await client.post(
                    URL,
                    headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
                    json={
                        "model": "Qwen/Qwen3-8B",
                        "messages": [
                            {"role": "system", "content": "You are an analyst"},
                            {"role": "user", "content": "Analyze" + "X" * size}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 100
                    }
                )
                elapsed = time.time() - start
                
                if response.status_code == 200:
                    write_result(f"  {name} SUCCESS in {elapsed:.1f}s")
                    return True
                else:
                    write_result(f"  {name} HTTP {response.status_code} in {elapsed:.1f}s")
                    return False
                    
            except Exception as e:
                elapsed = time.time() - start
                write_result(f"  {name} ERROR: {type(e).__name__} after {elapsed:.1f}s")
                return False
    
    # Phase 1: 2 small requests
    write_result("\nPhase 1: 2 concurrent requests (2400 chars)")
    phase1_start = time.time()
    
    results1 = await asyncio.gather(
        test_with_independent("macro", 2400),
        test_with_independent("industry", 2400)
    )
    
    phase1_time = time.time() - phase1_start
    write_result(f"Phase 1 completed: {sum(results1)}/2 succeeded in {phase1_time:.1f}s")
    
    await asyncio.sleep(2)
    
    # Phase 2: 3 large requests
    write_result("\nPhase 2: 3 concurrent requests (4800 chars)")
    phase2_start = time.time()
    
    results2 = await asyncio.gather(
        test_with_independent("technical", 4800),
        test_with_independent("fundamental", 4800),
        test_with_independent("funds", 4800)
    )
    
    phase2_time = time.time() - phase2_start
    write_result(f"Phase 2 completed: {sum(results2)}/3 succeeded in {phase2_time:.1f}s")
    
    if sum(results2) == 3:
        write_result("🟢 SUCCESS with independent clients!")
    
    # ========== CONCLUSION ==========
    write_result("\n" + "="*60)
    write_result("CONCLUSION:")
    
    # Read the results to determine conclusion
    with open(RESULT_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    
    if "DEADLOCK CONFIRMED" in content and "SUCCESS with independent" in content:
        write_result("✅ CONFIRMED: The problem IS httpx connection pool deadlock!")
        write_result("✅ The shared client deadlocks with 3 concurrent large requests")
        write_result("✅ Independent clients solve the problem completely")
        write_result("\n📝 SOLUTION: Modify backend to use independent httpx clients")
    elif "DEADLOCK CONFIRMED" in content:
        write_result("⚠️  Shared client has deadlock issues")
        write_result("📝 Need to verify independent clients work")
    else:
        write_result("❓ Results inconclusive, may need more testing")
    
    write_result("="*60)
    write_result(f"\nTest completed at {datetime.now()}")
    write_result(f"Full results saved to {RESULT_FILE}")

if __name__ == "__main__":
    print(f"Running deadlock test, results will be written to {RESULT_FILE}")
    asyncio.run(main())
    print(f"\nTest complete! Check {RESULT_FILE} for detailed results.")
