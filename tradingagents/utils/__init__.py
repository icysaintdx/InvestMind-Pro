"""
tradingagents.utils 兼容层
重定向到 backend.utils
"""
from backend.utils.logging_config import get_logger, setup_logging

__all__ = ['get_logger', 'setup_logging']
