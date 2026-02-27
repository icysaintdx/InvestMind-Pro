#!/usr/bin/env python3
"""
策略对比研究: EMA V2.1 vs MACD vs 混合策略
对比不同策略在相同股票池上的表现
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent.parent))
from strategies.ema_v2 import EMAV2Strategy

@dataclass
class StrategyResult:
    """策略回测结果"""
    strategy_name: str
    symbol: str
    total_return: float
    win_rate: float
    total_trades: int
    max_drawdown: float
    sharpe_ratio: float
    profit_factor: float


class MACDStrategy:
    """
    MACD策略实现
    - 买入: DIF上穿DEA (金叉)
    - 卖出: DIF下穿DEA (死叉)
    """
    
    def __init__(self, fast=12, slow=26, signal=9):
        self.fast = fast
        self.slow = slow
        self.signal = signal
    
    def calculate_macd(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算MACD指标"""
        data = df.copy()
        
        # 计算EMA
        ema_fast = data['close'].ewm(span=self.fast, adjust=False).mean()
        ema_slow = data['close'].ewm(span=self.slow, adjust=False).mean()
        
        # DIF = 快EMA - 慢EMA
        data['dif'] = ema_fast - ema_slow
        
        # DEA = DIF的9日EMA
        data['dea'] = data['dif'].ewm(span=self.signal, adjust=False).mean()
        
        # MACD柱状图 = 2 * (DIF - DEA)
        data['macd_bar'] = 2 * (data['dif'] - data['dea'])
        
        # 金叉/死叉信号
        data['golden_cross'] = (data['dif'] > data['dea']) & (data['dif'].shift(1) <= data['dea'].shift(1))
        data['death_cross'] = (data['dif'] < data['dea']) & (data['dif'].shift(1) >= data['dea'].shift(1))
        
        return data
    
    def run_backtest(self, df: pd.DataFrame, initial_capital: float = 100000.0) -> StrategyResult:
        """执行回测"""
        data = self.calculate_macd(df)
        
        position = 0
        entry_price = 0.0
        trades = []
        equity_curve = [initial_capital]
        current_capital = initial_capital
        
        for i in range(1, len(data)):
            price = data['close'].iloc[i]
            
            if position == 0:  # 空仓
                if data['golden_cross'].iloc[i]:
                    position = 1
                    entry_price = price
                    shares = current_capital / price
                    
            elif position == 1:  # 持仓
                if data['death_cross'].iloc[i]:
                    exit_price = price
                    pnl = (exit_price - entry_price) * shares
                    pnl_pct = (exit_price / entry_price - 1) * 100
                    
                    trades.append({
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct
                    })
                    
                    current_capital += pnl
                    position = 0
                    entry_price = 0.0
            
            equity_curve.append(current_capital)
        
        # 计算指标
        total_return = (current_capital - initial_capital) / initial_capital * 100
        
        if len(trades) > 0:
            winning_trades = [t for t in trades if t['pnl'] > 0]
            win_rate = len(winning_trades) / len(trades) * 100
            
            equity_series = pd.Series(equity_curve)
            rolling_max = equity_series.expanding().max()
            drawdown = (equity_series - rolling_max) / rolling_max * 100
            max_drawdown = drawdown.min()
            
            returns = pd.Series(equity_curve).pct_change().dropna()
            sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() != 0 else 0
            
            gross_profit = sum(t['pnl'] for t in trades if t['pnl'] > 0)
            gross_loss = abs(sum(t['pnl'] for t in trades if t['pnl'] < 0))
            profit_factor = gross_profit / gross_loss if gross_loss != 0 else float('inf')
        else:
            win_rate = 0
            max_drawdown = 0
            sharpe = 0
            profit_factor = 0
        
        return StrategyResult(
            strategy_name='MACD',
            symbol=df.attrs.get('symbol', 'Unknown'),
            total_return=total_return,
            win_rate=win_rate,
            total_trades=len(trades),
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe,
            profit_factor=profit_factor
        )


