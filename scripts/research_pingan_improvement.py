#!/usr/bin/env python3
"""
中国平安(601318)改进方案研究
问题: EMA趋势策略在低波动大盘股上效果不佳
目标: 寻找更适合的改进方案
"""

import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, str(Path(__file__).parent.parent / 'strategies'))
from ema_v2 import EMAV2Strategy, BacktestResult

def load_stock_data(symbol: str, data_dir: Path) -> pd.DataFrame:
    """加载股票数据"""
    csv_path = data_dir / f"{symbol}.csv"
    df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
    df.columns = [c.lower() for c in df.columns]
    df.attrs['symbol'] = symbol
    return df

def load_market_data(data_dir: Path) -> pd.DataFrame:
    """加载沪深300数据"""
    return load_stock_data('000300', data_dir)

class PingAnImprovedStrategy(EMAV2Strategy):
    """
    中国平安专用改进策略
    核心改进:
    1. 加长周期减少噪音 (EMA10/50 vs EMA7/20)
    2. 添加布林带过滤 (避开震荡区间)
    3. 添加RSI过滤 (超买超卖)
    4. 双均线确认 (需要MA20和MA60都向上)
    """
    
    def __init__(self, params: dict = None):
        super().__init__(params)
        self.bb_period = params.get('bb_period', 20)
        self.bb_std = params.get('bb_std', 2.0)
        self.rsi_period = params.get('rsi_period', 14)
        self.rsi_buy_max = params.get('rsi_buy_max', 60)  # RSI低于60才能买
        self.ma_confirm = params.get('ma_confirm', True)  # 双均线确认
        
    def generate_signals(self, df: pd.DataFrame, market_data: pd.DataFrame = None) -> pd.DataFrame:
        data = df.copy()
        
        # 计算EMA
        data['ema_fast'] = data['close'].ewm(span=self.fast_ema, adjust=False).mean()
        data['ema_slow'] = data['close'].ewm(span=self.slow_ema, adjust=False).mean()
        
        # 计算布林带
        data['bb_middle'] = data['close'].rolling(window=self.bb_period).mean()
        bb_std = data['close'].rolling(window=self.bb_period).std()
        data['bb_upper'] = data['bb_middle'] + self.bb_std * bb_std
        data['bb_lower'] = data['bb_middle'] - self.bb_std * bb_std
        data['bb_width'] = (data['bb_upper'] - data['bb_lower']) / data['bb_middle']
        
        # 计算RSI
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / (loss + 0.001)
        data['rsi'] = 100 - (100 / (1 + rs))
        
        # 双均线确认
        if self.ma_confirm:
            data['ma20'] = data['close'].rolling(window=20).mean()
            data['ma60'] = data['close'].rolling(window=60).mean()
            data['ma_bullish'] = (data['ma20'] > data['ma20'].shift(5)) & (data['ma60'] > data['ma60'].shift(10))
        else:
            data['ma_bullish'] = True
        
        # 布林带过滤: 价格在布林带内部且带宽适中(非极端震荡)
        data['bb_valid'] = (data['close'] > data['bb_lower']) & (data['close'] < data['bb_upper'] * 0.95) & (data['bb_width'] > 0.02)
        
        # RSI过滤: 不超买才能买入
        data['rsi_valid'] = data['rsi'] < self.rsi_buy_max
        
        # EMA交叉信号
        data['ema_cross_up'] = (data['ema_fast'] > data['ema_slow']) & (data['ema_fast'].shift(1) <= data['ema_slow'].shift(1))
        data['ema_cross_down'] = (data['ema_fast'] < data['ema_slow']) & (data['ema_fast'].shift(1) >= data['ema_slow'].shift(1))
        
        # 改进的买入信号: EMA金叉 + 布林带过滤 + RSI过滤 + 均线确认
        data['buy_signal'] = data['ema_cross_up'] & data['bb_valid'] & data['rsi_valid'] & data['ma_bullish']
        
        # 计算ATR止损
        data['atr'] = self.calculate_atr(data)
        data['stop_loss'] = data['close'] - self.atr_multiplier * data['atr']
        
        # 卖出信号: EMA死叉 或 价格跌破止损
        data['sell_signal'] = data['ema_cross_down'] | (data['close'] < data['stop_loss'].shift(1))
        
        return data

