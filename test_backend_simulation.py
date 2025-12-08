"""
模拟实际后端的 analyze_stock 函数行为
测试问题是否出在代码逻辑而不是连接池
"""
import asyncio
import httpx
import time
import json
from typing import Dict, Any

# 实际后端配置
API_KEYS = {
    "siliconflow": "sk-gdunxgtyhqokufmvnzjgsxsrqvfrxicigzslhzjrwlwejtyv"
}

# 全局HTTP客户端（模拟后端）
http_clients = {}

async def init_clients():
    """初始化客户端池（模拟后端的lifespan）"""
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
    
    print("✅ HTTP连接池初始化成功")

async def cleanup_clients():
    """清理客户端池"""
    for name, client in http_clients.items():
        await client.aclose()
        print(f"✅ 关闭 {name} 连接池")

async def siliconflow_api_original(system_prompt: str, user_prompt: str, agent_id: str):
    """模拟原始的 siliconflow_api 函数（使用共享客户端）"""
    try:
        api_key = API_KEYS["siliconflow"]
        
        # 使用全局连接池客户端（原始做法）
        client = http_clients.get('siliconflow', http_clients['default'])
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
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
        
        prompt_len = len(system_prompt) + len(user_prompt)
        print(f"[{agent_id}] 调用SiliconFlow API (共享客户端): {prompt_len} 字符")
        
        start = time.time()
        response = await client.post(
            "https://api.siliconflow.cn/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=httpx.Timeout(60.0)  # 60秒超时用于测试
        )
        
        elapsed = time.time() - start
        
        if response.status_code == 200:
            result = response.json()
            usage = result.get("usage", {})
            print(f"[{agent_id}] ✅ 成功 ({elapsed:.2f}秒) Token: {usage.get('total_tokens', 0)}")
            return {"success": True, "text": "模拟响应"}
        else:
            print(f"[{agent_id}] ❌ HTTP {response.status_code} ({elapsed:.2f}秒)")
            return {"success": False, "error": f"HTTP {response.status_code}"}
            
    except asyncio.TimeoutError:
        print(f"[{agent_id}] ⏱️ 超时!")
        return {"success": False, "error": "Timeout"}
    except Exception as e:
        print(f"[{agent_id}] ❌ 错误: {type(e).__name__}: {str(e)}")
        return {"success": False, "error": str(e)}

async def siliconflow_api_fixed(system_prompt: str, user_prompt: str, agent_id: str):
    """修复后的 siliconflow_api 函数（使用独立客户端）"""
    client = None
    try:
        api_key = API_KEYS["siliconflow"]
        
        # 为每个请求创建独立的客户端
        client = httpx.AsyncClient(
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
        )
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
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
        
        prompt_len = len(system_prompt) + len(user_prompt)
        print(f"[{agent_id}] 调用SiliconFlow API (独立客户端): {prompt_len} 字符")
        
        start = time.time()
        response = await client.post(
            "https://api.siliconflow.cn/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=httpx.Timeout(60.0)
        )
        
        elapsed = time.time() - start
        
        if response.status_code == 200:
            result = response.json()
            usage = result.get("usage", {})
            print(f"[{agent_id}] ✅ 成功 ({elapsed:.2f}秒) Token: {usage.get('total_tokens', 0)}")
            return {"success": True, "text": "模拟响应"}
        else:
            print(f"[{agent_id}] ❌ HTTP {response.status_code} ({elapsed:.2f}秒)")
            return {"success": False, "error": f"HTTP {response.status_code}"}
            
    except asyncio.TimeoutError:
        print(f"[{agent_id}] ⏱️ 超时!")
        return {"success": False, "error": "Timeout"}
    except Exception as e:
        print(f"[{agent_id}] ❌ 错误: {type(e).__name__}: {str(e)}")
        return {"success": False, "error": str(e)}
    finally:
        if client:
            await client.aclose()

async def simulate_analyze_request(agent_id: str, previous_outputs: Dict[str, str], use_fixed: bool = False):
    """模拟 analyze_stock 请求"""
    # 构建系统提示词（模拟实际的）
    system_prompt = f"你是{agent_id}，负责分析股票"
    
    # 构建用户提示词（包含前序输出）
    user_prompt = f"分析股票002254\n"
    
    if previous_outputs:
        user_prompt += "\n前序分析结果:\n"
        for name, output in previous_outputs.items():
            user_prompt += f"\n[{name}]:\n{output[:500]}...\n"  # 截断避免太长
    
    # 选择使用哪个版本的API
    if use_fixed:
        return await siliconflow_api_fixed(system_prompt, user_prompt, agent_id)
    else:
        return await siliconflow_api_original(system_prompt, user_prompt, agent_id)

