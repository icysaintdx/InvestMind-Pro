#!/usr/bin/env python3
"""
模拟第三阶段的真实并发请求
使用真实的前序输出和风控指令
"""

import asyncio
import aiohttp
import time
import json
from datetime import datetime

# 真实的前序输出（从实际运行中获取）
PREVIOUS_OUTPUTS = {
    "news_analyst": "基于当前市场环境分析，该股票近期新闻舆情偏向中性，没有重大利空消息。",
    "social_analyst": "社交媒体情绪分析显示市场情绪相对理性，散户讨论热度中等。",
    "china_market": "A股大盘处于震荡整理阶段，市场流动性适中，政策环境相对稳定。",
    "industry": "行业处于成长期，竞争格局相对稳定，产业链上下游关系良好。",
    "macro": "货币政策保持稳健，财政政策适度宽松，经济周期处于复苏阶段。",
    "technical": "K线形态显示上升趋势，均线系统呈多头排列，MACD指标显示买入信号。",
    "funds": "主力资金净流入，机构持仓稳定，北向资金持续买入，资金面偏强。",
    "fundamental": "PE估值处于合理区间，ROE保持较高水平，财务健康度良好，基本面良好。",
    "bull_researcher": "看涨逻辑：行业景气度提升，公司竞争力增强，估值修复空间大，建议买入。",
    "bear_researcher": "看跌风险：宏观经济存在不确定性，行业竞争加剧，估值偏高，谨慎操作。",
    "manager_fundamental": "基本面综合评估：内在价值评估合理，长期投资价值较高，评级推荐买入。",
    "manager_momentum": "市场动能分析：短期动能偏强，市场情绪积极，资金流入持续，短期看多。",
    "research_manager": "研究部综合意见：基本面支持，技术面配合，资金面良好，评级买入。"
}

# 6个风控智能体的配置
RISK_AGENTS = [
    {
        "id": "risk_aggressive",
        "instruction": "假设我们必须买入，如何设置止损以最大化赔率？"
    },
    {
        "id": "risk_conservative",
        "instruction": "指出当前最危险的风险点，并给出最保守的仓位建议。"
    },
    {
        "id": "risk_neutral",
        "instruction": "从中立角度评估风险收益比，给出合理的风险管理建议。"
    },
    {
        "id": "risk_system",
        "instruction": "评估系统性风险对该股票的潜在影响。"
    },
    {
        "id": "risk_portfolio",
        "instruction": "从组合管理角度，评估该股票在投资组合中的风险贡献。"
    },
    {
        "id": "risk_manager",
        "instruction": "作为风险总监，给出最终的风险评估和仓位建议。"
    }
]

STOCK_DATA = {
    "symbol": "600547",
    "name": "山东黄金",
    "price": 10.50,
    "change": 2.5,
    "volume": 1000000
}

async def send_request(session, agent, attempt=1):
    """发送单个分析请求"""
    url = "http://localhost:8000/api/analyze"
    
    payload = {
        "agent_id": agent["id"],
        "stock_code": STOCK_DATA["symbol"],
        "stock_data": STOCK_DATA,
        "previous_outputs": PREVIOUS_OUTPUTS,
        "custom_instruction": agent["instruction"]
    }
    
    start_time = time.time()
    
    try:
        print(f"[{agent['id']}] 🚀 开始请求 (尝试 {attempt})")
        
        async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=150)) as response:
            elapsed = time.time() - start_time
            
            if response.status == 200:
                result = await response.json()
                if result.get("success"):
                    print(f"[{agent['id']}] ✅ 成功 ({elapsed:.1f}秒)")
                    return {
                        "agent_id": agent["id"],
                        "success": True,
                        "elapsed": elapsed,
                        "result_length": len(result.get("result", ""))
                    }
                else:
                    print(f"[{agent['id']}] ❌ 失败: {result.get('error')}")
                    return {
                        "agent_id": agent["id"],
                        "success": False,
                        "elapsed": elapsed,
                        "error": result.get("error")
                    }
            else:
                print(f"[{agent['id']}] ❌ HTTP {response.status}")
                return {
                    "agent_id": agent["id"],
                    "success": False,
                    "elapsed": elapsed,
                    "error": f"HTTP {response.status}"
                }
                
    except asyncio.TimeoutError:
        elapsed = time.time() - start_time
        print(f"[{agent['id']}] ⏱️ 超时 ({elapsed:.1f}秒)")
        return {
            "agent_id": agent["id"],
            "success": False,
            "elapsed": elapsed,
            "error": "Timeout"
        }
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[{agent['id']}] ❌ 错误: {str(e)}")
        return {
            "agent_id": agent["id"],
            "success": False,
            "elapsed": elapsed,
            "error": str(e)
        }

