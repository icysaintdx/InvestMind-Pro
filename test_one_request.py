#!/usr/bin/env python3
"""
测试单个请求 - 验证格式是否正确
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

def generate_prompt(size):
    """生成指定长度的Prompt"""
    base_text = "这是一段详细的市场分析内容，包含了各种技术指标、基本面数据、市场情绪等信息。" * 10
    repeat_count = (size // len(base_text)) + 1
    full_text = base_text * repeat_count
    return full_text[:size]

async def test_single_request():
    url = "http://localhost:8000/api/analyze"
    
    # 生成测试数据
    previous_outputs = {}
    for i in range(5):
        previous_outputs[f"agent_{i}"] = generate_prompt(200)
    
    payload = {
        "agent_id": "test_agent",
        "stock_code": STOCK_DATA["symbol"],
        "stock_data": STOCK_DATA,
        "previous_outputs": previous_outputs,
        "custom_instruction": "请基于前序分析给出你的观点。"
    }
    
    print("发送测试请求...")
    print(f"前序输出数量: {len(previous_outputs)}")
    print(f"总Prompt长度: ~{sum(len(v) for v in previous_outputs.values())} 字符")
    print()
    
    start_time = time.time()
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=60)) as response:
                elapsed = time.time() - start_time
                
                print(f"状态码: {response.status}")
                print(f"耗时: {elapsed:.1f}秒")
                
                if response.status == 200:
                    result = await response.json()
                    print(f"成功: {result.get('success')}")
                    if result.get('success'):
                        print(f"结果长度: {len(result.get('result', ''))} 字符")
                        print("✅ 测试成功！")
                    else:
                        print(f"错误: {result.get('error')}")
                else:
                    text = await response.text()
                    print(f"响应内容: {text[:500]}")
                    
        except Exception as e:
            print(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_single_request())
