"""
熔断降级机制
实现Provider级别的熔断、降级和健康监控
"""

import time
import asyncio
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from collections import deque

from backend.utils.logging_config import get_logger
from .models import MarketType, Symbol, DataPriority

logger = get_logger("dataflows.unified.circuit")


class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = "closed"          # 正常（关闭）
    OPEN = "open"              # 熔断（开启）
    HALF_OPEN = "half_open"    # 半开（试探）


@dataclass
class ProviderHealth:
    """Provider健康状态"""
    provider_name: str
    state: CircuitState = CircuitState.CLOSED
    success_rate: float = 1.0
    avg_latency: float = 0.0
    last_failure: Optional[float] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    total_requests: int = 0
    total_successes: int = 0
    total_failures: int = 0
    latency_history: deque = field(default_factory=lambda: deque(maxlen=100))
    
    def record_latency(self, latency: float):
        """记录延迟"""
        self.latency_history.append(latency)
        self.avg_latency = sum(self.latency_history) / len(self.latency_history)
    
    @property
    def is_healthy(self) -> bool:
        """是否健康"""
        return self.state == CircuitState.CLOSED and self.success_rate > 0.5


class CircuitBreaker:
    """
    熔断器
    
    状态流转：
    CLOSED --(连续失败)--> OPEN --(超时)--> HALF_OPEN --(成功)--> CLOSED
                                           --(失败)--> OPEN
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,       # 连续失败阈值
        recovery_timeout: int = 30,        # 恢复时间（秒）
        success_threshold: int = 3,        # 半开成功阈值
        half_open_max_calls: int = 3       # 半开最大试探次数
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.half_open_max_calls = half_open_max_calls
        
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.successes = 0
        self.half_open_calls = 0
        self.last_failure_time: Optional[float] = None
        self._lock = asyncio.Lock()
    
    async def can_execute(self) -> bool:
        """判断是否可执行请求"""
        async with self._lock:
            if self.state == CircuitState.CLOSED:
                return True
            
            elif self.state == CircuitState.OPEN:
                # 检查是否超过恢复时间
                if self.last_failure_time and \
                   time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.successes = 0
                    self.half_open_calls = 0
                    logger.info(f"[{self.name}] 熔断器进入半开状态")
                    return True
                return False
            
            else:  # HALF_OPEN
                if self.half_open_calls < self.half_open_max_calls:
                    self.half_open_calls += 1
                    return True
                return False
    
    async def record_success(self):
        """记录成功"""
        async with self._lock:
            self.failures = 0
            
            if self.state == CircuitState.HALF_OPEN:
                self.successes += 1
                if self.successes >= self.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.successes = 0
                    self.half_open_calls = 0
                    logger.info(f"[{self.name}] 熔断器关闭，恢复正常")
    
    async def record_failure(self):
        """记录失败"""
        async with self._lock:
            self.failures += 1
            self.last_failure_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN:
                # 半开状态失败，立即熔断
                self.state = CircuitState.OPEN
                logger.warning(f"[{self.name}] 半开状态失败，重新熔断")
            
            elif self.failures >= self.failure_threshold:
                # 达到阈值，开启熔断
                if self.state != CircuitState.OPEN:
                    self.state = CircuitState.OPEN
                    logger.warning(f"[{self.name}] 连续失败{self.failures}次，熔断器开启")
    
    def get_state(self) -> CircuitState:
        """获取当前状态"""
        return self.state


class ProviderManager:
    """
    Provider管理器
    
    管理多个数据源的熔断、降级和优先级调度
    """
    
    # 各市场Provider优先级链
    PROVIDER_CHAINS = {
        MarketType.A_SHARE: {
            DataPriority.REALTIME: ["tdx", "akshare", "tushare"],
            DataPriority.FAST: ["akshare", "tdx", "tushare"],
            DataPriority.NORMAL: ["tushare", "akshare", "baostock"],
            DataPriority.BACKUP: ["baostock", "akshare"],
        },
        MarketType.HK_SHARE: {
            DataPriority.FAST: ["hkex", "akshare"],
            DataPriority.NORMAL: ["akshare", "hkex"],
        },
        MarketType.US_SHARE: {
            DataPriority.FAST: ["finnhub", "yfinance"],
            DataPriority.NORMAL: ["yfinance", "finnhub"],
        },
        MarketType.CRYPTO: {
            DataPriority.FAST: ["binance", "okx"],
            DataPriority.NORMAL: ["okx", "binance"],
        },
    }
    
    def __init__(self):
        self.providers: Dict[str, Any] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.health_status: Dict[str, ProviderHealth] = {}
        self._lock = asyncio.Lock()
    
    def register_provider(self, name: str, provider: Any):
        """注册Provider"""
        self.providers[name] = provider
        self.circuit_breakers[name] = CircuitBreaker(name)
        self.health_status[name] = ProviderHealth(name)
        logger.info(f"[ProviderManager] 注册Provider: {name}")
    
    def _get_provider_chain(
        self,
        market: MarketType,
        priority: DataPriority
    ) -> List[str]:
        """获取Provider优先级链"""
        market_chains = self.PROVIDER_CHAINS.get(market, {})
        return market_chains.get(priority, market_chains.get(DataPriority.NORMAL, []))
    
    async def execute_with_fallback(
        self,
        operation: str,
        symbol: Symbol,
        priority: DataPriority = DataPriority.FAST,
        **kwargs
    ) -> Optional[Any]:
        """
        带降级的执行
        
        按优先级链尝试执行，自动跳过熔断的Provider
        """
        provider_chain = self._get_provider_chain(symbol.market, priority)
        
        if not provider_chain:
            logger.error(f"[ProviderManager] 未找到{symbol.market}的Provider链")
            return None
        
        last_error = None
        
        for provider_name in provider_chain:
            breaker = self.circuit_breakers.get(provider_name)
            health = self.health_status.get(provider_name)
            provider = self.providers.get(provider_name)
            
            if not provider:
                continue
            
            # 检查熔断器
            if breaker and not await breaker.can_execute():
                logger.debug(f"[{provider_name}] 熔断器开启，跳过")
                continue
            
            try:
                start_time = time.time()
                
                # 执行操作
                method = getattr(provider, operation, None)
                if not method:
                    logger.warning(f"[{provider_name}] 不支持操作: {operation}")
                    continue
                
                # 调用Provider方法
                if asyncio.iscoroutinefunction(method):
                    result = await asyncio.wait_for(
                        method(symbol, **kwargs),
                        timeout=10
                    )
                else:
                    result = await asyncio.wait_for(
                        asyncio.to_thread(method, symbol, **kwargs),
                        timeout=10
                    )
                
                latency = time.time() - start_time
                
                # 记录成功
                if breaker:
                    await breaker.record_success()
                if health:
                    health.consecutive_failures = 0
                    health.consecutive_successes += 1
                    health.total_requests += 1
                    health.total_successes += 1
                    health.record_latency(latency)
                
                logger.debug(f"[{provider_name}] 执行成功，延迟: {latency:.3f}s")
                return result
                
            except Exception as e:
                logger.error(f"[{provider_name}] 执行失败: {e}")
                last_error = e
                
                # 记录失败
                if breaker:
                    await breaker.record_failure()
                if health:
                    health.consecutive_failures += 1
                    health.consecutive_successes = 0
                    health.total_requests += 1
                    health.total_failures += 1
                    health.last_failure = time.time()
        
        # 所有Provider都失败
        logger.error(f"[ProviderManager] 所有Provider都失败，最后错误: {last_error}")
        return None
    
    async def execute_with_fallback_no_symbol(
        self,
        operation: str,
        market: MarketType,
        priority: DataPriority = DataPriority.FAST,
        **kwargs
    ) -> Optional[Any]:
        """
        带降级的执行（不需要symbol参数的方法）
        
        按优先级链尝试执行，自动跳过熔断的Provider
        """
        provider_chain = self._get_provider_chain(market, priority)
        
        if not provider_chain:
            logger.error(f"[ProviderManager] 未找到{market}的Provider链")
            return None
        
        last_error = None
        
        for provider_name in provider_chain:
            breaker = self.circuit_breakers.get(provider_name)
            health = self.health_status.get(provider_name)
            provider = self.providers.get(provider_name)
            
            if not provider:
                continue
            
            # 检查熔断器
            if breaker and not await breaker.can_execute():
                logger.debug(f"[{provider_name}] 熔断器开启，跳过")
                continue
            
            try:
                start_time = time.time()
                
                # 执行操作
                method = getattr(provider, operation, None)
                if not method:
                    logger.warning(f"[{provider_name}] 不支持操作: {operation}")
                    continue
                
                # 调用Provider方法（不传递symbol）
                if asyncio.iscoroutinefunction(method):
                    result = await asyncio.wait_for(
                        method(**kwargs),
                        timeout=10
                    )
                else:
                    result = await asyncio.wait_for(
                        asyncio.to_thread(method, **kwargs),
                        timeout=10
                    )
                
                latency = time.time() - start_time
                
                # 记录成功
                if breaker:
                    await breaker.record_success()
                if health:
                    health.consecutive_failures = 0
                    health.consecutive_successes += 1
                    health.total_requests += 1
                    health.total_successes += 1
                    health.record_latency(latency)
                
                logger.debug(f"[{provider_name}] 执行成功，延迟: {latency:.3f}s")
                return result
                
            except Exception as e:
                logger.error(f"[{provider_name}] 执行失败: {e}")
                last_error = e
                
                # 记录失败
                if breaker:
                    await breaker.record_failure()
                if health:
                    health.consecutive_failures += 1
                    health.consecutive_successes = 0
                    health.total_requests += 1
                    health.total_failures += 1
                    health.last_failure = time.time()
        
        # 所有Provider都失败
        logger.error(f"[ProviderManager] 所有Provider都失败，最后错误: {last_error}")
        return None
    
    def get_health_report(self) -> Dict[str, Dict]:
        """获取健康报告"""
        report = {}
        for name, health in self.health_status.items():
            breaker = self.circuit_breakers.get(name)
            report[name] = {
                "state": health.state.value,
                "circuit_state": breaker.get_state().value if breaker else "unknown",
                "success_rate": health.success_rate,
                "avg_latency_ms": round(health.avg_latency * 1000, 2),
                "total_requests": health.total_requests,
                "total_successes": health.total_successes,
                "total_failures": health.total_failures,
                "is_healthy": health.is_healthy,
            }
        return report
    
    def reset_circuit(self, provider_name: str):
        """手动重置熔断器"""
        breaker = self.circuit_breakers.get(provider_name)
        if breaker:
            breaker.state = CircuitState.CLOSED
            breaker.failures = 0
            breaker.successes = 0
            logger.info(f"[{provider_name}] 熔断器手动重置")


# 全局实例
provider_manager = ProviderManager()
