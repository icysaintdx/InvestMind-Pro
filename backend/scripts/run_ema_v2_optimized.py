#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EMA V2.1 优化版回测脚本
- 动态止损参数（按股票波动率分类）
- 大盘趋势过滤（沪深300 EMA50）
- 对比原EMA V2策略效果
"""

import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import akshare as ak

# 添加项目路径
project_root = Path("/home/icysaintdx/.openclaw/workspace-investmindpro/InvestMindPro")
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

# 导入股票分类配置
from strategies.ema_breakout_v2_optimized import (
    get_stock_volatility_class, 
    STOCK_VOLATILITY_CONFIG,
    get_stock_classification_report
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


class EMABreakoutV2OptimizedBacktester:
    """EMA V2.1 优化版回测引擎（带动态止损和大盘过滤）"""
    
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
        
    def fetch_data(self, start_date: str = "20200101", end_date: str = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """获取个股和大盘数据"""
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")
        
        print(f"📊 获取 {self.symbol} 数据...")
        
        # 获取个股数据
        if self.symbol.startswith('6'):
            stock_code = f"{self.symbol}.SH"
        else:
            stock_code = f"{self.symbol}.SZ"
        
        df_stock = ak.stock_zh_a_hist(
            symbol=self.symbol,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq"
        )
        df_stock.columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'amount', 
                           'amplitude', 'pct_change', 'change', 'turnover']
        df_stock['date'] = pd.to_datetime(df_stock['date'])
        df_stock = df_stock.sort_values('date').reset_index(drop=True)
        
        # 获取沪深300数据（大盘趋势）
        print(f"📈 获取沪深300数据...")
        df_market = ak.index_zh_a_hist(symbol="000300", period="daily",
                                       start_date=start_date, end_date=end_date)
        df_market.columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'amount', 
                            'amplitude', 'pct_change', 'change', 'turnover']
        df_market['date'] = pd.to_datetime(df_market['date'])
        df_market = df_market.sort_values('date').reset_index(drop=True)
        
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
        
        # 大盘指标
        mdf = df_market.copy()
        mdf['ema'] = mdf['close'].ewm(span=self.market_ema_period).mean()
        mdf['trend_up'] = mdf['close'] > mdf['ema']
        
        return df, mdf
    
    def generate_signal(self, idx: int, df: pd.DataFrame, mdf: pd.DataFrame) -> StrategySignal:
        """生成交易信号"""
        if idx < max(self.ema_slow, self.market_ema_period):
            return StrategySignal(SignalType.HOLD, 0.0, df['close'].iloc[idx], reason="初始化中")
        
        bar = df.iloc[idx]
        price = float(bar['close'])
        
        if pd.isna(bar.get('ema_fast')) or pd.isna(bar.get('atr')):
            return StrategySignal(SignalType.HOLD, 0.0, price, reason="指标计算中")
        
        # 金叉/死叉判断
        ema_fast = bar['ema_fast']
        ema_slow = bar['ema_slow']
        ema_fast_prev = df['ema_fast'].iloc[idx-1]
        ema_slow_prev = df['ema_slow'].iloc[idx-1]
        
        golden_cross = (ema_fast > ema_slow) and (ema_fast_prev <= ema_slow_prev)
        death_cross = (ema_fast < ema_slow) and (ema_fast_prev >= ema_slow_prev)
        
        trend_up = ema_fast > ema_slow
        trend_down = ema_fast < ema_slow
        rsi = bar.get('rsi', 50)
        atr = bar['atr']
        
        # 大盘趋势检查
        market_trend_up = mdf['trend_up'].iloc[idx] if idx < len(mdf) else True
        
        # ===== 买入逻辑 =====
        if self.position == 0:
            if golden_cross and trend_up and rsi < 70:
                if self.market_filter_enabled and not market_trend_up:
                    return StrategySignal(
                        SignalType.HOLD, 0.0, price,
                        reason=f"个股金叉但大盘趋势向下，观望"
                    )
                
                stop_loss = price - self.atr_multiplier * atr
                take_profit = price + 2 * (price - stop_loss)
                
                return StrategySignal(
                    SignalType.BUY, 0.75, price,
                    stop_loss=round(stop_loss, 2),
                    take_profit=round(take_profit, 2),
                    position_size=0.2,
                    reason=f"EMA{self.ema_fast}/{self.ema_slow}金叉 | {self.vol_config['description']} | ATR{self.atr_multiplier}倍止损",
                    metadata={'market_trend_up': market_trend_up}
                )
        
        # ===== 卖出逻辑 =====
        elif self.position > 0:
            # 条件1：死叉
            if death_cross:
                return StrategySignal(
                    SignalType.SELL, 0.8, price,
                    reason="EMA死叉，趋势反转"
                )
            
            # 条件2：跌破EMA快
            if price < ema_fast and trend_down:
                return StrategySignal(
                    SignalType.SELL, 0.7, price,
                    reason="跌破EMA，止损离场"
                )
            
            # 条件3：触及ATR止损
            if self.stop_loss_price > 0 and price <= self.stop_loss_price:
                return StrategySignal(
                    SignalType.SELL, 0.9, price,
                    reason=f"触及ATR{self.atr_multiplier}倍止损 ({self.stop_loss_price:.2f})"
                )
        
        return StrategySignal(
            SignalType.HOLD, 0.3, price, reason="等待信号",
            metadata={'market_trend_up': market_trend_up}
        )
    
    def execute_signal(self, signal: StrategySignal, date: datetime, price: float):
        """执行交易信号"""
        if signal.signal_type == SignalType.BUY and self.position == 0:
            shares = int(self.cash * signal.position_size / price / 100) * 100
            if shares >= 100:
                cost = shares * price * 1.0005  # 含手续费
                if cost <= self.cash:
                    self.cash -= cost
                    self.holdings = shares
                    self.position = 1
                    self.entry_price = price
                    self.stop_loss_price = signal.stop_loss if signal.stop_loss else price * 0.95
                    
                    self.trades.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'action': 'BUY',
                        'price': price,
                        'shares': shares,
                        'amount': shares * price,
                        'stop_loss': self.stop_loss_price,
                        'reason': signal.reason
                    })
                    return True
        
        elif signal.signal_type == SignalType.SELL and self.position > 0:
            proceeds = self.holdings * price * 0.9995  # 含手续费
            profit = proceeds - (self.holdings * self.entry_price)
            profit_pct = profit / (self.holdings * self.entry_price) * 100
            
            self.trades.append({
                'date': date.strftime('%Y-%m-%d'),
                'action': 'SELL',
                'price': price,
                'shares': self.holdings,
                'amount': proceeds,
                'profit': profit,
                'profit_pct': profit_pct,
                'reason': signal.reason
            })
            
            self.cash += proceeds
            self.holdings = 0
            self.position = 0
            self.entry_price = 0
            self.stop_loss_price = 0
            return True
        
        return False
    
    def run_backtest(self, start_date: str = "20200101", end_date: str = None) -> Dict:
        """运行回测"""
        print(f"\n{'='*60}")
        print(f"🚀 EMA V2.1优化版回测: {self.symbol}")
        print(f"📊 配置: {self.vol_config['description']}")
        print(f"📈 EMA周期: {self.ema_fast}/{self.ema_slow}")
        print(f"🛑 ATR倍数: {self.atr_multiplier}")
        print(f"🌐 大盘过滤: {'启用' if self.market_filter_enabled else '禁用'}")
        print(f"{'='*60}\n")
        
        # 获取数据
        df_stock, df_market = self.fetch_data(start_date, end_date)
        df, mdf = self.calculate_indicators(df_stock, df_market)
        
        # 回测循环
        for idx in range(len(df)):
            date = df['date'].iloc[idx]
            price = df['close'].iloc[idx]
            
            # 生成信号
            signal = self.generate_signal(idx, df, mdf)
            
            # 执行信号
            executed = self.execute_signal(signal, date, price)
            
            # 记录持仓市值
            equity = self.cash + self.holdings * price
            self.equity_curve.append({
                'date': date,
                'equity': equity,
                'price': price,
                'position': self.position
            })
            
            if executed:
                print(f"  {date.strftime('%Y-%m-%d')} {signal.signal_type.value:4} @ {price:.2f} - {signal.reason[:60]}...")
        
        return self.calculate_metrics(df)
    
    def calculate_metrics(self, df: pd.DataFrame) -> Dict:
        """计算回测指标"""
        equity_df = pd.DataFrame(self.equity_curve)
        if len(equity_df) == 0:
            return {}
        
        final_equity = equity_df['equity'].iloc[-1]
        total_return = (final_equity - self.initial_capital) / self.initial_capital * 100
        
        # 年化收益
        days = (equity_df['date'].iloc[-1] - equity_df['date'].iloc[0]).days
        years = max(days / 365, 0.01)
        annual_return = ((final_equity / self.initial_capital) ** (1/years) - 1) * 100
        
        # 计算回撤
        equity_df['peak'] = equity_df['equity'].cummax()
        equity_df['drawdown'] = (equity_df['equity'] - equity_df['peak']) / equity_df['peak'] * 100
        max_drawdown = equity_df['drawdown'].min()
        
        # 夏普比率（简化）
        equity_df['daily_return'] = equity_df['equity'].pct_change()
        sharpe = 0
        if equity_df['daily_return'].std() > 0:
            sharpe = (equity_df['daily_return'].mean() / equity_df['daily_return'].std()) * np.sqrt(252)
        
        # 交易统计
        buy_trades = [t for t in self.trades if t['action'] == 'BUY']
        sell_trades = [t for t in self.trades if t['action'] == 'SELL']
        
        winning_trades = [t for t in sell_trades if t.get('profit', 0) > 0]
        losing_trades = [t for t in sell_trades if t.get('profit', 0) <= 0]
        
        win_rate = len(winning_trades) / len(sell_trades) * 100 if sell_trades else 0
        
        # 止损统计
        stop_loss_trades = [t for t in sell_trades if '止损' in t.get('reason', '')]
        
        metrics = {
            'symbol': self.symbol,
            'volatility_class': self.vol_config['class'],
            'config': self.vol_config['description'],
            'ema_periods': f"{self.ema_fast}/{self.ema_slow}",
            'atr_multiplier': self.atr_multiplier,
            'market_filter': self.market_filter_enabled,
            'total_return_pct': round(total_return, 2),
            'annual_return_pct': round(annual_return, 2),
            'sharpe_ratio': round(sharpe, 2),
            'max_drawdown_pct': round(max_drawdown, 2),
            'win_rate_pct': round(win_rate, 1),
            'total_trades': len(sell_trades),
            'stop_loss_triggered': len(stop_loss_trades),
            'initial_capital': self.initial_capital,
            'final_equity': round(final_equity, 2),
            'trades': self.trades,
            'equity_curve': [{'date': e['date'].strftime('%Y-%m-%d'), 'equity': e['equity']} 
                            for e in self.equity_curve]
        }
        
        return metrics


def run_optimized_backtest(symbol: str, start_date: str = "20200101", end_date: str = None) -> Dict:
    """运行单只股票优化版回测"""
    backtester = EMABreakoutV2OptimizedBacktester(symbol)
    return backtester.run_backtest(start_date, end_date)


def run_batch_optimized_backtest(symbols: List[str], start_date: str = "20200101", end_date: str = None) -> Dict:
    """批量运行优化版回测"""
    print(get_stock_classification_report())
    
    results = []
    for symbol in symbols:
        try:
            metrics = run_optimized_backtest(symbol, start_date, end_date)
            results.append(metrics)
        except Exception as e:
            print(f"❌ {symbol} 回测失败: {e}")
            import traceback
            traceback.print_exc()
    
    # 生成汇总报告
    summary = {
        'test_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'symbols': symbols,
        'total_stocks': len(results),
        'results': results
    }
    
    # 保存结果
    output_dir = project_root / 'backend' / 'data' / 'backtest_results' / 'optimized'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 保存JSON
    json_path = output_dir / f'ema_v2_optimized_results_{timestamp}.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n💾 结果已保存: {json_path}")
    
    # 生成Markdown报告
    md_lines = [
        "# EMA V2.1 优化版回测报告",
        f"\n**测试时间**: {timestamp}",
        f"**股票数量**: {len(results)}只",
        "\n## 配置说明",
        "- 动态止损参数：高波动股票3倍ATR，中波动2倍ATR，低波动1.5倍ATR",
        "- 大盘过滤：沪深300 EMA50趋势向上时才允许买入",
        "- 自适应EMA周期：不同波动率股票使用不同EMA周期",
        "\n## 股票分类",
    ]
    
    for vol_class, config in STOCK_VOLATILITY_CONFIG.items():
        md_lines.append(f"\n### {config['description']}")
        md_lines.append(f"- ATR倍数: {config['atr_multiplier']}")
        md_lines.append(f"- EMA周期: {config['ema_fast']}/{config['ema_slow']}")
        md_lines.append(f"- 股票: {', '.join(config['symbols'])}")
    
    md_lines.extend(["\n## 回测结果汇总", "\n| 股票 | 分类 | 总收益 | 年化收益 | 夏普比率 | 最大回撤 | 胜率 | 交易次数 | 止损次数 |"])
    md_lines.append("|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")
    
    for r in sorted(results, key=lambda x: x.get('total_return_pct', 0), reverse=True):
        md_lines.append(
            f"| {r['symbol']} | {r['config']} | {r['total_return_pct']}% | "
            f"{r['annual_return_pct']}% | {r['sharpe_ratio']} | {r['max_drawdown_pct']}% | "
            f"{r['win_rate_pct']}% | {r['total_trades']} | {r['stop_loss_triggered']} |"
        )
    
    md_path = output_dir / f'ema_v2_optimized_report_{timestamp}.md'
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))
    print(f"💾 报告已保存: {md_path}")
    
    return summary


if __name__ == "__main__":
    # 测试股票列表
    test_symbols = ['300750', '000858', '600519', '000001', '002594', '601318', '600036']
    
    print("="*60)
    print("EMA V2.1 优化版批量回测")
    print("="*60)
    
    results = run_batch_optimized_backtest(test_symbols)
    
    print("\n" + "="*60)
    print("✅ 批量回测完成!")
    print("="*60)