async def test_batch(batch_size):
    """测试指定批次大小的并发"""
    print(f"\n{'='*70}")
    print(f"测试批次大小: {batch_size}")
    print(f"{'='*70}\n")
    
    async with aiohttp.ClientSession() as session:
        results = []
        
        # 分批发送
        for i in range(0, len(RISK_AGENTS), batch_size):
            batch = RISK_AGENTS[i:i+batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(RISK_AGENTS) + batch_size - 1) // batch_size
            
            print(f"\n--- 批次 {batch_num}/{total_batches} ---")
            
            # 并发发送这一批
            tasks = [send_request(session, agent) for agent in batch]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
            
            # 批次间等待
            if i + batch_size < len(RISK_AGENTS):
                print(f"\n⏸️  等待3秒后继续下一批...\n")
                await asyncio.sleep(3)
        
        return results

def analyze_results(results, batch_size):
    """分析测试结果"""
    print(f"\n{'='*70}")
    print(f"结果分析 (批次大小: {batch_size})")
    print(f"{'='*70}\n")
    
    success_count = sum(1 for r in results if r["success"])
    total_count = len(results)
    success_rate = success_count / total_count * 100
    
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    print(f"总请求数: {total_count}")
    print(f"成功: {success_count} ({success_rate:.1f}%)")
    print(f"失败: {len(failed)} ({100-success_rate:.1f}%)")
    print()
    
    if successful:
        avg_time = sum(r["elapsed"] for r in successful) / len(successful)
        min_time = min(r["elapsed"] for r in successful)
        max_time = max(r["elapsed"] for r in successful)
        print(f"成功请求耗时:")
        print(f"  平均: {avg_time:.1f}秒")
        print(f"  最快: {min_time:.1f}秒")
        print(f"  最慢: {max_time:.1f}秒")
        print()
    
    if failed:
        print(f"失败请求:")
        for r in failed:
            print(f"  [{r['agent_id']}] {r['error']} ({r['elapsed']:.1f}秒)")
        print()
    
    return {
        "batch_size": batch_size,
        "total": total_count,
        "success": success_count,
        "failed": len(failed),
        "success_rate": success_rate,
        "avg_time": avg_time if successful else 0
    }

async def main():
    """主测试函数"""
    print("="*70)
    print("第三阶段真实并发测试")
    print("="*70)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"后端地址: http://localhost:8000")
    print(f"股票代码: {STOCK_DATA['symbol']}")
    print(f"前序输出数量: {len(PREVIOUS_OUTPUTS)}")
    print(f"风控智能体数量: {len(RISK_AGENTS)}")
    print()
    
    # 测试不同批次大小
    test_cases = [
        ("批次2（当前设置）", 2),
        ("批次3", 3),
        ("批次6（全并发）", 6),
    ]
    
    all_results = []
    
    for name, batch_size in test_cases:
        print(f"\n{'#'*70}")
        print(f"# {name}")
        print(f"{'#'*70}")
        
        results = await test_batch(batch_size)
        summary = analyze_results(results, batch_size)
        all_results.append(summary)
        
        # 测试间等待
        print(f"\n⏸️  等待10秒后继续下一个测试...\n")
        await asyncio.sleep(10)
    
    # 总结
    print(f"\n{'='*70}")
    print("总结")
    print(f"{'='*70}\n")
    
    print(f"{'批次大小':<15} {'成功率':<15} {'平均耗时':<15}")
    print("-" * 45)
    for r in all_results:
        print(f"{r['batch_size']:<15} {r['success_rate']:.1f}%{'':<10} {r['avg_time']:.1f}秒")
    
    print()
    print("🎯 关键发现:")
    
    # 找出成功率最高的
    best = max(all_results, key=lambda x: x['success_rate'])
    print(f"  最佳批次大小: {best['batch_size']} (成功率 {best['success_rate']:.1f}%)")
    
    # 找出问题
    worst = min(all_results, key=lambda x: x['success_rate'])
    if worst['success_rate'] < 100:
        print(f"  问题批次: {worst['batch_size']} (成功率 {worst['success_rate']:.1f}%)")
        print(f"  失败数量: {worst['failed']}")

if __name__ == "__main__":
    asyncio.run(main())