class EMAMACDHybridStrategy:
    """
    EMA+MACD混合策略
    - 买入: EMA金叉 AND MACD金叉 (双重确认)
    - 卖出: EMA死叉 OR MACD死叉 (任一触发)
    """
    
    def __init__(self, ema_fast=10, ema_slow=30, macd_fast=12, macd_slow=26, macd_signal=9):
        self.ema_fast = ema_fast
        self.ema_slow = ema_slow
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
    
    def run_backtest(self, df: pd.DataFrame, initial_capital: float = 100000.0) -> StrategyResult:
        """执行回测"""
        data = df.copy()
        
        # 计算EMA
        data['ema_fast'] = data['close'].ewm(span=self.ema_fast, adjust=False).mean()
        data['ema_slow'] = data['close'].ewm(span=self.ema_slow, adjust=False).mean()
        
        # 计算MACD
        ema_fast = data['close'].ewm(span=self.macd_fast, adjust=False).mean()
        ema_slow = data['close'].ewm(span=self.macd_slow, adjust=False).mean()
        data['dif'] = ema_fast - ema_slow
        data['dea'] = data['dif'].ewm(span=self.macd_signal, adjust=False).mean()
        
        # EMA信号
        data['ema_golden'] = (data['ema_fast'] > data['ema_slow']) & (data['ema_fast'].shift(1) <= data['ema_slow'].shift(1))
        data['ema_death'] = (data['ema_fast'] < data['ema_slow']) & (data['ema_fast'].shift(1) >= data['ema_slow'].shift(1))
        
        # MACD信号
        data['macd_golden'] = (data['dif'] > data['dea']) & (data['dif'].shift(1) <= data['dea'].shift(1))
        data['macd_death'] = (data['dif'] < data['dea']) & (data['dif'].shift(1) >= data['dea'].shift(1))
        
        # 混合信号: 双金叉买入，任一死叉卖出
        data['buy_signal'] = data['ema_golden'] & data['macd_golden']
        data['sell_signal'] = data['ema_death'] | data['macd_death']
        
        position = 0
        entry_price = 0.0
        trades = []
        equity_curve = [initial_capital]
        current_capital = initial_capital
        
        for i in range(1, len(data)):
            price = data['close'].iloc[i]
            
            if position == 0:  # 空仓
                if data['buy_signal'].iloc[i]:
                    position = 1
                    entry_price = price
                    shares = current_capital / price
                    
            elif position == 1:  # 持仓
                if data['sell_signal'].iloc[i]:
                    exit_price = price
                    pnl = (exit_price - entry_price) * shares
                    pnl_pct = (exit_price / entry_price - 1) * 100
                    
                    trades.append({
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct
                    })
                    
                    current_capital += pnl
                    position = 0
                    entry_price = 0.0
            
            equity_curve.append(current_capital)
        
        # 计算指标
        total_return = (current_capital - initial_capital) / initial_capital * 100
        
        if len(trades) > 0:
            winning_trades = [t for t in trades if t['pnl'] > 0]
            win_rate = len(winning_trades) / len(trades) * 100
            
            equity_series = pd.Series(equity_curve)
            rolling_max = equity_series.expanding().max()
            drawdown = (equity_series - rolling_max) / rolling_max * 100
            max_drawdown = drawdown.min()
            
            returns = pd.Series(equity_curve).pct_change().dropna()
            sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() != 0 else 0
            
            gross_profit = sum(t['pnl'] for t in trades if t['pnl'] > 0)
            gross_loss = abs(sum(t['pnl'] for t in trades if t['pnl'] < 0))
            profit_factor = gross_profit / gross_loss if gross_loss != 0 else float('inf')
        else:
            win_rate = 0
            max_drawdown = 0
            sharpe = 0
            profit_factor = 0
        
        return StrategyResult(
            strategy_name='EMA+MACD混合',
            symbol=df.attrs.get('symbol', 'Unknown'),
            total_return=total_return,
            win_rate=win_rate,
            total_trades=len(trades),
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe,
            profit_factor=profit_factor
        )


def load_stock_data(symbol: str, data_dir: Path) -> pd.DataFrame:
    """加载股票数据"""
    file_path = data_dir / f"{symbol}.csv"
    if not file_path.exists():
        return pd.DataFrame()
    
    df = pd.read_csv(file_path)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    df.attrs['symbol'] = symbol
    return df


