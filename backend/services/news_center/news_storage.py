# -*- coding: utf-8 -*-
"""
新闻数据存储服务
负责新闻的持久化存储和查询

Author: 臭宝
Date: 2026-02-19
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
import threading

logger = logging.getLogger(__name__)


@dataclass
class NewsArticle:
    """新闻文章数据模型"""
    id: Optional[int] = None
    title: str = ""
    content: str = ""
    source: str = ""  # 新闻来源：财联社/东方财富等
    source_key: str = ""  # 来源标识
    publish_time: str = ""  # 发布时间
    crawl_time: str = ""  # 抓取时间
    
    # 优先级分类
    priority: str = "P2"  # P0/P1/P2
    category: str = "general"  # 类别：业绩/政策/龙虎榜等
    sub_category: str = ""  # 子类别
    
    # 情绪分析
    sentiment: str = "neutral"  # positive/negative/neutral
    sentiment_score: float = 0.0  # -1.0 ~ 1.0
    
    # 影响评估
    expected_return: float = 0.0  # 预期收益率
    urgency_score: float = 0.0  # 紧急程度 0-100
    impact_score: float = 0.0  # 影响分数
    
    # 关键词和关联
    keywords: str = ""  # JSON字符串存储关键词列表
    related_stocks: str = ""  # JSON字符串存储关联股票列表
    
    # 原始数据
    url: str = ""
    raw_data: str = ""  # 原始JSON数据
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NewsArticle':
        """从字典创建"""
        return cls(**data)


class NewsStorage:
    """
    新闻数据存储服务
    
    使用SQLite存储，后期可迁移到PostgreSQL
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化存储服务
        
        Args:
            db_path: 数据库文件路径，默认使用项目目录下的news_database.db
        """
        if db_path is None:
            # 默认路径：项目根目录下的data文件夹
            base_dir = Path(__file__).parent.parent.parent.parent
            data_dir = base_dir / "data" / "news_storage"
            data_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(data_dir / "news_database.db")
        else:
            self.db_path = db_path
        
        self._lock = threading.Lock()
        self._init_database()
        logger.info(f"NewsStorage initialized with database: {self.db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_database(self):
        """初始化数据库表结构"""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 新闻主表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS news_articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT,
                    source TEXT,
                    source_key TEXT,
                    publish_time TEXT,
                    crawl_time TEXT DEFAULT CURRENT_TIMESTAMP,
                    priority TEXT DEFAULT 'P2',
                    category TEXT DEFAULT 'general',
                    sub_category TEXT,
                    sentiment TEXT DEFAULT 'neutral',
                    sentiment_score REAL DEFAULT 0.0,
                    expected_return REAL DEFAULT 0.0,
                    urgency_score REAL DEFAULT 0.0,
                    impact_score REAL DEFAULT 0.0,
                    keywords TEXT,
                    related_stocks TEXT,
                    url TEXT,
                    raw_data TEXT,
                    UNIQUE(title, publish_time)
                )
            """)
            
            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_news_priority 
                ON news_articles(priority)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_news_publish_time 
                ON news_articles(publish_time)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_news_category 
                ON news_articles(category)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_news_sentiment 
                ON news_articles(sentiment)
            """)
            
            # 每日统计表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS news_daily_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT UNIQUE,
                    total_count INTEGER DEFAULT 0,
                    p0_count INTEGER DEFAULT 0,
                    p1_count INTEGER DEFAULT 0,
                    p2_count INTEGER DEFAULT 0,
                    positive_count INTEGER DEFAULT 0,
                    negative_count INTEGER DEFAULT 0,
                    neutral_count INTEGER DEFAULT 0,
                    avg_sentiment REAL DEFAULT 0.0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info("Database tables initialized")
    
    def save_news(self, article: NewsArticle) -> bool:
        """
        保存单条新闻
        
        Args:
            article: 新闻文章对象
            
        Returns:
            是否保存成功（重复返回False）
        """
        try:
            with self._lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                # 检查是否已存在（根据标题和发布时间去重）
                cursor.execute(
                    "SELECT id FROM news_articles WHERE title = ? AND publish_time = ?",
                    (article.title, article.publish_time)
                )
                if cursor.fetchone():
                    logger.debug(f"News already exists: {article.title[:50]}...")
                    conn.close()
                    return False
                
                # 插入数据
                cursor.execute("""
                    INSERT INTO news_articles (
                        title, content, source, source_key, publish_time, crawl_time,
                        priority, category, sub_category, sentiment, sentiment_score,
                        expected_return, urgency_score, impact_score, keywords,
                        related_stocks, url, raw_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    article.title,
                    article.content,
                    article.source,
                    article.source_key,
                    article.publish_time,
                    article.crawl_time or datetime.now().isoformat(),
                    article.priority,
                    article.category,
                    article.sub_category,
                    article.sentiment,
                    article.sentiment_score,
                    article.expected_return,
                    article.urgency_score,
                    article.impact_score,
                    article.keywords,
                    article.related_stocks,
                    article.url,
                    article.raw_data
                ))
                
                conn.commit()
                article.id = cursor.lastrowid
                conn.close()
                
                logger.info(f"Saved news: {article.title[:50]}... (ID: {article.id})")
                return True
                
        except Exception as e:
            logger.error(f"Failed to save news: {e}")
            return False
    
    def save_news_batch(self, articles: List[NewsArticle]) -> Dict[str, int]:
        """
        批量保存新闻
        
        Args:
            articles: 新闻文章列表
            
        Returns:
            统计结果：{saved: x, duplicated: y}
        """
        saved = 0
        duplicated = 0
        
        for article in articles:
            if self.save_news(article):
                saved += 1
            else:
                duplicated += 1
        
        logger.info(f"Batch save: {saved} saved, {duplicated} duplicated")
        return {"saved": saved, "duplicated": duplicated}
    
    def get_news_by_date(
        self, 
        date: str, 
        priority: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[NewsArticle]:
        """
        按日期获取新闻
        
        Args:
            date: 日期，格式 YYYY-MM-DD
            priority: 优先级筛选（P0/P1/P2）
            category: 类别筛选
            limit: 返回数量限制
            
        Returns:
            新闻列表
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT * FROM news_articles 
                WHERE date(publish_time) = ?
            """
            params = [date]
            
            if priority:
                query += " AND priority = ?"
                params.append(priority)
            
            if category:
                query += " AND category = ?"
                params.append(category)
            
            query += " ORDER BY publish_time DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            articles = []
            for row in rows:
                article = NewsArticle(
                    id=row['id'],
                    title=row['title'],
                    content=row['content'],
                    source=row['source'],
                    source_key=row['source_key'],
                    publish_time=row['publish_time'],
                    crawl_time=row['crawl_time'],
                    priority=row['priority'],
                    category=row['category'],
                    sub_category=row['sub_category'],
                    sentiment=row['sentiment'],
                    sentiment_score=row['sentiment_score'],
                    expected_return=row['expected_return'],
                    urgency_score=row['urgency_score'],
                    impact_score=row['impact_score'],
                    keywords=row['keywords'],
                    related_stocks=row['related_stocks'],
                    url=row['url'],
                    raw_data=row['raw_data']
                )
                articles.append(article)
            
            return articles
            
        except Exception as e:
            logger.error(f"Failed to get news by date: {e}")
            return []
    
    def get_news_by_stock(
        self, 
        stock_code: str, 
        days: int = 7,
        limit: int = 100
    ) -> List[NewsArticle]:
        """
        获取与特定股票相关的新闻
        
        Args:
            stock_code: 股票代码
            days: 最近多少天
            limit: 返回数量限制
            
        Returns:
            新闻列表
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            cursor.execute("""
                SELECT * FROM news_articles 
                WHERE date(publish_time) >= ?
                AND related_stocks LIKE ?
                ORDER BY publish_time DESC
                LIMIT ?
            """, (start_date, f'%"{stock_code}"%', limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            articles = []
            for row in rows:
                article = NewsArticle(
                    id=row['id'],
                    title=row['title'],
                    content=row['content'],
                    source=row['source'],
                    source_key=row['source_key'],
                    publish_time=row['publish_time'],
                    crawl_time=row['crawl_time'],
                    priority=row['priority'],
                    category=row['category'],
                    sub_category=row['sub_category'],
                    sentiment=row['sentiment'],
                    sentiment_score=row['sentiment_score'],
                    expected_return=row['expected_return'],
                    urgency_score=row['urgency_score'],
                    impact_score=row['impact_score'],
                    keywords=row['keywords'],
                    related_stocks=row['related_stocks'],
                    url=row['url'],
                    raw_data=row['raw_data']
                )
                articles.append(article)
            
            return articles
            
        except Exception as e:
            logger.error(f"Failed to get news by stock: {e}")
            return []
    
    def get_latest_news(
        self, 
        hours: int = 24, 
        priority: Optional[str] = None,
        limit: int = 50
    ) -> List[NewsArticle]:
        """
        获取最近的新闻
        
        Args:
            hours: 最近多少小时
            priority: 优先级筛选
            limit: 返回数量限制
            
        Returns:
            新闻列表
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            start_time = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            query = """
                SELECT * FROM news_articles 
                WHERE publish_time >= ?
            """
            params = [start_time]
            
            if priority:
                query += " AND priority = ?"
                params.append(priority)
            
            query += " ORDER BY publish_time DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            articles = []
            for row in rows:
                article = NewsArticle(
                    id=row['id'],
                    title=row['title'],
                    content=row['content'],
                    source=row['source'],
                    source_key=row['source_key'],
                    publish_time=row['publish_time'],
                    crawl_time=row['crawl_time'],
                    priority=row['priority'],
                    category=row['category'],
                    sub_category=row['sub_category'],
                    sentiment=row['sentiment'],
                    sentiment_score=row['sentiment_score'],
                    expected_return=row['expected_return'],
                    urgency_score=row['urgency_score'],
                    impact_score=row['impact_score'],
                    keywords=row['keywords'],
                    related_stocks=row['related_stocks'],
                    url=row['url'],
                    raw_data=row['raw_data']
                )
                articles.append(article)
            
            return articles
            
        except Exception as e:
            logger.error(f"Failed to get latest news: {e}")
            return []
    
    def get_stats_by_date(self, date: str) -> Dict[str, Any]:
        """
        获取指定日期的新闻统计
        
        Args:
            date: 日期，格式 YYYY-MM-DD
            
        Returns:
            统计信息字典
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN priority = 'P0' THEN 1 ELSE 0 END) as p0_count,
                    SUM(CASE WHEN priority = 'P1' THEN 1 ELSE 0 END) as p1_count,
                    SUM(CASE WHEN priority = 'P2' THEN 1 ELSE 0 END) as p2_count,
                    SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) as positive_count,
                    SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) as negative_count,
                    SUM(CASE WHEN sentiment = 'neutral' THEN 1 ELSE 0 END) as neutral_count,
                    AVG(sentiment_score) as avg_sentiment
                FROM news_articles 
                WHERE date(publish_time) = ?
            """, (date,))
            
            row = cursor.fetchone()
            conn.close()
            
            return {
                "date": date,
                "total": row['total'] or 0,
                "p0_count": row['p0_count'] or 0,
                "p1_count": row['p1_count'] or 0,
                "p2_count": row['p2_count'] or 0,
                "positive_count": row['positive_count'] or 0,
                "negative_count": row['negative_count'] or 0,
                "neutral_count": row['neutral_count'] or 0,
                "avg_sentiment": round(row['avg_sentiment'] or 0, 4)
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}
    
    def delete_old_news(self, days: int = 90) -> int:
        """
        删除过期新闻
        
        Args:
            days: 保留最近多少天的新闻
            
        Returns:
            删除的新闻数量
        """
        try:
            with self._lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
                
                cursor.execute(
                    "DELETE FROM news_articles WHERE date(publish_time) < ?",
                    (cutoff_date,)
                )
                
                deleted = cursor.rowcount
                conn.commit()
                conn.close()
                
                logger.info(f"Deleted {deleted} old news (before {cutoff_date})")
                return deleted
                
        except Exception as e:
            logger.error(f"Failed to delete old news: {e}")
            return 0


