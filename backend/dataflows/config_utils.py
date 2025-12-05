#!/usr/bin/env python3
"""
配置工具
提供配置读取和管理功能
"""

import os
from pathlib import Path
from typing import Any, Optional

# 加载环境变量
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass


def get_config(key: str, default: Any = None) -> Any:
    """
    获取配置值
    
    Args:
        key: 配置键名
        default: 默认值
        
    Returns:
        配置值
    """
    return os.getenv(key, default)


def get_api_key(service: str) -> Optional[str]:
    """
    获取 API Key
    
    Args:
        service: 服务名称（如 'FINNHUB', 'NEWSAPI' 等）
        
    Returns:
        API Key 或 None
    """
    key_name = f"{service.upper()}_API_KEY"
    return os.getenv(key_name)


def get_timeout(default: int = 30) -> int:
    """
    获取超时配置
    
    Args:
        default: 默认超时时间（秒）
        
    Returns:
        超时时间
    """
    timeout = os.getenv('REQUEST_TIMEOUT', str(default))
    try:
        return int(timeout)
    except ValueError:
        return default


def get_max_retries(default: int = 3) -> int:
    """
    获取最大重试次数
    
    Args:
        default: 默认重试次数
        
    Returns:
        重试次数
    """
    retries = os.getenv('MAX_RETRIES', str(default))
    try:
        return int(retries)
    except ValueError:
        return default


def is_debug_mode() -> bool:
    """
    是否为调试模式
    
    Returns:
        True 如果是调试模式
    """
    return os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')


def get_int(*keys, default: int = 0) -> int:
    """
    获取整数配置值，支持多个键名（优先级从高到低）
    
    Args:
        *keys: 一个或多个配置键名，按优先级顺序尝试
        default: 默认值
        
    Returns:
        整数配置值
        
    Examples:
        get_int("MAX_RETRIES", default=3)
        get_int("TA_MAX_RETRIES", "max_retries", default=3)
    """
    # 如果最后一个参数是数字，则作为默认值
    if keys and isinstance(keys[-1], (int, float)):
        keys = keys[:-1]
        default = int(keys[-1]) if keys else default
    
    # 按优先级尝试每个键
    for key in keys:
        value = os.getenv(key)
        if value is not None:
            try:
                return int(value)
            except ValueError:
                continue
    
    return default


def get_float(*keys, default: float = 0.0) -> float:
    """
    获取浮点数配置值，支持多个键名（优先级从高到低）
    
    Args:
        *keys: 一个或多个配置键名，按优先级顺序尝试
        default: 默认值
        
    Returns:
        浮点数配置值
        
    Examples:
        get_float("TIMEOUT", default=30.0)
        get_float("TA_TIMEOUT", "timeout", default=30.0)
        get_float("TA_GOOGLE_NEWS_SLEEP_MIN_SECONDS", "ta_google_news_sleep_min_seconds", 2.0)
    """
    # 如果最后一个参数是数字，则作为默认值
    if keys and isinstance(keys[-1], (int, float)):
        default = float(keys[-1])
        keys = keys[:-1]
    
    # 按优先级尝试每个键
    for key in keys:
        value = os.getenv(key)
        if value is not None:
            try:
                return float(value)
            except ValueError:
                continue
    
    return default
