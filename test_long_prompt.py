#!/usr/bin/env python3
"""
测试长Prompt的响应时间
模拟第三阶段的真实Prompt长度
"""

import asyncio
import aiohttp
import time

STOCK_DATA = {
    "symbol": "600547",
    "name": "山东黄金",
    "nowPri": "10.50",
    "increase": "2.5",
    "traAmount": "1000000"
}

# 模拟13个前序智能体的输出（每个约500字符）
PREVIOUS_OUTPUTS = {}
for i in range(13):
    agent_name = f"agent_{i}"
    # 生成约500字符的输出
    output = f"这是智能体{i}的详细分析报告。" * 25  # 约500字符
    PREVIOUS_OUTPUTS[agent_name] = output

async def test_prompt(prompt_length_desc):
    url = "http://localhost:8000/api/analyze"
    
    payload = {
        "agent_id": "risk_aggressive",
        "stock_code": STOCK_DATA["symbol"],
        "stock_data": STOCK_DATA,
        "previous_outputs": PREVIOUS_OUTPUTS,
        "custom_instruction": "假设我们必须买入，如何设置止损以最大化赔率？"
    }
    
    total_prev_len = sum(len(v) for v in PREVIOUS_OUTPUTS.values())
    print(f"\n{'='*70}")
    print(f"测试: {prompt_length_desc}")
    print(f"{'='*70}")
    print(f"前序输出数量: {len(PREVIOUS_OUTPUTS)}")
    print(f"前序输出总长度: {total_prev_len} 字符")
    print(f"预估Prompt长度: ~{total_prev_len + 500} 字符")
    print()
    
    start_time = time.time()
    
    async with aiohttp.ClientSession() as session:
        try:
            print("🚀 开始请求...")
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=180)) as response:
                elapsed = time.time() - start_time
                
                print(f"状态码: {response.status}")
                print(f"耗时: {elapsed:.1f}秒")
                
                if response.status == 200:
                    result = await response.json()
                    if result.get('success'):
                        print(f"✅ 成功")
                        print(f"结果长度: {len(result.get('result', ''))} 字符")
                    else:
                        print(f"❌ 失败: {result.get('error')}")
                else:
                    text = await response.text()
                    print(f"❌ HTTP {response.status}")
                    print(f"响应: {text[:200]}")
                
                return elapsed
                
        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            print(f"⏱️ 超时 ({elapsed:.1f}秒)")
            return elapsed
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ 错误: {e}")
            return elapsed

async def main():
    print("="*70)
    print("长Prompt响应时间测试")
    print("="*70)
    print()
    print("模拟第三阶段的真实Prompt长度")
    print("13个前序智能体，每个约500字符")
    print()
    
    # 测试1: 完整的前序输出
    elapsed = await test_prompt("完整前序输出 (~6500字符)")
    
    print()
    print("="*70)
    print("总结")
    print("="*70)
    print(f"完整Prompt耗时: {elapsed:.1f}秒")
    
    if elapsed > 120:
        print("❌ 超过120秒，会导致超时！")
    elif elapsed > 60:
        print("⚠️ 超过60秒，接近超时边缘")
    else:
        print("✅ 在可接受范围内")

if __name__ == "__main__":
    asyncio.run(main())
