# -*- coding: utf-8 -*-
"""
Realtime Flash API
提供金十(JIN10)+汇通(FX678)实时快讯的健康检查、拉取执行、统计与查询接口。
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.realtime_flash.runner import RealtimeFlashRunner, build_runner, load_settings
from backend.services.news_center.news_storage import get_news_storage


logger = logging.getLogger("realtime_flash.api")
router = APIRouter(prefix="/api/realtime-flash", tags=["RealtimeFlash"])


class RunOnceRequest(BaseModel):
    max_items: int = Field(default=20, ge=1, le=500)
    ws_wait_seconds: int = Field(default=4, ge=1, le=20)


class RealtimeFlashService:
    """Realtime Flash 运行协调器（单进程单例）。"""

    def __init__(self) -> None:
        self.runner: RealtimeFlashRunner = build_runner()
        self.last_run_at: Optional[str] = None
        self.last_result: Dict[str, Any] = {}
        self.last_error: str = ""
        self.last_degraded: bool = False
        self.last_degrade_reasons: List[str] = []

    def refresh_settings(self) -> None:
        # 每次执行前重建 runner，确保 .env 变更即时生效
        self.runner = build_runner()

    async def run_once(self, max_items: int, ws_wait_seconds: int) -> Dict[str, Any]:
        self.refresh_settings()
        self.last_run_at = datetime.now().isoformat(timespec="seconds")
        self.last_error = ""
        self.last_degraded = False
        self.last_degrade_reasons = []

        try:
            result = await self.runner.run_once(max_items=max_items, ws_wait_seconds=ws_wait_seconds)
            self.last_result = result
            # 降级识别：启用但 0 接收/0 写入，且存在外部错误
            source_errors = result.get("source_errors", {}) if isinstance(result, dict) else {}
            if result.get("received", 0) == 0 and result.get("written", 0) == 0 and source_errors:
                self.last_degraded = True
                for src, err in source_errors.items():
                    self.last_degrade_reasons.append(f"{src}: {err}")
            return result
        except Exception as exc:
            self.last_error = str(exc)
            self.last_degraded = True
            self.last_degrade_reasons = [self.last_error]
            logger.exception("run_once failed: %s", exc)
            raise

    def latest(self, limit: int, source: str = "all") -> List[Dict[str, Any]]:
        storage = get_news_storage()
        conn = storage._get_connection()  # 复用现有 storage 连接配置
        cursor = conn.cursor()

        where_sql = "WHERE source_key IN ('jin10','fx678')"
        params: List[Any] = []

        src = (source or "all").strip().lower()
        if src in {"jin10", "fx678"}:
            where_sql += " AND source_key = ?"
            params.append(src)

        params.append(limit)

        cursor.execute(
            f"""
            SELECT id, title, content, source, source_key, publish_time, crawl_time, url
            FROM news_articles
            {where_sql}
            ORDER BY publish_time DESC, id DESC
            LIMIT ?
            """,
            params,
        )
        rows = cursor.fetchall()
        conn.close()

        items: List[Dict[str, Any]] = []
        for row in rows:
            items.append(
                {
                    "id": row["id"],
                    "title": row["title"] or "",
                    "content": row["content"] or "",
                    "source": row["source"] or "",
                    "source_key": row["source_key"] or "",
                    "publish_time": row["publish_time"] or "",
                    "crawl_time": row["crawl_time"] or "",
                    "url": row["url"] or "",
                }
            )
        return items

    def stats(self) -> Dict[str, Any]:
        settings = load_settings()
        storage_stats = get_news_storage().get_statistics(hours=24)
        return {
            "module": {
                "enabled": settings.enabled,
                "ws_enabled": settings.ws_enabled,
                "fx678_enabled": settings.fx678_enabled,
                "log_level": settings.log_level,
                "dedup_ttl_seconds": settings.dedup_ttl_seconds,
                "dedup_cache_file": settings.dedup_cache_file,
                "writer_batch_size": settings.writer_batch_size,
                "fx678_poll_seconds": settings.fx678_poll_seconds,
            },
            "runner_stats": self.runner.stats,
            "last_run": {
                "at": self.last_run_at,
                "result": self.last_result,
                "error": self.last_error,
                "degraded": self.last_degraded,
                "degrade_reasons": self.last_degrade_reasons,
            },
            "news_storage_24h": storage_stats,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }


_service = RealtimeFlashService()


def _parse_iframe_yaml_fallback(content: str) -> Dict[str, Any]:
    """无 PyYAML 依赖时，解析当前固定结构 YAML。"""
    result: Dict[str, Any] = {
        "realtime_flash_iframe": {
            "enabled": True,
            "default_provider": "jin10",
            "refresh_seconds": 30,
            "providers": {},
        }
    }
    root = result["realtime_flash_iframe"]

    current_provider: Optional[str] = None
    in_providers = False

    for raw_line in content.splitlines():
        line = raw_line.rstrip()
        if not line or line.strip().startswith("#"):
            continue

        stripped = line.strip()
        if stripped.startswith("realtime_flash_iframe:"):
            continue
        if stripped.startswith("providers:"):
            in_providers = True
            current_provider = None
            continue

        if not in_providers:
            if stripped.startswith("enabled:"):
                root["enabled"] = stripped.split(":", 1)[1].strip().lower() == "true"
            elif stripped.startswith("default_provider:"):
                root["default_provider"] = stripped.split(":", 1)[1].strip().strip('"')
            elif stripped.startswith("refresh_seconds:"):
                try:
                    root["refresh_seconds"] = int(stripped.split(":", 1)[1].strip())
                except Exception:
                    pass
            continue

        # provider block key: "    jin10:"
        if line.startswith("    ") and stripped.endswith(":") and stripped[:-1] in {"jin10", "fx678"}:
            current_provider = stripped[:-1]
            root["providers"][current_provider] = {}
            continue

        if current_provider and line.startswith("      ") and ":" in stripped:
            k, v = stripped.split(":", 1)
            val = v.strip().strip('"')
            if val.lower() in {"true", "false"}:
                parsed: Any = val.lower() == "true"
            else:
                parsed = val
            root["providers"][current_provider][k] = parsed

    return result


def _load_iframe_config() -> Dict[str, Any]:
    yaml_path = Path("frontend/config/realtime_flash_iframe.yaml")
    if not yaml_path.exists():
        return {"realtime_flash_iframe": {"enabled": False, "providers": {}}}

    content = yaml_path.read_text(encoding="utf-8")

    # 优先尝试 PyYAML（若环境已安装）
    try:
        import yaml  # type: ignore

        loaded = yaml.safe_load(content)
        if isinstance(loaded, dict):
            return loaded
    except Exception:
        pass

    return _parse_iframe_yaml_fallback(content)


@router.get("/health")
async def health() -> Dict[str, Any]:
    settings = load_settings()
    dedup_path = Path(settings.dedup_cache_file)

    return {
        "ok": True,
        "module": "realtime_flash",
        "enabled": settings.enabled,
        "sources": {
            "jin10": {
                "enabled": settings.ws_enabled,
                "ws_url": settings.ws_url,
            },
            "fx678": {
                "enabled": settings.fx678_enabled,
                "url": settings.fx678_url,
                "poll_seconds": settings.fx678_poll_seconds,
            },
        },
        "dedup": {
            "cache_file": str(dedup_path),
            "exists": dedup_path.exists(),
            "cache_size": _service.runner.stats.get("dedup_cache_size", 0),
        },
        "last_run": {
            "at": _service.last_run_at,
            "error": _service.last_error,
            "degraded": _service.last_degraded,
            "degrade_reasons": _service.last_degrade_reasons,
        },
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }


@router.get("/latest")
async def latest(
    limit: int = Query(default=50, ge=1, le=500),
    source: str = Query(default="all"),
) -> Dict[str, Any]:
    items = _service.latest(limit=limit, source=source)
    return {
        "ok": True,
        "count": len(items),
        "limit": limit,
        "source": source,
        "items": items,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }


@router.post("/run-once")
async def run_once(payload: RunOnceRequest = RunOnceRequest()) -> Dict[str, Any]:
    try:
        result = await _service.run_once(max_items=payload.max_items, ws_wait_seconds=payload.ws_wait_seconds)
        return {
            "ok": True,
            "message": "run_once finished",
            "result": result,
            "degraded": _service.last_degraded,
            "degrade_reasons": _service.last_degrade_reasons,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "ok": False,
                "message": "run_once failed",
                "error": str(exc),
                "timestamp": datetime.now().isoformat(timespec="seconds"),
            },
        )


@router.get("/stats")
async def stats() -> Dict[str, Any]:
    return {"ok": True, **_service.stats()}


@router.get("/iframe-config")
async def iframe_config() -> Dict[str, Any]:
    """前端接线点：实时读取 frontend/config/realtime_flash_iframe.yaml。"""
    data = _load_iframe_config()
    return {
        "ok": True,
        "config": data.get("realtime_flash_iframe", {}),
        "config_path": os.path.abspath("frontend/config/realtime_flash_iframe.yaml"),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }
