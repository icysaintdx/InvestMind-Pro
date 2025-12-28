#!/usr/bin/env python3
"""
数据流工具模块
"""

from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerRegistry,
    CircuitState,
    get_circuit_breaker,
    get_data_source_breaker,
    circuit_breaker_registry
)

# 从 backend.utils.dataflow_utils 导入常用工具
try:
    from backend.utils.dataflow_utils import (
        save_output,
        SavePathType,
        decorate_all_methods,
        format_stock_data,
        validate_ticker,
        format_number,
        parse_date,
    )
except ImportError:
    # 如果导入失败，提供默认实现
    SavePathType = None
    
    def save_output(data, description=None, save_path=None):
        pass
    
    def decorate_all_methods(decorator):
        return lambda cls: cls
    
    def format_stock_data(data):
        return data
    
    def validate_ticker(ticker):
        return bool(ticker)
    
    def format_number(value, precision=2):
        return str(value)
    
    def parse_date(date_str):
        return date_str

__all__ = [
    # 熔断器相关
    'CircuitBreaker',
    'CircuitBreakerConfig',
    'CircuitBreakerRegistry',
    'CircuitState',
    'get_circuit_breaker',
    'get_data_source_breaker',
    'circuit_breaker_registry',
    # 数据流工具
    'save_output',
    'SavePathType',
    'decorate_all_methods',
    'format_stock_data',
    'validate_ticker',
    'format_number',
    'parse_date',
]
