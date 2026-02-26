#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI策略生成器 — 双轮驱动（技术面 + 消息面）

基于K线技术指标和新闻情绪分析，通过动态权重融合输出买卖建议。

技术面指标：MA / MACD / RSI / 布林带
消息面信号：基于 news_articles 表的关键词情绪分析
动态权重：震荡市技术面权重高，事件驱动时消息面权重高

用法:
    python backend/ai_strategy_generator.py --stock 600519
    python backend/ai_strategy_generator.py --stock 000858 --days 120
    python backend/ai_strategy_generator.py --stock 601318 --verbose

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

logger = get_logger("ai_strategy_generator")

# ==================== 常量 ====================

# 情绪关键词词典
POSITIVE_KEYWORDS = [
    "利好", "上涨", "涨停", "突破", "新高", "增长", "盈利", "超预期",
    "买入", "看涨", "回购", "增持", "分红", "扩产", "中标", "签约",
    "战略合作", "业绩预增", "净利润增长", "营收增长", "订单", "景气",
]
NEGATIVE_KEYWORDS = [
    "利空", "下跌", "跌停", "破位", "新低", "亏损", "低于预期",
    "卖出", "看跌", "减持", "质押", "违规", "处罚", "诉讼",
    "业绩预减", "净利润下降", "营收下滑", "暴雷", "退市", "风险",
    "ST", "停牌",
]


# ==================== 数据获取 ====================


def fetch_kline_data(stock_code: str, days: int = 120) -> pd.DataFrame | None:
    """
    通过 AKShare 获取个股日K线数据

    Args:
        stock_code: 股票代码，如 '600519'
        days: 获取天数

    Returns:
        DataFrame(date, open, high, low, close, volume) 或 None
    """
    try:
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days + 30)).strftime("%Y%m%d")

        logger.info(f"获取K线数据: {stock_code} ({start_date} ~ {end_date})")
        df = ak.stock_zh_a_hist(
            symbol=stock_code,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq",
        )

        if df is None or df.empty:
            logger.warning(f"{stock_code}: AKShare 返回空数据")
            return None

        # 统一列名
        col_map = {
            "日期": "date",
            "开盘": "open",
            "收盘": "close",
            "最高": "high",
            "最低": "low",
            "成交量": "volume",
        }
        df = df.rename(columns=col_map)

        required = ["date", "open", "high", "low", "close", "volume"]
        for col in required:
            if col not in df.columns:
                logger.error(f"缺少必要列: {col}，实际列: {list(df.columns)}")
                return None

        df = df[required].copy()
        df["date"] = pd.to_datetime(df["date"])
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.dropna().sort_values("date").reset_index(drop=True)
        logger.info(f"获取到 {len(df)} 条K线数据")
        return df

    except Exception as e:
        logger.error(f"获取K线数据失败: {e}")
        return None


def fetch_news_from_db(
    stock_code: str | None = None, days: int = 7
) -> list[dict]:
    """
    从 news_articles 表读取近期新闻

    Args:
        stock_code: 股票代码（None 则读取全部市场新闻）
        days: 回溯天数

    Returns:
        新闻列表 [{title, content, source, stock_code, publish_time, sentiment_score}]
    """
    init_database()
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    articles = []

    with get_db_context() as db:
        query = db.query(NewsArticle).filter(NewsArticle.crawl_time >= cutoff)
        if stock_code:
            # 同时获取个股新闻和市场新闻
            query = query.filter(
                (NewsArticle.stock_code == stock_code)
                | (NewsArticle.stock_code.is_(None))
            )
        query = query.order_by(NewsArticle.publish_time.desc())
        rows = query.limit(200).all()

        for r in rows:
            articles.append({
                "title": r.title or "",
                "content": r.content or "",
                "source": r.source or "",
                "stock_code": r.stock_code,
                "publish_time": r.publish_time,
                "sentiment_score": r.sentiment_score,
            })

    logger.info(f"从数据库读取 {len(articles)} 条新闻 (近{days}天)")
    return articles


# ==================== 技术面分析 ====================


