"""
tradingagents.dataflows.realtime_metrics 兼容层
"""
try:
    from backend.dataflows.realtime_metrics import *
except ImportError:
    def get_pe_pb_with_fallback(*args, **kwargs):
        return None, None
