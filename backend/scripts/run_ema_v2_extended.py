#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EMA V2 扩展回测脚本 - 使用TDX数据源
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

# 内联必要的类和枚举
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
    
    description = "EMA突破 + ATR动态止损"
    
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
        self.trade_history = []
        self.win_count = 0
        self.loss_count = 0
    
    def initialize(self, data: pd.DataFrame):
        """计算指标"""
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
        
        self._data = df
        self._initialized = True
    
    def generate_signals(self, data: pd.DataFrame) -> List[StrategySignal]:
        """生成所有交易信号"""
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
            
            # 金叉/死叉判断
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
    """简化版策略回测引擎"""
    
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions = {}
        self.trades = []
        self.equity_curve = []
    
    def _reset(self):
        self.current_capital = self.initial_capital
        self.positions = {}
        self.trades = []
        self.equity_curve = []
    
    def run_backtest(self, strategy, data: pd.DataFrame, start_date=None, end_date=None) -> Dict[str, Any]:
        self._reset()
        
        if start_date:
            data = data[data.index >= start_date]
        if end_date:
            data = data[data.index <= end_date]
        
        if len(data) < 50:
            return {"success": False, "error": "数据不足，至少需要50个交易日"}
        
        try:
            signals = strategy.generate_signals(data)
        except Exception as e:
            return {"success": False, "error": f"生成信号失败: {str(e)}"}
        
        for signal in signals:
            self._execute_signal(signal, data)
        
        performance = self._calculate_performance(data)
        
        return {
            "success": True,
            "strategy_name": strategy.name,
            "backtest_period": {
                "start": str(data.index[0]),
                "end": str(data.index[-1]),
                "days": len(data)
            },
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
        
        self.trades.append({
            "date": str(date),
            "action": "BUY",
            "price": price,
            "shares": shares,
            "cost": total_cost,
            "capital_after": self.current_capital
        })
    
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
            "date": str(date),
            "action": "SELL",
            "price": price,
            "shares": shares,
            "revenue": total_revenue,
            "profit": profit,
            "profit_pct": profit_pct,
            "capital_after": self.current_capital
        })
        
        position["shares"] = 0
        position["cost"] = 0
    
    def _calculate_max_drawdown(self, equity_curve):
        if not equity_curve:
            return 0
        peak = equity_curve[0]
        max_dd = 0
        for value in equity_curve:
            if value > peak:
                peak = value
            dd = (peak - value) / peak
            if dd > max_dd:
                max_dd = dd
        return max_dd
    
    def _calculate_performance(self, data: pd.DataFrame) -> Dict[str, Any]:
        if not self.trades:
            return {
                "total_return": 0,
                "total_return_pct": 0,
                "win_rate": 0,
                "total_trades": 0
            }
        
        total_return = self.current_capital - self.initial_capital
        total_return_pct = total_return / self.initial_capital
        
        sell_trades = [t for t in self.trades if t.get("action") == "SELL"]
        profitable_trades = [t for t in sell_trades if t.get("profit", 0) > 0]
        win_rate = len(profitable_trades) / len(sell_trades) if sell_trades else 0
        
        profits = [t["profit"] for t in sell_trades if "profit" in t]
        avg_profit = np.mean(profits) if profits else 0
        
        profit_pcts = [t["profit_pct"] for t in sell_trades if "profit_pct" in t]
        avg_profit_pct = np.mean(profit_pcts) if profit_pcts else 0
        
        equity_curve = [self.initial_capital]
        for trade in self.trades:
            if "capital_after" in trade:
                equity_curve.append(trade["capital_after"])
        max_drawdown = self._calculate_max_drawdown(equity_curve)
        
        if len(profit_pcts) > 1:
            returns = np.array(profit_pcts)
            sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
        else:
            sharpe = 0
        
        return {
            "total_return": total_return,
            "total_return_pct": total_return_pct,
            "final_capital": self.current_capital,
            "win_rate": win_rate,
            "total_trades": len(self.trades),
            "buy_trades": len([t for t in self.trades if t["action"] == "BUY"]),
            "sell_trades": len(sell_trades),
            "profitable_trades": len(profitable_trades),
            "avg_profit": avg_profit,
            "avg_profit_pct": avg_profit_pct,
            "max_drawdown": max_drawdown,
            "sharpe_ratio": sharpe
        }


