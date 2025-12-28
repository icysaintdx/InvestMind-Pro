"""
新闻数据源提供者

包含各种新闻数据源的具体实现。
"""

from .akshare_provider import AKShareNewsProvider
from .wencai_provider import WencaiNewsProvider

__all__ = [
    'AKShareNewsProvider',
    'WencaiNewsProvider',
]