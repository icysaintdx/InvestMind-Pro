#!/usr/bin/env python3
"""
InvestMindPro 模拟盘交易引擎

功能:
1. 每日收盘后获取数据
2. 使用优化后的EMA V2参数生成交易信号
3. 模拟下单并记录持仓
4. 生成每日交易报告

使用方法:
    python3 paper_trading.py --init          # 初始化模拟盘
    python3 paper_trading.py --run           # 执行今日交易
    python3 paper_trading.py --report        # 生成报告
    python3 paper_trading.py --status        # 查看当前状态
"""

import os
import sys
import json
import argparse
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from strategies.ema_v2 import EMAV2Strategy, MarketRegime


class PositionStatus(Enum):
    """持仓状态"""
    EMPTY = "empty"      # 空仓
    HOLDING = "holding"  # 持仓


@dataclass
class Position:
    """持仓记录"""
    symbol: str
    status: PositionStatus
    entry_price: float = 0.0
    entry_date: str = ""
    shares: int = 0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    unrealized_pnl: float = 0.0
    
    def to_dict(self):
        return {
            'symbol': self.symbol,
            'status': self.status.value,
            'entry_price': self.entry_price,
            'entry_date': self.entry_date,
            'shares': self.shares,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'unrealized_pnl': self.unrealized_pnl
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            symbol=data['symbol'],
            status=PositionStatus(data['status']),
            entry_price=data.get('entry_price', 0.0),
            entry_date=data.get('entry_date', ''),
            shares=data.get('shares', 0),
            stop_loss=data.get('stop_loss', 0.0),
            take_profit=data.get('take_profit', 0.0),
            unrealized_pnl=data.get('unrealized_pnl', 0.0)
        )


@dataclass
class Trade:
    """交易记录"""
    trade_id: str
    symbol: str
    date: str
    action: str  # BUY, SELL
    price: float
    shares: int
    reason: str  # 交易原因
    realized_pnl: float = 0.0
    
    def to_dict(self):
        return asdict(self)


