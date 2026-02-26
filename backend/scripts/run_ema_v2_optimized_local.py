#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EMA V2.1 优化版回测脚本 - 本地数据版本
- 使用本地缓存数据避免网络问题
- 动态止损参数（按股票波动率分类）
- 大盘趋势过滤（沪深300 EMA50）
"""

import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

# 添加项目路径
project_root = Path("/home/icysaintdx/.openclaw/workspace-investmindpro/InvestMindPro")
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

# 导入股票分类配置
from strategies.ema_breakout_v2_optimized import (
    get_stock_volatility_class, 
    STOCK_VOLATILITY_CONFIG
)


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
    metadata: Dict = field(default_factory=dict)


class EMABreakoutV2OptimizedBacktesterLocal:
    """EMA V2.1 优化版回测引擎（本地数据版）"""
    
    def __init__(self, symbol: str, initial_capital: float = 100000.0):
        self.symbol = symbol
        self.initial_capital = initial_capital
        
        # 获取股票波动率分类配置
        self.vol_config = get_stock_volatility_class(symbol)
        
        # 动态参数
        self.ema_fast = self.vol_config['ema_fast']
        self.ema_slow = self.vol_config['ema_slow']
        self.atr_period = 14
        self.atr_multiplier = self.vol_config['atr_multiplier']
        
        # 大盘过滤
        self.market_filter_enabled = True
        self.market_ema_period = 50
        
        # 回测状态
        self.position = 0
        self.cash = initial_capital
        self.holdings = 0
        self.entry_price = 0.0
        self.stop_loss_price = 0.0
        self.trades = []
        self.equity_curve = []
        self.signals_history = []
        
    def load_local_data(self, start_date: str = "20200101", end_date: str = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """加载本地缓存数据"""
        cache_dir = project_root / "backend" / "data" / "backtest_cache"
        
        # 加载个股数据
        stock_file = cache_dir / f"{self.symbol}_20200101_20241231.csv"
        if not stock_file.exists():
            raise FileNotFoundError(f"未找到 {self.symbol} 的本地数据文件")
        
        print(f"📊 加载 {self.symbol} 本地数据...")
        df_stock = pd.read_csv(stock_file)
        df_stock['date'] = pd.to_datetime(df_stock['date'])
        df_stock = df_stock.sort_values('date').reset_index(drop=True)
        
        # 过滤日期范围
        if start_date:
            start_dt = pd.to_datetime(start_date)
            df_stock = df_stock[df_stock['date'] >= start_dt]
        if end_date:
            end_dt = pd.to_datetime(end_date)
            df_stock = df_stock[df_stock['date'] <= end_dt]
        
        # 加载沪深300数据（使用600276作为市场代理，如果没有000300）
        market_file = cache_dir / "600519_20200101_20241231.csv"  # 用茅台作为大盘股代理
        if market_file.exists():
            df_market = pd.read_csv(market_file)
            df_market['date'] = pd.to_datetime(df_market['date'])
            df_market = df_market.sort_values('date').reset_index(drop=True)
            # 同步日期范围
            df_market = df_market[df_market['date'].isin(df_stock['date'])]
        else:
            # 如果没有大盘数据，创建一个虚拟的
            df_market = df_stock.copy()
            df_market['trend_up'] = True
        
        return df_stock, df_market
    
    def calculate_indicators(self, df_stock: pd.DataFrame, df_market: pd.DataFrame):
        """计算技术指标"""
        # 个股指标
        df = df_stock.copy()
        df['ema_fast'] = df['close'].ewm(span=self.ema_fast).mean()
        df['ema_slow'] = df['close'].ewm(span=self.ema_slow).mean()
        
        # ATR
        high_low = df['high'] - df['low']
        high_close = (df['high'] - df['close'].shift()).abs()
        low_close = (df['low'] - df['close'].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = tr.ewm(span=self.atr_period).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = delta.clip(lower=0).ewm(span=14).mean()
        loss = (-delta.clip(upper=0)).ewm(span=14).mean()
        df['rsi'] = 100 - 100 / (1 + gain / (loss + 0.001))
        
        # 大盘指标 - 使用茅台作为大盘股代理
        mdf = df_market.copy()
        mdf['ema'] = mdf['close'].ewm(span=self.market_ema_period).mean()
        mdf['trend_up'] = mdf['close'] > mdf['ema']
        
        return df, mdf
    
    def generate_signal(self, idx: int, df: pd.DataFrame, mdf: pd.DataFrame) -> StrategySignal:
        """生成交易信号（含大盘过滤）"""
        if idx < max(self.ema_slow, self.market_ema_period):
            return StrategySignal(SignalType.HOLD, 0.0, df['close'].iloc[idx], reason="初始化中")
        
        bar = df.iloc[idx]
        prev_bar = df.iloc[idx - 1]
        
        # 大盘趋势检查
        market_trend_up = mdf['trend_up'].iloc[idx] if idx < len(mdf) else True
        
        # EMA金叉/死叉
        golden_cross = prev_bar['ema_fast'] <= prev_bar['ema_slow'] and bar['ema_fast'] > bar['ema_slow']
        death_cross = prev_bar['ema_fast'] >= prev_bar['ema_slow'] and bar['ema_fast'] < bar['ema_slow']
        
        # RSI过滤
        rsi = bar['rsi']
        
        # ATR止损计算
        atr = bar['atr']
        stop_loss = bar['close'] - self.atr_multiplier * atr
        
        # 买入信号（加大盘过滤）
        if golden_cross and rsi < 70:
            if not market_trend_up and self.market_filter_enabled:
                return StrategySignal(
                    SignalType.HOLD, 0.3, bar['close'],
                    reason=f"个股金叉但大盘趋势向下({self.market_ema_period}日EMA)，观望",
                    metadata={'golden_cross': True, 'market_filter_blocked': True}
                )
            
            confidence = min(0.5 + (70 - rsi) / 100, 0.9)
            return StrategySignal(
                SignalType.BUY, confidence, bar['close'],
                stop_loss=stop_loss,
                reason=f"EMA{self.ema_fast}/{self.ema_slow}金叉+RSI{rsi:.1f}+大盘向上，ATR倍数{self.atr_multiplier}",
                metadata={'ema_fast': self.ema_fast, 'ema_slow': self.ema_slow, 
                         'atr_multiplier': self.atr_multiplier, 'market_trend_up': market_trend_up}
            )
        
        # 卖出信号
        if death_cross or (self.position > 0 and bar['close'] < self.stop_loss_price):
            reason = "EMA死叉" if death_cross else f"止损触发({self.stop_loss_price:.2f})"
            return StrategySignal(
                SignalType.SELL, 0.8, bar['close'],
                reason=reason,
                metadata={'death_cross': death_cross, 'stop_loss_triggered': bar['close'] < self.stop_loss_price}
            )
        
        return StrategySignal(SignalType.HOLD, 0.0, bar['close'], reason="无信号")
    
    def run_backtest(self, start_date: str = "20200101", end_date: str = None) -> Dict:
        """运行回测"""
        print(f"\n{'='*60}")
        print(f"📈 EMA V2.1 优化版回测: {self.symbol}")
        print(f"   波动率分类: {self.vol_config['class']}")
        print(f"   参数: EMA{self.ema_fast}/{self.ema_slow}, ATR×{self.atr_multiplier}")
        print(f"   大盘过滤: {'开启' if self.market_filter_enabled else '关闭'}")
        print(f"{'='*60}")
        
        # 加载数据
        df_stock, df_market = self.load_local_data(start_date, end_date)
        df, mdf = self.calculate_indicators(df_stock, df_market)
        
        # 回测循环
        for i in range(len(df)):
            current_price = df['close'].iloc[i]
            current_date = df['date'].iloc[i]
            
            # 检查止损
            if self.position > 0 and current_price < self.stop_loss_price:
                self._execute_sell(i, df, mdf, stop_loss=True)
            
            # 生成信号
            signal = self.generate_signal(i, df, mdf)
            self.signals_history.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'signal': signal.signal_type.value,
                'price': signal.price,
                'reason': signal.reason
            })
            
            # 执行交易
            if signal.signal_type == SignalType.BUY and self.position == 0:
                self._execute_buy(i, df, signal)
            elif signal.signal_type == SignalType.SELL and self.position > 0:
                self._execute_sell(i, df, mdf)
            
            # 记录权益
            equity = self.cash + self.holdings * current_price
            self.equity_curve.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'equity': equity,
                'price': current_price
            })
        
        # 计算指标
        return self._calculate_metrics(df)
    
    def _execute_buy(self, idx: int, df: pd.DataFrame, signal: StrategySignal):
        """执行买入"""
        price = df['close'].iloc[idx]
        shares = int(self.cash * signal.position_size / price)
        
        if shares > 0:
            cost = shares * price
            self.cash -= cost
            self.holdings = shares
            self.position = 1
            self.entry_price = price
            self.stop_loss_price = signal.stop_loss
            
            self.trades.append({
                'type': 'buy',
                'date': df['date'].iloc[idx].strftime('%Y-%m-%d'),
                'price': price,
                'shares': shares,
                'amount': cost,
                'stop_loss': signal.stop_loss,
                'reason': signal.reason
            })
            print(f"  📥 买入 {self.symbol} @ {price:.2f} × {shares}股, 止损@{signal.stop_loss:.2f}")
    
    def _execute_sell(self, idx: int, df: pd.DataFrame, mdf: pd.DataFrame, stop_loss: bool = False):
        """执行卖出"""
        price = df['close'].iloc[idx]
        revenue = self.holdings * price
        
        # 计算盈亏
        pnl = revenue - (self.holdings * self.entry_price)
        pnl_pct = (price - self.entry_price) / self.entry_price * 100
        
        self.trades.append({
            'type': 'sell',
            'date': df['date'].iloc[idx].strftime('%Y-%m-%d'),
            'price': price,
            'shares': self.holdings,
            'amount': revenue,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'stop_loss': stop_loss
        })
        
        emoji = "🛑" if stop_loss else "📤"
        print(f"  {emoji} 卖出 {self.symbol} @ {price:.2f} × {self.holdings}股, 盈亏: {pnl:+.2f} ({pnl_pct:+.2f}%)")
        
        self.cash += revenue
        self.holdings = 0
        self.position = 0
        self.entry_price = 0
        self.stop_loss_price = 0
    
    def _calculate_metrics(self, df: pd.DataFrame) -> Dict:
        """计算回测指标"""
        final_equity = self.cash + self.holdings * df['close'].iloc[-1]
        total_return = (final_equity - self.initial_capital) / self.initial_capital * 100
        
        # 计算年化收益
        days = len(df)
        years = days / 252
        annual_return = ((final_equity / self.initial_capital) ** (1/years) - 1) * 100 if years > 0 else 0
        
        # 计算最大回撤
        equity_values = [e['equity'] for e in self.equity_curve]
        max_drawdown = 0
        peak = equity_values[0]
        for equity in equity_values:
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak * 100
            max_drawdown = max(max_drawdown, drawdown)
        
        # 统计交易
        buy_trades = [t for t in self.trades if t['type'] == 'buy']
        sell_trades = [t for t in self.trades if t['type'] == 'sell']
        
        win_trades = [t for t in sell_trades if t.get('pnl', 0) > 0]
        loss_trades = [t for t in sell_trades if t.get('pnl', 0) <= 0]
        stop_loss_trades = [t for t in sell_trades if t.get('stop_loss', False)]
        
        win_rate = len(win_trades) / len(sell_trades) * 100 if sell_trades else 0
        
        # 计算Sharpe比率
        if len(equity_values) > 1:
            equity_series = pd.Series(equity_values)
            returns = equity_series.pct_change().dropna()
            sharpe = (returns.mean() / returns.std() * np.sqrt(252)) if returns.std() != 0 else 0
        else:
            sharpe = 0
        
        return {
            'symbol': self.symbol,
            'volatility_class': self.vol_config['class'],
            'ema_fast': self.ema_fast,
            'ema_slow': self.ema_slow,
            'atr_multiplier': self.atr_multiplier,
            'initial_capital': self.initial_capital,
            'final_equity': final_equity,
            'total_return': total_return,
            'annual_return': annual_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe,
            'total_trades': len(sell_trades),
            'win_trades': len(win_trades),
            'loss_trades': len(loss_trades),
            'stop_loss_count': len(stop_loss_trades),
            'win_rate': win_rate,
            'trades': self.trades,
            'equity_curve': self.equity_curve,
            'signals_history': self.signals_history
        }


def run_optimized_backtest_local(symbol: str, start_date: str = "20200101", end_date: str = None) -> Dict:
    """运行单个股票的优化版回测"""
    backtester = EMABreakoutV2OptimizedBacktesterLocal(symbol)
    return backtester.run_backtest(start_date, end_date)


def run_batch_optimized_backtest(symbols: List[str], start_date: str = "20200101", end_date: str = None):
    """批量回测多个股票"""
    results = []
    
    print("\n" + "="*70)
    print("🚀 EMA V2.1 优化版批量回测")
    print("="*70)
    print(f"📅 回测区间: {start_date} - {end_date or '最新'}")
    print(f"📊 股票数量: {len(symbols)}")
    print(f"🎯 动态止损: 按波动率分类 (高/中/低)")
    print(f"📈 大盘过滤: 开启")
    print("="*70)
    
    for symbol in symbols:
        try:
            metrics = run_optimized_backtest_local(symbol, start_date, end_date)
            results.append(metrics)
        except Exception as e:
            print(f"❌ {symbol} 回测失败: {e}")
    
    # 生成汇总报告
    generate_summary_report(results, start_date, end_date)
    return results


def generate_summary_report(results: List[Dict], start_date: str, end_date: str):
    """生成汇总报告"""
    if not results:
        print("❌ 没有成功的回测结果")
        return
    
    print("\n" + "="*70)
    print("📊 EMA V2.1 优化版批量回测汇总")
    print("="*70)
    
    # 按收益排序
    sorted_results = sorted(results, key=lambda x: x['total_return'], reverse=True)
    
    print(f"\n{'排名':<4} {'股票':<8} {'分类':<8} {'EMA参数':<10} {'总收益':<10} {'胜率':<8} {'交易次数':<8}")
    print("-"*70)
    
    for i, r in enumerate(sorted_results, 1):
        symbol = r['symbol']
        vol_class = r['volatility_class']
        ema_param = f"EMA{r['ema_fast']}/{r['ema_slow']}"
        atr = f"ATR×{r['atr_multiplier']}"
        ret = f"{r['total_return']:+.2f}%"
        win = f"{r['win_rate']:.1f}%"
        trades = r['total_trades']
        
        print(f"{i:<4} {symbol:<8} {vol_class:<8} {ema_param:<10} {ret:<10} {win:<8} {trades:<8}")
    
    # 统计摘要
    returns = [r['total_return'] for r in results]
    avg_return = sum(returns) / len(returns)
    
    print("\n" + "-"*70)
    print(f"📈 平均总收益: {avg_return:+.2f}%")
    print(f"📉 收益范围: {min(returns):+.2f}% ~ {max(returns):+.2f}%")
    print(f"🎯 总交易次数: {sum(r['total_trades'] for r in results)}")
    print(f"🛑 总止损次数: {sum(r['stop_loss_count'] for r in results)}")
    
    # 按波动率分类统计
    print("\n📊 按波动率分类统计:")
    for vol_class in ['high_volatility', 'medium_volatility', 'low_volatility']:
        class_results = [r for r in results if r['volatility_class'] == vol_class]
        if class_results:
            avg_ret = sum(r['total_return'] for r in class_results) / len(class_results)
            total_trades = sum(r['total_trades'] for r in class_results)
            print(f"  • {vol_class}: 平均收益 {avg_ret:+.2f}%, 总交易 {total_trades}次")
    
    # 保存JSON结果
    output_dir = project_root / "backtest_results"
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 保存详细结果
    json_file = output_dir / f"ema_v2_1_optimized_results_{timestamp}.json"
    with open(json_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n💾 详细结果已保存: {json_file}")
    
    # 生成Markdown报告
    md_file = output_dir / f"ema_v2_1_optimized_report_{timestamp}.md"
    with open(md_file, 'w') as f:
        f.write("# EMA V2.1 优化版回测报告\n\n")
        f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**回测区间**: {start_date} - {end_date or '最新'}\n\n")
        f.write("## 参数配置\n\n")
        f.write("| 波动率分类 | ATR倍数 | EMA周期 | 股票示例 |\n")
        f.write("|:---|:---:|:---:|:---|\n")
        f.write("| 高波动 | 3.0 | 10/30 | 宁德时代、比亚迪、中国中免 |\n")
        f.write("| 中波动 | 2.0 | 8/25 | 五粮液、美的、格力 |\n")
        f.write("| 低波动 | 1.5 | 5/20 | 茅台、平安、招行、恒瑞 |\n")
        f.write("\n## 回测结果汇总\n\n")
        f.write(f"| 排名 | 股票 | 分类 | EMA参数 | 总收益 | 年化 | 最大回撤 | 胜率 | 交易 |\n")
        f.write(f"|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|\n")
        
        for i, r in enumerate(sorted_results, 1):
            f.write(f"| {i} | {r['symbol']} | {r['volatility_class'][:4]} | ")
            f.write(f"EMA{r['ema_fast']}/{r['ema_slow']} | ")
            f.write(f"{r['total_return']:+.2f}% | {r['annual_return']:+.2f}% | ")
            f.write(f"{r['max_drawdown']:.2f}% | {r['win_rate']:.1f}% | {r['total_trades']} |\n")
        
        f.write(f"\n## 统计摘要\n\n")
        f.write(f"- **平均总收益**: {avg_return:+.2f}%\n")
        f.write(f"- **收益范围**: {min(returns):+.2f}% ~ {max(returns):+.2f}%\n")
        f.write(f"- **总交易次数**: {sum(r['total_trades'] for r in results)}\n")
        f.write(f"- **总止损次数**: {sum(r['stop_loss_count'] for r in results)}\n\n")
    
    print(f"📝 报告已保存: {md_file}")


if __name__ == "__main__":
    # 可用股票列表（基于本地缓存）
    available_symbols = ['000333', '000651', '000858', '600276', '600519', '601318', '601888']
    
    print("🚀 EMA V2.1 优化版回测 - 本地数据模式")
    print(f"📊 可用股票: {', '.join(available_symbols)}")
    
    # 批量回测
    run_batch_optimized_backtest(available_symbols, "20200101", "20241231")
