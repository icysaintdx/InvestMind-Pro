from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import AsyncGenerator, Dict, List, Optional

import aiohttp


logger = logging.getLogger("realtime_flash.jin10_ws")


class Jin10WSClient:
    def __init__(
        self,
        ws_url: str,
        timeout_seconds: int,
        reconnect_seconds: int,
        enabled: bool,
        subscription_payload: str = '{"action":"subscribe","channel":"flash"}',
    ):
        self.ws_url = ws_url
        self.timeout_seconds = max(3, int(timeout_seconds))
        self.reconnect_seconds = max(1, int(reconnect_seconds))
        self.enabled = bool(enabled)
        self.subscription_payload = subscription_payload

    async def stream(self, stop_event: Optional[asyncio.Event] = None) -> AsyncGenerator[List[Dict], None]:
        if not self.enabled:
            logger.info("JIN10 websocket disabled by config")
            return

        session_timeout = aiohttp.ClientTimeout(total=self.timeout_seconds)
        while not self._should_stop(stop_event):
            try:
                async with aiohttp.ClientSession(timeout=session_timeout) as session:
                    async with session.ws_connect(self.ws_url, heartbeat=20) as ws:
                        await ws.send_str(self.subscription_payload)
                        logger.info("JIN10 websocket connected")
                        while not self._should_stop(stop_event):
                            msg = await ws.receive(timeout=1)
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                items = self._parse_message(msg.data)
                                if items:
                                    yield items
                            elif msg.type == aiohttp.WSMsgType.PING:
                                await ws.pong()
                            elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                                break
            except Exception as exc:
                logger.warning("JIN10 websocket unavailable, fallback to polling: %s", exc)
                if self._should_stop(stop_event):
                    break
                await asyncio.sleep(self.reconnect_seconds)

    @staticmethod
    def _should_stop(stop_event: Optional[asyncio.Event]) -> bool:
        return bool(stop_event and stop_event.is_set())

    def _parse_message(self, data: str) -> List[Dict]:
        try:
            parsed = json.loads(data)
        except Exception:
            return []

        payloads: List[Dict] = []
        if isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, dict):
                    payloads.append(item)
        elif isinstance(parsed, dict):
            payloads.append(parsed)

        out: List[Dict] = []
        for payload in payloads:
            data_node = payload.get("data", payload)
            if not isinstance(data_node, dict):
                continue

            title = str(data_node.get("title") or data_node.get("content") or "").strip()
            content = str(data_node.get("content") or title).strip()
            if not title:
                continue

            ts = data_node.get("time") or data_node.get("timestamp")
            publish_time = self._parse_time(ts)

            out.append(
                {
                    "title": title,
                    "content": content,
                    "source": "JIN10",
                    "source_key": "jin10",
                    "publish_time": publish_time,
                    "url": "https://www.jin10.com/",
                    "external_id": str(data_node.get("id") or "").strip(),
                }
            )
        return out

    @staticmethod
    def _parse_time(ts) -> str:
        now = datetime.now()
        if ts is None:
            return now.isoformat(timespec="seconds")
        try:
            value = float(ts)
            if value > 1e12:
                value = value / 1000.0
            return datetime.fromtimestamp(value).isoformat(timespec="seconds")
        except Exception:
            return now.isoformat(timespec="seconds")
