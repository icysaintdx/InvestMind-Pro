#!/usr/bin/env python3
"""
复杂并发测试 - 使用真实风控智能体提示词测试

使用方法:
python test_concurrency_complex.py
"""

import asyncio
import aiohttp
import time
from datetime import datetime
import json

BASE_URL = "http://localhost:8000"
STOCK_CODE = "600519"

# 6个风控智能体的真实提示词
RISK_AGENTS = [
    {
        "id": "risk_aggressive",
        "name": "激进风控师",
        "instruction": """作为激进风控师，假设我们必须买入该股票，请给出：
1. 最佳买入点位（具体价格）
2. 止损位设置（具体价格和百分比）
3. 目标价位（短期、中期、长期）
4. 仓位建议（百分比）
5. 最大可接受亏损（金额和百分比）
6. 加仓条件（什么情况下可以加仓）
7. 减仓条件（什么情况下必须减仓）
8. 最大化赔率的策略（如何在控制风险的同时追求最大收益）

请给出具体、可执行的建议，不要模棱两可。"""
    },
    {
        "id": "risk_conservative",
        "name": "保守风控师",
        "instruction": """作为保守风控师，请指出：
1. 当前最危险的风险点（至少列出5个）
2. 每个风险点的发生概率和影响程度
3. 最保守的仓位建议（不超过多少）
4. 严格的止损线（不能突破的底线）
5. 必须满足的买入条件（至少列出3个）
6. 立即清仓的警告信号（什么情况下必须马上卖出）
7. 不建议买入的理由（如果有）
8. 对激进投资者的警告

请用最严格的标准进行评估，宁可错过，不可犯错。"""
    },
    {
        "id": "risk_neutral",
        "name": "中立风控师",
        "instruction": """作为中立风控师，请从中立角度评估：
1. 风险收益比分析（具体数值）
2. 期望收益率计算（乐观、中性、悲观三种情况）
3. 最大回撤风险评估
4. 合理的仓位建议（百分比范围）
5. 动态调仓策略（什么情况下加仓/减仓）
6. 持有周期建议（短期/中期/长期）
7. 风险管理建议（具体措施）
8. 综合评级（A/B/C/D/E）和理由

请给出客观、理性的分析，不偏向乐观或悲观。"""
    }
]

def get_test_request(agent_config):
    """生成测试请求"""
    return {
        "agent_id": agent_config["id"],
        "stock_code": STOCK_CODE,
        "stock_data": {
            "symbol": STOCK_CODE,
            "name": "贵州茅台",
            "price": 1500.0,
            "change_percent": 2.5
        },
        "previous_outputs": {
            "news_analyst": "最近新闻偏积极，多家机构给出买入评级。",
            "technical": "技术面处于上升通道，支撑位1450元，压力位1600元。",
            "fundamental": "PE估值30倍，处于历史中位，ROE 25%，盈利能力强。",
            "bull_researcher": "看涨逻辑：行业复苏+估值修复+政策支持，目标价1800元。",
            "bear_researcher": "看跌风险：宏观经济下行+行业竞争加剧+估值偏高，可能回调至1300元。"
        },
        "custom_instruction": agent_config["instruction"]
    }

