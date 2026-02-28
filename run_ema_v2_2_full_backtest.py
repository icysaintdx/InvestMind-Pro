#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EMA V2.2 策略全量回测脚本
对backtest_cache中所有未测股票执行回测
"""

import sys
import os
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# 设置项目路径
project_root = Path(__file__).parent
backend_root = project_root / "backend"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_root))
os.chdir(project_root)

import pandas as pd
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / 'backtest_results' / f'ema_v2_2_full_backtest_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

START_DATE = "20200101"
END_DATE = "20241231"
INITIAL_CAPITAL = 1_000_000.0
COMMISSION_RATE = 0.0003
SLIPPAGE_RATE = 0.0005

# 已测股票（跳过）
TESTED_STOCKS = ['600519', '601318', '000858', '601888']

# 股票名称映射
STOCK_NAMES = {
    '000333': '美的集团',
    '000651': '格力电器',
    '000858': '五粮液',
    '600276': '恒瑞医药',
    '600519': '贵州茅台',
    '601318': '中国平安',
    '601888': '中国中免'
}

CACHE_DIR = project_root / "backend" / "data" / "backtest_cache"
RESULTS_DIR = project_root / "backtest_results"
RESULTS_DIR.mkdir(exist_ok=True)


def get_all_stocks_from_cache() -> List[str]:
    """从缓存目录获取所有股票代码"""
    stocks = []
    if not CACHE_DIR.exists():
        return stocks
    
    for file in CACHE_DIR.glob('*_20200101_20241231.csv'):
        # 提取股票代码
        code = file.name.split('_')[0]
        if code not in ['sh000300']:  # 排除指数
            stocks.append(code)
    
    return sorted(stocks)


def load_ohlcv(symbol: str, start: str, end: str):
    """加载K线数据"""
    cache_file = CACHE_DIR / f"{symbol}_{start}_{end}.csv"

    if cache_file.exists():
        logger.info(f"[{symbol}] 从缓存加载K线数据")
        df = pd.read_csv(cache_file, index_col='date', parse_dates=True)
        return df
    return None


def load_market_data(start: str, end: str):
    """加载沪深300大盘数据用于趋势过滤"""
    cache_file = CACHE_DIR / f"sh000300_{start}_{end}.csv"
    
    if cache_file.exists():
        logger.info("[沪深300] 从缓存加载")
        return pd.read_csv(cache_file, index_col='date', parse_dates=True)
    return None


def run_backtest_v22(stock_code: str, stock_name: str) -> Dict[str, Any]:
    """使用EMA V2.2策略执行回测"""
    from strategies.ema_breakout_v2_2 import EMABreakoutV22Strategy
    from strategies.base import StrategyConfig
    
    logger.info(f"\n{'='*60}")
    logger.info(f"EMA V2.2 回测: {stock_code} {stock_name}")
    logger.info(f"{'='*60}")
    
    # 加载数据
    data = load_ohlcv(stock_code, START_DATE, END_DATE)
    if data is None or len(data) < 100:
        logger.error(f"[{stock_code}] 数据不足")
        return None
    
    market_data = load_market_data(START_DATE, END_DATE)
    
    # 初始化策略
    config = StrategyConfig(name="ema_breakout_v2_2", parameters={'symbol': stock_code})
    strategy = EMABreakoutV22Strategy(config)
    strategy.initialize(data, market_data)
    
    # 输出策略信息
    info = strategy.get_strategy_info()
    logger.info(f"策略配置: {info['volatility_description']}")
    logger.info(f"EMA周期: {info['ema_fast']}/{info['ema_slow']}")
    logger.info(f"ATR倍数: {info['atr_multiplier']}")
    logger.info(f"最大仓位: {info['max_position']:.0%}")
    logger.info(f"大盘过滤: {'启用' if info['market_filter_enabled'] else '禁用'} ({info['market_symbol']})")
    
    # 回测循环
    cash = INITIAL_CAPITAL
    position = 0
    avg_cost = 0.0
    trades = []
    equity_curve = [{'date': str(data.index[0]), 'value': INITIAL_CAPITAL}]
    stoploss_count = 0
    highest_value = INITIAL_CAPITAL
    max_drawdown = 0.0
    
    start_idx = 60
    if len(data) <= start_idx:
        return None
    
    for idx in range(start_idx, len(data)):
        current_data = data.iloc[:idx + 1]
        bar = data.iloc[idx]
        price = float(bar['close'])
        
        strategy.initialize(current_data, market_data)
        
        try:
            signal = strategy.generate_signal(current_data, position)
            if signal is None:
                signal_type = "hold"
                reason = "无信号"
            else:
                from strategies.base import SignalType
                signal_type = signal.signal_type.value if hasattr(signal.signal_type, 'value') else str(signal.signal_type)
                reason = getattr(signal, 'reason', '')
        except Exception as e:
            logger.warning(f"信号生成错误: {e}")
            signal_type = "hold"
            reason = "错误"
        
        # 买入逻辑
        if signal_type in ("buy", "strong_buy") and position == 0:
            max_value = cash * 0.95
            shares = int(max_value / price / 100) * 100
            if shares >= 100:
                cost = shares * price
                commission = max(cost * COMMISSION_RATE, 5)
                slippage = cost * SLIPPAGE_RATE
                total = cost + commission + slippage
                if total <= cash:
                    cash -= total
                    position = shares
                    avg_cost = price
                    trades.append({
                        'date': str(bar.name), 'action': 'BUY', 'price': price,
                        'shares': shares, 'commission': commission, 'slippage': slippage,
                        'reason': reason
                    })
                    logger.info(f"  [买入] {bar.name.date()}: {price:.2f}元 × {shares}股")
        
        # 卖出逻辑
        elif signal_type in ("sell", "strong_sell") and position > 0:
            revenue = position * price
            commission = max(revenue * COMMISSION_RATE, 5)
            slippage = revenue * SLIPPAGE_RATE
            stamp_tax = revenue * 0.001
            net = revenue - commission - slippage - stamp_tax
            profit = net - position * avg_cost
            profit_pct = profit / (position * avg_cost) if avg_cost > 0 else 0
            cash += net
            
            is_stoploss = '止损' in reason
            if is_stoploss:
                stoploss_count += 1
            
            trades.append({
                'date': str(bar.name), 'action': 'SELL', 'price': price,
                'shares': position, 'commission': commission, 'slippage': slippage,
                'stamp_tax': stamp_tax, 'profit': profit, 'profit_pct': profit_pct,
                'is_stoploss': is_stoploss, 'reason': reason
            })
            
            emoji = "📉" if profit < 0 else "📈"
            logger.info(f"  [{emoji}卖出] {bar.name.date()}: {price:.2f}元 | 盈亏: {profit:,.0f}元 ({profit_pct:+.2%})")
            logger.info(f"        原因: {reason[:80]}...")
            position = 0
            avg_cost = 0.0
        
        # 计算权益和回撤
        total_value = cash + position * price
        equity_curve.append({'date': str(bar.name), 'value': total_value})
        
        if total_value > highest_value:
            highest_value = total_value
        drawdown = (highest_value - total_value) / highest_value
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    
    # 计算最终统计
    final_value = cash + position * float(data['close'].iloc[-1])
    total_return = (final_value - INITIAL_CAPITAL) / INITIAL_CAPITAL
    
    # 计算年化收益
    days = (data.index[-1] - data.index[0]).days
    years = max(days / 365.25, 0.1)
    annual_return = (final_value / INITIAL_CAPITAL) ** (1/years) - 1
    
    # 计算夏普比率
    equity_df = pd.DataFrame(equity_curve)
    equity_df['returns'] = equity_df['value'].pct_change()
    volatility = equity_df['returns'].std() * np.sqrt(252)
    sharpe_ratio = (annual_return - 0.03) / volatility if volatility > 0 else 0
    
    # 计算胜率
    if trades:
        sell_trades = [t for t in trades if t['action'] == 'SELL']
        win_trades = [t for t in sell_trades if t.get('profit', 0) > 0]
        win_rate = len(win_trades) / len(sell_trades) if sell_trades else 0
    else:
        win_rate = 0
        sell_trades = []
    
    result = {
        'stock_code': stock_code,
        'stock_name': stock_name,
        'strategy_version': '2.2',
        'volatility_class': info['volatility_class'],
        'volatility_description': info['volatility_description'],
        'ema_fast': info['ema_fast'],
        'ema_slow': info['ema_slow'],
        'atr_multiplier': info['atr_multiplier'],
        'total_return': round(total_return, 4),
        'annual_return': round(annual_return, 4),
        'max_drawdown': round(max_drawdown, 4),
        'sharpe_ratio': round(sharpe_ratio, 4),
        'volatility': round(volatility, 4),
        'win_rate': round(win_rate, 4),
        'total_trades': len(sell_trades),
        'stoploss_count': stoploss_count,
        'final_value': round(final_value, 2),
        'initial_capital': INITIAL_CAPITAL,
        'trades': trades,
        'equity_curve': equity_curve,
        'strategy_info': info
    }
    
    logger.info(f"\n{'='*60}")
    logger.info(f"回测结果: {stock_code} {stock_name}")
    logger.info(f"{'='*60}")
    logger.info(f"总收益率: {total_return:.2%}")
    logger.info(f"年化收益: {annual_return:.2%}")
    logger.info(f"最大回撤: {max_drawdown:.2%}")
    logger.info(f"夏普比率: {sharpe_ratio:.3f}")
    logger.info(f"胜率: {win_rate:.2%}")
    logger.info(f"交易次数: {len(sell_trades)}")
    logger.info(f"止损次数: {stoploss_count}")
    logger.info(f"期末资金: {final_value:,.2f}")
    
    return result


def load_v21_result(stock_code: str) -> Dict[str, Any]:
    """加载V2.1回测结果"""
    # 查找V2.1优化结果文件
    v21_files = list(RESULTS_DIR.glob(f'ema_v2_{stock_code}_optimized_results_*.json'))
    if v21_files:
        # 使用最新的文件
        latest_file = max(v21_files, key=lambda p: p.stat().st_mtime)
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"加载V2.1结果失败 {stock_code}: {e}")
    return None


def compare_v21_v22(stock_code: str, v22_result: Dict[str, Any]) -> Dict[str, Any]:
    """对比V2.1和V2.2的结果"""
    v21_data = load_v21_result(stock_code)
    
    comparison = {
        'stock_code': stock_code,
        'stock_name': v22_result['stock_name'],
        'v2_1': {},
        'v2_2': {
            'total_return': v22_result['total_return'],
            'annual_return': v22_result['annual_return'],
            'max_drawdown': v22_result['max_drawdown'],
            'sharpe_ratio': v22_result['sharpe_ratio'],
            'win_rate': v22_result['win_rate'],
            'total_trades': v22_result['total_trades'],
            'atr_multiplier': v22_result['atr_multiplier'],
            'volatility_class': v22_result['volatility_class']
        },
        'improvement': {}
    }
    
    if v21_data:
        comparison['v2_1'] = {
            'total_return': v21_data.get('total_return', 0),
            'annual_return': v21_data.get('annual_return', 0),
            'max_drawdown': v21_data.get('max_drawdown', 0),
            'sharpe_ratio': v21_data.get('sharpe_ratio', 0),
            'win_rate': v21_data.get('win_rate', 0),
            'total_trades': v21_data.get('total_trades', 0)
        }
        
        # 计算改进幅度
        comparison['improvement'] = {
            'return_diff': round(v22_result['total_return'] - comparison['v2_1']['total_return'], 4),
            'sharpe_diff': round(v22_result['sharpe_ratio'] - comparison['v2_1']['sharpe_ratio'], 4),
            'drawdown_diff': round(v22_result['max_drawdown'] - comparison['v2_1']['max_drawdown'], 4),
            'winrate_diff': round(v22_result['win_rate'] - comparison['v2_1']['win_rate'], 4),
            'trades_diff': v22_result['total_trades'] - comparison['v2_1']['total_trades']
        }
    else:
        comparison['v2_1'] = {'error': 'V2.1结果文件不存在'}
    
    return comparison


def save_progress(progress: Dict[str, Any]):
    """保存进度文件"""
    progress_file = project_root / 'ema_v2_verify_progress.json'
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def load_progress() -> Dict[str, Any]:
    """加载进度文件"""
    progress_file = project_root / 'ema_v2_verify_progress.json'
    if progress_file.exists():
        with open(progress_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def generate_summary_report(all_results: Dict[str, Any], all_comparisons: Dict[str, Any], timestamp: str):
    """生成汇总报告"""
    report_lines = []
    report_lines.append("# EMA V2.2 策略全量回测报告")
    report_lines.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"回测区间: {START_DATE} - {END_DATE}")
    report_lines.append(f"初始资金: {INITIAL_CAPITAL:,.0f}元")
    report_lines.append("")
    report_lines.append("## 一、回测股票列表")
    report_lines.append("")
    
    # 股票列表
    for code, result in sorted(all_results.items()):
        report_lines.append(f"- **{code}** - {result['stock_name']} ({result['volatility_description']})")
    
    report_lines.append("")
    report_lines.append("## 二、V2.2 回测结果汇总")
    report_lines.append("")
    report_lines.append("| 股票代码 | 股票名称 | 总收益率 | 年化收益 | 最大回撤 | 夏普比率 | 胜率 | 交易次数 | 止损次数 |")
    report_lines.append("|----------|----------|----------|----------|----------|----------|------|----------|----------|")
    
    for code, result in sorted(all_results.items()):
        report_lines.append(
            f"| {code} | {result['stock_name']} | "
            f"{result['total_return']:+.2%} | {result['annual_return']:+.2%} | "
            f"{result['max_drawdown']:.2%} | {result['sharpe_ratio']:.3f} | "
            f"{result['win_rate']:.1%} | {result['total_trades']} | {result['stoploss_count']} |"
        )
    
    # 计算平均值
    if all_results:
        avg_return = sum(r['total_return'] for r in all_results.values()) / len(all_results)
        avg_annual = sum(r['annual_return'] for r in all_results.values()) / len(all_results)
        avg_drawdown = sum(r['max_drawdown'] for r in all_results.values()) / len(all_results)
        avg_sharpe = sum(r['sharpe_ratio'] for r in all_results.values()) / len(all_results)
        avg_winrate = sum(r['win_rate'] for r in all_results.values()) / len(all_results)
        total_trades = sum(r['total_trades'] for r in all_results.values())
        total_stoploss = sum(r['stoploss_count'] for r in all_results.values())
        
        report_lines.append(f"| **平均值** | - | {avg_return:+.2%} | {avg_annual:+.2%} | "
                          f"{avg_drawdown:.2%} | {avg_sharpe:.3f} | {avg_winrate:.1%} | {total_trades} | {total_stoploss} |")
    
    report_lines.append("")
    report_lines.append("## 三、V2.1 vs V2.2 对比分析")
    report_lines.append("")
    report_lines.append("| 股票代码 | 股票名称 | V2.1收益 | V2.2收益 | 收益差 | V2.1夏普 | V2.2夏普 | 夏普差 | V2.1回撤 | V2.2回撤 | 回撤差 |")
    report_lines.append("|----------|----------|----------|----------|--------|----------|----------|--------|----------|----------|--------|")
    
    improvements = []
    for code, comp in sorted(all_comparisons.items()):
        if 'error' not in comp['v2_1']:
            imp = comp['improvement']
            improvements.append(imp)
            report_lines.append(
                f"| {code} | {comp['stock_name']} | "
                f"{comp['v2_1']['total_return']:+.2%} | {comp['v2_2']['total_return']:+.2%} | {imp['return_diff']:+.2%} | "
                f"{comp['v2_1']['sharpe_ratio']:.3f} | {comp['v2_2']['sharpe_ratio']:.3f} | {imp['sharpe_diff']:+.3f} | "
                f"{comp['v2_1']['max_drawdown']:.2%} | {comp['v2_2']['max_drawdown']:.2%} | {imp['drawdown_diff']:+.2%} |"
            )
        else:
            report_lines.append(f"| {code} | {comp['stock_name']} | - | {comp['v2_2']['total_return']:+.2%} | - | - | "
                              f"{comp['v2_2']['sharpe_ratio']:.3f} | - | - | {comp['v2_2']['max_drawdown']:.2%} | - |")
    
    # 平均改进
    if improvements:
        avg_return_diff = sum(i['return_diff'] for i in improvements) / len(improvements)
        avg_sharpe_diff = sum(i['sharpe_diff'] for i in improvements) / len(improvements)
        avg_drawdown_diff = sum(i['drawdown_diff'] for i in improvements) / len(improvements)
        
        report_lines.append("")
        report_lines.append(f"**平均改进：**")
        report_lines.append(f"- 收益率提升: {avg_return_diff:+.2%}")
        report_lines.append(f"- 夏普比率提升: {avg_sharpe_diff:+.3f}")
        report_lines.append(f"- 最大回撤变化: {avg_drawdown_diff:+.2%} (负值表示改善)")
    
    report_lines.append("")
    report_lines.append("## 四、策略配置详情")
    report_lines.append("")
    
    for code, result in sorted(all_results.items()):
        info = result['strategy_info']
        report_lines.append(f"### {code} {result['stock_name']}")
        report_lines.append(f"- 波动率分类: {info['volatility_description']}")
        report_lines.append(f"- EMA周期: {info['ema_fast']}/{info['ema_slow']}")
        report_lines.append(f"- ATR止损倍数: {info['atr_multiplier']}")
        report_lines.append(f"- 最大仓位: {info['max_position']:.0%}")
        report_lines.append(f"- 大盘过滤: {'启用' if info['market_filter_enabled'] else '禁用'} ({info['market_symbol']})")
        report_lines.append(f"- 追踪止损: {'启用' if info['trailing_stop_enabled'] else '禁用'}")
        report_lines.append("")
    
    report_lines.append("## 五、结论与建议")
    report_lines.append("")
    if improvements:
        if avg_return_diff > 0:
            report_lines.append(f"1. **V2.2策略整体表现优于V2.1**，平均收益率提升 {avg_return_diff:+.2%}")
        else:
            report_lines.append(f"1. **V2.2策略整体收益率略低于V2.1**，平均差异 {avg_return_diff:+.2%}")
        
        if avg_sharpe_diff > 0:
            report_lines.append(f"2. **风险调整后收益改善**，夏普比率平均提升 {avg_sharpe_diff:+.3f}")
        else:
            report_lines.append(f"2. 夏普比率平均变化 {avg_sharpe_diff:+.3f}")
        
        if avg_drawdown_diff < 0:
            report_lines.append(f"3. **风险控制改善**，最大回撤平均降低 {abs(avg_drawdown_diff):.2%}")
        else:
            report_lines.append(f"3. 最大回撤平均变化 {avg_drawdown_diff:+.2%}")
    
    report_lines.append("")
    report_lines.append("---")
    report_lines.append(f"*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    
    report_content = '\n'.join(report_lines)
    
    # 保存报告
    report_file = RESULTS_DIR / f'ema_v2_2_full_backtest_report.md'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    logger.info(f"\n汇总报告已保存: {report_file}")
    return report_content


def main():
    """主函数"""
    logger.info("="*70)
    logger.info("EMA V2.2 策略全量回测开始")
    logger.info("="*70)
    
    # 加载进度
    progress = load_progress()
    
    # 获取所有待测股票
    all_stocks = get_all_stocks_from_cache()
    logger.info(f"缓存目录中发现 {len(all_stocks)} 只股票")
    
    # 排除已测股票
    stocks_to_test = [s for s in all_stocks if s not in TESTED_STOCKS]
    logger.info(f"已测股票（跳过）: {', '.join(TESTED_STOCKS)}")
    logger.info(f"待测股票: {', '.join(stocks_to_test)}")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    all_results = {}
    all_comparisons = {}
    errors = []
    
    # 逐个执行回测
    for stock_code in stocks_to_test:
        stock_name = STOCK_NAMES.get(stock_code, '未知')
        
        try:
            # 运行V2.2回测
            result = run_backtest_v22(stock_code, stock_name)
            if result:
                all_results[stock_code] = result
                
                # 对比V2.1
                comparison = compare_v21_v22(stock_code, result)
                all_comparisons[stock_code] = comparison
                
                # 保存单个结果
                result_file = RESULTS_DIR / f"ema_v2_2_{stock_code}_results.json"
                with open(result_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                logger.info(f"结果已保存: {result_file}")
            else:
                errors.append(f"{stock_code}: 回测返回空结果")
                
        except Exception as e:
            error_msg = f"{stock_code}: {str(e)}"
            logger.error(f"回测失败 {stock_code}: {e}")
            errors.append(error_msg)
            import traceback
            logger.error(traceback.format_exc())
        
        time.sleep(0.5)  # 避免请求过快
    
    # 保存批量结果
    batch_results = {
        'timestamp': timestamp,
        'strategy_version': '2.2',
        'stocks': all_results,
        'comparisons': all_comparisons,
        'errors': errors
    }
    
    batch_file = RESULTS_DIR / f"ema_v2_2_full_results_{timestamp}.json"
    with open(batch_file, 'w', encoding='utf-8') as f:
        json.dump(batch_results, f, ensure_ascii=False, indent=2)
    
    # 生成汇总报告
    report = generate_summary_report(all_results, all_comparisons, timestamp)
    
    # 更新进度文件
    progress['v2_2_full_backtest'] = {
        'status': 'completed' if not errors else 'completed_with_errors',
        'timestamp': timestamp,
        'stocks_tested': list(all_results.keys()),
        'errors': errors,
        'summary': {
            'total_stocks': len(stocks_to_test),
            'successful': len(all_results),
            'failed': len(errors)
        }
    }
    save_progress(progress)
    
    logger.info(f"\n{'='*70}")
    logger.info("EMA V2.2 全量回测完成")
    logger.info(f"汇总结果: {batch_file}")
    logger.info(f"测试股票数: {len(all_results)}/{len(stocks_to_test)}")
    if errors:
        logger.info(f"错误数: {len(errors)}")
        for e in errors:
            logger.info(f"  - {e}")
    logger.info("="*70)
    
    return batch_results


if __name__ == "__main__":
    results = main()