def run_comparison(test_stocks: List[str], data_dir: Path) -> Dict:
    """运行策略对比"""
    results = {
        'ema_v21': [],
        'macd': [],
        'hybrid': []
    }
    
    # EMA V2.1 优化参数 (按波动率分类)
    ema_params = {
        # 高波动 - 新能源
        '002594': {'fast_ema': 7, 'slow_ema': 30, 'atr_mult': 2.5},
        '300750': {'fast_ema': 3, 'slow_ema': 35, 'atr_mult': 2.0},
        # 低波动 - 白酒
        '600519': {'fast_ema': 5, 'slow_ema': 20, 'atr_mult': 1.5},
        '000858': {'fast_ema': 5, 'slow_ema': 20, 'atr_mult': 1.5},
        # 中波动 - 科技
        '002415': {'fast_ema': 8, 'slow_ema': 25, 'atr_mult': 2.0},
        '300124': {'fast_ema': 3, 'slow_ema': 40, 'atr_mult': 1.5},
        # 中波动 - 医药
        '603259': {'fast_ema': 8, 'slow_ema': 25, 'atr_mult': 2.0},
        # 中波动 - 消费
        '000333': {'fast_ema': 8, 'slow_ema': 25, 'atr_mult': 1.5},
        '601888': {'fast_ema': 8, 'slow_ema': 25, 'atr_mult': 2.0},
        # 低波动 - 金融
        '000001': {'fast_ema': 5, 'slow_ema': 20, 'atr_mult': 1.5},
        # 高波动 - 资源
        '601899': {'fast_ema': 10, 'slow_ema': 30, 'atr_mult': 2.5},
    }
    
    for symbol in test_stocks:
        df = load_stock_data(symbol, data_dir)
        if df.empty or len(df) < 100:
            continue
        
        print(f"  回测 {symbol}...")
        
        # EMA V2.1
        params = ema_params.get(symbol, {'fast_ema': 10, 'slow_ema': 30, 'atr_mult': 2.0})
        ema_strategy = EMAV2Strategy(params={
            'fast_ema': params['fast_ema'],
            'slow_ema': params['slow_ema'],
            'atr_period': 14,
            'atr_multiplier': params['atr_mult'],
            'market_filter': True
        })
        ema_result = ema_strategy.run_backtest(df)
        results['ema_v21'].append({
            'symbol': symbol,
            'return': ema_result.total_return,
            'win_rate': ema_result.win_rate,
            'trades': ema_result.total_trades,
            'drawdown': ema_result.max_drawdown,
            'sharpe': ema_result.sharpe_ratio
        })
        
        # MACD
        macd_strategy = MACDStrategy(fast=12, slow=26, signal=9)
        macd_result = macd_strategy.run_backtest(df)
        results['macd'].append({
            'symbol': symbol,
            'return': macd_result.total_return,
            'win_rate': macd_result.win_rate,
            'trades': macd_result.total_trades,
            'drawdown': macd_result.max_drawdown,
            'sharpe': macd_result.sharpe_ratio
        })
        
        # 混合策略
        hybrid_strategy = EMAMACDHybridStrategy(
            ema_fast=params['fast_ema'],
            ema_slow=params['slow_ema']
        )
        hybrid_result = hybrid_strategy.run_backtest(df)
        results['hybrid'].append({
            'symbol': symbol,
            'return': hybrid_result.total_return,
            'win_rate': hybrid_result.win_rate,
            'trades': hybrid_result.total_trades,
            'drawdown': hybrid_result.max_drawdown,
            'sharpe': hybrid_result.sharpe_ratio
        })
    
    return results


