"""
精确模拟后端实际情况的测试
"""
import asyncio
import httpx
import time
import json
from datetime import datetime

RESULT_FILE = "exact_simulation_result.json"

# 实际的API配置
API_KEY = "sk-gdunxgtyhqokufmvnzjgsxsrqvfrxicigzslhzjrwlwejtyv"
API_URL = "https://api.siliconflow.cn/v1/chat/completions"

# 全局客户端（模拟后端）
http_clients = {}

async def init_backend_clients():
    """完全模拟后端的客户端初始化"""
    limits = httpx.Limits(
        max_keepalive_connections=20,
        max_connections=50,
        keepalive_expiry=30
    )
    
    ai_timeout = httpx.Timeout(
        connect=5.0,
        read=180.0,
        write=10.0,
        pool=5.0
    )
    
    http_clients['siliconflow'] = httpx.AsyncClient(
        limits=limits,
        timeout=ai_timeout,
        verify=True
    )
    
    http_clients['default'] = httpx.AsyncClient(
        limits=limits,
        timeout=ai_timeout,
        verify=True
    )
    
    print("✅ HTTP连接池初始化成功（模拟后端）")

async def analyze_stock(agent_id: str, previous_outputs: dict, test_name: str):
    """模拟实际的 analyze_stock 函数"""
    results = {
        "agent_id": agent_id,
        "test_name": test_name,
        "start_time": datetime.now().isoformat()
    }
    
    # 构建提示词（模拟实际）
    system_prompt = f"你是{agent_id}，专业的投资分析师"
    user_prompt = f"分析股票002254\n"
    
    # 添加前序输出（这是关键）
    if previous_outputs:
        user_prompt += "\n基于以下分析：\n"
        for name, output in previous_outputs.items():
            user_prompt += f"\n[{name}]:\n{output}\n"
    
    prompt_len = len(system_prompt) + len(user_prompt)
    results["prompt_length"] = prompt_len
    
    # 使用全局客户端（模拟原始后端）
    client = http_clients.get('siliconflow', http_clients['default'])
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    data = {
        "model": "Qwen/Qwen3-8B",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 500,
        "stream": False
    }
    
    print(f"[{agent_id}] 开始请求 ({prompt_len} 字符)")
    start = time.time()
    
    try:
        response = await client.post(API_URL, headers=headers, json=data)
        elapsed = time.time() - start
        
        results["elapsed_time"] = elapsed
        results["status_code"] = response.status_code
        
        if response.status_code == 200:
            result = response.json()
            usage = result.get("usage", {})
            results["success"] = True
            results["tokens"] = usage.get("total_tokens", 0)
            print(f"[{agent_id}] ✅ 成功 ({elapsed:.1f}秒, {usage.get('total_tokens', 0)} tokens)")
        else:
            results["success"] = False
            results["error"] = f"HTTP {response.status_code}"
            print(f"[{agent_id}] ❌ HTTP {response.status_code} ({elapsed:.1f}秒)")
            
    except asyncio.TimeoutError:
        elapsed = time.time() - start
        results["elapsed_time"] = elapsed
        results["success"] = False
        results["error"] = "Timeout"
        print(f"[{agent_id}] ⏱️ 超时 ({elapsed:.1f}秒)")
        
    except Exception as e:
        elapsed = time.time() - start
        results["elapsed_time"] = elapsed
        results["success"] = False
        results["error"] = str(e)
        print(f"[{agent_id}] ❌ 错误: {type(e).__name__} ({elapsed:.1f}秒)")
    
    results["end_time"] = datetime.now().isoformat()
    return results

