"""
tradingagents.llm_adapters 兼容层
"""
try:
    from backend.services.llm.adapters import *
except ImportError:
    class ChatDashScopeOpenAI:
        """占位类"""
        pass
