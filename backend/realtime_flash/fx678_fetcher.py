from __future__ import annotations

from datetime import datetime
from typing import Dict, List

import requests
from bs4 import BeautifulSoup


class Fx678Fetcher:
    def __init__(self, url: str, timeout_seconds: int, user_agent: str, max_retries: int = 2):
        self.url = url
        self.timeout_seconds = max(3, int(timeout_seconds))
        self.max_retries = max(1, int(max_retries))
        self.headers = {
            "User-Agent": user_agent,
            "Referer": "https://www.fx678.com/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Connection": "keep-alive",
        }

    def fetch_once(self, limit: int = 20) -> List[Dict]:
        last_error = None
        response = None
        for _ in range(self.max_retries):
            try:
                response = requests.get(self.url, headers=self.headers, timeout=self.timeout_seconds)
                response.raise_for_status()
                break
            except requests.RequestException as exc:
                last_error = exc
        if response is None:
            raise last_error if last_error else RuntimeError("fx678 request failed")
        response.encoding = "utf-8"

        soup = BeautifulSoup(response.text, "lxml")
        items = self._extract_items(soup)
        return items[: max(1, int(limit))]

    def _extract_items(self, soup: BeautifulSoup) -> List[Dict]:
        selectors = [
            ".flash_list li",
            "li[data-id]",
            ".content li",
        ]
        nodes = []
        for selector in selectors:
            nodes = soup.select(selector)
            if nodes:
                break

        now = datetime.now()
        results: List[Dict] = []
        for node in nodes:
            text = " ".join(node.stripped_strings).strip()
            if not text:
                continue

            item_id = (node.get("data-id") or node.get("id") or "").strip()
            time_part = ""
            time_node = node.select_one(".flash_time")
            if time_node:
                time_part = "".join(time_node.stripped_strings).strip()
            publish_time = self._compose_publish_time(now, time_part)

            title_node = node.select_one(".flash_title") or node.select_one("a")
            title = " ".join(title_node.stripped_strings).strip() if title_node else text

            results.append(
                {
                    "title": title,
                    "content": text,
                    "source": "FX678",
                    "source_key": "fx678",
                    "publish_time": publish_time,
                    "url": self.url,
                    "external_id": item_id,
                }
            )
        return results

    @staticmethod
    def _compose_publish_time(now: datetime, time_part: str) -> str:
        if not time_part:
            return now.isoformat(timespec="seconds")
        clean = time_part.strip()
        try:
            if len(clean) == 5:
                dt = datetime.strptime(f"{now.strftime('%Y-%m-%d')} {clean}:00", "%Y-%m-%d %H:%M:%S")
            elif len(clean) == 8:
                dt = datetime.strptime(f"{now.strftime('%Y-%m-%d')} {clean}", "%Y-%m-%d %H:%M:%S")
            else:
                return now.isoformat(timespec="seconds")
            if dt > now:
                dt = dt.replace(day=now.day)
            return dt.isoformat(timespec="seconds")
        except Exception:
            return now.isoformat(timespec="seconds")
