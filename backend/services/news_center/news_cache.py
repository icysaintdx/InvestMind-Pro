# -*- coding: utf-8 -*-
import hashlib
import json
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class NewsUrgency(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class CachedNews:
    news_id: str
    title: str
    content: str = ""
    summary: str = ""
    source: str = ""
    url: str = ""
    pub_time: str = ""
    fetch_time: str = ""
    sentiment: str = "neutral"
    sentiment_score: float = 50.0
    urgency: str = "low"
    report_type: str = "news"
    keywords: List[str] = field(default_factory=list)
    related_stocks: List[str] = field(default_factory=list)
    impact_score: float = 0.0
    is_pushed: bool = False
    push_time: str = ""
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

class NewsCache:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._cache = {}
        self._cache_lock = threading.RLock()
        self._fingerprints = set()
        self._ttl_config = {NewsUrgency.CRITICAL: 1440, NewsUrgency.HIGH: 720, NewsUrgency.MEDIUM: 360, NewsUrgency.LOW: 180}  # 分钟: 24h, 12h, 6h, 3h
        self._expiry = {}
        self._cache_dir = Path("data/news_center_cache")
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._stats = {"total_added": 0, "duplicates_skipped": 0, "expired_cleaned": 0}
        self._load_file_cache()
    
    def generate_fingerprint(self, title, pub_time=""):
        return hashlib.md5(f"{title.strip().lower()}_{pub_time}".encode()).hexdigest()
    
    def add_news(self, news):
        with self._cache_lock:
            if news.news_id in self._fingerprints:
                self._stats["duplicates_skipped"] += 1
                return False
            self._cache[news.news_id] = news
            self._fingerprints.add(news.news_id)
            urgency = NewsUrgency(news.urgency) if news.urgency in [e.value for e in NewsUrgency] else NewsUrgency.LOW
            self._expiry[news.news_id] = datetime.now() + timedelta(minutes=self._ttl_config.get(urgency, 30))
            self._stats["total_added"] += 1
            return True
    
    def add_news_batch(self, news_list):
        added, skipped = 0, 0
        for nd in news_list:
            try:
                title = nd.get("title", nd.get("新闻标题", ""))
                pub_time = nd.get("pub_time", nd.get("发布时间", ""))
                if not title:
                    skipped += 1
                    continue
                news = CachedNews(
                    news_id=self.generate_fingerprint(title, pub_time), title=title,
                    content=str(nd.get("content", ""))[:2000],
                    source=nd.get("source", ""), url=nd.get("url", ""),
                    pub_time=str(pub_time), fetch_time=datetime.now().isoformat(),
                    sentiment=nd.get("sentiment", "neutral"),
                    sentiment_score=float(nd.get("sentiment_score", 50.0)),
                    urgency=nd.get("urgency", "low"),
                    keywords=nd.get("keywords", []),
                    related_stocks=nd.get("related_stocks", []),
                    impact_score=float(nd.get("impact_score", 0.0))
                )
                if self.add_news(news):
                    added += 1
                else:
                    skipped += 1
            except:
                skipped += 1
        return {"added": added, "skipped": skipped}
    
    def get_latest_news(self, limit=0, urgency=None, source=None, stock_code=None, unpushed_only=False):
        with self._cache_lock:
            news_list = list(self._cache.values())
        if urgency:
            news_list = [n for n in news_list if n.urgency == urgency]
        if source:
            news_list = [n for n in news_list if source.lower() in n.source.lower()]
        if stock_code:
            news_list = [n for n in news_list if stock_code in n.related_stocks]
        if unpushed_only:
            news_list = [n for n in news_list if not n.is_pushed]
        news_list.sort(key=lambda x: x.fetch_time, reverse=True)
        return news_list if limit <= 0 else news_list[:limit]
    
    def get_urgent_news(self, limit=20):
        with self._cache_lock:
            urgent = [n for n in self._cache.values() if n.urgency in ["critical", "high"]]
        urgent.sort(key=lambda x: x.fetch_time, reverse=True)
        return urgent[:limit]

    def get_news_for_stock(self, stock_code: str, limit: int = 30):
        """获取与指定股票相关的新闻"""
        with self._cache_lock:
            # 标准化股票代码（去掉后缀）
            code_base = stock_code.split('.')[0] if '.' in stock_code else stock_code
            related = [n for n in self._cache.values()
                      if code_base in n.related_stocks or
                      any(code_base in s for s in n.related_stocks) or
                      code_base in n.title or
                      code_base in n.content]
        related.sort(key=lambda x: x.fetch_time, reverse=True)
        return related[:limit]
    
    def is_duplicate(self, title, pub_time=""):
        return self.generate_fingerprint(title, pub_time) in self._fingerprints
    
    def cleanup_expired(self):
        now = datetime.now()
        expired = [nid for nid, exp in list(self._expiry.items()) if now > exp]
        with self._cache_lock:
            for nid in expired:
                self._cache.pop(nid, None)
                self._fingerprints.discard(nid)
                self._expiry.pop(nid, None)
            self._stats["expired_cleaned"] += len(expired)
        return len(expired)
    
    def get_stats(self):
        with self._cache_lock:
            return {**self._stats, "current_size": len(self._cache)}
    
    def save_to_file(self):
        try:
            with self._cache_lock:
                data = {"news": [n.to_dict() for n in self._cache.values()], "expiry": {k: v.isoformat() for k, v in self._expiry.items()}}
            with open(self._cache_dir / "news_cache.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Save failed: {e}")
    
    def _load_file_cache(self):
        try:
            cache_file = self._cache_dir / "news_cache.json"
            if not cache_file.exists():
                return
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            for nd in data.get("news", []):
                try:
                    news = CachedNews.from_dict(nd)
                    self._cache[news.news_id] = news
                    self._fingerprints.add(news.news_id)
                except:
                    pass
            for nid, exp_str in data.get("expiry", {}).items():
                try:
                    self._expiry[nid] = datetime.fromisoformat(exp_str)
                except:
                    pass
            self.cleanup_expired()
        except:
            pass
    
    def clear(self):
        with self._cache_lock:
            self._cache.clear()
            self._fingerprints.clear()
            self._expiry.clear()

_news_cache = None
def get_news_cache():
    global _news_cache
    if _news_cache is None:
        _news_cache = NewsCache()
    return _news_cache
