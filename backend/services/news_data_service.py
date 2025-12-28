"""
新闻数据服务
提供统一的新闻数据存储、查询、统计和管理功能
参考 TradingAgents-CN 的设计，适配 SQLite 数据库
"""

import hashlib
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_

from backend.database.models import StockNewsRecord, MonitoredStock
from backend.database.database import get_db
from backend.dataflows.news.news_filter import NewsRelevanceFilter, get_company_name, NEWS_QUALITY_CONFIG
from backend.dataflows.news.sentiment_engine import SentimentEngine

logger = logging.getLogger(__name__)


@dataclass
class NewsQueryParams:
    """新闻查询参数"""
    symbol: Optional[str] = None
    symbols: Optional[List[str]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    sentiment: Optional[str] = None  # positive/negative/neutral
    urgency: Optional[str] = None  # critical/high/medium/low
    report_type: Optional[str] = None  # financial/announcement/news/policy/research
    source: Optional[str] = None
    keywords: Optional[List[str]] = None
    min_score: Optional[int] = None  # 最低情绪分数
    limit: int = 50
    skip: int = 0
    sort_by: str = "pub_time"
    sort_order: str = "desc"  # asc/desc


@dataclass
class NewsStats:
    """新闻统计信息"""
    total_count: int = 0
    positive_count: int = 0
    negative_count: int = 0
    neutral_count: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    sources: Dict[str, int] = field(default_factory=dict)
    report_types: Dict[str, int] = field(default_factory=dict)
    avg_sentiment_score: float = 0.0
    sentiment_trend: str = "neutral"  # bullish/bearish/neutral


class NewsDataService:
    """新闻数据服务"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.sentiment_engine = SentimentEngine()

    def _generate_news_id(self, title: str, pub_time: datetime) -> str:
        """生成新闻唯一ID"""
        content = f"{title}_{pub_time.isoformat() if pub_time else ''}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def _assess_source_quality(self, source: str) -> str:
        """评估新闻来源质量"""
        if not source:
            return "unknown"

        source_lower = source.lower()

        for high_source in NEWS_QUALITY_CONFIG['high_quality_sources']:
            if high_source.lower() in source_lower:
                return "high"

        for medium_source in NEWS_QUALITY_CONFIG['medium_quality_sources']:
            if medium_source.lower() in source_lower:
                return "medium"

        for low_source in NEWS_QUALITY_CONFIG['low_quality_sources']:
            if low_source.lower() in source_lower:
                return "low"

        return "unknown"

    def save_news(
        self,
        db: Session,
        ts_code: str,
        news_list: List[Dict[str, Any]],
        apply_filter: bool = True,
        min_relevance_score: float = 30
    ) -> Dict[str, int]:
        """
        保存新闻数据

        Args:
            db: 数据库会话
            ts_code: 股票代码
            news_list: 新闻列表
            apply_filter: 是否应用相关性过滤
            min_relevance_score: 最低相关性评分

        Returns:
            保存统计信息
        """
        if not news_list:
            return {"saved": 0, "skipped": 0, "filtered": 0, "duplicate": 0}

        stats = {"saved": 0, "skipped": 0, "filtered": 0, "duplicate": 0}

        # 创建过滤器
        news_filter = None
        if apply_filter:
            company_name = get_company_name(ts_code)
            news_filter = NewsRelevanceFilter(ts_code, company_name)

        for news in news_list:
            try:
                title = news.get('title', news.get('新闻标题', ''))
                content = news.get('content', news.get('新闻内容', ''))

                if not title:
                    stats["skipped"] += 1
                    continue

                # 应用相关性过滤
                if news_filter:
                    relevance_score = news_filter.calculate_relevance_score(title, content)
                    if relevance_score < min_relevance_score:
                        stats["filtered"] += 1
                        continue

                # 解析发布时间
                pub_time = news.get('pub_time', news.get('发布时间'))
                if isinstance(pub_time, str):
                    try:
                        pub_time = datetime.fromisoformat(pub_time.replace('Z', '+00:00'))
                    except:
                        pub_time = datetime.utcnow()
                elif not isinstance(pub_time, datetime):
                    pub_time = datetime.utcnow()

                # 生成新闻ID
                news_id = self._generate_news_id(title, pub_time)

                # 检查是否已存在
                existing = db.query(StockNewsRecord).filter(
                    StockNewsRecord.news_id == news_id
                ).first()

                if existing:
                    stats["duplicate"] += 1
                    continue

                # 情绪分析
                sentiment_result = self.sentiment_engine.analyze(title, content)

                # 创建新闻记录
                news_record = StockNewsRecord(
                    ts_code=ts_code,
                    news_id=news_id,
                    title=title,
                    content=content[:5000] if content else None,  # 限制内容长度
                    summary=news.get('summary', news.get('摘要', ''))[:1000] if news.get('summary') or news.get('摘要') else None,
                    source=news.get('source', news.get('来源', '')),
                    url=news.get('url', news.get('链接', '')),
                    pub_time=pub_time,
                    sentiment=sentiment_result.get('sentiment', 'neutral'),
                    sentiment_score=sentiment_result.get('score', 50),
                    urgency=sentiment_result.get('urgency', 'medium'),
                    report_type=sentiment_result.get('report_type', 'news'),
                    keywords=sentiment_result.get('keywords', [])
                )

                db.add(news_record)
                stats["saved"] += 1

            except Exception as e:
                self.logger.error(f"保存新闻失败: {e}")
                stats["skipped"] += 1

        try:
            db.commit()
            self.logger.info(f"📰 新闻保存完成: {ts_code}, 保存={stats['saved']}, 过滤={stats['filtered']}, 重复={stats['duplicate']}")
        except Exception as e:
            db.rollback()
            self.logger.error(f"提交新闻数据失败: {e}")
            raise

        return stats

    def query_news(
        self,
        db: Session,
        params: NewsQueryParams
    ) -> List[Dict[str, Any]]:
        """
        查询新闻数据

        Args:
            db: 数据库会话
            params: 查询参数

        Returns:
            新闻列表
        """
        query = db.query(StockNewsRecord)

        # 构建查询条件
        if params.symbol:
            query = query.filter(StockNewsRecord.ts_code == params.symbol)
        elif params.symbols:
            query = query.filter(StockNewsRecord.ts_code.in_(params.symbols))

        if params.start_time:
            query = query.filter(StockNewsRecord.pub_time >= params.start_time)
        if params.end_time:
            query = query.filter(StockNewsRecord.pub_time <= params.end_time)

        if params.sentiment:
            query = query.filter(StockNewsRecord.sentiment == params.sentiment)
        if params.urgency:
            query = query.filter(StockNewsRecord.urgency == params.urgency)
        if params.report_type:
            query = query.filter(StockNewsRecord.report_type == params.report_type)
        if params.source:
            query = query.filter(StockNewsRecord.source.like(f"%{params.source}%"))
        if params.min_score:
            query = query.filter(StockNewsRecord.sentiment_score >= params.min_score)

        # 关键词搜索
        if params.keywords:
            keyword_filters = []
            for keyword in params.keywords:
                keyword_filters.append(StockNewsRecord.title.like(f"%{keyword}%"))
                keyword_filters.append(StockNewsRecord.content.like(f"%{keyword}%"))
            query = query.filter(or_(*keyword_filters))

        # 排序
        if params.sort_by == "pub_time":
            order_col = StockNewsRecord.pub_time
        elif params.sort_by == "sentiment_score":
            order_col = StockNewsRecord.sentiment_score
        elif params.sort_by == "created_at":
            order_col = StockNewsRecord.created_at
        else:
            order_col = StockNewsRecord.pub_time

        if params.sort_order == "desc":
            query = query.order_by(desc(order_col))
        else:
            query = query.order_by(order_col)

        # 分页
        query = query.offset(params.skip).limit(params.limit)

        # 执行查询
        results = query.all()
        return [record.to_dict() for record in results]

    def get_latest_news(
        self,
        db: Session,
        ts_code: Optional[str] = None,
        limit: int = 20,
        hours_back: int = 24
    ) -> List[Dict[str, Any]]:
        """获取最新新闻"""
        start_time = datetime.utcnow() - timedelta(hours=hours_back)

        params = NewsQueryParams(
            symbol=ts_code,
            start_time=start_time,
            limit=limit,
            sort_by="pub_time",
            sort_order="desc"
        )

        return self.query_news(db, params)

    def search_news(
        self,
        db: Session,
        query_text: str,
        ts_code: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        全文搜索新闻

        Args:
            db: 数据库会话
            query_text: 搜索文本
            ts_code: 股票代码（可选）
            limit: 返回数量限制

        Returns:
            搜索结果列表
        """
        query = db.query(StockNewsRecord)

        if ts_code:
            query = query.filter(StockNewsRecord.ts_code == ts_code)

        # 搜索标题和内容
        search_filter = or_(
            StockNewsRecord.title.like(f"%{query_text}%"),
            StockNewsRecord.content.like(f"%{query_text}%"),
            StockNewsRecord.summary.like(f"%{query_text}%")
        )
        query = query.filter(search_filter)

        # 按发布时间排序
        query = query.order_by(desc(StockNewsRecord.pub_time))
        query = query.limit(limit)

        results = query.all()
        return [record.to_dict() for record in results]

    def get_news_statistics(
        self,
        db: Session,
        ts_code: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> NewsStats:
        """
        获取新闻统计信息

        Args:
            db: 数据库会话
            ts_code: 股票代码
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            新闻统计信息
        """
        query = db.query(StockNewsRecord)

        if ts_code:
            query = query.filter(StockNewsRecord.ts_code == ts_code)
        if start_time:
            query = query.filter(StockNewsRecord.pub_time >= start_time)
        if end_time:
            query = query.filter(StockNewsRecord.pub_time <= end_time)

        # 获取所有记录
        records = query.all()

        if not records:
            return NewsStats()

        # 统计
        stats = NewsStats()
        stats.total_count = len(records)

        sentiment_scores = []
        for record in records:
            # 情绪统计
            if record.sentiment == 'positive':
                stats.positive_count += 1
            elif record.sentiment == 'negative':
                stats.negative_count += 1
            else:
                stats.neutral_count += 1

            # 紧急程度统计
            if record.urgency == 'critical':
                stats.critical_count += 1
            elif record.urgency == 'high':
                stats.high_count += 1
            elif record.urgency == 'medium':
                stats.medium_count += 1
            else:
                stats.low_count += 1

            # 来源统计
            source = record.source or 'unknown'
            stats.sources[source] = stats.sources.get(source, 0) + 1

            # 报告类型统计
            report_type = record.report_type or 'news'
            stats.report_types[report_type] = stats.report_types.get(report_type, 0) + 1

            # 情绪分数
            if record.sentiment_score:
                sentiment_scores.append(record.sentiment_score)

        # 计算平均情绪分数
        if sentiment_scores:
            stats.avg_sentiment_score = sum(sentiment_scores) / len(sentiment_scores)

        # 判断情绪趋势
        if stats.positive_count > stats.negative_count * 1.5:
            stats.sentiment_trend = "bullish"
        elif stats.negative_count > stats.positive_count * 1.5:
            stats.sentiment_trend = "bearish"
        else:
            stats.sentiment_trend = "neutral"

        return stats

    def get_sentiment_trend(
        self,
        db: Session,
        ts_code: str,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        获取情绪趋势（按天统计）

        Args:
            db: 数据库会话
            ts_code: 股票代码
            days: 天数

        Returns:
            每日情绪统计列表
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)

        query = db.query(StockNewsRecord).filter(
            StockNewsRecord.ts_code == ts_code,
            StockNewsRecord.pub_time >= start_time,
            StockNewsRecord.pub_time <= end_time
        ).all()

        # 按天分组统计
        daily_stats = {}
        for record in query:
            if record.pub_time:
                date_key = record.pub_time.strftime('%Y-%m-%d')
                if date_key not in daily_stats:
                    daily_stats[date_key] = {
                        'date': date_key,
                        'total': 0,
                        'positive': 0,
                        'negative': 0,
                        'neutral': 0,
                        'avg_score': 0,
                        'scores': []
                    }

                daily_stats[date_key]['total'] += 1
                if record.sentiment == 'positive':
                    daily_stats[date_key]['positive'] += 1
                elif record.sentiment == 'negative':
                    daily_stats[date_key]['negative'] += 1
                else:
                    daily_stats[date_key]['neutral'] += 1

                if record.sentiment_score:
                    daily_stats[date_key]['scores'].append(record.sentiment_score)

        # 计算每日平均分数
        result = []
        for date_key in sorted(daily_stats.keys()):
            stats = daily_stats[date_key]
            if stats['scores']:
                stats['avg_score'] = sum(stats['scores']) / len(stats['scores'])
            del stats['scores']
            result.append(stats)

        return result

    def delete_old_news(
        self,
        db: Session,
        days_to_keep: int = 90
    ) -> int:
        """
        删除过期新闻

        Args:
            db: 数据库会话
            days_to_keep: 保留天数

        Returns:
            删除的记录数量
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        deleted_count = db.query(StockNewsRecord).filter(
            StockNewsRecord.created_at < cutoff_date
        ).delete()

        db.commit()
        self.logger.info(f"🗑️ 删除过期新闻: {deleted_count}条")

        return deleted_count

    def get_news_by_id(
        self,
        db: Session,
        news_id: str
    ) -> Optional[Dict[str, Any]]:
        """根据ID获取新闻"""
        record = db.query(StockNewsRecord).filter(
            StockNewsRecord.news_id == news_id
        ).first()

        return record.to_dict() if record else None


# 全局服务实例
_news_data_service = None


def get_news_data_service() -> NewsDataService:
    """获取新闻数据服务实例"""
    global _news_data_service
    if _news_data_service is None:
        _news_data_service = NewsDataService()
        logger.info("✅ 新闻数据服务初始化成功")
    return _news_data_service
