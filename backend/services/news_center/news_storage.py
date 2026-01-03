# -*- coding: utf-8 -*-
"""
新闻数据库存储层
提供新闻的持久化存储和查询功能
"""

import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import desc, and_, or_
from sqlalchemy.exc import IntegrityError

from backend.database.database import get_db_context
from backend.database.models import MarketNews
from backend.utils.logging_config import get_logger

logger = get_logger("news_storage")


def generate_news_id(title: str, source: str, pub_time: Optional[datetime] = None) -> str:
    """
    生成新闻唯一ID
    使用标题+来源+发布时间的hash
    """
    time_str = pub_time.isoformat() if pub_time else ""
    content = f"{title}|{source}|{time_str}"
    return hashlib.md5(content.encode('utf-8')).hexdigest()


class NewsStorage:
    """新闻存储服务"""

    def save_news(self, news_item: Dict[str, Any]) -> bool:
        """
        保存单条新闻到数据库
        如果已存在则跳过（去重）

        Args:
            news_item: 新闻数据字典

        Returns:
            True=新增成功, False=已存在或失败
        """
        try:
            # 解析发布时间
            pub_time = None
            pub_time_str = news_item.get('pub_time') or news_item.get('publish_time') or news_item.get('time')
            if pub_time_str:
                if isinstance(pub_time_str, datetime):
                    pub_time = pub_time_str
                elif isinstance(pub_time_str, str):
                    # 尝试多种时间格式
                    for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d', '%Y/%m/%d %H:%M:%S']:
                        try:
                            pub_time = datetime.strptime(pub_time_str, fmt)
                            break
                        except ValueError:
                            continue

            title = news_item.get('title', '')
            source = news_item.get('source', 'unknown')

            # 生成唯一ID
            news_id = generate_news_id(title, source, pub_time)

            with get_db_context() as db:
                # 检查是否已存在
                existing = db.query(MarketNews).filter(MarketNews.news_id == news_id).first()
                if existing:
                    return False  # 已存在

                # 创建新记录
                news = MarketNews(
                    news_id=news_id,
                    title=title,
                    content=news_item.get('content'),
                    summary=news_item.get('summary') or (news_item.get('content', '')[:200] if news_item.get('content') else None),
                    source=source,
                    source_type=news_item.get('source_type') or news_item.get('type', 'market'),
                    source_url=news_item.get('url') or news_item.get('source_url'),
                    stock_code=news_item.get('stock_code') or news_item.get('code'),
                    stock_name=news_item.get('stock_name') or news_item.get('name'),
                    pub_time=pub_time,
                    fetch_time=datetime.now(),
                    sentiment=news_item.get('sentiment'),
                    sentiment_score=news_item.get('sentiment_score'),
                    category=news_item.get('category'),
                    keywords=news_item.get('keywords'),
                    extra_data=news_item.get('extra_data')
                )
                db.add(news)
                return True

        except IntegrityError:
            # 唯一约束冲突，说明已存在
            return False
        except Exception as e:
            logger.error(f"保存新闻失败: {e}")
            return False

    def save_news_batch(self, news_list: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        批量保存新闻

        Args:
            news_list: 新闻列表

        Returns:
            {"saved": 新增数量, "skipped": 跳过数量, "failed": 失败数量}
        """
        result = {"saved": 0, "skipped": 0, "failed": 0}

        for news_item in news_list:
            try:
                if self.save_news(news_item):
                    result["saved"] += 1
                else:
                    result["skipped"] += 1
            except Exception as e:
                logger.error(f"批量保存新闻失败: {e}")
                result["failed"] += 1

        if result["saved"] > 0:
            logger.info(f"批量保存新闻: 新增{result['saved']}条, 跳过{result['skipped']}条, 失败{result['failed']}条")

        return result

    def get_market_news(
        self,
        limit: int = 100,
        offset: int = 0,
        source: Optional[str] = None,
        sentiment: Optional[str] = None,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        获取市场新闻

        Args:
            limit: 返回数量
            offset: 偏移量
            source: 数据源筛选
            sentiment: 情绪筛选
            hours: 获取最近N小时的新闻

        Returns:
            新闻列表
        """
        try:
            with get_db_context() as db:
                query = db.query(MarketNews)

                # 时间筛选
                if hours > 0:
                    since = datetime.now() - timedelta(hours=hours)
                    query = query.filter(MarketNews.created_at >= since)

                # 来源筛选
                if source:
                    query = query.filter(MarketNews.source == source)

                # 情绪筛选
                if sentiment:
                    query = query.filter(MarketNews.sentiment == sentiment)

                # 排序和分页
                query = query.order_by(desc(MarketNews.pub_time), desc(MarketNews.created_at))
                query = query.offset(offset).limit(limit)

                news_list = query.all()
                return [n.to_dict() for n in news_list]

        except Exception as e:
            logger.error(f"获取市场新闻失败: {e}")
            return []

    def get_stock_news(
        self,
        stock_code: str,
        limit: int = 50,
        hours: int = 72
    ) -> List[Dict[str, Any]]:
        """
        获取个股新闻

        Args:
            stock_code: 股票代码
            limit: 返回数量
            hours: 获取最近N小时的新闻

        Returns:
            新闻列表
        """
        try:
            # 标准化股票代码（去掉后缀）
            code = stock_code.split('.')[0] if '.' in stock_code else stock_code

            with get_db_context() as db:
                query = db.query(MarketNews)

                # 股票代码筛选（模糊匹配）
                query = query.filter(
                    or_(
                        MarketNews.stock_code == code,
                        MarketNews.stock_code == stock_code,
                        MarketNews.stock_code.like(f"{code}%")
                    )
                )

                # 时间筛选
                if hours > 0:
                    since = datetime.now() - timedelta(hours=hours)
                    query = query.filter(MarketNews.created_at >= since)

                # 排序和分页
                query = query.order_by(desc(MarketNews.pub_time), desc(MarketNews.created_at))
                query = query.limit(limit)

                news_list = query.all()
                return [n.to_dict() for n in news_list]

        except Exception as e:
            logger.error(f"获取个股新闻失败: {e}")
            return []

    def search_news(
        self,
        keyword: str,
        limit: int = 50,
        hours: int = 72
    ) -> List[Dict[str, Any]]:
        """
        搜索新闻

        Args:
            keyword: 搜索关键词
            limit: 返回数量
            hours: 搜索最近N小时的新闻

        Returns:
            新闻列表
        """
        try:
            with get_db_context() as db:
                query = db.query(MarketNews)

                # 关键词搜索（标题和内容）
                query = query.filter(
                    or_(
                        MarketNews.title.like(f"%{keyword}%"),
                        MarketNews.content.like(f"%{keyword}%"),
                        MarketNews.stock_code.like(f"%{keyword}%"),
                        MarketNews.stock_name.like(f"%{keyword}%")
                    )
                )

                # 时间筛选
                if hours > 0:
                    since = datetime.now() - timedelta(hours=hours)
                    query = query.filter(MarketNews.created_at >= since)

                # 排序和分页
                query = query.order_by(desc(MarketNews.pub_time), desc(MarketNews.created_at))
                query = query.limit(limit)

                news_list = query.all()
                return [n.to_dict() for n in news_list]

        except Exception as e:
            logger.error(f"搜索新闻失败: {e}")
            return []

    def get_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """
        获取新闻统计数据

        Args:
            hours: 统计最近N小时的数据

        Returns:
            统计数据
        """
        try:
            with get_db_context() as db:
                since = datetime.now() - timedelta(hours=hours)

                # 总数
                total = db.query(MarketNews).filter(MarketNews.created_at >= since).count()

                # 按来源统计
                from sqlalchemy import func
                source_stats = db.query(
                    MarketNews.source,
                    func.count(MarketNews.id)
                ).filter(
                    MarketNews.created_at >= since
                ).group_by(MarketNews.source).all()

                # 按情绪统计
                sentiment_stats = db.query(
                    MarketNews.sentiment,
                    func.count(MarketNews.id)
                ).filter(
                    MarketNews.created_at >= since
                ).group_by(MarketNews.sentiment).all()

                return {
                    "total": total,
                    "hours": hours,
                    "by_source": {s[0]: s[1] for s in source_stats if s[0]},
                    "by_sentiment": {
                        "positive": next((s[1] for s in sentiment_stats if s[0] == 'positive'), 0),
                        "negative": next((s[1] for s in sentiment_stats if s[0] == 'negative'), 0),
                        "neutral": next((s[1] for s in sentiment_stats if s[0] == 'neutral'), 0)
                    }
                }

        except Exception as e:
            logger.error(f"获取新闻统计失败: {e}")
            return {"total": 0, "hours": hours, "by_source": {}, "by_sentiment": {}}

    def cleanup_old_news(self, days: int = 30) -> int:
        """
        清理旧新闻

        Args:
            days: 保留最近N天的新闻

        Returns:
            删除的记录数
        """
        try:
            with get_db_context() as db:
                cutoff = datetime.now() - timedelta(days=days)
                deleted = db.query(MarketNews).filter(MarketNews.created_at < cutoff).delete()
                logger.info(f"清理旧新闻: 删除{deleted}条（{days}天前）")
                return deleted

        except Exception as e:
            logger.error(f"清理旧新闻失败: {e}")
            return 0


# 单例
_news_storage: Optional[NewsStorage] = None


def get_news_storage() -> NewsStorage:
    """获取新闻存储服务单例"""
    global _news_storage
    if _news_storage is None:
        _news_storage = NewsStorage()
    return _news_storage
