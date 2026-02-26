#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻回测引擎 — 基于历史新闻 + K线数据的策略回测

核心逻辑：
  1. 加载回测区间的K线数据（含预热期）
  2. 从 news_articles 表加载历史新闻
  3. 逐交易日回放：技术面信号 + 消息面信号 → 动态权重融合 → BUY/SELL/HOLD
  4. 模拟交易执行（手续费 + 滑点）
  5. 计算回测指标：总收益率、年化收益率、最大回撤、夏普比率、胜率
  6. 输出回测报告、交易记录、每日净值曲线

用法:
    python backend/news_backtest_engine.py --stock 600519 --start 2025-01-01 --end 2025-12-31
    python backend/news_backtest_engine.py --stock 000858 --start 2025-06-01 --end 2025-12-31 --capital 200000
    python backend/news_backtest_engine.py --stock 601318 --start 2025-01-01 --end 2025-12-31 --commission 0.0005 --slippage 0.001

Author: InvestMindPro
Date: 2026-02-20
"""

import sys
import os
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

import numpy as np
import pandas as pd
import akshare as ak

from backend.database.database import get_db_context, init_database
from backend.database.models import NewsArticle
from backend.utils.logging_config import get_logger

# 复用 ai_strategy_generator 中的信号生成逻辑
from backend.ai_strategy_generator import (
    calculate_technical_indicators,
    generate_technical_signal,
    analyze_news_sentiment,
    calculate_dynamic_weights,
    fuse_signals,
)

logger = get_logger("news_backtest_engine")

# ==================== 常量 ====================

WARMUP_DAYS = 80          # 技术指标预热天数（MA60 需要至少60根K线）
MIN_TRADE_DAYS = 10       # 最少交易日数
NEWS_LOOKBACK_DAYS = 7    # 每个交易日回溯的新闻天数
SIGNAL_BUY_THRESHOLD = 15   # 融合得分 >= 此值触发买入
SIGNAL_SELL_THRESHOLD = -15  # 融合得分 <= 此值触发卖出


# ==================== 数据加载 ====================


def load_kline_for_backtest(
    stock_code: str, start_date: str, end_date: str, warmup_days: int = WARMUP_DAYS
) -> pd.DataFrame | None:
    """
    加载回测所需的K线数据（含预热期）

    Args:
        stock_code: 股票代码
        start_date: 回测开始日期 (YYYY-MM-DD)
        end_date: 回测结束日期 (YYYY-MM-DD)
        warmup_days: 预热天数

    Returns:
        DataFrame(date, open, high, low, close, volume) 或 None
    """
    try:
        # 预热期：往前多取数据
        actual_start = (
            datetime.strptime(start_date, "%Y-%m-%d") - timedelta(days=warmup_days + 30)
        ).strftime("%Y%m%d")
        actual_end = datetime.strptime(end_date, "%Y-%m-%d").strftime("%Y%m%d")

        logger.info(f"加载K线: {stock_code} ({actual_start} ~ {actual_end}，含预热期)")
        df = ak.stock_zh_a_hist(
            symbol=stock_code,
            period="daily",
            start_date=actual_start,
            end_date=actual_end,
            adjust="qfq",
        )

        if df is None or df.empty:
            logger.error(f"{stock_code}: AKShare 返回空数据")
            return None

        col_map = {
            "日期": "date", "开盘": "open", "收盘": "close",
            "最高": "high", "最低": "low", "成交量": "volume",
        }
        df = df.rename(columns=col_map)

        required = ["date", "open", "high", "low", "close", "volume"]
        for col in required:
            if col not in df.columns:
                logger.error(f"缺少必要列: {col}")
                return None

        df = df[required].copy()
        df["date"] = pd.to_datetime(df["date"])
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.dropna().sort_values("date").reset_index(drop=True)
        logger.info(f"获取到 {len(df)} 条K线数据")
        return df

    except Exception as e:
        logger.error(f"加载K线数据失败: {e}")
        return None


def load_news_for_backtest(
    stock_code: str, start_date: str, end_date: str
) -> list[dict]:
    """
    从 news_articles 表加载回测区间内的所有新闻

    Args:
        stock_code: 股票代码
        start_date: 回测开始日期 (YYYY-MM-DD)
        end_date: 回测结束日期 (YYYY-MM-DD)

    Returns:
        新闻列表，按 publish_time 排序
    """
    init_database()

    # 多取 NEWS_LOOKBACK_DAYS 天，确保第一天也有新闻可用
    dt_start = datetime.strptime(start_date, "%Y-%m-%d") - timedelta(days=NEWS_LOOKBACK_DAYS)
    dt_end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)

    articles = []
    with get_db_context() as db:
        query = db.query(NewsArticle).filter(
            NewsArticle.publish_time >= dt_start,
            NewsArticle.publish_time < dt_end,
        )
        # 同时获取个股新闻和市场新闻
        query = query.filter(
            (NewsArticle.stock_code == stock_code) | (NewsArticle.stock_code.is_(None))
        )
        query = query.order_by(NewsArticle.publish_time.asc())
        rows = query.all()

        for r in rows:
            articles.append({
                "title": r.title or "",
                "content": r.content or "",
                "source": r.source or "",
                "stock_code": r.stock_code,
                "publish_time": r.publish_time,
                "sentiment_score": r.sentiment_score,
            })

    logger.info(f"加载 {len(articles)} 条历史新闻 ({start_date} ~ {end_date})")
    return articles


def get_news_for_date(
    all_news: list[dict], current_date: datetime, lookback_days: int = NEWS_LOOKBACK_DAYS
) -> list[dict]:
    """筛选某个交易日可用的新闻（publish_time 在 [current_date - lookback_days, current_date] 内）"""
    cutoff = current_date - timedelta(days=lookback_days)
    return [
        art for art in all_news
        if art["publish_time"] is not None
        and cutoff <= art["publish_time"] <= current_date
    ]


# ==================== 回测引擎 ====================


class NewsBacktestEngine:
    """新闻回测引擎"""

    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission_rate: float = 0.0003,
        slippage_rate: float = 0.0005,
    ):
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate

        # 状态
        self.cash = initial_capital
        self.position_shares = 0       # 持仓股数
        self.position_avg_price = 0.0  # 持仓均价
        self.trades: list[dict] = []
        self.daily_nav: list[dict] = []  # 每日净值

    def run(
        self,
        stock_code: str,
        start_date: str,
        end_date: str,
    ) -> dict:
        """
        运行新闻回测

        Args:
            stock_code: 股票代码
            start_date: 回测开始日期 (YYYY-MM-DD)
            end_date: 回测结束日期 (YYYY-MM-DD)

        Returns:
            回测结果字典
        """
        logger.info("=" * 60)
        logger.info(f"新闻回测引擎 — {stock_code} ({start_date} ~ {end_date})")
        logger.info(f"初始资金: {self.initial_capital:,.2f}  手续费: {self.commission_rate:.4f}  滑点: {self.slippage_rate:.4f}")
        logger.info("=" * 60)

        # 1. 加载K线数据
        kline_df = load_kline_for_backtest(stock_code, start_date, end_date)
        if kline_df is None or len(kline_df) < WARMUP_DAYS + MIN_TRADE_DAYS:
            return {"success": False, "error": "K线数据不足，无法回测"}

        # 2. 加载历史新闻
        all_news = load_news_for_backtest(stock_code, start_date, end_date)

        # 3. 确定回测区间（排除预热期）
        bt_start = pd.Timestamp(start_date)
        bt_end = pd.Timestamp(end_date)
        backtest_mask = (kline_df["date"] >= bt_start) & (kline_df["date"] <= bt_end)
        backtest_indices = kline_df.index[backtest_mask].tolist()

        if len(backtest_indices) < MIN_TRADE_DAYS:
            return {"success": False, "error": f"回测区间交易日不足 {MIN_TRADE_DAYS} 天"}

        logger.info(f"回测交易日: {len(backtest_indices)} 天")

        # 4. 逐日回放
        for idx in backtest_indices:
            # 截取到当天的K线（含预热期数据）
            hist_df = kline_df.iloc[: idx + 1].copy()
            current_row = kline_df.iloc[idx]
            current_date = current_row["date"].to_pydatetime()
            close_price = float(current_row["close"])
            open_price = float(current_row["open"])

            # 计算技术指标 & 技术面信号
            hist_with_indicators = calculate_technical_indicators(hist_df)
            tech_result = generate_technical_signal(hist_with_indicators)

            # 获取当日可用新闻 & 消息面信号
            day_news = get_news_for_date(all_news, current_date)
            sent_result = analyze_news_sentiment(day_news)

            # 动态权重 & 融合信号
            tech_w, sent_w = calculate_dynamic_weights(hist_with_indicators, sent_result["total_count"])
            fused = fuse_signals(tech_result, sent_result, tech_w, sent_w)

            # 执行交易（使用开盘价模拟 T+0 简化，实际A股T+1，此处用当日收盘价近似）
            self._execute_signal(fused, close_price, current_date)

            # 记录每日净值
            portfolio_value = self.cash + self.position_shares * close_price
            self.daily_nav.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "close": close_price,
                "nav": round(portfolio_value, 2),
                "cash": round(self.cash, 2),
                "position_value": round(self.position_shares * close_price, 2),
                "signal": fused["signal"],
                "score": fused["score"],
            })

        # 5. 强制平仓（回测结束时如有持仓）
        if self.position_shares > 0:
            last_price = float(kline_df.iloc[backtest_indices[-1]]["close"])
            last_date = kline_df.iloc[backtest_indices[-1]]["date"].to_pydatetime()
            self._force_sell(last_price, last_date, reason="回测结束强制平仓")

        # 6. 计算指标
        metrics = self._calculate_metrics()

        result = {
            "success": True,
            "stock_code": stock_code,
            "backtest_period": {"start": start_date, "end": end_date, "trade_days": len(backtest_indices)},
            "params": {
                "initial_capital": self.initial_capital,
                "commission_rate": self.commission_rate,
                "slippage_rate": self.slippage_rate,
            },
            "metrics": metrics,
            "trades": self.trades,
            "daily_nav": self.daily_nav,
            "news_stats": {
                "total_news": len(all_news),
                "avg_daily_news": round(len(all_news) / max(len(backtest_indices), 1), 1),
            },
        }

        self._print_report(result)
        return result

    # -------------------- 交易执行 --------------------

    def _execute_signal(self, fused: dict, price: float, date: datetime):
        """根据融合信号执行交易"""
        signal = fused["signal"]
        score = fused["score"]
        confidence = fused["confidence"]

        if signal == "BUY" and self.position_shares == 0:
            self._buy(price, date, confidence, score, fused["reasons"])
        elif signal == "SELL" and self.position_shares > 0:
            self._sell(price, date, score, fused["reasons"])

    def _buy(self, price: float, date: datetime, confidence: float, score: float, reasons: list):
        """买入"""
        # 仓位比例：基于置信度，最低30%最高90%
        position_pct = max(0.3, min(0.9, confidence))
        available = self.cash * position_pct

        # 滑点
        exec_price = price * (1 + self.slippage_rate)

        # 计算可买股数（100股整数倍）
        shares = int(available / exec_price / 100) * 100
        if shares < 100:
            return

        cost = shares * exec_price
        commission = max(cost * self.commission_rate, 5.0)  # 最低5元
        total_cost = cost + commission

        if total_cost > self.cash:
            shares -= 100
            if shares < 100:
                return
            cost = shares * exec_price
            commission = max(cost * self.commission_rate, 5.0)
            total_cost = cost + commission

        self.cash -= total_cost
        self.position_shares = shares
        self.position_avg_price = exec_price

        self.trades.append({
            "date": date.strftime("%Y-%m-%d"),
            "action": "BUY",
            "price": round(exec_price, 2),
            "shares": shares,
            "cost": round(total_cost, 2),
            "commission": round(commission, 2),
            "cash_after": round(self.cash, 2),
            "score": score,
            "reason": reasons[0] if reasons else "",
        })
        logger.info(f"[{date.strftime('%Y-%m-%d')}] 买入 {shares}股 @ {exec_price:.2f}，成本 {total_cost:.2f}")

    def _sell(self, price: float, date: datetime, score: float, reasons: list):
        """卖出（全部）"""
        exec_price = price * (1 - self.slippage_rate)
        revenue = self.position_shares * exec_price
        commission = max(revenue * self.commission_rate, 5.0)
        stamp_tax = revenue * 0.001  # 印花税千分之一
        net_revenue = revenue - commission - stamp_tax

        # 盈亏
        profit = net_revenue - (self.position_avg_price * self.position_shares)
        profit_pct = profit / (self.position_avg_price * self.position_shares) if self.position_avg_price > 0 else 0

        self.cash += net_revenue

        self.trades.append({
            "date": date.strftime("%Y-%m-%d"),
            "action": "SELL",
            "price": round(exec_price, 2),
            "shares": self.position_shares,
            "revenue": round(net_revenue, 2),
            "commission": round(commission, 2),
            "stamp_tax": round(stamp_tax, 2),
            "profit": round(profit, 2),
            "profit_pct": round(profit_pct, 4),
            "cash_after": round(self.cash, 2),
            "score": score,
            "reason": reasons[0] if reasons else "",
        })
        logger.info(
            f"[{date.strftime('%Y-%m-%d')}] 卖出 {self.position_shares}股 @ {exec_price:.2f}，"
            f"盈亏 {profit:+.2f} ({profit_pct:+.2%})"
        )

        self.position_shares = 0
        self.position_avg_price = 0.0

    def _force_sell(self, price: float, date: datetime, reason: str = ""):
        """强制平仓"""
        self._sell(price, date, score=0, reasons=[reason])

    # -------------------- 指标计算 --------------------

    def _calculate_metrics(self) -> dict:
        """计算回测指标"""
        if not self.daily_nav:
            return {}

        navs = [d["nav"] for d in self.daily_nav]
        initial = self.initial_capital
        final = navs[-1]

        # 总收益率
        total_return_pct = (final - initial) / initial

        # 年化收益率
        trade_days = len(navs)
        years = trade_days / 252
        annual_return = (1 + total_return_pct) ** (1 / years) - 1 if years > 0 else 0

        # 最大回撤
        max_drawdown = self._calc_max_drawdown(navs)

        # 夏普比率（日收益率 → 年化）
        daily_returns = pd.Series(navs).pct_change().dropna()
        if len(daily_returns) > 1 and daily_returns.std() > 0:
            sharpe = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)
        else:
            sharpe = 0.0

        # 胜率
        sell_trades = [t for t in self.trades if t["action"] == "SELL"]
        winning = [t for t in sell_trades if t.get("profit", 0) > 0]
        win_rate = len(winning) / len(sell_trades) if sell_trades else 0

        # 盈亏比
        avg_win = np.mean([t["profit"] for t in winning]) if winning else 0
        losing = [t for t in sell_trades if t.get("profit", 0) <= 0]
        avg_loss = abs(np.mean([t["profit"] for t in losing])) if losing else 0
        profit_factor = avg_win / avg_loss if avg_loss > 0 else float("inf")

        return {
            "initial_capital": initial,
            "final_capital": round(final, 2),
            "total_return": round(final - initial, 2),
            "total_return_pct": round(total_return_pct, 4),
            "annual_return_pct": round(annual_return, 4),
            "max_drawdown": round(max_drawdown, 4),
            "sharpe_ratio": round(sharpe, 2),
            "total_trades": len(self.trades),
            "buy_trades": len([t for t in self.trades if t["action"] == "BUY"]),
            "sell_trades": len(sell_trades),
            "win_rate": round(win_rate, 4),
            "winning_trades": len(winning),
            "losing_trades": len(losing),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "profit_factor": round(profit_factor, 2) if profit_factor != float("inf") else 999.99,
        }

    @staticmethod
    def _calc_max_drawdown(navs: list[float]) -> float:
        """计算最大回撤"""
        peak = navs[0]
        max_dd = 0.0
        for nav in navs:
            if nav > peak:
                peak = nav
            dd = (peak - nav) / peak
            if dd > max_dd:
                max_dd = dd
        return max_dd

    # -------------------- 报告输出 --------------------

    def _print_report(self, result: dict):
        """打印回测报告"""
        m = result["metrics"]
        p = result["backtest_period"]
        params = result["params"]
        ns = result["news_stats"]

        print()
        print("=" * 65)
        print(f"  新闻回测报告 — {result['stock_code']}")
        print("=" * 65)
        print(f"  回测区间: {p['start']} ~ {p['end']}  ({p['trade_days']} 个交易日)")
        print(f"  初始资金: ¥{params['initial_capital']:,.2f}  手续费: {params['commission_rate']:.4f}  滑点: {params['slippage_rate']:.4f}")
        print(f"  新闻数据: 共 {ns['total_news']} 条，日均 {ns['avg_daily_news']} 条")
        print("-" * 65)
        print(f"  💰 最终资金: ¥{m['final_capital']:,.2f}")
        print(f"  📈 总收益率: {m['total_return_pct']:.2%}  (¥{m['total_return']:+,.2f})")
        print(f"  📊 年化收益: {m['annual_return_pct']:.2%}")
        print(f"  📉 最大回撤: {m['max_drawdown']:.2%}")
        print(f"  ⚡ 夏普比率: {m['sharpe_ratio']:.2f}")
        print("-" * 65)
        print(f"  交易次数: {m['total_trades']} (买入 {m['buy_trades']} / 卖出 {m['sell_trades']})")
        print(f"  胜率: {m['win_rate']:.2%}  (盈利 {m['winning_trades']} / 亏损 {m['losing_trades']})")
        print(f"  平均盈利: ¥{m['avg_win']:,.2f}  平均亏损: ¥{m['avg_loss']:,.2f}")
        print(f"  盈亏比: {m['profit_factor']:.2f}")
        print("-" * 65)

        # 最近交易记录
        trades = result["trades"]
        if trades:
            print("  最近交易记录:")
            for t in trades[-10:]:
                if t["action"] == "BUY":
                    print(f"    {t['date']}  BUY   {t['shares']}股 @ ¥{t['price']:.2f}  成本 ¥{t['cost']:,.2f}")
                else:
                    print(
                        f"    {t['date']}  SELL  {t['shares']}股 @ ¥{t['price']:.2f}  "
                        f"盈亏 ¥{t['profit']:+,.2f} ({t['profit_pct']:+.2%})"
                    )
        print("=" * 65)
        print()


# ==================== CLI ====================


def main():
    parser = argparse.ArgumentParser(description="InvestMindPro 新闻回测引擎 — 基于历史新闻+K线的策略回测")
    parser.add_argument("--stock", type=str, required=True, help="股票代码 (如 600519)")
    parser.add_argument("--start", type=str, required=True, help="回测开始日期 (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, required=True, help="回测结束日期 (YYYY-MM-DD)")
    parser.add_argument("--capital", type=float, default=100000.0, help="初始资金 (默认 100000)")
    parser.add_argument("--commission", type=float, default=0.0003, help="手续费率 (默认 0.0003)")
    parser.add_argument("--slippage", type=float, default=0.0005, help="滑点率 (默认 0.0005)")
    args = parser.parse_args()

    engine = NewsBacktestEngine(
        initial_capital=args.capital,
        commission_rate=args.commission,
        slippage_rate=args.slippage,
    )
    engine.run(
        stock_code=args.stock,
        start_date=args.start,
        end_date=args.end,
    )


if __name__ == "__main__":
    main()
