"""
回测系统初始化文件
"""

from .engine import BacktestEngine, BacktestConfig, BacktestResult
from .data_loader import DataLoader, DataSource
from .metrics import MetricsCalculator, PerformanceMetrics
from .news_backtest_engine import (
    NewsBacktestEngine, 
    NewsBacktestResult, 
    DailySentiment,
    run_news_backtest
)
from .joint_backtest import (
    JointBacktestEngine,
    JointBacktestConfig,
    JointBacktestResult,
    CombinedSignal,
    TechnicalSignal,
    NewsSignal,
    MarketState,
    run_joint_backtest
)

__all__ = [
    'BacktestEngine',
    'BacktestConfig',
    'BacktestResult',
    'DataLoader',
    'DataSource',
    'MetricsCalculator',
    'PerformanceMetrics',
    # 新闻回测
    'NewsBacktestEngine',
    'NewsBacktestResult',
    'DailySentiment',
    'run_news_backtest',
    # 联合回测
    'JointBacktestEngine',
    'JointBacktestConfig',
    'JointBacktestResult',
    'CombinedSignal',
    'TechnicalSignal',
    'NewsSignal',
    'MarketState',
    'run_joint_backtest'
]
