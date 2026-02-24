# -*- coding: utf-8 -*-
"""
全策略批量回测脚本
对所有策略 × 7只测试股票进行批量回测，生成完整报告

运行方式: python backend/scripts/batch_backtest_all.py
"""

import sys
import os
import json
import time
import logging
import sqlite3
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

# 设置项目路径
project_root = Path(__file__).parent.parent.parent
backend_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_root))
os.chdir(project_root)

import pandas as pd
import numpy as np

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('batch_backtest.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# ============ 配置参数 ============
START_DATE = "20200101"
END_DATE = "20241231"
INITIAL_CAPITAL = 1_000_000.0
COMMISSION_RATE = 0.0003  # 万三
SLIPPAGE_RATE = 0.0005    # 万五

TEST_STOCKS = {
    "600519": "贵州茅台",
    "601318": "中国平安",
    "000858": "五粮液",
    "000333": "美的集团",
    "000651": "格力电器",
    "600276": "恒瑞医药",
    "601888": "中国中免",
}

# 策略列表（按类别分组）
STRATEGIES = [
    # 技术分析
    "vegas_adx", "ema_breakout", "macd_crossover", "bollinger_breakout",
    "turtle_trading", "trident", "scalping_blade",
    # 价值投资
    "buffett_value", "lynch_growth", "graham_margin",
    # 动量/突破
    "limit_up_trading", "volume_price_surge", "dragon_leader",
    # 均值回归/特殊
    "martingale_refined",
    # AI/情绪策略
    "sentiment_resonance", "debate_weighted", "ai_sentiment_strategy",
    # 复合策略
    "wavetrend_jma",
    # Top3 融合策略
    "ensemble_top3",
    # WT+JMA 参数扫描
    "wavetrend_jma_t40", "wavetrend_jma_t50", "wavetrend_jma_t60", "wavetrend_jma_t70",
]

DB_PATH = str(project_root / "InvestMindPro.db")
REPORT_MD_PATH = str(project_root / "FULL_BACKTEST_REPORT.md")
RESULTS_JSON_PATH = str(project_root / "backtest_results.json")
CACHE_DIR = project_root / "backend" / "data" / "backtest_cache"


# ============ 数据加载 ============

def load_ohlcv(symbol: str, start: str, end: str) -> Optional[pd.DataFrame]:
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
    time.sleep(0.5)  # 减少请求频率
    return df


def load_sentiment(stock_code: str, start: str, end: str) -> Optional[pd.DataFrame]:
    """从 SQLite 加载情绪数据。"""
    if not os.path.exists(DB_PATH):
        logger.warning(f"数据库不存在: {DB_PATH}")
        return None

    try:
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
        return df
    except Exception as e:
        logger.warning(f"加载情绪数据失败: {e}")
        return None


def merge_sentiment(ohlcv: pd.DataFrame, sent: Optional[pd.DataFrame]) -> pd.DataFrame:
    """合并情绪到K线。"""
    df = ohlcv.copy()
    if sent is None or sent.empty:
        df['sent_raw'] = 0.0
        df['sent_smooth'] = 0.0
        df['sent_momentum'] = 0.0
        return df

    df = df.join(sent[['sent_raw', 'sent_smooth']], how='left')
    df['sent_raw'] = df['sent_raw'].fillna(0.0)
    df['sent_smooth'] = df['sent_smooth'].ffill().fillna(0.0)
    df['sent_momentum'] = df['sent_smooth'] - df['sent_smooth'].shift(3)
    df['sent_momentum'] = df['sent_momentum'].fillna(0.0)
    return df


# ============ 回测器 ============

class BatchBacktester:
    """
    批量回测器
    逐bar回测，支持A股T+1、手续费万三、滑点万五、印花税千一（卖出）
    """

    def __init__(self, initial_capital: float = 1_000_000.0):
        self.initial_capital = initial_capital

    def run(self, strategy, data: pd.DataFrame, stock_code: str) -> Dict[str, Any]:
        """运行回测，返回性能指标"""
        cash = self.initial_capital
        position = 0
        avg_cost = 0.0
        trades = []
        equity_curve = []

        # 初始化策略
        try:
            strategy.initialize(data)
        except Exception as e:
            logger.error(f"策略初始化失败: {e}")
            return {"error": f"初始化失败: {str(e)}"}

        # 从第65个bar开始（确保有足够历史数据计算指标）
        start_idx = 65
        if len(data) <= start_idx + 10:
            return {"error": "数据不足"}

        for idx in range(start_idx, len(data)):
            current_data = data.iloc[:idx + 1]
            bar = data.iloc[idx]
            price = float(bar['close'])

            # 生成信号
            try:
                signal = strategy.generate_signal(current_data, position)
                if signal is None:
                    signal_type = "hold"
                    confidence = 0.0
                else:
                    signal_type = signal.signal_type.value if hasattr(signal.signal_type, 'value') else str(signal.signal_type)
                    confidence = getattr(signal, 'confidence', 0.5)
            except Exception as e:
                logger.warning(f"信号生成失败: {e}")
                signal_type = "hold"
                confidence = 0.0

            # 执行交易逻辑
            if signal_type in ("buy", "strong_buy") and position == 0:
                # 计算买入数量（满仓的95%）
                max_value = cash * 0.95
                shares = int(max_value / price / 100) * 100
                if shares >= 100:
                    cost = shares * price
                    # 佣金万三，最低5元
                    commission = max(cost * COMMISSION_RATE, 5)
                    # 滑点万五
                    slippage = cost * SLIPPAGE_RATE
                    total = cost + commission + slippage
                    if total <= cash:
                        cash -= total
                        position = shares
                        avg_cost = price
                        trades.append({
                            'date': str(bar.name),
                            'action': 'BUY',
                            'price': price,
                            'shares': shares,
                            'commission': commission,
                            'slippage': slippage,
                        })

            elif signal_type in ("sell", "strong_sell") and position > 0:
                # 卖出全部
                revenue = position * price
                commission = max(revenue * COMMISSION_RATE, 5)
                slippage = revenue * SLIPPAGE_RATE
                stamp_tax = revenue * 0.001  # 印花税千一
                net = revenue - commission - slippage - stamp_tax
                profit = net - position * avg_cost
                profit_pct = profit / (position * avg_cost) if avg_cost > 0 else 0
                cash += net
                trades.append({
                    'date': str(bar.name),
                    'action': 'SELL',
                    'price': price,
                    'shares': position,
                    'commission': commission,
                    'slippage': slippage,
                    'stamp_tax': stamp_tax,
                    'profit': profit,
                    'profit_pct': profit_pct,
                })
                position = 0
                avg_cost = 0.0

            # 记录净值
            portfolio_value = cash + position * price
            equity_curve.append({'date': str(bar.name), 'value': portfolio_value})

        # 最终结算（按收盘价平仓）
        final_price = float(data.iloc[-1]['close'])
        final_value = cash + position * final_price

        # 计算指标
        metrics = self._calc_metrics(equity_curve, trades, final_value)
        metrics['stock_code'] = stock_code
        metrics['final_value'] = final_value
        metrics['trades_detail'] = trades[:20]  # 只保留前20笔交易详情
        return metrics

    def _calc_metrics(self, equity_curve: List[Dict], trades: List[Dict], final_value: float) -> Dict[str, Any]:
        """计算性能指标"""
        if not equity_curve:
            return self._empty_metrics()

        values = pd.Series([e['value'] for e in equity_curve])
        dates = pd.to_datetime([e['date'] for e in equity_curve])
        
        # 总收益
        total_return = (final_value / self.initial_capital) - 1

        # 年化收益
        days = (dates[-1] - dates[0]).days
        years = max(days / 365.25, 0.01)
        annual_return = (1 + total_return) ** (1 / years) - 1

        # 日收益率和波动率
        daily_returns = values.pct_change().dropna()
        volatility = daily_returns.std() * np.sqrt(252) if len(daily_returns) > 1 else 0

        # 夏普比率 (假设无风险利率3%)
        sharpe = (annual_return - 0.03) / volatility if volatility > 0 else 0

        # 最大回撤
        cummax = values.expanding().max()
        drawdown = (values - cummax) / cummax
        max_drawdown = drawdown.min()

        # 胜率
        sell_trades = [t for t in trades if t['action'] == 'SELL']
        win_trades = [t for t in sell_trades if t.get('profit', 0) > 0]
        win_rate = len(win_trades) / len(sell_trades) if sell_trades else 0

        # 索提诺比率
        downside = daily_returns[daily_returns < 0]
        downside_std = downside.std() * np.sqrt(252) if len(downside) > 1 else 0
        sortino = (annual_return - 0.03) / downside_std if downside_std > 0 else 0

        # 卡尔玛比率
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
            'buy_trades': len([t for t in trades if t['action'] == 'BUY']),
            'sell_trades': len(sell_trades),
            'win_trades': len(win_trades),
            'lose_trades': len(sell_trades) - len(win_trades),
        }

    def _empty_metrics(self) -> Dict[str, Any]:
        return {
            'total_return': 0, 'annual_return': 0, 'max_drawdown': 0,
            'sharpe_ratio': 0, 'sortino_ratio': 0, 'calmar_ratio': 0,
            'volatility': 0, 'win_rate': 0,
            'total_trades': 0, 'buy_trades': 0, 'sell_trades': 0,
            'win_trades': 0, 'lose_trades': 0,
        }


