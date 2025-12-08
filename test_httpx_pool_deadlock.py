"""
测试 httpx 连接池死锁问题
模拟实际场景：共享客户端 vs 独立客户端
"""
import asyncio
import httpx
import time
import json
from typing import List, Dict
import threading

# API配置
SILICONFLOW_API_KEY = "sk-gdunxgtyhqokufmvnzjgsxsrqvfrxicigzslhzjrwlwejtyv"
API_URL = "https://api.siliconflow.cn/v1/chat/completions"

# 全局共享客户端（模拟当前后端的做法）
shared_client = None

def create_shared_client():
    """创建共享客户端（模拟后端的做法）"""
    global shared_client
    shared_client = httpx.AsyncClient(
        limits=httpx.Limits(
            max_keepalive_connections=20,  # 和后端一样的设置
            max_connections=50,
            keepalive_expiry=30
        ),
        timeout=httpx.Timeout(
            connect=5.0,
            read=180.0,  # 3分钟，和后端一样
            write=10.0,
            pool=5.0
        )
    )
    return shared_client

async def monitor_client_status(client: httpx.AsyncClient, name: str):
    """监控客户端连接池状态"""
    while True:
        try:
            pool = client._transport._pool if hasattr(client, '_transport') else None
            if pool:
                print(f"[{name}] 连接池状态: "
                      f"活跃连接={len(getattr(pool, '_connections', []))} "
                      f"等待队列={len(getattr(pool, '_waiters', []))}")
        except:
            pass
        await asyncio.sleep(2)

