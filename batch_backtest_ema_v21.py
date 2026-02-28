#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EMA V2.1 策略批量回测 - 内联实现版本
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

# 股票列表 (代码: 名称)
# 本次回测目标: 4只新下载数据的股票
STOCKS = {
    "300750": "宁德时代",
    "002594": "比亚迪",
    "002415": "海康威视",
    "601012": "隆基绿能",
}

# 本地数据映射
project_root = Path("/home/icysaintdx/.openclaw/workspace-investmindpro/InvestMindPro")
CACHE_DIR = project_root / "backend" / "data" / "backtest_cache"
RESULTS_DIR = Path("/home/icysaintdx/.openclaw/workspace/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ======== 内联策略类定义 ========

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
    """EMA突破策略 V2.1 - 内联版"""
    
    description = "EMA突破 + ATR动态止损 V2.1"
    
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
                    reason="EMA金叉买入",
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

# ======== 回测引擎 ========

class SimpleBacktester:
    """简化版回测引擎"""
    
    def __init__(self, initial_capital: float = 1000000.0):
        self.initial_capital = initial_capital
        self.commission_rate = COMMISSION_RATE
        self.slippage_rate = SLIPPAGE_RATE
    
    def run(self, strategy: EMABreakoutV2Strategy, data: pd.DataFrame) -> Dict:
        """执行回测"""
        signals = strategy.generate_signals(data)
        
        cash = self.initial_capital
        position = 0
        avg_cost = 0.0
        trades = []
        equity_curve = []
        stoploss_count = 0
        
        # 按日期遍历
        for idx, (date, row) in enumerate(data.iterrows()):
            price = float(row['close'])
            
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
                                trades.append({
                                    'date': str(date.date()),
                                    'action': 'BUY',
                                    'price': price,
                                    'shares': shares,
                                    'commission': commission,
                                    'slippage': slippage
                                })
                                logger.info(f"  [买入] {date.date()}: {price:.2f}元, {shares}股")
                        break  # 只执行第一个买入信号
            
            # 处理卖出信号或止损
            elif position > 0:
                sell_triggered = False
                is_stoploss = False
                
                # 检查止损
                stop_loss_price = avg_cost * 0.95  # 5%止损
                if price <= stop_loss_price:
                    sell_triggered = True
                    is_stoploss = True
                
                # 检查卖出信号
                if not sell_triggered:
                    for signal in day_signals:
                        if signal.signal_type == SignalType.SELL:
                            sell_triggered = True
                            break
                
                if sell_triggered:
                    sell_value = position * price
                    commission = sell_value * self.commission_rate
                    slippage = sell_value * self.slippage_rate
                    stamp_tax = sell_value * 0.001  # 印花税
                    total_cost = commission + slippage + stamp_tax
                    
                    profit = position * (price - avg_cost) - total_cost
                    profit_pct = (price / avg_cost - 1) if avg_cost > 0 else 0
                    
                    cash += sell_value - total_cost
                    
                    if is_stoploss:
                        stoploss_count += 1
                    
                    trades.append({
                        'date': str(date.date()),
                        'action': 'SELL',
                        'price': price,
                        'shares': position,
                        'commission': commission,
                        'slippage': slippage,
                        'stamp_tax': stamp_tax,
                        'profit': profit,
                        'profit_pct': profit_pct,
                        'is_stoploss': is_stoploss
                    })
                    logger.info(f"  [卖出] {date.date()}: {price:.2f}元, 盈亏: {profit_pct:+.2%} {'[止损]' if is_stoploss else ''}")
                    position = 0
                    avg_cost = 0.0
            
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
    # 新增下载的4只股票
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
        # 筛选2024年数据
        df = df[df.index >= START_DATE]
        df = df[df.index <= END_DATE]
        
        if len(df) < 30:
            return None
        
        # 标准化列名
        column_mapping = {
            '开盘': 'open', '收盘': 'close',
            '最高': 'high', '最低': 'low', '成交量': 'volume',
            'open': 'open', 'close': 'close', 'high': 'high', 'low': 'low', 'volume': 'volume'
        }
        df = df.rename(columns=column_mapping)
        
        # 确保数值类型
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
    
    # 加载数据
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
    
    # 创建策略
    config = StrategyConfig(
        strategy_id="ema_v2_1",
        name="EMA V2.1",
        parameters={'ema_fast': 8, 'ema_slow': 25, 'atr_period': 14, 'atr_multiplier': 2.0}
    )
    strategy = EMABreakoutV2Strategy(config)
    
    # 执行回测
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
    logger.info(f"  止损次数: {result['stoploss_count']}")
    
    return result

# ======== 报告生成 ========

def generate_report(results: Dict[str, Dict]) -> str:
    """生成Markdown报告"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    lines = [
        "# EMA V2.1 策略批量回测报告",
        "",
        f"**生成时间**: {timestamp}",
        "",
        f"**回测区间**: 2024-01-01 - 2024-12-31",
        "",
        f"**初始资金**: ¥{INITIAL_CAPITAL:,.0f}",
        "",
        "## 股票池",
        "",
    ]
    
    for code, name in STOCKS.items():
        lines.append(f"- {code}: {name}")
    
    lines.extend([
        "",
        "## 各股票回测结果",
        "",
        "| 股票代码 | 股票名称 | 总收益 | 最大回撤 | 胜率 | 交易次数 | 状态 |",
        "|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
    ])
    
    successful_results = {}
    failed_stocks = []
    
    for code, r in results.items():
        if r.get('success'):
            successful_results[code] = r
            lines.append(f"| {code} | {r['stock_name']} | {r['total_return']:+.2%} | {r['max_drawdown']:.2%} | {r['win_rate']:.1%} | {r['sell_trades']} | ✅ 成功 |")
        else:
            failed_stocks.append((code, r.get('stock_name', STOCKS.get(code, '')), r.get('error', '未知错误')))
            lines.append(f"| {code} | {r.get('stock_name', STOCKS.get(code, ''))} | - | - | - | - | ❌ {r.get('error', '失败')} |")
    
    lines.append("")
    
    # 汇总统计
    if successful_results:
        returns = [r['total_return'] for r in successful_results.values()]
        win_rates = [r['win_rate'] for r in successful_results.values()]
        drawdowns = [r['max_drawdown'] for r in successful_results.values()]
        trade_counts = [r['sell_trades'] for r in successful_results.values()]
        
        positive_returns = [r for r in returns if r > 0]
        
        lines.extend([
            "## 汇总统计",
            "",
            f"- **测试股票总数**: {len(STOCKS)}",
            f"- **成功回测**: {len(successful_results)}",
            f"- **失败/无数据**: {len(failed_stocks)}",
            f"- **平均总收益**: {np.mean(returns):+.2%}",
            f"- **收益中位数**: {np.median(returns):+.2%}",
            f"- **正收益股票数**: {len(positive_returns)}/{len(returns)}",
            f"- **收益最高**: {max(returns):+.2%}",
            f"- **收益最低**: {min(returns):+.2%}",
            f"- **平均胜率**: {np.mean(win_rates):.1%}",
            f"- **平均最大回撤**: {np.mean(drawdowns):.2%}",
            f"- **总交易次数**: {sum(trade_counts)}",
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
            f"- **止损次数**: {r['stoploss_count']}",
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
        "*报告由 InvestMindPro 自动生成*"
    ])
    
    return '\n'.join(lines)

# ======== 主函数 ========

def main():
    """主函数"""
    logger.info(f"\n{'#'*70}")
    logger.info(f"# EMA V2.1 策略批量回测")
    logger.info(f"# 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"# 股票数量: {len(STOCKS)}")
    logger.info(f"# 回测区间: {START_DATE} - {END_DATE}")
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
    json_file = RESULTS_DIR / "ema_v2_batch_results.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2, default=str)
    
    # 生成并保存Markdown报告
    report = generate_report(all_results)
    report_file = RESULTS_DIR / "EMA_V2_BATCH_BACKTEST.md"
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