# 参数组合测试
PARAM_COMBINATIONS = [
    {"ema_fast": 5, "ema_slow": 30, "atr_multiplier": 2.0},
    {"ema_fast": 5, "ema_slow": 60, "atr_multiplier": 2.0},
    {"ema_fast": 5, "ema_slow": 120, "atr_multiplier": 2.0},
    {"ema_fast": 10, "ema_slow": 30, "atr_multiplier": 2.0},
    {"ema_fast": 10, "ema_slow": 60, "atr_multiplier": 2.0},
    {"ema_fast": 10, "ema_slow": 120, "atr_multiplier": 2.0},
    {"ema_fast": 20, "ema_slow": 60, "atr_multiplier": 2.0},
    {"ema_fast": 20, "ema_slow": 120, "atr_multiplier": 2.0},
    {"ema_fast": 8, "ema_slow": 25, "atr_multiplier": 2.0},
]

# 新增股票列表 (8只)
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
    """从TDX获取股票数据"""
    try:
        provider = get_tdx_native_provider()
        
        # 获取日线数据 (kline_type=9 表示日线)
        # 获取1200天的数据（约5年）
        data = provider.get_kline_with_retry(stock_code, kline_type=9, count=1200)
        
        if not data or len(data) < 50:
            print(f"  ❌ TDX数据不足 ({len(data) if data else 0} 条)")
            return None
        
        # 转换为DataFrame
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df.sort_index(inplace=True)
        
        # 过滤2020-2024年数据
        df = df[(df.index >= '2020-01-01') & (df.index <= '2024-12-31')]
        
        if len(df) < 50:
            print(f"  ❌ 过滤后数据不足 ({len(df)} 条)")
            return None
        
        print(f"  ✅ TDX数据获取成功 ({len(df)} 条)")
        return df
        
    except Exception as e:
        print(f"  ❌ TDX获取失败: {e}")
        return None

def save_stock_data(stock_code: str, df: pd.DataFrame):
    """保存股票数据到缓存"""
    output_file = DATA_DIR / f"{stock_code}_20200101_20241231.csv"
    df.to_csv(output_file)
    return output_file

def load_stock_data(filepath: Path) -> pd.DataFrame:
    """加载股票数据"""
    df = pd.read_csv(filepath)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    df.sort_index(inplace=True)
    return df

