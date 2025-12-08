"""
测试 SiliconFlow API 并发请求问题
"""
import asyncio
import httpx
import json
import time
from typing import List

# API配置
SILICONFLOW_API_KEY = "sk-gdunxgtyhqokufmvnzjgsxsrqvfrxicigzslhzjrwlwejtyv"
API_URL = "https://api.siliconflow.cn/v1/chat/completions"

async def call_siliconflow(session_id: str, prompt_length: int):
    """单个 SiliconFlow API 调用"""
    start_time = time.time()
    
    # 构造指定长度的提示词
    prompt = "测试" * (prompt_length // 6)  # 中文字符约3字节
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SILICONFLOW_API_KEY}"
    }
    
    data = {
        "model": "Qwen/Qwen3-8B",
        "messages": [
            {"role": "system", "content": "你是一个测试助手"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 100,
        "stream": False
    }
    
    print(f"[{session_id}] 开始请求 (长度: {len(prompt)} 字符)")
    
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
            response = await client.post(API_URL, headers=headers, json=data)
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                tokens = result.get('usage', {})
                print(f"[{session_id}] ✅ 成功! 耗时: {elapsed:.2f}秒, Token: {tokens}")
                return True, elapsed
            else:
                print(f"[{session_id}] ❌ 错误: {response.status_code}")
                return False, elapsed
                
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[{session_id}] ❌ 异常: {type(e).__name__}: {str(e)}, 耗时: {elapsed:.2f}秒")
        return False, elapsed

async def test_concurrent_requests():
    """测试并发请求"""
    print("=" * 60)
    print("测试 SiliconFlow API 并发请求")
    print("=" * 60)
    
    # 测试场景
    test_cases = [
        # (并发数, 字符长度)
        (1, 2000),   # 单个请求，2000字符
        (2, 2000),   # 2个并发，各2000字符
        (3, 2000),   # 3个并发，各2000字符
        (3, 5000),   # 3个并发，各5000字符（模拟实际场景）
        (5, 2000),   # 5个并发，各2000字符
    ]
    
    for concurrency, length in test_cases:
        print(f"\n测试: {concurrency}个并发, 每个{length}字符")
        print("-" * 40)
        
        # 创建并发任务
        tasks = []
        for i in range(concurrency):
            task = call_siliconflow(f"请求{i+1}", length)
            tasks.append(task)
        
        # 并发执行
        start = time.time()
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start
        
        # 统计结果
        success_count = sum(1 for r, _ in results if r)
        avg_time = sum(t for _, t in results) / len(results)
        
        print(f"总耗时: {total_time:.2f}秒")
        print(f"成功率: {success_count}/{concurrency}")
        print(f"平均响应: {avg_time:.2f}秒")
        
        # 等待一下避免触发限流
        await asyncio.sleep(2)
    
    print("\n" + "=" * 60)
    print("测试完成！")

async def test_shared_client():
    """测试共享客户端的问题"""
    print("\n" + "=" * 60)
    print("测试共享 httpx 客户端")
    print("=" * 60)
    
    # 创建一个共享的客户端（模拟当前后端的做法）
    shared_client = httpx.AsyncClient(
        limits=httpx.Limits(max_connections=50, max_keepalive_connections=20),
        timeout=httpx.Timeout(180.0)
    )
    
    async def call_with_shared_client(session_id: str):
        """使用共享客户端调用"""
        start = time.time()
        prompt = "测试" * 1000  # 3000字符
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {SILICONFLOW_API_KEY}"
        }
        
        data = {
            "model": "Qwen/Qwen3-8B",
            "messages": [
                {"role": "system", "content": "你是测试助手"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 100
        }
        
        print(f"[{session_id}] 使用共享客户端请求...")
        
        try:
            response = await shared_client.post(API_URL, headers=headers, json=data)
            elapsed = time.time() - start
            print(f"[{session_id}] ✅ 完成，耗时: {elapsed:.2f}秒")
            return True, elapsed
        except Exception as e:
            elapsed = time.time() - start
            print(f"[{session_id}] ❌ 失败: {e}, 耗时: {elapsed:.2f}秒")
            return False, elapsed
    
    # 测试3个并发请求
    print("发送3个并发请求（共享客户端）...")
    tasks = [call_with_shared_client(f"共享{i+1}") for i in range(3)]
    
    start = time.time()
    results = await asyncio.gather(*tasks)
    total = time.time() - start
    
    print(f"总耗时: {total:.2f}秒")
    print(f"成功: {sum(1 for r, _ in results if r)}/3")
    
    # 关闭共享客户端
    await shared_client.aclose()

if __name__ == "__main__":
    asyncio.run(test_concurrent_requests())
    asyncio.run(test_shared_client())