# ============ 策略加载 ============

def load_strategy(strategy_id: str):
    """动态加载策略类"""
    from backend.strategies.base import StrategyConfig, StrategyCategory

    config = StrategyConfig(name=strategy_id)

    try:
        if strategy_id == "vegas_adx":
            from backend.strategies.vegas_adx import VegasADXStrategy
            return VegasADXStrategy(config)
        elif strategy_id == "ema_breakout":
            from backend.strategies.ema_breakout import EMABreakoutStrategy
            return EMABreakoutStrategy(config)
        elif strategy_id == "macd_crossover":
            from backend.strategies.macd_crossover import MACDCrossoverStrategy
            return MACDCrossoverStrategy(config)
        elif strategy_id == "bollinger_breakout":
            from backend.strategies.bollinger_breakout import BollingerBreakoutStrategy
            return BollingerBreakoutStrategy(config)
        elif strategy_id == "turtle_trading":
            from backend.strategies.turtle_trading import TurtleTradingStrategy
            return TurtleTradingStrategy(config)
        elif strategy_id == "trident":
            from backend.strategies.trident import TridentStrategy
            return TridentStrategy(config)
        elif strategy_id == "scalping_blade":
            from backend.strategies.scalping_blade import ScalpingBladeStrategy
            return ScalpingBladeStrategy(config)
        elif strategy_id == "buffett_value":
            from backend.strategies.buffett_value import BuffettValueStrategy
            return BuffettValueStrategy(config)
        elif strategy_id == "lynch_growth":
            from backend.strategies.lynch_growth import LynchGrowthStrategy
            return LynchGrowthStrategy(config)
        elif strategy_id == "graham_margin":
            from backend.strategies.graham_margin import GrahamMarginStrategy
            return GrahamMarginStrategy(config)
        elif strategy_id == "limit_up_trading":
            from backend.strategies.limit_up_trading import LimitUpTradingStrategy
            return LimitUpTradingStrategy(config)
        elif strategy_id == "volume_price_surge":
            from backend.strategies.volume_price_surge import VolumePriceSurgeStrategy
            return VolumePriceSurgeStrategy(config)
        elif strategy_id == "dragon_leader":
            from backend.strategies.dragon_leader import DragonLeaderStrategy
            return DragonLeaderStrategy(config)
        elif strategy_id == "martingale_refined":
            from backend.strategies.martingale_refined import MartingaleRefinedStrategy
            return MartingaleRefinedStrategy(config)
        elif strategy_id == "sentiment_resonance":
            from backend.strategies.sentiment_resonance import SentimentResonanceStrategy
            return SentimentResonanceStrategy(config)
        elif strategy_id == "debate_weighted":
            from backend.strategies.debate_weighted import DebateWeightedStrategy
            return DebateWeightedStrategy(config)
        elif strategy_id == "ai_sentiment_strategy":
            from backend.strategies.ai_sentiment_strategy import AISentimentStrategy
            config.category = StrategyCategory.AI
            return AISentimentStrategy(config)
        elif strategy_id == "wavetrend_jma":
            from backend.strategies.wavetrend_jma import WaveTrendJMAStrategy
            return WaveTrendJMAStrategy(config)
        elif strategy_id == "ensemble_top3":
            from backend.strategies.ensemble_top3 import EnsembleTop3Strategy
            return EnsembleTop3Strategy(config)
        elif strategy_id.startswith("wavetrend_jma_t"):
            from backend.strategies.wavetrend_jma_scans import WaveTrendJMAVariant
            # 动态设置阈值
            threshold_map = {'t40': -40, 't50': -50, 't60': -60, 't70': -70}
            t_val = strategy_id.split('_t')[1]
            config.parameters['long_wt2_th'] = threshold_map.get(f't{t_val}', -50)
            return WaveTrendJMAVariant(config)
        else:
            logger.error(f"未知策略: {strategy_id}")
            return None
    except Exception as e:
        logger.error(f"加载策略 {strategy_id} 失败: {e}")
        return None


