from __future__ import annotations

import argparse
import asyncio
import logging
import os
import signal
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from backend.realtime_flash.dedup_store import DedupStore
from backend.realtime_flash.fx678_fetcher import Fx678Fetcher
from backend.realtime_flash.jin10_ws import Jin10WSClient
from backend.realtime_flash.writer import write_items


@dataclass
class FlashSettings:
    enabled: bool
    log_level: str
    dedup_ttl_seconds: int
    dedup_cache_file: str
    dedup_max_size: int
    writer_batch_size: int
    ws_enabled: bool
    ws_url: str
    ws_timeout_seconds: int
    ws_reconnect_seconds: int
    ws_subscription_payload: str
    fx678_enabled: bool
    fx678_url: str
    fx678_poll_seconds: int
    fx678_timeout_seconds: int
    fx678_max_retries: int
    http_user_agent: str


def _to_bool(value: Optional[str], default: bool) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def load_settings() -> FlashSettings:
    module_env = os.path.join(os.path.dirname(__file__), ".env")
    load_dotenv(module_env, override=False)
    load_dotenv(override=False)
    return FlashSettings(
        enabled=_to_bool(os.getenv("REALTIME_FLASH_ENABLED"), True),
        log_level=os.getenv("REALTIME_FLASH_LOG_LEVEL", "INFO"),
        dedup_ttl_seconds=int(os.getenv("REALTIME_FLASH_DEDUP_TTL_SECONDS", "86400")),
        dedup_cache_file=os.getenv("REALTIME_FLASH_DEDUP_CACHE_FILE", "data/realtime_flash/dedup_cache.json"),
        dedup_max_size=int(os.getenv("REALTIME_FLASH_DEDUP_MAX_SIZE", "20000")),
        writer_batch_size=int(os.getenv("REALTIME_FLASH_WRITER_BATCH_SIZE", "100")),
        ws_enabled=_to_bool(os.getenv("REALTIME_FLASH_JIN10_WS_ENABLED"), True),
        ws_url=os.getenv("REALTIME_FLASH_JIN10_WS_URL", "wss://flash.jin10.com/ws"),
        ws_timeout_seconds=int(os.getenv("REALTIME_FLASH_JIN10_WS_TIMEOUT_SECONDS", "15")),
        ws_reconnect_seconds=int(os.getenv("REALTIME_FLASH_JIN10_WS_RECONNECT_SECONDS", "5")),
        ws_subscription_payload=os.getenv("REALTIME_FLASH_JIN10_WS_SUBSCRIPTION_PAYLOAD", '{"action":"subscribe","channel":"flash"}'),
        fx678_enabled=_to_bool(os.getenv("REALTIME_FLASH_FX678_ENABLED"), True),
        fx678_url=os.getenv("REALTIME_FLASH_FX678_URL", "https://data.fx678.com/flash/"),
        fx678_poll_seconds=int(os.getenv("REALTIME_FLASH_FX678_POLL_SECONDS", "30")),
        fx678_timeout_seconds=int(os.getenv("REALTIME_FLASH_FX678_TIMEOUT_SECONDS", "12")),
        fx678_max_retries=int(os.getenv("REALTIME_FLASH_FX678_MAX_RETRIES", "2")),
        http_user_agent=os.getenv(
            "REALTIME_FLASH_HTTP_USER_AGENT",
            "InvestMindPro-RealtimeFlash/1.0 (+https://github.com/icysaintdx/InvestMind-Pro)",
        ),
    )


