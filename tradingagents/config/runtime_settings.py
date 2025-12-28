"""
tradingagents.config.runtime_settings 兼容层
重定向到 backend.dataflows.utils.config_utils
"""
import os
from backend.dataflows.utils.config_utils import get_float, get_int, get_str, get_bool

def get_timezone_name() -> str:
    """获取时区名称"""
    return os.environ.get('TZ', 'Asia/Shanghai')

def use_app_cache_enabled() -> bool:
    """是否启用应用缓存"""
    return get_bool('USE_APP_CACHE', 'use_app_cache', False)

__all__ = ['get_float', 'get_int', 'get_str', 'get_bool', 'get_timezone_name', 'use_app_cache_enabled']
