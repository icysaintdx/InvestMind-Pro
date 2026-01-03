# -*- coding: utf-8 -*-
"""
行情异动检测服务
监控股票价格、成交量等异动，并创建预警
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from backend.utils.logging_config import get_logger

logger = get_logger("price_monitor")


@dataclass
class PriceSnapshot:
    """价格快照"""
    ts_code: str
    price: float
    change_pct: float
    volume: float
    amount: float
    timestamp: datetime


class PriceMonitorService:
    """行情异动检测服务"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._running = False
        self._check_interval = 60  # 1分钟检查一次
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="price_")
        self._task: Optional[asyncio.Task] = None

        # 价格快照缓存
        self._price_cache: Dict[str, PriceSnapshot] = {}
        # 历史成交量（用于计算放量）
        self._volume_history: Dict[str, List[float]] = {}

        # 预警阈值配置
        self._thresholds = {
            'surge_pct': 5.0,       # 急涨阈值 5%
            'plunge_pct': -5.0,     # 急跌阈值 -5%
            'limit_up_pct': 9.9,    # 涨停阈值
            'limit_down_pct': -9.9, # 跌停阈值
            'volume_ratio': 3.0,    # 放量倍数
        }

        logger.info("PriceMonitorService initialized")

    async def start(self):
        """启动行情监控"""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("PriceMonitorService started")

    async def stop(self):
        """停止行情监控"""
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None
        if self._executor:
            self._executor.shutdown(wait=False)
        logger.info("PriceMonitorService stopped")

    async def _monitor_loop(self):
        """监控循环"""
        while self._running:
            try:
                # 只在交易时间检查
                if self._is_trading_time():
                    await self._check_price_changes()
            except Exception as e:
                logger.error(f"Price monitor error: {e}")
            await asyncio.sleep(self._check_interval)

    def _is_trading_time(self) -> bool:
        """判断是否在交易时间"""
        now = datetime.now()
        # 周末不交易
        if now.weekday() >= 5:
            return False
        # 交易时间: 9:30-11:30, 13:00-15:00
        hour = now.hour
        minute = now.minute
        time_val = hour * 100 + minute

        if 930 <= time_val <= 1130:
            return True
        if 1300 <= time_val <= 1500:
            return True
        return False

    async def _check_price_changes(self):
        """检查价格变化"""
        try:
            from backend.services.alert_service import get_alert_service
            alert_service = get_alert_service()
            monitored_stocks = alert_service.get_monitored_stocks()

            if not monitored_stocks:
                return

            # 批量获取实时行情
            ts_codes = list(monitored_stocks.keys())
            quotes = await self._fetch_realtime_quotes(ts_codes)

            if not quotes:
                return

            # 检查每只股票的异动
            for ts_code, quote in quotes.items():
                stock_info = monitored_stocks.get(ts_code, {})
                await self._check_stock_anomaly(ts_code, stock_info, quote)

        except Exception as e:
            logger.error(f"Check price changes failed: {e}")

    async def _fetch_realtime_quotes(self, ts_codes: List[str]) -> Dict[str, Dict]:
        """获取实时行情"""
        quotes = {}
        loop = asyncio.get_event_loop()

        try:
            import akshare as ak

            def fetch_quotes():
                result = {}
                try:
                    # 获取实时行情
                    df = ak.stock_zh_a_spot_em()
                    if df is not None and not df.empty:
                        for ts_code in ts_codes:
                            pure_code = ts_code.split('.')[0]
                            # 在数据中查找
                            row = df[df['代码'] == pure_code]
                            if not row.empty:
                                row = row.iloc[0]
                                result[ts_code] = {
                                    'price': float(row.get('最新价', 0) or 0),
                                    'change_pct': float(row.get('涨跌幅', 0) or 0),
                                    'volume': float(row.get('成交量', 0) or 0),
                                    'amount': float(row.get('成交额', 0) or 0),
                                    'high': float(row.get('最高', 0) or 0),
                                    'low': float(row.get('最低', 0) or 0),
                                    'open': float(row.get('今开', 0) or 0),
                                    'pre_close': float(row.get('昨收', 0) or 0),
                                }
                except Exception as e:
                    logger.debug(f"Fetch quotes failed: {e}")
                return result

            quotes = await loop.run_in_executor(self._executor, fetch_quotes)

        except Exception as e:
            logger.error(f"Fetch realtime quotes failed: {e}")

        return quotes

    async def _check_stock_anomaly(self, ts_code: str, stock_info: Dict, quote: Dict):
        """检查单只股票的异动"""
        stock_name = stock_info.get('name', '')
        change_pct = quote.get('change_pct', 0)
        volume = quote.get('volume', 0)
        price = quote.get('price', 0)

        from backend.services.alert_service import get_alert_service, AlertData, AlertType, AlertLevel
        alert_service = get_alert_service()

        alerts_to_create = []

        # 1. 检查涨停
        if change_pct >= self._thresholds['limit_up_pct']:
            alerts_to_create.append(AlertData(
                ts_code=ts_code,
                stock_name=stock_name,
                alert_type=AlertType.PRICE_LIMIT_UP,
                alert_level=AlertLevel.HIGH,
                title=f"🔴 涨停 {stock_name}({ts_code.split('.')[0]}) +{change_pct:.2f}%",
                message=f"当前价格: {price:.2f}，涨幅: {change_pct:.2f}%",
                suggestion="涨停板，关注后续走势"
            ))

        # 2. 检查跌停
        elif change_pct <= self._thresholds['limit_down_pct']:
            alerts_to_create.append(AlertData(
                ts_code=ts_code,
                stock_name=stock_name,
                alert_type=AlertType.PRICE_LIMIT_DOWN,
                alert_level=AlertLevel.CRITICAL,
                title=f"🟢 跌停 {stock_name}({ts_code.split('.')[0]}) {change_pct:.2f}%",
                message=f"当前价格: {price:.2f}，跌幅: {change_pct:.2f}%",
                suggestion="跌停板，注意风险"
            ))

        # 3. 检查急涨
        elif change_pct >= self._thresholds['surge_pct']:
            alerts_to_create.append(AlertData(
                ts_code=ts_code,
                stock_name=stock_name,
                alert_type=AlertType.PRICE_SURGE,
                alert_level=AlertLevel.MEDIUM,
                title=f"📈 急涨 {stock_name}({ts_code.split('.')[0]}) +{change_pct:.2f}%",
                message=f"当前价格: {price:.2f}，涨幅: {change_pct:.2f}%",
                suggestion="股价快速上涨，关注是否有利好消息"
            ))

        # 4. 检查急跌
        elif change_pct <= self._thresholds['plunge_pct']:
            alerts_to_create.append(AlertData(
                ts_code=ts_code,
                stock_name=stock_name,
                alert_type=AlertType.PRICE_PLUNGE,
                alert_level=AlertLevel.HIGH,
                title=f"📉 急跌 {stock_name}({ts_code.split('.')[0]}) {change_pct:.2f}%",
                message=f"当前价格: {price:.2f}，跌幅: {change_pct:.2f}%",
                suggestion="股价快速下跌，注意风险"
            ))

        # 5. 检查放量
        if volume > 0:
            avg_volume = self._get_average_volume(ts_code)
            if avg_volume > 0:
                volume_ratio = volume / avg_volume
                if volume_ratio >= self._thresholds['volume_ratio']:
                    alerts_to_create.append(AlertData(
                        ts_code=ts_code,
                        stock_name=stock_name,
                        alert_type=AlertType.VOLUME_SURGE,
                        alert_level=AlertLevel.MEDIUM,
                        title=f"📊 放量 {stock_name}({ts_code.split('.')[0]}) {volume_ratio:.1f}倍",
                        message=f"成交量: {volume/10000:.0f}万手，是平均成交量的{volume_ratio:.1f}倍",
                        suggestion="成交量异常放大，关注资金动向"
                    ))

            # 更新成交量历史
            self._update_volume_history(ts_code, volume)

        # 更新价格缓存
        self._price_cache[ts_code] = PriceSnapshot(
            ts_code=ts_code,
            price=price,
            change_pct=change_pct,
            volume=volume,
            amount=quote.get('amount', 0),
            timestamp=datetime.now()
        )

        # 创建预警（避免重复）
        for alert_data in alerts_to_create:
            # 检查是否在短时间内已经创建过相同类型的预警
            if not self._is_duplicate_alert(ts_code, alert_data.alert_type):
                await alert_service.create_alert(alert_data)

    def _get_average_volume(self, ts_code: str) -> float:
        """获取平均成交量"""
        history = self._volume_history.get(ts_code, [])
        if not history:
            return 0
        return sum(history) / len(history)

    def _update_volume_history(self, ts_code: str, volume: float):
        """更新成交量历史"""
        if ts_code not in self._volume_history:
            self._volume_history[ts_code] = []

        self._volume_history[ts_code].append(volume)

        # 只保留最近20个数据点
        if len(self._volume_history[ts_code]) > 20:
            self._volume_history[ts_code] = self._volume_history[ts_code][-20:]

    def _is_duplicate_alert(self, ts_code: str, alert_type) -> bool:
        """检查是否是重复预警（同一股票同一类型在5分钟内）"""
        # 简单实现：使用内存缓存
        cache_key = f"{ts_code}_{alert_type.value if hasattr(alert_type, 'value') else alert_type}"

        if not hasattr(self, '_alert_cache'):
            self._alert_cache = {}

        now = datetime.now()
        if cache_key in self._alert_cache:
            last_time = self._alert_cache[cache_key]
            if (now - last_time).total_seconds() < 300:  # 5分钟内
                return True

        self._alert_cache[cache_key] = now
        return False

    def set_thresholds(self, thresholds: Dict):
        """设置预警阈值"""
        self._thresholds.update(thresholds)
        logger.info(f"Price thresholds updated: {self._thresholds}")

    def set_check_interval(self, seconds: int):
        """设置检查间隔"""
        self._check_interval = max(30, seconds)  # 最少30秒
        logger.info(f"Price check interval set to {self._check_interval}s")

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'running': self._running,
            'check_interval': self._check_interval,
            'thresholds': self._thresholds,
            'cached_prices': len(self._price_cache),
            'is_trading_time': self._is_trading_time()
        }


# 单例获取函数
_price_monitor = None


def get_price_monitor_service() -> PriceMonitorService:
    global _price_monitor
    if _price_monitor is None:
        _price_monitor = PriceMonitorService()
    return _price_monitor
