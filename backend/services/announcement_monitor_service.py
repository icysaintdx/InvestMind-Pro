# -*- coding: utf-8 -*-
"""
公告监控服务
定时检查监控股票的新公告，并创建预警
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from concurrent.futures import ThreadPoolExecutor

from backend.utils.logging_config import get_logger

logger = get_logger("announcement_monitor")


class AnnouncementMonitorService:
    """公告监控服务"""

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
        self._check_interval = 300  # 5分钟检查一次
        self._last_check_time: Dict[str, datetime] = {}  # 每只股票的最后检查时间
        self._seen_announcements: Set[str] = set()  # 已处理的公告ID
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ann_")
        self._task: Optional[asyncio.Task] = None
        logger.info("AnnouncementMonitorService initialized")

    async def start(self):
        """启动公告监控"""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("AnnouncementMonitorService started")

    async def stop(self):
        """停止公告监控"""
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None
        if self._executor:
            self._executor.shutdown(wait=False)
        logger.info("AnnouncementMonitorService stopped")

    async def _monitor_loop(self):
        """监控循环"""
        while self._running:
            try:
                await self._check_announcements()
            except Exception as e:
                logger.error(f"Announcement monitor error: {e}")
            await asyncio.sleep(self._check_interval)

    async def _check_announcements(self):
        """检查监控股票的公告"""
        try:
            from backend.services.alert_service import get_alert_service
            alert_service = get_alert_service()
            monitored_stocks = alert_service.get_monitored_stocks()

            if not monitored_stocks:
                return

            logger.info(f"Checking announcements for {len(monitored_stocks)} stocks")

            # 获取所有监控股票的公告
            for ts_code, stock_info in monitored_stocks.items():
                try:
                    await self._check_stock_announcements(ts_code, stock_info)
                except Exception as e:
                    logger.debug(f"Check announcement failed for {ts_code}: {e}")

        except Exception as e:
            logger.error(f"Check announcements failed: {e}")

    async def _check_stock_announcements(self, ts_code: str, stock_info: Dict):
        """检查单只股票的公告"""
        stock_name = stock_info.get('name', '')
        pure_code = ts_code.split('.')[0]

        # 获取最近的公告
        announcements = await self._fetch_stock_announcements(pure_code)

        if not announcements:
            return

        # 过滤已处理的公告
        new_announcements = []
        for ann in announcements:
            ann_id = self._generate_announcement_id(ann)
            if ann_id not in self._seen_announcements:
                self._seen_announcements.add(ann_id)
                new_announcements.append(ann)

        if not new_announcements:
            return

        logger.info(f"Found {len(new_announcements)} new announcements for {ts_code}")

        # 为新公告创建预警
        from backend.services.alert_service import get_alert_service, AlertData, AlertType, AlertLevel
        alert_service = get_alert_service()

        for ann in new_announcements:
            title = ann.get('title', '')
            pub_time = ann.get('pub_time', '')

            # 判断公告类型和级别
            alert_type, alert_level = self._classify_announcement(title)

            # 只为重要公告创建预警
            if alert_level == AlertLevel.LOW:
                continue

            alert_data = AlertData(
                ts_code=ts_code,
                stock_name=stock_name,
                alert_type=alert_type,
                alert_level=alert_level,
                title=f"[公告] {title[:80]}",
                message=ann.get('content', title)[:500],
                suggestion=f"发布时间: {pub_time}",
                source=ann.get('source', '巨潮公告'),
                url=ann.get('url', '')
            )

            await alert_service.create_alert(alert_data)

    async def _fetch_stock_announcements(self, stock_code: str) -> List[Dict]:
        """获取股票公告"""
        announcements = []
        loop = asyncio.get_event_loop()

        # 方法1: 使用巨潮API
        try:
            from backend.dataflows.announcement.cninfo_api import get_cninfo_api_client, CninfoConfig

            if CninfoConfig.is_configured():
                client = get_cninfo_api_client()
                today = datetime.now().strftime('%Y-%m-%d')
                yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

                result = await client.get_announcement_info(
                    stock_code=stock_code,
                    start_date=yesterday,
                    end_date=today,
                    page_size=50
                )

                if result.get('success') and result.get('data'):
                    for item in result['data']:
                        title = item.get('F002V', '')
                        if title:
                            announcements.append({
                                'title': title,
                                'content': f"证券代码: {stock_code}",
                                'pub_time': item.get('F001D', ''),
                                'url': item.get('F003V', ''),
                                'source': '巨潮公告',
                                'category': item.get('F006V', '')
                            })
        except Exception as e:
            logger.debug(f"Cninfo announcement fetch failed: {e}")

        # 方法2: 使用AKShare
        if not announcements:
            try:
                import akshare as ak

                def fetch_ak():
                    try:
                        df = ak.stock_notice_report(symbol=stock_code)
                        if df is not None and not df.empty:
                            result = []
                            for _, row in df.head(20).iterrows():
                                title = str(row.get('公告标题', row.get('标题', '')))
                                if title:
                                    result.append({
                                        'title': title,
                                        'content': str(row.get('公告内容', ''))[:500],
                                        'pub_time': str(row.get('公告日期', '')),
                                        'url': str(row.get('公告链接', '')),
                                        'source': 'AKShare公告'
                                    })
                            return result
                    except:
                        pass
                    return []

                announcements = await loop.run_in_executor(self._executor, fetch_ak)
            except Exception as e:
                logger.debug(f"AKShare announcement fetch failed: {e}")

        return announcements

    def _generate_announcement_id(self, announcement: Dict) -> str:
        """生成公告唯一ID"""
        import hashlib
        title = announcement.get('title', '')
        pub_time = announcement.get('pub_time', '')
        content = f"{title}_{pub_time}"
        return hashlib.md5(content.encode()).hexdigest()

    def _classify_announcement(self, title: str):
        """分类公告类型和级别"""
        from backend.services.alert_service import AlertType, AlertLevel

        title_lower = title.lower()

        # 业绩相关 - 高优先级
        if any(kw in title for kw in ['业绩预告', '业绩快报', '年度报告', '季度报告', '中期报告']):
            return AlertType.ANNOUNCEMENT_EARNINGS, AlertLevel.HIGH

        # 分红相关 - 中优先级
        if any(kw in title for kw in ['分红', '派息', '送股', '转增', '利润分配']):
            return AlertType.ANNOUNCEMENT_DIVIDEND, AlertLevel.MEDIUM

        # 股东变动 - 高优先级
        if any(kw in title for kw in ['增持', '减持', '股东', '举牌', '权益变动']):
            return AlertType.ANNOUNCEMENT_HOLDER, AlertLevel.HIGH

        # 风险提示 - 紧急
        if any(kw in title for kw in ['风险提示', 'ST', '退市', '暂停上市', '终止上市']):
            return AlertType.ANNOUNCEMENT_RISK, AlertLevel.CRITICAL

        # 停复牌 - 高优先级
        if any(kw in title for kw in ['停牌', '复牌']):
            return AlertType.ANNOUNCEMENT_SUSPEND, AlertLevel.HIGH

        # 重大事项 - 高优先级
        if any(kw in title for kw in ['重大', '重组', '并购', '收购', '资产注入']):
            return AlertType.NEWS_MAJOR, AlertLevel.HIGH

        # 其他公告 - 低优先级
        return AlertType.NEWS_MAJOR, AlertLevel.LOW

    def set_check_interval(self, seconds: int):
        """设置检查间隔"""
        self._check_interval = max(60, seconds)  # 最少1分钟
        logger.info(f"Announcement check interval set to {self._check_interval}s")

    async def check_now(self, ts_code: str = None):
        """立即检查公告"""
        if ts_code:
            from backend.services.alert_service import get_alert_service
            alert_service = get_alert_service()
            stock_info = alert_service.get_stock_info(ts_code)
            if stock_info:
                await self._check_stock_announcements(ts_code, stock_info)
        else:
            await self._check_announcements()

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'running': self._running,
            'check_interval': self._check_interval,
            'seen_announcements': len(self._seen_announcements),
            'last_check_times': {
                k: v.isoformat() for k, v in self._last_check_time.items()
            }
        }


# 单例获取函数
_announcement_monitor = None


def get_announcement_monitor_service() -> AnnouncementMonitorService:
    global _announcement_monitor
    if _announcement_monitor is None:
        _announcement_monitor = AnnouncementMonitorService()
    return _announcement_monitor
