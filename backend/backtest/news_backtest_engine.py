#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻回测引擎 - News Backtest Engine
实现技术+新闻双驱动回测系统的核心模块

功能：
1. 按日期范围查询历史新闻数据
2. 对历史新闻进行AI情绪分析
3. 生成新闻情绪时间序列数据
4. 与技术数据对齐（同一天的技术K线+新闻情绪）
"""

import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict
import asyncio

import pandas as pd
import numpy as np

# 添加项目根目录到路径
project_root = "/home/icysaintdx/.openclaw/workspace-investmindpro/InvestMindPro"
sys.path.insert(0, project_root)

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from backend.database.models import StockNewsRecord, MonitoredStock, Base
from backend.dataflows.news.sentiment_engine import SentimentEngine

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


@dataclass
class DailySentiment:
    """单日情绪数据"""
    date: str  # YYYY-MM-DD
    sentiment_score: float  # 0-100
    sentiment_label: str  # positive/negative/neutral
    news_count: int
    positive_count: int
    negative_count: int
    neutral_count: int
    urgency_score: float  # 紧急程度加权得分
    avg_confidence: float  # 平均置信度
    keywords: List[str] = field(default_factory=list)
    major_events: List[Dict] = field(default_factory=list)


@dataclass
class NewsBacktestResult:
    """新闻回测结果"""
    stock_code: str
    stock_name: str
    start_date: str
    end_date: str
    daily_sentiments: List[DailySentiment] = field(default_factory=list)
    sentiment_series: pd.DataFrame = field(default_factory=pd.DataFrame)
    statistics: Dict = field(default_factory=dict)


class NewsBacktestEngine:
    """
    新闻回测引擎
    
    功能：
    1. 加载指定股票在回测时间段内的历史新闻
    2. 进行情绪分析（使用已有SentimentEngine或重新分析）
    3. 生成情绪时间序列（日频）
    4. 提供数据对齐接口，与技术指标对齐
    """
    
    def __init__(self, db_url: Optional[str] = None):
        """
        初始化新闻回测引擎
        
        Args:
            db_url: 数据库连接URL，默认使用项目数据库
        """
        if db_url is None:
            db_url = f"sqlite:///{project_root}/InvestMindPro.db"
        
        self.engine = create_engine(db_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.sentiment_engine = SentimentEngine()
        
        logger.info(f"新闻回测引擎初始化完成，数据库: {db_url}")
    
    def get_db(self) -> Session:
        """获取数据库会话"""
        return self.SessionLocal()
    
    def fetch_news_for_period(
        self,
        stock_code: str,
        start_date: str,
        end_date: str
    ) -> List[StockNewsRecord]:
        """
        获取指定时间段内的新闻数据
        
        Args:
            stock_code: 股票代码（如 601888.SH 或 601888）
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD
            
        Returns:
            新闻记录列表
        """
        db = self.get_db()
        try:
            # 处理股票代码格式（去掉后缀）
            ts_code = stock_code.split('.')[0]
            
            # 转换日期字符串为datetime
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            
            # 查询新闻
            news_list = db.query(StockNewsRecord).filter(
                and_(
                    StockNewsRecord.ts_code == ts_code,
                    StockNewsRecord.pub_time >= start_dt,
                    StockNewsRecord.pub_time < end_dt
                )
            ).order_by(StockNewsRecord.pub_time.asc()).all()
            
            logger.info(f"获取到 {len(news_list)} 条新闻 [{stock_code}] {start_date} ~ {end_date}")
            return news_list
            
        except SQLAlchemyError as e:
            logger.error(f"数据库查询失败: {e}")
            return []
        finally:
            db.close()
    
    def analyze_news_sentiment(
        self,
        news: StockNewsRecord
    ) -> Dict[str, Any]:
        """
        分析单条新闻的情绪
        
        Args:
            news: 新闻记录
            
        Returns:
            情绪分析结果字典
        """
        # 使用已有的sentiment字段，如果没有则重新分析
        if news.sentiment and news.sentiment_score is not None:
            return {
                'sentiment': news.sentiment,
                'score': news.sentiment_score,
                'urgency': news.urgency or 'medium',
                'keywords': news.keywords or [],
                'source': 'database'
            }
        
        # 重新分析（使用SentimentEngine）
        text = f"{news.title} {news.content or ''}"
        result = self.sentiment_engine.analyze(text)
        
        return {
            'sentiment': result['sentiment'],
            'score': result['score'],
            'urgency': result.get('urgency', 'medium'),
            'keywords': result.get('keywords', []),
            'source': 'engine'
        }
    
    def aggregate_daily_sentiment(
        self,
        news_list: List[StockNewsRecord]
    ) -> Dict[str, DailySentiment]:
        """
        将新闻按日期聚合，生成每日情绪指标
        
        Args:
            news_list: 新闻列表
            
        Returns:
            日期->DailySentiment的字典
        """
        # 按日期分组
        daily_news: Dict[str, List[StockNewsRecord]] = defaultdict(list)
        for news in news_list:
            date_str = news.pub_time.strftime("%Y-%m-%d")
            daily_news[date_str].append(news)
        
        daily_sentiments = {}
        
        for date_str, day_news_list in sorted(daily_news.items()):
            sentiments = []
            positive_count = 0
            negative_count = 0
            neutral_count = 0
            urgency_scores = []
            all_keywords = []
            major_events = []
            
            for news in day_news_list:
                analysis = self.analyze_news_sentiment(news)
                sentiments.append(analysis['score'])
                
                # 统计正负中性
                if analysis['sentiment'] == 'positive':
                    positive_count += 1
                elif analysis['sentiment'] == 'negative':
                    negative_count += 1
                else:
                    neutral_count += 1
                
                # 紧急程度评分
                urgency_map = {'critical': 1.0, 'high': 0.7, 'medium': 0.4, 'low': 0.1}
                urgency_scores.append(urgency_map.get(analysis['urgency'], 0.4))
                
                # 收集关键词
                if analysis['keywords']:
                    all_keywords.extend(analysis['keywords'])
                
                # 记录重大事件（critical/high urgency）
                if analysis['urgency'] in ['critical', 'high']:
                    major_events.append({
                        'title': news.title,
                        'sentiment': analysis['sentiment'],
                        'score': analysis['score'],
                        'urgency': analysis['urgency']
                    })
            
            # 计算加权情绪得分（考虑紧急程度）
            if sentiments:
                # 基础平均分
                base_score = np.mean(sentiments)
                # 紧急程度加权
                urgency_weight = np.mean(urgency_scores)
                # 正负情绪倾向调整
                sentiment_bias = (positive_count - negative_count) / len(day_news_list)
                # 最终得分（0-100）
                final_score = base_score + (sentiment_bias * 10 * urgency_weight)
                final_score = max(0, min(100, final_score))  # 限制在0-100
            else:
                final_score = 50  # 中性
                urgency_weight = 0
            
            # 确定情绪标签
            if final_score >= 60:
                sentiment_label = 'positive'
            elif final_score <= 40:
                sentiment_label = 'negative'
            else:
                sentiment_label = 'neutral'
            
            daily_sentiments[date_str] = DailySentiment(
                date=date_str,
                sentiment_score=round(final_score, 2),
                sentiment_label=sentiment_label,
                news_count=len(day_news_list),
                positive_count=positive_count,
                negative_count=negative_count,
                neutral_count=neutral_count,
                urgency_score=round(urgency_weight * 100, 2),
                avg_confidence=round(50 + abs(final_score - 50), 2),
                keywords=list(set(all_keywords))[:10],  # 去重，保留前10
                major_events=major_events[:5]  # 保留前5个重大事件
            )
        
        return daily_sentiments
    
    def create_sentiment_series(
        self,
        daily_sentiments: Dict[str, DailySentiment]
    ) -> pd.DataFrame:
        """
        将每日情绪数据转换为pandas DataFrame时间序列
        
        Args:
            daily_sentiments: 日期->DailySentiment字典
            
        Returns:
            DataFrame包含情绪时间序列
        """
        if not daily_sentiments:
            return pd.DataFrame()
        
        records = []
        for date_str, sentiment in sorted(daily_sentiments.items()):
            records.append({
                'date': date_str,
                'sentiment_score': sentiment.sentiment_score,
                'sentiment_label': sentiment.sentiment_label,
                'news_count': sentiment.news_count,
                'positive_count': sentiment.positive_count,
                'negative_count': sentiment.negative_count,
                'neutral_count': sentiment.neutral_count,
                'urgency_score': sentiment.urgency_score,
                'sentiment_ma3': None,  # 将在后续计算
                'sentiment_ma7': None,
            })
        
        df = pd.DataFrame(records)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date').sort_index()
        
        # 计算移动平均线
        df['sentiment_ma3'] = df['sentiment_score'].rolling(window=3, min_periods=1).mean()
        df['sentiment_ma7'] = df['sentiment_score'].rolling(window=7, min_periods=1).mean()
        
        # 计算情绪MACD（类似价格MACD）
        df['sentiment_ema12'] = df['sentiment_score'].ewm(span=12, min_periods=1).mean()
        df['sentiment_ema26'] = df['sentiment_score'].ewm(span=26, min_periods=1).mean()
        df['sentiment_macd'] = df['sentiment_ema12'] - df['sentiment_ema26']
        df['sentiment_signal'] = df['sentiment_macd'].ewm(span=9, min_periods=1).mean()
        
        return df
    
    def run_backtest(
        self,
        stock_code: str,
        stock_name: str,
        start_date: str,
        end_date: str
    ) -> NewsBacktestResult:
        """
        执行新闻回测主入口
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD
            
        Returns:
            NewsBacktestResult包含完整回测结果
        """
        logger.info(f"开始新闻回测: {stock_name}({stock_code}) {start_date} ~ {end_date}")
        
        # 1. 获取新闻数据
        news_list = self.fetch_news_for_period(stock_code, start_date, end_date)
        
        if not news_list:
            logger.warning(f"未找到新闻数据: {stock_code}")
            return NewsBacktestResult(
                stock_code=stock_code,
                stock_name=stock_name,
                start_date=start_date,
                end_date=end_date
            )
        
        # 2. 聚合每日情绪
        daily_sentiments = self.aggregate_daily_sentiment(news_list)
        
        # 3. 生成时间序列
        sentiment_series = self.create_sentiment_series(daily_sentiments)
        
        # 4. 计算统计指标
        statistics = self._calculate_statistics(daily_sentiments, sentiment_series)
        
        result = NewsBacktestResult(
            stock_code=stock_code,
            stock_name=stock_name,
            start_date=start_date,
            end_date=end_date,
            daily_sentiments=list(daily_sentiments.values()),
            sentiment_series=sentiment_series,
            statistics=statistics
        )
        
        logger.info(f"新闻回测完成: {len(daily_sentiments)} 个交易日, 平均情绪得分: {statistics.get('avg_score', 0):.2f}")
        return result
    
    def _calculate_statistics(
        self,
        daily_sentiments: Dict[str, DailySentiment],
        sentiment_series: pd.DataFrame
    ) -> Dict:
        """计算情绪统计指标"""
        if not daily_sentiments:
            return {}
        
        scores = [s.sentiment_score for s in daily_sentiments.values()]
        news_counts = [s.news_count for s in daily_sentiments.values()]
        
        positive_days = sum(1 for s in daily_sentiments.values() if s.sentiment_label == 'positive')
        negative_days = sum(1 for s in daily_sentiments.values() if s.sentiment_label == 'negative')
        neutral_days = sum(1 for s in daily_sentiments.values() if s.sentiment_label == 'neutral')
        
        return {
            'total_days': len(daily_sentiments),
            'total_news': sum(news_counts),
            'avg_news_per_day': round(np.mean(news_counts), 2),
            'avg_score': round(np.mean(scores), 2),
            'score_std': round(np.std(scores), 2),
            'max_score': round(max(scores), 2),
            'min_score': round(min(scores), 2),
            'positive_days': positive_days,
            'negative_days': negative_days,
            'neutral_days': neutral_days,
            'positive_ratio': round(positive_days / len(daily_sentiments) * 100, 2),
            'sentiment_trend': 'up' if sentiment_series['sentiment_score'].iloc[-1] > sentiment_series['sentiment_score'].iloc[0] else 'down'
        }
    
    def align_with_price_data(
        self,
        sentiment_series: pd.DataFrame,
        price_data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        将情绪数据与价格数据对齐
        
        Args:
            sentiment_series: 情绪时间序列
            price_data: 价格数据DataFrame（需有date索引）
            
        Returns:
            合并后的DataFrame
        """
        # 确保price_data有date索引
        if 'date' in price_data.columns:
            price_data = price_data.set_index('date')
        
        price_data.index = pd.to_datetime(price_data.index)
        
        # 合并数据
        merged = price_data.join(sentiment_series, how='left')
        
        # 用前值填充缺失的情绪数据（交易日没有新闻的情况）
        merged['sentiment_score'] = merged['sentiment_score'].ffill()
        merged['sentiment_ma3'] = merged['sentiment_ma3'].ffill()
        merged['sentiment_ma7'] = merged['sentiment_ma7'].ffill()
        
        # 填充默认值
        merged['sentiment_score'] = merged['sentiment_score'].fillna(50)
        merged['sentiment_label'] = merged['sentiment_label'].fillna('neutral')
        
        return merged
    
    def export_to_json(
        self,
        result: NewsBacktestResult,
        filepath: str
    ):
        """
        导出回测结果为JSON文件
        
        Args:
            result: 回测结果
            filepath: 输出文件路径
        """
        export_data = {
            'stock_code': result.stock_code,
            'stock_name': result.stock_name,
            'start_date': result.start_date,
            'end_date': result.end_date,
            'statistics': result.statistics,
            'daily_sentiments': [
                {
                    'date': s.date,
                    'sentiment_score': s.sentiment_score,
                    'sentiment_label': s.sentiment_label,
                    'news_count': s.news_count,
                    'positive_count': s.positive_count,
                    'negative_count': s.negative_count,
                    'urgency_score': s.urgency_score,
                    'keywords': s.keywords,
                    'major_events': s.major_events
                }
                for s in result.daily_sentiments
            ]
        }
        
        # 添加时间序列数据
        if not result.sentiment_series.empty:
            export_data['sentiment_series'] = result.sentiment_series.reset_index().to_dict('records')
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"结果已导出: {filepath}")