async def run_exact_simulation():
    """运行精确模拟"""
    all_results = {
        "test_time": datetime.now().isoformat(),
        "stages": {}
    }
    
    print("\n" + "="*60)
    print("精确模拟后端实际请求流程")
    print("="*60)
    
    # 初始化客户端
    await init_backend_clients()
    
    # 存储输出（模拟实际流程）
    outputs = {}
    
    # Stage 0: 新闻分析（单独）
    print("\n阶段0: 新闻分析师")
    result = await analyze_stock("news_analyst", {}, "stage0")
    all_results["stages"]["stage0"] = [result]
    outputs["news_analyst"] = "新闻分析结果" * 100  # 300字符
    
    # Stage 1a: social + china (2个并发)
    print("\n阶段1a: social_analyst + china_market")
    tasks = [
        analyze_stock("social_analyst", outputs, "stage1a"),
        analyze_stock("china_market", outputs, "stage1a")
    ]
    results = await asyncio.gather(*tasks)
    all_results["stages"]["stage1a"] = results
    
    outputs["social_analyst"] = "社交分析" * 200  # 600字符
    outputs["china_market"] = "中国市场" * 200
    
    # Stage 1b: macro + industry (2个并发)
    print("\n阶段1b: macro + industry (约2400字符)")
    tasks = [
        analyze_stock("macro", outputs, "stage1b"),
        analyze_stock("industry", outputs, "stage1b")
    ]
    results = await asyncio.gather(*tasks)
    all_results["stages"]["stage1b"] = results
    
    outputs["macro"] = "宏观分析" * 250  # 750字符
    outputs["industry"] = "行业分析" * 250
    
    # Stage 1c: technical + fundamental + funds (3个并发 - 问题发生处)
    print("\n阶段1c: technical + fundamental + funds (约4800字符)")
    print("⚠️  这是实际发生卡死的地方")
    
    stage1c_start = time.time()
    
    # 设置总超时以检测死锁
    try:
        tasks = [
            analyze_stock("technical", outputs, "stage1c"),
            analyze_stock("fundamental", outputs, "stage1c"),
            analyze_stock("funds", outputs, "stage1c")
        ]
        
        results = await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=True),
            timeout=120.0  # 2分钟超时
        )
        
        stage1c_time = time.time() - stage1c_start
        
        # 处理结果
        success_count = 0
        for r in results:
            if isinstance(r, dict) and r.get("success"):
                success_count += 1
        
        all_results["stages"]["stage1c"] = results
        all_results["stage1c_time"] = stage1c_time
        all_results["stage1c_success"] = success_count
        
        print(f"\n阶段1c结果: {success_count}/3 成功, 耗时 {stage1c_time:.1f}秒")
        
        if success_count < 3:
            print("⚠️  部分请求失败!")
            all_results["deadlock"] = "partial"
        else:
            print("✅ 所有请求成功!")
            all_results["deadlock"] = "none"
            
    except asyncio.TimeoutError:
        stage1c_time = time.time() - stage1c_start
        all_results["stage1c_time"] = stage1c_time
        all_results["stage1c_success"] = 0
        all_results["deadlock"] = "confirmed"
        print(f"\n❌ 阶段1c超时! 耗时 {stage1c_time:.1f}秒")
        print("🔴 确认死锁!")
    
    # 清理
    for name, client in http_clients.items():
        await client.aclose()
    print("\n✅ 客户端已关闭")
    
    # 保存结果
    with open(RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n结果已保存到 {RESULT_FILE}")
    
    # 打印结论
    print("\n" + "="*60)
    print("结论:")
    
    if all_results.get("deadlock") == "confirmed":
        print("✅ 确认：存在httpx连接池死锁问题！")
        print("   - 共享客户端在3个并发大请求时会卡死")
        print("   - 解决方案：使用独立客户端")
    elif all_results.get("deadlock") == "partial":
        print("⚠️  部分问题：有请求失败但未完全死锁")
        print("   - 可能是连接池压力或其他问题")
        print("   - 建议：仍应使用独立客户端")
    else:
        print("❓ 未发现死锁问题")
        print("   - 可能需要更多测试")
        print("   - 或问题可能在其他地方")
    
    print("="*60)
    
    return all_results

async def main():
    print("开始精确模拟测试...")
    print("这将完全模拟后端的实际请求流程")
    
    results = await run_exact_simulation()
    
    print("\n测试完成!")
    print(f"详细结果查看: {RESULT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