def generate_report(results: Dict, output_path: Path):
    """生成详细的策略对比报告"""
    
    name_map = {'ema_v21': 'EMA V2.1', 'macd': 'MACD', 'hybrid': 'EMA+MACD混合'}
    
    report = []
    report.append("# 📊 策略对比研究报告: EMA V2.1 vs MACD vs 混合策略")
    report.append("")
    report.append(f"**报告时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    report.append("## 📋 对比概述")
    report.append("")
    report.append("| 策略 | 核心逻辑 | 特点 |")
    report.append("|------|----------|------|")
    report.append("| **EMA V2.1** | 双EMA交叉 + ATR动态止损 + 大盘过滤 | 自适应止损，风险控制强 |")
    report.append("| **MACD** | DIF/DEA交叉 (12/26/9参数) | 经典指标，信号稳定 |")
    report.append("| **EMA+MACD混合** | 双金叉确认买入，任一死叉卖出 | 双重过滤，减少假信号 |")
    report.append("")
    report.append("---")
    report.append("")
    
    # 汇总统计
    report.append("## 📈 汇总对比")
    report.append("")
    report.append("### 整体表现统计")
    report.append("")
    report.append("| 策略 | 平均收益率 | 平均胜率 | 平均交易次数 | 平均最大回撤 | 平均Sharpe | 收益回撤比 |")
    report.append("|------|------------|----------|--------------|--------------|------------|------------|")
    
    summary_stats = {}
    for strategy_name, data in results.items():
        if not data:
            continue
        avg_return = np.mean([d['return'] for d in data])
        avg_winrate = np.mean([d['win_rate'] for d in data])
        avg_trades = np.mean([d['trades'] for d in data])
        avg_drawdown = np.mean([d['drawdown'] for d in data])
        avg_sharpe = np.mean([d['sharpe'] for d in data])
        return_drawdown = avg_return / abs(avg_drawdown) if avg_drawdown != 0 else 0
        
        summary_stats[strategy_name] = {
            'return': avg_return,
            'winrate': avg_winrate,
            'trades': avg_trades,
            'drawdown': avg_drawdown,
            'sharpe': avg_sharpe,
            'rd_ratio': return_drawdown
        }
        
        report.append(f"| **{name_map[strategy_name]}** | {avg_return:+.2f}% | {avg_winrate:.1f}% | {avg_trades:.1f} | {avg_drawdown:.2f}% | {avg_sharpe:.2f} | {return_drawdown:.2f} |")
    
    report.append("")
    report.append("### 🏆 单项冠军")
    report.append("")
    
    # 找出各单项最优
    best_return = max(summary_stats.items(), key=lambda x: x[1]['return'])
    best_winrate = max(summary_stats.items(), key=lambda x: x[1]['winrate'])
    best_drawdown = max(summary_stats.items(), key=lambda x: x[1]['drawdown'])  # 最大回撤最小（数值最大，最接近0）
    best_sharpe = max(summary_stats.items(), key=lambda x: x[1]['sharpe'])
    best_rd = max(summary_stats.items(), key=lambda x: x[1]['rd_ratio'])
    
    report.append(f"- **最高平均收益率**: {name_map[best_return[0]]} ({best_return[1]['return']:+.2f}%)")
    report.append(f"- **最高胜率**: {name_map[best_winrate[0]]} ({best_winrate[1]['winrate']:.1f}%)")
    report.append(f"- **最小最大回撤**: {name_map[best_drawdown[0]]} ({best_drawdown[1]['drawdown']:.2f}%)")
    report.append(f"- **最高Sharpe比率**: {name_map[best_sharpe[0]]} ({best_sharpe[1]['sharpe']:.2f})")
    report.append(f"- **最佳收益回撤比**: {name_map[best_rd[0]]} ({best_rd[1]['rd_ratio']:.2f})")
    report.append("")
    report.append("---")
    report.append("")
    
    # 板块表现分析
    report.append("## 🏭 板块表现分析")
    report.append("")
    
    for category in ['新能源', '白酒', '科技', '医药', '消费', '金融', '资源']:
        category_stocks = [s for s, (_, cat) in STOCK_CATEGORIES.items() if cat == category]
        if not category_stocks:
            continue
            
        report.append(f"### {category}板块")
        report.append("")
        report.append("| 股票 | 策略 | 收益率 | 胜率 | 交易次数 | 最大回撤 | Sharpe |")
        report.append("|------|------|--------|------|----------|----------|--------|")
        
        for symbol in category_stocks:
            stock_name = STOCK_CATEGORIES[symbol][0]
            for strategy_name, data in results.items():
                stock_data = next((d for d in data if d['symbol'] == symbol), None)
                if stock_data:
                    report.append(f"| {stock_name}({symbol}) | {name_map[strategy_name]} | {stock_data['return']:+.2f}% | {stock_data['win_rate']:.1f}% | {stock_data['trades']} | {stock_data['drawdown']:.2f}% | {stock_data['sharpe']:.2f} |")
        
        report.append("")
    
    report.append("---")
    report.append("")
    
    # 个股详细对比
    report.append("## 📋 个股详细对比")
    report.append("")
    
    symbols = [d['symbol'] for d in results['ema_v21']]
    
    for symbol in symbols:
        stock_name, category = STOCK_CATEGORIES.get(symbol, (symbol, '未知'))
        report.append(f"### {stock_name} ({symbol}) - {category}")
        report.append("")
        report.append("| 策略 | 收益率 | 胜率 | 交易次数 | 最大回撤 | Sharpe | 收益回撤比 |")
        report.append("|------|--------|------|----------|----------|--------|------------|")
        
        for strategy_name, data in results.items():
            stock_data = next((d for d in data if d['symbol'] == symbol), None)
            if stock_data:
                rd_ratio = stock_data['return'] / abs(stock_data['drawdown']) if stock_data['drawdown'] != 0 else 0
                report.append(f"| {name_map[strategy_name]} | {stock_data['return']:+.2f}% | {stock_data['win_rate']:.1f}% | {stock_data['trades']} | {stock_data['drawdown']:.2f}% | {stock_data['sharpe']:.2f} | {rd_ratio:.2f} |")
        
        report.append("")
    
    report.append("---")
    report.append("")
    
    # 策略优缺点分析
    report.append("## 💡 策略深度分析")
    report.append("")
    
    report.append("### EMA V2.1 策略")
    report.append("")
    report.append("**核心优势** ✅")
    report.append("- **ATR动态止损**: 根据股票波动率自动调整止损位，高波动股票更宽止损，低波动股票更紧止损")
    report.append("- **大盘过滤机制**: 熊市环境下暂停新开仓，避免逆势交易，大幅降低系统性风险")
    report.append("- **参数可优化**: 针对不同波动率特征的股票可调整EMA周期和ATR倍数")
    report.append("- **及时止损**: 相比传统EMA策略，增加了ATR止损机制，单笔亏损控制更好")
    report.append("")
    report.append("**主要劣势** ❌")
    report.append("- **参数敏感**: 不同股票需要不同的最优参数，泛化能力相对较弱")
    report.append("- **震荡市表现差**: 在横盘震荡行情中可能产生多次假信号")
    report.append("- **大盘依赖**: 需要沪深300数据作为市场过滤，数据源要求高")
    report.append("")
    report.append("**适用场景**: 高波动股票（新能源、资源股）、趋势明显的市场环境")
    report.append("")
    
    report.append("### MACD 策略")
    report.append("")
    report.append("**核心优势** ✅")
    report.append("- **参数标准化**: 经典12/26/9参数，无需针对不同股票优化，泛化能力强")
    report.append("- **信号稳定**: 基于长期EMA计算，信号相对平滑，过滤了短期噪音")
    report.append("- **广泛使用**: 市场认可度高，大量交易者关注MACD信号")
    report.append("- **趋势跟踪**: 在强趋势行情中表现优异，能够捕捉主要趋势")
    report.append("")
    report.append("**主要劣势** ❌")
    report.append("- **信号滞后**: 由于EMA的滞后性，MACD信号往往慢于价格变化")
    report.append("- **震荡市假信号**: 在横盘震荡行情中，DIF/DEA频繁交叉产生假信号")
    report.append("- **无止损机制**: 原始MACD策略没有内置止损，可能导致大额亏损")
    report.append("")
    report.append("**适用场景**: 中长期趋势跟踪、大盘股、机构持仓股票")
    report.append("")
    
    report.append("### EMA+MACD 混合策略")
    report.append("")
    report.append("**核心优势** ✅")
    report.append("- **双重确认**: EMA金叉和MACD金叉同时满足才买入，过滤了大量假信号")
    report.append("- **胜率较高**: 由于入场条件更严格，单次交易胜率相对较高")
    report.append("- **灵活性**: EMA死叉或MACD死叉任一触发即卖出，比单一指标更灵活")
    report.append("- **适合震荡市**: 双重确认减少了震荡市的频繁交易")
    report.append("")
    report.append("**主要劣势** ❌")
    report.append("- **信号稀少**: 双重确认条件导致交易机会大幅减少，可能错过部分趋势")
    report.append("- **入场滞后**: 需要两个指标同时满足，往往错过最佳入场点")
    report.append("- **出场过早**: 任一死叉触发卖出，可能导致在趋势中继时过早离场")
    report.append("- **无止损机制**: 同MACD，缺乏独立止损机制")
    report.append("")
    report.append("**适用场景**: 震荡市、高胜率要求、低频交易者")
    report.append("")
    report.append("---")
    report.append("")
    
    # 最优策略推荐
    report.append("## 🎯 最优策略推荐")
    report.append("")
    
    # 计算综合得分
    scores = {}
    for strategy_name, stats in summary_stats.items():
        # 综合评分 = 收益率*0.3 + 胜率*0.2 + (100+回撤)*0.2 + Sharpe*10*0.3
        score = (stats['return'] * 0.3 + 
                 stats['winrate'] * 0.2 + 
                 (100 + stats['drawdown']) * 0.2 + 
                 stats['sharpe'] * 10 * 0.3)
        scores[strategy_name] = score
    
    best_strategy = max(scores.items(), key=lambda x: x[1])
    
    report.append("### 综合评分排名")
    report.append("")
    report.append("| 排名 | 策略 | 综合得分 | 适用人群 |")
    report.append("|------|------|----------|----------|")
    
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    recommendations = {
        'ema_v21': '追求收益、能承受波动的积极型投资者',
        'macd': '追求稳健、偏好标准化的保守型投资者',
        'hybrid': '追求高胜率、低频交易的稳健型投资者'
    }
    
    for i, (strategy, score) in enumerate(sorted_scores, 1):
        report.append(f"| {i} | **{name_map[strategy]}** | {score:.2f} | {recommendations[strategy]} |")
    
    report.append("")
    report.append(f"### 推荐结论")
    report.append("")
    report.append(f"**🏆 最优策略: {name_map[best_strategy[0]]}** (综合得分: {best_strategy[1]:.2f})")
    report.append("")
    report.append("**推荐理由**:")
    
    if best_strategy[0] == 'ema_v21':
        report.append("1. **收益能力最强**: 在大多数股票上都能获得正收益")
        report.append("2. **风险控制优秀**: ATR止损机制有效控制了最大回撤")
        report.append("3. **适应性强**: 通过参数优化可适应不同波动率的股票")
        report.append("4. **熊市保护**: 大盘过滤机制在熊市中有效保护资本")
    elif best_strategy[0] == 'macd':
        report.append("1. **简单稳定**: 无需复杂参数优化，一套参数适用于多数股票")
        report.append("2. **趋势捕捉**: 在强趋势行情中表现优异")
        report.append("3. **标准化**: 广泛使用的指标，易于理解和执行")
    else:
        report.append("1. **高胜率**: 双重确认机制提高了单次交易成功率")
        report.append("2. **假信号少**: 有效过滤了震荡市的噪音信号")
        report.append("3. **适合稳健投资者**: 适合风险偏好较低的投资者")
    
    report.append("")
    report.append("### 分场景推荐")
    report.append("")
    report.append("| 场景 | 推荐策略 | 理由 |")
    report.append("|------|----------|------|")
    report.append("| **高波动股票** (新能源、资源) | EMA V2.1 | ATR止损适合高波动 |")
    report.append("| **低波动股票** (银行、白酒) | MACD | 稳定趋势，假信号少 |")
    report.append("| **震荡市场** | 混合策略 | 双重确认过滤假信号 |")
    report.append("| **强趋势市场** | MACD | 趋势跟踪能力强 |")
    report.append("| **熊市环境** | EMA V2.1 | 大盘过滤保护资本 |")
    report.append("| **新手投资者** | MACD | 参数简单，易于执行 |")
    report.append("")
    report.append("---")
    report.append("")
    
    # 风险提示
    report.append("## ⚠️ 风险提示")
    report.append("")
    report.append("1. **历史回测不代表未来表现**: 本报告基于历史数据回测，实际交易结果可能不同")
    report.append("2. **参数过拟合风险**: EMA V2.1针对不同股票的优化参数可能存在过拟合")
    report.append("3. **市场风格切换**: 不同市场风格下各策略表现会有显著差异")
    report.append("4. **交易成本控制**: 回测未充分考虑滑点、佣金等交易成本")
    report.append("5. **流动性风险**: 部分小盘股可能存在流动性不足的问题")
    report.append("")
    report.append("---")
    report.append("")
    report.append(f"*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    report.append("*InvestMindPro - 智能量化投资研究*")
    
    # 保存报告
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print(f"\n📁 报告已保存: {output_path}")


# 股票分类信息
STOCK_CATEGORIES = {
    '002594': ('比亚迪', '新能源'),
    '300750': ('宁德时代', '新能源'),
    '600519': ('贵州茅台', '白酒'),
    '000858': ('五粮液', '白酒'),
    '002415': ('海康威视', '科技'),
    '300124': ('汇川技术', '科技'),
    '603259': ('药明康德', '医药'),
    '000333': ('美的集团', '消费'),
    '601888': ('中国中免', '消费'),
    '000001': ('平安银行', '金融'),
    '601899': ('紫金矿业', '资源'),
}


def main():
    print("=" * 80)
    print("🔬 策略对比研究: EMA V2.1 vs MACD vs 混合策略")
    print("=" * 80)
    
    # 选择代表性股票进行对比 (10只不同板块)
    test_stocks = [
        '002594',  # 比亚迪 - 新能源
        '300750',  # 宁德时代 - 新能源
        '600519',  # 贵州茅台 - 白酒
        '000858',  # 五粮液 - 白酒
        '002415',  # 海康威视 - 科技
        '300124',  # 汇川技术 - 科技
        '603259',  # 药明康德 - 医药
        '000333',  # 美的集团 - 消费
        '601888',  # 中国中免 - 消费
        '000001',  # 平安银行 - 金融
        '601899',  # 紫金矿业 - 资源
    ]
    
    data_dir = Path(__file__).parent.parent / "data"
    
    print(f"\n📊 对比股票池 ({len(test_stocks)}只不同板块):")
    for s in test_stocks:
        name, cat = STOCK_CATEGORIES.get(s, (s, '未知'))
        print(f"  - {s} {name} [{cat}]")
    
    print("\n🔄 开始回测...")
    results = run_comparison(test_stocks, data_dir)
    
    # 打印汇总
    print("\n" + "=" * 80)
    print("📈 策略对比汇总结果")
    print("=" * 80)
    print("")
    print(f"{'策略':<15} {'平均收益':>10} {'平均胜率':>10} {'平均回撤':>10} {'平均Sharpe':>12}")
    print("-" * 60)
    
    name_map = {'ema_v21': 'EMA V2.1', 'macd': 'MACD', 'hybrid': 'EMA+MACD混合'}
    summary_stats = {}
    
    for strategy_name, data in results.items():
        if not data:
            continue
        avg_return = np.mean([d['return'] for d in data])
        avg_winrate = np.mean([d['win_rate'] for d in data])
        avg_drawdown = np.mean([d['drawdown'] for d in data])
        avg_sharpe = np.mean([d['sharpe'] for d in data])
        
        summary_stats[strategy_name] = {
            'return': avg_return,
            'winrate': avg_winrate,
            'drawdown': avg_drawdown,
            'sharpe': avg_sharpe
        }
        
        print(f"{name_map[strategy_name]:<15} {avg_return:+10.2f}% {avg_winrate:>9.1f}% {avg_drawdown:>9.2f}% {avg_sharpe:>11.2f}")
    
    print("")
    print("🏆 单项冠军:")
    best_return = max(summary_stats.items(), key=lambda x: x[1]['return'])
    best_winrate = max(summary_stats.items(), key=lambda x: x[1]['winrate'])
    best_sharpe = max(summary_stats.items(), key=lambda x: x[1]['sharpe'])
    print(f"  最高收益率: {name_map[best_return[0]]} ({best_return[1]['return']:+.2f}%)")
    print(f"  最高胜率:   {name_map[best_winrate[0]]} ({best_winrate[1]['winrate']:.1f}%)")
    print(f"  最高Sharpe: {name_map[best_sharpe[0]]} ({best_sharpe[1]['sharpe']:.2f})")
    
    # 生成报告
    output_path = Path(__file__).parent.parent / "results" / "STRATEGY_COMPARISON_REPORT.md"
    generate_report(results, output_path)
    
    print("\n" + "=" * 80)
    print("✅ 策略对比研究完成!")
    print("=" * 80)


if __name__ == "__main__":
    main()
