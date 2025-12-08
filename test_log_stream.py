"""
测试实时日志流功能
"""
import asyncio
import httpx
from backend.examples.agent_with_log_stream import analyze_news_with_log_stream

async def test_sse_connection():
    """测试 SSE 连接"""
    print("=" * 60)
    print("测试 SSE 日志流连接")
    print("=" * 60)
    
    agent_id = "news_analyst"
    url = f"http://localhost:8000/api/agent-logs/stream/{agent_id}"
    
    print(f"\n连接到: {url}")
    print("等待日志消息...\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        async with client.stream("GET", url) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]  # 移除 "data: " 前缀
                    print(f"收到日志: {data}")


def test_log_push():
    """测试日志推送"""
    print("\n" + "=" * 60)
    print("测试日志推送")
    print("=" * 60)
    
    # 在另一个线程中运行智能体分析
    import threading
    
    def run_analysis():
        import time
        time.sleep(2)  # 等待 SSE 连接建立
        print("\n[后台] 开始运行智能体分析...")
        analyze_news_with_log_stream("603211", "news_analyst")
        print("[后台] 智能体分析完成")
    
    # 启动后台分析
    thread = threading.Thread(target=run_analysis)
    thread.start()
    
    # 运行 SSE 连接
    try:
        asyncio.run(test_sse_connection())
    except KeyboardInterrupt:
        print("\n\n测试中断")
    
    thread.join()


if __name__ == "__main__":
    print("=" * 60)
    print("实时日志流功能测试")
    print("=" * 60)
    print("\n请确保后端服务器正在运行 (python backend/server.py)")
    print("然后按 Enter 开始测试...")
    input()
    
    test_log_push()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
