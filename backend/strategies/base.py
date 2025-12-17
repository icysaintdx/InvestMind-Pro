"""
策略系统基础框架
定义策略基类、信号类型、性能指标等
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd


class SignalType(str, Enum):
    """信号类型"""
    BUY = "buy"           # 买入
    SELL = "sell"         # 卖出
    HOLD = "hold"         # 持有
    STRONG_BUY = "strong_buy"    # 强烈买入
    STRONG_SELL = "strong_sell"  # 强烈卖出


class StrategyCategory(str, Enum):
    """策略分类"""
    TREND = "trend"           # 趋势跟踪
    MEAN_REVERSION = "mean_reversion"  # 均值回归
    MOMENTUM = "momentum"     # 动量策略
    VALUE = "value"           # 价值投资
    TECHNICAL = "technical"   # 技术分析
    QUANTITATIVE = "quantitative"  # 量化因子
    AI = "ai"                 # AI智能体
    HYBRID = "hybrid"         # 混合策略


@dataclass
class StrategySignal:
    """策略信号"""
    signal_type: SignalType
    confidence: float = 0.5      # 置信度 0-1
    price: float = 0.0           # 建议价格
    quantity: int = 0            # 建议数量
    stop_loss: float = 0.0       # 止损价
    take_profit: float = 0.0     # 止盈价
    reason: str = ""             # 信号原因
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 新增字段，与新接口兼容
    strength: float = 0.5        # 信号强度 0-1
    reasons: List[str] = field(default_factory=list)  # 多个原因
    strategy_id: str = ""        # 策略ID
    strategy_name: str = ""      # 策略名称
    position_size: float = 0.0   # 仓位比例
    target_price: float = 0.0    # 目标价格

    def to_dict(self) -> Dict:
        return {
            "signal_type": self.signal_type.value,
            "confidence": self.confidence,
            "price": self.price,
            "quantity": self.quantity,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "strength": self.strength,
            "reasons": self.reasons,
            "strategy_id": self.strategy_id,
            "strategy_name": self.strategy_name,
            "position_size": self.position_size,
            "target_price": self.target_price
        }


# 别名，保持向后兼容
Signal = StrategySignal


@dataclass
class StrategyPerformance:
    """策略性能指标"""
    total_return: float = 0.0        # 总收益率
    annual_return: float = 0.0       # 年化收益率
    max_drawdown: float = 0.0        # 最大回撤
    sharpe_ratio: float = 0.0        # 夏普比率
    sortino_ratio: float = 0.0       # 索提诺比率
    win_rate: float = 0.0            # 胜率
    profit_factor: float = 0.0       # 盈亏比
    total_trades: int = 0            # 总交易次数
    winning_trades: int = 0          # 盈利交易次数
    losing_trades: int = 0           # 亏损交易次数
    avg_win: float = 0.0             # 平均盈利
    avg_loss: float = 0.0            # 平均亏损
    avg_holding_days: float = 0.0    # 平均持仓天数
    benchmark_return: float = 0.0    # 基准收益率
    alpha: float = 0.0               # 超额收益
    beta: float = 0.0                # 贝塔系数

    def to_dict(self) -> Dict:
        return {
            "total_return": round(self.total_return, 4),
            "annual_return": round(self.annual_return, 4),
            "max_drawdown": round(self.max_drawdown, 4),
            "sharpe_ratio": round(self.sharpe_ratio, 2),
            "sortino_ratio": round(self.sortino_ratio, 2),
            "win_rate": round(self.win_rate, 4),
            "profit_factor": round(self.profit_factor, 2),
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "avg_win": round(self.avg_win, 4),
            "avg_loss": round(self.avg_loss, 4),
            "avg_holding_days": round(self.avg_holding_days, 1),
            "benchmark_return": round(self.benchmark_return, 4),
            "alpha": round(self.alpha, 4),
            "beta": round(self.beta, 2)
        }


@dataclass
class StrategyConfig:
    """策略配置"""
    name: str
    version: str = "1.0.0"
    category: StrategyCategory = StrategyCategory.TECHNICAL
    description: str = ""
    author: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    risk_params: Dict[str, Any] = field(default_factory=lambda: {
        "max_position_pct": 0.3,      # 最大仓位比例
        "stop_loss_pct": 0.05,        # 止损比例
        "take_profit_pct": 0.10,      # 止盈比例
        "max_drawdown_pct": 0.15      # 最大回撤限制
    })


class BaseStrategy(ABC):
    """策略基类"""
    
    # 策略描述（子类可以覆盖）
    description: str = "未提供描述"

    def __init__(self, config: Optional[StrategyConfig] = None):
        if config is None:
            config = StrategyConfig(name=self.__class__.__name__)
        self.config = config
        self.name = config.name
        self.category = config.category
        self.parameters = config.parameters
        self.risk_params = config.risk_params
        self._initialized = False

    @abstractmethod
    def initialize(self, data: pd.DataFrame) -> None:
        """初始化策略（计算指标等）"""
        pass

    @abstractmethod
    def generate_signal(
        self,
        data: pd.DataFrame,
        current_position: int = 0
    ) -> StrategySignal:
        """生成交易信号"""
        pass

    @abstractmethod
    def get_required_indicators(self) -> List[str]:
        """获取策略所需的技术指标"""
        pass

    def validate_data(self, data: pd.DataFrame) -> bool:
        """验证数据完整性"""
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        return all(col in data.columns for col in required_columns)

    def calculate_position_size(
        self,
        capital: float,
        price: float,
        risk_per_trade: float = 0.02
    ) -> int:
        """计算仓位大小"""
        max_position_value = capital * self.risk_params.get('max_position_pct', 0.3)
        risk_value = capital * risk_per_trade
        stop_loss_pct = self.risk_params.get('stop_loss_pct', 0.05)

        # 基于风险计算
        position_by_risk = risk_value / (price * stop_loss_pct)

        # 基于最大仓位计算
        position_by_max = max_position_value / price

        # 取较小值
        quantity = int(min(position_by_risk, position_by_max))

        # A股需要是100的整数倍
        quantity = (quantity // 100) * 100

        return max(quantity, 100)

    def calculate_stop_loss(self, entry_price: float, side: str = 'buy') -> float:
        """计算止损价"""
        stop_loss_pct = self.risk_params.get('stop_loss_pct', 0.05)
        if side == 'buy':
            return round(entry_price * (1 - stop_loss_pct), 2)
        else:
            return round(entry_price * (1 + stop_loss_pct), 2)

    def calculate_take_profit(self, entry_price: float, side: str = 'buy') -> float:
        """计算止盈价"""
        take_profit_pct = self.risk_params.get('take_profit_pct', 0.10)
        if side == 'buy':
            return round(entry_price * (1 + take_profit_pct), 2)
        else:
            return round(entry_price * (1 - take_profit_pct), 2)

    def get_info(self) -> Dict:
        """获取策略信息"""
        return {
            "name": self.name,
            "category": self.category.value,
            "description": self.config.description,
            "version": self.config.version,
            "author": self.config.author,
            "parameters": self.parameters,
            "risk_params": self.risk_params,
            "required_indicators": self.get_required_indicators()
        }


class StrategyRegistry:
    """策略注册表"""

    def __init__(self):
        self._strategies: Dict[str, type] = {}

    def register(self, name: str, strategy_class: type) -> None:
        """注册策略"""
        if not issubclass(strategy_class, BaseStrategy):
            raise ValueError(f"{strategy_class} must be a subclass of BaseStrategy")
        self._strategies[name] = strategy_class

    def get(self, name: str) -> Optional[type]:
        """获取策略类"""
        return self._strategies.get(name)
    
    def get_strategy_class(self, name: str) -> Optional[type]:
        """获取策略类（别名方法）"""
        return self.get(name)

    def list_strategies(self) -> List[str]:
        """列出所有策略"""
        return list(self._strategies.keys())

    def create_strategy(self, name: str, config: StrategyConfig) -> Optional[BaseStrategy]:
        """创建策略实例"""
        strategy_class = self.get(name)
        if strategy_class:
            return strategy_class(config)
        return None


# 全局策略注册表
strategy_registry = StrategyRegistry()


def register_strategy(name: str):
    """策略注册装饰器"""
    def decorator(cls):
        strategy_registry.register(name, cls)
        return cls
    return decorator


def get_strategy_registry() -> StrategyRegistry:
    """获取策略注册表"""
    return strategy_registry
