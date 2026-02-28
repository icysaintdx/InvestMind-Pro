#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EMA V2 扩展回测脚本 - 使用TDX数据源 (修复版)
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

# 导入TDX provider
from backend.dataflows.providers.tdx_native_provider import get_tdx_native_provider

# 配置
DATA_DIR = project_root / "backend/data/backtest_cache"
RESULTS_DIR = project_root / "backend/backtest_results/individual"
INITIAL_CAPITAL = 100000.0

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

class StrategyBacktester:
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions = {}
        self.trades = []
    
    def _reset(self):
        self.current_capital = self.initial_capital
        self.positions = {}
        self.trades = []
    
    def run_backtest(self, strategy, data: pd.DataFrame) -> Dict[str, Any]:
        self._reset()
        
        if len(data) < 50:
            return {"success": False, "error": "数据不足"}
        
        try:
            signals = strategy.generate_signals(data)
        except Exception as e:
            return {"success": False, "error": f"生成信号失败: {str(e)}"}
        
        for signal in signals:
            self._execute_signal(signal, data)
        
        performance = self._calculate_performance()
        
        return {
            "success": True,
            "strategy_name": strategy.name,
            "performance": performance,
            "trades": self.trades
        }
    
    def _execute_signal(self, signal, data: pd.DataFrame):
        signal_date = signal.timestamp
        if signal_date not in data.index:
            return
        
        signal_idx = data.index.get_loc(signal_date)
        if signal_idx + 1 >= len(data):
            return
        
        next_day = data.index[signal_idx + 1]
        execution_price = data.loc[next_day, 'open']
        
        if signal.signal_type == SignalType.BUY:
            self._execute_buy(signal, execution_price, next_day)
        elif signal.signal_type == SignalType.SELL:
            self._execute_sell(signal, execution_price, next_day)
    
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
            self.positions[signal.strategy_id] = {"shares": 0, "cost": 0}
        
        position = self.positions[signal.strategy_id]
        position["shares"] += shares
        position["cost"] += total_cost
        self.current_capital -= total_cost
        
        self.trades.append({"date": str(date), "action": "BUY", "price": price, "shares": shares})
    
    def _execute_sell(self, signal, price: float, date):
        if signal.strategy_id not in self.positions:
            return
        
        position = self.positions[signal.strategy_id]
        if position["shares"] == 0:
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
            "date": str(date), "action": "SELL", "price": price, "shares": shares,
            "profit": profit, "profit_pct": profit_pct
        })
        
        position["shares"] = 0
        position["cost"] = 0
    
    def _calculate_performance(self) -> Dict[str, Any]:
        if not self.trades:
            return {"total_return_pct": 0, "win_rate": 0, "total_trades": 0}
        
        total_return = self.current_capital - self.initial_capital
        total_return_pct = total_return / self.initial_capital
        
        sell_trades = [t for t in self.trades if t.get("action") == "SELL"]
        profitable_trades = [t for t in sell_trades if t.get("profit", 0) > 0]
        win_rate = len(profitable_trades) / len(sell_trades) if sell_trades else 0
        
        return {
            "total_return": total_return,
            "total_return_pct": total_return_pct,
            "final_capital": self.current_capital,
            "win_rate": win_rate,
            "total_trades": len(self.trades),
            "profitable_trades": len(profitable_trades)
        }

# 参数组合
PARAM_COMBINATIONS = [
    {"ema_fast": 5, "ema_slow": 30},
    {"ema_fast": 5, "ema_slow": 60},
    {"ema_fast": 5, "ema_slow": 120},
    {"ema_fast": 10, "ema_slow": 30},
    {"ema_fast": 10, "ema_slow": 60},
    {"ema_fast": 10, "ema_slow": 120},
    {"ema_fast": 20, "ema_slow": 60},
    {"ema_fast": 20, "ema_slow": 120},
    {"ema_fast": 8, "ema_slow": 25},
]

# 新增股票列表
EXTENDED_STOCKS = [
    ("002594", "比亚迪", "科技/新能源"),
    ("300750", "宁德时代", "科技/新能源"),
    ("600887", "伊利股份", "消费/食品饮料"),
    ("002271", "东方雨虹", "消费/建材"),
    ("600436", "片仔癀", "医药"),
    ("000538", "云南白药", "医药"),
    ("600036", "招商银行", "金融/银行"),
    ("601398", "工商银行", "金融/银行"),
]

def get_stock_data_from_tdx(stock_code: str) -> Optional[pd.DataFrame]:
    """从TDX获取股票数据 - 修复版"""
    try:
        provider = get_tdx_native_provider()
        
        # TDX每次最多800条，分2次获取约1600条数据（约6-7年）
        all_data = []
        
        # 第一次获取最新800条
        data1 = provider.get_kline_with_retry(stock_code, kline_type=9, count=800)
        if data1:
            all_data.extend(data1)
        
        # 第二次获取更多历史数据
        data2 = provider.get_kline_with_retry(stock_code, kline_type=9, count=800)
        if data2:
            # 避免重复数据
            dates1 = {d['date'] for d in data1} if data1 else set()
            for d in data2:
                if d['date'] not in dates1:
                    all_data.append(d)
        
        if not all_data or len(all_data) < 50:
            return None
        
        # 转换为DataFrame
        df = pd.DataFrame(all_data)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df.sort_index(inplace=True)
        
        # 过滤2020-2024年数据
        df = df[(df.index >= '2020-01-01') & (df.index <= '2024-12-31')]
        
        if len(df) < 50:
            return None
        
        return df
        
    except Exception as e:
        print(f"  TDX获取失败: {e}")
        return None

