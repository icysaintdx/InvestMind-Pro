"""
增强版 SiliconFlow API - 带多级降级处理
这是一个示例实现，展示如何集成降级处理器
"""
import asyncio
import httpx
import time
from fastapi import HTTPException
from backend.utils.llm_fallback_handler import get_fallback_handler

async def siliconflow_api_enhanced(request):
    """
    增强版 SiliconFlow API 代理
    带多级降级和详细错误报告
    """
    import datetime
    req_time = datetime.datetime.now().strftime("%H:%M:%S")
    request._start_time = time.time()
    
    # 获取降级处理器
    fallback_handler = get_fallback_handler()
    
    # 记录等待获取锁的时间
    lock_wait_start = time.time()
    async with siliconflow_semaphore:  # 假设这个信号量已定义
        lock_wait_time = time.time() - lock_wait_start
        concurrent_count = 10 - siliconflow_semaphore._value
        print(f"[SiliconFlow] [{req_time}] 获取并发锁")
        print(f"  - 等待锁耗时: {lock_wait_time:.1f}秒")
        print(f"  - 当前并发数: {concurrent_count}/10")
        
        client = None
        try:
            api_key = request.apiKey or API_KEYS["siliconflow"]
            if not api_key:
                raise HTTPException(status_code=500, detail="未配置 SiliconFlow API Key")
            
            # 智能体角色（用于降级策略）
            agent_role = request.agentRole if hasattr(request, 'agentRole') else "UNKNOWN"
            
            # 根据智能体类型配置超时
            complex_agents = ['NEWS', 'FUNDAMENTAL', 'TECHNICAL', 'MACRO', 'INDUSTRY']
            
            if agent_role in complex_agents:
                base_timeout = 60.0
            else:
                base_timeout = 45.0
            
            # 创建 HTTP 客户端
            client = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    timeout=base_timeout + 30,  # 总超时比读取超时多30秒
                    connect=15.0,
                    read=base_timeout,
                    write=15.0,
                    pool=15.0
                ),
                limits=httpx.Limits(
                    max_connections=10,
                    max_keepalive_connections=5
                )
            )
            
            # 准备请求
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            # 基础请求数据
            data = {
                "model": request.model,
                "messages": [
                    {"role": "system", "content": request.systemPrompt},
                    {"role": "user", "content": request.prompt}
                ],
                "temperature": request.temperature,
                "max_tokens": getattr(request, 'maxTokens', 1024),
                "stream": False
            }
            
            # 使用降级处理器执行请求
            result, metrics = await fallback_handler.execute_with_fallback(
                client=client,
                url=API_ENDPOINTS["siliconflow"],  # 假设这个已定义
                headers=headers,
                data=data,
                agent_role=agent_role,
                max_retries=4
            )
            
            # 记录指标
            total_time = time.time() - request._start_time
            print(f"[SiliconFlow] [{req_time}] 🏁 请求完成")
            print(f"  - 总耗时: {total_time:.1f}秒")
            print(f"  - 最终状态: {metrics.final_status}")
            print(f"  - 尝试次数: {len(metrics.attempt_times)}")
            
            if metrics.final_status.startswith("success"):
                print(f"  - ✅ 成功")
            elif "cached" in metrics.final_status:
                print(f"  - ⚡ 使用缓存")
            elif "default" in metrics.final_status:
                print(f"  - ⚠️ 使用默认响应")
                
                # 如果所有尝试都失败，记录详细错误
                if len(metrics.error_types) > 0:
                    print(f"  - 错误类型: {', '.join(metrics.error_types)}")
                    print(f"  - 原始提示词长度: {metrics.prompt_length} 字符")
                    print(f"  - 建议：")
                    print(f"    1. 检查网络连接")
                    print(f"    2. 减少提示词长度")
                    print(f"    3. 使用其他 AI 模型")
                    print(f"    4. 稍后重试")
            
            # 提取响应文本
            text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # 返回响应
            return {
                "success": True,
                "text": text,
                "usage": result.get("usage", {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }),
                "fallback_level": result.get("fallback_level", 0),
                "metrics": {
                    "total_time": total_time,
                    "attempts": len(metrics.attempt_times),
                    "final_status": metrics.final_status
                }
            }
            
        except HTTPException as e:
            # HTTP 错误（如 API 密钥无效）
            print(f"[SiliconFlow] HTTP错误: {e.detail}")
            return {
                "success": False,
                "error": e.detail
            }
            
        except Exception as e:
            # 其他未预期的错误
            import traceback
            error_msg = f"{type(e).__name__}: {str(e)}"
            print(f"[SiliconFlow] 未知错误: {error_msg}")
            print(traceback.format_exc())
            
            # 返回默认响应
            return {
                "success": True,
                "text": "⚠️ 系统遇到未知错误，建议稍后重试。",
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "error": True
            }
            
        finally:
            # 清理资源
            if client:
                try:
                    await client.aclose()
                    print(f"[SiliconFlow] 已关闭HTTP客户端")
                except:
                    pass
            
            # 计算总耗时
            if hasattr(request, '_start_time'):
                total_elapsed = time.time() - request._start_time
                if total_elapsed > 60:
                    print(f"[SiliconFlow] ⚠️ 耗时过长: {total_elapsed:.1f}秒")


# ============ 使用示例 ============

"""
要集成到现有的 server.py，需要：

1. 导入降级处理器：
from backend.utils.llm_fallback_handler import get_fallback_handler

2. 在 siliconflow_api 函数中替换现有的重试逻辑：

# 原来的代码
for attempt in range(max_retries):
    try:
        response = await client.post(...)
        # ...
    except TimeoutError:
        # 重试或失败
        
# 新的代码
fallback_handler = get_fallback_handler()
result, metrics = await fallback_handler.execute_with_fallback(
    client=client,
    url=API_ENDPOINTS["siliconflow"],
    headers=headers,
    data=data,
    agent_role=agent_role,
    max_retries=4
)

3. 处理返回结果：
- result 包含响应数据
- metrics 包含请求指标（用于调试）

4. 添加智能体角色到请求：
在前端请求中添加 agentRole 字段，例如：
{
    "model": "...",
    "prompt": "...",
    "agentRole": "NEWS"  // 或 "FUNDAMENTAL", "RISK" 等
}
"""
