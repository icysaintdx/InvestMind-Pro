#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EMA V2 批量回测 - 修复版引擎
对比原结果，展示止损修复效果
"""

import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

# 添加项目路径
project_root = Path("/home/icysaintdx/.openclaw/workspace-investmindpro/InvestMindPro")
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

@dataclass
class StrategySignal:
    signal_type: SignalType
    confidence: float
    price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    position_size: float = 0.2
    reason: str = ""
    strategy_id: str = ""
    timestamp: Any = None
    metadata: Dict = field(default_factory=dict)

@dataclass
class StrategyConfig:
    strategy_id: str
    name: str
    parameters: Dict = field(default_factory=dict)
    enabled: bool = True

class EMABreakoutV2Strategy:
    """EMA突破策略 V2.0"""
    
    def __init__(self, config: StrategyConfig):
        self.config = config
        self.name = config.name
        self.parameters = config.parameters
        self.ema_fast = self.parameters.get('ema_fast', 8)
        self.ema_slow = self.parameters.get('ema_slow', 25)
        self.atr_period = self.parameters.get('atr_period', 14)
        self.atr_multiplier = self.parameters.get('atr_multiplier', 2.0)
        self._data = None
        self._initialized = False
    
    def initialize(self, data: pd.DataFrame):
        df = data.copy()
        df['ema_fast'] = df['close'].ewm(span=self.ema_fast).mean()
        df['ema_slow'] = df['close'].ewm(span=self.ema_slow).mean()
        
        high_low = df['high'] - df['low']
        high_close = (df['high'] - df['close'].shift()).abs()
        low_close = (df['low'] - df['close'].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = tr.ewm(span=self.atr_period).mean()
        
        delta = df['close'].diff()
        gain = delta.clip(lower=0).ewm(span=14).mean()
        loss = (-delta.clip(upper=0)).ewm(span=14).mean()
        df['rsi'] = 100 - 100 / (1 + gain / (loss + 0.001))
        
        self._data = df
        self._initialized = True
    
    def generate_signals(self, data: pd.DataFrame) -> List[StrategySignal]:
        if not self._initialized:
            self.initialize(data)
        
        signals = []
        for idx in range(1, len(self._data)):
            row = self._data.iloc[idx]
            prev_row = self._data.iloc[idx-1]
            
            if pd.isna(row.get('ema_fast')) or pd.isna(row.get('atr')):
                continue
            
            price = float(row['close'])
            timestamp = self._data.index[idx]
            
            golden_cross = (row['ema_fast'] > row['ema_slow']) and (prev_row['ema_fast'] <= prev_row['ema_slow'])
            death_cross = (row['ema_fast'] < row['ema_slow']) and (prev_row['ema_fast'] >= prev_row['ema_slow'])
            trend_up = row['ema_fast'] > row['ema_slow']
            rsi = row.get('rsi', 50)
            atr = row['atr']
            
            if golden_cross and trend_up and rsi < 70:
                stop_loss = price - self.atr_multiplier * atr
                take_profit = price + 2 * (price - stop_loss)
                signals.append(StrategySignal(
                    signal_type=SignalType.BUY,
                    confidence=0.75,
                    price=price,
                    stop_loss=round(stop_loss, 2),
                    take_profit=round(take_profit, 2),
                    position_size=0.2,
                    reason=f"EMA金叉买入",
                    strategy_id=self.config.strategy_id,
                    timestamp=timestamp
                ))
            elif death_cross:
                signals.append(StrategySignal(
                    signal_type=SignalType.SELL,
                    confidence=0.8,
                    price=price,
                    reason="EMA死叉卖出",
                    strategy_id=self.config.strategy_id,
                    timestamp=timestamp
                ))
        return signals

class StrategyBacktesterWithStopLoss:
    """回测引擎 - 带止损执行"""
    
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions = {}
        self.trades = []
        self.stop_loss_hits = 0
    
    def _reset(self):
        self.current_capital = self.initial_capital
        self.positions = {}
        self.trades = []
        self.stop_loss_hits = 0
    
    def run_backtest(self, strategy, data: pd.DataFrame) -> Dict[str, Any]:
        self._reset()
        
        if len(data) < 50:
            return {"success": False, "error": "数据不足"}
        
        try:
            signals = strategy.generate_signals(data)
            signal_map = {s.timestamp: s for s in signals}
        except Exception as e:
            return {"success": False, "error": f"生成信号失败: {str(e)}"}
        
        for idx in range(len(data)):
            current_date = data.index[idx]
            current_bar = data.iloc[idx]
            
            # 检查止损
            self._check_stop_loss(current_date, current_bar)
            
            # 处理信号
            if current_date in signal_map:
                signal = signal_map[current_date]
                if idx + 1 < len(data):
                    next_date = data.index[idx + 1]
                    next_open = data.iloc[idx + 1]['open']
                    self._execute_signal(signal, next_date, next_open)
        
        return {
            "success": True,
            "performance": self._calculate_performance(),
            "trades": self.trades,
            "stop_loss_hits": self.stop_loss_hits
        }
    
    def _check_stop_loss(self, date, bar):
        for strategy_id, position in self.positions.items():
            if position.get("shares", 0) == 0:
                continue
            stop_loss_price = position.get("stop_loss")
            if stop_loss_price is None:
                continue
            if bar['low'] <= stop_loss_price:
                self._execute_stop_loss(strategy_id, date, stop_loss_price)
    
    def _execute_stop_loss(self, strategy_id, date, stop_price):
        position = self.positions.get(strategy_id)
        if not position or position.get("shares", 0) == 0:
            return
        
        shares = position["shares"]
        revenue = shares * stop_price
        commission = revenue * 0.0003
        stamp_tax = revenue * 0.001
        total_revenue = revenue - commission - stamp_tax
        profit = total_revenue - position["cost"]
        profit_pct = profit / position["cost"] if position["cost"] > 0 else 0
        
        self.current_capital += total_revenue
        self.stop_loss_hits += 1
        
        self.trades.append({
            "date": str(date), "action": "SELL", "type": "STOP_LOSS",
            "price": stop_price, "shares": shares, "revenue": total_revenue,
            "profit": profit, "profit_pct": profit_pct,
            "capital_after": self.current_capital
        })
        
        position["shares"] = 0
        position["cost"] = 0
        position["stop_loss"] = None
    
    def _execute_signal(self, signal, date, execution_price):
        if signal.signal_type == SignalType.BUY:
            self._execute_buy(signal, execution_price, date)
        elif signal.signal_type == SignalType.SELL:
            self._execute_sell(signal, execution_price, date)
    
    def _execute_buy(self, signal, price: float, date):
        position_value = self.current_capital * signal.position_size
        shares = int(position_value / price / 100) * 100
        if shares < 100:
            return
        
        cost = shares * price
        commission = cost * 0.0003
        total_cost = cost + commission
        
        if total_cost > self.current_capital:
            return
        
        if signal.strategy_id not in self.positions:
            self.positions[signal.strategy_id] = {"shares": 0, "cost": 0, "stop_loss": None}
        
        position = self.positions[signal.strategy_id]
        position["shares"] += shares
        position["cost"] += total_cost
        position["stop_loss"] = signal.stop_loss
        self.current_capital -= total_cost
        
        self.trades.append({
            "date": str(date), "action": "BUY", "type": "SIGNAL",
            "price": price, "shares": shares, "cost": total_cost,
            "stop_loss": signal.stop_loss, "capital_after": self.current_capital
        })
    
    def _execute_sell(self, signal, price: float, date):
        position = self.positions.get(signal.strategy_id)
        if not position or position.get("shares", 0) == 0:
            return
        
        shares = position["shares"]
        revenue = shares * price
        commission = revenue * 0.0003
        stamp_tax = revenue * 0.001
        total_revenue = revenue - commission - stamp_tax
        profit = total_revenue - position["cost"]
        profit_pct = profit / position["cost"] if position["cost"] > 0 else 0
        
        self.current_capital += total_revenue
        self.trades.append({
            "date": str(date), "action": "SELL", "type": "SIGNAL",
            "price": price, "shares": shares, "revenue": total_revenue,
            "profit": profit, "profit_pct": profit_pct,
            "capital_after": self.current_capital
        })
        
        position["shares"] = 0
        position["cost"] = 0
        position["stop_loss"] = None
    
    def _calculate_performance(self) -> Dict[str, Any]:
        if not self.trades:
            return {"total_return_pct": 0, "win_rate": 0, "total_trades": 0}
        
        total_return_pct = (self.current_capital - self.initial_capital) / self.initial_capital
        sell_trades = [t for t in self.trades if t.get("action") == "SELL"]
        profitable = [t for t in sell_trades if t.get("profit", 0) > 0]
        win_rate = len(profitable) / len(sell_trades) if sell_trades else 0
        
        return {
            "total_return_pct": total_return_pct,
            "final_capital": self.current_capital,
            "win_rate": win_rate,
            "total_trades": len(self.trades),
            "sell_trades": len(sell_trades),
            "stop_loss_hits": self.stop_loss_hits
        }

# 配置
DATA_DIR = project_root / "backend/data/backtest_cache"
STOCKS = [
    ("000333", "美的集团"),
    ("000651", "格力电器"),
    ("000858", "五粮液"),
    ("600276", "恒瑞医药"),
    ("600519", "贵州茅台"),
    ("601318", "中国平安"),
    ("601888", "中国中免"),
]

PARAMS = {"ema_fast": 5, "ema_slow": 30, "atr_multiplier": 2.0}

def load_data(stock_code: str) -> pd.DataFrame:
    filepath = DATA_DIR / f"{stock_code}_20200101_20241231.csv"
    df = pd.read_csv(filepath)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    df.sort_index(inplace=True)
    return df

def run_backtest(stock_code: str, stock_name: str) -> Dict:
    df = load_data(stock_code)
    
    config = StrategyConfig(
        strategy_id=f"ema_v2_{stock_code}",
        name=f"EMA V2 {stock_code}",
        parameters=PARAMS
    )
    
    strategy = EMABreakoutV2Strategy(config)
    backtester = StrategyBacktesterWithStopLoss(initial_capital=100000.0)
    result = backtester.run_backtest(strategy, df)
    
    if result["success"]:
        perf = result["performance"]
        return {
            "stock_code": stock_code,
            "stock_name": stock_name,
            "success": True,
            **perf
        }
    return {"stock_code": stock_code, "stock_name": stock_name, "success": False}

def main():
    print("="*70)
    print("EMA V2 批量回测 - 修复版引擎（带止损执行）")
    print("="*70)
    print(f"参数: EMA{PARAMS['ema_fast']}/{PARAMS['ema_slow']}, ATR×{PARAMS['atr_multiplier']}")
    print(f"股票数: {len(STOCKS)}")
    print("="*70)
    
    results = []
    for stock_code, stock_name in STOCKS:
        print(f"\n📊 回测 {stock_code} {stock_name}...", end=" ")
        result = run_backtest(stock_code, stock_name)
        results.append(result)
        
        if result["success"]:
            print(f"✅ 收益={result['total_return_pct']:.2%} 胜率={result['win_rate']:.1%} 止损={result.get('stop_loss_hits', 0)}次")
        else:
            print(f"❌ 失败")
    
    # 生成汇总
    print("\n" + "="*70)
    print("📈 回测结果汇总")
    print("="*70)
    print(f"{'代码':<8} {'名称':<10} {'总收益':>10} {'胜率':>8} {'交易':>6} {'止损':>6}")
    print("-"*70)
    
    successful = [r for r in results if r["success"]]
    for r in sorted(successful, key=lambda x: x['total_return_pct'], reverse=True):
        print(f"{r['stock_code']:<8} {r['stock_name']:<10} {r['total_return_pct']:>+9.2%} {r['win_rate']:>7.1%} {r.get('sell_trades', 0):>6} {r.get('stop_loss_hits', 0):>6}")
    
    if successful:
        avg_return = np.mean([r['total_return_pct'] for r in successful])
        avg_winrate = np.mean([r['win_rate'] for r in successful])
        total_stops = sum([r.get('stop_loss_hits', 0) for r in successful])
        print("-"*70)
        print(f"{'平均':<8} {'':<10} {avg_return:>+9.2%} {avg_winrate:>7.1%} {'':>6} {total_stops:>6}")
    
    # 保存结果
    output = {
        "timestamp": datetime.now().isoformat(),
        "parameters": PARAMS,
        "results": results
    }
    
    output_file = project_root / "ema_v2_fixed_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 结果已保存: {output_file}")

if __name__ == "__main__":
    main()
