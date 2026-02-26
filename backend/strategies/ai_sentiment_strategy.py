"""
AI情绪驱动量化策略 (AI Sentiment-Driven Quantitative Strategy)
==============================================================

策略概述：
    结合历史新闻情绪数据、多维技术指标和资金流向代理信号的混合量化策略。
    当情绪、技术、资金三维度产生共振时生成高置信度交易信号。

策略来源与学术基础：
    1. 情绪因子 (Sentiment Factor)
       - Baker & Wurgler (2006) "Investor Sentiment and the Cross-Section of Stock Returns"
         投资者情绪影响难以估值的股票（小盘、高波动、无盈利）的横截面收益。
       - Tetlock (2007) "Giving Content to Investor Sentiment: The Role of Media in the Stock Market"
         媒体悲观情绪预测市场下行压力，高悲观情绪后市场倾向反弹。
       - Loughran & McDonald (2011) "When Is a Liability Not a Liability?"
         金融文本需要专用情感词典，通用词典在金融语境下表现不佳。

    2. 动量因子 (Momentum Factor)
       - Jegadeesh & Titman (1993) "Returns to Buying Winners and Selling Losers"
         3-12个月的价格动量效应显著，赢家组合持续跑赢输家组合。
       - Carhart (1997) "On Persistence in Mutual Fund Performance"
         四因子模型（市场、规模、价值、动量）解释基金业绩持续性。

    3. 均值回归 (Mean Reversion)
       - Poterba & Summers (1988) "Mean Reversion in Stock Prices"
         长期（2-8年）股价存在负自相关，价格偏离基本面后倾向回归。

    4. 技术指标组合
       - RSI (Wilder, 1978): 相对强弱指标，衡量超买超卖
       - MACD (Appel, 1979): 趋势跟踪与动量确认
       - Bollinger Bands (Bollinger, 2001): 波动率通道，识别极端价格
       - 均线系统: 趋势方向判断

    5. 资金流向代理 (Fund Flow Proxy)
       - 量比 (Volume Ratio): 当日成交量/20日均量，反映资金活跃度
       - 价量背离: 价格创新高但成交量萎缩，预示趋势衰竭

数据来源：
    - 新闻情绪: InvestMindPro.db -> news_daily_sentiment 表
      字段: stock_code, date, positive_all, neutral_all, negative_all
    - K线数据: AKShare (ak.stock_zh_a_hist)
    - 技术指标: 策略内部计算
"""

import os
import sqlite3
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime
from .base import (
    BaseStrategy, StrategySignal, SignalType,
    StrategyConfig, StrategyCategory, register_strategy
)


# ---------------------------------------------------------------------------
# 情绪数据加载工具
# ---------------------------------------------------------------------------

def _find_db_path() -> Optional[str]:
    """定位 InvestMindPro.db（4.9 GB 主库，含 news_daily_sentiment）"""
    candidates = [
        os.path.join(os.path.dirname(__file__), '..', '..', 'InvestMindPro.db'),
        os.path.join(os.path.dirname(__file__), '..', 'InvestMindPro.db'),
    ]
    for p in candidates:
        full = os.path.abspath(p)
        if os.path.exists(full):
            return full
    return None


def load_sentiment_from_db(
    stock_code: str,
    start_date: str,
    end_date: str,
    db_path: Optional[str] = None,
) -> Optional[pd.DataFrame]:
    """
    从 SQLite 加载 news_daily_sentiment 数据。

    返回 DataFrame 列:
        date (DatetimeIndex), positive, neutral, negative, sent_raw, sent_smooth
    """
    if db_path is None:
        db_path = _find_db_path()
    if db_path is None or not os.path.exists(db_path):
        return None

    query = """
        SELECT date, positive_all AS positive, neutral_all AS neutral, negative_all AS negative
        FROM news_daily_sentiment
        WHERE stock_code = ? AND date >= ? AND date <= ?
        ORDER BY date
    """
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(query, conn, params=(stock_code, start_date, end_date))
        conn.close()
    except Exception:
        return None

    if df.empty:
        return None

    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)

    # 原始情绪分数: (正面 - 负面) / (总量 + 1)  ∈ [-1, 1]
    total = df['positive'] + df['neutral'] + df['negative']
    df['sent_raw'] = (df['positive'] - df['negative']) / (total + 1)

    # 5日指数平滑
    df['sent_smooth'] = df['sent_raw'].ewm(span=5, min_periods=1).mean()

    return df


