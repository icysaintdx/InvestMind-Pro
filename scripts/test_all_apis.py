#!/usr/bin/env python3
"""
测试所有API端点是否正常工作
"""

import asyncio
import httpx
import json
from datetime import datetime
from pathlib import Path

# API基础URL
BASE_URL = "http://localhost:8000"

async def test_api():
    """测试所有API端点"""
    
    async with httpx.AsyncClient() as client:
        results = []
        
        print("=" * 60)
        print("AlphaCouncil API 端点测试")
        print("=" * 60)
        print()
        
        # 1. 测试新闻API
        print("📰 测试新闻API...")
        
        # 获取新闻源
        try:
            response = await client.get(f"{BASE_URL}/api/news/sources")
            if response.status_code == 200:
                print("  ✅ GET /api/news/sources - 成功")
                results.append(("news/sources", "SUCCESS"))
            else:
                print(f"  ❌ GET /api/news/sources - 失败 ({response.status_code})")
                results.append(("news/sources", "FAILED"))
        except Exception as e:
            print(f"  ❌ GET /api/news/sources - 错误: {e}")
            results.append(("news/sources", "ERROR"))
            
        # 测试新闻分析
        try:
            data = {
                "stock_code": "600519",
                "days": 7
            }
            response = await client.post(f"{BASE_URL}/api/news/analyze", json=data)
            if response.status_code == 200:
                print("  ✅ POST /api/news/analyze - 成功")
                results.append(("news/analyze", "SUCCESS"))
            else:
                print(f"  ❌ POST /api/news/analyze - 失败 ({response.status_code})")
                results.append(("news/analyze", "FAILED"))
        except Exception as e:
            print(f"  ❌ POST /api/news/analyze - 错误: {e}")
            results.append(("news/analyze", "ERROR"))
            
        print()
        
        # 2. 测试辩论API
        print("🤖 测试辩论API...")
        
        # 测试研究辩论
        try:
            data = {
                "stock_code": "600519",
                "analysis_data": {"price": 1800},
                "debate_type": "research",
                "rounds": 2
            }
            response = await client.post(f"{BASE_URL}/api/debate/research", json=data)
            if response.status_code == 200:
                print("  ✅ POST /api/debate/research - 成功")
                results.append(("debate/research", "SUCCESS"))
            else:
                print(f"  ❌ POST /api/debate/research - 失败 ({response.status_code})")
                results.append(("debate/research", "FAILED"))
        except Exception as e:
            print(f"  ❌ POST /api/debate/research - 错误: {e}")
            results.append(("debate/research", "ERROR"))
            
        # 测试风险辩论
        try:
            response = await client.post(f"{BASE_URL}/api/debate/risk", json=data)
            if response.status_code == 200:
                print("  ✅ POST /api/debate/risk - 成功")
                results.append(("debate/risk", "SUCCESS"))
            else:
                print(f"  ❌ POST /api/debate/risk - 失败 ({response.status_code})")
                results.append(("debate/risk", "FAILED"))
        except Exception as e:
            print(f"  ❌ POST /api/debate/risk - 错误: {e}")
            results.append(("debate/risk", "ERROR"))
            
        print()
        
        # 3. 测试交易API
        print("💹 测试交易API...")
        
        # 获取投资组合
        try:
            response = await client.get(f"{BASE_URL}/api/trading/portfolio")
            if response.status_code == 200:
                print("  ✅ GET /api/trading/portfolio - 成功")
                results.append(("trading/portfolio", "SUCCESS"))
            else:
                print(f"  ❌ GET /api/trading/portfolio - 失败 ({response.status_code})")
                results.append(("trading/portfolio", "FAILED"))
        except Exception as e:
            print(f"  ❌ GET /api/trading/portfolio - 错误: {e}")
            results.append(("trading/portfolio", "ERROR"))
            
        # 测试交易执行
        try:
            trade_order = {
                "stock_code": "600519",
                "action": "BUY",
                "quantity": 100,
                "price": 1800.0,
                "order_type": "LIMIT"
            }
            response = await client.post(f"{BASE_URL}/api/trading/execute", json=trade_order)
            if response.status_code == 200:
                print("  ✅ POST /api/trading/execute - 成功")
                results.append(("trading/execute", "SUCCESS"))
            else:
                print(f"  ❌ POST /api/trading/execute - 失败 ({response.status_code})")
                results.append(("trading/execute", "FAILED"))
        except Exception as e:
            print(f"  ❌ POST /api/trading/execute - 错误: {e}")
            results.append(("trading/execute", "ERROR"))
            
        # 获取交易历史
        try:
            response = await client.get(f"{BASE_URL}/api/trading/history?limit=10")
            if response.status_code == 200:
                print("  ✅ GET /api/trading/history - 成功")
                results.append(("trading/history", "SUCCESS"))
            else:
                print(f"  ❌ GET /api/trading/history - 失败 ({response.status_code})")
                results.append(("trading/history", "FAILED"))
        except Exception as e:
            print(f"  ❌ GET /api/trading/history - 错误: {e}")
            results.append(("trading/history", "ERROR"))
            
        print()
        
        # 4. 测试验证API
        print("🔄 测试验证API...")
        
        # 记录决策
        try:
            decision = {
                "stock_code": "600519",
                "recommendation": "BUY",
                "confidence": 0.75,
                "target_price": 2000.0,
                "stop_loss": 1700.0,
                "reasons": ["技术指标看涨", "基本面良好"],
                "source": "DEBATE",
                "strategy": "平衡型策略"
            }
            response = await client.post(f"{BASE_URL}/api/verification/decision", json=decision)
            if response.status_code == 200:
                print("  ✅ POST /api/verification/decision - 成功")
                results.append(("verification/decision", "SUCCESS"))
                
                # 保存decision_id供后续测试
                decision_id = response.json().get("decision_id")
            else:
                print(f"  ❌ POST /api/verification/decision - 失败 ({response.status_code})")
                results.append(("verification/decision", "FAILED"))
                decision_id = None
        except Exception as e:
            print(f"  ❌ POST /api/verification/decision - 错误: {e}")
            results.append(("verification/decision", "ERROR"))
            decision_id = None
            
        # 获取决策列表
        try:
            response = await client.get(f"{BASE_URL}/api/verification/decisions?limit=10")
            if response.status_code == 200:
                print("  ✅ GET /api/verification/decisions - 成功")
                results.append(("verification/decisions", "SUCCESS"))
            else:
                print(f"  ❌ GET /api/verification/decisions - 失败 ({response.status_code})")
                results.append(("verification/decisions", "FAILED"))
        except Exception as e:
            print(f"  ❌ GET /api/verification/decisions - 错误: {e}")
            results.append(("verification/decisions", "ERROR"))
            
        # 获取策略列表
        try:
            response = await client.get(f"{BASE_URL}/api/verification/strategies")
            if response.status_code == 200:
                print("  ✅ GET /api/verification/strategies - 成功")
                results.append(("verification/strategies", "SUCCESS"))
            else:
                print(f"  ❌ GET /api/verification/strategies - 失败 ({response.status_code})")
                results.append(("verification/strategies", "FAILED"))
        except Exception as e:
            print(f"  ❌ GET /api/verification/strategies - 错误: {e}")
            results.append(("verification/strategies", "ERROR"))
            
        print()
        
        # 5. 测试智能体管理API
        print("🤖 测试智能体管理API...")
        
        # 获取注册表
        try:
            response = await client.get(f"{BASE_URL}/api/agents/registry")
            if response.status_code == 200:
                data = response.json()
                agent_count = data.get("data", {}).get("total", 0)
                print(f"  ✅ GET /api/agents/registry - 成功 (共{agent_count}个智能体)")
                results.append(("agents/registry", "SUCCESS"))
            else:
                print(f"  ❌ GET /api/agents/registry - 失败 ({response.status_code})")
                results.append(("agents/registry", "FAILED"))
        except Exception as e:
            print(f"  ❌ GET /api/agents/registry - 错误: {e}")
            results.append(("agents/registry", "ERROR"))
            
        # 获取智能体列表
        try:
            response = await client.get(f"{BASE_URL}/api/agents/list")
            if response.status_code == 200:
                print("  ✅ GET /api/agents/list - 成功")
                results.append(("agents/list", "SUCCESS"))
            else:
                print(f"  ❌ GET /api/agents/list - 失败 ({response.status_code})")
                results.append(("agents/list", "FAILED"))
        except Exception as e:
            print(f"  ❌ GET /api/agents/list - 错误: {e}")
            results.append(("agents/list", "ERROR"))
            
        # 获取工作流阶段
        try:
            response = await client.get(f"{BASE_URL}/api/agents/workflow/stages")
            if response.status_code == 200:
                print("  ✅ GET /api/agents/workflow/stages - 成功")
                results.append(("agents/workflow/stages", "SUCCESS"))
            else:
                print(f"  ❌ GET /api/agents/workflow/stages - 失败 ({response.status_code})")
                results.append(("agents/workflow/stages", "FAILED"))
        except Exception as e:
            print(f"  ❌ GET /api/agents/workflow/stages - 错误: {e}")
            results.append(("agents/workflow/stages", "ERROR"))
        
        print()
        print("=" * 60)
        print("测试结果汇总")
        print("=" * 60)
        
        # 统计结果
        success_count = sum(1 for _, status in results if status == "SUCCESS")
        failed_count = sum(1 for _, status in results if status == "FAILED")
        error_count = sum(1 for _, status in results if status == "ERROR")
        
        print(f"✅ 成功: {success_count}")
        print(f"❌ 失败: {failed_count}")
        print(f"⚠️ 错误: {error_count}")
        print(f"📊 总计: {len(results)}")
        
        # 成功率
        if results:
            success_rate = success_count / len(results) * 100
            print(f"🎯 成功率: {success_rate:.1f}%")
            
        # 保存测试结果
        test_report = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(results),
            "success": success_count,
            "failed": failed_count,
            "error": error_count,
            "success_rate": success_rate if results else 0,
            "details": [{"endpoint": endpoint, "status": status} for endpoint, status in results]
        }
        
        report_file = Path("backend/data/api_test_report.json")
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(test_report, f, ensure_ascii=False, indent=2)
            
        print(f"\n📝 测试报告已保存到: {report_file}")
        
        return test_report


async def main():
    """主函数"""
    print("🚀 开始测试AlphaCouncil API...")
    print("请确保后端服务已启动 (python backend/server.py)")
    print()
    
    try:
        # 测试连接
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/docs")
            if response.status_code != 200:
                print("❌ 无法连接到后端服务，请先启动服务器")
                print("运行: python backend/server.py")
                return
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        print("请先启动后端服务: python backend/server.py")
        return
        
    # 运行测试
    await test_api()


if __name__ == "__main__":
    asyncio.run(main())