# ============ 主回测流程 ============

def run_batch_backtest():
    """运行批量回测"""
    logger.info("=" * 70)
    logger.info("InvestMindPro 全策略批量回测")
    logger.info(f"回测区间: {START_DATE} - {END_DATE}")
    logger.info(f"测试标的: {len(TEST_STOCKS)} 只股票")
    logger.info(f"策略数量: {len(STRATEGIES)} 个")
    logger.info("=" * 70)

    backtester = BatchBacktester(INITIAL_CAPITAL)
    all_results = {}
    errors = []

    # 预加载所有股票数据
    stock_data = {}
    sentiment_data = {}

    for code, name in TEST_STOCKS.items():
        logger.info(f"\n[数据加载] {code} {name}")
        ohlcv = load_ohlcv(code, START_DATE, END_DATE)
        if ohlcv is not None and len(ohlcv) >= 100:
            stock_data[code] = ohlcv
            sent = load_sentiment(code, START_DATE, END_DATE)
            sentiment_data[code] = sent
        else:
            logger.error(f"跳过 {code}: 数据不足")

    if not stock_data:
        logger.error("没有可用的股票数据，回测终止")
        return {}, []

    # 对每个策略运行回测
    for strategy_idx, strategy_id in enumerate(STRATEGIES, 1):
        logger.info(f"\n{'=' * 70}")
        logger.info(f"[{strategy_idx}/{len(STRATEGIES)}] 策略: {strategy_id}")
        logger.info(f"{'=' * 70}")

        # 加载策略
        strategy = load_strategy(strategy_id)
        if strategy is None:
            logger.error(f"策略 {strategy_id} 加载失败，跳过")
            errors.append({"strategy": strategy_id, "error": "加载失败"})
            continue

        strategy_results = {}

        # 对每只股票运行回测
        for stock_idx, (code, name) in enumerate(TEST_STOCKS.items(), 1):
            if code not in stock_data:
                continue

            print(f"  [{stock_idx}/{len(TEST_STOCKS)}] {code} {name}... ", end="", flush=True)

            try:
                ohlcv = stock_data[code]

                # 如果是情绪相关策略，合并情绪数据
                if strategy_id in ["sentiment_resonance", "ai_sentiment_strategy"]:
                    data = merge_sentiment(ohlcv.copy(), sentiment_data.get(code))
                else:
                    data = ohlcv.copy()

                # 运行回测
                result = backtester.run(strategy, data, code)

                if "error" in result:
                    print(f"失败: {result['error']}")
                    logger.warning(f"失败: {result['error']}")
                    errors.append({"strategy": strategy_id, "stock": code, "error": result['error']})
                else:
                    print(f"收益={result['total_return']:+.2%} 夏普={result['sharpe_ratio']:.2f} "
                          f"回撤={result['max_drawdown']:.2%} 交易={result['total_trades']}")
                    strategy_results[code] = result

            except Exception as e:
                print(f"异常: {str(e)[:50]}")
                logger.error(f"异常: {str(e)[:50]}")
                errors.append({"strategy": strategy_id, "stock": code, "error": str(e)})
                if strategy_id == "dragon_leader":
                    logger.warning(f"dragon_leader 策略已知有问题，继续下一个...")

        all_results[strategy_id] = strategy_results

    return all_results, errors