# ==================== 快捷函数 ====================

def run_news_backtest(
    stock_code: str,
    stock_name: str,
    start_date: str,
    end_date: str,
    db_url: Optional[str] = None
) -> NewsBacktestResult:
    """
    快速执行新闻回测的便捷函数
    
    Args:
        stock_code: 股票代码
        stock_name: 股票名称
        start_date: 开始日期 YYYY-MM-DD
        end_date: 结束日期 YYYY-MM-DD
        db_url: 可选数据库URL
        
    Returns:
        NewsBacktestResult
    """
    engine = NewsBacktestEngine(db_url)
    return engine.run_backtest(stock_code, stock_name, start_date, end_date)


if __name__ == "__main__":
    # 测试代码
    result = run_news_backtest(
        stock_code="601888",
        stock_name="中国中免",
        start_date="2024-01-01",
        end_date="2024-06-30"
    )
    
    print(f"\n{'='*60}")
    print(f"新闻回测结果: {result.stock_name}({result.stock_code})")
    print(f"{'='*60}")
    print(f"统计指标:")
    for key, value in result.statistics.items():
        print(f"  {key}: {value}")
    
    # 导出结果
    result_dir = f"{project_root}/backtest_results"
    import os
    os.makedirs(result_dir, exist_ok=True)
    
    output_file = f"{result_dir}/news_backtest_{result.stock_code}_{result.start_date}_{result.end_date}.json"
    engine = NewsBacktestEngine()
    engine.export_to_json(result, output_file)
