"""
深入监控 httpx 连接池内部状态
查看连接是否真的被占满导致死锁
"""
import asyncio
import httpx
import time
import threading
from datetime import datetime

# API配置
SILICONFLOW_API_KEY = "sk-gdunxgtyhqokufmvnzjgsxsrqvfrxicigzslhzjrwlwejtyv"
API_URL = "https://api.siliconflow.cn/v1/chat/completions"

class ConnectionPoolMonitor:
    """连接池监控器"""
    
    def __init__(self, client: httpx.AsyncClient, name: str):
        self.client = client
        self.name = name
        self.monitoring = False
        self.stats = {
            "max_connections_seen": 0,
            "max_waiters_seen": 0,
            "timeouts": 0,
            "successes": 0,
            "failures": 0
        }
    
    async def start_monitoring(self):
        """开始监控"""
        self.monitoring = True
        while self.monitoring:
            try:
                # 尝试获取连接池信息
                transport = getattr(self.client, '_transport', None)
                if transport:
                    pool = getattr(transport, '_pool', None)
                    if pool:
                        # 获取连接信息
                        connections = len(getattr(pool, '_connections', []))
                        waiters = len(getattr(pool, '_waiters', []))
                        
                        # 更新最大值
                        self.stats["max_connections_seen"] = max(
                            self.stats["max_connections_seen"], connections
                        )
                        self.stats["max_waiters_seen"] = max(
                            self.stats["max_waiters_seen"], waiters
                        )
                        
                        # 打印当前状态
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        print(f"[{timestamp}] {self.name} - "
                              f"连接: {connections}, "
                              f"等待: {waiters}")
                        
                        # 如果有等待的连接，说明可能出现瓶颈
                        if waiters > 0:
                            print(f"  ⚠️ 警告: 有 {waiters} 个请求在等待连接!")
            except Exception as e:
                pass
            
            await asyncio.sleep(1)
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
    
    def print_summary(self):
        """打印统计摘要"""
        print(f"\n{self.name} 统计摘要:")
        print(f"  最大并发连接: {self.stats['max_connections_seen']}")
        print(f"  最大等待队列: {self.stats['max_waiters_seen']}")
        print(f"  成功请求: {self.stats['successes']}")
        print(f"  失败请求: {self.stats['failures']}")
        print(f"  超时请求: {self.stats['timeouts']}")