async def test_concurrent(num_concurrent):
    """测试指定并发数"""
    print(f"\n{'='*70}")
    print(f"🚀 测试并发数: {num_concurrent}")
    
    # 循环使用风控智能体
    agents_to_use = [RISK_AGENTS[i % len(RISK_AGENTS)] for i in range(num_concurrent)]
    print(f"🧑‍💼 使用智能体: {', '.join([a['name'] for a in agents_to_use])}")
    print(f"{'='*70}")
    
    start_time = time.time()
    results = []
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i, agent in enumerate(agents_to_use):
            request_data = get_test_request(agent)
            task = session.post(
                f"{BASE_URL}/api/analyze",
                json=request_data,
                timeout=aiohttp.ClientTimeout(total=180)  # 3分钟超时
            )
            tasks.append((i+1, agent['name'], task))
        
        # 并发执行
        for req_id, agent_name, task in tasks:
            try:
                req_start = time.time()
                async with await task as response:
                    elapsed = time.time() - req_start
                    if response.status == 200:
                        data = await response.json()
                        success = data.get('success', False)
                        results.append({
                            'id': req_id,
                            'agent': agent_name,
                            'status': 'success' if success else 'failed',
                            'elapsed': elapsed
                        })
                        print(f"  ✅ #{req_id} {agent_name}: {elapsed:.2f}秒")
                    else:
                        results.append({
                            'id': req_id,
                            'agent': agent_name,
                            'status': 'failed',
                            'elapsed': elapsed
                        })
                        print(f"  ❌ #{req_id} {agent_name}: HTTP {response.status}")
            except asyncio.TimeoutError:
                elapsed = time.time() - req_start
                results.append({
                    'id': req_id,
                    'agent': agent_name,
                    'status': 'timeout',
                    'elapsed': elapsed
                })
                print(f"  ⏱️ #{req_id} {agent_name}: 超时 ({elapsed:.2f}秒)")
            except Exception as e:
                results.append({
                    'id': req_id,
                    'agent': agent_name,
                    'status': 'error',
                    'elapsed': 0
                })
                print(f"  🔥 #{req_id} {agent_name}: {str(e)}")
    
    total_elapsed = time.time() - start_time
    
    # 统计
    success_count = sum(1 for r in results if r['status'] == 'success')
    success_times = [r['elapsed'] for r in results if r['status'] == 'success']
    
    print(f"\n📊 结果统计:")
    print(f"  总耗时: {total_elapsed:.2f}秒")
    print(f"  成功: {success_count}/{num_concurrent} ({success_count/num_concurrent*100:.1f}%)")
    if success_times:
        print(f"  平均: {sum(success_times)/len(success_times):.2f}秒")
        print(f"  最快: {min(success_times):.2f}秒")
        print(f"  最慢: {max(success_times):.2f}秒")
    print(f"  吞吐量: {success_count/total_elapsed:.2f} 请求/秒")
    
    return {
        'concurrent': num_concurrent,
        'total_elapsed': total_elapsed,
        'success_count': success_count,
        'success_rate': success_count/num_concurrent*100,
        'avg_time': sum(success_times)/len(success_times) if success_times else 0,
        'throughput': success_count/total_elapsed
    }

async def main():
    print("="*70)
    print("🧪 AlphaCouncil 复杂并发测试（真实风控智能体提示词）")
    print("="*70)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"后端地址: {BASE_URL}")
    print(f"测试股票: {STOCK_CODE}")
    print(f"使用智能体: {', '.join([a['name'] for a in RISK_AGENTS])}")
    print(f"提示词长度: 约{sum(len(a['instruction']) for a in RISK_AGENTS)}字符")
    
    # 测试不同并发数
    test_cases = [1, 2, 3, 4, 5, 6]
    all_results = []
    
    for concurrent in test_cases:
        result = await test_concurrent(concurrent)
        all_results.append(result)
        
        if concurrent < test_cases[-1]:
            print(f"\n⏸️  等待10秒后继续...")
            await asyncio.sleep(10)
    
    # 总结
    print("\n" + "="*70)
    print("📊 测试总结")
    print("="*70)
    print(f"\n{'并发数':<8} {'成功率':<12} {'平均耗时':<14} {'吞吐量':<14} {'推荐'}")
    print("-" * 70)
    
    best_concurrent = None
    best_throughput = 0
    
    for r in all_results:
        recommend = ""
        if r['success_rate'] == 100 and r['throughput'] > best_throughput:
            best_throughput = r['throughput']
            best_concurrent = r['concurrent']
            recommend = "✅ 推荐"
        elif r['success_rate'] < 80:
            recommend = "❌ 不推荐"
        
        print(f"{r['concurrent']:<8} {r['success_rate']:<12.1f}% {r['avg_time']:<14.2f}s {r['throughput']:<14.2f}/s {recommend}")
    
    print("\n" + "="*70)
    print(f"🎯 推荐并发数: {best_concurrent}")
    print(f"   理由: 成功率100%，吞吐量最高({best_throughput:.2f}请求/秒)")
    print("="*70)
    
    # 保存结果
    filename = f"complex_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({
            'test_time': datetime.now().isoformat(),
            'test_type': 'complex_risk_agents',
            'results': all_results
        }, f, indent=2, ensure_ascii=False)
    print(f"\n💾 结果已保存到: {filename}")

if __name__ == "__main__":
    asyncio.run(main())
