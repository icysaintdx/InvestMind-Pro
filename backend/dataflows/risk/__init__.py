"""
风险数据模块
提供失信被执行人、裁判文书等风险数据查询
"""

from .akshare_risk import get_akshare_risk, AKShareRiskData

__all__ = [
    'get_akshare_risk',
    'AKShareRiskData',
]