async def call_with_shared_client(session_id: str, char_length: int):
    """使用共享客户端调用"""
    start_time = time.time()
    prompt = "分析股票" + "测试" * (char_length // 6)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SILICONFLOW_API_KEY}"
    }
    
    data = {
        "model": "Qwen/Qwen3-8B",
        "messages": [
            {"role": "system", "content": "你是投资分析师"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 500,
        "stream": False
    }
    
    print(f"[{session_id}] 开始请求 ({len(prompt)}字符) - 使用共享客户端")
    
    try:
        response = await shared_client.post(API_URL, headers=headers, json=data)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            tokens = result.get('usage', {})
            print(f"[{session_id}] ✅ 成功! 耗时: {elapsed:.2f}秒")
            return True, elapsed
        else:
            print(f"[{session_id}] ❌ 错误: {response.status_code}, 耗时: {elapsed:.2f}秒")
            return False, elapsed
            
    except asyncio.TimeoutError:
        elapsed = time.time() - start_time
        print(f"[{session_id}] ⏱️ 超时! 耗时: {elapsed:.2f}秒")
        return False, elapsed
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[{session_id}] ❌ 异常: {type(e).__name__}, 耗时: {elapsed:.2f}秒")
        return False, elapsed

async def call_with_independent_client(session_id: str, char_length: int):
    """使用独立客户端调用"""
    start_time = time.time()
    prompt = "分析股票" + "测试" * (char_length // 6)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SILICONFLOW_API_KEY}"
    }
    
    data = {
        "model": "Qwen/Qwen3-8B",
        "messages": [
            {"role": "system", "content": "你是投资分析师"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 500,
        "stream": False
    }
    
    print(f"[{session_id}] 开始请求 ({len(prompt)}字符) - 使用独立客户端")
    
    # 每次创建新客户端
    async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
        try:
            response = await client.post(API_URL, headers=headers, json=data)
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"[{session_id}] ✅ 成功! 耗时: {elapsed:.2f}秒")
                return True, elapsed
            else:
                print(f"[{session_id}] ❌ 错误: {response.status_code}, 耗时: {elapsed:.2f}秒")
                return False, elapsed
                
        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            print(f"[{session_id}] ⏱️ 超时! 耗时: {elapsed:.2f}秒")
            return False, elapsed
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"[{session_id}] ❌ 异常: {type(e).__name__}, 耗时: {elapsed:.2f}秒")
            return False, elapsed

async def test_scenario_1():
    """场景1：模拟实际的请求模式（逐步增加并发）"""
    print("\n" + "="*60)
    print("场景1: 模拟实际请求模式（共享客户端）")
    print("="*60)
    
    # 创建共享客户端
    create_shared_client()
    
    # 启动监控任务
    monitor_task = asyncio.create_task(
        monitor_client_status(shared_client, "共享客户端")
    )
    
    try:
        # 第一波：2个请求（模拟macro和industry）
        print("\n第一波: 2个并发请求（2400字符）")
        tasks = [
            call_with_shared_client("macro", 2400),
            call_with_shared_client("industry", 2400)
        ]
        results = await asyncio.gather(*tasks)
        print(f"第一波完成: {sum(1 for r, _ in results if r)}/2 成功\n")
        
        # 等待2秒
        await asyncio.sleep(2)
        
        # 第二波：3个请求（模拟technical, fundamental, funds）
        print("第二波: 3个并发请求（4800字符）")
        tasks = [
            call_with_shared_client("technical", 4800),
            call_with_shared_client("fundamental", 4800),
            call_with_shared_client("funds", 4800)
        ]
        results = await asyncio.gather(*tasks)
        print(f"第二波完成: {sum(1 for r, _ in results if r)}/3 成功")
        
    finally:
        monitor_task.cancel()
        await shared_client.aclose()

async def test_scenario_2():
    """场景2：同样的请求，但使用独立客户端"""
    print("\n" + "="*60)
    print("场景2: 模拟实际请求模式（独立客户端）")
    print("="*60)
    
    # 第一波：2个请求
    print("\n第一波: 2个并发请求（2400字符）")
    tasks = [
        call_with_independent_client("macro", 2400),
        call_with_independent_client("industry", 2400)
    ]
    results = await asyncio.gather(*tasks)
    print(f"第一波完成: {sum(1 for r, _ in results if r)}/2 成功\n")
    
    # 等待2秒
    await asyncio.sleep(2)
    
    # 第二波：3个请求
    print("第二波: 3个并发请求（4800字符）")
    tasks = [
        call_with_independent_client("technical", 4800),
        call_with_independent_client("fundamental", 4800),
        call_with_independent_client("funds", 4800)
    ]
    results = await asyncio.gather(*tasks)
    print(f"第二波完成: {sum(1 for r, _ in results if r)}/3 成功")

async def test_scenario_3():
    """场景3：测试连接池极限"""
    print("\n" + "="*60)
    print("场景3: 测试连接池极限（5个并发大请求）")
    print("="*60)
    
    # 共享客户端
    create_shared_client()
    print("\n使用共享客户端：")
    tasks = [call_with_shared_client(f"请求{i+1}", 5000) for i in range(5)]
    start = time.time()
    results = await asyncio.gather(*tasks)
    total = time.time() - start
    success = sum(1 for r, _ in results if r)
    print(f"共享客户端: {success}/5 成功, 总耗时: {total:.2f}秒")
    await shared_client.aclose()
    
    await asyncio.sleep(3)
    
    # 独立客户端
    print("\n使用独立客户端：")
    tasks = [call_with_independent_client(f"请求{i+1}", 5000) for i in range(5)]
    start = time.time()
    results = await asyncio.gather(*tasks)
    total = time.time() - start
    success = sum(1 for r, _ in results if r)
    print(f"独立客户端: {success}/5 成功, 总耗时: {total:.2f}秒")

async def main():
    """主测试函数"""
    print("="*60)
    print("httpx 连接池死锁测试")
    print("="*60)
    
    # 运行各个场景测试
    await test_scenario_1()
    await asyncio.sleep(5)  # 场景之间等待
    
    await test_scenario_2()
    await asyncio.sleep(5)
    
    await test_scenario_3()
    
    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