def test_ping_an_improvements():
    """测试中国平安的各种改进方案"""
    
    data_dir = Path(__file__).parent.parent / 'data'
    stock_data = load_stock_data('601318', data_dir)
    market_data = load_market_data(data_dir)
    
    print("=" * 70)
    print("中国平安(601318)改进方案研究")
    print("=" * 70)
    print(f"数据范围: {stock_data.index[0].strftime('%Y-%m-%d')} ~ {stock_data.index[-1].strftime('%Y-%m-%d')}")
    print(f"数据条数: {len(stock_data)}")
    print()
    
    results = []
    
    # 方案1: 原参数基准
    print("【方案1】原EMA V2参数")
    params1 = {'fast_ema': 7, 'slow_ema': 20, 'atr_period': 14, 'atr_multiplier': 1.0, 'market_filter': True}
    strategy1 = EMAV2Strategy(params1)
    result1 = strategy1.run_backtest(stock_data, market_data)
    print(f"  总收益: {result1.total_return:+.2f}% | 胜率: {result1.win_rate:.1f}% | 交易次数: {result1.total_trades}")
    results.append({'方案': '原参数基准', '收益': result1.total_return, '胜率': result1.win_rate, '次数': result1.total_trades, '回撤': result1.max_drawdown, 'Sharpe': result1.sharpe_ratio})
    
    # 方案2: 加长周期
    print("\n【方案2】加长EMA周期 (10/50)")
    params2 = {'fast_ema': 10, 'slow_ema': 50, 'atr_period': 14, 'atr_multiplier': 1.5, 'market_filter': True}
    strategy2 = EMAV2Strategy(params2)
    result2 = strategy2.run_backtest(stock_data, market_data)
    print(f"  总收益: {result2.total_return:+.2f}% | 胜率: {result2.win_rate:.1f}% | 交易次数: {result2.total_trades}")
    results.append({'方案': '加长周期', '收益': result2.total_return, '胜率': result2.win_rate, '次数': result2.total_trades, '回撤': result2.max_drawdown, 'Sharpe': result2.sharpe_ratio})
    
    # 方案3: 超长周期
    print("\n【方案3】超长EMA周期 (15/60)")
    params3 = {'fast_ema': 15, 'slow_ema': 60, 'atr_period': 14, 'atr_multiplier': 2.0, 'market_filter': True}
    strategy3 = EMAV2Strategy(params3)
    result3 = strategy3.run_backtest(stock_data, market_data)
    print(f"  总收益: {result3.total_return:+.2f}% | 胜率: {result3.win_rate:.1f}% | 交易次数: {result3.total_trades}")
    results.append({'方案': '超长周期', '收益': result3.total_return, '胜率': result3.win_rate, '次数': result3.total_trades, '回撤': result3.max_drawdown, 'Sharpe': result3.sharpe_ratio})
    
    # 方案4: 改进策略 - 加长周期+布林带+RSI
    print("\n【方案4】改进策略 (EMA10/50 + 布林带过滤 + RSI过滤)")
    params4 = {
        'fast_ema': 10, 'slow_ema': 50, 'atr_period': 14, 'atr_multiplier': 1.5, 'market_filter': True,
        'bb_period': 20, 'bb_std': 2.0, 'rsi_period': 14, 'rsi_buy_max': 60, 'ma_confirm': True
    }
    strategy4 = PingAnImprovedStrategy(params4)
    result4 = strategy4.run_backtest(stock_data, market_data)
    print(f"  总收益: {result4.total_return:+.2f}% | 胜率: {result4.win_rate:.1f}% | 交易次数: {result4.total_trades}")
    results.append({'方案': '改进策略V1', '收益': result4.total_return, '胜率': result4.win_rate, '次数': result4.total_trades, '回撤': result4.max_drawdown, 'Sharpe': result4.sharpe_ratio})
    
    # 方案5: 改进策略 - 更长周期
    print("\n【方案5】改进策略V2 (EMA15/60 + 布林带过滤 + RSI过滤)")
    params5 = {
        'fast_ema': 15, 'slow_ema': 60, 'atr_period': 14, 'atr_multiplier': 2.0, 'market_filter': True,
        'bb_period': 20, 'bb_std': 2.0, 'rsi_period': 14, 'rsi_buy_max': 60, 'ma_confirm': True
    }
    strategy5 = PingAnImprovedStrategy(params5)
    result5 = strategy5.run_backtest(stock_data, market_data)
    print(f"  总收益: {result5.total_return:+.2f}% | 胜率: {result5.win_rate:.1f}% | 交易次数: {result5.total_trades}")
    results.append({'方案': '改进策略V2', '收益': result5.total_return, '胜率': result5.win_rate, '次数': result5.total_trades, '回撤': result5.max_drawdown, 'Sharpe': result5.sharpe_ratio})
    
    # 方案6: 纯长期趋势跟踪
    print("\n【方案6】纯长期趋势 (EMA20/120)")
    params6 = {'fast_ema': 20, 'slow_ema': 120, 'atr_period': 14, 'atr_multiplier': 3.0, 'market_filter': True}
    strategy6 = EMAV2Strategy(params6)
    result6 = strategy6.run_backtest(stock_data, market_data)
    print(f"  总收益: {result6.total_return:+.2f}% | 胜率: {result6.win_rate:.1f}% | 交易次数: {result6.total_trades}")
    results.append({'方案': '纯长期趋势', '收益': result6.total_return, '胜率': result6.win_rate, '次数': result6.total_trades, '回撤': result6.max_drawdown, 'Sharpe': result6.sharpe_ratio})
    
    # 汇总
    print("\n" + "=" * 70)
    print("结果汇总对比")
    print("=" * 70)
    print(f"{'方案':<15} {'总收益':>10} {'胜率':>8} {'交易次数':>10} {'最大回撤':>10} {'Sharpe':>8}")
    print("-" * 70)
    for r in results:
        print(f"{r['方案']:<15} {r['收益']:>+9.2f}% {r['胜率']:>7.1f}% {r['次数']:>10} {r['回撤']:>9.2f}% {r['Sharpe']:>8.2f}")
    
    # 找出最佳方案
    best = max(results, key=lambda x: x['收益'])
    print(f"\n✅ 最佳方案: {best['方案']} (收益 {best['收益']:+.2f}%)")
    
    # 生成报告
    report = {
        'symbol': '601318',
        'name': '中国平安',
        'test_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'data_range': f"{stock_data.index[0].strftime('%Y-%m-%d')} ~ {stock_data.index[-1].strftime('%Y-%m-%d')}",
        'baseline': results[0],
        'results': results,
        'recommendation': f"推荐方案: {best['方案']}",
        'note': '低波动大盘股，趋势策略效果有限，建议改用价值投资策略或更长期趋势跟踪'
    }
    
    output_dir = Path(__file__).parent.parent / 'results'
    output_dir.mkdir(exist_ok=True)
    report_file = output_dir / f"pingan_improvement_{datetime.now().strftime('%Y%m%d')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n📄 报告已保存: {report_file}")
    
    return report

if __name__ == '__main__':
    test_ping_an_improvements()
