"""
配置工具函数
用于从环境变量获取配置值
"""

import os
from typing import Optional

def get_float(env_name: str, alt_name: str, default: float) -> float:
    """
    获取浮点数配置值，优先从环境变量读取
    
    Args:
        env_name: 主环境变量名
        alt_name: 备用环境变量名（会自动转为大写）
        default: 默认值
    
    Returns:
        浮点数配置值
    """
    value = os.environ.get(env_name) or os.environ.get(alt_name.upper())
    if value:
        try:
            return float(value)
        except (ValueError, TypeError):
            pass
    return default

def get_int(env_name: str, alt_name: str, default: int) -> int:
    """
    获取整数配置值，优先从环境变量读取
    
    Args:
        env_name: 主环境变量名
        alt_name: 备用环境变量名（会自动转为大写）
        default: 默认值
    
    Returns:
        整数配置值
    """
    value = os.environ.get(env_name) or os.environ.get(alt_name.upper())
    if value:
        try:
            return int(value)
        except (ValueError, TypeError):
            pass
    return default

def get_str(env_name: str, alt_name: str, default: str = "") -> str:
    """
    获取字符串配置值，优先从环境变量读取
    
    Args:
        env_name: 主环境变量名
        alt_name: 备用环境变量名（会自动转为大写）
        default: 默认值
    
    Returns:
        字符串配置值
    """
    return os.environ.get(env_name) or os.environ.get(alt_name.upper()) or default

def get_bool(env_name: str, alt_name: str, default: bool = False) -> bool:
    """
    获取布尔配置值，优先从环境变量读取
    
    Args:
        env_name: 主环境变量名
        alt_name: 备用环境变量名（会自动转为大写）
        default: 默认值
    
    Returns:
        布尔配置值
    """
    value = os.environ.get(env_name) or os.environ.get(alt_name.upper())
    if value:
        return value.lower() in ('true', '1', 'yes', 'on')
    return default

# 导出所有函数
__all__ = ['get_float', 'get_int', 'get_str', 'get_bool']
