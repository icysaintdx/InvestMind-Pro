from .utils.agent_utils import Toolkit, create_msg_delete
from .utils.agent_states import AgentState, InvestDebateState, RiskDebateState

# ChromaDB是可选的，如果导入失败则禁用memory功能
try:
    from .utils.memory import FinancialSituationMemory
    MEMORY_AVAILABLE = True
except ImportError as e:
    FinancialSituationMemory = None
    MEMORY_AVAILABLE = False
    # 导入失败但不影响其他功能

from .analysts.fundamentals_analyst import create_fundamentals_analyst
from .analysts.market_analyst import create_market_analyst
from .analysts.news_analyst import create_news_analyst
from .analysts.social_media_analyst import create_social_media_analyst

from .researchers.bear_researcher import create_bear_researcher
from .researchers.bull_researcher import create_bull_researcher

from .risk_mgmt.aggresive_debator import create_risky_debator
from .risk_mgmt.conservative_debator import create_safe_debator
from .risk_mgmt.neutral_debator import create_neutral_debator

from .managers.research_manager import create_research_manager
from .managers.risk_manager import create_risk_manager

from .trader.trader import create_trader

# 导入统一日志系统
from backend.utils.logging_config import get_logger
logger = get_logger("default")

__all__ = [
    "Toolkit",
    "AgentState",
    "create_msg_delete",
    "InvestDebateState",
    "RiskDebateState",
    "create_bear_researcher",
    "create_bull_researcher",
    "create_research_manager",
    "create_fundamentals_analyst",
    "create_market_analyst",
    "create_neutral_debator",
    "create_news_analyst",
    "create_risky_debator",
    "create_risk_manager",
    "create_safe_debator",
    "create_social_media_analyst",
    "create_trader",
]

# 如果memory功能可用，则添加到导出列表
if MEMORY_AVAILABLE:
    __all__.append("FinancialSituationMemory")
