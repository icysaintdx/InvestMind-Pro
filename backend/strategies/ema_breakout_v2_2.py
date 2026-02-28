# -*- coding: utf-8 -*-
"""
EMA突破策略 V2.2 - 增强版（动态止损 + 沪深300大盘过滤）
核心改进：
1. 精确动态止损：按股票波动率分类设置不同ATR倍数
   - 高波动：3倍ATR止损
   - 中波动：2倍ATR止损
   - 低波动：1.5倍ATR止损
2. 沪深300大盘趋势过滤：只在大盘EMA50上方交易
3. 自适应仓位：根据波动率动态调整仓位上限
4. 追踪止损：盈利后启动移动止损保护
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


# 股票波动率分类配置 V2.2
STOCK_VOLATILITY_CONFIG = {
    # 高波动股票 - 3倍ATR止损
    'high_volatility': {
        'symbols': ['300750', '002594', '601888', '300059', '002230'],  # 宁德时代、比亚迪、中国中免、东方财富、科大讯飞
        'atr_multiplier': 3.0,
        'ema_fast': 10,
        'ema_slow': 30,
        'max_position': 0.25,  # 高波动降低仓位
        'description': '高波动 - 3倍ATR止损',
        'trailing_stop': True
    },
    # 中波动股票 - 2倍ATR止损
    'medium_volatility': {
        'symbols': ['000858', '000333', '000651', '000002', '002415'],  # 五粮液、美的、格力、万科、海康威视
        'atr_multiplier': 2.0,
        'ema_fast': 8,
        'ema_slow': 25,
        'max_position': 0.35,
        'description': '中波动 - 2倍ATR止损',
        'trailing_stop': True
    },
    # 低波动股票 - 1.5倍ATR止损
    'low_volatility': {
        'symbols': ['600519', '601318', '600036', '600276', '601398'],  # 茅台、平安、招行、恒瑞、工行
        'atr_multiplier': 1.5,
        'ema_fast': 5,
        'ema_slow': 20,
        'max_position': 0.45,  # 低波动可提高仓位
        'description': '低波动 - 1.5倍ATR止损',
        'trailing_stop': True
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


@register_strategy("ema_breakout_v2_2")
class EMABreakoutV22Strategy(BaseStrategy):
    """
    EMA突破策略 V2.2 - 增强版
    
    核心特性：
    - 动态止损参数：高波动3倍ATR，中波动2倍ATR，低波动1.5倍ATR
    - 沪深300大盘过滤：EMA50趋势向上才允许买入
    - 追踪止损：盈利达1倍ATR后启动移动止损
    - 波动率自适应仓位：根据股票波动率动态调整最大仓位
    """
    
    description = "EMA突破V2.2 - 动态止损(1.5/2/3xATR) + 沪深300过滤"
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.name = "EMA突破V2.2增强版"
        self.category = "技术分析"
        self.version = "2.2"
        
        # 获取股票代码
        self.symbol = config.parameters.get('symbol', '')
        
        # 根据股票波动率分类获取动态参数
        vol_config = get_stock_volatility_class(self.symbol)
        self.vol_class = vol_config['class']
        self.vol_description = vol_config['description']
        
        # EMA参数（动态）
        self.ema_fast = config.parameters.get('ema_fast', vol_config['ema_fast'])
        self.ema_slow = config.parameters.get('ema_slow', vol_config['ema_slow'])
        
        # ATR止损参数（动态 - V2.2核心特性）
        self.atr_period = config.parameters.get('atr_period', 14)
        self.atr_multiplier = config.parameters.get('atr_multiplier', vol_config['atr_multiplier'])
        
        # 仓位参数（动态）
        self.max_position = config.parameters.get('max_position', vol_config['max_position'])
        self.kelly_fraction = config.parameters.get('kelly_fraction', 0.5)
        
        # 大盘过滤参数 - V2.2使用沪深300
        self.market_filter_enabled = config.parameters.get('market_filter_enabled', True)
        self.market_ema_period = config.parameters.get('market_ema_period', 50)
        self.market_symbol = 'sh000300'  # 沪深300指数
        
        # 追踪止损参数
        self.trailing_stop_enabled = config.parameters.get('trailing_stop_enabled', vol_config['trailing_stop'])
        self.trailing_activation_atr = config.parameters.get('trailing_activation_atr', 1.5)  # 盈利1.5倍ATR启动
        self.trailing_atr_multiplier = config.parameters.get('trailing_atr_multiplier', self.atr_multiplier * 0.8)
        
        # 交易状态
        self.trade_history = []
        self.win_count = 0
        self.loss_count = 0
        self.entry_price = 0.0
        self.highest_price = 0.0
        self.stop_loss_price = 0.0
        
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
        df['ema_fast'] = df['close'].ewm(span=self.ema_fast, adjust=False).mean()
        df['ema_slow'] = df['close'].ewm(span=self.ema_slow, adjust=False).mean()
        
        # ATR
        high_low = df['high'] - df['low']
        high_close = (df['high'] - df['close'].shift()).abs()
        low_close = (df['low'] - df['close'].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = tr.ewm(span=self.atr_period, adjust=False).mean()
        
        # 波动率评估
        df['volatility'] = df['close'].pct_change().rolling(20).std() * np.sqrt(252)
        
        # RSI辅助
        delta = df['close'].diff()
        gain = delta.clip(lower=0).ewm(span=14, adjust=False).mean()
        loss = (-delta.clip(upper=0)).ewm(span=14, adjust=False).mean()
        rs = gain / (loss + 1e-10)
        df['rsi'] = 100 - 100 / (1 + rs)
        
        # 趋势强度
        df['trend_strength'] = (df['ema_fast'] - df['ema_slow']) / df['ema_slow'] * 100
        
        self._data = df
        
        # 处理大盘数据 - V2.2沪深300过滤
        if market_data is not None and self.market_filter_enabled:
            mdf = market_data.copy()
            mdf['ema50'] = mdf['close'].ewm(span=self.market_ema_period, adjust=False).mean()
            mdf['trend_up'] = mdf['close'] > mdf['ema50']
            mdf['trend_strength'] = (mdf['close'] - mdf['ema50']) / mdf['ema50'] * 100
            self._market_data = mdf
        
        self._initialized = True
    
    def _check_market_trend(self, idx: int) -> tuple:
        """检查沪深300大盘趋势
        
        Returns:
            tuple: (是否允许交易, 趋势强度)
        """
        if not self.market_filter_enabled or self._market_data is None:
            return True, 0.0  # 未启用大盘过滤，默认允许
        
        if idx >= len(self._market_data):
            return False, 0.0
        
        trend_up = bool(self._market_data['trend_up'].iloc[idx])
        trend_strength = float(self._market_data['trend_strength'].iloc[idx])
        
        return trend_up, trend_strength
    
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
        
        # 应用波动率限制的最大仓位
        position = kelly * self.kelly_fraction
        return min(position, self.max_position)
    
    def _get_dynamic_stop_loss(self, entry_price: float, current_price: float, 
                                atr: float, highest_price: float = None) -> float:
        """计算动态止损价格
        
        Args:
            entry_price: 入场价格
            current_price: 当前价格
            atr: 当前ATR值
            highest_price: 持仓期间最高价（用于追踪止损）
        """
        # 基础止损
        base_stop = entry_price - self.atr_multiplier * atr
        
        # 追踪止损
        if self.trailing_stop_enabled and highest_price is not None:
            profit_atr = (highest_price - entry_price) / atr
            if profit_atr >= self.trailing_activation_atr:
                # 启动追踪止损
                trailing_stop = highest_price - self.trailing_atr_multiplier * atr
                return max(base_stop, trailing_stop)
        
        return base_stop
    
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
        ema_fast_prev = self._data['ema_fast'].iloc[max(0, idx-1)]
        ema_slow_prev = self._data['ema_slow'].iloc[max(0, idx-1)]
        
        golden_cross = (ema_fast > ema_slow) and (ema_fast_prev <= ema_slow_prev)
        death_cross = (ema_fast < ema_slow) and (ema_fast_prev >= ema_slow_prev)
        
        trend_up = ema_fast > ema_slow
        trend_down = ema_fast < ema_slow
        
        rsi = bar.get('rsi', 50)
        atr = bar['atr']
        volatility = bar.get('volatility', 0.2)
        
        # 大盘趋势检查 - V2.2沪深300过滤
        market_trend_ok, market_strength = self._check_market_trend(idx)
        
        # ===== 买入逻辑 =====
        if current_position == 0:
            # 条件：金叉 + 趋势向上 + RSI不超买 + 大盘趋势向上
            if golden_cross and trend_up and rsi < 70:
                if not market_trend_ok:
                    return StrategySignal(
                        signal_type=SignalType.HOLD,
                        confidence=0.0,
                        price=price,
                        reason=f"个股金叉但沪深300低于EMA50(趋势强度:{market_strength:.2f}%),观望|{self.vol_description}"
                    )
                
                position_size = self._calculate_kelly_position()
                stop_loss = price - self.atr_multiplier * atr
                take_profit = price + 3.0 * self.atr_multiplier * atr  # V2.2优化: 3倍ATR止盈
                
                # 更新交易状态
                self.entry_price = price
                self.highest_price = price
                self.stop_loss_price = stop_loss
                
                return StrategySignal(
                    signal_type=SignalType.BUY,
                    confidence=0.75 if market_strength > 2 else 0.65,  # 大盘强势增加置信度
                    price=price,
                    stop_loss=round(stop_loss, 2),
                    take_profit=round(take_profit, 2),
                    position_size=position_size,
                    reason=f"EMA{self.ema_fast}/{self.ema_slow}金叉|沪深300趋势向上(+{market_strength:.1f}%)|{self.vol_description}|止损={stop_loss:.2f}|仓位={position_size:.1%}"
                )
        
        # ===== 卖出逻辑 =====
        elif current_position > 0:
            # 更新最高价
            if price > self.highest_price:
                self.highest_price = price
            
            # 动态止损检查
            dynamic_stop = self._get_dynamic_stop_loss(
                self.entry_price, price, atr, self.highest_price
            )
            
            # 死叉卖出
            if death_cross:
                self._record_trade(False)
                self.entry_price = 0.0
                self.highest_price = 0.0
                return StrategySignal(
                    signal_type=SignalType.SELL,
                    confidence=0.8,
                    price=price,
                    reason=f"EMA死叉止损|入场价={self.entry_price:.2f},出场价={price:.2f}"
                )
            
            # 跌破动态止损
            if price < dynamic_stop:
                self._record_trade(False)
                profit_pct = (price - self.entry_price) / self.entry_price * 100 if self.entry_price > 0 else 0
                stop_type = "追踪止损" if dynamic_stop > self.entry_price - self.atr_multiplier * atr else "固定止损"
                self.entry_price = 0.0
                self.highest_price = 0.0
                return StrategySignal(
                    signal_type=SignalType.SELL,
                    confidence=0.75,
                    price=price,
                    reason=f"{stop_type}触发|{self.vol_description}|盈亏{profit_pct:+.2f}%|止损价={dynamic_stop:.2f}"
                )
            
            # 跌破EMA快速线
            if price < ema_fast and trend_down:
                self._record_trade(False)
                profit_pct = (price - self.entry_price) / self.entry_price * 100 if self.entry_price > 0 else 0
                self.entry_price = 0.0
                self.highest_price = 0.0
                return StrategySignal(
                    signal_type=SignalType.SELL,
                    confidence=0.7,
                    price=price,
                    reason=f"跌破EMA{self.ema_fast}离场|盈亏{profit_pct:+.2f}%"
                )
            
            # 止盈检查
            if self.stop_loss_price > 0:
                profit_target = self.entry_price + 3.0 * self.atr_multiplier * atr
                if price >= profit_target:
                    self._record_trade(True)
                    profit_pct = (price - self.entry_price) / self.entry_price * 100
                    self.entry_price = 0.0
                    self.highest_price = 0.0
                    return StrategySignal(
                        signal_type=SignalType.SELL,
                        confidence=0.7,
                        price=price,
                        reason=f"达到止盈目标{self.atr_multiplier*3.0:.1f}倍ATR|盈利{profit_pct:.2f}%"
                    )
        
        # 返回持有信号，附带详细元数据
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
                'atr_multiplier': self.atr_multiplier,
                'volatility_class': self.vol_class,
                'volatility_annual': round(volatility * 100, 1),
                'market_trend_ok': market_trend_ok,
                'market_strength': round(market_strength, 2),
                'dynamic_stop': round(self._get_dynamic_stop_loss(self.entry_price, price, atr, self.highest_price), 2) if current_position > 0 else None
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
        return ['ema_fast', 'ema_slow', 'atr', 'rsi', 'volatility', 'trend_strength']
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """获取策略信息"""
        return {
            'name': self.name,
            'version': self.version,
            'symbol': self.symbol,
            'volatility_class': self.vol_class,
            'volatility_description': self.vol_description,
            'ema_fast': self.ema_fast,
            'ema_slow': self.ema_slow,
            'atr_multiplier': self.atr_multiplier,
            'max_position': self.max_position,
            'market_filter_enabled': self.market_filter_enabled,
            'market_symbol': self.market_symbol,
            'trailing_stop_enabled': self.trailing_stop_enabled
        }


def get_stock_classification_report() -> str:
    """生成股票分类报告"""
    report = ["# EMA V2.2 股票波动率分类配置", ""]
    
    for vol_class, config in STOCK_VOLATILITY_CONFIG.items():
        report.append(f"## {config['description']}")
        report.append(f"- 分类代码: {vol_class}")
        report.append(f"- ATR止损倍数: {config['atr_multiplier']}")
        report.append(f"- EMA周期: {config['ema_fast']}/{config['ema_slow']}")
        report.append(f"- 最大仓位: {config['max_position']:.0%}")
        report.append(f"- 追踪止损: {'启用' if config['trailing_stop'] else '禁用'}")
        report.append(f"- 包含股票: {', '.join(config['symbols'])}")
        report.append("")
    
    report.append("## 核心特性")
    report.append("- 动态止损: 高波动3倍ATR / 中波动2倍ATR / 低波动1.5倍ATR")
    report.append("- 大盘过滤: 沪深300(sh000300) EMA50趋势向上才允许买入")
    report.append("- 追踪止损: 盈利达1倍ATR后启动0.8倍ATR移动止损")
    report.append("- 自适应仓位: 低波动45% / 中波动35% / 高波动25%")
    
    return "\n".join(report)


if __name__ == "__main__":
    print(get_stock_classification_report())