def merge_sentiment_into_ohlcv(
    ohlcv: pd.DataFrame,
    sentiment: Optional[pd.DataFrame],
) -> pd.DataFrame:
    """将情绪数据合并到 K 线 DataFrame（按日期左连接）。"""
    df = ohlcv.copy()
    if sentiment is None or sentiment.empty:
        df['sent_raw'] = 0.0
        df['sent_smooth'] = 0.0
        df['sent_momentum'] = 0.0
        df['sent_volume'] = 0.0
        df['has_sentiment'] = False
        return df

    sent_cols = sentiment[['sent_raw', 'sent_smooth']].copy()
    df = df.join(sent_cols, how='left')
    df['sent_raw'] = df['sent_raw'].fillna(0.0)
    df['sent_smooth'] = df['sent_smooth'].fillna(method='ffill').fillna(0.0)

    # 情绪动量: 3日变化
    df['sent_momentum'] = df['sent_smooth'] - df['sent_smooth'].shift(3)
    df['sent_momentum'] = df['sent_momentum'].fillna(0.0)

    # 情绪成交量: 当日新闻总量（正+中+负），用于置信度加权
    if 'positive' in sentiment.columns:
        vol = (sentiment['positive'] + sentiment['neutral'] + sentiment['negative'])
        df = df.join(vol.rename('sent_volume'), how='left')
        df['sent_volume'] = df['sent_volume'].fillna(0.0)
    else:
        df['sent_volume'] = 0.0

    df['has_sentiment'] = df['sent_volume'] > 0
    return df


# ---------------------------------------------------------------------------
# AI 情绪驱动策略
# ---------------------------------------------------------------------------

