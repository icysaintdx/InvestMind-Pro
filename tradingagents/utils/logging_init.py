"""
tradingagents.utils.logging_init 兼容层
重定向到 backend.utils.logging_config
"""
from backend.utils.logging_config import setup_logging, get_logger

def setup_dataflow_logging(level="INFO"):
    """设置数据流日志（兼容旧接口）"""
    setup_logging(level=level)
    return get_logger('dataflows')

__all__ = ['setup_dataflow_logging', 'setup_logging', 'get_logger']