async def test_actual_scenario():
    """测试实际场景：完全模拟前端的请求流程"""
    print("="*60)
    print("测试实际场景（模拟前端请求流程）")
    print("="*60)
    
    # 初始化客户端池
    await init_clients()
    
    # 存储各阶段输出
    outputs = {}
    
    print("\n### 使用原始方法（共享客户端）###\n")
    
    # 阶段0：新闻分析（单独）
    print("阶段0: 新闻分析")
    result = await simulate_analyze_request("news_analyst", {}, use_fixed=False)
    outputs["news_analyst"] = "新闻分析结果" * 100  # 模拟300字符
    
    # 阶段1前期：2个并发
    print("\n阶段1前期: macro + industry (2400字符)")
    tasks = [
        simulate_analyze_request("macro", outputs, use_fixed=False),
        simulate_analyze_request("industry", outputs, use_fixed=False)
    ]
    results = await asyncio.gather(*tasks)
    
    # 更新输出
    outputs["macro"] = "宏观分析" * 200  # 模拟600字符
    outputs["industry"] = "行业分析" * 200
    
    # 阶段1后期：3个并发（这是问题发生的地方）
    print("\n阶段1后期: technical + fundamental + funds (4800字符)")
    print("⚠️ 这里是实际卡死的地方")
    
    start_time = time.time()
    tasks = [
        simulate_analyze_request("technical", outputs, use_fixed=False),
        simulate_analyze_request("fundamental", outputs, use_fixed=False),
        simulate_analyze_request("funds", outputs, use_fixed=False)
    ]
    
    # 设置总超时，避免永远等待
    try:
        results = await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=True),
            timeout=120.0  # 2分钟总超时
        )
        elapsed = time.time() - start_time
        success_count = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        print(f"\n结果: {success_count}/3 成功, 总耗时: {elapsed:.2f}秒")
    except asyncio.TimeoutError:
        elapsed = time.time() - start_time
        print(f"\n❌ 总超时! 耗时: {elapsed:.2f}秒 - 确认死锁!")
    
    # 清理
    await cleanup_clients()
    
    # 等待5秒后测试修复版本
    await asyncio.sleep(5)
    
    print("\n### 使用修复方法（独立客户端）###\n")
    
    outputs = {}
    
    # 重复同样的流程，但使用修复版本
    print("阶段0: 新闻分析")
    result = await simulate_analyze_request("news_analyst", {}, use_fixed=True)
    outputs["news_analyst"] = "新闻分析结果" * 100
    
    print("\n阶段1前期: macro + industry")
    tasks = [
        simulate_analyze_request("macro", outputs, use_fixed=True),
        simulate_analyze_request("industry", outputs, use_fixed=True)
    ]
    results = await asyncio.gather(*tasks)
    
    outputs["macro"] = "宏观分析" * 200
    outputs["industry"] = "行业分析" * 200
    
    print("\n阶段1后期: technical + fundamental + funds")
    start_time = time.time()
    tasks = [
        simulate_analyze_request("technical", outputs, use_fixed=True),
        simulate_analyze_request("fundamental", outputs, use_fixed=True),
        simulate_analyze_request("funds", outputs, use_fixed=True)
    ]
    
    results = await asyncio.gather(*tasks)
    elapsed = time.time() - start_time
    success_count = sum(1 for r in results if r.get("success"))
    print(f"\n结果: {success_count}/3 成功, 总耗时: {elapsed:.2f}秒")

async def test_connection_leak():
    """测试是否存在连接泄漏"""
    print("\n" + "="*60)
    print("测试连接泄漏")
    print("="*60)
    
    await init_clients()
    
    # 监控连接数
    async def monitor_connections():
        while True:
            client = http_clients.get('siliconflow')
            if client:
                transport = getattr(client, '_transport', None)
                if transport:
                    pool = getattr(transport, '_pool', None)
                    if pool:
                        connections = len(getattr(pool, '_connections', []))
                        print(f"  活跃连接数: {connections}")
            await asyncio.sleep(2)
    
    # 启动监控
    monitor_task = asyncio.create_task(monitor_connections())
    
    # 连续发送请求，看连接数是否不断增加
    for i in range(10):
        print(f"\n迭代 {i+1}/10")
        await simulate_analyze_request(f"test_{i}", {}, use_fixed=False)
        await asyncio.sleep(1)
    
    monitor_task.cancel()
    await cleanup_clients()

async def main():
    """主测试函数"""
    print("后端行为模拟测试")
    print("="*60)
    
    # 运行实际场景测试
    await test_actual_scenario()
    
    # 测试连接泄漏
    await test_connection_leak()
    
    print("\n" + "="*60)
    print("测试完成！")

if __name__ == "__main__":
    asyncio.run(main())
