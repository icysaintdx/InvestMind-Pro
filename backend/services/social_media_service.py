"""
社交媒体数据服务
提供统一的社交媒体数据存储、查询和分析功能
支持多平台：微博、微信、抖音、小红书、知乎、Twitter、Reddit
"""

import hashlib
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Index, Float
from sqlalchemy.ext.declarative import declarative_base

from backend.database.database import Base, get_db
from backend.dataflows.news.sentiment_engine import SentimentEngine

logger = logging.getLogger(__name__)


# ==================== 数据模型 ====================

class SocialMediaMessage(Base):
    """社交媒体消息表"""
    __tablename__ = 'social_media_messages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(String(100), unique=True, nullable=False, index=True)  # 消息唯一ID
    ts_code = Column(String(20), index=True)  # 关联股票代码

    # 平台信息
    platform = Column(String(20), nullable=False, index=True)  # weibo/wechat/douyin/xiaohongshu/zhihu/twitter/reddit
    message_type = Column(String(20), default='post')  # post/comment/repost/reply

    # 内容
    content = Column(Text)
    title = Column(String(500))
    url = Column(String(500))
    publish_time = Column(DateTime, index=True)

    # 作者信息
    author_name = Column(String(100))
    author_id = Column(String(100))
    author_verified = Column(Integer, default=0)  # 是否认证
    author_followers = Column(Integer, default=0)  # 粉丝数
    influence_score = Column(Float, default=0.0)  # 影响力评分 0-100

    # 互动数据
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    engagement_rate = Column(Float, default=0.0)  # 互动率

    # 情绪分析
    sentiment = Column(String(20))  # positive/negative/neutral
    sentiment_score = Column(Integer)  # 0-100
    importance = Column(String(20), default='medium')  # critical/high/medium/low

    # 标签
    hashtags = Column(JSON)  # 话题标签列表
    keywords = Column(JSON)  # 关键词列表
    mentioned_stocks = Column(JSON)  # 提及的股票列表

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 索引
    __table_args__ = (
        Index('idx_social_platform_time', 'platform', 'publish_time'),
        Index('idx_social_stock_time', 'ts_code', 'publish_time'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'message_id': self.message_id,
            'ts_code': self.ts_code,
            'platform': self.platform,
            'message_type': self.message_type,
            'content': self.content,
            'title': self.title,
            'url': self.url,
            'publish_time': self.publish_time.isoformat() if self.publish_time else None,
            'author': {
                'name': self.author_name,
                'id': self.author_id,
                'verified': bool(self.author_verified),
                'followers': self.author_followers,
                'influence_score': self.influence_score
            },
            'engagement': {
                'views': self.views,
                'likes': self.likes,
                'shares': self.shares,
                'comments': self.comments,
                'engagement_rate': self.engagement_rate
            },
            'sentiment': self.sentiment,
            'sentiment_score': self.sentiment_score,
            'importance': self.importance,
            'hashtags': self.hashtags,
            'keywords': self.keywords,
            'mentioned_stocks': self.mentioned_stocks,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# ==================== 数据类 ====================

@dataclass
class SocialMediaQueryParams:
    """社媒消息查询参数"""
    symbol: Optional[str] = None
    symbols: Optional[List[str]] = None
    platform: Optional[str] = None  # weibo/wechat/douyin/xiaohongshu/zhihu/twitter/reddit
    message_type: Optional[str] = None  # post/comment/repost/reply
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    sentiment: Optional[str] = None
    importance: Optional[str] = None
    min_influence_score: Optional[float] = None
    min_engagement_rate: Optional[float] = None
    verified_only: bool = False
    keywords: Optional[List[str]] = None
    hashtags: Optional[List[str]] = None
    limit: int = 50
    skip: int = 0
    sort_by: str = "publish_time"
    sort_order: str = "desc"


@dataclass
class SocialMediaStats:
    """社媒消息统计信息"""
    total_count: int = 0
    positive_count: int = 0
    negative_count: int = 0
    neutral_count: int = 0
    platforms: Dict[str, int] = field(default_factory=dict)
    message_types: Dict[str, int] = field(default_factory=dict)
    top_hashtags: List[Dict[str, Any]] = field(default_factory=list)
    avg_engagement_rate: float = 0.0
    total_views: int = 0
    total_likes: int = 0
    total_shares: int = 0
    total_comments: int = 0
    sentiment_trend: str = "neutral"


# ==================== 服务类 ====================

class SocialMediaService:
    """社交媒体数据服务"""

    # 平台配置
    PLATFORMS = {
        'weibo': {'name': '微博', 'weight': 1.0},
        'wechat': {'name': '微信', 'weight': 0.9},
        'douyin': {'name': '抖音', 'weight': 0.8},
        'xiaohongshu': {'name': '小红书', 'weight': 0.7},
        'zhihu': {'name': '知乎', 'weight': 0.8},
        'twitter': {'name': 'Twitter', 'weight': 0.6},
        'reddit': {'name': 'Reddit', 'weight': 0.5}
    }

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.sentiment_engine = SentimentEngine()

    def _generate_message_id(self, platform: str, content: str, publish_time: datetime) -> str:
        """生成消息唯一ID"""
        data = f"{platform}_{content[:100]}_{publish_time.isoformat() if publish_time else ''}"
        return hashlib.md5(data.encode('utf-8')).hexdigest()

    def _calculate_influence_score(self, followers: int, verified: bool) -> float:
        """计算影响力评分"""
        base_score = 0

        # 基于粉丝数
        if followers >= 10000000:  # 1000万+
            base_score = 90
        elif followers >= 1000000:  # 100万+
            base_score = 80
        elif followers >= 100000:  # 10万+
            base_score = 60
        elif followers >= 10000:  # 1万+
            base_score = 40
        elif followers >= 1000:  # 1000+
            base_score = 20
        else:
            base_score = 10

        # 认证加成
        if verified:
            base_score = min(100, base_score + 15)

        return base_score

    def _calculate_engagement_rate(self, views: int, likes: int, shares: int, comments: int) -> float:
        """计算互动率"""
        if views <= 0:
            return 0.0

        total_engagement = likes + shares * 2 + comments * 3  # 加权计算
        return min(100, (total_engagement / views) * 100)

    def save_messages(
        self,
        db: Session,
        messages: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        批量保存社媒消息

        Args:
            db: 数据库会话
            messages: 消息列表

        Returns:
            保存统计信息
        """
        if not messages:
            return {"saved": 0, "skipped": 0, "duplicate": 0}

        stats = {"saved": 0, "skipped": 0, "duplicate": 0}

        for msg in messages:
            try:
                platform = msg.get('platform', 'unknown')
                content = msg.get('content', '')

                if not content:
                    stats["skipped"] += 1
                    continue

                # 解析发布时间
                publish_time = msg.get('publish_time')
                if isinstance(publish_time, str):
                    try:
                        publish_time = datetime.fromisoformat(publish_time.replace('Z', '+00:00'))
                    except:
                        publish_time = datetime.utcnow()
                elif not isinstance(publish_time, datetime):
                    publish_time = datetime.utcnow()

                # 生成消息ID
                message_id = msg.get('message_id') or self._generate_message_id(platform, content, publish_time)

                # 检查是否已存在
                existing = db.query(SocialMediaMessage).filter(
                    SocialMediaMessage.message_id == message_id
                ).first()

                if existing:
                    stats["duplicate"] += 1
                    continue

                # 提取作者信息
                author = msg.get('author', {})
                followers = author.get('followers', 0)
                verified = author.get('verified', False)

                # 提取互动数据
                engagement = msg.get('engagement', {})
                views = engagement.get('views', 0)
                likes = engagement.get('likes', 0)
                shares = engagement.get('shares', 0)
                comments = engagement.get('comments', 0)

                # 计算评分
                influence_score = self._calculate_influence_score(followers, verified)
                engagement_rate = self._calculate_engagement_rate(views, likes, shares, comments)

                # 情绪分析
                sentiment_result = self.sentiment_engine.analyze(msg.get('title', ''), content)

                # 创建记录
                record = SocialMediaMessage(
                    message_id=message_id,
                    ts_code=msg.get('ts_code', msg.get('symbol')),
                    platform=platform,
                    message_type=msg.get('message_type', 'post'),
                    content=content[:5000],
                    title=msg.get('title', '')[:500] if msg.get('title') else None,
                    url=msg.get('url'),
                    publish_time=publish_time,
                    author_name=author.get('name'),
                    author_id=author.get('id'),
                    author_verified=1 if verified else 0,
                    author_followers=followers,
                    influence_score=influence_score,
                    views=views,
                    likes=likes,
                    shares=shares,
                    comments=comments,
                    engagement_rate=engagement_rate,
                    sentiment=sentiment_result.get('sentiment', 'neutral'),
                    sentiment_score=sentiment_result.get('score', 50),
                    importance=msg.get('importance', 'medium'),
                    hashtags=msg.get('hashtags', []),
                    keywords=sentiment_result.get('keywords', []),
                    mentioned_stocks=msg.get('mentioned_stocks', [])
                )

                db.add(record)
                stats["saved"] += 1

            except Exception as e:
                self.logger.error(f"保存社媒消息失败: {e}")
                stats["skipped"] += 1

        try:
            db.commit()
            self.logger.info(f"📱 社媒消息保存完成: 保存={stats['saved']}, 重复={stats['duplicate']}")
        except Exception as e:
            db.rollback()
            self.logger.error(f"提交社媒数据失败: {e}")
            raise

        return stats

    def query_messages(
        self,
        db: Session,
        params: SocialMediaQueryParams
    ) -> List[Dict[str, Any]]:
        """
        查询社媒消息

        Args:
            db: 数据库会话
            params: 查询参数

        Returns:
            消息列表
        """
        from sqlalchemy import desc as sql_desc, or_

        query = db.query(SocialMediaMessage)

        # 构建查询条件
        if params.symbol:
            query = query.filter(SocialMediaMessage.ts_code == params.symbol)
        elif params.symbols:
            query = query.filter(SocialMediaMessage.ts_code.in_(params.symbols))

        if params.platform:
            query = query.filter(SocialMediaMessage.platform == params.platform)
        if params.message_type:
            query = query.filter(SocialMediaMessage.message_type == params.message_type)

        if params.start_time:
            query = query.filter(SocialMediaMessage.publish_time >= params.start_time)
        if params.end_time:
            query = query.filter(SocialMediaMessage.publish_time <= params.end_time)

        if params.sentiment:
            query = query.filter(SocialMediaMessage.sentiment == params.sentiment)
        if params.importance:
            query = query.filter(SocialMediaMessage.importance == params.importance)

        if params.min_influence_score:
            query = query.filter(SocialMediaMessage.influence_score >= params.min_influence_score)
        if params.min_engagement_rate:
            query = query.filter(SocialMediaMessage.engagement_rate >= params.min_engagement_rate)

        if params.verified_only:
            query = query.filter(SocialMediaMessage.author_verified == 1)

        # 关键词搜索
        if params.keywords:
            keyword_filters = []
            for keyword in params.keywords:
                keyword_filters.append(SocialMediaMessage.content.like(f"%{keyword}%"))
                keyword_filters.append(SocialMediaMessage.title.like(f"%{keyword}%"))
            query = query.filter(or_(*keyword_filters))

        # 排序
        if params.sort_by == "publish_time":
            order_col = SocialMediaMessage.publish_time
        elif params.sort_by == "influence_score":
            order_col = SocialMediaMessage.influence_score
        elif params.sort_by == "engagement_rate":
            order_col = SocialMediaMessage.engagement_rate
        elif params.sort_by == "likes":
            order_col = SocialMediaMessage.likes
        else:
            order_col = SocialMediaMessage.publish_time

        if params.sort_order == "desc":
            query = query.order_by(sql_desc(order_col))
        else:
            query = query.order_by(order_col)

        # 分页
        query = query.offset(params.skip).limit(params.limit)

        results = query.all()
        return [record.to_dict() for record in results]

    def get_latest_messages(
        self,
        db: Session,
        ts_code: Optional[str] = None,
        platform: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """获取最新社媒消息"""
        params = SocialMediaQueryParams(
            symbol=ts_code,
            platform=platform,
            limit=limit,
            sort_by="publish_time",
            sort_order="desc"
        )
        return self.query_messages(db, params)

    def get_statistics(
        self,
        db: Session,
        ts_code: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> SocialMediaStats:
        """
        获取社媒消息统计信息

        Args:
            db: 数据库会话
            ts_code: 股票代码
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            统计信息
        """
        query = db.query(SocialMediaMessage)

        if ts_code:
            query = query.filter(SocialMediaMessage.ts_code == ts_code)
        if start_time:
            query = query.filter(SocialMediaMessage.publish_time >= start_time)
        if end_time:
            query = query.filter(SocialMediaMessage.publish_time <= end_time)

        records = query.all()

        if not records:
            return SocialMediaStats()

        stats = SocialMediaStats()
        stats.total_count = len(records)

        engagement_rates = []
        hashtag_counts = {}

        for record in records:
            # 情绪统计
            if record.sentiment == 'positive':
                stats.positive_count += 1
            elif record.sentiment == 'negative':
                stats.negative_count += 1
            else:
                stats.neutral_count += 1

            # 平台统计
            platform = record.platform or 'unknown'
            stats.platforms[platform] = stats.platforms.get(platform, 0) + 1

            # 消息类型统计
            msg_type = record.message_type or 'post'
            stats.message_types[msg_type] = stats.message_types.get(msg_type, 0) + 1

            # 互动数据汇总
            stats.total_views += record.views or 0
            stats.total_likes += record.likes or 0
            stats.total_shares += record.shares or 0
            stats.total_comments += record.comments or 0

            if record.engagement_rate:
                engagement_rates.append(record.engagement_rate)

            # 话题标签统计
            if record.hashtags:
                for tag in record.hashtags:
                    hashtag_counts[tag] = hashtag_counts.get(tag, 0) + 1

        # 计算平均互动率
        if engagement_rates:
            stats.avg_engagement_rate = sum(engagement_rates) / len(engagement_rates)

        # 热门话题标签
        sorted_hashtags = sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)
        stats.top_hashtags = [{'tag': tag, 'count': count} for tag, count in sorted_hashtags[:10]]

        # 情绪趋势
        if stats.positive_count > stats.negative_count * 1.5:
            stats.sentiment_trend = "bullish"
        elif stats.negative_count > stats.positive_count * 1.5:
            stats.sentiment_trend = "bearish"
        else:
            stats.sentiment_trend = "neutral"

        return stats

    def get_hot_topics(
        self,
        db: Session,
        platform: Optional[str] = None,
        hours_back: int = 24,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        获取热门话题

        Args:
            db: 数据库会话
            platform: 平台
            hours_back: 时间范围（小时）
            limit: 返回数量

        Returns:
            热门话题列表
        """
        from sqlalchemy import desc as sql_desc

        start_time = datetime.utcnow() - timedelta(hours=hours_back)

        query = db.query(SocialMediaMessage).filter(
            SocialMediaMessage.publish_time >= start_time
        )

        if platform:
            query = query.filter(SocialMediaMessage.platform == platform)

        # 按互动量排序
        query = query.order_by(sql_desc(SocialMediaMessage.likes + SocialMediaMessage.shares + SocialMediaMessage.comments))
        query = query.limit(limit)

        results = query.all()
        return [record.to_dict() for record in results]

    def delete_old_messages(
        self,
        db: Session,
        days_to_keep: int = 30
    ) -> int:
        """删除过期消息"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        deleted_count = db.query(SocialMediaMessage).filter(
            SocialMediaMessage.created_at < cutoff_date
        ).delete()

        db.commit()
        self.logger.info(f"🗑️ 删除过期社媒消息: {deleted_count}条")

        return deleted_count


# 全局服务实例
_social_media_service = None


def get_social_media_service() -> SocialMediaService:
    """获取社交媒体服务实例"""
    global _social_media_service
    if _social_media_service is None:
        _social_media_service = SocialMediaService()
        logger.info("✅ 社交媒体服务初始化成功")
    return _social_media_service
