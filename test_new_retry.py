"""
测试新的重试机制
"""
import httpx
import asyncio
import time

API_KEY = "sk-gdunxgtyhqokufmvnzjgsxsrqvfrxicigzslhzjrwlwejtyv"
API_URL = "https://api.siliconflow.cn/v1/chat/completions"

async def test_single_request():
    """测试单个请求的超时和重试"""
    prompt = "简单测试：什么是Python？请用20字以内回答。"
    
    print("=" * 60)
    print(f"测试提示词长度: {len(prompt)} 字符")
    print("=" * 60)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    data = {
        "model": "Qwen/Qwen2.5-7B-Instruct",
        "messages": [
            {"role": "system", "content": "你是一个简洁的助手"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 100,
        "stream": False
    }
    
    max_retries = 3
    for attempt in range(max_retries):
        client = None
        try:
            print(f"\n尝试 {attempt+1}/{max_retries}")
            
            # 创建新客户端
            client = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    timeout=60.0,     # 总默认超时60秒
                    connect=15.0,     # 连接超时15秒
                    read=50.0,        # 读取超时50秒
                    write=15.0,       # 写入超时15秒
                    pool=10.0         # 连接池超时10秒
                )
            )
            
            # 发送请求
            start_time = time.time()
            print(f"发送请求...")
            
            response = await asyncio.wait_for(
                client.post(
                    API_URL,
                    headers=headers,
                    json=data
                ),
                timeout=30.0
            )
            
            elapsed = time.time() - start_time
            print(f"✅ 响应成功，耗时: {elapsed:.2f}秒")
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                print(f"回复: {content[:100]}...")
                return True
            else:
                print(f"❌ HTTP {response.status_code}")
                
        except asyncio.TimeoutError:
            print(f"❌ 总超时（30秒）")
        except httpx.ReadTimeout:
            print(f"❌ 读取超时（25秒）")
        except Exception as e:
            print(f"❌ 错误: {type(e).__name__}: {str(e)[:100]}")
        finally:
            if client:
                await client.aclose()
                
        if attempt < max_retries - 1:
            wait_time = 3 + (2 * attempt)
            print(f"等待 {wait_time} 秒后重试...")
            await asyncio.sleep(wait_time)
    
    print("\n所有重试都失败")
    return False

async def test_concurrent_requests():
    """测试并发请求"""
    print("\n" + "=" * 60)
    print("测试3个并发请求")
    print("=" * 60)
    
    tasks = [test_single_request() for _ in range(3)]
    results = await asyncio.gather(*tasks)
    
    success_count = sum(1 for r in results if r)
    print(f"\n结果: {success_count}/3 成功")
    
if __name__ == "__main__":
    print("测试新的重试机制")
    asyncio.run(test_single_request())
    # asyncio.run(test_concurrent_requests())