def calculate_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """计算 MA / MACD / RSI / 布林带 技术指标"""
    df = df.copy()

    # --- MA ---
    df["ma5"] = df["close"].rolling(5).mean()
    df["ma10"] = df["close"].rolling(10).mean()
    df["ma20"] = df["close"].rolling(20).mean()
    df["ma60"] = df["close"].rolling(60).mean()

    # --- MACD ---
    ema12 = df["close"].ewm(span=12).mean()
    ema26 = df["close"].ewm(span=26).mean()
    df["dif"] = ema12 - ema26
    df["dea"] = df["dif"].ewm(span=9).mean()
    df["macd_hist"] = (df["dif"] - df["dea"]) * 2

    # --- RSI (14) ---
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0.0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    df["rsi"] = 100 - (100 / (1 + rs))

    # --- 布林带 (20, 2) ---
    df["boll_mid"] = df["close"].rolling(20).mean()
    boll_std = df["close"].rolling(20).std()
    df["boll_upper"] = df["boll_mid"] + 2 * boll_std
    df["boll_lower"] = df["boll_mid"] - 2 * boll_std

    # --- ATR (14) 用于判断震荡/趋势 ---
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - df["close"].shift(1)).abs(),
        (df["low"] - df["close"].shift(1)).abs(),
    ], axis=1).max(axis=1)
    df["atr"] = tr.rolling(14).mean()

    # --- 成交量均线 ---
    df["vol_ma20"] = df["volume"].rolling(20).mean()

    return df


def generate_technical_signal(df: pd.DataFrame) -> dict:
    """
    基于技术指标生成技术面信号

    Returns:
        {signal: BUY/SELL/HOLD, score: -100~100, reasons: [...]}
    """
    if len(df) < 30:
        return {"signal": "HOLD", "score": 0, "reasons": ["K线数据不足"]}

    row = df.iloc[-1]
    prev = df.iloc[-2]
    score = 0
    reasons = []

    # --- MA 多头/空头排列 ---
    ma5 = row.get("ma5")
    ma10 = row.get("ma10")
    ma20 = row.get("ma20")
    if pd.notna(ma5) and pd.notna(ma10) and pd.notna(ma20):
        if ma5 > ma10 > ma20:
            score += 20
            reasons.append("MA多头排列 (MA5>MA10>MA20)")
        elif ma5 < ma10 < ma20:
            score -= 20
            reasons.append("MA空头排列 (MA5<MA10<MA20)")
        # 金叉/死叉
        if pd.notna(prev.get("ma5")) and pd.notna(prev.get("ma10")):
            if prev["ma5"] <= prev["ma10"] and ma5 > ma10:
                score += 15
                reasons.append("MA5上穿MA10 (金叉)")
            elif prev["ma5"] >= prev["ma10"] and ma5 < ma10:
                score -= 15
                reasons.append("MA5下穿MA10 (死叉)")

    # --- MACD ---
    dif = row.get("dif")
    dea = row.get("dea")
    macd_hist = row.get("macd_hist")
    if pd.notna(dif) and pd.notna(dea):
        prev_dif = prev.get("dif")
        prev_dea = prev.get("dea")
        if pd.notna(prev_dif) and pd.notna(prev_dea):
            if prev_dif <= prev_dea and dif > dea:
                score += 20
                reasons.append(f"MACD金叉 (DIF={dif:.3f})")
            elif prev_dif >= prev_dea and dif < dea:
                score -= 20
                reasons.append(f"MACD死叉 (DIF={dif:.3f})")
        if pd.notna(macd_hist):
            if macd_hist > 0:
                score += 5
            else:
                score -= 5

    # --- RSI ---
    rsi = row.get("rsi")
    if pd.notna(rsi):
        if rsi < 30:
            score += 20
            reasons.append(f"RSI超卖 ({rsi:.1f})")
        elif rsi < 40:
            score += 10
            reasons.append(f"RSI偏低 ({rsi:.1f})")
        elif rsi > 70:
            score -= 20
            reasons.append(f"RSI超买 ({rsi:.1f})")
        elif rsi > 60:
            score -= 10
            reasons.append(f"RSI偏高 ({rsi:.1f})")

    # --- 布林带 ---
    close = row["close"]
    boll_upper = row.get("boll_upper")
    boll_lower = row.get("boll_lower")
    boll_mid = row.get("boll_mid")
    if pd.notna(boll_upper) and pd.notna(boll_lower):
        if close <= boll_lower:
            score += 15
            reasons.append(f"触及布林带下轨 ({boll_lower:.2f})")
        elif close >= boll_upper:
            score -= 15
            reasons.append(f"触及布林带上轨 ({boll_upper:.2f})")
        elif pd.notna(boll_mid) and close > boll_mid:
            score += 5
        elif pd.notna(boll_mid):
            score -= 5

    # --- 量价配合 ---
    vol = row.get("volume", 0)
    vol_ma = row.get("vol_ma20")
    if pd.notna(vol_ma) and vol_ma > 0:
        vol_ratio = vol / vol_ma
        if vol_ratio > 1.5 and score > 0:
            score += 10
            reasons.append(f"放量上涨 (量比{vol_ratio:.1f})")
        elif vol_ratio > 1.5 and score < 0:
            score -= 10
            reasons.append(f"放量下跌 (量比{vol_ratio:.1f})")

    # 限制范围
    score = max(-100, min(100, score))

    if score >= 20:
        signal = "BUY"
    elif score <= -20:
        signal = "SELL"
    else:
        signal = "HOLD"

    return {"signal": signal, "score": score, "reasons": reasons}


