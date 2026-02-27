#!/usr/bin/env python3
"""
EMA V2.1 - 使用本地CSV数据回测剩余股票
"""

import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

# 添加模块路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'strategies'))
from ema_v2 import EMAV2Strategy, BacktestResult

# 12只新增股票配置
EXTENDED_STOCKS = {
    '688981': {'name': '中芯国际', 'type': 'high_volatility', 'sector': '半导体'},
    '603501': {'name': '韦尔股份', 'type': 'high_volatility', 'sector': '半导体'},
    '300274': {'name': '阳光电源', 'type': 'high_volatility', 'sector': '新能源'},
    '600438': {'name': '通威股份', 'type': 'high_volatility', 'sector': '新能源'},
    '600893': {'name': '航发动力', 'type': 'high_volatility', 'sector': '军工'},
    '600760': {'name': '中航沈飞', 'type': 'high_volatility', 'sector': '军工'},
    '601899': {'name': '紫金矿业', 'type': 'high_volatility', 'sector': '有色'},
    '603993': {'name': '洛阳钼业', 'type': 'high_volatility', 'sector': '有色'},
    '300760': {'name': '迈瑞医疗', 'type': 'medium_volatility', 'sector': '医药'},
    '603259': {'name': '药明康德', 'type': 'medium_volatility', 'sector': '医药'},
    '603288': {'name': '海天味业', 'type': 'medium_volatility', 'sector': '消费'},
    '002475': {'name': '立讯精密', 'type': 'medium_volatility', 'sector': '电子'},
    # 还有一只000300是大盘指数
}

# 按波动率分类的优化参数
OPTIMIZED_PARAMS = {
    "high_volatility": {
        "fast_ema": 10, "slow_ema": 30, "atr_period": 14, "atr_multiplier": 3.0, "market_filter": True
    },
    "medium_volatility": {
        "fast_ema": 8, "slow_ema": 25, "atr_period": 14, "atr_multiplier": 2.0, "market_filter": True
    },
    "low_volatility": {
        "fast_ema": 5, "slow_ema": 20, "atr_period": 14, "atr_multiplier": 1.5, "market_filter": True
    }
}

def load_stock_data(symbol: str, data_dir: Path) -> Optional[pd.DataFrame]:
    """从本地CSV加载股票数据"""
    csv_path = data_dir / f"{symbol}.csv"
    if not csv_path.exists():
        return None
    
    df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
    df.columns = [c.lower() for c in df.columns]
    
    # 列名标准化
    col_map = {'收盘价': 'close', '开盘价': 'open', '最高价': 'high', '最低价': 'low', '成交量': 'volume'}
    df.rename(columns=col_map, inplace=True)
    
    df.attrs['symbol'] = symbol
    df.attrs['source'] = 'local_csv'
    return df

def run_single_backtest(symbol: str, info: Dict, data_dir: Path, 
                        market_data: pd.DataFrame) -> Optional[Dict]:
    """执行单只股票回测"""
    print(f"\n{'='*60}")
    print(f"回测: {symbol} {info['name']} ({info['type']}) - {info['sector']}")
    print(f"{'='*60}")
    
    stock_data = load_stock_data(symbol, data_dir)
    if stock_data is None:
        print(f"[ERROR] 找不到数据文件: {symbol}")
        return None
    
    if len(stock_data) < 100:
        print(f"[ERROR] 数据不足: {symbol}, 仅 {len(stock_data)} 行")
        return None
    
    print(f"  数据源: 本地CSV, 数据量: {len(stock_data)} 天")
    print(f"  时间范围: {stock_data.index[0].strftime('%Y-%m-%d')} ~ {stock_data.index[-1].strftime('%Y-%m-%d')}")
    
    # 对齐大盘数据
    aligned_market = market_data.reindex(stock_data.index, method='ffill') if market_data is not None else None
    
    # 获取参数
    volatility_type = info['type']
    params = OPTIMIZED_PARAMS.get(volatility_type, OPTIMIZED_PARAMS["medium_volatility"])
    
    strategy = EMAV2Strategy(params)
    print(f"  参数: fast_ema={strategy.fast_ema}, slow_ema={strategy.slow_ema}, atr_mult={strategy.atr_multiplier}")
    
    result = strategy.run_backtest(stock_data, aligned_market, initial_capital=100000.0)
    
    print(f"  总收益: {result.total_return:+.2f}%")
    print(f"  胜率: {result.win_rate:.1f}%  交易: {result.total_trades}次")
    print(f"  最大回撤: {result.max_drawdown:.2f}%  Sharpe: {result.sharpe_ratio:.2f}")
    
    return {
        'symbol': symbol,
        'name': info['name'],
        'type': info['type'],
        'sector': info['sector'],
        'data_source': 'local_csv',
        'data_rows': len(stock_data),
        'date_range': f"{stock_data.index[0].strftime('%Y-%m-%d')} ~ {stock_data.index[-1].strftime('%Y-%m-%d')}",
        'total_return': float(result.total_return),
        'win_rate': float(result.win_rate),
        'total_trades': int(result.total_trades),
        'max_drawdown': float(result.max_drawdown),
        'sharpe_ratio': float(result.sharpe_ratio),
        'params': params,
        'trades': [{**t, 'entry_date': str(t['entry_date']), 'exit_date': str(t['exit_date'])} for t in result.trades]
    }