@register_strategy("ai_sentiment")
class AISentimentStrategy(BaseStrategy):
    """
    AI情绪驱动量化策略

    信号生成逻辑（三维度加权共振）：
        composite = w_tech × tech_score + w_sent × sent_score + w_fund × fund_score

    维度说明：
        1. 技术维度 (tech_score ∈ [-1, 1]):
           RSI 超买超卖 + MACD 金叉死叉 + 布林带位置 + 均线趋势
        2. 情绪维度 (sent_score ∈ [-1, 1]):
           基于 news_daily_sentiment 的平滑情绪分数 + 情绪动量
        3. 资金维度 (fund_score ∈ [-1, 1]):
           量比 + 价量背离检测

    权重自适应：
        - 有充足情绪数据时: tech=0.35, sent=0.40, fund=0.25
        - 情绪数据不足时:   tech=0.55, sent=0.15, fund=0.30
    """

    description = "AI情绪驱动策略：融合新闻情绪、技术指标和资金流向的三维度共振策略"

    def __init__(self, config: Optional[StrategyConfig] = None):
        if config is None:
            config = StrategyConfig(
                name="AISentimentStrategy",
                category=StrategyCategory.AI,
                description="AI情绪驱动量化策略",
            )
        super().__init__(config)
        self.name = "AI情绪驱动策略"
        self.category = StrategyCategory.AI

        # ---- 技术指标参数 ----
        self.rsi_period = 14
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal_period = 9
        self.bb_period = 20
        self.bb_std = 2.0
        self.ma_short = 5
        self.ma_mid = 20
        self.ma_long = 60
        self.vol_ma_period = 20

        # ---- 信号阈值 ----
        self.strong_buy_threshold = 0.50
        self.buy_threshold = 0.20
        self.sell_threshold = -0.20
        self.strong_sell_threshold = -0.50

        # ---- 风险参数 ----
        self.risk_params = {
            "max_position_pct": 0.35,
            "stop_loss_pct": 0.05,
            "take_profit_pct": 0.12,
            "max_drawdown_pct": 0.12,
        }

    # ------------------------------------------------------------------
    # BaseStrategy 接口实现
    # ------------------------------------------------------------------

    def initialize(self, data: pd.DataFrame) -> None:
        self._initialized = True

    def get_required_indicators(self) -> List[str]:
        return [
            'rsi', 'macd', 'macd_signal', 'macd_hist',
            'bb_upper', 'bb_middle', 'bb_lower',
            'ma_5', 'ma_20', 'ma_60',
            'volume_ma', 'volume_ratio',
            'sent_smooth', 'sent_momentum',
        ]

    def generate_signal(
        self,
        data: pd.DataFrame,
        current_position: int = 0,
        **kwargs,
    ) -> StrategySignal:
        """生成交易信号（回测引擎调用入口）。"""
        df = self._ensure_indicators(data)

        if len(df) < self.ma_long + 5:
            return self._hold_signal("数据不足")

        row = df.iloc[-1]
        price = row['close']

        # ---- 三维度评分 ----
        tech_score, tech_reasons = self._calc_technical_score(df)
        sent_score, sent_reasons = self._calc_sentiment_score(df)
        fund_score, fund_reasons = self._calc_fund_flow_score(df)

        # ---- 自适应权重 ----
        # Baker & Wurgler (2006): 情绪数据充足时赋予更高权重
        has_sent = bool(row.get('has_sentiment', False))
        sent_vol = float(row.get('sent_volume', 0))
        if has_sent and sent_vol > 0:
            w_tech, w_sent, w_fund = 0.35, 0.40, 0.25
        else:
            w_tech, w_sent, w_fund = 0.55, 0.15, 0.30

        composite = w_tech * tech_score + w_sent * sent_score + w_fund * fund_score

        # ---- 特殊情况修正 ----
        # Tetlock (2007): 负面情绪突增时降低买入信心
        sent_mom = float(row.get('sent_momentum', 0))
        if sent_mom < -0.3 and composite > 0:
            composite *= 0.6
            sent_reasons.append("⚠️ 情绪急跌修正")

        # ---- 信号映射 ----
        if composite >= self.strong_buy_threshold:
            sig_type = SignalType.STRONG_BUY
        elif composite >= self.buy_threshold:
            sig_type = SignalType.BUY
        elif composite <= self.strong_sell_threshold:
            sig_type = SignalType.STRONG_SELL
        elif composite <= self.sell_threshold:
            sig_type = SignalType.SELL
        else:
            sig_type = SignalType.HOLD

        confidence = min(0.5 + abs(composite) * 0.4, 0.95)
        strength = min(abs(composite), 1.0)

        # ---- 构建原因列表 ----
        reasons = []
        reasons.extend(tech_reasons[:2])
        reasons.extend(sent_reasons[:2])
        reasons.extend(fund_reasons[:1])
        reasons.append(
            f"综合={composite:+.3f} (技术{tech_score:+.2f}×{w_tech} "
            f"情绪{sent_score:+.2f}×{w_sent} 资金{fund_score:+.2f}×{w_fund})"
        )

        is_buy = sig_type in (SignalType.BUY, SignalType.STRONG_BUY)
        return StrategySignal(
            signal_type=sig_type,
            confidence=round(confidence, 3),
            strength=round(strength, 3),
            price=price,
            stop_loss=round(price * (1 - self.risk_params['stop_loss_pct']), 2) if is_buy else 0,
            target_price=round(price * (1 + self.risk_params['take_profit_pct']), 2) if is_buy else 0,
            position_size=self.risk_params['max_position_pct'] * strength if is_buy else 0,
            reasons=reasons[:6],
            strategy_id="ai_sentiment",
            strategy_name=self.name,
        )

    # ------------------------------------------------------------------
    # 技术维度评分
    # ------------------------------------------------------------------

    def _calc_technical_score(self, df: pd.DataFrame) -> tuple:
        """
        技术指标综合评分 ∈ [-1, 1]

        参考:
            - Wilder (1978): RSI 超买(>70)/超卖(<30)
            - Appel (1979): MACD 金叉/死叉 + 零轴位置
            - Bollinger (2001): 价格触及上下轨
            - 均线多头/空头排列
        """
        row = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else row
        score = 0.0
        reasons = []

        # --- RSI ---
        rsi = row.get('rsi', 50)
        if rsi < 30:
            score += 0.30
            reasons.append(f"RSI超卖({rsi:.1f})")
        elif rsi < 40:
            score += 0.15
        elif rsi > 70:
            score -= 0.30
            reasons.append(f"RSI超买({rsi:.1f})")
        elif rsi > 60:
            score -= 0.15

        # --- MACD ---
        macd = row.get('macd', 0)
        macd_sig = row.get('macd_signal', 0)
        macd_hist = row.get('macd_hist', 0)
        prev_macd = prev.get('macd', 0)
        prev_sig = prev.get('macd_signal', 0)

        # 金叉/死叉
        golden_cross = (macd > macd_sig) and (prev_macd <= prev_sig)
        death_cross = (macd < macd_sig) and (prev_macd >= prev_sig)

        if golden_cross:
            bonus = 0.30 if macd > 0 else 0.20  # 零轴上方金叉更强
            score += bonus
            reasons.append("MACD金叉" + ("(零轴上)" if macd > 0 else ""))
        elif death_cross:
            score -= 0.25
            reasons.append("MACD死叉")
        elif macd_hist > 0:
            score += 0.10
        elif macd_hist < 0:
            score -= 0.10

        # --- 布林带 ---
        bb_upper = row.get('bb_upper', 0)
        bb_lower = row.get('bb_lower', 0)
        bb_mid = row.get('bb_middle', 0)
        price = row['close']

        if bb_lower > 0 and price <= bb_lower:
            score += 0.20
            reasons.append("触及布林下轨")
        elif bb_upper > 0 and price >= bb_upper:
            score -= 0.20
            reasons.append("触及布林上轨")

        # --- 均线趋势 ---
        ma5 = row.get('ma_5', 0)
        ma20 = row.get('ma_20', 0)
        ma60 = row.get('ma_60', 0)

        if ma5 > 0 and ma20 > 0 and ma60 > 0:
            if ma5 > ma20 > ma60:
                score += 0.20
                reasons.append("均线多头排列")
            elif ma5 < ma20 < ma60:
                score -= 0.20
                reasons.append("均线空头排列")

        return max(-1.0, min(1.0, score)), reasons

    # ------------------------------------------------------------------
    # 情绪维度评分
    # ------------------------------------------------------------------

    def _calc_sentiment_score(self, df: pd.DataFrame) -> tuple:
        """
        新闻情绪评分 ∈ [-1, 1]

        数据来源: news_daily_sentiment 表
        计算方法:
            sent_raw = (positive_all - negative_all) / (total + 1)
            sent_smooth = 5日EMA平滑
            sent_momentum = sent_smooth - sent_smooth.shift(3)

        参考:
            - Baker & Wurgler (2006): 情绪极端时对特定股票影响最大
            - Loughran & McDonald (2011): 金融文本情绪需专用词典
        """
        row = df.iloc[-1]
        reasons = []

        sent = float(row.get('sent_smooth', 0))
        momentum = float(row.get('sent_momentum', 0))
        has_data = bool(row.get('has_sentiment', False))

        if not has_data:
            reasons.append("📰 情绪: 无数据")
            return 0.0, reasons

        # 情绪分数直接作为基础分
        score = sent

        # 情绪动量加成: 情绪加速改善/恶化
        if abs(momentum) > 0.1:
            score += momentum * 0.3

        score = max(-1.0, min(1.0, score))

        direction = "正面" if sent > 0.1 else ("负面" if sent < -0.1 else "中性")
        reasons.append(f"📰 情绪{direction}({sent:+.2f}, 动量{momentum:+.2f})")

        return score, reasons

    # ------------------------------------------------------------------
    # 资金流向维度评分
    # ------------------------------------------------------------------

    def _calc_fund_flow_score(self, df: pd.DataFrame) -> tuple:
        """
        资金流向代理评分 ∈ [-1, 1]

        使用量比 (Volume Ratio) 和价量关系作为资金流向的代理变量。
        - 量比 > 2.0: 资金大幅流入信号
        - 量比 < 0.5: 资金萎缩信号
        - 价量背离: 价格新高但量能萎缩 → 趋势衰竭
        """
        row = df.iloc[-1]
        reasons = []
        score = 0.0

        vol_ratio = float(row.get('volume_ratio', 1.0))

        if vol_ratio > 2.0:
            score += 0.40
            reasons.append(f"💰 量比放大({vol_ratio:.1f}x)")
        elif vol_ratio > 1.5:
            score += 0.25
        elif vol_ratio > 1.2:
            score += 0.10
        elif vol_ratio < 0.5:
            score -= 0.30
            reasons.append(f"💰 量能萎缩({vol_ratio:.1f}x)")
        elif vol_ratio < 0.8:
            score -= 0.15

        # 价量背离检测: 近5日价格上涨但成交量下降
        if len(df) >= 6:
            price_chg = df['close'].iloc[-1] / df['close'].iloc[-5] - 1
            vol_chg = df['volume'].iloc[-5:].mean() / df['volume'].iloc[-10:-5].mean() - 1 if len(df) >= 11 else 0

            if price_chg > 0.03 and vol_chg < -0.2:
                score -= 0.20
                reasons.append("⚠️ 价量背离(量缩价涨)")
            elif price_chg < -0.03 and vol_chg > 0.3:
                score += 0.15
                reasons.append("放量下跌后企稳")

        if not reasons:
            reasons.append(f"💰 量比{vol_ratio:.1f}x")

        return max(-1.0, min(1.0, score)), reasons

    # ------------------------------------------------------------------
    # 辅助方法
    # ------------------------------------------------------------------

    def _ensure_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """确保 DataFrame 包含所需技术指标，缺失则计算。"""
        df = data.copy()

        # RSI
        if 'rsi' not in df.columns:
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(self.rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(self.rsi_period).mean()
            rs = gain / (loss + 1e-10)
            df['rsi'] = 100 - (100 / (1 + rs))

        # MACD
        if 'macd' not in df.columns:
            ema_f = df['close'].ewm(span=self.macd_fast).mean()
            ema_s = df['close'].ewm(span=self.macd_slow).mean()
            df['macd'] = ema_f - ema_s
            df['macd_signal'] = df['macd'].ewm(span=self.macd_signal_period).mean()
            df['macd_hist'] = df['macd'] - df['macd_signal']

        # Bollinger Bands
        if 'bb_upper' not in df.columns:
            df['bb_middle'] = df['close'].rolling(self.bb_period).mean()
            bb_std = df['close'].rolling(self.bb_period).std()
            df['bb_upper'] = df['bb_middle'] + self.bb_std * bb_std
            df['bb_lower'] = df['bb_middle'] - self.bb_std * bb_std

        # 均线
        for period, name in [(self.ma_short, 'ma_5'), (self.ma_mid, 'ma_20'), (self.ma_long, 'ma_60')]:
            if name not in df.columns:
                df[name] = df['close'].rolling(period).mean()

        # 量比
        if 'volume_ratio' not in df.columns:
            df['volume_ma'] = df['volume'].rolling(self.vol_ma_period).mean()
            df['volume_ratio'] = df['volume'] / (df['volume_ma'] + 1)

        # 情绪列默认值
        for col in ['sent_raw', 'sent_smooth', 'sent_momentum', 'sent_volume', 'has_sentiment']:
            if col not in df.columns:
                df[col] = False if col == 'has_sentiment' else 0.0

        return df

    def _hold_signal(self, reason: str) -> StrategySignal:
        return StrategySignal(
            signal_type=SignalType.HOLD,
            confidence=0.0,
            strength=0.0,
            reasons=[reason],
            strategy_id="ai_sentiment",
            strategy_name=self.name,
        )