def run_single_backtest(stock_code: str, data: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
    """运行单个参数组合回测"""
    
    config = StrategyConfig(
        strategy_id=f"ema_v2_{params['ema_fast']}_{params['ema_slow']}",
        name=f"EMA V2 ({params['ema_fast']}/{params['ema_slow']})",
        parameters=params,
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
            "final_capital": perf.get("final_capital", INITIAL_CAPITAL),
            "win_rate": perf.get("win_rate", 0),
            "sharpe_ratio": perf.get("sharpe_ratio", 0),
            "max_drawdown": perf.get("max_drawdown", 0),
            "total_trades": perf.get("total_trades", 0),
            "profitable_trades": perf.get("profitable_trades", 0),
            "avg_profit_pct": perf.get("avg_profit_pct", 0),
        }
    else:
        return {
            "params": params,
            "success": False,
            "error": result.get("error", "未知错误")
        }

def run_stock_backtests(stock_code: str, stock_name: str, industry: str) -> Dict[str, Any]:
    """对单个股票运行所有参数组合回测"""
    
    print(f"\n{'='*60}")
    print(f"📊 开始回测: {stock_code} {stock_name} ({industry})")
    print(f"{'='*60}")
    
    # 尝试从TDX获取数据
    data = get_stock_data_from_tdx(stock_code)
    
    if data is None:
        # 尝试从缓存读取
        cache_file = DATA_DIR / f"{stock_code}_20200101_20241231.csv"
        if cache_file.exists():
            try:
                data = load_stock_data(cache_file)
                print(f"  ✅ 从缓存加载数据 ({len(data)} 条)")
            except Exception as e:
                print(f"  ❌ 缓存加载失败: {e}")
                return {"stock_code": stock_code, "stock_name": stock_name, "industry": industry, "success": False, "error": "无可用数据"}
        else:
            return {"stock_code": stock_code, "stock_name": stock_name, "industry": industry, "success": False, "error": "无可用数据"}
    else:
        # 保存到缓存
        save_stock_data(stock_code, data)
    
    print(f"📅 时间范围: {data.index[0].strftime('%Y-%m-%d')} ~ {data.index[-1].strftime('%Y-%m-%d')}")
    
    # 运行所有参数组合
    results = []
    for params in PARAM_COMBINATIONS:
        param_desc = f"EMA{params['ema_fast']}/{params['ema_slow']}"
        print(f"  测试参数: {param_desc}...", end=" ", flush=True)
        
        result = run_single_backtest(stock_code, data, params)
        results.append(result)
        
        if result["success"]:
            print(f"✅ 收益={result['total_return_pct']:.2%}, 胜率={result['win_rate']:.1%}, 夏普={result['sharpe_ratio']:.2f}")
        else:
            print(f"❌ 失败: {result.get('error', '未知错误')}")
    
    # 找出最佳参数
    successful = [r for r in results if r["success"]]
    if successful:
        best_by_return = max(successful, key=lambda x: x["total_return_pct"])
        best_by_sharpe = max(successful, key=lambda x: x["sharpe_ratio"])
        
        return {
            "stock_code": stock_code,
            "stock_name": stock_name,
            "industry": industry,
            "success": True,
            "data_period": {
                "start": data.index[0].strftime('%Y-%m-%d'),
                "end": data.index[-1].strftime('%Y-%m-%d'),
                "days": len(data)
            },
            "all_results": results,
            "best_by_return": {
                "params": best_by_return["params"],
                "total_return_pct": best_by_return["total_return_pct"],
                "win_rate": best_by_return["win_rate"],
                "sharpe_ratio": best_by_return["sharpe_ratio"],
                "max_drawdown": best_by_return["max_drawdown"],
                "total_trades": best_by_return["total_trades"]
            },
            "best_by_sharpe": {
                "params": best_by_sharpe["params"],
                "total_return_pct": best_by_sharpe["total_return_pct"],
                "win_rate": best_by_sharpe["win_rate"],
                "sharpe_ratio": best_by_sharpe["sharpe_ratio"],
                "max_drawdown": best_by_sharpe["max_drawdown"],
                "total_trades": best_by_sharpe["total_trades"]
            }
        }
    else:
        return {
            "stock_code": stock_code,
            "stock_name": stock_name,
            "industry": industry,
            "success": False,
            "error": "所有参数组合均失败"
        }

def main():
    """主函数"""
    print("🚀 EMA V2 策略扩展回测 - 新增8只股票 (TDX数据源)")
    print(f"📁 数据目录: {DATA_DIR}")
    print(f"📊 测试参数组合: {len(PARAM_COMBINATIONS)} 种")
    print(f"📈 新增测试股票: {len(EXTENDED_STOCKS)} 只")
    
    # 创建结果目录
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 测试TDX连接
    print(f"\n{'='*60}")
    print("🔗 测试TDX连接...")
    print(f"{'='*60}")
    
    try:
        provider = get_tdx_native_provider()
        if provider.is_available():
            print("✅ TDX连接成功")
        else:
            print("⚠️ TDX连接失败，将尝试使用缓存数据")
    except Exception as e:
        print(f"⚠️ TDX初始化失败: {e}")
    
    # 运行回测
    print(f"\n{'='*60}")
    print("📊 运行EMA V2回测")
    print(f"{'='*60}")
    
    all_results = []
    for stock_code, stock_name, industry in EXTENDED_STOCKS:
        result = run_stock_backtests(stock_code, stock_name, industry)
        all_results.append(result)
        
        if result.get("success"):
            # 保存单个股票结果
            result_file = RESULTS_DIR / f"{stock_code}_ema_v2_results.json"
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"💾 结果已保存: {result_file}")
    
    # 生成报告
    print(f"\n{'='*60}")
    print("📋 生成扩展回测报告")
    print(f"{'='*60}")
    
    # 加载原有7只股票的结果用于对比
    original_detail = {}
    try:
        with open(project_root / "ema_v2_results.json", 'r', encoding='utf-8') as f:
            original_detail = json.load(f)
    except:
        pass
    
    # 生成报告
    from ema_v2_report_generator import generate_extended_report
    report = generate_extended_report(all_results, original_detail)
    
    report_file = RESULTS_DIR / "ema_v2_extended_report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"✅ 报告已保存: {report_file}")
    
    # 输出摘要
    successful = [r for r in all_results if r.get("success")]
    print(f"\n{'='*60}")
    print("📊 扩展回测完成摘要")
    print(f"{'='*60}")
    print(f"✅ 成功: {len(successful)}/{len(all_results)} 只股票")
    print(f"📁 结果目录: {RESULTS_DIR}")
    
    if successful:
        returns = [r["best_by_return"]["total_return_pct"] for r in successful]
        print(f"📈 新增股票平均收益: {np.mean(returns):.2%}")
        print(f"📉 新增股票收益范围: {min(returns):.2%} ~ {max(returns):.2%}")
    
    print("\n" + "="*60)
    print("✅ 扩展回测任务完成!")
    print("="*60)

if __name__ == "__main__":
    main()