class PaperTradingEngine:
    """模拟盘交易引擎"""
    
    # 从优化结果加载的参数
    OPTIMIZED_PARAMS = {
        '000001': {'name': '平安银行', 'fast_ema': 7, 'slow_ema': 20, 'atr_period': 14, 'atr_multiplier': 1.0, 'market_filter': True},
        '000333': {'name': '美的集团', 'fast_ema': 3, 'slow_ema': 40, 'atr_period': 14, 'atr_multiplier': 1.5, 'market_filter': True},
        '000568': {'name': '泸州老窖', 'fast_ema': 15, 'slow_ema': 40, 'atr_period': 14, 'atr_multiplier': 2.5, 'market_filter': True},
        '000651': {'name': '格力电器', 'fast_ema': 10, 'slow_ema': 30, 'atr_period': 14, 'atr_multiplier': 1.5, 'market_filter': True},
        '000858': {'name': '五粮液', 'fast_ema': 8, 'slow_ema': 35, 'atr_period': 14, 'atr_multiplier': 2.5, 'market_filter': True},
        '002415': {'name': '海康威视', 'fast_ema': 12, 'slow_ema': 15, 'atr_period': 14, 'atr_multiplier': 3.0, 'market_filter': True},
        '002460': {'name': '赣锋锂业', 'fast_ema': 3, 'slow_ema': 35, 'atr_period': 14, 'atr_multiplier': 1.5, 'market_filter': True},
        '002594': {'name': '比亚迪', 'fast_ema': 7, 'slow_ema': 30, 'atr_period': 14, 'atr_multiplier': 2.5, 'market_filter': True},
        '002714': {'name': '牧原股份', 'fast_ema': 12, 'slow_ema': 20, 'atr_period': 14, 'atr_multiplier': 2.0, 'market_filter': True},
        '300014': {'name': '亿纬锂能', 'fast_ema': 5, 'slow_ema': 40, 'atr_period': 14, 'atr_multiplier': 2.0, 'market_filter': True},
        '300033': {'name': '同花顺', 'fast_ema': 15, 'slow_ema': 35, 'atr_period': 14, 'atr_multiplier': 1.0, 'market_filter': True},
        '300124': {'name': '汇川技术', 'fast_ema': 3, 'slow_ema': 40, 'atr_period': 14, 'atr_multiplier': 1.5, 'market_filter': True},
        '300750': {'name': '宁德时代', 'fast_ema': 3, 'slow_ema': 35, 'atr_period': 14, 'atr_multiplier': 2.0, 'market_filter': True},
        '600036': {'name': '招商银行', 'fast_ema': 7, 'slow_ema': 25, 'atr_period': 14, 'atr_multiplier': 1.0, 'market_filter': True},
        '600276': {'name': '恒瑞医药', 'fast_ema': 7, 'slow_ema': 40, 'atr_period': 14, 'atr_multiplier': 1.5, 'market_filter': True},
        '600519': {'name': '贵州茅台', 'fast_ema': 15, 'slow_ema': 40, 'atr_period': 14, 'atr_multiplier': 1.5, 'market_filter': True},
        '600887': {'name': '伊利股份', 'fast_ema': 15, 'slow_ema': 40, 'atr_period': 14, 'atr_multiplier': 3.0, 'market_filter': True},  # 优化后: +12.86%
        '600900': {'name': '长江电力', 'fast_ema': 12, 'slow_ema': 20, 'atr_period': 14, 'atr_multiplier': 1.0, 'market_filter': True},
        '601012': {'name': '隆基绿能', 'fast_ema': 12, 'slow_ema': 18, 'atr_period': 14, 'atr_multiplier': 1.5, 'market_filter': True},
        '601288': {'name': '农业银行', 'fast_ema': 12, 'slow_ema': 30, 'atr_period': 14, 'atr_multiplier': 1.0, 'market_filter': True},
        '601318': {'name': '中国平安', 'fast_ema': 10, 'slow_ema': 50, 'atr_period': 14, 'atr_multiplier': 1.5, 'market_filter': True, 'note': '加长周期版本，测试收益+55.14%'},
        # '601398': {'name': '工商银行', 'fast_ema': 10, 'slow_ema': 35, 'atr_period': 14, 'atr_multiplier': 1.0, 'market_filter': True},  # REMOVED: 低波动银行股不适合EMA趋势策略
        '601888': {'name': '中国中免', 'fast_ema': 15, 'slow_ema': 40, 'atr_period': 14, 'atr_multiplier': 2.0, 'market_filter': True},
        # 负收益股票优化参数 (2025-02-27)
        '603993': {'name': '洛阳钼业', 'fast_ema': 10, 'slow_ema': 40, 'atr_period': 14, 'atr_multiplier': 2.5, 'market_filter': True, 'note': '保守优化，改善+7.14%'},
        '603288': {'name': '海天味业', 'fast_ema': 10, 'slow_ema': 40, 'atr_period': 14, 'atr_multiplier': 2.0, 'market_filter': True, 'note': '延长周期，改善+50.06%'},
    }
    
    def __init__(self, initial_capital: float = 1000000.0):
        """
        初始化模拟盘
        
        Args:
            initial_capital: 初始资金 (默认100万)
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.daily_values: List[dict] = []
        
        # 数据路径
        self.data_dir = Path(__file__).parent.parent / "data"
        self.results_dir = Path(__file__).parent.parent / "results"
        self.paper_trading_dir = self.results_dir / "paper_trading"
        self.paper_trading_dir.mkdir(exist_ok=True)
        
        # 状态文件
        self.state_file = self.paper_trading_dir / "portfolio_state.json"
        self.trades_file = self.paper_trading_dir / "trades.json"
        self.daily_values_file = self.paper_trading_dir / "daily_values.json"
        
        # 加载状态
        self._load_state()
    
    def _load_state(self):
        """加载持仓状态"""
        if self.state_file.exists():
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
                self.current_capital = state.get('current_capital', self.initial_capital)
                self.positions = {
                    symbol: Position.from_dict(pos)
                    for symbol, pos in state.get('positions', {}).items()
                }
        
        if self.trades_file.exists():
            with open(self.trades_file, 'r', encoding='utf-8') as f:
                trades_data = json.load(f)
                self.trades = [Trade(**t) for t in trades_data]
        
        if self.daily_values_file.exists():
            with open(self.daily_values_file, 'r', encoding='utf-8') as f:
                self.daily_values = json.load(f)
    
    def _save_state(self):
        """保存持仓状态"""
        state = {
            'current_capital': self.current_capital,
            'positions': {
                symbol: pos.to_dict()
                for symbol, pos in self.positions.items()
            },
            'last_update': datetime.now().isoformat()
        }
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        
        with open(self.trades_file, 'w', encoding='utf-8') as f:
            json.dump([t.to_dict() for t in self.trades], f, ensure_ascii=False, indent=2)
        
        with open(self.daily_values_file, 'w', encoding='utf-8') as f:
            json.dump(self.daily_values, f, ensure_ascii=False, indent=2)
    
    def load_stock_data(self, symbol: str, days: int = 120) -> pd.DataFrame:
        """
        加载股票数据
        
        Args:
            symbol: 股票代码
            days: 获取天数
            
        Returns:
            DataFrame with OHLCV data
        """
        file_path = self.data_dir / f"{symbol}.csv"
        if not file_path.exists():
            print(f"警告: 未找到 {symbol} 的数据文件")
            return pd.DataFrame()
        
        df = pd.read_csv(file_path)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # 只取最近N天
        df = df.tail(days).copy()
        
        return df
    
    def check_signals(self, symbol: str) -> tuple:
        """
        检查交易信号
        
        Returns:
            (signal, price, stop_loss) 信号类型，当前价格，止损价
        """
        if symbol not in self.OPTIMIZED_PARAMS:
            print(f"警告: {symbol} 没有优化参数")
            return None, 0, 0
        
        params = self.OPTIMIZED_PARAMS[symbol]
        df = self.load_stock_data(symbol)
        
        if df.empty or len(df) < 50:
            return None, 0, 0
        
        # 使用优化参数创建策略
        strategy_params = {
            'fast_ema': params['fast_ema'],
            'slow_ema': params['slow_ema'],
            'atr_period': params['atr_period'],
            'atr_multiplier': params['atr_multiplier'],
            'market_filter': params['market_filter']
        }
        strategy = EMAV2Strategy(params=strategy_params)
        
        # 计算指标
        df['fast_ema'] = strategy.calculate_ema(df['close'], params['fast_ema'])
        df['slow_ema'] = strategy.calculate_ema(df['close'], params['slow_ema'])
        df['atr'] = strategy.calculate_atr(df)
        
        # 获取最新数据
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        current_price = latest['close']
        atr = latest['atr']
        
        # 检查大盘过滤
        if params['market_filter']:
            market_df = self.load_stock_data('000300', days=60)  # 沪深300
            if not market_df.empty:
                market_df['ema20'] = market_df['close'].ewm(span=20, adjust=False).mean()
                market_latest = market_df.iloc[-1]
                is_bull_market = market_latest['close'] > market_latest['ema20']
                
                if not is_bull_market:
                    return 'MARKET_FILTER_BLOCK', current_price, 0
        
        # 生成信号
        prev_fast = prev['fast_ema']
        prev_slow = prev['slow_ema']
        curr_fast = latest['fast_ema']
        curr_slow = latest['slow_ema']
        
        # 金叉 (买入信号)
        if prev_fast <= prev_slow and curr_fast > curr_slow:
            stop_loss = current_price - params['atr_multiplier'] * atr
            return 'BUY', current_price, stop_loss
        
        # 死叉 (卖出信号)
        if prev_fast >= prev_slow and curr_fast < curr_slow:
            return 'SELL', current_price, 0
        
        return None, current_price, 0
    
    def execute_trade(self, symbol: str, signal: str, price: float, stop_loss: float = 0):
        """
        执行交易
        
        Args:
            symbol: 股票代码
            signal: 信号类型 (BUY, SELL)
            price: 价格
            stop_loss: 止损价
        """
        date_str = datetime.now().strftime('%Y-%m-%d')
        trade_id = f"{symbol}_{date_str}_{len(self.trades)}"
        
        if signal == 'BUY':
            # 计算可买入股数 (每只股票最多投入资金的10%)
            max_position_value = self.current_capital * 0.10
            shares = int(max_position_value / price / 100) * 100  # 100股整数
            
            if shares < 100:
                print(f"资金不足，无法买入 {symbol}")
                return
            
            cost = shares * price * 1.0003  # 含手续费
            
            if cost > self.current_capital:
                print(f"资金不足，无法买入 {symbol}")
                return
            
            # 更新资金
            self.current_capital -= cost
            
            # 创建持仓
            self.positions[symbol] = Position(
                symbol=symbol,
                status=PositionStatus.HOLDING,
                entry_price=price,
                entry_date=date_str,
                shares=shares,
                stop_loss=stop_loss
            )
            
            # 记录交易
            trade = Trade(
                trade_id=trade_id,
                symbol=symbol,
                date=date_str,
                action='BUY',
                price=price,
                shares=shares,
                reason=f"EMA金叉买入 | 止损: {stop_loss:.2f}"
            )
            self.trades.append(trade)
            
            print(f"✅ 买入 {symbol}: {shares}股 @ {price:.2f}, 止损: {stop_loss:.2f}")
            
        elif signal == 'SELL':
            if symbol not in self.positions or self.positions[symbol].status != PositionStatus.HOLDING:
                return
            
            position = self.positions[symbol]
            shares = position.shares
            
            # 计算盈亏
            realized_pnl = shares * (price - position.entry_price)
            
            # 更新资金
            proceeds = shares * price * 0.9997  # 扣除手续费
            self.current_capital += proceeds
            
            # 更新持仓状态
            position.status = PositionStatus.EMPTY
            position.unrealized_pnl = realized_pnl
            
            # 记录交易
            trade = Trade(
                trade_id=trade_id,
                symbol=symbol,
                date=date_str,
                action='SELL',
                price=price,
                shares=shares,
                reason="EMA死叉卖出",
                realized_pnl=realized_pnl
            )
            self.trades.append(trade)
            
            pnl_pct = (realized_pnl / (shares * position.entry_price)) * 100
            print(f"✅ 卖出 {symbol}: {shares}股 @ {price:.2f}, 盈亏: {realized_pnl:+.2f} ({pnl_pct:+.2f}%)")
    
    def check_stop_loss(self):
        """检查止损"""
        date_str = datetime.now().strftime('%Y-%m-%d')
        
        for symbol, position in self.positions.items():
            if position.status != PositionStatus.HOLDING:
                continue
            
            df = self.load_stock_data(symbol, days=5)
            if df.empty:
                continue
            
            current_price = df['close'].iloc[-1]
            
            # 触发止损
            if current_price <= position.stop_loss:
                trade_id = f"{symbol}_{date_str}_SL_{len(self.trades)}"
                
                realized_pnl = position.shares * (current_price - position.entry_price)
                proceeds = position.shares * current_price * 0.9997
                self.current_capital += proceeds
                
                position.status = PositionStatus.EMPTY
                
                trade = Trade(
                    trade_id=trade_id,
                    symbol=symbol,
                    date=date_str,
                    action='SELL',
                    price=current_price,
                    shares=position.shares,
                    reason=f"止损触发 | 止损价: {position.stop_loss:.2f}",
                    realized_pnl=realized_pnl
                )
                self.trades.append(trade)
                
                pnl_pct = (realized_pnl / (position.shares * position.entry_price)) * 100
                print(f"⚠️ 止损 {symbol}: {position.shares}股 @ {current_price:.2f}, 盈亏: {realized_pnl:+.2f} ({pnl_pct:+.2f}%)")
    
    def run_daily(self):
        """执行每日交易"""
        print(f"\n{'='*60}")
        print(f"📅 模拟盘交易 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        print(f"💰 当前资金: {self.current_capital:,.2f}")
        print(f"📊 持仓数量: {sum(1 for p in self.positions.values() if p.status == PositionStatus.HOLDING)}\n")
        
        # 1. 检查止损
        print("🔍 检查止损...")
        self.check_stop_loss()
        
        # 2. 生成交易信号
        print("\n📈 生成交易信号...")
        for symbol in self.OPTIMIZED_PARAMS.keys():
            signal, price, stop_loss = self.check_signals(symbol)
            
            if signal == 'BUY':
                # 检查是否已有持仓
                if symbol in self.positions and self.positions[symbol].status == PositionStatus.HOLDING:
                    continue
                self.execute_trade(symbol, signal, price, stop_loss)
                
            elif signal == 'SELL':
                self.execute_trade(symbol, signal, price)
        
        # 3. 计算总资产
        total_value = self.current_capital
        for symbol, position in self.positions.items():
            if position.status == PositionStatus.HOLDING:
                df = self.load_stock_data(symbol, days=5)
                if not df.empty:
                    current_price = df['close'].iloc[-1]
                    position_value = position.shares * current_price
                    total_value += position_value
                    position.unrealized_pnl = position.shares * (current_price - position.entry_price)
        
        # 4. 记录每日净值
        self.daily_values.append({
            'date': datetime.now().strftime('%Y-%m-%d'),
            'cash': self.current_capital,
            'total_value': total_value,
            'positions_value': total_value - self.current_capital
        })
        
        # 5. 保存状态
        self._save_state()
        
        print(f"\n💵 总资产: {total_value:,.2f}")
        total_return = (total_value - self.initial_capital) / self.initial_capital * 100
        print(f"📊 总收益: {total_return:+.2f}%")
        print(f"\n{'='*60}\n")
    
    def generate_report(self):
        """生成交易报告"""
        print(f"\n{'='*60}")
        print(f"📋 模拟盘交易报告")
        print(f"{'='*60}\n")
        
        # 基本统计
        print(f"初始资金: {self.initial_capital:,.2f}")
        print(f"当前资金: {self.current_capital:,.2f}")
        
        total_value = self.current_capital
        for symbol, position in self.positions.items():
            if position.status == PositionStatus.HOLDING:
                df = self.load_stock_data(symbol, days=5)
                if not df.empty:
                    current_price = df['close'].iloc[-1]
                    total_value += position.shares * current_price
        
        print(f"总资产: {total_value:,.2f}")
        total_return = (total_value - self.initial_capital) / self.initial_capital * 100
        print(f"总收益率: {total_return:+.2f}%\n")
        
        # 持仓列表
        print("📦 当前持仓:")
        print("-" * 60)
        for symbol, position in self.positions.items():
            if position.status == PositionStatus.HOLDING:
                df = self.load_stock_data(symbol, days=5)
                if not df.empty:
                    current_price = df['close'].iloc[-1]
                    pnl = position.shares * (current_price - position.entry_price)
                    pnl_pct = (current_price - position.entry_price) / position.entry_price * 100
                    print(f"  {symbol}: {position.shares}股 | 成本: {position.entry_price:.2f} | "
                          f"现价: {current_price:.2f} | 盈亏: {pnl:+.2f} ({pnl_pct:+.2f}%)")
        
        # 交易历史
        print(f"\n📜 最近10笔交易:")
        print("-" * 60)
        for trade in self.trades[-10:]:
            pnl_str = f" | 盈亏: {trade.realized_pnl:+.2f}" if trade.realized_pnl != 0 else ""
            print(f"  {trade.date} | {trade.action} {trade.symbol} | "
                  f"{trade.shares}股 @ {trade.price:.2f}{pnl_str}")
        
        print(f"\n{'='*60}\n")
    
    def get_status(self):
        """获取当前状态"""
        print(f"\n{'='*60}")
        print(f"📊 模拟盘当前状态")
        print(f"{'='*60}\n")
        
        print(f"💰 现金: {self.current_capital:,.2f}")
        
        total_value = self.current_capital
        holding_count = 0
        for symbol, position in self.positions.items():
            if position.status == PositionStatus.HOLDING:
                holding_count += 1
                df = self.load_stock_data(symbol, days=5)
                if not df.empty:
                    current_price = df['close'].iloc[-1]
                    total_value += position.shares * current_price
        
        print(f"📈 总资产: {total_value:,.2f}")
        print(f"📦 持仓数: {holding_count}/{len(self.OPTIMIZED_PARAMS)}")
        
        total_return = (total_value - self.initial_capital) / self.initial_capital * 100
        print(f"📊 总收益: {total_return:+.2f}%")
        
        print(f"\n📝 总交易次数: {len(self.trades)}")
        print(f"📅 最后更新: {self.state_file.stat().st_mtime if self.state_file.exists() else 'N/A'}")
        
        print(f"\n{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description='InvestMindPro 模拟盘交易引擎')
    parser.add_argument('--init', action='store_true', help='初始化模拟盘')
    parser.add_argument('--run', action='store_true', help='执行今日交易')
    parser.add_argument('--report', action='store_true', help='生成报告')
    parser.add_argument('--status', action='store_true', help='查看状态')
    parser.add_argument('--capital', type=float, default=1000000.0, help='初始资金 (默认100万)')
    
    args = parser.parse_args()
    
    engine = PaperTradingEngine(initial_capital=args.capital)
    
    if args.init:
        print("✅ 模拟盘已初始化")
        engine.get_status()
    elif args.run:
        engine.run_daily()
    elif args.report:
        engine.generate_report()
    elif args.status:
        engine.get_status()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
