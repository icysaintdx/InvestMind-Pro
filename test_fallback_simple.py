"""
简单测试降级处理器
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test():
    try:
        from backend.utils.llm_fallback_handler import get_fallback_handler
        print("✅ 成功导入降级处理器")
        
        handler = get_fallback_handler()
        print("✅ 成功创建处理器实例")
        
        # 测试默认响应
        result = handler._get_default_response("RISK", "测试错误")
        print(f"✅ 默认响应: {result['choices'][0]['message']['content'][:50]}...")
        
        print("\n测试成功！降级处理器已正确集成。")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
