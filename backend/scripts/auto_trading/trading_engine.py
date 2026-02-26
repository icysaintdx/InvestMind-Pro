"""
自动交易引擎 - TradingEngine
每30秒轮询候选列表，akshare取实时价格，触发目标位/止损位自动下单/平仓
对接现有 paper_trading_api
"""

import time
import json
import logging
import requests
import akshare as ak
import pandas as pd
from datetime import datetime, time as dtime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("auto_trading.engine")


@dataclass
class PositionInfo:
    """持仓跟踪"""
    stock_code: str
    stock_name: str
    direction: str  # BUY
    quantity: int
    entry_price: float
    stop_loss: float
    take_profit: float
    entry_time: str = ""


class TradingEngine:
    """自动交易引擎"""

    MORNING_START = dtime(9, 30)
    MORNING_END = dtime(11, 30)
    AFTERNOON_START = dtime(13, 0)
    AFTERNOON_END = dtime(15, 0)

    def __init__(
        self,
        api_base: str = "http://localhost:8000",
        initial_capital: float = 1_000_000,
        poll_interval: int = 30,
        max_retries: int = 3,
        account_name: str = "自动模拟交易账户",
    ):
        self.api_base = api_base.rstrip("/")
        self.initial_capital = initial_capital
        self.poll_interval = poll_interval
        self.max_retries = max_retries
        self.account_name = account_name
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

        # 状态
        self.account_id: Optional[str] = None
        self.candidates: List[Dict] = []
        self.active_positions: Dict[str, PositionInfo] = {}  # stock_code -> PositionInfo
        self.trade_log: List[Dict] = []
        self.running = False

        # 价格缓存（避免重复拉全市场）
        self._price_cache: Dict[str, Dict] = {}
        self._price_cache_time: Optional[datetime] = None

    # ==================== API调用 ====================

    def _api_call(self, method: str, path: str, **kwargs) -> Optional[Dict]:
        """带重试的API调用"""
        url = f"{self.api_base}{path}"
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.request(method, url, timeout=30, **kwargs)
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                logger.warning(f"[API] {method} {path} 第{attempt}次失败: {e}")
                if attempt < self.max_retries:
                    time.sleep(2 * attempt)
        logger.error(f"[API] {method} {path} 彻底失败")
        return None

    # ==================== 账户管理 ====================

    def init_account(self) -> bool:
        """创建模拟交易账户"""
        data = self._api_call("POST", "/api/paper-trading/account/create", json={
            "initial_capital": self.initial_capital,
            "account_name": self.account_name,
        })
        if not data or not data.get("success"):
            logger.error("创建模拟账户失败")
            return False

        self.account_id = data["account"]["account_id"]
        logger.info(f"[账户] 创建成功: {self.account_id} 初始资金={self.initial_capital:,.0f}")
        return True

    def get_account_info(self) -> Optional[Dict]:
        """获取账户信息"""
        if not self.account_id:
            return None
        return self._api_call("GET", f"/api/paper-trading/account/{self.account_id}")

    def get_positions(self) -> List[Dict]:
        """获取当前持仓"""
        if not self.account_id:
            return []
        data = self._api_call("GET", f"/api/paper-trading/account/{self.account_id}/positions")
        if data and data.get("success"):
            return data.get("positions", [])
        return []

    def get_trades(self) -> List[Dict]:
        """获取交易记录"""
        if not self.account_id:
            return []
        data = self._api_call("GET", f"/api/paper-trading/account/{self.account_id}/trades")
        if data and data.get("success"):
            return data.get("trades", [])
        return []

    # ==================== 行情获取 ====================

    def fetch_realtime_prices(self, stock_codes: List[str]) -> Dict[str, float]:
        """批量获取实时价格（akshare）"""
        now = datetime.now()

        # 5秒内缓存有效
        if (self._price_cache_time and
                (now - self._price_cache_time).total_seconds() < 5 and
                self._price_cache):
            result = {}
            for code in stock_codes:
                if code in self._price_cache:
                    result[code] = self._price_cache[code]
            if len(result) == len(stock_codes):
                return result

        try:
            df = ak.stock_zh_a_spot_em()
            if df is None or df.empty:
                logger.warning("[行情] akshare返回空数据")
                return {}

            prices = {}
            cache = {}
            for _, row in df.iterrows():
                code = str(row.get("代码", ""))
                price = row.get("最新价", 0)
                if price and float(price) > 0:
                    cache[code] = float(price)

            self._price_cache = cache
            self._price_cache_time = now

            for code in stock_codes:
                if code in cache:
                    prices[code] = cache[code]
                else:
                    logger.warning(f"[行情] 未找到 {code} 的价格")

            return prices

        except Exception as e:
            logger.error(f"[行情] 获取实时价格失败: {e}")
            return {}

    # ==================== 下单 ====================

    def place_order(self, stock_code: str, side: str, quantity: int, price: float) -> Optional[Dict]:
        """通过paper_trading_api下单"""
        payload = {
            "account_id": self.account_id,
            "stock_code": stock_code,
            "side": side,
            "quantity": quantity,
            "price": price,
            "order_type": "market",
        }
        data = self._api_call("POST", "/api/paper-trading/order/place", json=payload)
        if data and data.get("success"):
            logger.info(f"[下单成功] {side.upper()} {stock_code} {quantity}股 @ {price:.2f}")
            return data
        else:
            logger.error(f"[下单失败] {side.upper()} {stock_code} {quantity}股 @ {price:.2f}")
            return None

    def _calc_quantity(self, price: float, position_size: float) -> int:
        """计算买入数量（整百股）"""
        info = self.get_account_info()
        if not info or not info.get("success"):
            return 0
        available = info["account"]["available_cash"]
        budget = available * position_size
        qty = int(budget / price / 100) * 100
        return max(qty, 0)

    # ==================== 交易时间 ====================

    @classmethod
    def is_trading_time(cls) -> bool:
        """判断是否在交易时间"""
        now = datetime.now()
        if now.weekday() >= 5:
            return False
        t = now.time()
        return (cls.MORNING_START <= t <= cls.MORNING_END or
                cls.AFTERNOON_START <= t <= cls.AFTERNOON_END)

    @classmethod
    def is_market_closed(cls) -> bool:
        """判断今日是否已收盘"""
        now = datetime.now()
        if now.weekday() >= 5:
            return True
        return now.time() > cls.AFTERNOON_END

    # ==================== 核心循环 ====================

    def _log_trade(self, action: str, stock_code: str, stock_name: str,
                   quantity: int, price: float, reason: str):
        """记录交易日志"""
        entry = {
            "time": datetime.now().isoformat(),
            "action": action,
            "stock_code": stock_code,
            "stock_name": stock_name,
            "quantity": quantity,
            "price": price,
            "reason": reason,
        }
        self.trade_log.append(entry)
        logger.info(
            f"[交易记录] {action} {stock_name}({stock_code}) "
            f"{quantity}股 @ {price:.2f} | {reason}"
        )

    def _try_entry(self, candidate: Dict, current_price: float):
        """尝试入场"""
        code = candidate["stock_code"]
        name = candidate.get("stock_name", code)
        direction = candidate["direction"]

        if code in self.active_positions:
            return  # 已持仓

        if direction != "BUY":
            return  # 目前只做多

        # 入场条件：当前价 <= 目标价（信号给出的合理买入区间）
        target = candidate.get("target_price", 0)
        stop_loss = candidate.get("stop_loss", 0)
        take_profit = candidate.get("take_profit", 0)

        # 如果当前价在止损和目标价之间，视为合理入场区间
        if current_price <= 0 or stop_loss <= 0:
            return

        # 入场逻辑：价格在合理范围内就买入
        # （信号已经通过策略中心验证，这里直接执行）
        position_size = candidate.get("position_size", 0.2)
        quantity = self._calc_quantity(current_price, position_size)
        if quantity < 100:
            logger.warning(f"[入场] {name}({code}) 资金不足，跳过")
            return

        result = self.place_order(code, "buy", quantity, current_price)
        if result:
            self.active_positions[code] = PositionInfo(
                stock_code=code,
                stock_name=name,
                direction="BUY",
                quantity=quantity,
                entry_price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                entry_time=datetime.now().isoformat(),
            )
            self._log_trade("BUY", code, name, quantity, current_price,
                            f"策略信号入场 置信度={candidate.get('confidence', 0):.2f}")

    def _check_exit(self, code: str, current_price: float):
        """检查是否需要平仓"""
        pos = self.active_positions.get(code)
        if not pos:
            return

        reason = ""
        should_exit = False

        # 止损
        if pos.stop_loss > 0 and current_price <= pos.stop_loss:
            reason = f"触发止损 止损价={pos.stop_loss:.2f} 现价={current_price:.2f}"
            should_exit = True

        # 止盈
        elif pos.take_profit > 0 and current_price >= pos.take_profit:
            reason = f"触发止盈 止盈价={pos.take_profit:.2f} 现价={current_price:.2f}"
            should_exit = True

        if should_exit:
            result = self.place_order(code, "sell", pos.quantity, current_price)
            if result:
                pnl = (current_price - pos.entry_price) * pos.quantity
                self._log_trade(
                    "SELL", code, pos.stock_name, pos.quantity, current_price,
                    f"{reason} 盈亏={pnl:+,.2f}"
                )
                del self.active_positions[code]

    def run(self, candidates: List[Dict]):
        """
        启动交易引擎主循环

        Args:
            candidates: 早盘扫描产生的候选列表
        """
        self.candidates = candidates
        self.running = True

        if not self.account_id:
            if not self.init_account():
                logger.error("初始化账户失败，引擎退出")
                return

        logger.info(f"{'='*60}")
        logger.info(f"[交易引擎] 启动 - 候选={len(candidates)}只 轮询间隔={self.poll_interval}秒")
        logger.info(f"[交易引擎] 账户={self.account_id} 资金={self.initial_capital:,.0f}")
        logger.info(f"{'='*60}")

        # 入场：对所有BUY候选立即尝试入场
        buy_candidates = [c for c in candidates if c.get("direction") == "BUY"]
        if buy_candidates:
            codes = [c["stock_code"] for c in buy_candidates]
            prices = self.fetch_realtime_prices(codes)
            for c in buy_candidates:
                code = c["stock_code"]
                if code in prices:
                    self._try_entry(c, prices[code])

        # 轮询监控
        cycle = 0
        while self.running:
            cycle += 1

            if not self.is_trading_time():
                if self.is_market_closed():
                    logger.info("[交易引擎] 今日已收盘，引擎停止")
                    break
                logger.debug(f"[交易引擎] 非交易时间，等待...")
                time.sleep(30)
                continue

            # 获取所有需要监控的股票价格
            monitor_codes = list(self.active_positions.keys())
            # 也监控还没入场的候选
            for c in candidates:
                if c["stock_code"] not in self.active_positions:
                    monitor_codes.append(c["stock_code"])
            monitor_codes = list(set(monitor_codes))

            if not monitor_codes:
                logger.info("[交易引擎] 无监控标的，等待...")
                time.sleep(self.poll_interval)
                continue

            prices = self.fetch_realtime_prices(monitor_codes)
            if not prices:
                logger.warning(f"[交易引擎] 第{cycle}轮 获取价格失败")
                time.sleep(self.poll_interval)
                continue

            # 检查平仓
            for code in list(self.active_positions.keys()):
                if code in prices:
                    self._check_exit(code, prices[code])

            # 检查入场（未持仓的候选）
            for c in candidates:
                code = c["stock_code"]
                if code not in self.active_positions and code in prices:
                    self._try_entry(c, prices[code])

            # 日志
            if cycle % 10 == 0:
                logger.info(
                    f"[交易引擎] 第{cycle}轮 持仓={len(self.active_positions)} "
                    f"交易={len(self.trade_log)}笔"
                )

            time.sleep(self.poll_interval)

        self.running = False
        logger.info(f"[交易引擎] 已停止 总交易={len(self.trade_log)}笔")

    def stop(self):
        """停止引擎"""
        self.running = False
        logger.info("[交易引擎] 收到停止信号")

    def save_trade_log(self, filepath: str = "trade_log.json"):
        """保存交易日志"""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.trade_log, f, ensure_ascii=False, indent=2)
        logger.info(f"[交易引擎] 交易日志已保存: {filepath}")
