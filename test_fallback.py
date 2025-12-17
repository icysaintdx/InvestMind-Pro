"""
测试降级处理器
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.utils.llm_fallback_handler import get_fallback_handler, TextSummarizer
import httpx

async def test_text_summarizer():
    """测试文本摘要器"""
    print("=" * 60)
    print("测试文本摘要器")
    print("=" * 60)
    
    summarizer = TextSummarizer()
    
    # 测试文本
    test_text = """
    贵州茅台（600519）今日股价表现强势，开盘价2158元，最高价2180元，最低价2150元，收盘价2175元。
    成交量达到12万手，成交额26亿元。从技术面来看，MACD金叉，KDJ超买，RSI处于强势区间。
    基本面方面，公司第三季度营收450亿元，同比增长15%，净利润220亿元，同比增长18%。
    机构观点：中信证券给予买入评级，目标价2500元；海通证券维持增持评级，目标价2400元。
    风险提示：白酒消费增速放缓，原材料价格上涨，政策调控风险。
    投资建议：短期看多，建议逢低买入，止损位2100元，目标位2300元。
    """
    
    # 测试不同压缩比例
    for ratio in [1.0, 0.5, 0.25, 0.1]:
        compressed = await summarizer.compress(
            test_text,
            target_ratio=ratio,
            preserve_key_info=True,
            context="STOCK_ANALYSIS"
        )
        print(f"\n压缩比例: {ratio*100:.0f}%")
        print(f"原始长度: {len(test_text)} 字符")
        print(f"压缩后长度: {len(compressed)} 字符")
        print(f"压缩后内容:\n{compressed[:200]}...")
        print("-" * 40)

async def test_fallback_handler():
    """测试降级处理器"""
    print("\n" + "=" * 60)
    print("测试降级处理器")
    print("=" * 60)
    
    handler = get_fallback_handler()
    
    # 测试1: 模拟超时的请求（使用假URL）
    print("\n测试1: 模拟完全失败的请求")
    print("-" * 40)
    
    # 创建一个永远超时的客户端
    client = httpx.AsyncClient(timeout=httpx.Timeout(0.001))  # 1毫秒超时
    
    try:
        result, metrics = await handler.execute_with_fallback(
            client=client,
            url="https://httpbin.org/delay/10",  # 延迟10秒的测试URL
            headers={},
            data={
                "messages": [
                    {"role": "user", "content": "分析贵州茅台的投资价值"}
                ],
                "max_tokens": 1024
            },
            agent_role="RISK",
            max_retries=2  # 减少重试次数以加快测试
        )
        
        print(f"结果: {result['choices'][0]['message']['content'][:200]}...")
        print(f"降级级别: {result.get('fallback_level', 0)}")
        print(f"最终状态: {metrics.final_status}")
        print(f"总耗时: {metrics.total_time:.1f}秒")
        print(f"尝试次数: {len(metrics.attempt_times)}")
        print(f"错误类型: {metrics.error_types}")
        
    finally:
        await client.aclose()
    
    # 测试2: 测试缓存
    print("\n测试2: 测试缓存功能")
    print("-" * 40)
    
    client2 = httpx.AsyncClient(timeout=httpx.Timeout(0.001))
    
    try:
        # 第二次调用相同请求，应该命中缓存
        result2, metrics2 = await handler.execute_with_fallback(
            client=client2,
            url="https://httpbin.org/delay/10",
            headers={},
            data={
                "messages": [
                    {"role": "user", "content": "分析贵州茅台的投资价值"}
                ],
                "max_tokens": 1024
            },
            agent_role="RISK",
            max_retries=2
        )
        
        if "cached" in metrics2.final_status:
            print("✅ 成功命中缓存！")
        else:
            print("❌ 未命中缓存")
        
        print(f"最终状态: {metrics2.final_status}")
        print(f"总耗时: {metrics2.total_time:.3f}秒")
        
    finally:
        await client2.aclose()
    
    # 测试3: 测试不同智能体的默认响应
    print("\n测试3: 测试不同智能体的默认响应")
    print("-" * 40)
    
    roles = ["NEWS", "RISK", "BULL", "BEAR", "TRADER"]
    
    for role in roles:
        client3 = httpx.AsyncClient(timeout=httpx.Timeout(0.001))
        try:
            result3, _ = await handler.execute_with_fallback(
                client=client3,
                url="https://fake.url",
                headers={},
                data={"messages": [{"role": "user", "content": "test"}]},
                agent_role=role,
                max_retries=1
            )
            
            response_text = result3['choices'][0]['message']['content']
            print(f"\n{role}: {response_text[:100]}...")
            
        finally:
            await client3.aclose()

async def test_with_real_api():
    """测试真实API（需要配置API密钥）"""
    print("\n" + "=" * 60)
    print("测试真实API（可选）")
    print("=" * 60)
    
    # 检查是否有API密钥
    api_key = os.getenv("SILICONFLOW_API_KEY")
    if not api_key:
        print("跳过真实API测试（未配置SILICONFLOW_API_KEY）")
        return
    
    handler = get_fallback_handler()
    client = httpx.AsyncClient(
        timeout=httpx.Timeout(
            timeout=90.0,
            connect=15.0,
            read=60.0,
            write=15.0,
            pool=15.0
        )
    )
    
    try:
        # 测试一个较长的提示词
        long_prompt = "分析贵州茅台的投资价值。" * 100  # 重复100次
        
        result, metrics = await handler.execute_with_fallback(
            client=client,
            url="https://api.siliconflow.cn/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            data={
                "model": "Qwen/Qwen2.5-7B-Instruct",
                "messages": [
                    {"role": "system", "content": "你是一个股票分析师"},
                    {"role": "user", "content": long_prompt}
                ],
                "max_tokens": 256,
                "temperature": 0.7
            },
            agent_role="FUNDAMENTAL",
            max_retries=3
        )
        
        print(f"\n真实API测试结果:")
        print(f"降级级别: {result.get('fallback_level', 0)}")
        print(f"最终状态: {metrics.final_status}")
        print(f"总耗时: {metrics.total_time:.1f}秒")
        print(f"响应预览: {result['choices'][0]['message']['content'][:200]}...")
        
    finally:
        await client.aclose()

async def main():
    """主测试函数"""
    print("\n🧪 降级处理器测试套件")
    print("=" * 60)
    
    # 运行各项测试
    await test_text_summarizer()
    await test_fallback_handler()
    await test_with_real_api()
    
    print("\n" + "=" * 60)
    print("✅ 所有测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