class RealtimeFlashRunner:
    def __init__(self, settings: FlashSettings):
        self.settings = settings
        self.logger = logging.getLogger("realtime_flash.runner")
        self.dedup = DedupStore(
            ttl_seconds=settings.dedup_ttl_seconds,
            cache_file=settings.dedup_cache_file,
            max_cache_size=settings.dedup_max_size,
        )
        self.fx678 = Fx678Fetcher(
            url=settings.fx678_url,
            timeout_seconds=settings.fx678_timeout_seconds,
            user_agent=settings.http_user_agent,
            max_retries=settings.fx678_max_retries,
        )
        self.jin10_ws = Jin10WSClient(
            ws_url=settings.ws_url,
            timeout_seconds=settings.ws_timeout_seconds,
            reconnect_seconds=settings.ws_reconnect_seconds,
            enabled=settings.ws_enabled,
            subscription_payload=settings.ws_subscription_payload,
        )
        self._stats = {
            "received": 0,
            "written": 0,
            "duplicated": 0,
            "invalid": 0,
            "dedup_cache_size": self.dedup.size(),
        }
        self._stop_event = asyncio.Event()
        self._tasks: List[asyncio.Task] = []

    @property
    def stats(self) -> Dict[str, int]:
        latest = dict(self._stats)
        latest["dedup_cache_size"] = self.dedup.size()
        return latest

    def _merge_stats(self, partial: Dict[str, int]) -> None:
        for key in ["received", "written", "duplicated", "invalid"]:
            self._stats[key] = self._stats.get(key, 0) + int(partial.get(key, 0))
        self._stats["dedup_cache_size"] = self.dedup.size()

    def _dedup_filter(self, items: List[Dict]) -> List[Dict]:
        selected: List[Dict] = []
        duplicate_count = 0
        for item in items:
            fp = self.dedup.fingerprint(item)
            if self.dedup.contains(fp):
                duplicate_count += 1
                continue
            self.dedup.mark(fp)
            selected.append(item)
        if duplicate_count:
            self._merge_stats({"duplicated": duplicate_count})
        return selected

    def process_items(self, items: List[Dict]) -> Dict[str, int]:
        if not items:
            return {"received": 0, "written": 0, "duplicated": 0, "invalid": 0}
        self._merge_stats({"received": len(items)})
        filtered = self._dedup_filter(items)
        if not filtered:
            return {"received": len(items), "written": 0, "duplicated": len(items), "invalid": 0}
        result = write_items(filtered)
        self._merge_stats(result)
        self.dedup.save()
        return result

    async def run_polling_once(self, max_items: int = 20) -> Dict[str, int]:
        if not self.settings.fx678_enabled:
            return {"received": 0, "written": 0, "duplicated": 0, "invalid": 0}
        items = self.fx678.fetch_once(limit=max_items)
        return self.process_items(items)

    async def run_once(self, max_items: int = 20, ws_wait_seconds: int = 4) -> Dict[str, Any]:
        """执行一次全源抓取：FX678 轮询 + JIN10 WS 短时监听。"""
        total = {"received": 0, "written": 0, "duplicated": 0, "invalid": 0}
        source_results: Dict[str, Dict[str, int]] = {}
        source_errors: Dict[str, str] = {}

        # FX678: 同步抓取一次
        if self.settings.fx678_enabled:
            try:
                fx_result = await self.run_polling_once(max_items=max_items)
                source_results["fx678"] = fx_result
                self._merge_once(total, fx_result)
            except Exception as exc:
                source_errors["fx678"] = str(exc) or repr(exc)

        # JIN10: ws短时监听，取首批有效消息
        if self.settings.ws_enabled:
            try:
                batch: List[Dict] = []

                async def _consume_once() -> None:
                    nonlocal batch
                    async for ws_batch in self.jin10_ws.stream(stop_event=None):
                        if ws_batch:
                            batch = ws_batch[: max(1, int(max_items))]
                            break

                await asyncio.wait_for(_consume_once(), timeout=max(1, int(ws_wait_seconds)))
                jin10_result = self.process_items(batch) if batch else {"received": 0, "written": 0, "duplicated": 0, "invalid": 0}
                source_results["jin10"] = jin10_result
                self._merge_once(total, jin10_result)
            except Exception as exc:
                source_errors["jin10"] = str(exc) or repr(exc)

        degraded = bool(source_errors) and total["written"] == 0
        return {
            **total,
            "source_results": source_results,
            "source_errors": source_errors,
            "degraded": degraded,
            "degrade_reasons": [f"{k}: {v}" for k, v in source_errors.items()],
        }

    @staticmethod
    def _merge_once(acc: Dict[str, int], delta: Dict[str, int]) -> None:
        for key in ("received", "written", "duplicated", "invalid"):
            acc[key] = int(acc.get(key, 0)) + int(delta.get(key, 0))

    async def _run_fx678_loop(self) -> None:
        if not self.settings.fx678_enabled:
            self.logger.info("FX678 polling disabled by config")
            return
        while not self._stop_event.is_set():
            try:
                batch = self.fx678.fetch_once(limit=self.settings.writer_batch_size)
                result = self.process_items(batch)
                self.logger.info("FX678 cycle: %s", result)
            except Exception as exc:
                self.logger.warning("FX678 polling failed: %s", exc)
            await asyncio.sleep(max(1, self.settings.fx678_poll_seconds))

    async def _run_jin10_ws_loop(self) -> None:
        if not self.settings.ws_enabled:
            self.logger.info("JIN10 websocket disabled by config")
            return
        async for batch in self.jin10_ws.stream(stop_event=self._stop_event):
            if self._stop_event.is_set():
                break
            result = self.process_items(batch)
            self.logger.info("JIN10 websocket cycle: %s", result)

    async def run_forever(self, run_seconds: Optional[int] = None) -> None:
        if not self.settings.enabled:
            self.logger.info("Realtime flash module disabled by config")
            return
        # 合规注意：仅使用公开可访问入口，严格遵守来源站点服务条款与访问频率限制。
        self.logger.warning("Compliance notice: use only public endpoints, obey source terms and access policies")
        self._tasks = [
            asyncio.create_task(self._run_fx678_loop(), name="fx678-loop"),
            asyncio.create_task(self._run_jin10_ws_loop(), name="jin10-ws-loop"),
        ]
        timer_task: Optional[asyncio.Task] = None
        if run_seconds and run_seconds > 0:
            timer_task = asyncio.create_task(self._auto_stop_after(run_seconds), name="auto-stop")
        try:
            await asyncio.gather(*self._tasks)
        except asyncio.CancelledError:
            self.logger.info("Realtime flash runner cancelled")
            raise
        finally:
            if timer_task:
                timer_task.cancel()
            self.dedup.save()
            self.logger.info("Realtime flash stopped, final stats: %s", self.stats)

    async def _auto_stop_after(self, run_seconds: int) -> None:
        await asyncio.sleep(run_seconds)
        self.logger.info("Auto stop triggered after %s seconds", run_seconds)
        await self.request_stop()

    async def request_stop(self) -> None:
        if self._stop_event.is_set():
            return
        self._stop_event.set()
        for task in self._tasks:
            if not task.done():
                task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)