# ============ 报告生成 ============

def generate_markdown_report(all_results: Dict[str, Dict], errors: List[Dict]):
    """生成Markdown报告"""

    def avg_metric(results: Dict[str, Dict], key: str) -> float:
        """计算某指标的平均值"""
        vals = [r[key] for r in results.values() if key in r and 'error' not in r]
        return np.mean(vals) if vals else 0

    def fmt_pct(v): return f"{v:.2%}"
    def fmt_f2(v): return f"{v:.2f}"

    lines = []
    lines.append("# InvestMindPro 全策略批量回测报告")
    lines.append("")
    lines.append(f"**生成时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # 1. 回测配置
    lines.append("## 1. 回测配置")
    lines.append("")
    lines.append(f"- **回测区间:** {START_DATE[:4]}-{START_DATE[4:6]}-{START_DATE[6:]} ~ {END_DATE[:4]}-{END_DATE[4:6]}-{END_DATE[6:]}")
    lines.append(f"- **初始资金:** ¥{INITIAL_CAPITAL:,.0f}")
    lines.append(f"- **交易成本:** 佣金万三(最低5元) + 滑点万五 + 印花税千一(卖出)")
    lines.append(f"- **测试标的:** {len(TEST_STOCKS)}只沪深300成分股")
    lines.append(f"- **策略数量:** {len(STRATEGIES)}个")
    lines.append("")

    # 2. 测试标的
    lines.append("## 2. 测试标的")
    lines.append("")
    lines.append("| 代码 | 名称 |")
    lines.append("|------|------|")
    for code, name in TEST_STOCKS.items():
        lines.append(f"| {code} | {name} |")
    lines.append("")

    # 3. 策略综合排名
    lines.append("## 3. 策略综合排名")
    lines.append("")

    # 计算每个策略的平均表现
    strategy_summary = []
    for strategy_id, results in all_results.items():
        if not results:
            continue
        avg_return = avg_metric(results, 'total_return')
        avg_annual = avg_metric(results, 'annual_return')
        avg_drawdown = avg_metric(results, 'max_drawdown')
        avg_sharpe = avg_metric(results, 'sharpe_ratio')
        avg_winrate = avg_metric(results, 'win_rate')
        total_trades = sum(r.get('total_trades', 0) for r in results.values())

        strategy_summary.append({
            'strategy_id': strategy_id,
            'avg_return': avg_return,
            'avg_annual': avg_annual,
            'avg_drawdown': avg_drawdown,
            'avg_sharpe': avg_sharpe,
            'avg_winrate': avg_winrate,
            'total_trades': total_trades,
            'success_count': len(results)
        })

    # 按夏普比率排序
    strategy_summary.sort(key=lambda x: x['avg_sharpe'], reverse=True)

    lines.append("### 按夏普比率排名")
    lines.append("")
    lines.append("| 排名 | 策略 | 平均收益 | 年化收益 | 最大回撤 | 夏普比率 | 胜率 | 总交易 | 成功/总数 |")
    lines.append("|------|------|---------|---------|---------|---------|------|-------|----------|")
    for i, s in enumerate(strategy_summary, 1):
        lines.append(f"| {i} | {s['strategy_id']} | {fmt_pct(s['avg_return'])} | "
                    f"{fmt_pct(s['avg_annual'])} | {fmt_pct(s['avg_drawdown'])} | "
                    f"{fmt_f2(s['avg_sharpe'])} | {fmt_pct(s['avg_winrate'])} | "
                    f"{s['total_trades']} | {s['success_count']}/{len(TEST_STOCKS)} |")
    lines.append("")

    # 按总收益排序
    strategy_summary.sort(key=lambda x: x['avg_return'], reverse=True)
    lines.append("### 按总收益排名")
    lines.append("")
    lines.append("| 排名 | 策略 | 平均收益 | 年化收益 | 最大回撤 | 夏普比率 | 胜率 | 总交易 |")
    lines.append("|------|------|---------|---------|---------|---------|------|-------|")
    for i, s in enumerate(strategy_summary[:10], 1):
        lines.append(f"| {i} | {s['strategy_id']} | {fmt_pct(s['avg_return'])} | "
                    f"{fmt_pct(s['avg_annual'])} | {fmt_pct(s['avg_drawdown'])} | "
                    f"{fmt_f2(s['avg_sharpe'])} | {fmt_pct(s['avg_winrate'])} | {s['total_trades']} |")
    lines.append("")

    # 4. 单策略详细结果
    lines.append("## 4. 单策略详细结果")
    lines.append("")

    for strategy_id in STRATEGIES:
        if strategy_id not in all_results or not all_results[strategy_id]:
            continue

        lines.append(f"### {strategy_id}")
        lines.append("")
        lines.append("| 代码 | 名称 | 总收益 | 年化收益 | 最大回撤 | 夏普比率 | 胜率 | 交易次数 |")
        lines.append("|------|------|--------|---------|---------|---------|------|---------|")

        results = all_results[strategy_id]
        for code in TEST_STOCKS.keys():
            name = TEST_STOCKS[code]
            if code in results:
                r = results[code]
                lines.append(f"| {code} | {name} | {fmt_pct(r['total_return'])} | "
                            f"{fmt_pct(r['annual_return'])} | {fmt_pct(r['max_drawdown'])} | "
                            f"{fmt_f2(r['sharpe_ratio'])} | {fmt_pct(r['win_rate'])} | {r['total_trades']} |")
            else:
                lines.append(f"| {code} | {name} | N/A | N/A | N/A | N/A | N/A | N/A |")
        lines.append("")

    # 5. 单股票多策略对比
    lines.append("## 5. 单股票多策略对比")
    lines.append("")

    for code, name in TEST_STOCKS.items():
        lines.append(f"### {code} {name}")
        lines.append("")
        lines.append("| 策略 | 总收益 | 年化收益 | 最大回撤 | 夏普比率 | 胜率 | 交易次数 |")
        lines.append("|------|--------|---------|---------|---------|------|---------|")

        # 收集该股票所有策略的结果
        stock_results = []
        for strategy_id, results in all_results.items():
            if code in results:
                r = results[code]
                stock_results.append({
                    'strategy': strategy_id,
                    'total_return': r['total_return'],
                    'annual_return': r['annual_return'],
                    'max_drawdown': r['max_drawdown'],
                    'sharpe_ratio': r['sharpe_ratio'],
                    'win_rate': r['win_rate'],
                    'total_trades': r['total_trades']
                })

        # 按收益排序
        stock_results.sort(key=lambda x: x['total_return'], reverse=True)

        for r in stock_results:
            lines.append(f"| {r['strategy']} | {fmt_pct(r['total_return'])} | "
                        f"{fmt_pct(r['annual_return'])} | {fmt_pct(r['max_drawdown'])} | "
                        f"{fmt_f2(r['sharpe_ratio'])} | {fmt_pct(r['win_rate'])} | {r['total_trades']} |")
        lines.append("")

    # 6. 错误记录
    if errors:
        lines.append("## 6. 错误记录")
        lines.append("")
        lines.append("| 策略 | 股票 | 错误信息 |")
        lines.append("|------|------|---------|")
        for err in errors[:30]:  # 只显示前30条
            strategy = err.get('strategy', 'N/A')
            stock = err.get('stock', 'N/A')
            error_msg = str(err.get('error', 'Unknown'))[:50]
            lines.append(f"| {strategy} | {stock} | {error_msg} |")
        if len(errors) > 30:
            lines.append(f"| ... | ... | 还有 {len(errors) - 30} 条错误未显示 |")
        lines.append("")

    # 7. 策略分类汇总
    lines.append("## 7. 策略分类表现")
    lines.append("")

    categories = {
        '技术分析': ['vegas_adx', 'ema_breakout', 'macd_crossover', 'bollinger_breakout',
                   'turtle_trading', 'trident', 'scalping_blade'],
        '价值投资': ['buffett_value', 'lynch_growth', 'graham_margin'],
        '动量/突破': ['limit_up_trading', 'volume_price_surge', 'dragon_leader'],
        '均值回归': ['martingale_refined'],
        'AI/情绪': ['sentiment_resonance', 'debate_weighted', 'ai_sentiment_strategy'],
        '复合策略': ['wavetrend_jma', 'ensemble_top3', 'wavetrend_jma_t40', 'wavetrend_jma_t50', 'wavetrend_jma_t60', 'wavetrend_jma_t70']
    }

    lines.append("| 类别 | 策略数 | 平均收益 | 平均夏普 | 平均胜率 |")
    lines.append("|------|--------|---------|---------|---------|")
    for cat_name, cat_strategies in categories.items():
        cat_returns = []
        cat_sharpes = []
        cat_winrates = []
        for sid in cat_strategies:
            if sid in all_results and all_results[sid]:
                cat_returns.append(avg_metric(all_results[sid], 'total_return'))
                cat_sharpes.append(avg_metric(all_results[sid], 'sharpe_ratio'))
                cat_winrates.append(avg_metric(all_results[sid], 'win_rate'))

        if cat_returns:
            lines.append(f"| {cat_name} | {len(cat_strategies)} | "
                        f"{fmt_pct(np.mean(cat_returns))} | "
                        f"{fmt_f2(np.mean(cat_sharpes))} | "
                        f"{fmt_pct(np.mean(cat_winrates))} |")
    lines.append("")

    # 8. 关键发现
    lines.append("## 8. 关键发现")
    lines.append("")

    # 找出最佳和最差策略
    if strategy_summary:
        best = max(strategy_summary, key=lambda x: x['avg_sharpe'])
        worst = min(strategy_summary, key=lambda x: x['avg_sharpe'])
        lines.append(f"- **最佳策略(夏普):** {best['strategy_id']} (夏普{best['avg_sharpe']:.2f}, 收益{best['avg_return']:.2%})")
        lines.append(f"- **最差策略(夏普):** {worst['strategy_id']} (夏普{worst['avg_sharpe']:.2f}, 收益{worst['avg_return']:.2%})")

    # 统计成功/失败
    success_count = sum(1 for s in strategy_summary if s['success_count'] == len(TEST_STOCKS))
    lines.append(f"- **完整成功率:** {success_count}/{len(STRATEGIES)} 个策略在所有股票上成功运行")

    # 统计正收益策略
    positive_count = sum(1 for s in strategy_summary if s['avg_return'] > 0)
    lines.append(f"- **正收益策略:** {positive_count}/{len(strategy_summary)} 个策略平均收益为正")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*本报告由 InvestMindPro 批量回测系统自动生成，仅供研究参考，不构成投资建议。*")

    report = "\n".join(lines)

    with open(REPORT_MD_PATH, 'w', encoding='utf-8') as f:
        f.write(report)
    logger.info(f"\nMarkdown报告已保存: {REPORT_MD_PATH}")

    return report


def save_json_results(all_results: Dict, errors: List):
    """保存JSON格式的原始数据"""
    output = {
        "meta": {
            "generated_at": datetime.now().isoformat(),
            "start_date": START_DATE,
            "end_date": END_DATE,
            "initial_capital": INITIAL_CAPITAL,
            "commission_rate": COMMISSION_RATE,
            "slippage_rate": SLIPPAGE_RATE,
            "stocks": TEST_STOCKS,
            "strategies": STRATEGIES
        },
        "results": all_results,
        "errors": errors
    }

    with open(RESULTS_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2, default=str)
    logger.info(f"JSON数据已保存: {RESULTS_JSON_PATH}")


# ============ 主入口 ============

def main():
    """主入口"""
    logger.info("\n" + "=" * 70)
    logger.info("InvestMindPro 全策略批量回测 - 开始")
    logger.info("=" * 70)

    start_time = time.time()

    # 运行回测
    all_results, errors = run_batch_backtest()

    # 生成报告
    if all_results:
        generate_markdown_report(all_results, errors)
        save_json_results(all_results, errors)
    else:
        logger.error("没有回测结果，无法生成报告")

    elapsed = time.time() - start_time
    logger.info(f"\n{'=' * 70}")
    logger.info(f"回测完成，耗时: {elapsed:.1f}秒 ({elapsed/60:.1f}分钟)")
    logger.info(f"{'=' * 70}")


if __name__ == "__main__":
    main()
