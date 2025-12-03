"""
测试LLM集成
验证统一LLM客户端和智能体调用是否正常工作
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.utils.llm_client import create_llm_client, create_agent_llm
from backend.utils.logging_config import get_logger

logger = get_logger("test_llm")

async def test_unified_client():
    """测试统一LLM客户端"""
    print("\n" + "="*60)
    print("测试统一LLM客户端")
    print("="*60)
    
    # 测试不同的provider
    providers = [
        ("deepseek", "deepseek-chat"),
        ("qwen", "qwen-plus"),
        ("siliconflow", "Qwen/Qwen2.5-7B-Instruct")
    ]
    
    for provider, model in providers:
        print(f"\n测试 {provider} - {model}...")
        try:
            client = create_llm_client(provider=provider, model=model, temperature=0.7)
            
            # 测试简单生成
            response = await client.generate(
                prompt="简单介绍一下Python编程语言，不超过50字",
                system_prompt="你是一个编程助手"
            )
            
            if response and not response.startswith("错误"):
                print(f"✅ {provider} 测试成功")
                print(f"   响应: {response[:100]}...")
            else:
                print(f"❌ {provider} 测试失败: {response}")
                
        except Exception as e:
            print(f"❌ {provider} 测试异常: {str(e)}")
            
        # 确保客户端关闭
        if hasattr(client, '_client') and client._client:
            await client._client.aclose()

async def test_agent_llm():
    """测试智能体LLM适配器"""
    print("\n" + "="*60)
    print("测试智能体LLM适配器")
    print("="*60)
    
    try:
        # 创建智能体LLM
        llm = create_agent_llm(provider="deepseek", temperature=0.3)
        
        # 测试消息格式调用
        messages = [
            {"role": "system", "content": "你是一个股票分析师"},
            {"role": "user", "content": "分析贵州茅台(600519)的投资价值，不超过100字"}
        ]
        
        response = await llm.ainvoke(messages)
        
        if response and hasattr(response, 'content'):
            print("✅ 智能体LLM测试成功")
            print(f"   响应: {response.content[:200]}...")
        else:
            print("❌ 智能体LLM测试失败")
            
    except Exception as e:
        print(f"❌ 智能体LLM测试异常: {str(e)}")

async def test_agent_api():
    """测试智能体API调用"""
    print("\n" + "="*60)
    print("测试智能体API调用")
    print("="*60)
    
    import httpx
    
    # 确保服务器运行
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. 测试获取智能体列表
        try:
            response = await client.get(f"{base_url}/api/agents/list")
            if response.status_code == 200:
                data = response.json()
                agent_count = data.get("count", 0)
                print(f"✅ 获取智能体列表成功: 共{agent_count}个智能体")
            else:
                print(f"❌ 获取智能体列表失败: {response.status_code}")
        except Exception as e:
            print(f"❌ 无法连接到服务器: {e}")
            print("   请确保后端服务器已启动: python backend/server.py")
            return
            
        # 2. 测试调用原系统智能体（使用/api/analyze）
        try:
            analyze_data = {
                "agent_id": "macro",
                "stock_code": "600519",
                "stock_data": {
                    "nowPri": "1800.00",
                    "increase": "2.5",
                    "traAmount": "1000000",
                    "traNumber": "500"
                }
            }
            
            response = await client.post(
                f"{base_url}/api/analyze",
                json=analyze_data
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print("✅ 原系统智能体调用成功（宏观政策分析师）")
                else:
                    print(f"❌ 原系统智能体调用失败: {result.get('error')}")
            else:
                print(f"❌ 原系统智能体调用失败: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 原系统智能体调用异常: {str(e)}")
            
        # 3. 测试统一智能体调用接口
        try:
            call_data = {
                "agent_id": "news_analyst",
                "stock_code": "600519",
                "params": {
                    "trade_date": "2024-12-03",
                    "provider": "deepseek",
                    "model": "deepseek-chat"
                },
                "context": {
                    "session_id": "test_session"
                }
            }
            
            response = await client.post(
                f"{base_url}/api/agents/call",
                json=call_data
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print("✅ 新系统智能体调用成功（新闻舆情分析师）")
                else:
                    print(f"⚠️ 新系统智能体调用返回: {result}")
            else:
                print(f"⚠️ 新系统智能体调用状态: {response.status_code}")
                print(f"   响应: {response.text[:200]}")
                
        except Exception as e:
            print(f"⚠️ 新系统智能体调用异常: {str(e)}")
            print("   注：这可能是因为智能体模块依赖未完全配置")

async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("🚀 开始测试LLM集成")
    print("="*60)
    
    # 1. 测试LLM客户端
    await test_unified_client()
    
    # 2. 测试智能体LLM适配器
    await test_agent_llm()
    
    # 3. 测试智能体API
    await test_agent_api()
    
    print("\n" + "="*60)
    print("✅ LLM集成测试完成")
    print("="*60)
    
    print("\n建议：")
    print("1. 确保.env文件中配置了必要的API Keys")
    print("2. 如果某些provider失败，检查对应的API Key是否配置")
    print("3. 新系统智能体可能需要额外的依赖配置")

if __name__ == "__main__":
    asyncio.run(main())