def configure_logging(level: str) -> None:
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def build_runner() -> RealtimeFlashRunner:
    settings = load_settings()
    configure_logging(settings.log_level)
    return RealtimeFlashRunner(settings)


async def _main(run_once: bool, max_items: int, run_seconds: int, ws_wait_seconds: int) -> None:
    runner = build_runner()
    if run_once:
        result = await runner.run_once(max_items=max_items, ws_wait_seconds=ws_wait_seconds)
        logging.getLogger("realtime_flash.runner").info("run_once result: %s", result)
        return

    loop = asyncio.get_running_loop()

    def _signal_handler() -> None:
        logging.getLogger("realtime_flash.runner").info("Received stop signal, shutting down")
        asyncio.create_task(runner.request_stop())

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _signal_handler)
        except NotImplementedError:
            pass

    await runner.run_forever(run_seconds=run_seconds if run_seconds > 0 else None)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="realtime_flash_runner")
    parser.add_argument("--run-once", action="store_true")
    parser.add_argument("--max-items", type=int, default=20)
    parser.add_argument("--ws-wait-seconds", type=int, default=4, help="run-once模式下JIN10 WS等待秒数")
    parser.add_argument("--run-seconds", type=int, default=0, help="Auto stop after N seconds in daemon mode")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    asyncio.run(
        _main(
            run_once=args.run_once,
            max_items=args.max_items,
            run_seconds=args.run_seconds,
            ws_wait_seconds=args.ws_wait_seconds,
        )
    )


if __name__ == "__main__":
    main()
