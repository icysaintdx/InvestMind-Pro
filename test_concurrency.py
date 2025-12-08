#!/usr/bin/env python3
"""
并发测试脚本 - 测试后端最大并发处理能力

测试场景:
1. 测试不同并发数下的响应时间
2. 找出最佳并发数
3. 验证超时和重试机制

使用方法:
python test_concurrency.py
"""

import asyncio
import aiohttp
import time
from datetime import datetime
import json
import sys

# 测试配置
BASE_URL = "http://localhost:8000"
STOCK_CODE = "600519"  # 贵州茅台
TEST_AGENT_ID = "technical"  # 使用技术分析师测试

# 测试用的请求数据
TEST_REQUEST = {
    "agent_id": TEST_AGENT_ID,
    "stock_code": STOCK_CODE,
    "stock_data": {
        "symbol": STOCK_CODE,
        "name": "贵州茅台",
        "price": 1500.0,
        "change_percent": 2.5
    },
    "previous_outputs": {},
    "custom_instruction": "请进行技术分析"
}

class ConcurrencyTester:
    def __init__(self):
        self.results = []
        
    async def single_request(self, session, request_id, timeout=120):
        """发起单个请求"""
        start_time = time.time()
        
        try:
            async with session.post(
                f"{BASE_URL}/api/analyze",
                json=TEST_REQUEST,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                elapsed = time.time() - start_time
                status = response.status
                
                if status == 200:
                    data = await response.json()
                    success = data.get('success', False)
                    return {
                        'request_id': request_id,
                        'status': 'success' if success else 'failed',
                        'http_status': status,
                        'elapsed': elapsed,
                        'error': None
                    }
                else:
                    return {
                        'request_id': request_id,
                        'status': 'failed',
                        'http_status': status,
                        'elapsed': elapsed,
                        'error': f'HTTP {status}'
                    }
                    
        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            return {
                'request_id': request_id,
                'status': 'timeout',
                'http_status': None,
                'elapsed': elapsed,
                'error': 'Timeout'
            }
        except Exception as e:
            elapsed = time.time() - start_time
            return {
                'request_id': request_id,
                'status': 'error',
                'http_status': None,
                'elapsed': elapsed,
                'error': str(e)
            }
    
    async def test_concurrent_requests(self, num_concurrent, timeout=120):
        """测试指定并发数"""
        print(f"\n{'='*60}")
        print(f"🚀 测试并发数: {num_concurrent}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.single_request(session, i+1, timeout)
                for i in range(num_concurrent)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_elapsed = time.time() - start_time
        
        # 统计结果
        success_count = sum(1 for r in results if isinstance(r, dict) and r['status'] == 'success')
        failed_count = sum(1 for r in results if isinstance(r, dict) and r['status'] == 'failed')
        timeout_count = sum(1 for r in results if isinstance(r, dict) and r['status'] == 'timeout')
        error_count = sum(1 for r in results if isinstance(r, dict) and r['status'] == 'error')
        
        # 计算平均响应时间（只统计成功的）
        success_times = [r['elapsed'] for r in results if isinstance(r, dict) and r['status'] == 'success']
        avg_time = sum(success_times) / len(success_times) if success_times else 0
        max_time = max(success_times) if success_times else 0
        min_time = min(success_times) if success_times else 0
        
        # 打印结果
        print(f"\n📊 测试结果:")
        print(f"  总请求数: {num_concurrent}")
        print(f"  总耗时: {total_elapsed:.2f}秒")
        print(f"  ✅ 成功: {success_count} ({success_count/num_concurrent*100:.1f}%)")
        print(f"  ❌ 失败: {failed_count}")
        print(f"  ⏱️  超时: {timeout_count}")
        print(f"  🔥 错误: {error_count}")
        
        if success_times:
            print(f"\n⏱️  响应时间统计:")
            print(f"  平均: {avg_time:.2f}秒")
            print(f"  最快: {min_time:.2f}秒")
            print(f"  最慢: {max_time:.2f}秒")
        
        # 计算吞吐量
        throughput = success_count / total_elapsed if total_elapsed > 0 else 0
        print(f"\n📈 吞吐量: {throughput:.2f} 请求/秒")
        
        # 详细结果
        print(f"\n📋 详细结果:")
        for r in results:
            if isinstance(r, dict):
                status_icon = {
                    'success': '✅',
                    'failed': '❌',
                    'timeout': '⏱️',
                    'error': '🔥'
                }.get(r['status'], '❓')
                
                print(f"  {status_icon} 请求#{r['request_id']}: {r['status']} - {r['elapsed']:.2f}秒")
                if r['error']:
                    print(f"     错误: {r['error']}")
        
        return {
            'concurrent': num_concurrent,
            'total_elapsed': total_elapsed,
            'success_count': success_count,
            'failed_count': failed_count,
            'timeout_count': timeout_count,
            'error_count': error_count,
            'avg_time': avg_time,
            'max_time': max_time,
            'min_time': min_time,
            'throughput': throughput,
            'success_rate': success_count / num_concurrent * 100
        }
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("="*60)
        print("🧪 AlphaCouncil 后端并发测试")
        print("="*60)
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"后端地址: {BASE_URL}")
        print(f"测试股票: {STOCK_CODE}")
        print(f"测试智能体: {TEST_AGENT_ID}")
        
        # 测试不同的并发数
        test_cases = [1, 2, 3, 4, 5, 6, 8, 10]
        
        all_results = []
        
        for concurrent in test_cases:
            result = await self.test_concurrent_requests(concurrent, timeout=120)
            all_results.append(result)
            
            # 等待一段时间，让后端恢复
            if concurrent < test_cases[-1]:
                print(f"\n⏸️  等待5秒后继续下一个测试...")
                await asyncio.sleep(5)
        
        # 生成总结报告
        self.print_summary(all_results)
        
        # 保存结果到文件
        self.save_results(all_results)
    
    def print_summary(self, results):
        """打印总结报告"""
        print("\n" + "="*60)
        print("📊 测试总结")
        print("="*60)
        
        print(f"\n{'并发数':<8} {'成功率':<10} {'平均耗时':<12} {'吞吐量':<12} {'推荐':<6}")
        print("-" * 60)
        
        best_concurrent = None
        best_throughput = 0
        
        for r in results:
            recommend = ""
            if r['success_rate'] == 100 and r['throughput'] > best_throughput:
                best_throughput = r['throughput']
                best_concurrent = r['concurrent']
                recommend = "✅ 推荐"
            elif r['success_rate'] < 80:
                recommend = "❌ 不推荐"
            
            print(f"{r['concurrent']:<8} {r['success_rate']:<10.1f}% {r['avg_time']:<12.2f}s {r['throughput']:<12.2f}/s {recommend}")
        
        print("\n" + "="*60)
        print(f"🎯 推荐并发数: {best_concurrent}")
        print(f"   理由: 成功率100%，吞吐量最高({best_throughput:.2f}请求/秒)")
        print("="*60)
    
    def save_results(self, results):
        """保存结果到JSON文件"""
        filename = f"concurrency_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'test_time': datetime.now().isoformat(),
                'base_url': BASE_URL,
                'stock_code': STOCK_CODE,
                'agent_id': TEST_AGENT_ID,
                'results': results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 结果已保存到: {filename}")

async def main():
    """主函数"""
    tester = ConcurrencyTester()
    
    try:
        await tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    # 检查Python版本
    if sys.version_info < (3, 7):
        print("❌ 需要Python 3.7或更高版本")
        sys.exit(1)
    
    # 运行测试
    asyncio.run(main())
