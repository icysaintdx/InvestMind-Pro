#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EMA V2策略专用回测脚本
"""

import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime

# 设置项目路径 - InvestMindPro目录
project_root = Path(__file__).parent
backend_root = project_root / "backend"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_root))
os.chdir(project_root)

print(f"Project root: {project_root}")
print(f"Backend root: {backend_root}")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

START_DATE = "20200101"
END_DATE = "20241231"
INITIAL_CAPITAL = 1_000_000.0

STOCKS = [
    ("600519", "贵州茅台"),
    ("601318", "中国平安"),
    ("000858", "五粮液"),
    ("000333", "美的集团"),
    ("000651", "格力电器"),
    ("600276", "恒瑞医药"),
    ("601888", "中国中免")
]

def run_ema_v2_backtest():
    from backtest.backtest_engine import BacktestEngine
    
    results = {}
    logger.info("="*60)
    logger.info("EMA V2 策略回测开始")
    logger.info("="*60)
    
    for stock_code, stock_name in STOCKS:
        logger.info(f"\n[{stock_code} {stock_name}] 开始回测...")
        try:
            engine = BacktestEngine(
                start_date=START_DATE,
                end_date=END_DATE,
                initial_capital=INITIAL_CAPITAL,
                strategy_name='ema_breakout_v2',
                stock_code=stock_code
            )
            result = engine.run()
            results[stock_code] = {
                'total_return': float(result.get('total_return', 0)),
                'annual_return': float(result.get('annual_return', 0)),
                'max_drawdown': float(result.get('max_drawdown', 0)),
                'sharpe_ratio': float(result.get('sharpe_ratio', 0)),
                'sortino_ratio': float(result.get('sortino_ratio', 0)),
                'calmar_ratio': float(result.get('calmar_ratio', 0)),
                'volatility': float(result.get('volatility', 0)),
                'win_rate': float(result.get('win_rate', 0)),
                'total_trades': int(result.get('total_trades', 0)),
                'buy_trades': int(result.get('buy_trades', 0)),
                'sell_trades': int(result.get('sell_trades', 0))
            }
            logger.info(f"  总收益率: {results[stock_code]['total_return']:.2%}")
            logger.info(f"  年化收益: {results[stock_code]['annual_return']:.2%}")
            logger.info(f"  最大回撤: {results[stock_code]['max_drawdown']:.2%}")
            logger.info(f"  夏普比率: {results[stock_code]['sharpe_ratio']:.2f}")
            logger.info(f"  交易次数: {results[stock_code]['total_trades']}")
        except Exception as e:
            logger.error(f"  错误: {e}")
            import traceback
            traceback.print_exc()
            results[stock_code] = {'error': str(e)}
    
    # 保存结果
    output_file = 'ema_v2_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    logger.info(f"\n结果已保存到: {output_file}")
    
    # 打印汇总
    logger.info("\n" + "="*60)
    logger.info("EMA V2 回测汇总")
    logger.info("="*60)
    for code, name in STOCKS:
        r = results.get(code, {})
        if 'error' not in r:
            logger.info(f"{code} {name}: 收益{r['total_return']:.2%} 夏普{r['sharpe_ratio']:.2f} 回撤{r['max_drawdown']:.2%}")
        else:
            logger.info(f"{code} {name}: 失败 - {r.get('error', 'Unknown')}")
    
    return results

if __name__ == '__main__':
    run_ema_v2_backtest()