# 全局实例
_news_storage = None

def get_news_storage() -> NewsStorage:
    """获取新闻存储服务实例（单例）"""
    global _news_storage
    if _news_storage is None:
        _news_storage = NewsStorage()
    return _news_storage


# 便捷函数
def save_news_article(news_data: Dict[str, Any]) -> bool:
    """便捷函数：保存新闻数据字典"""
    article = NewsArticle(
        title=news_data.get('title', ''),
        content=news_data.get('content', ''),
        source=news_data.get('source', ''),
        source_key=news_data.get('source_key', ''),
        publish_time=news_data.get('publish_time', ''),
        priority=news_data.get('priority', 'P2'),
        category=news_data.get('category', 'general'),
        sub_category=news_data.get('sub_category', ''),
        sentiment=news_data.get('sentiment', 'neutral'),
        sentiment_score=news_data.get('sentiment_score', 0.0),
        expected_return=news_data.get('expected_return', 0.0),
        urgency_score=news_data.get('urgency_score', 0.0),
        impact_score=news_data.get('impact_score', 0.0),
        keywords=json.dumps(news_data.get('keywords', [])),
        related_stocks=json.dumps(news_data.get('related_stocks', [])),
        url=news_data.get('url', ''),
        raw_data=json.dumps(news_data)
    )
    return get_news_storage().save_news(article)


# 测试代码
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    storage = NewsStorage()
    
    # 测试保存
    test_news = NewsArticle(
        title="测试新闻：贵州茅台业绩预增50%",
        content="贵州茅台发布业绩预告...",
        source="东方财富",
        source_key="eastmoney",
        publish_time=datetime.now().isoformat(),
        priority="P0",
        category="业绩",
        sub_category="high_positive",
        sentiment="positive",
        sentiment_score=0.8,
        expected_return=8.0,
        urgency_score=95.0,
        keywords=json.dumps(["茅台", "业绩", "预增"]),
        related_stocks=json.dumps(["600519"])
    )
    
    result = storage.save_news(test_news)
    print(f"Save result: {result}")
    
    # 测试查询
    today = datetime.now().strftime('%Y-%m-%d')
    news_list = storage.get_news_by_date(today)
    print(f"Today's news count: {len(news_list)}")
    
    if news_list:
        print(f"Latest: {news_list[0].title}")
    
    # 测试统计
    stats = storage.get_stats_by_date(today)
    print(f"Stats: {stats}")
