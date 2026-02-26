"""
早盘扫描模块 - PreMarketScanner
9:15前扫描选股池，调用策略中心API生成信号，输出今日候选列表
"""

import time
import json
import logging
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger("auto_trading.scanner")


# 默认选股池：沪深热门标的
DEFAULT_STOCK_POOL = [
    "600519",  # 贵州茅台
    "000858",  # 五粮液
    "601318",  # 中国平安
    "000333",  # 美的集团
    "600036",  # 招商银行
    "002594",  # 比亚迪
    "601899",  # 紫金矿业
    "600900",  # 长江电力
    "000001",  # 平安银行
    "002475",  # 立讯精密
    "601012",  # 隆基绿能
    "600276",  # 恒瑞医药
    "000568",  # 泸州老窖
    "002714",  # 牧原股份
    "600809",  # 山西汾酒
]


class PreMarketScanner:
    """早盘扫描器"""

    def __init__(
        self,
        api_base: str = "http://localhost:8000",
        stock_pool: Optional[List[str]] = None,
        strategy_id: Optional[str] = None,
        min_confidence: float = 0.55,
        max_retries: int = 3,
    ):
        self.api_base = api_base.rstrip("/")
        self.stock_pool = stock_pool or DEFAULT_STOCK_POOL
        self.strategy_id = strategy_id
        self.min_confidence = min_confidence
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def _api_call(self, method: str, path: str, **kwargs) -> Optional[Dict]:
        """带重试的API调用"""
        url = f"{self.api_base}{path}"
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.request(method, url, timeout=60, **kwargs)
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                logger.warning(f"[API调用失败] {method} {path} 第{attempt}次: {e}")
                if attempt < self.max_retries:
                    time.sleep(2 * attempt)
        logger.error(f"[API调用彻底失败] {method} {path} 已重试{self.max_retries}次")
        return None

    def _pick_strategy(self) -> Optional[str]:
        """选择策略：优先用指定的，否则取第一个预设策略"""
        if self.strategy_id:
            return self.strategy_id

        data = self._api_call("GET", "/api/strategy-center/strategies")
        if not data or not data.get("success"):
            logger.error("获取策略列表失败")
            return None

        strategies = data.get("data", [])
        if not strategies:
            logger.error("没有可用策略")
            return None

        # 优先选技术类策略
        for s in strategies:
            if s.get("category") == "technical":
                logger.info(f"选择策略: {s['id']} - {s['name']}")
                return s["id"]

        chosen = strategies[0]
        logger.info(f"选择策略: {chosen['id']} - {chosen['name']}")
        return chosen["id"]

    def generate_signal(self, stock_code: str, strategy_id: str) -> Optional[Dict]:
        """为单只股票生成交易信号"""
        payload = {
            "stock_code": stock_code,
            "strategy_id": strategy_id,
            "include_chart": False,
            "include_news": True,
            "timeframe": "daily",
        }
        data = self._api_call("POST", "/api/strategy-center/signal/generate", json=payload)
        if not data or not data.get("success"):
            logger.warning(f"[信号生成失败] {stock_code}")
            return None
        return data.get("data")

    def scan(self) -> List[Dict[str, Any]]:
        """
        执行早盘扫描

        Returns:
            候选列表: [{stock_code, stock_name, direction, target_price, stop_loss,
                        take_profit, confidence, strategy_name, reasoning}]
        """
        logger.info(f"{'='*60}")
        logger.info(f"[早盘扫描] 开始 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"[早盘扫描] 选股池: {len(self.stock_pool)}只")
        logger.info(f"{'='*60}")

        strategy_id = self._pick_strategy()
        if not strategy_id:
            logger.error("无法选择策略，扫描终止")
            return []

        candidates = []
        for i, code in enumerate(self.stock_pool, 1):
            logger.info(f"[扫描进度] ({i}/{len(self.stock_pool)}) 分析 {code} ...")
            signal = self.generate_signal(code, strategy_id)
            if not signal:
                continue

            signal_type = signal.get("signal_type", "HOLD")
            confidence = signal.get("confidence", 0)
            stock_name = signal.get("market_data_summary", {}).get("name", code)
            current_price = signal.get("market_data_summary", {}).get("current_price", 0)

            logger.info(
                f"  -> {stock_name}({code}): {signal_type} "
                f"置信度={confidence:.2f} 现价={current_price}"
            )

            if signal_type == "HOLD":
                continue
            if confidence < self.min_confidence:
                logger.info(f"  -> 置信度不足 {self.min_confidence}，跳过")
                continue

            candidate = {
                "stock_code": code,
                "stock_name": stock_name,
                "direction": signal_type,  # BUY or SELL
                "current_price": current_price,
                "target_price": signal.get("price_target", 0),
                "stop_loss": signal.get("stop_loss", 0),
                "take_profit": signal.get("take_profit", 0),
                "confidence": confidence,
                "position_size": signal.get("position_size", 0.2),
                "strategy_id": strategy_id,
                "strategy_name": signal.get("strategy_name", ""),
                "reasoning": signal.get("reasoning", ""),
                "scan_time": datetime.now().isoformat(),
            }
            candidates.append(candidate)
            logger.info(
                f"  ★ 加入候选: {signal_type} 目标={candidate['target_price']:.2f} "
                f"止损={candidate['stop_loss']:.2f}"
            )

            # 避免API限流
            time.sleep(1)

        logger.info(f"{'='*60}")
        logger.info(f"[早盘扫描] 完成 - 候选数量: {len(candidates)}/{len(self.stock_pool)}")
        for c in candidates:
            logger.info(
                f"  {c['stock_name']}({c['stock_code']}) {c['direction']} "
                f"置信度={c['confidence']:.2f}"
            )
        logger.info(f"{'='*60}")

        return candidates

    def save_candidates(self, candidates: List[Dict], filepath: str = "candidates.json"):
        """保存候选列表到文件"""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(candidates, f, ensure_ascii=False, indent=2)
        logger.info(f"[早盘扫描] 候选列表已保存: {filepath}")

    @staticmethod
    def load_candidates(filepath: str = "candidates.json") -> List[Dict]:
        """从文件加载候选列表"""
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
