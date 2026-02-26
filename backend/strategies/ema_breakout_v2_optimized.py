# -*- coding: utf-8 -*-
"""
EMA突破策略 V2.1 - 优化版（动态止损 + 大盘过滤）
核心改进：
1. 动态止损参数：按股票波动率分类设置不同ATR倍数
2. 大盘趋势过滤：基于沪深300 EMA50判断
3. 参数自适应：不同股票类型使用不同EMA周期
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List
from .base import (
    BaseStrategy,
    StrategySignal,
    SignalType,
    StrategyConfig,
    register_strategy
)


# 股票波动率分类配置
STOCK_VOLATILITY_CONFIG = {
    # 高波动股票（科技股、小盘股）
    'high_volatility': {
        'symbols': ['300750', '002594', '601888'],  # 宁德时代、比亚迪、中国中免
        'atr_multiplier': 3.0,  # 更宽松的止损
        'ema_fast': 10,
        'ema_slow': 30,
        'description': '高波动 - 宽松止损'
    },
    # 中波动股票（消费蓝筹）
    'medium_volatility': {
        'symbols': ['000858', '000333', '000651'],  # 五粮液、美的、格力
        'atr_multiplier': 2.0,  # 标准止损
        'ema_fast': 8,
        'ema_slow': 25,
        'description': '中波动 - 标准止损'
    },
    # 低波动股票（价值蓝筹）
    'low_volatility': {
        'symbols': ['600519', '601318', '600036', '600276'],  # 茅台、平安、招行、恒瑞
        'atr_multiplier': 1.5,  # 更严格的止损
        'ema_fast': 5,
        'ema_slow': 20,
        'description': '低波动 - 严格止损'
    }
}


def get_stock_volatility_class(symbol: str) -> Dict[str, Any]:
    """获取股票的波动率分类配置"""
    for vol_class, config in STOCK_VOLATILITY_CONFIG.items():
        if symbol in config['symbols']:
            return {
                'class': vol_class,
                **config
            }
    # 默认中波动
    return {
        'class': 'medium_volatility',
        **STOCK_VOLATILITY_CONFIG['medium_volatility']
    }


@register_strategy("ema_breakout_v2_optimized")
class EMABreakoutV2OptimizedStrategy(BaseStrategy):
    """
    EMA突破策略 V2.1 - 优化版
    
    改进点：
    - 动态参数：按股票波动率分类配置
    - 动态止损：高波动3倍ATR，中波动2倍ATR，低波动1.5倍ATR
    - 大盘过滤：沪深300 EMA50趋势向上才允许买入
    - 自适应EMA周期：不同波动率使用不同均线周期
    """
    
    description = "EMA突破V2.1 - 动态止损 + 大盘过滤"
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.name = "EMA突破V2.1优化版"
        self.category = "技术分析"
        
        # 获取股票代码
        self.symbol = config.parameters.get('symbol', '')
        
        # 根据股票波动率分类获取动态参数
        vol_config = get_stock_volatility_class(self.symbol)
        
        # EMA参数（动态）
        self.ema_fast = config.parameters.get('ema_fast', vol_config['ema_fast'])
        self.ema_slow = config.parameters.get('ema_slow', vol_config['ema_slow'])
        
        # ATR止损参数（动态）
        self.atr_period = config.parameters.get('atr_period', 14)
        self.atr_multiplier = config.parameters.get('atr_multiplier', vol_config['atr_multiplier'])
        
        # 大盘过滤参数
        self.market_filter_enabled = config.parameters.get('market_filter_enabled', True)
        self.market_ema_period = config.parameters.get('market_ema_period', 50)
        
        # Kelly仓位参数
        self.kelly_fraction = config.parameters.get('kelly_fraction', 0.5)
        self.max_position = config.parameters.get('max_position', 0.4)
        self.min_position = config.parameters.get('min_position', 0.1)
        
        # 历史记录
        self.trade_history = []
        self.win_count = 0
        self.loss_count = 0
        
        # 大盘数据缓存
        self._market_data = None
        
    def initialize(self, data: pd.DataFrame, market_data: Optional[pd.DataFrame] = None):
        """计算指标
        
        Args:
            data: 个股数据
            market_data: 大盘数据（沪深300）
        """
        df = data.copy()
        
        # EMA
        df['ema_fast'] = df['close'].ewm(span=self.ema_fast).mean()
        df['ema_slow'] = df['close'].ewm(span=self.ema_slow).mean()
        
        # ATR
        high_low = df['high'] - df['low']
        high_close = (df['high'] - df['close'].shift()).abs()
        low_close = (df['low'] - df['close'].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = tr.ewm(span=self.atr_period).mean()
        
        # RSI辅助
        delta = df['close'].diff()
        gain = delta.clip(lower=0).ewm(span=14).mean()
        loss = (-delta.clip(upper=0)).ewm(span=14).mean()
        df['rsi'] = 100 - 100 / (1 + gain / (loss + 0.001))
        
        # 趋势强度
        df['trend_strength'] = (df['ema_fast'] - df['ema_slow']) / df['ema_slow'] * 100
        
        self._data = df
        
        # 处理大盘数据
        if market_data is not None and self.market_filter_enabled:
            mdf = market_data.copy()
            mdf['ema'] = mdf['close'].ewm(span=self.market_ema_period).mean()
            mdf['trend_up'] = mdf['close'] > mdf['ema']
            self._market_data = mdf
        
        self._initialized = True
    
    def _check_market_trend(self, idx: int) -> bool:
        """检查大盘趋势是否向上
        
        Returns:
            True: 大盘趋势向上，允许买入
            False: 大盘趋势向下，禁止买入
        """
        if not self.market_filter_enabled or self._market_data is None:
            return True  # 未启用大盘过滤，默认允许
        
        if idx >= len(self._market_data):
            return False
        
        return bool(self._market_data['trend_up'].iloc[idx])
    
    def _calculate_kelly_position(self) -> float:
        """计算Kelly最优仓位"""
        total = self.win_count + self.loss_count
        if total < 10:
            return 0.2
        
        p = self.win_count / total
        q = 1 - p
        b = 2.0  # 假设盈亏比2:1
        
        kelly = (p * b - q) / b
        kelly = max(0, min(kelly, 0.5))
        
        return kelly * self.kelly_fraction
    
    def generate_signal(self, data: pd.DataFrame, current_position: int = 0) -> Optional[StrategySignal]:
        if not self._initialized:
            self.initialize(data)
        
        idx = len(data) - 1
        if idx >= len(self._data):
            return StrategySignal(signal_type=SignalType.HOLD, confidence=0.0, price=data['close'].iloc[-1])
        
        bar = self._data.iloc[idx]
        price = float(bar['close'])
        
        if pd.isna(bar.get('ema_fast')) or pd.isna(bar.get('atr')):
            return StrategySignal(signal_type=SignalType.HOLD, confidence=0.0, price=price, reason="指标计算中")
        
        # 金叉/死叉判断
        ema_fast = bar['ema_fast']
        ema_slow = bar['ema_slow']
        ema_fast_prev = self._data['ema_fast'].iloc[idx-1]
        ema_slow_prev = self._data['ema_slow'].iloc[idx-1]
        
        golden_cross = (ema_fast > ema_slow) and (ema_fast_prev <= ema_slow_prev)
        death_cross = (ema_fast < ema_slow) and (ema_fast_prev >= ema_slow_prev)
        
        trend_up = ema_fast > ema_slow
        trend_down = ema_fast < ema_slow
        
        rsi = bar.get('rsi', 50)
        atr = bar['atr']
        
        # 获取波动率分类信息
        vol_config = get_stock_volatility_class(self.symbol)
        
        # ===== 买入逻辑 =====
        if current_position == 0:
            # 大盘趋势检查
            market_trend_ok = self._check_market_trend(idx)
            
            # 条件：金叉 + 趋势向上 + RSI不超买 + 大盘趋势向上
            if golden_cross and trend_up and rsi < 70:
                if not market_trend_ok:
                    return StrategySignal(
                        signal_type=SignalType.HOLD,
                        confidence=0.0,
                        price=price,
                        reason=f"个股金叉但大盘趋势向下，观望 | {vol_config['description']}"
                    )
                
                position_size = self._calculate_kelly_position()
                stop_loss = price - self.atr_multiplier * atr
                take_profit = price + 2 * (price - stop_loss)
                
                return StrategySignal(
                    signal_type=SignalType.BUY,
                    confidence=0.75,
                    price=price,
                    stop_loss=round(stop_loss, 2),
                    take_profit=round(take_profit, 2),
                    position_size=position_size,
                    reason=f"EMA{self.ema_fast}/{self.ema_slow}金叉 | {vol_config['description']} | ATR{self.atr_multiplier}倍止损={stop_loss:.2f} | Kelly仓位={position_size:.1%}"
                )
        
        # ===== 卖出逻辑 =====
        elif current_position > 0:
            if death_cross:
                self._record_trade(False)
                return StrategySignal(
                    signal_type=SignalType.SELL,
                    confidence=0.8,
                    price=price,
                    reason="EMA死叉，趋势反转"
                )
            
            if price < ema_fast and trend_down:
                self._record_trade(False)
                return StrategySignal(
                    signal_type=SignalType.SELL,
                    confidence=0.7,
                    price=price,
                    reason="跌破EMA，止损离场"
                )
        
        return StrategySignal(
            signal_type=SignalType.HOLD,
            confidence=0.3,
            price=price,
            reason="等待信号",
            metadata={
                'ema_fast': round(ema_fast, 2),
                'ema_slow': round(ema_slow, 2),
                'trend': 'UP' if trend_up else 'DOWN',
                'rsi': round(rsi, 1),
                'atr': round(atr, 2),
                'volatility_class': vol_config['class'],
                'market_trend_ok': self._check_market_trend(idx)
            }
        )
    
    def _record_trade(self, is_win: bool):
        """记录交易结果"""
        if is_win:
            self.win_count += 1
        else:
            self.loss_count += 1
        self.trade_history.append(1 if is_win else 0)
        
        if len(self.trade_history) > 50:
            removed = self.trade_history.pop(0)
            if removed == 1:
                self.win_count -= 1
            else:
                self.loss_count -= 1
    
    def get_required_indicators(self) -> list:
        return ['ema_fast', 'ema_slow', 'atr', 'rsi', 'trend_strength']


def get_stock_classification_report() -> str:
    """生成股票分类报告"""
    report = ["# 股票波动率分类配置", ""]
    
    for vol_class, config in STOCK_VOLATILITY_CONFIG.items():
        report.append(f"## {config['description']}")
        report.append(f"- 分类代码: {vol_class}")
        report.append(f"- ATR倍数: {config['atr_multiplier']}")
        report.append(f"- EMA周期: {config['ema_fast']}/{config['ema_slow']}")
        report.append(f"- 包含股票: {', '.join(config['symbols'])}")
        report.append("")
    
    return "\n".join(report)


if __name__ == "__main__":
    print(get_stock_classification_report())
