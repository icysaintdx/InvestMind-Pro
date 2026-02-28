#!/usr/bin/env python3
"""
短线回测脚本 - 结合新闻情绪数据
使用最近1-3个月数据，测试微调过的EMA V2策略
"""

import json
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

# 导入必要的模块
try:
    from services.stock_data_service import StockDataService
    from services.indicator_service import IndicatorService
except ImportError:
    print("Warning: Could not import backend services")
    StockDataService = None
    IndicatorService = None


class ShortTermBacktest:
    """短线回测器 - 结合新闻情绪"""
    
    def __init__(self, db_path: str = "data/news_storage/news_database.db"):
        self.db_path = db_path
        self.news_cache = {}
        self.trades = []
        self.portfolio = {
            'cash': 1000000,  # 初始资金100万
            'positions': {},  # 持仓
            'total_value': 1000000
        }
        
    def load_optimized_params(self, params_file: str = "results/extended_optimized_params_20260228_042042.json") -> Dict:
        """加载优化后的策略参数"""
        try:
            with open(params_file, 'r', encoding='utf-8') as f:
                params = json.load(f)
            print(f"✅ 加载了 {len(params)} 只股票的优化参数")
            return params
        except Exception as e:
            print(f"❌ 加载参数失败: {e}")
            # 使用默认参数
            return {
                "300274": {"fast_ema": 10, "slow_ema": 20, "atr_period": 14, "atr_multiplier": 2.0},
                "002594": {"fast_ema": 10, "slow_ema": 25, "atr_period": 14, "atr_multiplier": 2.0},
                "600519": {"fast_ema": 12, "slow_ema": 30, "atr_period": 14, "atr_multiplier": 2.0},
            }
    
    def get_news_sentiment(self, stock_code: str, date: str) -> Dict:
        """获取某只股票某天的情绪数据"""
        if not os.path.exists(self.db_path):
            return {'sentiment_score': 0, 'urgency_score': 0, 'impact_score': 0, 'count': 0}
        
        cache_key = f"{stock_code}_{date}"
        if cache_key in self.news_cache:
            return self.news_cache[cache_key]
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 查询相关新闻
            cursor.execute("""
                SELECT sentiment_score, urgency_score, impact_score, priority
                FROM news_articles
                WHERE related_stocks LIKE ? 
                AND DATE(publish_time) = ?
            """, (f'%"{stock_code}"%', date))
            
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                result = {'sentiment_score': 0, 'urgency_score': 0, 'impact_score': 0, 'count': 0}
            else:
                result = {
                    'sentiment_score': np.mean([r[0] for r in rows]),
                    'urgency_score': np.mean([r[1] for r in rows]),
                    'impact_score': np.mean([r[2] for r in rows]),
                    'count': len(rows)
                }
            
            self.news_cache[cache_key] = result
            return result
            
        except Exception as e:
            print(f"Error querying news: {e}")
            return {'sentiment_score': 0, 'urgency_score': 0, 'impact_score': 0, 'count': 0}
    
    def calculate_ema(self, prices: pd.Series, fast_period: int, slow_period: int) -> Tuple[pd.Series, pd.Series]:
        """计算EMA"""
        fast_ema = prices.ewm(span=fast_period, adjust=False).mean()
        slow_ema = prices.ewm(span=slow_period, adjust=False).mean()
        return fast_ema, slow_ema
    
    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """计算ATR"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        atr = true_range.ewm(span=period, adjust=False).mean()
        return atr
    
    def get_stock_data(self, stock_code: str, days: int = 90) -> pd.DataFrame:
        """获取股票数据 (使用akshare或本地数据)"""
        try:
            import akshare as ak
            # 获取日线数据
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
            
            # 添加后缀
            if stock_code.startswith('6'):
                symbol = f"{stock_code}.SH"
            else:
                symbol = f"{stock_code}.SZ"
            
            df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", 
                                    start_date=start_date, end_date=end_date, adjust="qfq")
            
            if df is None or df.empty:
                print(f"⚠️ 无法获取 {stock_code} 的数据")
                return pd.DataFrame()
            
            # 标准化列名
            df.columns = [col.lower().replace(' ', '_') for col in df.columns]
            df.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount',
                '振幅': 'amplitude',
                '涨跌幅': 'pct_change',
                '涨跌额': 'change',
                '换手率': 'turnover'
            }, inplace=True)
            
            return df
            
        except Exception as e:
            print(f"❌ 获取 {stock_code} 数据失败: {e}")
            return pd.DataFrame()
    
    def backtest_stock(self, stock_code: str, params: Dict, days: int = 90) -> Dict:
        """对单只股票进行短线回测"""
        print(f"\n📊 回测 {stock_code} ({params.get('name', 'Unknown')})")
        
        # 获取数据
        df = self.get_stock_data(stock_code, days)
        if df.empty or len(df) < 30:
            print(f"⚠️ 数据不足，跳过")
            return None
        
        # 获取参数
        fast_ema = params.get('fast_ema', 10)
        slow_ema = params.get('slow_ema', 25)
        atr_period = params.get('atr_period', 14)
        atr_multiplier = params.get('atr_multiplier', 2.0)
        
        # 计算指标
        df['fast_ema'] = df['close'].ewm(span=fast_ema, adjust=False).mean()
        df['slow_ema'] = df['close'].ewm(span=slow_ema, adjust=False).mean()
        
        # 计算ATR和止损线
        df['atr'] = self.calculate_atr(df, atr_period)
        df['stop_loss'] = df['close'] - df['atr'] * atr_multiplier
        
        # 信号检测
        df['signal'] = 0
        df.loc[df['fast_ema'] > df['slow_ema'], 'signal'] = 1  # 买入信号
        df.loc[df['fast_ema'] < df['slow_ema'], 'signal'] = -1  # 卖出信号
        
        # 交易模拟
        trades = []
        position = 0  # 0: 空仓, 1: 持仓
        entry_price = 0
        entry_date = None
        stop_loss_price = 0
        
        for i in range(slow_ema + 5, len(df)):
            row = df.iloc[i]
            date = str(row['date']) if 'date' in row else str(i)
            
            # 获取情绪数据
            sentiment = self.get_news_sentiment(stock_code, str(date)[:10])
            sentiment_boost = sentiment['sentiment_score'] * 0.1 if sentiment['count'] > 0 else 0
            
            # 金叉买入
            if position == 0 and row['signal'] == 1:
                position = 1
                entry_price = row['close']
                entry_date = date
                stop_loss_price = row['stop_loss']
                
                trades.append({
                    'date': date,
                    'action': 'BUY',
                    'price': entry_price,
                    'sentiment': sentiment['sentiment_score'],
                    'sentiment_boost': sentiment_boost
                })
            
            # 止损或死叉卖出
            elif position == 1:
                exit_reason = None
                exit_price = row['close']
                
                if row['close'] < stop_loss_price:
                    exit_reason = 'STOP_LOSS'
                elif row['signal'] == -1:
                    exit_reason = 'SELL_SIGNAL'
                
                if exit_reason:
                    position = 0
                    pnl = (exit_price - entry_price) / entry_price * 100
                    
                    trades.append({
                        'date': date,
                        'action': 'SELL',
                        'price': exit_price,
                        'reason': exit_reason,
                        'pnl': pnl,
                        'sentiment': sentiment['sentiment_score']
                    })
        
        # 如果还持仓，以最后价格平仓
        if position == 1:
            exit_price = df.iloc[-1]['close']
            pnl = (exit_price - entry_price) / entry_price * 100
            trades.append({
                'date': str(df.iloc[-1]['date']),
                'action': 'SELL',
                'price': exit_price,
                'reason': 'END_OF_PERIOD',
                'pnl': pnl
            })
        
        # 计算统计
        if len(trades) >= 2:
            buy_trades = [t for t in trades if t['action'] == 'BUY']
            sell_trades = [t for t in trades if t['action'] == 'SELL']
            
            if sell_trades:
                pnls = [t['pnl'] for t in sell_trades]
                win_rate = len([p for p in pnls if p > 0]) / len(pnls) * 100
                avg_return = np.mean(pnls)
                total_return = np.sum(pnls)
            else:
                win_rate = 0
                avg_return = 0
                total_return = 0
            
            result = {
                'stock_code': stock_code,
                'name': params.get('name', 'Unknown'),
                'total_trades': len(buy_trades),
                'win_rate': win_rate,
                'avg_return': avg_return,
                'total_return': total_return,
                'trades': trades,
                'data_period': f"{df.iloc[0]['date']} to {df.iloc[-1]['date']}"
            }
            
            print(f"   交易次数: {len(buy_trades)}")
            print(f"   胜率: {win_rate:.1f}%")
            print(f"   平均收益: {avg_return:.2f}%")
            print(f"   总收益: {total_return:.2f}%")
            
            return result
        
        return None
    
    def run_backtest(self, days: int = 90):
        """运行完整回测"""
        print("=" * 60)
        print(f"📈 短线回测开始 - 最近 {days} 天")
        print("=" * 60)
        
        # 加载优化参数
        params_dict = self.load_optimized_params()
        
        # 回测每只股票
        results = []
        for stock_code, params in params_dict.items():
            result = self.backtest_stock(stock_code, params, days)
            if result:
                results.append(result)
        
        # 生成报告
        self.generate_report(results, days)
        
        return results
    
    def generate_report(self, results: List[Dict], days: int):
        """生成回测报告"""
        if not results:
            print("\n❌ 无有效回测结果")
            return
        
        print("\n" + "=" * 60)
        print("📋 回测汇总报告")
        print("=" * 60)
        
        total_trades = sum(r['total_trades'] for r in results)
        avg_win_rate = np.mean([r['win_rate'] for r in results])
        avg_return = np.mean([r['avg_return'] for r in results])
        total_return = np.sum([r['total_return'] for r in results])
        
        print(f"\n回测周期: 最近 {days} 天")
        print(f"回测股票数: {len(results)}")
        print(f"总交易次数: {total_trades}")
        print(f"平均胜率: {avg_win_rate:.1f}%")
        print(f"平均收益: {avg_return:.2f}%")
        print(f"组合总收益: {total_return:.2f}%")
        
        # 保存报告
        report_file = f"results/short_term_backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'backtest_date': datetime.now().isoformat(),
                'period_days': days,
                'summary': {
                    'stocks': len(results),
                    'total_trades': total_trades,
                    'avg_win_rate': avg_win_rate,
                    'avg_return': avg_return,
                    'total_return': total_return
                },
                'details': results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 报告已保存: {report_file}")


if __name__ == "__main__":
    # 创建回测器
    backtest = ShortTermBacktest()
    
    # 运行回测 - 最近60天
    results = backtest.run_backtest(days=60)