def main():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / 'data'
    output_dir = base_dir / 'results' / 'individual_backtests'
    output_dir.mkdir(exist_ok=True, parents=True)
    
    print(f"{'#'*70}")
    print(f"# EMA V2.1 - 本地数据回测 (12只新增股票)")
    print(f"# 时间: {report_ts}")
    print(f"{'#'*70}")
    
    # 加载沪深300数据
    print("\n[STEP 1] 加载沪深300大盘数据...")
    market_data = load_stock_data('000300', data_dir)
    if market_data is not None:
        print(f"  沪深300: {len(market_data)} 天")
    
    # 执行回测
    print(f"\n[STEP 2] 开始回测 {len(EXTENDED_STOCKS)} 只股票...")
    results = []
    failed = []
    
    for i, (symbol, info) in enumerate(EXTENDED_STOCKS.items(), 1):
        print(f"\n--- 进度: [{i}/{len(EXTENDED_STOCKS)}] ---")
        try:
            result = run_single_backtest(symbol, info, data_dir, market_data)
            if result:
                results.append(result)
                # 保存单个结果
                trades_file = output_dir / f"{symbol}_trades.json"
                with open(trades_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2, default=str)
            else:
                failed.append(symbol)
        except Exception as e:
            print(f"[ERROR] {symbol} 回测失败: {e}")
            import traceback
            traceback.print_exc()
            failed.append(symbol)
    
    if not results:
        print("\n[FATAL] 无有效回测结果!")
        return
    
    # 保存汇总结果
    print(f"\n[STEP 3] 保存汇总结果...")
    
    summary = {
        'timestamp': timestamp,
        'report_time': report_ts,
        'total_stocks': len(EXTENDED_STOCKS),
        'successful': len(results),
        'failed': failed,
        'avg_return': float(np.mean([r['total_return'] for r in results])),
        'median_return': float(np.median([r['total_return'] for r in results])),
        'best_return': float(max([r['total_return'] for r in results])),
        'worst_return': float(min([r['total_return'] for r in results])),
        'positive_count': sum(1 for r in results if r['total_return'] > 0),
        'avg_win_rate': float(np.mean([r['win_rate'] for r in results])),
        'avg_sharpe': float(np.mean([r['sharpe_ratio'] for r in results])),
        'total_trades': int(sum(r['total_trades'] for r in results)),
        'results': results
    }
    
    json_file = output_dir / f"ema_v2_extended_real_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2, default=str)
    print(f"  JSON: {json_file}")
    
    # 生成汇总报告
    print(f"\n{'='*70}")
    print(f"✅ 本地数据回测完成!")
    print(f"  成功: {len(results)}/{len(EXTENDED_STOCKS)}")
    if failed:
        print(f"  失败: {failed}")
    print(f"  平均收益: {summary['avg_return']:+.2f}%")
    print(f"  正收益: {summary['positive_count']}/{len(results)}")
    print(f"  最佳: {summary['best_return']:+.2f}%")
    print(f"  最差: {summary['worst_return']:+.2f}%")
    print(f"  总交易: {summary['total_trades']}次")
    print(f"{'='*70}")
    
    return summary

if __name__ == '__main__':
    main()
