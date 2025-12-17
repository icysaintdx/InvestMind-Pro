#!/usr/bin/env python3
"""
断路器模式实现
用于保护数据源调用，防止级联故障
"""

import time
from enum import Enum
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass, field
from threading import Lock

from backend.utils.logging_config import get_logger
logger = get_logger("circuit_breaker")


class CircuitState(Enum):
    """断路器状态"""
    CLOSED = "closed"      # 正常状态，允许请求
    OPEN = "open"          # 熔断状态，拒绝请求
    HALF_OPEN = "half_open"  # 半开状态，允许少量请求测试


@dataclass
class CircuitBreakerConfig:
    """断路器配置"""
    failure_threshold: int = 5          # 失败次数阈值
    success_threshold: int = 3          # 半开状态成功次数阈值
    timeout: float = 60.0               # 熔断超时时间（秒）
    half_open_max_calls: int = 3        # 半开状态最大允许调用数


@dataclass
class CircuitBreakerStats:
    """断路器统计信息"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    state_changes: int = 0


class CircuitBreaker:
    """
    断路器实现

    使用方法:
        breaker = CircuitBreaker("akshare")

        if breaker.can_execute():
            try:
                result = call_akshare_api()
                breaker.record_success()
                return result
            except Exception as e:
                breaker.record_failure()
                raise
        else:
            # 断路器打开，使用备用数据源
            return fallback_result
    """

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.stats = CircuitBreakerStats()
        self._lock = Lock()
        self._last_state_change_time = time.time()
        self._half_open_calls = 0

    def can_execute(self) -> bool:
        """检查是否可以执行请求"""
        with self._lock:
            self._check_state_transition()

            if self.state == CircuitState.CLOSED:
                return True
            elif self.state == CircuitState.OPEN:
                return False
            else:  # HALF_OPEN
                if self._half_open_calls < self.config.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
                return False

    def record_success(self):
        """记录成功调用"""
        with self._lock:
            self.stats.total_calls += 1
            self.stats.successful_calls += 1
            self.stats.consecutive_successes += 1
            self.stats.consecutive_failures = 0
            self.stats.last_success_time = time.time()

            if self.state == CircuitState.HALF_OPEN:
                if self.stats.consecutive_successes >= self.config.success_threshold:
                    self._transition_to(CircuitState.CLOSED)
                    logger.info(f"[断路器] {self.name}: 恢复正常 (HALF_OPEN -> CLOSED)")

    def record_failure(self):
        """记录失败调用"""
        with self._lock:
            self.stats.total_calls += 1
            self.stats.failed_calls += 1
            self.stats.consecutive_failures += 1
            self.stats.consecutive_successes = 0
            self.stats.last_failure_time = time.time()

            if self.state == CircuitState.CLOSED:
                if self.stats.consecutive_failures >= self.config.failure_threshold:
                    self._transition_to(CircuitState.OPEN)
                    logger.warning(f"[断路器] {self.name}: 熔断触发 (CLOSED -> OPEN), 连续失败 {self.stats.consecutive_failures} 次")
            elif self.state == CircuitState.HALF_OPEN:
                self._transition_to(CircuitState.OPEN)
                logger.warning(f"[断路器] {self.name}: 测试失败，重新熔断 (HALF_OPEN -> OPEN)")

    def _check_state_transition(self):
        """检查是否需要状态转换"""
        if self.state == CircuitState.OPEN:
            elapsed = time.time() - self._last_state_change_time
            if elapsed >= self.config.timeout:
                self._transition_to(CircuitState.HALF_OPEN)
                logger.info(f"[断路器] {self.name}: 超时恢复测试 (OPEN -> HALF_OPEN)")

    def _transition_to(self, new_state: CircuitState):
        """状态转换"""
        self.state = new_state
        self._last_state_change_time = time.time()
        self.stats.state_changes += 1

        if new_state == CircuitState.HALF_OPEN:
            self._half_open_calls = 0
            self.stats.consecutive_successes = 0
        elif new_state == CircuitState.CLOSED:
            self.stats.consecutive_failures = 0

    def reset(self):
        """重置断路器"""
        with self._lock:
            self.state = CircuitState.CLOSED
            self.stats = CircuitBreakerStats()
            self._last_state_change_time = time.time()
            self._half_open_calls = 0
            logger.info(f"[断路器] {self.name}: 已重置")

    def get_status(self) -> Dict[str, Any]:
        """获取断路器状态"""
        with self._lock:
            return {
                "name": self.name,
                "state": self.state.value,
                "stats": {
                    "total_calls": self.stats.total_calls,
                    "successful_calls": self.stats.successful_calls,
                    "failed_calls": self.stats.failed_calls,
                    "consecutive_failures": self.stats.consecutive_failures,
                    "consecutive_successes": self.stats.consecutive_successes,
                    "success_rate": (
                        self.stats.successful_calls / self.stats.total_calls * 100
                        if self.stats.total_calls > 0 else 0
                    ),
                    "state_changes": self.stats.state_changes
                },
                "config": {
                    "failure_threshold": self.config.failure_threshold,
                    "success_threshold": self.config.success_threshold,
                    "timeout": self.config.timeout
                }
            }


class CircuitBreakerRegistry:
    """断路器注册表，管理所有数据源的断路器"""

    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._breakers: Dict[str, CircuitBreaker] = {}
                    cls._instance._registry_lock = Lock()
        return cls._instance

    def get_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """获取或创建断路器"""
        with self._registry_lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(name, config)
                logger.debug(f"[断路器注册表] 创建断路器: {name}")
            return self._breakers[name]

    def get_all_status(self) -> Dict[str, Dict]:
        """获取所有断路器状态"""
        with self._registry_lock:
            return {name: breaker.get_status() for name, breaker in self._breakers.items()}

    def reset_all(self):
        """重置所有断路器"""
        with self._registry_lock:
            for breaker in self._breakers.values():
                breaker.reset()
            logger.info("[断路器注册表] 已重置所有断路器")


# 全局断路器注册表
circuit_breaker_registry = CircuitBreakerRegistry()


def get_circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
    """获取断路器的便捷函数"""
    return circuit_breaker_registry.get_breaker(name, config)


# 预定义的数据源断路器配置
DATA_SOURCE_BREAKER_CONFIGS = {
    "akshare": CircuitBreakerConfig(
        failure_threshold=3,
        success_threshold=2,
        timeout=30.0,
        half_open_max_calls=2
    ),
    "tushare": CircuitBreakerConfig(
        failure_threshold=5,
        success_threshold=3,
        timeout=60.0,
        half_open_max_calls=3
    ),
    "sina": CircuitBreakerConfig(
        failure_threshold=3,
        success_threshold=2,
        timeout=30.0,
        half_open_max_calls=2
    ),
    "juhe": CircuitBreakerConfig(
        failure_threshold=5,
        success_threshold=3,
        timeout=120.0,  # 付费API，更长的恢复时间
        half_open_max_calls=1
    ),
    "baostock": CircuitBreakerConfig(
        failure_threshold=5,
        success_threshold=3,
        timeout=60.0,
        half_open_max_calls=3
    )
}


def get_data_source_breaker(source_name: str) -> CircuitBreaker:
    """获取数据源专用断路器"""
    config = DATA_SOURCE_BREAKER_CONFIGS.get(source_name.lower())
    return get_circuit_breaker(f"datasource_{source_name}", config)
