# -*- coding: utf-8 -*-
"""
情绪趋势服务
查询 news_articles / news_daily_stats 表，计算7天/30天情绪趋势

Author: AI升级
Date: 2026-02-22
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path
import threading

logger = logging.getLogger(__name__)


class SentimentTrendService:
    """
    情绪趋势服务
    
    从 news_articles 表聚合情绪数据，计算：
    - 7天/30天情绪均值和趋势方向
    - 情绪动量（近期 vs 远期）
    - 情绪波动率
    - 正负面新闻比例变化
    """
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            base_dir = Path(__file__).parent.parent.parent
            data_dir = base_dir / "data" / "news_storage"
            self.db_path = str(data_dir / "news_database.db")
        else:
            self.db_path = db_path
        self._lock = threading.Lock()
        logger.info(f"SentimentTrendService initialized: {self.db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_sentiment_trend(self, stock_code: Optional[str] = None, days: int = 30) -> Dict[str, Any]:
        """
        获取情绪趋势数据
        
        Args:
            stock_code: 股票代码（None=全市场）
            days: 回溯天数
            
        Returns:
            {
                "trend_7d": {...},
                "trend_30d": {...},
                "momentum": float,       # 情绪动量 (-1 ~ 1)
                "volatility": float,      # 情绪波动率
                "direction": str,         # "bullish" / "bearish" / "neutral"
                "daily_scores": [...],    # 每日情绪分数
                "signal_strength": float  # 信号强度 0~1
            }
        """
        try:
            daily_data = self._query_daily_sentiment(stock_code, days)
            
            if not daily_data:
                return self._empty_trend()
            
            # 计算7天和30天趋势
            trend_7d = self._compute_window_trend(daily_data, 7)
            trend_30d = self._compute_window_trend(daily_data, 30)
            
            # 情绪动量：7天均值 vs 30天均值的差
            momentum = 0.0
            if trend_7d["avg_score"] is not None and trend_30d["avg_score"] is not None:
                momentum = trend_7d["avg_score"] - trend_30d["avg_score"]
                # 归一化到 -1 ~ 1
                momentum = max(-1.0, min(1.0, momentum * 5))
            
            # 方向判断
            if momentum > 0.2:
                direction = "bullish"
            elif momentum < -0.2:
                direction = "bearish"
            else:
                direction = "neutral"
            
            # 信号强度：基于动量绝对值和数据量
            data_confidence = min(len(daily_data) / 7.0, 1.0)
            signal_strength = abs(momentum) * data_confidence
            
            return {
                "trend_7d": trend_7d,
                "trend_30d": trend_30d,
                "momentum": round(momentum, 4),
                "volatility": trend_7d.get("volatility", 0.0),
                "direction": direction,
                "daily_scores": daily_data[-14:],  # 最近14天
                "signal_strength": round(signal_strength, 4),
                "stock_code": stock_code,
                "computed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to compute sentiment trend: {e}")
            return self._empty_trend()
    
    def _query_daily_sentiment(self, stock_code: Optional[str], days: int) -> List[Dict[str, Any]]:
        """从 news_articles 表聚合每日情绪"""
        try:
            with self._lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
                
                if stock_code:
                    cursor.execute("""
                        SELECT 
                            date(publish_time) as date,
                            COUNT(*) as total_count,
                            AVG(sentiment_score) as avg_score,
                            SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) as positive_count,
                            SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) as negative_count,
                            SUM(CASE WHEN sentiment = 'neutral' THEN 1 ELSE 0 END) as neutral_count
                        FROM news_articles
                        WHERE date(publish_time) >= ?
                        AND related_stocks LIKE ?
                        GROUP BY date(publish_time)
                        ORDER BY date(publish_time) ASC
                    """, (start_date, f'%"{stock_code}"%'))
                else:
                    cursor.execute("""
                        SELECT 
                            date(publish_time) as date,
                            COUNT(*) as total_count,
                            AVG(sentiment_score) as avg_score,
                            SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) as positive_count,
                            SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) as negative_count,
                            SUM(CASE WHEN sentiment = 'neutral' THEN 1 ELSE 0 END) as neutral_count
                        FROM news_articles
                        WHERE date(publish_time) >= ?
                        GROUP BY date(publish_time)
                        ORDER BY date(publish_time) ASC
                    """, (start_date,))
                
                rows = cursor.fetchall()
                conn.close()
                
                results = []
                for row in rows:
                    total = row['total_count'] or 1
                    pos = row['positive_count'] or 0
                    neg = row['negative_count'] or 0
                    
                    results.append({
                        "date": row['date'],
                        "total_count": total,
                        "avg_score": round(float(row['avg_score'] or 0), 4),
                        "positive_count": pos,
                        "negative_count": neg,
                        "neutral_count": row['neutral_count'] or 0,
                        "positive_ratio": round(pos / total, 4),
                        "negative_ratio": round(neg / total, 4),
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"Failed to query daily sentiment: {e}")
            return []
    
    def _compute_window_trend(self, daily_data: List[Dict], window: int) -> Dict[str, Any]:
        """计算指定窗口的趋势"""
        data = daily_data[-window:] if len(daily_data) >= window else daily_data
        
        if not data:
            return {"avg_score": None, "trend_slope": 0, "volatility": 0, "data_points": 0}
        
        scores = [d["avg_score"] for d in data]
        n = len(scores)
        
        # 均值
        avg_score = sum(scores) / n
        
        # 线性回归斜率（趋势方向）
        if n >= 2:
            x_mean = (n - 1) / 2.0
            y_mean = avg_score
            numerator = sum((i - x_mean) * (scores[i] - y_mean) for i in range(n))
            denominator = sum((i - x_mean) ** 2 for i in range(n))
            slope = numerator / denominator if denominator != 0 else 0
        else:
            slope = 0
        
        # 波动率（标准差）
        if n >= 2:
            variance = sum((s - avg_score) ** 2 for s in scores) / (n - 1)
            volatility = variance ** 0.5
        else:
            volatility = 0
        
        # 正负面比例趋势
        pos_ratios = [d["positive_ratio"] for d in data]
        neg_ratios = [d["negative_ratio"] for d in data]
        
        return {
            "avg_score": round(avg_score, 4),
            "trend_slope": round(slope, 6),
            "volatility": round(volatility, 4),
            "data_points": n,
            "latest_score": scores[-1] if scores else 0,
            "avg_positive_ratio": round(sum(pos_ratios) / n, 4),
            "avg_negative_ratio": round(sum(neg_ratios) / n, 4),
            "trend_direction": "up" if slope > 0.01 else ("down" if slope < -0.01 else "flat")
        }
    
    def _empty_trend(self) -> Dict[str, Any]:
        """返回空趋势数据"""
        empty_window = {
            "avg_score": None, "trend_slope": 0, "volatility": 0,
            "data_points": 0, "latest_score": 0,
            "avg_positive_ratio": 0, "avg_negative_ratio": 0,
            "trend_direction": "flat"
        }
        return {
            "trend_7d": empty_window,
            "trend_30d": empty_window,
            "momentum": 0.0,
            "volatility": 0.0,
            "direction": "neutral",
            "daily_scores": [],
            "signal_strength": 0.0,
            "stock_code": None,
            "computed_at": datetime.now().isoformat()
        }
    
    def get_stock_sentiment_summary(self, stock_code: str) -> Dict[str, Any]:
        """
        获取个股情绪摘要（供策略层使用）
        
        Returns:
            {
                "score": float,           # 综合情绪分 -1~1
                "direction": str,         # bullish/bearish/neutral
                "momentum": float,        # 情绪动量
                "confidence": float,      # 数据置信度
                "recent_negative_spike": bool,  # 近期是否有负面突增
                "trend_reversal": bool,   # 是否出现趋势反转
            }
        """
        trend = self.get_sentiment_trend(stock_code, days=30)
        
        t7 = trend["trend_7d"]
        t30 = trend["trend_30d"]
        
        # 综合情绪分
        score = t7.get("avg_score") or 0.0
        
        # 数据置信度
        data_points = t7.get("data_points", 0)
        confidence = min(data_points / 5.0, 1.0)
        
        # 负面突增检测：最近3天负面比例 > 30天均值的2倍
        daily = trend.get("daily_scores", [])
        recent_negative_spike = False
        if len(daily) >= 3 and t30.get("avg_negative_ratio", 0) > 0:
            recent_neg = sum(d["negative_ratio"] for d in daily[-3:]) / 3
            if recent_neg > t30["avg_negative_ratio"] * 2:
                recent_negative_spike = True
        
        # 趋势反转检测：7天和30天方向相反
        trend_reversal = (
            t7.get("trend_direction") != t30.get("trend_direction")
            and t7.get("trend_direction") != "flat"
            and t30.get("trend_direction") != "flat"
        )
        
        return {
            "score": round(score, 4),
            "direction": trend["direction"],
            "momentum": trend["momentum"],
            "confidence": round(confidence, 2),
            "recent_negative_spike": recent_negative_spike,
            "trend_reversal": trend_reversal,
            "signal_strength": trend["signal_strength"],
        }


# 全局实例
_trend_service = None

def get_sentiment_trend_service() -> SentimentTrendService:
    """获取情绪趋势服务实例（单例）"""
    global _trend_service
    if _trend_service is None:
        _trend_service = SentimentTrendService()
    return _trend_service
