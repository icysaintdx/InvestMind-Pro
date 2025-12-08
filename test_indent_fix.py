"""
测试缩进修复是否生效
"""
import asyncio
import httpx
import time
import json

async def test_api():
    """测试SiliconFlow API是否正常响应"""
    url = "http://localhost:8000/api/ai/siliconflow"
    
    data = {
        "model": "Qwen/Qwen3-8B",
        "systemPrompt": "你是一个测试助手",
        "prompt": "简单回答：1+1等于几？",
        "temperature": 0.1
    }
    
    print("发送测试请求...")
    start = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=data)
            elapsed = time.time() - start
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print(f"✅ 成功！耗时: {elapsed:.2f}秒")
                    print(f"响应: {result.get('text', '')[:100]}...")
                    print(f"Token使用: {result.get('usage', {})}")
                else:
                    print(f"❌ 失败: {result.get('error')}")
            else:
                print(f"❌ HTTP {response.status_code}")
                print(response.text)
                
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ 异常: {str(e)}, 耗时: {elapsed:.2f}秒")
        print("如果超时，说明缩进问题还未完全修复")

if __name__ == "__main__":
    print("=" * 60)
    print("测试SiliconFlow API缩进修复")
    print("=" * 60)
    print()
    asyncio.run(test_api())
