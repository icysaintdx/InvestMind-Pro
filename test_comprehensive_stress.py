#!/usr/bin/env python3
"""
综合压力测试 - 测试不同并发和Prompt长度的组合
找出真正的性能瓶颈
"""

import asyncio
import aiohttp
import time
import json
from datetime import datetime
from itertools import product

# 测试配置
CONCURRENCY_LEVELS = [2, 4, 6, 8, 10]  # 并发数
PROMPT_SIZES = [1000, 2000, 4000, 6000, 8000, 10000]  # Prompt长度（字符）

STOCK_DATA = {
    "symbol": "600547",
    "name": "山东黄金",
    "nowPri": "10.50",
    "increase": "2.5",
    "traAmount": "1000000"
}

def generate_prompt(size):
    """生成指定长度的Prompt"""
    base_text = "这是一段详细的市场分析内容，包含了各种技术指标、基本面数据、市场情绪等信息。" * 10
    # 重复直到达到目标长度
    repeat_count = (size // len(base_text)) + 1
    full_text = base_text * repeat_count
    return full_text[:size]

async def send_request(session, agent_id, prompt_size, request_num):
    """发送单个请求"""
    url = "http://localhost:8000/api/analyze"
    
    # 生成指定长度的前序输出
    previous_outputs = {}
    num_agents = 13  # 模拟13个前序智能体
    per_agent_size = prompt_size // num_agents
    
    for i in range(num_agents):
        agent_name = f"agent_{i}"
        previous_outputs[agent_name] = generate_prompt(per_agent_size)
    
    payload = {
        "agent_id": agent_id,
        "stock_code": STOCK_DATA["symbol"],
        "stock_data": STOCK_DATA,
        "previous_outputs": previous_outputs,
        "custom_instruction": "请基于前序分析给出你的观点。"
    }
    
    start_time = time.time()
    
    try:
        async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=180)) as response:
            elapsed = time.time() - start_time
            
            if response.status == 200:
                result = await response.json()
                if result.get("success"):
                    return {
                        "request_num": request_num,
                        "success": True,
                        "elapsed": elapsed,
                        "result_length": len(result.get("result", ""))
                    }
                else:
                    return {
                        "request_num": request_num,
                        "success": False,
                        "elapsed": elapsed,
                        "error": result.get("error")
                    }
            else:
                return {
                    "request_num": request_num,
                    "success": False,
                    "elapsed": elapsed,
                    "error": f"HTTP {response.status}"
                }
                
    except asyncio.TimeoutError:
        elapsed = time.time() - start_time
        return {
            "request_num": request_num,
            "success": False,
            "elapsed": elapsed,
            "error": "Timeout"
        }
    except Exception as e:
        elapsed = time.time() - start_time
        return {
            "request_num": request_num,
            "success": False,
            "elapsed": elapsed,
            "error": str(e)
        }

async def test_combination(concurrency, prompt_size):
    """测试特定的并发和Prompt长度组合"""
    print(f"\n{'='*70}")
    print(f"测试: 并发={concurrency}, Prompt长度={prompt_size}字符")
    print(f"{'='*70}")
    
    async with aiohttp.ClientSession() as session:
        # 创建并发请求
        tasks = []
        for i in range(concurrency):
            agent_id = f"test_agent_{i}"
            task = send_request(session, agent_id, prompt_size, i+1)
            tasks.append(task)
        
        # 并发执行
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # 分析结果
        success_count = sum(1 for r in results if r["success"])
        failed_count = len(results) - success_count
        
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]
        
        print(f"\n结果:")
        print(f"  总请求数: {concurrency}")
        print(f"  成功: {success_count}")
        print(f"  失败: {failed_count}")
        print(f"  总耗时: {total_time:.1f}秒")
        
        if successful:
            avg_time = sum(r["elapsed"] for r in successful) / len(successful)
            min_time = min(r["elapsed"] for r in successful)
            max_time = max(r["elapsed"] for r in successful)
            print(f"\n成功请求:")
            print(f"  平均耗时: {avg_time:.1f}秒")
            print(f"  最快: {min_time:.1f}秒")
            print(f"  最慢: {max_time:.1f}秒")
        
        if failed:
            print(f"\n失败请求:")
            for r in failed:
                print(f"  请求{r['request_num']}: {r['error']} ({r['elapsed']:.1f}秒)")
        
        return {
            "concurrency": concurrency,
            "prompt_size": prompt_size,
            "total_requests": concurrency,
            "success": success_count,
            "failed": failed_count,
            "total_time": total_time,
            "avg_time": avg_time if successful else 0,
            "success_rate": (success_count / concurrency * 100) if concurrency > 0 else 0
        }

async def main():
    """主测试函数"""
    print("="*70)
    print("综合压力测试")
    print("="*70)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"后端地址: http://localhost:8000")
    print(f"并发级别: {CONCURRENCY_LEVELS}")
    print(f"Prompt长度: {PROMPT_SIZES}")
    print()
    
    all_results = []
    
    # 测试所有组合
    total_tests = len(CONCURRENCY_LEVELS) * len(PROMPT_SIZES)
    current_test = 0
    
    for concurrency in CONCURRENCY_LEVELS:
        for prompt_size in PROMPT_SIZES:
            current_test += 1
            print(f"\n{'#'*70}")
            print(f"# 测试 {current_test}/{total_tests}")
            print(f"{'#'*70}")
            
            result = await test_combination(concurrency, prompt_size)
            all_results.append(result)
            
            # 测试间等待5秒
            if current_test < total_tests:
                print(f"\n⏸️  等待5秒后继续下一个测试...")
                await asyncio.sleep(5)
    
    # 生成总结报告
    print(f"\n{'='*70}")
    print("总结报告")
    print(f"{'='*70}\n")
    
    # 按并发分组
    print("按并发级别分组:")
    print(f"{'并发':<8} {'Prompt':<10} {'成功率':<10} {'平均耗时':<12} {'总耗时':<10}")
    print("-" * 70)
    
    for result in all_results:
        print(f"{result['concurrency']:<8} {result['prompt_size']:<10} "
              f"{result['success_rate']:.1f}%{'':<5} {result['avg_time']:.1f}秒{'':<6} "
              f"{result['total_time']:.1f}秒")
    
    # 找出问题组合
    print(f"\n{'='*70}")
    print("问题分析")
    print(f"{'='*70}\n")
    
    failed_tests = [r for r in all_results if r['success_rate'] < 100]
    if failed_tests:
        print("失败的测试组合:")
        for r in failed_tests:
            print(f"  并发={r['concurrency']}, Prompt={r['prompt_size']}: "
                  f"成功率{r['success_rate']:.1f}%")
    else:
        print("✅ 所有测试都成功！")
    
    # 找出最慢的组合
    slowest = max(all_results, key=lambda x: x['avg_time'])
    print(f"\n最慢的组合:")
    print(f"  并发={slowest['concurrency']}, Prompt={slowest['prompt_size']}: "
          f"平均{slowest['avg_time']:.1f}秒")
    
    # 找出最快的组合
    fastest = min(all_results, key=lambda x: x['avg_time'] if x['avg_time'] > 0 else float('inf'))
    print(f"\n最快的组合:")
    print(f"  并发={fastest['concurrency']}, Prompt={fastest['prompt_size']}: "
          f"平均{fastest['avg_time']:.1f}秒")
    
    # 保存结果到文件
    with open('stress_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n详细结果已保存到: stress_test_results.json")

if __name__ == "__main__":
    asyncio.run(main())