async def make_request_with_monitoring(
    client: httpx.AsyncClient, 
    monitor: ConnectionPoolMonitor,
    request_id: str, 
    content_size: int
):
    """发送请求并监控"""
    prompt = "分析" + "X" * content_size
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SILICONFLOW_API_KEY}"
    }
    
    data = {
        "model": "Qwen/Qwen3-8B",
        "messages": [
            {"role": "system", "content": "你是助手"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 100,
        "stream": False
    }
    
    print(f"\n[{request_id}] 发起请求 ({content_size}字符)...")
    start_time = time.time()
    
    try:
        response = await client.post(
            API_URL, 
            headers=headers, 
            json=data,
            timeout=httpx.Timeout(30.0)  # 30秒超时用于测试
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            monitor.stats["successes"] += 1
            print(f"[{request_id}] ✅ 成功 ({elapsed:.2f}秒)")
            return True
        else:
            monitor.stats["failures"] += 1
            print(f"[{request_id}] ❌ 失败: HTTP {response.status_code} ({elapsed:.2f}秒)")
            return False
            
    except httpx.TimeoutException:
        elapsed = time.time() - start_time
        monitor.stats["timeouts"] += 1
        print(f"[{request_id}] ⏱️ 超时 ({elapsed:.2f}秒)")
        return False
    except Exception as e:
        elapsed = time.time() - start_time
        monitor.stats["failures"] += 1
        print(f"[{request_id}] ❌ 异常: {type(e).__name__} ({elapsed:.2f}秒)")
        return False

async def test_with_limited_connections():
    """测试有限连接数的情况"""
    print("="*60)
    print("测试1: 有限连接数（最大2个连接）")
    print("="*60)
    
    # 创建限制连接数的客户端
    client = httpx.AsyncClient(
        limits=httpx.Limits(
            max_connections=2,  # 只允许2个并发连接
            max_keepalive_connections=1
        ),
        timeout=httpx.Timeout(30.0)
    )
    
    monitor = ConnectionPoolMonitor(client, "限制客户端")
    monitor_task = asyncio.create_task(monitor.start_monitoring())
    
    # 同时发起5个请求（但只有2个连接可用）
    print("\n发起5个并发请求（但只有2个连接）...")
    tasks = []
    for i in range(5):
        task = make_request_with_monitoring(
            client, monitor, f"请求{i+1}", 1000
        )
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    
    monitor.stop_monitoring()
    await monitor_task
    monitor.print_summary()
    
    await client.aclose()

async def test_gradual_increase():
    """测试逐步增加并发"""
    print("\n" + "="*60)
    print("测试2: 逐步增加并发（模拟实际场景）")
    print("="*60)
    
    # 创建标准客户端
    client = httpx.AsyncClient(
        limits=httpx.Limits(
            max_connections=50,
            max_keepalive_connections=20
        ),
        timeout=httpx.Timeout(60.0)
    )
    
    monitor = ConnectionPoolMonitor(client, "标准客户端")
    monitor_task = asyncio.create_task(monitor.start_monitoring())
    
    # 第一阶段：2个请求
    print("\n阶段1: 2个并发请求")
    tasks = []
    for i in range(2):
        task = make_request_with_monitoring(
            client, monitor, f"阶段1-{i+1}", 2000
        )
        tasks.append(task)
    await asyncio.gather(*tasks)
    
    print("\n等待3秒...")
    await asyncio.sleep(3)
    
    # 第二阶段：3个请求（不等待第一阶段完成）
    print("\n阶段2: 3个并发请求（更大）")
    tasks = []
    for i in range(3):
        task = make_request_with_monitoring(
            client, monitor, f"阶段2-{i+1}", 4000
        )
        tasks.append(task)
    await asyncio.gather(*tasks)
    
    monitor.stop_monitoring()
    await monitor_task
    monitor.print_summary()
    
    await client.aclose()

async def test_connection_reuse():
    """测试连接复用问题"""
    print("\n" + "="*60)
    print("测试3: 连接复用问题")
    print("="*60)
    
    # 测试是否因为连接没有正确复用导致死锁
    client = httpx.AsyncClient(
        limits=httpx.Limits(
            max_connections=10,
            max_keepalive_connections=5,
            keepalive_expiry=5  # 5秒后关闭空闲连接
        ),
        timeout=httpx.Timeout(30.0)
    )
    
    monitor = ConnectionPoolMonitor(client, "复用测试")
    monitor_task = asyncio.create_task(monitor.start_monitoring())
    
    # 连续发送请求，看连接是否正确复用
    for batch in range(3):
        print(f"\n批次{batch+1}: 发送3个请求")
        tasks = []
        for i in range(3):
            task = make_request_with_monitoring(
                client, monitor, f"批次{batch+1}-{i+1}", 2000
            )
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        print(f"批次{batch+1}完成，等待2秒...")
        await asyncio.sleep(2)
    
    monitor.stop_monitoring()
    await monitor_task
    monitor.print_summary()
    
    await client.aclose()

async def main():
    """主测试函数"""
    print("httpx 连接池深度监控测试")
    print("="*60)
    
    # 依次运行各个测试
    await test_with_limited_connections()
    await asyncio.sleep(5)
    
    await test_gradual_increase()
    await asyncio.sleep(5)
    
    await test_connection_reuse()
    
    print("\n" + "="*60)
    print("所有测试完成！")

if __name__ == "__main__":
    asyncio.run(main())
