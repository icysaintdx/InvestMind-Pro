"""
测试修复后的SiliconFlow API
"""
import asyncio
import httpx
import time
import json

# API配置
API_URL = "http://localhost:8000/api/ai/siliconflow"
TEST_REQUESTS = [
    {
        "model": "Qwen/Qwen3-8B",
        "systemPrompt": "你是一个专业的投资分析师",
        "prompt": f"测试请求 {i}: 分析股票代码000541的投资价值"
    }
    for i in range(5)  # 创建5个测试请求
]

async def test_single_request(session, request_data, index):
    """测试单个请求"""
    start_time = time.time()
    try:
        response = await session.post(API_URL, json=request_data, timeout=200)
        result = response.json()
        elapsed = time.time() - start_time
        
        if result.get("success"):
            print(f"✅ 请求 {index} 成功，耗时: {elapsed:.2f}秒")
        else:
            print(f"❌ 请求 {index} 失败: {result.get('error')}, 耗时: {elapsed:.2f}秒")
        
        return elapsed, result.get("success", False)
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ 请求 {index} 异常: {str(e)}, 耗时: {elapsed:.2f}秒")
        return elapsed, False

async def test_concurrent_requests():
    """测试并发请求"""
    print("=" * 60)
    print("测试修复后的SiliconFlow API并发处理")
    print("=" * 60)
    
    async with httpx.AsyncClient() as session:
        # 测试并发5个请求
        print("\n📊 测试并发5个请求（模拟第二阶段）...")
        start_time = time.time()
        
        tasks = [
            test_single_request(session, TEST_REQUESTS[i], i+1)
            for i in range(5)
        ]
        
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # 统计结果
        success_count = sum(1 for _, success in results if success)
        avg_time = sum(elapsed for elapsed, _ in results) / len(results)
        
        print("\n📈 测试结果:")
        print(f"  - 总耗时: {total_time:.2f}秒")
        print(f"  - 成功率: {success_count}/{len(results)}")
        print(f"  - 平均响应时间: {avg_time:.2f}秒")
        
        if success_count == len(results):
            print("\n✅ 修复成功！所有请求都正常完成")
        elif success_count > 0:
            print("\n⚠️ 部分成功，可能需要进一步优化")
        else:
            print("\n❌ 修复失败，所有请求都失败了")

if __name__ == "__main__":
    print("开始测试...")
    print("注意：确保后端服务器已启动在 http://localhost:8000")
    print()
    
    asyncio.run(test_concurrent_requests())
    
    print("\n测试完成！")
