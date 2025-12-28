"""
数据流工具模块
提供数据流相关的辅助功能
"""

import os
import json
from typing import Optional, Callable, Any, TypeVar
from functools import wraps

from backend.utils.logging_config import get_logger

logger = get_logger("dataflow_utils")

# 类型别名
SavePathType = Optional[str]

# 泛型类型变量
T = TypeVar('T')


def format_stock_data(data):
    """
    格式化股票数据
    
    Args:
        data: 原始股票数据
        
    Returns:
        格式化后的数据
    """
    if not data:
        return None
    
    # 简单的格式化逻辑
    return data


def validate_ticker(ticker):
    """
    验证股票代码格式
    
    Args:
        ticker: 股票代码
        
    Returns:
        bool: 是否有效
    """
    if not ticker or not isinstance(ticker, str):
        return False
    
    # 简单验证
    return len(ticker) >= 4


def save_output(data, description: str = None, save_path: SavePathType = None):
    """
    保存输出数据到文件
    
    Args:
        data: 要保存的数据
        description: 数据描述（可选）
        save_path: 保存路径（可选）
    """
    if save_path is None:
        return
    
    # 确保目录存在
    dir_path = os.path.dirname(save_path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)
    
    # 保存数据
    try:
        with open(save_path, 'w', encoding='utf-8') as f:
            if hasattr(data, 'to_csv'):
                # DataFrame
                data.to_csv(f)
            elif isinstance(data, (dict, list)):
                json.dump(data, f, ensure_ascii=False, indent=2)
            else:
                f.write(str(data))
        
        if description:
            logger.info(f"{description} 已保存到: {save_path}")
        else:
            logger.info(f"数据已保存到: {save_path}")
    except Exception as e:
        logger.error(f"保存数据失败: {e}")


def decorate_all_methods(decorator: Callable) -> Callable:
    """
    类装饰器：为类的所有方法应用指定的装饰器
    
    Args:
        decorator: 要应用的装饰器
        
    Returns:
        类装饰器
    """
    def class_decorator(cls):
        for attr_name in dir(cls):
            if attr_name.startswith('_'):
                continue
            attr = getattr(cls, attr_name)
            if callable(attr):
                setattr(cls, attr_name, decorator(attr))
        return cls
    return class_decorator


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """
    重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 重试间隔（秒）
        
    Returns:
        装饰器
    """
    import time
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(f"函数 {func.__name__} 执行失败，{delay}秒后重试 ({attempt + 1}/{max_retries}): {e}")
                        time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator


def cache_result(ttl_seconds: int = 300):
    """
    缓存装饰器
    
    Args:
        ttl_seconds: 缓存有效期（秒）
        
    Returns:
        装饰器
    """
    import time
    
    cache = {}
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            key = (func.__name__, args, tuple(sorted(kwargs.items())))
            
            # 检查缓存
            if key in cache:
                result, timestamp = cache[key]
                if time.time() - timestamp < ttl_seconds:
                    return result
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 存入缓存
            cache[key] = (result, time.time())
            
            return result
        return wrapper
    return decorator


def format_number(value: float, precision: int = 2) -> str:
    """
    格式化数字（支持大数字简写）
    
    Args:
        value: 数值
        precision: 精度
        
    Returns:
        格式化后的字符串
    """
    if value is None:
        return "N/A"
    
    abs_value = abs(value)
    
    if abs_value >= 1e12:
        return f"{value / 1e12:.{precision}f}万亿"
    elif abs_value >= 1e8:
        return f"{value / 1e8:.{precision}f}亿"
    elif abs_value >= 1e4:
        return f"{value / 1e4:.{precision}f}万"
    else:
        return f"{value:.{precision}f}"


def parse_date(date_str: str) -> Optional[str]:
    """
    解析日期字符串，统一转换为 YYYY-MM-DD 格式
    
    Args:
        date_str: 日期字符串
        
    Returns:
        标准化的日期字符串
    """
    from datetime import datetime
    
    if not date_str:
        return None
    
    # 尝试多种格式
    formats = [
        "%Y-%m-%d",
        "%Y%m%d",
        "%Y/%m/%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    return None
