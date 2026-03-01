#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EMA V2.2 策略批量回测 - 扩展版 (11只股票)
使用优化参数: 追踪止损激活 1.5 ATR, 止盈目标 3.0 ATR
回测区间: 2024-01-01 到 2024-12-31
"""

import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

import pandas as pd
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# 配置参数
START_DATE = "2024-01-01"
END_DATE = "2024-12-31"
INITIAL_CAPITAL = 1_000_000.0
COMMISSION_RATE = 0.0003
SLIPPAGE_RATE = 0.0005

# 扩展股票列表 (11只 - 基于可用数据)
STOCKS = {
    "300750": "宁德时代",
    "002594": "比亚迪", 
    "002415": "海康威视",
    "601012": "隆基绿能",
    "600519": "贵州茅台",
    "601318": "中国平安",
    "000858": "五粮液",
    "000333": "美的集团",
    "000651": "格力电器",
    "600276": "恒瑞医药",
    "601888": "中国中免",
}

# 本地数据映射
project_root = Path("/home/icysaintdx/.openclaw/workspace-investmindpro/InvestMindPro")
CACHE_DIR = project_root / "backend" / "data" / "backtest_cache"
RESULTS_DIR = Path("/home/icysaintdx/.openclaw/workspace/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ======== EMA V2.2 策略类 (优化参数) ========

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

class EMABreakoutV22Strategy:
    """EMA突破策略 V2.2 - 优化参数版
    
    优化参数:
    - TRAILING_STOP_ACTIVATION: 1.5 ATR (原为1.0)
    - PROFIT_TARGET_ATR: 3.0 ATR (原为2.5)
    """
    
    description = "EMA突破 + ATR动态止损 V2.2 (优化版)"
    
    def __init__(self, config: StrategyConfig):
        self.config = config
        self.name = config.name
        self.parameters = config.parameters
        
        self.ema_fast = self.parameters.get('ema_fast', 8)
        self.ema_slow = self.parameters.get('ema_slow', 25)
        self.atr_period = self.parameters.get('atr_period', 14)
        self.atr_multiplier = self.parameters.get('atr_multiplier', 2.0)
        # V2.2优化参数
        self.trailing_stop_activation = self.parameters.get('trailing_stop_activation', 1.5)
        self.profit_target_atr = self.parameters.get('profit_target_atr', 3.0)
        
        self._data = None
        self._initialized = False
    
    def initialize(self, data: pd.DataFrame):
        """计算技术指标"""
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
        
        # 波动率分类
        df['volatility'] = df['close'].pct_change().rolling(20).std() * np.sqrt(252)
        
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
                # V2.2优化: 使用1.5倍ATR追踪止损激活，3.0倍ATR止盈
                stop_loss = price - self.atr_multiplier * atr
                take_profit = price + self.profit_target_atr * atr
                
                signals.append(StrategySignal(
                    signal_type=SignalType.BUY,
                    confidence=0.75,
                    price=price,
                    stop_loss=round(stop_loss, 2),
                    take_profit=round(take_profit, 2),
                    position_size=0.2,
                    reason=f"EMA金叉买入 (V2.2优化: {self.trailing_stop_activation}xATR追踪, {self.profit_target_atr}xATR止盈)",
                    strategy_id=self.config.strategy_id,
                    timestamp=timestamp,
                    metadata={
                        'trailing_activation': self.trailing_stop_activation,
                        'profit_target_atr': self.profit_target_atr
                    }
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

# ======== 回测引擎 ========

class SimpleBacktester:
    """简化版回测引擎 - V2.2支持追踪止损"""
    
    def __init__(self, initial_capital: float = 1000000.0):
        self.initial_capital = initial_capital
        self.commission_rate = COMMISSION_RATE
        self.slippage_rate = SLIPPAGE_RATE
    
    def run(self, strategy: EMABreakoutV22Strategy, data: pd.DataFrame) -> Dict:
        """执行回测 - V2.2优化"""
        signals = strategy.generate_signals(data)
        
        cash = self.initial_capital
        position = 0
        avg_cost = 0.0
        trades = []
        equity_curve = []
        stoploss_count = 0
        trailing_stop_count = 0
        profit_target_count = 0
        
        # 追踪止损状态
        highest_price_since_entry = 0.0
        trailing_stop_active = False
        
        # 按日期遍历
        for idx, (date, row) in enumerate(data.iterrows()):
            price = float(row['close'])
            atr = row.get('atr', price * 0.02)  # 默认2%ATR
            
            # 更新最高价（用于追踪止损）
            if position > 0 and price > highest_price_since_entry:
                highest_price_since_entry = price
            
            # 查找当天的信号
            day_signals = [s for s in signals if s.timestamp == date]
            
            # 处理买入信号
            if position == 0:
                for signal in day_signals:
                    if signal.signal_type == SignalType.BUY:
                        position_value = self.initial_capital * signal.position_size
                        shares = int(position_value / price / 100) * 100
                        if shares >= 100:
                            cost = shares * price
                            commission = cost * self.commission_rate
                            slippage = cost * self.slippage_rate
                            total_cost = cost + commission + slippage
                            
                            if cash >= total_cost:
                                cash -= total_cost
                                position = shares
                                avg_cost = price
                                highest_price_since_entry = price
                                trailing_stop_active = False
                                
                                trades.append({
                                    'date': str(date.date()),
                                    'action': 'BUY',
                                    'price': price,
                                    'shares': shares,
                                    'commission': commission,
                                    'slippage': slippage
                                })
                                logger.info(f"  [买入] {date.date()}: {price:.2f}元, {shares}股")
                        break
            
            # 处理卖出信号、止盈或止损
            elif position > 0:
                sell_triggered = False
                is_stoploss = False
                sell_reason = ""
                
                profit_pct = (price - avg_cost) / avg_cost
                profit_atr = (price - avg_cost) / atr if atr > 0 else 0
                
                # 检查是否激活追踪止损
                if not trailing_stop_active and profit_atr >= strategy.trailing_stop_activation:
                    trailing_stop_active = True
                    logger.info(f"  [追踪止损激活] {date.date()}: 盈利{profit_atr:.1f}ATR >= {strategy.trailing_stop_activation}ATR")
                
                # 检查止盈目标 (V2.2: 3.0 ATR)
                if profit_atr >= strategy.profit_target_atr:
                    sell_triggered = True
                    is_stoploss = False
                    sell_reason = f"止盈 ({strategy.profit_target_atr}xATR)"
                    profit_target_count += 1
                
                # 检查追踪止损
                elif trailing_stop_active:
                    trailing_stop_price = highest_price_since_entry - strategy.atr_multiplier * atr
                    if price <= trailing_stop_price:
                        sell_triggered = True
                        is_stoploss = True
                        sell_reason = f"追踪止损 ({strategy.atr_multiplier}xATR)"
                        trailing_stop_count += 1
                
                # 检查硬止损 (5%)
                elif price <= avg_cost * 0.95:
                    sell_triggered = True
                    is_stoploss = True
                    sell_reason = "硬止损 (5%)"
                    stoploss_count += 1
                
                # 检查卖出信号
                if not sell_triggered:
                    for signal in day_signals:
                        if signal.signal_type == SignalType.SELL:
                            sell_triggered = True
                            sell_reason = "EMA死叉"
                            break
                
                if sell_triggered:
                    sell_value = position * price
                    commission = sell_value * self.commission_rate
                    slippage = sell_value * self.slippage_rate
                    stamp_tax = sell_value * 0.001
                    total_cost = commission + slippage + stamp_tax
                    
                    profit = position * (price - avg_cost) - total_cost
                    profit_pct_actual = (price / avg_cost - 1) if avg_cost > 0 else 0
                    
                    cash += sell_value - total_cost
                    
                    trades.append({
                        'date': str(date.date()),
                        'action': 'SELL',
                        'price': price,
                        'shares': position,
                        'commission': commission,
                        'slippage': slippage,
                        'stamp_tax': stamp_tax,
                        'profit': profit,
                        'profit_pct': profit_pct_actual,
                        'is_stoploss': is_stoploss,
                        'reason': sell_reason
                    })
                    logger.info(f"  [卖出] {date.date()}: {price:.2f}元, 盈亏: {profit_pct_actual:+.2%} [{sell_reason}]")
                    position = 0
                    avg_cost = 0.0
                    highest_price_since_entry = 0.0
                    trailing_stop_active = False
            
            # 记录权益曲线
            portfolio_value = cash + position * price
            equity_curve.append({'date': str(date.date()), 'value': portfolio_value})
        
        # 计算绩效指标
        final_value = cash + position * float(data.iloc[-1]['close'])
        values = pd.Series([e['value'] for e in equity_curve])
        dates = pd.to_datetime([e['date'] for e in equity_curve])
        
        total_return = (final_value / self.initial_capital) - 1
        days = (dates[-1] - dates[0]).days
        years = max(days / 365.25, 0.01)
        annual_return = (1 + total_return) ** (1 / years) - 1
        
        daily_returns = values.pct_change().dropna()
        volatility = daily_returns.std() * np.sqrt(252) if len(daily_returns) > 1 else 0
        sharpe = (annual_return - 0.03) / volatility if volatility > 0 else 0
        
        cummax = values.expanding().max()
        drawdown = (values - cummax) / cummax
        max_drawdown = drawdown.min()
        
        sell_trades = [t for t in trades if t['action'] == 'SELL']
        win_trades = [t for t in sell_trades if t.get('profit', 0) > 0]
        win_rate = len(win_trades) / len(sell_trades) if sell_trades else 0
        
        return {
            'success': True,
            'total_return': float(total_return),
            'annual_return': float(annual_return),
            'max_drawdown': float(max_drawdown),
            'sharpe_ratio': float(sharpe),
            'volatility': float(volatility),
            'win_rate': float(win_rate),
            'total_trades': len(trades),
            'buy_trades': len([t for t in trades if t['action'] == 'BUY']),
            'sell_trades': len(sell_trades),
            'stoploss_count': stoploss_count,
            'trailing_stop_count': trailing_stop_count,
            'profit_target_count': profit_target_count,
            'final_value': float(final_value),
            'trades': trades,
            'equity_curve': equity_curve
        }

# ======== 数据加载 ========

LOCAL_DATA_MAP = {
    "600519": "600519_20200101_20241231.csv",
    "601318": "601318_20200101_20241231.csv",
    "000858": "000858_20200101_20241231.csv",
    "000333": "000333_20200101_20241231.csv",
    "000651": "000651_20200101_20241231.csv",
    "600276": "600276_20200101_20241231.csv",
    "601888": "601888_20200101_20241231.csv",
    "300750": "300750_20200101_20241231.csv",
    "002594": "002594_20200101_20241231.csv",
    "002415": "002415_20200101_20241231.csv",
    "601012": "601012_20200101_20241231.csv",
}

def load_local_data(symbol: str):
    """从本地缓存加载股票数据并筛选2024年"""
    if symbol not in LOCAL_DATA_MAP:
        return None
    
    cache_file = CACHE_DIR / LOCAL_DATA_MAP[symbol]
    if not cache_file.exists():
        return None
    
    try:
        df = pd.read_csv(cache_file, index_col='date', parse_dates=True)
        df = df[df.index >= START_DATE]
        df = df[df.index <= END_DATE]
        
        if len(df) < 30:
            return None
        
        column_mapping = {
            '开盘': 'open', '收盘': 'close',
            '最高': 'high', '最低': 'low', '成交量': 'volume',
            'open': 'open', 'close': 'close', 'high': 'high', 'low': 'low', 'volume': 'volume'
        }
        df = df.rename(columns=column_mapping)
        
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df.sort_index(inplace=True)
        return df
    except Exception as e:
        logger.error(f"[{symbol}] 本地数据加载失败: {e}")
        return None

# ======== 回测执行 ========

def run_backtest(stock_code: str, stock_name: str) -> Dict:
    """执行单只股票回测"""
    logger.info(f"\n{'='*60}")
    logger.info(f"开始回测: {stock_code} {stock_name}")
    logger.info(f"{'='*60}")
    
    data = load_local_data(stock_code)
    if data is None:
        logger.error(f"[{stock_code}] 无本地数据，跳过回测")
        return {
            "stock_code": stock_code,
            "stock_name": stock_name,
            "success": False,
            "error": "无本地数据"
        }
    
    logger.info(f"[{stock_code}] 数据加载成功: {len(data)} 条记录")
    logger.info(f"[{stock_code}] 数据区间: {data.index[0].date()} ~ {data.index[-1].date()}")
    
    # V2.2优化参数
    config = StrategyConfig(
        strategy_id="ema_v2_2_optimized",
        name="EMA V2.2 (优化版)",
        parameters={
            'ema_fast': 8, 
            'ema_slow': 25, 
            'atr_period': 14, 
            'atr_multiplier': 2.0,
            'trailing_stop_activation': 1.5,  # V2.2优化
            'profit_target_atr': 3.0  # V2.2优化
        }
    )
    strategy = EMABreakoutV22Strategy(config)
    
    backtester = SimpleBacktester(initial_capital=INITIAL_CAPITAL)
    result = backtester.run(strategy, data)
    
    result['stock_code'] = stock_code
    result['stock_name'] = stock_name
    
    logger.info(f"\n[{stock_code} 回测结果]")
    logger.info(f"  总收益: {result['total_return']:+.2%}")
    logger.info(f"  年化收益: {result['annual_return']:+.2%}")
    logger.info(f"  最大回撤: {result['max_drawdown']:.2%}")
    logger.info(f"  夏普比率: {result['sharpe_ratio']:.2f}")
    logger.info(f"  胜率: {result['win_rate']:.1%}")
    logger.info(f"  交易次数: {result['sell_trades']}")
    logger.info(f"  止盈次数: {result['profit_target_count']}")
    logger.info(f"  追踪止损: {result['trailing_stop_count']}")
    logger.info(f"  硬止损: {result['stoploss_count']}")
    
    return result

# ======== 报告生成 ========

def generate_report(results: Dict[str, Dict]) -> str:
    """生成Markdown报告"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    lines = [
        "# EMA V2.2 策略批量回测报告 (11只股票)",
        "",
        f"**生成时间**: {timestamp}",
        "",
        "**策略版本**: EMA V2.2 (优化版)",
        "",
        "**优化参数**:",
        "- 追踪止损激活: 1.5 ATR (原为1.0)",
        "- 止盈目标: 3.0 ATR (原为2.5)",
        "",
        f"**回测区间**: 2024-01-01 - 2024-12-31",
        "",
        f"**初始资金**: ¥{INITIAL_CAPITAL:,.0f}",
        "",
        "## 股票池 (11只)",
        "",
    ]
    
    for code, name in STOCKS.items():
        lines.append(f"- {code}: {name}")
    
    lines.extend([
        "",
        "## 回测结果汇总",
        "",
        "| 股票代码 | 股票名称 | 总收益 | 年化 | 最大回撤 | 胜率 | 交易 | 止盈 | 追踪止损 | 状态 |",
        "|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
    ])
    
    successful_results = {}
    failed_stocks = []
    
    for code, r in results.items():
        if r.get('success'):
            successful_results[code] = r
            lines.append(f"| {code} | {r['stock_name']} | {r['total_return']:+.2%} | {r['annual_return']:+.2%} | {r['max_drawdown']:.2%} | {r['win_rate']:.0%} | {r['sell_trades']} | {r['profit_target_count']} | {r['trailing_stop_count']} | ✅ |")
        else:
            failed_stocks.append((code, r.get('stock_name', STOCKS.get(code, '')), r.get('error', '未知错误')))
            lines.append(f"| {code} | {r.get('stock_name', STOCKS.get(code, ''))} | - | - | - | - | - | - | - | ❌ {r.get('error', '失败')} |")
    
    lines.append("")
    
    # 汇总统计
    if successful_results:
        returns = [r['total_return'] for r in successful_results.values()]
        win_rates = [r['win_rate'] for r in successful_results.values()]
        drawdowns = [r['max_drawdown'] for r in successful_results.values()]
        trade_counts = [r['sell_trades'] for r in successful_results.values()]
        profit_targets = [r['profit_target_count'] for r in successful_results.values()]
        trailing_stops = [r['trailing_stop_count'] for r in successful_results.values()]
        
        positive_returns = [r for r in returns if r > 0]
        
        lines.extend([
            "## 统计摘要",
            "",
            f"- **测试股票总数**: {len(STOCKS)}",
            f"- **成功回测**: {len(successful_results)}",
            f"- **失败/无数据**: {len(failed_stocks)}",
            f"- **平均总收益**: {np.mean(returns):+.2%}",
            f"- **收益中位数**: {np.median(returns):+.2%}",
            f"- **正收益股票数**: {len(positive_returns)}/{len(returns)} ({len(positive_returns)/len(returns)*100:.0f}%)",
            f"- **收益最高**: {max(returns):+.2%}",
            f"- **收益最低**: {min(returns):+.2%}",
            f"- **平均胜率**: {np.mean(win_rates):.1%}",
            f"- **平均最大回撤**: {np.mean(drawdowns):.2%}",
            f"- **总交易次数**: {sum(trade_counts)}",
            f"- **总止盈次数**: {sum(profit_targets)}",
            f"- **总追踪止损次数**: {sum(trailing_stops)}",
            "",
        ])
    
    # 详细结果
    lines.extend([
        "## 详细结果",
        "",
    ])
    
    for code, r in successful_results.items():
        lines.extend([
            f"### {code} {r['stock_name']}",
            "",
            f"- **总收益**: {r['total_return']:+.2%}",
            f"- **年化收益**: {r['annual_return']:+.2%}",
            f"- **最大回撤**: {r['max_drawdown']:.2%}",
            f"- **夏普比率**: {r['sharpe_ratio']:.2f}",
            f"- **波动率**: {r['volatility']:.2%}",
            f"- **胜率**: {r['win_rate']:.1%}",
            f"- **买入次数**: {r['buy_trades']}",
            f"- **卖出次数**: {r['sell_trades']}",
            f"- **止盈次数**: {r['profit_target_count']}",
            f"- **追踪止损次数**: {r['trailing_stop_count']}",
            f"- **硬止损次数**: {r['stoploss_count']}",
            f"- **最终资金**: ¥{r['final_value']:,.2f}",
            ""
        ])
    
    if failed_stocks:
        lines.extend([
            "## 失败/无数据股票",
            "",
        ])
        for code, name, error in failed_stocks:
            lines.append(f"- {code} {name}: {error}")
        lines.append("")
    
    lines.extend([
        "---",
        "",
        "*报告由 InvestMindPro 自动生成*",
        "",
        "*策略: EMA V2.2 (1.5 ATR追踪止损激活, 3.0 ATR止盈)*"
    ])
    
    return '\n'.join(lines)

