#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EMA V2 逐个股票回测脚本
对7只股票使用EMA V2策略进行逐个回测
"""

import pandas as pd
import numpy as np
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Tuple
import warnings
warnings.filterwarnings('ignore')

# 添加项目路径
sys.path.insert(0, '/home/icysaintdx/.openclaw/workspace-investmindpro/InvestMindPro/backend')

# 回测配置
INITIAL_CAPITAL = 100000.0
DATA_DIR = '/home/icysaintdx/.openclaw/workspace-investmindpro/InvestMindPro/backend/data/backtest_cache'
OUTPUT_DIR = '/home/icysaintdx/.openclaw/workspace-investmindpro/InvestMindPro/backend/backtest_results/individual'

# 股票列表
STOCKS = [
    ('000333', '美的集团'),
    ('000651', '格力电器'),
    ('000858', '五粮液'),
    ('600276', '恒瑞医药'),
    ('600519', '贵州茅台'),
    ('601318', '中国平安'),
    ('601888', '中国中免')
]

# EMA参数组合
PARAM_COMBINATIONS = [
    {'ema_fast': 5, 'ema_slow': 30, 'name': '保守型'},
    {'ema_fast': 10, 'ema_slow': 60, 'name': '平衡型'},
    {'ema_fast': 20, 'ema_slow': 120, 'name': '激进型'}
]

class EMABacktest:
    """简化版EMA回测引擎"""
    
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.reset()
    
    def reset(self):
        self.capital = self.initial_capital
        self.position = 0
        self.position_value = 0.0
        self.entry_price = 0.0
        self.trades = []
        self.equity_curve = []
    
    def calculate_indicators(self, df: pd.DataFrame, ema_fast: int, ema_slow: int) -> pd.DataFrame:
        """计算EMA指标"""
        df = df.copy()
        df['ema_fast'] = df['close'].ewm(span=ema_fast, adjust=False).mean()
        df['ema_slow'] = df['close'].ewm(span=ema_slow, adjust=False).mean()
        
        # ATR计算
        high_low = df['high'] - df['low']
        high_close = (df['high'] - df['close'].shift()).abs()
        low_close = (df['low'] - df['close'].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = tr.ewm(span=14, adjust=False).mean()
        
        return df
    
    def run_backtest(self, df: pd.DataFrame, params: Dict[str, Any], stock_code: str) -> Dict[str, Any]:
        """运行回测"""
        self.reset()
        
        ema_fast = params['ema_fast']
        ema_slow = params['ema_slow']
        
        # 计算指标
        df = self.calculate_indicators(df, ema_fast, ema_slow)
        
        if len(df) < ema_slow + 10:
            return {'success': False, 'error': '数据不足'}
        
        # 开始回测
        for i in range(ema_slow + 5, len(df)):
            current = df.iloc[i]
            prev = df.iloc[i-1]
            
            price = float(current['close'])
            date = str(current.name) if hasattr(current, 'name') else str(i)
            
            # 金叉/死叉判断
            golden_cross = (current['ema_fast'] > current['ema_slow']) and \
                          (prev['ema_fast'] <= prev['ema_slow'])
            death_cross = (current['ema_fast'] < current['ema_slow']) and \
                         (prev['ema_fast'] >= prev['ema_slow'])
            
            # 买入逻辑
            if self.position == 0 and golden_cross:
                # 计算仓位（使用半Kelly简化版：20%固定）
                position_pct = 0.2
                position_value = self.capital * position_pct
                shares = int(position_value / price)
                
                if shares > 0:
                    cost = shares * price
                    if cost <= self.capital:
                        self.position = shares
                        self.entry_price = price
                        self.position_value = cost
                        self.capital -= cost
                        
                        self.trades.append({
                            'type': 'BUY',
                            'date': date,
                            'price': price,
                            'shares': shares,
                            'value': cost
                        })
            
            # 卖出逻辑
            elif self.position > 0 and death_cross:
                sell_value = self.position * price
                self.capital += sell_value
                
                pnl = sell_value - self.position_value
                pnl_pct = (price - self.entry_price) / self.entry_price * 100
                
                self.trades.append({
                    'type': 'SELL',
                    'date': date,
                    'price': price,
                    'shares': self.position,
                    'value': sell_value,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct
                })
                
                self.position = 0
                self.position_value = 0
                self.entry_price = 0
            
            # 记录权益曲线
            total_value = self.capital + (self.position * price if self.position > 0 else 0)
            self.equity_curve.append({
                'date': date,
                'value': total_value,
                'price': price
            })
        
        # 计算最终收益
        final_price = float(df.iloc[-1]['close'])
        final_value = self.capital + (self.position * final_price if self.position > 0 else 0)
        total_return = (final_value - self.initial_capital) / self.initial_capital * 100
        
        # 计算胜率
        closed_trades = [t for t in self.trades if t['type'] == 'SELL']
        win_trades = [t for t in closed_trades if t.get('pnl', 0) > 0]
        win_rate = len(win_trades) / len(closed_trades) * 100 if closed_trades else 0
        
        # 计算最大回撤
        max_drawdown = self._calculate_max_drawdown()
        
        return {
            'success': True,
            'stock_code': stock_code,
            'params': params,
            'initial_capital': self.initial_capital,
            'final_value': round(final_value, 2),
            'total_return_pct': round(total_return, 2),
            'total_trades': len(closed_trades),
            'win_trades': len(win_trades),
            'loss_trades': len(closed_trades) - len(win_trades),
            'win_rate_pct': round(win_rate, 2),
            'max_drawdown_pct': round(max_drawdown, 2),
            'trades': self.trades,
            'equity_curve': self.equity_curve
        }
    
    def _calculate_max_drawdown(self) -> float:
        """计算最大回撤"""
        if not self.equity_curve:
            return 0.0
        
        values = [e['value'] for e in self.equity_curve]
        peak = values[0]
        max_dd = 0.0
        
        for value in values:
            if value > peak:
                peak = value
            dd = (peak - value) / peak * 100
            if dd > max_dd:
                max_dd = dd
        
        return max_dd


def load_stock_data(stock_code: str) -> pd.DataFrame:
    """加载股票数据"""
    file_path = os.path.join(DATA_DIR, f'{stock_code}_20200101_20241231.csv')
    if not os.path.exists(file_path):
        return None
    
    df = pd.read_csv(file_path)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    df.sort_index(inplace=True)
    return df


def run_individual_backtests():
    """运行逐个股票回测"""
    print("=" * 60)
    print("InvestMindPro EMA V2 逐个股票回测")
    print("=" * 60)
    print()
    
    # 创建输出目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    all_results = []
    
    for stock_code, stock_name in STOCKS:
        print(f"\n📊 回测股票: {stock_code} ({stock_name})")
        print("-" * 40)
        
        # 加载数据
        df = load_stock_data(stock_code)
        if df is None:
            print(f"  ❌ 数据文件不存在: {stock_code}")
            continue
        
        print(f"  数据范围: {df.index[0]} 至 {df.index[-1]}")
        print(f"  数据条数: {len(df)}")
        
        stock_results = []
        
        for params in PARAM_COMBINATIONS:
            backtest = EMABacktest()
            result = backtest.run_backtest(df, params, stock_code)
            
            if result['success']:
                stock_results.append(result)
                print(f"  ✅ {params['name']}: 收益{result['total_return_pct']:+.2f}% | "
                      f"胜率{result['win_rate_pct']:.1f}% | 交易{result['total_trades']}次")
            else:
                print(f"  ❌ {params['name']}: {result.get('error', '失败')}")
        
        # 保存单个股票结果
        if stock_results:
            output_file = os.path.join(OUTPUT_DIR, f'{stock_code}_ema_v2_results.json')
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(stock_results, f, ensure_ascii=False, indent=2)
            print(f"  💾 结果已保存: {output_file}")
            all_results.extend(stock_results)
    
    # 生成汇总报告
    generate_summary_report(all_results)
    
    return all_results


def generate_summary_report(all_results: List[Dict[str, Any]]):
    """生成汇总报告"""
    if not all_results:
        print("\n❌ 没有回测结果")
        return
    
    print("\n" + "=" * 60)
    print("生成汇总报告...")
    print("=" * 60)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = os.path.join(OUTPUT_DIR, f'ema_v2_summary_report_{timestamp}.md')
    
    # 按股票分组
    by_stock = {}
    for r in all_results:
        code = r['stock_code']
        if code not in by_stock:
            by_stock[code] = []
        by_stock[code].append(r)
    
    # 生成Markdown报告
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# EMA V2 策略逐个股票回测报告\n\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## 回测配置\n\n")
        f.write(f"- 初始资金: {INITIAL_CAPITAL:,.0f}元\n")
        f.write(f"- 股票数量: {len(by_stock)}只\n")
        f.write(f"- 参数组合: {len(PARAM_COMBINATIONS)}种\n")
        f.write("- 策略: EMA突破 V2\n\n")
        
        # 汇总表格
        f.write("## 各股票最佳参数表现\n\n")
        f.write("| 股票代码 | 股票名称 | 最佳参数 | 收益率 | 胜率 | 交易次数 | 最大回撤 |\n")
        f.write("|---------|---------|---------|-------|------|---------|---------|\n")
        
        for stock_code, stock_name in STOCKS:
            if stock_code not in by_stock:
                continue
            
            results = by_stock[stock_code]
            best = max(results, key=lambda x: x['total_return_pct'])
            
            f.write(f"| {stock_code} | {stock_name} | {best['params']['name']} | "
                   f"{best['total_return_pct']:+.2f}% | {best['win_rate_pct']:.1f}% | "
                   f"{best['total_trades']} | {best['max_drawdown_pct']:.2f}% |\n")
        
        # 详细结果
        f.write("\n## 详细回测结果\n\n")
        
        for stock_code, stock_name in STOCKS:
            if stock_code not in by_stock:
                continue
            
            f.write(f"### {stock_code} ({stock_name})\n\n")
            f.write("| 参数组合 | 收益率 | 最终资金 | 胜率 | 交易次数 | 最大回撤 |\n")
            f.write("|---------|-------|---------|------|---------|---------|\n")
            
            for r in sorted(by_stock[stock_code], key=lambda x: x['total_return_pct'], reverse=True):
                f.write(f"| {r['params']['name']} | {r['total_return_pct']:+.2f}% | "
                       f"{r['final_value']:,.0f} | {r['win_rate_pct']:.1f}% | "
                       f"{r['total_trades']} | {r['max_drawdown_pct']:.2f}% |\n")
            
            f.write("\n")
        
        # 统计摘要
        f.write("## 统计摘要\n\n")
        returns = [r['total_return_pct'] for r in all_results]
        win_rates = [r['win_rate_pct'] for r in all_results]
        
        f.write(f"- **平均收益率**: {np.mean(returns):.2f}%\n")
        f.write(f"- **最高收益率**: {max(returns):.2f}%\n")
        f.write(f"- **最低收益率**: {min(returns):.2f}%\n")
        f.write(f"- **平均胜率**: {np.mean(win_rates):.1f}%\n")
        f.write(f"- **正收益组合数**: {sum(1 for r in returns if r > 0)}/{len(returns)}\n")
    
    print(f"\n✅ 汇总报告已生成: {report_file}")
    
    # 打印简报表格
    print("\n" + "=" * 60)
    print("回测结果摘要")
    print("=" * 60)
    print(f"{'股票':<10} {'最佳参数':<10} {'收益率':<10} {'胜率':<8} {'交易次数':<8}")
    print("-" * 60)
    
    for stock_code, stock_name in STOCKS:
        if stock_code not in by_stock:
            continue
        results = by_stock[stock_code]
        best = max(results, key=lambda x: x['total_return_pct'])
        print(f"{stock_code} ({stock_name[:4]}) {best['params']['name']:<8} "
              f"{best['total_return_pct']:+7.2f}%   {best['win_rate_pct']:5.1f}%    {best['total_trades']:>3}次")


if __name__ == '__main__':
    results = run_individual_backtests()
    print("\n" + "=" * 60)
    print("回测完成!")
    print("=" * 60)
