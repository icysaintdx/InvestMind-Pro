"""
测试不同上下文长度的SiliconFlow API响应
测试 10000, 12000, 15000, 18000 字符
"""
import asyncio
import httpx
import time

async def test_context_length(char_count: int):
    """
    测试指定字符数的上下文
    
    Args:
        char_count: 字符数
    """
    print(f"\n{'='*60}")
    print(f"测试 {char_count} 字符上下文")
    print(f"{'='*60}")
    
    # 构建测试数据
    system_prompt = "你是一个专业的股票分析师。"
    
    # 生成指定长度的用户提示词
    # 模拟前序输出
    previous_outputs = ""
    for i in range(13):
        agent_output = f"智能体{i}的分析结果：" + "这是详细的分析内容。" * 50  # 每个约500字符
        previous_outputs += f"\n>>> 智能体{i}:\n{agent_output}\n"
    
    # 计算还需要多少字符
    current_len = len(system_prompt) + len(previous_outputs)
    remaining = char_count - current_len - 200  # 预留200字符
    
    if remaining > 0:
        # 添加更多内容
        user_prompt = previous_outputs + "\n【补充数据】\n" + "补充分析数据。" * (remaining // 10)
    else:
        user_prompt = previous_outputs
    
    total_len = len(system_prompt) + len(user_prompt)
    estimated_tokens = total_len // 2
    
    print(f"系统提示词: {len(system_prompt)} 字符")
    print(f"用户提示词: {len(user_prompt)} 字符")
    print(f"总长度: {total_len} 字符 (~{estimated_tokens} tokens)")
    
    # 调用API
    url = "http://localhost:8000/api/ai/siliconflow"
    data = {
        "model": "Qwen/Qwen2.5-7B-Instruct",
        "systemPrompt": system_prompt,
        "prompt": user_prompt,
        "temperature": 0.3
    }
    
    start_time = time.time()
    
    async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as client:
        try:
            print(f"⏱️ 开始请求...")
            response = await client.post(url, json=data)
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    text = result.get("text", "")
                    usage = result.get("usage", {})
                    
                    print(f"✅ 成功！耗时: {elapsed:.2f}秒")
                    print(f"📊 Token使用:")
                    print(f"  - 输入: {usage.get('prompt_tokens', 0)}")
                    print(f"  - 输出: {usage.get('completion_tokens', 0)}")
                    print(f"  - 总计: {usage.get('total_tokens', 0)}")
                    print(f"📝 响应长度: {len(text)} 字符")
                    print(f"📄 响应预览: {text[:200]}...")
                    
                    return {
                        "char_count": char_count,
                        "success": True,
                        "elapsed": elapsed,
                        "usage": usage,
                        "response_len": len(text)
                    }
                else:
                    print(f"❌ API返回失败: {result.get('error')}")
                    return {
                        "char_count": char_count,
                        "success": False,
                        "error": result.get('error'),
                        "elapsed": elapsed
                    }
            else:
                print(f"❌ HTTP {response.status_code}")
                print(f"响应: {response.text[:500]}")
                return {
                    "char_count": char_count,
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "elapsed": elapsed
                }
                
        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            print(f"⏱️ 超时！耗时: {elapsed:.2f}秒")
            return {
                "char_count": char_count,
                "success": False,
                "error": "Timeout",
                "elapsed": elapsed
            }
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ 错误: {e}")
            return {
                "char_count": char_count,
                "success": False,
                "error": str(e),
                "elapsed": elapsed
            }

async def main():
    """主函数"""
    print("="*60)
    print("SiliconFlow API 上下文长度测试")
    print("="*60)
    print("测试目标: 10000, 12000, 15000, 18000 字符")
    print("模型: Qwen/Qwen2.5-7B-Instruct")
    print("="*60)
    
    # 测试不同长度
    test_lengths = [10000, 12000, 15000, 18000]
    results = []
    
    for length in test_lengths:
        result = await test_context_length(length)
        results.append(result)
        
        # 等待一下，避免请求过快
        await asyncio.sleep(2)
    
    # 打印总结
    print(f"\n{'='*60}")
    print("测试总结")
    print(f"{'='*60}")
    print(f"{'字符数':<10} {'状态':<10} {'耗时(秒)':<12} {'Token使用':<15} {'响应长度'}")
    print("-"*60)
    
    for r in results:
        status = "✅ 成功" if r['success'] else "❌ 失败"
        elapsed = f"{r['elapsed']:.2f}"
        
        if r['success']:
            usage = r.get('usage', {})
            tokens = f"{usage.get('total_tokens', 0)}"
            response_len = f"{r.get('response_len', 0)}"
        else:
            tokens = "-"
            response_len = f"错误: {r.get('error', 'Unknown')}"
        
        print(f"{r['char_count']:<10} {status:<10} {elapsed:<12} {tokens:<15} {response_len}")
    
    print(f"{'='*60}")
    
    # 分析结果
    success_count = sum(1 for r in results if r['success'])
    print(f"\n✅ 成功: {success_count}/{len(results)}")
    
    if success_count > 0:
        max_success = max([r['char_count'] for r in results if r['success']])
        print(f"📊 最大成功字符数: {max_success}")
        
        avg_time = sum([r['elapsed'] for r in results if r['success']]) / success_count
        print(f"⏱️ 平均响应时间: {avg_time:.2f}秒")
    
    if success_count < len(results):
        failed = [r for r in results if not r['success']]
        print(f"\n❌ 失败的测试:")
        for r in failed:
            print(f"  - {r['char_count']} 字符: {r.get('error', 'Unknown')}")

if __name__ == "__main__":
    asyncio.run(main())