# ======== 主函数 ========

def main():
    """主函数"""
    logger.info(f"\n{'#'*70}")
    logger.info(f"# EMA V2.2 策略批量回测 (11只股票)")
    logger.info(f"# 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"# 股票数量: {len(STOCKS)}")
    logger.info(f"# 回测区间: {START_DATE} - {END_DATE}")
    logger.info(f"# V2.2优化: 1.5 ATR追踪激活, 3.0 ATR止盈")
    logger.info(f"{'#'*70}\n")
    
    all_results = {}
    
    for stock_code, stock_name in STOCKS.items():
        try:
            result = run_backtest(stock_code, stock_name)
            all_results[stock_code] = result
        except Exception as e:
            logger.error(f"[{stock_code}] 回测异常: {e}")
            import traceback
            traceback.print_exc()
            all_results[stock_code] = {
                "stock_code": stock_code,
                "stock_name": stock_name,
                "success": False,
                "error": str(e)
            }
    
    # 保存JSON结果
    json_file = RESULTS_DIR / f"ema_v22_batch_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2, default=str)
    
    # 生成并保存Markdown报告
    report = generate_report(all_results)
    report_file = RESULTS_DIR / f"EMA_V22_BATCH_BACKTEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    # 输出摘要
    successful = [r for r in all_results.values() if r.get('success')]
    
    logger.info(f"\n{'='*60}")
    logger.info("批量回测完成!")
    logger.info(f"成功回测: {len(successful)}/{len(STOCKS)} 只股票")
    if successful:
        avg_return = sum(r['total_return'] for r in successful) / len(successful)
        logger.info(f"平均收益: {avg_return:+.2%}")
    logger.info(f"JSON结果: {json_file}")
    logger.info(f"MD报告: {report_file}")
    logger.info(f"{'='*60}")

if __name__ == "__main__":
    main()
