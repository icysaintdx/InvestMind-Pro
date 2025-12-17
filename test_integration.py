"""
测试降级集成
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置环境变量
os.environ["USE_FALLBACK"] = "true"

async def test_server_integration():
    """测试 server.py 中的集成"""
    print("=" * 60)
    print("测试降级集成")
    print("=" * 60)
    
    try:
        # 导入server模块
        from backend.server import SiliconFlowRequest, analyze_stock, AnalyzeRequest
        print("✅ 成功导入 server 模块")
        
        # 测试1: 检查 SiliconFlowRequest 是否有 agentRole
        req = SiliconFlowRequest(
            model="test",
            systemPrompt="test",
            prompt="test",
            agentRole="NEWS"
        )
        print(f"✅ SiliconFlowRequest.agentRole = {req.agentRole}")
        
        # 测试2: 创建分析请求
        analyze_req = AnalyzeRequest(
            agent_id="news_analyst",
            stock_code="600519",
            stock_data={"price": 2000, "change": 1.5},
            previous_outputs={}
        )
        print(f"✅ 创建分析请求: {analyze_req.agent_id}")
        
        # 测试3: 检查降级处理器
        from backend.utils.llm_fallback_handler import get_fallback_handler
        handler = get_fallback_handler()
        print("✅ 降级处理器正常工作")
        
        # 测试4: 测试默认响应
        default_response = handler._get_default_response("NEWS", "测试错误")
        text = default_response['choices'][0]['message']['content']
        print(f"✅ NEWS 默认响应: {text[:50]}...")
        
        print("\n" + "=" * 60)
        print("✅ 所有集成测试通过！")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_server_integration())
