#!/usr/bin/env python3
"""
EMA V2.1 回测执行脚本
逐个股票执行回测，支持从本地数据或在线数据源获取
"""

import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict
import warnings
warnings.filterwarnings('ignore')

# 添加策略模块路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'strategies'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'data'))
from ema_v2 import EMAV2Strategy, BacktestResult

# 尝试导入akshare数据源
try:
    from akshare_datasource import AkshareDataSource
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False


class LocalDataSource:
    """本地数据源 - 使用本地CSV文件"""
    
    def __init__(self, data_dir: str = "../data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # 股票代码映射
        self.symbol_map = {
            # 高波动股票
            '601888': {'name': '中国中免', 'type': 'high_volatility'},
            '300750': {'name': '宁德时代', 'type': 'high_volatility'},
            '002594': {'name': '比亚迪', 'type': 'high_volatility'},
            
            # 中波动股票
            '000858': {'name': '五粮液', 'type': 'medium_volatility'},
            '000333': {'name': '美的集团', 'type': 'medium_volatility'},
            '000651': {'name': '格力电器', 'type': 'medium_volatility'},
            '600276': {'name': '恒瑞医药', 'type': 'medium_volatility'},
            
            # 低波动股票
            '600519': {'name': '贵州茅台', 'type': 'low_volatility'},
            '601318': {'name': '中国平安', 'type': 'low_volatility'},
            '000001': {'name': '平安银行', 'type': 'low_volatility'},
            '600036': {'name': '招商银行', 'type': 'low_volatility'},
        }
    
    def generate_sample_data(self, symbol: str, days: int = 500) -> pd.DataFrame:
        """生成模拟股票数据 (用于测试)"""
        np.random.seed(int(symbol))
        
        end_date = datetime.now()
        dates = pd.date_range(end=end_date, periods=days, freq='B')  # 工作日
        
        # 生成价格序列 (随机游走)
        returns = np.random.normal(0.0005, 0.02, days)  # 日收益率
        price = 100 * np.exp(np.cumsum(returns))
        
        # 生成OHLC
        data = pd.DataFrame(index=dates)
        data['close'] = price
        data['high'] = price * (1 + np.abs(np.random.normal(0, 0.01, days)))
        data['low'] = price * (1 - np.abs(np.random.normal(0, 0.01, days)))
        data['open'] = price * (1 + np.random.normal(0, 0.005, days))
        data['volume'] = np.random.randint(1000000, 10000000, days)
        
        data.attrs['symbol'] = symbol
        return data
    
    def get_stock_data(self, symbol: str, start_date: str = None, end_date: str = None) -> Optional[pd.DataFrame]:
        """获取股票数据"""
        # 优先从本地文件读取
        csv_path = self.data_dir / f"{symbol}.csv"
        if csv_path.exists():
            df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
            df.attrs['symbol'] = symbol
            return df
        
        # 否则生成模拟数据
        print(f"[INFO] 使用模拟数据: {symbol}")
        return self.generate_sample_data(symbol)
    
    def get_market_data(self) -> Optional[pd.DataFrame]:
        """获取大盘数据 (沪深300)"""
        # 生成模拟沪深300数据
        return self.generate_sample_data('000300', days=500)
    
    def get_stock_info(self, symbol: str) -> Dict:
        """获取股票信息"""
        return self.symbol_map.get(symbol, {'name': symbol, 'type': 'medium_volatility'})


def run_single_stock_backtest(symbol: str, data_source: LocalDataSource, 
                              initial_capital: float = 100000.0) -> Dict:
    """
    执行单只股票回测
    
    Args:
        symbol: 股票代码
        data_source: 数据源
        initial_capital: 初始资金
        
    Returns:
        回测结果字典
    """
    print(f"\n{'='*60}")
    print(f"开始回测: {symbol}")
    print(f"{'='*60}")
    
    # 获取股票数据
    stock_data = data_source.get_stock_data(symbol)
    if stock_data is None or len(stock_data) < 100:
        print(f"[ERROR] 数据不足: {symbol}")
        return None
    
    # 获取大盘数据
    market_data = data_source.get_market_data()
    
    # 获取股票信息和参数
    stock_info = data_source.get_stock_info(symbol)
    volatility_type = stock_info.get('type', 'medium_volatility')
    
    print(f"股票名称: {stock_info['name']}")
    print(f"波动类型: {volatility_type}")
    print(f"数据长度: {len(stock_data)} 天")
    
    # 创建策略
    strategy = EMAV2Strategy(volatility_type=volatility_type)
    print(f"策略参数: 快EMA={strategy.fast_ema}, 慢EMA={strategy.slow_ema}, ATR倍数={strategy.atr_multiplier}")
    
    # 执行回测
    result = strategy.run_backtest(stock_data, market_data, initial_capital)
    
    # 打印结果
    print(f"\n回测结果:")
    print(f"  总收益率: {result.total_return:+.2f}%")
    print(f"  胜率: {result.win_rate:.1f}%")
    print(f"  交易次数: {result.total_trades}")
    print(f"  最大回撤: {result.max_drawdown:.2f}%")
    print(f"  Sharpe比率: {result.sharpe_ratio:.2f}")
    
    if len(result.trades) > 0:
        stop_loss_count = sum(1 for t in result.trades if t['exit_reason'] == 'stop_loss')
        signal_count = sum(1 for t in result.trades if t['exit_reason'] == 'signal')
        print(f"  信号平仓: {signal_count}次, 止损平仓: {stop_loss_count}次")
    
    return {
        'symbol': symbol,
        'name': stock_info['name'],
        'type': volatility_type,
        'total_return': result.total_return,
        'win_rate': result.win_rate,
        'total_trades': result.total_trades,
        'max_drawdown': result.max_drawdown,
        'sharpe_ratio': result.sharpe_ratio,
        'trades': result.trades,
        'params': result.params
    }


def run_batch_backtest(symbols: list, output_dir: str = "../results", use_real_data: bool = True) -> Dict:
    """
    批量回测多只股票
    
    Args:
        symbols: 股票代码列表
        output_dir: 结果输出目录
        use_real_data: 是否使用akshare真实数据
        
    Returns:
        汇总结果
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # 选择数据源
    if use_real_data and AKSHARE_AVAILABLE:
        print("[INFO] 使用akshare真实数据源")
        data_source = AkshareDataSource()
    else:
        print("[INFO] 使用本地/模拟数据源")
        data_source = LocalDataSource()
    results = []
    
    print(f"\n{'#'*70}")
    print(f"# EMA V2.1 批量回测")
    print(f"# 股票数量: {len(symbols)}")
    print(f"# 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*70}")
    
    for i, symbol in enumerate(symbols, 1):
        print(f"\n[进度 {i}/{len(symbols)}]")
        result = run_single_stock_backtest(symbol, data_source)
        if result:
            results.append(result)
    
    # 汇总统计
    print(f"\n{'='*70}")
    print(f"汇总报告")
    print(f"{'='*70}")
    
    if len(results) == 0:
        print("无有效结果")
        return {}
    
    # 按收益率排序
    results_sorted = sorted(results, key=lambda x: x['total_return'], reverse=True)
    
    print(f"\n| 排名 | 股票 | 类型 | 总收益 | 胜率 | 交易次数 |")
    print(f"|-----|-----|-----|-------|-----|---------|")
    
    for i, r in enumerate(results_sorted, 1):
        print(f"| {i} | {r['symbol']}{r['name']} | {r['type'][:4]} | {r['total_return']:+.2f}% | {r['win_rate']:.1f}% | {r['total_trades']} |")
    
    # 统计
    avg_return = np.mean([r['total_return'] for r in results])
    avg_win_rate = np.mean([r['win_rate'] for r in results])
    total_trades = sum([r['total_trades'] for r in results])
    
    print(f"\n统计摘要:")
    print(f"  平均总收益: {avg_return:+.2f}%")
    print(f"  平均胜率: {avg_win_rate:.1f}%")
    print(f"  总交易次数: {total_trades}")
    
    # 按类型统计
    type_returns = {}
    for r in results:
        t = r['type']
        if t not in type_returns:
            type_returns[t] = []
        type_returns[t].append(r['total_return'])
    
    print(f"\n按波动率分类统计:")
    for t, returns in type_returns.items():
        print(f"  {t}: 平均收益 {np.mean(returns):+.2f}% (n={len(returns)})")
    
    # 保存结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    result_file = output_path / f"ema_v2_backtest_{timestamp}.json"
    
    # 转换trades中的Timestamp为字符串
    results_serializable = []
    for r in results:
        r_copy = r.copy()
        if 'trades' in r_copy:
            r_copy['trades'] = [
                {**t, 'entry_date': str(t['entry_date']), 'exit_date': str(t['exit_date'])}
                for t in r_copy['trades']
            ]
        results_serializable.append(r_copy)
    
    summary = {
        'timestamp': timestamp,
        'symbols': symbols,
        'avg_return': float(avg_return),
        'avg_win_rate': float(avg_win_rate),
        'total_trades': int(total_trades),
        'results': results_serializable
    }
    
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n结果已保存: {result_file}")
    
    return summary


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='EMA V2.1 回测')
    parser.add_argument('--symbol', '-s', type=str, help='单个股票代码')
    parser.add_argument('--batch', '-b', action='store_true', help='批量回测')
    parser.add_argument('--list', '-l', type=str, help='股票列表 (逗号分隔)')
    
    args = parser.parse_args()
    
    # 默认股票列表
    default_symbols = [
        '600519',  # 茅台
        '601888',  # 中国中免
        '000333',  # 美的
        '600276',  # 恒瑞
        '000858',  # 五粮液
        '000651',  # 格力
        '601318',  # 平安
    ]
    
    if args.symbol:
        # 单只股票回测
        data_source = LocalDataSource()
        result = run_single_stock_backtest(args.symbol, data_source)
    elif args.batch or args.list:
        # 批量回测
        if args.list:
            symbols = args.list.split(',')
        else:
            symbols = default_symbols
        run_batch_backtest(symbols)
    else:
        # 默认执行批量回测
        run_batch_backtest(default_symbols)


if __name__ == '__main__':
    main()
