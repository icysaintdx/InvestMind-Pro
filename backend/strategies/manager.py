"""
策略管理器
负责策略的注册、运行、回测和优化
"""

from typing import Dict, List, Optional, Any
import asyncio
from datetime import datetime
import json
from pathlib import Path
import pandas as pd
import numpy as np

from backend.utils.logging_config import get_logger
from .base import BaseStrategy, StrategySignal, SignalType, StrategyPerformance

logger = get_logger("strategies.manager")


class StrategyManager:
    """策略管理器"""
    
    def __init__(self):
        self.strategies: Dict[str, BaseStrategy] = {}
        self.active_strategies: set = set()
        self.strategy_weights: Dict[str, float] = {}
        self.performance_history: Dict[str, List[StrategyPerformance]] = {}
        self.config_file = Path("backend/data/strategy_config.json")
        
        self._load_config()
        self._register_all_strategies()
        
    def _load_config(self):
        """加载策略配置"""
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.active_strategies = set(config.get("active", []))
                self.strategy_weights = config.get("weights", {})
        else:
            # 默认配置
            self.active_strategies = {"buffett_value", "turtle_trading", "ma_cross"}
            self.strategy_weights = {
                "buffett_value": 0.4,
                "turtle_trading": 0.3,
                "ma_cross": 0.3
            }
            self._save_config()
            
    def _save_config(self):
        """保存策略配置"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        config = {
            "active": list(self.active_strategies),
            "weights": self.strategy_weights,
            "updated_at": datetime.now().isoformat()
        }
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
            
    def _register_all_strategies(self):
        """注册所有策略"""
        # 延迟导入避免循环引用
        try:
            # 价值投资策略
            from .value_investing.buffett import BuffettValueStrategy
            self.register_strategy("buffett_value", BuffettValueStrategy())
            
            # 技术分析策略
            # from .technical.turtle import TurtleTradingStrategy
            # self.register_strategy("turtle_trading", TurtleTradingStrategy())
            
            # from .technical.ma_cross import MACrossStrategy
            # self.register_strategy("ma_cross", MACrossStrategy())
            
            logger.info(f"成功注册 {len(self.strategies)} 个策略")
            
        except ImportError as e:
            logger.warning(f"部分策略未能注册: {e}")
            
    def register_strategy(self, strategy_id: str, strategy: BaseStrategy):
        """
        注册策略
        
        Args:
            strategy_id: 策略ID
            strategy: 策略实例
        """
        self.strategies[strategy_id] = strategy
        logger.info(f"注册策略: {strategy.name} ({strategy_id})")
        
    def activate_strategy(self, strategy_id: str, weight: float = 1.0):
        """
        激活策略
        
        Args:
            strategy_id: 策略ID
            weight: 策略权重
        """
        if strategy_id not in self.strategies:
            raise ValueError(f"策略 {strategy_id} 不存在")
            
        self.active_strategies.add(strategy_id)
        self.strategy_weights[strategy_id] = weight
        self._save_config()
        
        logger.info(f"激活策略: {strategy_id}, 权重: {weight}")
        
    def deactivate_strategy(self, strategy_id: str):
        """停用策略"""
        self.active_strategies.discard(strategy_id)
        self.strategy_weights.pop(strategy_id, None)
        self._save_config()
        
        logger.info(f"停用策略: {strategy_id}")
        
    async def run_strategies(
        self,
        stock_code: str,
        market_data: pd.DataFrame = None,
        fundamental_data: Dict = None
    ) -> List[StrategySignal]:
        """
        运行所有激活的策略
        
        Args:
            stock_code: 股票代码
            market_data: 市场数据
            fundamental_data: 基本面数据
            
        Returns:
            策略信号列表
        """
        if not self.active_strategies:
            logger.warning("没有激活的策略")
            return []
            
        # 如果没有提供数据，获取默认数据
        if market_data is None:
            market_data = await self._get_default_market_data(stock_code)
            
        # 并发运行所有策略
        tasks = []
        for strategy_id in self.active_strategies:
            if strategy_id in self.strategies:
                strategy = self.strategies[strategy_id]
                tasks.append(
                    self._run_strategy_safe(
                        strategy, stock_code, market_data, fundamental_data
                    )
                )
                
        signals = await asyncio.gather(*tasks)
        
        # 过滤掉None值
        signals = [s for s in signals if s is not None]
        
        logger.info(f"运行 {len(signals)} 个策略，生成 {len(signals)} 个信号")
        
        return signals
        
    async def _run_strategy_safe(
        self,
        strategy: BaseStrategy,
        stock_code: str,
        market_data: pd.DataFrame,
        fundamental_data: Dict
    ) -> Optional[StrategySignal]:
        """安全运行策略（带异常处理）"""
        try:
            return await strategy.analyze(stock_code, market_data, fundamental_data)
        except Exception as e:
            logger.error(f"策略 {strategy.strategy_id} 运行失败: {e}")
            return None
            
    def combine_signals(
        self,
        signals: List[StrategySignal],
        method: str = "weighted_vote"
    ) -> Dict[str, Any]:
        """
        组合多个策略信号
        
        Args:
            signals: 策略信号列表
            method: 组合方法 (weighted_vote, majority_vote, consensus)
            
        Returns:
            组合后的决策
        """
        if not signals:
            return {
                "action": "HOLD",
                "confidence": 0,
                "strength": 0,
                "reasons": ["没有策略信号"]
            }
            
        if method == "weighted_vote":
            return self._weighted_vote(signals)
        elif method == "majority_vote":
            return self._majority_vote(signals)
        elif method == "consensus":
            return self._consensus_vote(signals)
        else:
            return self._weighted_vote(signals)
            
    def _weighted_vote(self, signals: List[StrategySignal]) -> Dict[str, Any]:
        """加权投票"""
        buy_score = 0
        sell_score = 0
        hold_score = 0
        total_weight = 0
        all_reasons = []
        
        for signal in signals:
            # 获取策略权重
            weight = self.strategy_weights.get(signal.strategy_id, 1.0)
            signal_weight = weight * signal.confidence * signal.strength
            
            if signal.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
                buy_score += signal_weight
            elif signal.signal_type in [SignalType.SELL, SignalType.STRONG_SELL]:
                sell_score += signal_weight
            else:
                hold_score += signal_weight
                
            total_weight += signal_weight
            all_reasons.extend([f"[{signal.strategy_name}] {r}" for r in signal.reasons[:2]])
            
        # 归一化分数
        if total_weight > 0:
            buy_score /= total_weight
            sell_score /= total_weight
            hold_score /= total_weight
            
        # 决策
        if buy_score > max(sell_score, hold_score) * 1.2:
            action = "BUY"
            confidence = buy_score
            strength = np.mean([s.strength for s in signals 
                               if s.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]])
        elif sell_score > max(buy_score, hold_score) * 1.1:
            action = "SELL"
            confidence = sell_score
            strength = np.mean([s.strength for s in signals
                               if s.signal_type in [SignalType.SELL, SignalType.STRONG_SELL]])
        else:
            action = "HOLD"
            confidence = hold_score
            strength = 0.5
            
        # 计算建议仓位
        position_sizes = [s.position_size for s in signals if s.position_size is not None]
        avg_position = np.mean(position_sizes) if position_sizes else 0
        
        # 计算目标价格（加权平均）
        target_prices = []
        stop_losses = []
        
        for signal in signals:
            if signal.target_price:
                weight = self.strategy_weights.get(signal.strategy_id, 1.0)
                target_prices.append((signal.target_price, weight))
            if signal.stop_loss:
                stop_losses.append((signal.stop_loss, weight))
                
        avg_target = sum(p * w for p, w in target_prices) / sum(w for _, w in target_prices) if target_prices else None
        avg_stop_loss = sum(p * w for p, w in stop_losses) / sum(w for _, w in stop_losses) if stop_losses else None
        
        return {
            "action": action,
            "confidence": float(confidence),
            "strength": float(strength),
            "position_size": float(avg_position),
            "target_price": avg_target,
            "stop_loss": avg_stop_loss,
            "buy_score": float(buy_score),
            "sell_score": float(sell_score),
            "hold_score": float(hold_score),
            "strategies_count": len(signals),
            "strategies_agree": sum(1 for s in signals if s.signal_type.value.startswith(action)),
            "reasons": all_reasons[:10]  # 最多10条理由
        }
        
    def _majority_vote(self, signals: List[StrategySignal]) -> Dict[str, Any]:
        """多数投票"""
        buy_count = sum(1 for s in signals if s.signal_type in [SignalType.BUY, SignalType.STRONG_BUY])
        sell_count = sum(1 for s in signals if s.signal_type in [SignalType.SELL, SignalType.STRONG_SELL])
        hold_count = len(signals) - buy_count - sell_count
        
        total = len(signals)
        
        if buy_count > total / 2:
            action = "BUY"
            confidence = buy_count / total
        elif sell_count > total / 2:
            action = "SELL"
            confidence = sell_count / total
        else:
            action = "HOLD"
            confidence = hold_count / total
            
        return {
            "action": action,
            "confidence": confidence,
            "buy_votes": buy_count,
            "sell_votes": sell_count,
            "hold_votes": hold_count,
            "total_votes": total
        }
        
    def _consensus_vote(self, signals: List[StrategySignal]) -> Dict[str, Any]:
        """共识投票（需要高度一致）"""
        signal_types = [s.signal_type for s in signals]
        
        # 检查是否有强烈共识
        buy_signals = [SignalType.BUY, SignalType.STRONG_BUY]
        sell_signals = [SignalType.SELL, SignalType.STRONG_SELL]
        
        if all(st in buy_signals for st in signal_types):
            return {
                "action": "STRONG_BUY",
                "confidence": 0.95,
                "consensus": True
            }
        elif all(st in sell_signals for st in signal_types):
            return {
                "action": "STRONG_SELL",
                "confidence": 0.95,
                "consensus": True
            }
        else:
            # 没有共识，保持观望
            return {
                "action": "HOLD",
                "confidence": 0.5,
                "consensus": False,
                "reason": "策略之间没有达成共识"
            }
            
    async def backtest_portfolio(
        self,
        stock_codes: List[str],
        start_date: str,
        end_date: str,
        initial_capital: float = 1000000
    ) -> Dict[str, Any]:
        """
        回测策略组合
        
        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            initial_capital: 初始资金
            
        Returns:
            组合回测结果
        """
        portfolio_results = {}
        
        for stock_code in stock_codes:
            # 对每只股票运行所有策略的回测
            stock_results = []
            
            for strategy_id in self.active_strategies:
                if strategy_id in self.strategies:
                    strategy = self.strategies[strategy_id]
                    try:
                        performance = await strategy.backtest(
                            stock_code, start_date, end_date, 
                            initial_capital / len(stock_codes)
                        )
                        stock_results.append(performance)
                    except Exception as e:
                        logger.error(f"回测失败 {strategy_id} on {stock_code}: {e}")
                        
            portfolio_results[stock_code] = stock_results
            
        # 汇总结果
        return self._aggregate_backtest_results(portfolio_results)
        
    def _aggregate_backtest_results(self, results: Dict) -> Dict[str, Any]:
        """汇总回测结果"""
        # TODO: 实现结果汇总逻辑
        return {
            "total_return": 15.5,
            "sharpe_ratio": 1.2,
            "max_drawdown": -12.3,
            "win_rate": 55.0,
            "results": results
        }
        
    async def _get_default_market_data(self, stock_code: str) -> pd.DataFrame:
        """获取默认市场数据（模拟）"""
        # TODO: 从实际数据源获取
        dates = pd.date_range(end=datetime.now(), periods=100)
        return pd.DataFrame({
            'open': np.random.randn(100) * 2 + 100,
            'high': np.random.randn(100) * 2 + 102,
            'low': np.random.randn(100) * 2 + 98,
            'close': np.random.randn(100) * 2 + 100,
            'volume': np.random.randint(1000000, 10000000, 100)
        }, index=dates)
        
    def get_strategy_info(self) -> Dict[str, Any]:
        """获取策略信息"""
        return {
            "total": len(self.strategies),
            "active": len(self.active_strategies),
            "strategies": {
                sid: {
                    "name": s.name,
                    "category": s.category.value,
                    "description": s.description,
                    "is_active": sid in self.active_strategies,
                    "weight": self.strategy_weights.get(sid, 0)
                }
                for sid, s in self.strategies.items()
            }
        }
