from __future__ import annotations

from datetime import datetime
from typing import Dict, Iterable

from backend.services.news_center.news_storage import save_news_article


def normalize_item(item: Dict) -> Dict:
    publish_time = item.get("publish_time")
    if isinstance(publish_time, datetime):
        publish_time = publish_time.isoformat(timespec="seconds")
    elif not publish_time:
        publish_time = datetime.now().isoformat(timespec="seconds")

    title = (item.get("title") or "").strip()
    content = (item.get("content") or "").strip() or title

    return {
        "title": title,
        "content": content,
        "source": item.get("source", "realtime_flash"),
        "source_key": item.get("source_key", "realtime_flash"),
        "publish_time": publish_time,
        "priority": item.get("priority", "P2"),
        "category": item.get("category", "market_flash"),
        "sub_category": item.get("sub_category", "realtime"),
        "sentiment": item.get("sentiment", "neutral"),
        "sentiment_score": item.get("sentiment_score", 0.0),
        "expected_return": item.get("expected_return", 0.0),
        "urgency_score": item.get("urgency_score", 50.0),
        "impact_score": item.get("impact_score", 50.0),
        "keywords": item.get("keywords", []),
        "related_stocks": item.get("related_stocks", []),
        "url": item.get("url", ""),
    }


def write_items(items: Iterable[Dict]) -> Dict[str, int]:
    stats = {"received": 0, "written": 0, "duplicated": 0, "invalid": 0}
    for item in items:
        stats["received"] += 1
        normalized = normalize_item(item)
        if not normalized["title"]:
            stats["invalid"] += 1
            continue
        ok = save_news_article(normalized)
        if ok:
            stats["written"] += 1
        else:
            stats["duplicated"] += 1
    return stats