def run_single_backtest(stock_code: str, data: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
    config = StrategyConfig(
        strategy_id=f"ema_v2_{params['ema_fast']}_{params['ema_slow']}",
        name=f"EMA V2 ({params['ema_fast']}/{params['ema_slow']})",
        parameters={**params, "atr_multiplier": 2.0},
        enabled=True
    )
    
    strategy = EMABreakoutV2Strategy(config)
    backtester = StrategyBacktester(initial_capital=INITIAL_CAPITAL)
    
    result = backtester.run_backtest(strategy, data)
    
    if result["success"]:
        perf = result["performance"]
        return {
            "params": params,
            "success": True,
            "total_return_pct": perf.get("total_return_pct", 0),
            "win_rate": perf.get("win_rate", 0),
            "total_trades": perf.get("total_trades", 0),
        }
    else:
        return {"params": params, "success": False, "error": result.get("error", "失败")}

def run_stock_backtests(stock_code: str, stock_name: str, industry: str) -> Dict[str, Any]:
    print(f"\n{'='*60}")
    print(f"📊 回测: {stock_code} {stock_name} ({industry})")
    print(f"{'='*60}")
    
    # 从TDX获取数据
    print("  从TDX获取数据...", end=" ")
    data = get_stock_data_from_tdx(stock_code)
    
    if data is None:
        print("❌ 失败")
        return {"stock_code": stock_code, "stock_name": stock_name, "industry": industry, "success": False}
    
    print(f"✅ ({len(data)} 条)")
    print(f"  时间范围: {data.index[0].strftime('%Y-%m-%d')} ~ {data.index[-1].strftime('%Y-%m-%d')}")
    
    # 运行所有参数组合
    results = []
    for params in PARAM_COMBINATIONS:
        result = run_single_backtest(stock_code, data, params)
        results.append(result)
        status = "✅" if result["success"] else "❌"
        print(f"  EMA{params['ema_fast']}/{params['ema_slow']}: {status} 收益={result.get('total_return_pct', 0):.2%}")
    
    # 找出最佳参数
    successful = [r for r in results if r["success"]]
    if successful:
        best = max(successful, key=lambda x: x["total_return_pct"])
        return {
            "stock_code": stock_code, "stock_name": stock_name, "industry": industry, "success": True,
            "data_period": {"start": data.index[0].strftime('%Y-%m-%d'), "end": data.index[-1].strftime('%Y-%m-%d'), "days": len(data)},
            "all_results": results,
            "best_by_return": {
                "params": best["params"], "total_return_pct": best["total_return_pct"],
                "win_rate": best["win_rate"], "total_trades": best["total_trades"]
            }
        }
    
    return {"stock_code": stock_code, "stock_name": stock_name, "industry": industry, "success": False}

def generate_simple_report(all_results: List[Dict]) -> str:
    """生成简化版报告"""
    lines = []
    lines.append("# EMA V2 策略扩展回测报告")
    lines.append("")
    lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    lines.append("## 新增股票概览")
    lines.append("")
    lines.append("| 股票代码 | 股票名称 | 行业 | 状态 |")
    lines.append("|----------|----------|------|------|")
    for code, name, industry in EXTENDED_STOCKS:
        r = next((x for x in all_results if x["stock_code"] == code), None)
        status = "✅ 成功" if r and r.get("success") else "❌ 失败"
        lines.append(f"| {code} | {name} | {industry} | {status} |")
    lines.append("")
    
    successful = [r for r in all_results if r.get("success")]
    if successful:
        lines.append("## 最佳参数汇总")
        lines.append("")
        lines.append("| 股票代码 | 最佳参数 | 总收益 | 胜率 | 交易次数 |")
        lines.append("|----------|----------|--------|------|----------|")
        for r in successful:
            b = r["best_by_return"]
            p = b["params"]
            lines.append(f"| {r['stock_code']} | EMA{p['ema_fast']}/{p['ema_slow']} | {b['total_return_pct']:.2%} | {b['win_rate']:.1%} | {b['total_trades']} |")
        lines.append("")
        
        # 统计
        returns = [r["best_by_return"]["total_return_pct"] for r in successful]
        lines.append("## 统计摘要")
        lines.append("")
        lines.append(f"- 成功回测: {len(successful)}/8 只股票")
        lines.append(f"- 平均收益: {np.mean(returns):.2%}")
        lines.append(f"- 收益中位数: {np.median(returns):.2%}")
        lines.append(f"- 最高收益: {max(returns):.2%}")
        lines.append(f"- 最低收益: {min(returns):.2%}")
        lines.append("")
    
    lines.append("---")
    lines.append("*由 InvestMindPro 自动生成*")
    return "\n".join(lines)

def main():
    print("🚀 EMA V2 策略扩展回测 (TDX修复版)")
    print(f"📈 测试股票: {len(EXTENDED_STOCKS)} 只")
    
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    all_results = []
    for code, name, industry in EXTENDED_STOCKS:
        result = run_stock_backtests(code, name, industry)
        all_results.append(result)
        
        if result.get("success"):
            with open(RESULTS_DIR / f"{code}_ema_v2_results.json", 'w') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
    
    # 生成报告
    report = generate_simple_report(all_results)
    report_file = RESULTS_DIR / "ema_v2_extended_report.md"
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"\n{'='*60}")
    print("✅ 扩展回测完成!")
    print(f"📁 报告: {report_file}")
    successful = [r for r in all_results if r.get("success")]
    print(f"📊 成功: {len(successful)}/8 只股票")
    if successful:
        returns = [r["best_by_return"]["total_return_pct"] for r in successful]
        print(f"📈 平均收益: {np.mean(returns):.2%}")

if __name__ == "__main__":
    main()
