# -*- coding: utf-8 -*-
"""
AI情绪驱动策略回测脚本
对比纯技术策略 vs 情绪+技术混合策略在2020-2024年的表现

运行方式: python backend/scripts/backtest_sentiment_strategy.py
"""

import sys
import os
import json
import time
import logging
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent.parent
backend_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_root))
os.chdir(project_root)

import pandas as pd
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

START_DATE = "20200101"
END_DATE = "20241231"
INITIAL_CAPITAL = 1_000_000.0

TEST_STOCKS = {
    "600519": "贵州茅台",
    "601318": "中国平安",
    "000858": "五粮液",
    "000333": "美的集团",
    "000651": "格力电器",
    "600276": "恒瑞医药",
    "601888": "中国中免",
}

DB_PATH = str(project_root / "InvestMindPro.db")
REPORT_PATH = str(project_root / "BACKTEST_REPORT.md")
CACHE_DIR = project_root / "backend" / "data" / "backtest_cache"


def load_ohlcv(symbol: str, start: str, end: str) -> pd.DataFrame | None:
    """通过 AKShare 加载前复权日K数据，带本地缓存。"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{symbol}_{start}_{end}.csv"

    if cache_file.exists():
        logger.info(f"[缓存] 加载 {symbol} K线")
        df = pd.read_csv(cache_file, index_col='date', parse_dates=True)
        return df

    try:
        import akshare as ak
        logger.info(f"[AKShare] 下载 {symbol} K线 {start}-{end}")
        df = ak.stock_zh_a_hist(
            symbol=symbol, period="daily",
            start_date=start, end_date=end, adjust="qfq"
        )
    except Exception as e:
        logger.error(f"下载 {symbol} 失败: {e}")
        return None

    if df is None or df.empty:
        return None

    df = df.rename(columns={
        '日期': 'date', '开盘': 'open', '收盘': 'close',
        '最高': 'high', '最低': 'low', '成交量': 'volume', '成交额': 'amount',
    })
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    for c in ['open', 'high', 'low', 'close', 'volume']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df.sort_index(inplace=True)

    df.to_csv(cache_file)
    logger.info(f"[AKShare] {symbol} 加载 {len(df)} 条, 已缓存")
    time.sleep(1)
    return df


def load_sentiment(stock_code: str, start: str, end: str) -> pd.DataFrame | None:
    """从 SQLite 加载情绪数据。"""
    if not os.path.exists(DB_PATH):
        logger.warning(f"数据库不存在: {DB_PATH}")
        return None

    import sqlite3
    start_fmt = f"{start[:4]}-{start[4:6]}-{start[6:]}"
    end_fmt = f"{end[:4]}-{end[4:6]}-{end[6:]}"

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT date, positive_all AS positive, neutral_all AS neutral, negative_all AS negative "
        "FROM news_daily_sentiment WHERE stock_code=? AND date>=? AND date<=? ORDER BY date",
        conn, params=(stock_code, start_fmt, end_fmt)
    )
    conn.close()

    if df.empty:
        return None

    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    total = df['positive'] + df['neutral'] + df['negative']
    df['sent_raw'] = (df['positive'] - df['negative']) / (total + 1)
    df['sent_smooth'] = df['sent_raw'].ewm(span=5, min_periods=1).mean()
    logger.info(f"[DB] {stock_code} 情绪数据 {len(df)} 条")
    return df


def merge_sentiment(ohlcv: pd.DataFrame, sent: pd.DataFrame | None) -> pd.DataFrame:
    """合并情绪到K线。"""
    df = ohlcv.copy()
    if sent is None or sent.empty:
        df['sent_raw'] = 0.0
        df['sent_smooth'] = 0.0
        df['sent_momentum'] = 0.0
        df['sent_volume'] = 0.0
        df['has_sentiment'] = False
        return df

    df = df.join(sent[['sent_raw', 'sent_smooth']], how='left')
    df['sent_raw'] = df['sent_raw'].fillna(0.0)
    df['sent_smooth'] = df['sent_smooth'].ffill().fillna(0.0)
    df['sent_momentum'] = df['sent_smooth'] - df['sent_smooth'].shift(3)
    df['sent_momentum'] = df['sent_momentum'].fillna(0.0)

    if 'positive' in sent.columns:
        vol = sent['positive'] + sent['neutral'] + sent['negative']
        df = df.join(vol.rename('sent_volume'), how='left')
        df['sent_volume'] = df['sent_volume'].fillna(0.0)
    else:
        df['sent_volume'] = 0.0
    df['has_sentiment'] = df['sent_volume'] > 0
    return df


class SimpleBacktester:
    """
    轻量回测器，直接调用策略的 generate_signal 逐bar回测。
    模拟A股T+1、手续费万三、印花税千一（卖出）。
    """

    def __init__(self, initial_capital: float = 1_000_000.0):
        self.initial_capital = initial_capital

    def run(self, strategy, data: pd.DataFrame, stock_code: str) -> dict:
        cash = self.initial_capital
        position = 0
        avg_cost = 0.0
        trades = []
        equity_curve = []

        strategy.initialize(data)
        start_idx = 65

        for idx in range(start_idx, len(data)):
            current_data = data.iloc[:idx + 1]
            bar = data.iloc[idx]
            price = bar['close']

            signal = strategy.generate_signal(current_data, position)
            if signal is None:
                signal_type = "hold"
            else:
                signal_type = signal.signal_type.value

            if signal_type in ("buy", "strong_buy") and position == 0:
                max_value = cash * 0.95
                shares = int(max_value / price / 100) * 100
                if shares >= 100:
                    cost = shares * price
                    commission = max(cost * 0.0003, 5)
                    total = cost + commission
                    if total <= cash:
                        cash -= total
                        position = shares
                        avg_cost = price
                        trades.append({
                            'date': bar.name, 'action': 'BUY',
                            'price': price, 'shares': shares,
                            'commission': commission,
                        })

            elif signal_type in ("sell", "strong_sell") and position > 0:
                revenue = position * price
                commission = max(revenue * 0.0003, 5)
                stamp_tax = revenue * 0.001
                net = revenue - commission - stamp_tax
                profit = net - position * avg_cost
                cash += net
                trades.append({
                    'date': bar.name, 'action': 'SELL',
                    'price': price, 'shares': position,
                    'commission': commission, 'stamp_tax': stamp_tax,
                    'profit': profit, 'profit_pct': profit / (position * avg_cost) if avg_cost > 0 else 0,
                })
                position = 0
                avg_cost = 0.0

            portfolio_value = cash + position * price
            equity_curve.append({'date': bar.name, 'value': portfolio_value})

        final_value = cash + position * data.iloc[-1]['close']
        metrics = self._calc_metrics(equity_curve, trades, final_value)
        metrics['stock_code'] = stock_code
        metrics['final_value'] = final_value
        return metrics

    def _calc_metrics(self, equity_curve: list, trades: list, final_value: float) -> dict:
        if not equity_curve:
            return self._empty_metrics()

        values = pd.Series([e['value'] for e in equity_curve])
        dates = pd.Series([e['date'] for e in equity_curve])

        total_return = (final_value / self.initial_capital) - 1
        days = (dates.iloc[-1] - dates.iloc[0]).days
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

        downside = daily_returns[daily_returns < 0]
        downside_std = downside.std() * np.sqrt(252) if len(downside) > 1 else 0
        sortino = (annual_return - 0.03) / downside_std if downside_std > 0 else 0
        calmar = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0

        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'calmar_ratio': calmar,
            'volatility': volatility,
            'win_rate': win_rate,
            'total_trades': len(trades),
            'sell_trades': len(sell_trades),
            'win_trades': len(win_trades),
        }

    def _empty_metrics(self):
        return {k: 0 for k in [
            'total_return', 'annual_return', 'max_drawdown', 'sharpe_ratio',
            'sortino_ratio', 'calmar_ratio', 'volatility', 'win_rate',
            'total_trades', 'sell_trades', 'win_trades',
        ]}


def run_all_backtests():
    from backend.strategies.macd_crossover import MACDCrossoverStrategy
    from backend.strategies.ai_sentiment_strategy import AISentimentStrategy
    from backend.strategies.base import StrategyConfig, StrategyCategory

    backtester = SimpleBacktester(INITIAL_CAPITAL)
    results_tech = {}
    results_hybrid = {}
    sentiment_stats = {}

    for code, name in TEST_STOCKS.items():
        logger.info(f"\n{'='*60}")
        logger.info(f"回测 {code} {name}")
        logger.info(f"{'='*60}")

        ohlcv = load_ohlcv(code, START_DATE, END_DATE)
        if ohlcv is None or len(ohlcv) < 100:
            logger.warning(f"跳过 {code}: 数据不足")
            continue

        sent_df = load_sentiment(code, START_DATE, END_DATE)
        sent_days = len(sent_df) if sent_df is not None else 0
        trading_days = len(ohlcv)
        sentiment_stats[code] = {
            'name': name,
            'trading_days': trading_days,
            'sentiment_days': sent_days,
            'coverage': sent_days / trading_days if trading_days > 0 else 0,
        }

        tech_config = StrategyConfig(name="MACD纯技术策略")
        tech_strategy = MACDCrossoverStrategy(tech_config)
        tech_result = backtester.run(tech_strategy, ohlcv.copy(), code)
        results_tech[code] = tech_result
        logger.info(f"[MACD] 收益={tech_result['total_return']:.2%} 夏普={tech_result['sharpe_ratio']:.2f} 回撤={tech_result['max_drawdown']:.2%}")

        hybrid_data = merge_sentiment(ohlcv, sent_df)
        hybrid_config = StrategyConfig(name="AI情绪混合策略", category=StrategyCategory.AI)
        hybrid_strategy = AISentimentStrategy(hybrid_config)
        hybrid_result = backtester.run(hybrid_strategy, hybrid_data, code)
        results_hybrid[code] = hybrid_result
        logger.info(f"[混合] 收益={hybrid_result['total_return']:.2%} 夏普={hybrid_result['sharpe_ratio']:.2f} 回撤={hybrid_result['max_drawdown']:.2%}")

    return results_tech, results_hybrid, sentiment_stats


def generate_report(results_tech: dict, results_hybrid: dict, sentiment_stats: dict):
    """生成 Markdown 回测报告。"""

    def avg_metric(results: dict, key: str) -> float:
        vals = [r[key] for r in results.values() if key in r]
        return np.mean(vals) if vals else 0

    def fmt_pct(v): return f"{v:.2%}"
    def fmt_f2(v): return f"{v:.2f}"

    lines = []
    lines.append("# AI情绪驱动策略回测报告")
    lines.append("")
    lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    lines.append("## 1. 回测配置")
    lines.append("")
    lines.append(f"- 回测区间: {START_DATE[:4]}-{START_DATE[4:6]}-{START_DATE[6:]} ~ {END_DATE[:4]}-{END_DATE[4:6]}-{END_DATE[6:]}")
    lines.append(f"- 初始资金: ¥{INITIAL_CAPITAL:,.0f}")
    lines.append(f"- 测试标的: {len(TEST_STOCKS)}只沪深300成分股")
    lines.append(f"- 对比策略: MACD纯技术策略 vs AI情绪+技术混合策略")
    lines.append(f"- 交易成本: 佣金万三(最低5元) + 印花税千一(卖出)")
    lines.append(f"- 情绪数据: InvestMindPro.db news_daily_sentiment表 (2001-2024)")
    lines.append("")

    lines.append("### 测试标的")
    lines.append("")
    lines.append("| 代码 | 名称 | 交易日 | 情绪数据天数 | 覆盖率 |")
    lines.append("|------|------|--------|------------|--------|")
    for code, stat in sentiment_stats.items():
        lines.append(f"| {code} | {stat['name']} | {stat['trading_days']} | {stat['sentiment_days']} | {fmt_pct(stat['coverage'])} |")
    lines.append("")

    lines.append("## 2. 单股回测结果")
    lines.append("")
    lines.append("### MACD纯技术策略")
    lines.append("")
    lines.append("| 代码 | 名称 | 总收益 | 年化收益 | 最大回撤 | 夏普比率 | 索提诺 | 胜率 | 交易次数 |")
    lines.append("|------|------|--------|---------|---------|---------|--------|------|---------|")
    for code in results_tech:
        r = results_tech[code]
        n = TEST_STOCKS.get(code, code)
        lines.append(f"| {code} | {n} | {fmt_pct(r['total_return'])} | {fmt_pct(r['annual_return'])} | {fmt_pct(r['max_drawdown'])} | {fmt_f2(r['sharpe_ratio'])} | {fmt_f2(r['sortino_ratio'])} | {fmt_pct(r['win_rate'])} | {r['total_trades']} |")
    lines.append("")

    lines.append("### AI情绪+技术混合策略")
    lines.append("")
    lines.append("| 代码 | 名称 | 总收益 | 年化收益 | 最大回撤 | 夏普比率 | 索提诺 | 胜率 | 交易次数 |")
    lines.append("|------|------|--------|---------|---------|---------|--------|------|---------|")
    for code in results_hybrid:
        r = results_hybrid[code]
        n = TEST_STOCKS.get(code, code)
        lines.append(f"| {code} | {n} | {fmt_pct(r['total_return'])} | {fmt_pct(r['annual_return'])} | {fmt_pct(r['max_drawdown'])} | {fmt_f2(r['sharpe_ratio'])} | {fmt_f2(r['sortino_ratio'])} | {fmt_pct(r['win_rate'])} | {r['total_trades']} |")
    lines.append("")

    lines.append("## 3. 策略对比汇总")
    lines.append("")
    lines.append("| 指标 | MACD纯技术 | AI情绪混合 | 差异 |")
    lines.append("|------|-----------|-----------|------|")

    for label, key, fmt in [
        ("平均总收益", "total_return", fmt_pct),
        ("平均年化收益", "annual_return", fmt_pct),
        ("平均最大回撤", "max_drawdown", fmt_pct),
        ("平均夏普比率", "sharpe_ratio", fmt_f2),
        ("平均索提诺比率", "sortino_ratio", fmt_f2),
        ("平均卡尔玛比率", "calmar_ratio", fmt_f2),
        ("平均胜率", "win_rate", fmt_pct),
    ]:
        t = avg_metric(results_tech, key)
        h = avg_metric(results_hybrid, key)
        diff = h - t
        diff_str = f"{diff:+.4f}" if 'ratio' in key.lower() else f"{diff:+.2%}"
        lines.append(f"| {label} | {fmt(t)} | {fmt(h)} | {diff_str} |")
    lines.append("")

    lines.append("## 4. 情绪因子贡献度分析")
    lines.append("")

    better_count = 0
    worse_count = 0
    sentiment_alpha = []
    for code in results_tech:
        if code in results_hybrid:
            t_ret = results_tech[code]['total_return']
            h_ret = results_hybrid[code]['total_return']
            alpha = h_ret - t_ret
            sentiment_alpha.append(alpha)
            if h_ret > t_ret:
                better_count += 1
            else:
                worse_count += 1

    avg_alpha = np.mean(sentiment_alpha) if sentiment_alpha else 0
    lines.append(f"- 情绪因子平均超额收益(Alpha): {avg_alpha:+.2%}")
    lines.append(f"- 混合策略优于纯技术: {better_count}/{better_count + worse_count} 只股票")
    lines.append(f"- 混合策略劣于纯技术: {worse_count}/{better_count + worse_count} 只股票")
    lines.append("")

    lines.append("### 逐股情绪贡献")
    lines.append("")
    lines.append("| 代码 | 名称 | 纯技术收益 | 混合收益 | 情绪Alpha | 情绪覆盖率 |")
    lines.append("|------|------|-----------|---------|----------|-----------|")
    for code in results_tech:
        if code in results_hybrid:
            t = results_tech[code]['total_return']
            h = results_hybrid[code]['total_return']
            alpha = h - t
            cov = sentiment_stats.get(code, {}).get('coverage', 0)
            n = TEST_STOCKS.get(code, code)
            lines.append(f"| {code} | {n} | {fmt_pct(t)} | {fmt_pct(h)} | {alpha:+.2%} | {fmt_pct(cov)} |")
    lines.append("")

    lines.append("### 情绪覆盖率与Alpha相关性")
    lines.append("")
    coverages = []
    alphas = []
    for code in results_tech:
        if code in results_hybrid and code in sentiment_stats:
            coverages.append(sentiment_stats[code]['coverage'])
            alphas.append(results_hybrid[code]['total_return'] - results_tech[code]['total_return'])
    if len(coverages) > 2:
        corr = np.corrcoef(coverages, alphas)[0, 1]
        lines.append(f"情绪数据覆盖率与超额收益的相关系数: {corr:.3f}")
        if corr > 0.3:
            lines.append("- 正相关: 情绪数据越充足，混合策略表现越好，说明情绪因子有正向贡献")
        elif corr < -0.3:
            lines.append("- 负相关: 情绪数据可能引入噪声，需要优化情绪信号的过滤机制")
        else:
            lines.append("- 弱相关: 情绪因子的贡献与数据量关系不大，可能受个股特性影响更多")
    else:
        lines.append("样本不足，无法计算相关性")
    lines.append("")

    lines.append("## 5. 优化建议")
    lines.append("")
    lines.append("### 策略层面")
    lines.append("1. **情绪信号滞后优化**: 当前使用5日EMA平滑，可尝试3日或自适应窗口")
    lines.append("2. **情绪极端值过滤**: 当单日新闻量<3条时降低情绪权重，避免小样本偏差")
    lines.append("3. **行业情绪联动**: 引入同行业其他股票的情绪数据作为辅助信号")
    lines.append("4. **市场状态自适应**: 牛市中降低情绪权重(趋势主导)，震荡市中提高情绪权重")
    lines.append("")
    lines.append("### 风控层面")
    lines.append("1. **动态止损**: 根据ATR自适应调整止损位，替代固定5%止损")
    lines.append("2. **仓位管理**: 引入Kelly公式或风险平价模型优化仓位")
    lines.append("3. **最大回撤控制**: 当组合回撤超过阈值时强制减仓")
    lines.append("")
    lines.append("### 数据层面")
    lines.append("1. **情绪粒度提升**: 使用news_articles表的逐条新闻数据，计算更精细的情绪指标")
    lines.append("2. **情绪词典优化**: 参考Loughran & McDonald (2011)构建A股专用金融情绪词典")
    lines.append("3. **多源情绪融合**: 结合社交媒体(雪球/东方财富股吧)情绪数据")
    lines.append("")

    lines.append("## 6. 学术参考")
    lines.append("")
    lines.append("| 论文 | 核心发现 | 本策略应用 |")
    lines.append("|------|---------|-----------|")
    lines.append("| Baker & Wurgler (2006) | 投资者情绪影响难估值股票的横截面收益 | 情绪维度权重自适应 |")
    lines.append("| Tetlock (2007) | 媒体悲观情绪预测市场下行 | 负面情绪突增修正因子 |")
    lines.append("| Loughran & McDonald (2011) | 金融文本需专用情感词典 | 情绪数据来源选择 |")
    lines.append("| Jegadeesh & Titman (1993) | 3-12月价格动量效应显著 | 均线趋势评分 |")
    lines.append("| Poterba & Summers (1988) | 长期股价均值回归 | 布林带超买超卖信号 |")
    lines.append("")
    lines.append("---")
    lines.append(f"*本报告由 InvestMindPro 回测系统自动生成，仅供研究参考，不构成投资建议。*")

    report = "\n".join(lines)

    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write(report)
    logger.info(f"\n报告已写入: {REPORT_PATH}")

    return report


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("AI情绪驱动策略回测 - 开始")
    logger.info(f"回测区间: {START_DATE} - {END_DATE}")
    logger.info(f"测试标的: {len(TEST_STOCKS)} 只")
    logger.info("=" * 60)

    results_tech, results_hybrid, sentiment_stats = run_all_backtests()

    if not results_tech:
        logger.error("所有股票回测失败，请检查网络连接和AKShare可用性")
        sys.exit(1)

    report = generate_report(results_tech, results_hybrid, sentiment_stats)
    print("\n" + report)
