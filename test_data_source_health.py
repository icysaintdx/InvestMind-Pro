#!/usr/bin/env python3
"""
数据源健康检查测试脚本
"""

import asyncio
import sys
import os

# 设置环境变量避免编码问题
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.path.insert(0, '.')

async def test_health_checks():
    """测试各数据源健康检查"""
    print("=" * 60)
    print("数据源健康检查测试")
    print("=" * 60)

    from backend.api.data_source_health_api import (
        check_akshare_health,
        check_sina_health,
        check_tushare_health,
        check_baostock_health,
        check_juhe_health
    )

    checks = [
        ("AKShare", check_akshare_health),
        ("新浪财经", check_sina_health),
        ("Tushare", check_tushare_health),
        ("BaoStock", check_baostock_health),
        ("聚合数据", check_juhe_health),
    ]

    results = []
    for name, check_func in checks:
        print(f"\n检查 {name}...")
        try:
            result = await check_func()
            status = "[OK] 可用" if result.get("available") else "[FAIL] 不可用"
            time_ms = result.get("response_time_ms", 0)
            error = result.get("error", "")
            print(f"  {status} - 响应时间: {time_ms:.2f}ms")
            if error:
                print(f"  错误: {error[:100]}")
            results.append(result)
        except Exception as e:
            print(f"  [FAIL] 检查失败: {e}")
            results.append({"name": name, "available": False, "error": str(e)})

    # 汇总
    print("\n" + "=" * 60)
    print("汇总")
    print("=" * 60)
    available = sum(1 for r in results if r.get("available"))
    total = len(results)
    print(f"可用数据源: {available}/{total}")

    return results


def test_circuit_breaker():
    """测试断路器功能"""
    print("\n" + "=" * 60)
    print("断路器测试")
    print("=" * 60)

    from backend.dataflows.utils.circuit_breaker import (
        CircuitBreaker,
        CircuitBreakerConfig,
        CircuitState
    )

    # 创建测试断路器
    config = CircuitBreakerConfig(
        failure_threshold=3,
        success_threshold=2,
        timeout=5.0
    )
    breaker = CircuitBreaker("test_source", config)

    print(f"\n初始状态: {breaker.state.value}")
    assert breaker.state == CircuitState.CLOSED

    # 模拟连续失败
    print("\n模拟3次连续失败...")
    for i in range(3):
        breaker.record_failure()
        print(f"  失败 {i+1}: 状态={breaker.state.value}, 连续失败={breaker.stats.consecutive_failures}")

    assert breaker.state == CircuitState.OPEN
    print(f"\n断路器已熔断: {breaker.state.value}")

    # 检查是否可以执行
    can_exec = breaker.can_execute()
    print(f"can_execute(): {can_exec}")
    assert not can_exec

    # 重置并测试成功路径
    breaker.reset()
    print(f"\n重置后状态: {breaker.state.value}")

    # 模拟成功
    print("\n模拟成功调用...")
    breaker.record_success()
    print(f"  成功: 状态={breaker.state.value}, 连续成功={breaker.stats.consecutive_successes}")

    print("\n[OK] 断路器测试通过!")


def test_data_source_manager_with_breaker():
    """测试数据源管理器的断路器集成"""
    print("\n" + "=" * 60)
    print("数据源管理器断路器集成测试")
    print("=" * 60)

    from backend.dataflows.data_source_manager import DataSourceManager, ChinaDataSource

    manager = DataSourceManager()

    # 检查断路器是否初始化
    print(f"\n断路器数量: {len(manager._breakers)}")
    assert len(manager._breakers) > 0

    # 检查各数据源断路器状态
    for source, breaker in manager._breakers.items():
        status = breaker.get_status()
        print(f"  {source.value}: {status['state']}")

    # 测试 _can_use_source
    can_use = manager._can_use_source(ChinaDataSource.AKSHARE)
    print(f"\nAKShare可用: {can_use}")
    assert can_use

    print("\n[OK] 数据源管理器断路器集成测试通过!")


if __name__ == "__main__":
    # 测试断路器
    test_circuit_breaker()

    # 测试数据源管理器集成
    test_data_source_manager_with_breaker()

    # 测试健康检查
    asyncio.run(test_health_checks())

    print("\n" + "=" * 60)
    print("所有测试完成!")
    print("=" * 60)