# ==================== 消息面分析 ====================


def analyze_news_sentiment(articles: list[dict]) -> dict:
    """
    基于关键词的新闻情绪分析

    Returns:
        {signal: BUY/SELL/HOLD, score: -100~100, reasons: [...],
         positive_count, negative_count, total_count}
    """
    if not articles:
        return {
            "signal": "HOLD",
            "score": 0,
            "reasons": ["无新闻数据"],
            "positive_count": 0,
            "negative_count": 0,
            "total_count": 0,
        }

    positive_count = 0
    negative_count = 0
    neutral_count = 0
    key_positive_news = []
    key_negative_news = []

    for art in articles:
        text = (art["title"] + " " + art["content"][:200]).lower()
        pos_hits = sum(1 for kw in POSITIVE_KEYWORDS if kw in text)
        neg_hits = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text)

        if pos_hits > neg_hits:
            positive_count += 1
            if pos_hits >= 2:
                key_positive_news.append(art["title"][:40])
        elif neg_hits > pos_hits:
            negative_count += 1
            if neg_hits >= 2:
                key_negative_news.append(art["title"][:40])
        else:
            neutral_count += 1

    total = len(articles)
    reasons = []

    # 计算情绪得分 (-100 ~ 100)
    if positive_count + negative_count == 0:
        score = 0
    else:
        ratio = (positive_count - negative_count) / (positive_count + negative_count)
        # 按新闻覆盖率缩放（新闻越多越可信）
        coverage = min(total / 20, 1.0)
        score = int(ratio * 80 * coverage)

    reasons.append(f"新闻统计: 正面{positive_count} / 负面{negative_count} / 中性{neutral_count} (共{total}条)")

    if key_positive_news:
        reasons.append(f"关键利好: {key_positive_news[0]}")
    if key_negative_news:
        reasons.append(f"关键利空: {key_negative_news[0]}")

    if score >= 20:
        signal = "BUY"
    elif score <= -20:
        signal = "SELL"
    else:
        signal = "HOLD"

    return {
        "signal": signal,
        "score": max(-100, min(100, score)),
        "reasons": reasons,
        "positive_count": positive_count,
        "negative_count": negative_count,
        "total_count": total,
    }


# ==================== 动态权重融合 ====================


