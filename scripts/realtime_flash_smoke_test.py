#!/usr/bin/env python3

"""
Realtime Flash 冒烟测试：
1) 拉取一批快讯（默认 FX678）
2) 写入 news_storage
3) 输出关键统计
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from backend.realtime_flash.runner import build_runner  # noqa: E402
from backend.services.news_center.news_storage import get_news_storage  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Realtime Flash smoke test")
    parser.add_argument("--max-items", type=int, default=20, help="单次最多拉取条数")
    parser.add_argument("--hours", type=int, default=24, help="统计窗口（小时）")
    return parser.parse_args()


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def _compact(obj: Dict[str, Any]) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True)


async def run_smoke(max_items: int, hours: int) -> Dict[str, Any]:
    runner = build_runner()
    storage = get_news_storage()

    before = storage.get_statistics(hours=hours)
    fetch_error = ""
    try:
        cycle = await runner.run_once(max_items=max_items, ws_wait_seconds=4)
    except Exception as exc:
        fetch_error = str(exc)
        cycle = {"received": 0, "written": 0, "duplicated": 0, "invalid": 0}

    degraded = bool(fetch_error) or (int(cycle.get("received", 0)) == 0 and int(cycle.get("written", 0)) == 0)

    after = storage.get_statistics(hours=hours)

    output = {
        "max_items": max_items,
        "hours": hours,
        "before_total": int(before.get("total", 0)),
        "after_total": int(after.get("total", 0)),
        "delta_total": int(after.get("total", 0)) - int(before.get("total", 0)),
        "cycle": cycle,
        "fetch_error": fetch_error,
        "degraded": degraded,
        "degrade_reason": fetch_error or ("no_live_data" if degraded else ""),
        "runner_stats": runner.stats,
        "db_path": str(getattr(storage, "db_path", "")),
    }
    return output


def main() -> int:
    args = parse_args()
    setup_logging()

    module_env = PROJECT_ROOT / "backend" / "realtime_flash" / ".env"
    if module_env.exists():
        logging.getLogger("realtime_flash_smoke_test").info("Using module env: %s", module_env)
    else:
        logging.getLogger("realtime_flash_smoke_test").info(
            "Module env not found, using process/root env (path checked: %s)", module_env
        )

    try:
        result = asyncio.run(run_smoke(max_items=max(1, args.max_items), hours=max(1, args.hours)))
        print("[realtime_flash_smoke_test] RESULT")
        print(_compact(result))
        return 0
    except Exception as exc:
        logging.getLogger("realtime_flash_smoke_test").exception("Smoke test failed: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