def calculate_dynamic_weights(
    df: pd.DataFrame, news_count: int
) -> tuple[float, float]:
    """
    动态计算技术面/消息面权重

    规则:
    - 震荡市（ATR低、波动小）→ 技术面权重高
    - 事件驱动（新闻多、波动大）→ 消息面权重高

    Returns:
        (technical_weight, sentiment_weight)，两者之和为 1.0
    """
    # 默认权重
    tech_w = 0.6
    sent_w = 0.4

    if len(df) < 20:
        return tech_w, sent_w

    row = df.iloc[-1]

    # 波动率判断：ATR / 收盘价 的百分比
    atr = row.get("atr")
    close = row["close"]
    if pd.notna(atr) and close > 0:
        atr_pct = atr / close * 100
        if atr_pct < 1.5:
            # 低波动 → 震荡市，技术面更可靠
            tech_w = 0.70
            sent_w = 0.30
        elif atr_pct > 3.0:
            # 高波动 → 可能事件驱动
            tech_w = 0.45
            sent_w = 0.55

    # 新闻密度调整
    if news_count >= 30:
        # 新闻密集 → 消息面权重提升
        sent_w = min(sent_w + 0.10, 0.65)
        tech_w = 1.0 - sent_w
    elif news_count <= 3:
        # 新闻稀少 → 技术面为主
        tech_w = min(tech_w + 0.10, 0.80)
        sent_w = 1.0 - tech_w

    return round(tech_w, 2), round(sent_w, 2)


def fuse_signals(
    tech_result: dict,
    sent_result: dict,
    tech_weight: float,
    sent_weight: float,
) -> dict:
    """
    融合技术面和消息面信号

    Returns:
        {signal: BUY/SELL/HOLD, confidence: 0~1, score: -100~100,
         reasons: [...], tech_weight, sent_weight}
    """
    # 加权得分
    fused_score = tech_result["score"] * tech_weight + sent_result["score"] * sent_weight
    fused_score = max(-100, min(100, fused_score))

    # 置信度：两个信号方向一致时置信度更高
    tech_dir = 1 if tech_result["score"] > 0 else (-1 if tech_result["score"] < 0 else 0)
    sent_dir = 1 if sent_result["score"] > 0 else (-1 if sent_result["score"] < 0 else 0)

    base_confidence = abs(fused_score) / 100
    if tech_dir == sent_dir and tech_dir != 0:
        # 双轮共振 → 置信度加成
        confidence = min(base_confidence * 1.3, 0.95)
    elif tech_dir != 0 and sent_dir != 0 and tech_dir != sent_dir:
        # 方向矛盾 → 置信度打折
        confidence = base_confidence * 0.6
    else:
        confidence = base_confidence

    confidence = round(max(0.05, min(0.95, confidence)), 2)

    # 最终信号
    if fused_score >= 15:
        signal = "BUY"
    elif fused_score <= -15:
        signal = "SELL"
    else:
        signal = "HOLD"

    # 汇总理由
    reasons = []
    reasons.append(f"【技术面】得分 {tech_result['score']:+d} (权重{tech_weight:.0%})")
    reasons.extend([f"  · {r}" for r in tech_result["reasons"][:4]])
    reasons.append(f"【消息面】得分 {sent_result['score']:+d} (权重{sent_weight:.0%})")
    reasons.extend([f"  · {r}" for r in sent_result["reasons"][:3]])

    if tech_dir == sent_dir and tech_dir != 0:
        reasons.append("⚡ 技术面与消息面共振，信号增强")
    elif tech_dir != 0 and sent_dir != 0 and tech_dir != sent_dir:
        reasons.append("⚠ 技术面与消息面矛盾，建议观望")

    return {
        "signal": signal,
        "confidence": confidence,
        "score": round(fused_score, 1),
        "reasons": reasons,
        "tech_weight": tech_weight,
        "sent_weight": sent_weight,
    }


# ==================== 主流程 ====================


def generate_strategy(
    stock_code: str,
    days: int = 120,
    news_days: int = 7,
    verbose: bool = False,
) -> dict:
    """
    AI策略生成器主入口

    Args:
        stock_code: 股票代码
        days: K线回溯天数
        news_days: 新闻回溯天数
        verbose: 是否输出详细信息

    Returns:
        {stock_code, signal, confidence, score, reasons,
         technical, sentiment, weights, price, timestamp}
    """
    logger.info(f"{'='*60}")
    logger.info(f"AI策略生成器 — 分析 {stock_code}")
    logger.info(f"{'='*60}")

    # 1. 获取K线数据
    df = fetch_kline_data(stock_code, days=days)
    if df is None or len(df) < 30:
        return {
            "stock_code": stock_code,
            "signal": "HOLD",
            "confidence": 0.0,
            "score": 0,
            "reasons": ["K线数据不足，无法分析"],
            "timestamp": datetime.now().isoformat(),
        }

    # 2. 计算技术指标
    df = calculate_technical_indicators(df)

    # 3. 生成技术面信号
    tech_result = generate_technical_signal(df)
    logger.info(f"技术面信号: {tech_result['signal']} (得分 {tech_result['score']:+d})")

    # 4. 获取新闻并分析情绪
    articles = fetch_news_from_db(stock_code=stock_code, days=news_days)
    sent_result = analyze_news_sentiment(articles)
    logger.info(f"消息面信号: {sent_result['signal']} (得分 {sent_result['score']:+d})")

    # 5. 动态权重
    tech_w, sent_w = calculate_dynamic_weights(df, sent_result["total_count"])
    logger.info(f"动态权重: 技术面 {tech_w:.0%} / 消息面 {sent_w:.0%}")

    # 6. 融合信号
    result = fuse_signals(tech_result, sent_result, tech_w, sent_w)

    # 补充元数据
    last_row = df.iloc[-1]
    output = {
        "stock_code": stock_code,
        "signal": result["signal"],
        "confidence": result["confidence"],
        "score": result["score"],
        "reasons": result["reasons"],
        "technical": {
            "signal": tech_result["signal"],
            "score": tech_result["score"],
            "reasons": tech_result["reasons"],
        },
        "sentiment": {
            "signal": sent_result["signal"],
            "score": sent_result["score"],
            "positive": sent_result["positive_count"],
            "negative": sent_result["negative_count"],
            "total": sent_result["total_count"],
        },
        "weights": {
            "technical": tech_w,
            "sentiment": sent_w,
        },
        "price": {
            "close": float(last_row["close"]),
            "date": str(last_row["date"].date()) if hasattr(last_row["date"], "date") else str(last_row["date"]),
            "rsi": round(float(last_row["rsi"]), 1) if pd.notna(last_row.get("rsi")) else None,
            "macd_hist": round(float(last_row["macd_hist"]), 3) if pd.notna(last_row.get("macd_hist")) else None,
        },
        "timestamp": datetime.now().isoformat(),
    }

    # 打印结果
    _print_result(output, verbose)

    return output


def _print_result(result: dict, verbose: bool = False):
    """格式化打印分析结果"""
    signal_emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}
    sig = result["signal"]
    emoji = signal_emoji.get(sig, "⚪")

    print()
    print("=" * 60)
    print(f"  AI策略生成器 — {result['stock_code']} 分析报告")
    print("=" * 60)
    print(f"  收盘价: {result['price']['close']:.2f}  |  日期: {result['price']['date']}")
    print(f"  RSI: {result['price']['rsi']}  |  MACD柱: {result['price']['macd_hist']}")
    print("-" * 60)
    print(f"  {emoji} 综合信号: {sig}")
    print(f"  📊 置信度: {result['confidence']:.0%}")
    print(f"  📈 综合得分: {result['score']:+.1f}")
    print(f"  ⚖️  权重: 技术面 {result['weights']['technical']:.0%} / 消息面 {result['weights']['sentiment']:.0%}")
    print("-" * 60)

    if verbose:
        print("  分析理由:")
        for r in result["reasons"]:
            print(f"    {r}")
        print("-" * 60)

    news = result["sentiment"]
    print(f"  新闻: 正面{news['positive']} / 负面{news['negative']} / 共{news['total']}条")
    print("=" * 60)
    print()


# ==================== CLI ====================


def main():
    parser = argparse.ArgumentParser(description="InvestMindPro AI策略生成器 — 双轮驱动分析")
    parser.add_argument("--stock", type=str, required=True, help="股票代码 (如 600519)")
    parser.add_argument("--days", type=int, default=120, help="K线回溯天数 (默认120)")
    parser.add_argument("--news-days", type=int, default=7, help="新闻回溯天数 (默认7)")
    parser.add_argument("--verbose", action="store_true", help="输出详细分析理由")
    args = parser.parse_args()

    generate_strategy(
        stock_code=args.stock,
        days=args.days,
        news_days=args.news_days,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()
