# -*- coding: utf-8 -*-
"""
新闻监控中心
支持两种业务场景：
1. 市场新闻（新闻中心/实时新闻流）- 不带个股参数，获取全市场新闻
2. 个股新闻（智能分析/个股监控）- 带个股参数，获取特定股票相关新闻
"""
import asyncio
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum

from .news_cache import NewsCache, CachedNews, get_news_cache
from .stock_relation_analyzer import StockRelationAnalyzer, get_stock_relation_analyzer
from .impact_assessor import ImpactAssessor, get_impact_assessor
from .news_config import get_news_config_manager, NewsSourceType

logger = logging.getLogger(__name__)

# WebSocket 推送函数 (延迟导入避免循环依赖)
_ws_notify_news = None
_ws_notify_urgent = None

def _get_ws_notifiers():
    global _ws_notify_news, _ws_notify_urgent
    if _ws_notify_news is None:
        try:
            from backend.api.websocket_api import notify_news_update, notify_urgent_news
            _ws_notify_news = notify_news_update
            _ws_notify_urgent = notify_urgent_news
        except Exception as e:
            logger.warning(f"Failed to import WebSocket notifiers: {e}")
    return _ws_notify_news, _ws_notify_urgent

class DataSourceType(str, Enum):
    CLS = "cls"
    EASTMONEY = "eastmoney"
    SINA = "sina"
    CNINFO = "cninfo"
    BAIDU = "baidu"
    CCTV = "cctv"

@dataclass
class DataSourceConfig:
    name: str
    source_type: DataSourceType
    interval: int
    enabled: bool = True
    priority: int = 1
    last_fetch: str = ""
    fetch_count: int = 0
    error_count: int = 0

class NewsMonitorCenter:
    """
    新闻监控中心

    业务场景区分：
    - fetch_market_news(): 用于新闻中心/实时新闻流，获取全市场新闻，不调用个股接口
    - fetch_stock_news(stock_code): 用于智能分析/个股监控，获取特定股票新闻
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._cache = get_news_cache()
        self._stock_analyzer = get_stock_relation_analyzer()
        self._impact_assessor = get_impact_assessor()
        self._sentiment_engine = None
        self._config_manager = get_news_config_manager()
        self._init_sentiment_engine()
        self._sources: Dict[str, DataSourceConfig] = {
            "cls": DataSourceConfig("财联社电报", DataSourceType.CLS, 30, priority=10),
            "eastmoney": DataSourceConfig("东方财富", DataSourceType.EASTMONEY, 60, priority=8),
            "sina": DataSourceConfig("新浪财经", DataSourceType.SINA, 90, priority=7),
            "cninfo": DataSourceConfig("巨潮公告", DataSourceType.CNINFO, 300, priority=6),
        }
        self._running = False
        self._executor: Optional[ThreadPoolExecutor] = None
        self._fetch_tasks: Dict[str, asyncio.Task] = {}
        self._on_new_news: List[Callable] = []
        self._on_urgent_news: List[Callable] = []
        self._stats = {"total_fetched": 0, "total_processed": 0, "total_duplicates": 0, "start_time": None, "last_fetch_time": None}
        logger.info("NewsMonitorCenter initialized with config manager")
    
    def _init_sentiment_engine(self):
        try:
            from backend.dataflows.news.sentiment_engine import get_sentiment_engine
            self._sentiment_engine = get_sentiment_engine()
        except Exception as e:
            logger.warning(f"Failed to load sentiment engine: {e}")
    
    async def start(self):
        if self._running:
            return
        self._running = True
        self._stats["start_time"] = datetime.now().isoformat()
        # 增加线程池大小以避免阻塞
        self._executor = ThreadPoolExecutor(max_workers=8, thread_name_prefix="news_")
        for source_id, config in self._sources.items():
            if config.enabled:
                task = asyncio.create_task(self._fetch_loop(source_id))
                self._fetch_tasks[source_id] = task
        logger.info(f"NewsMonitorCenter started with {len(self._fetch_tasks)} sources")
    
    async def stop(self):
        self._running = False
        for task in self._fetch_tasks.values():
            task.cancel()
        self._fetch_tasks.clear()
        if self._executor:
            self._executor.shutdown(wait=False)
            self._executor = None
        self._cache.save_to_file()
        logger.info("NewsMonitorCenter stopped")
    
    async def _fetch_loop(self, source_id: str):
        config = self._sources.get(source_id)
        if not config:
            return
        while self._running:
            try:
                await self._fetch_source(source_id)
                config.last_fetch = datetime.now().isoformat()
                config.fetch_count += 1
            except Exception as e:
                config.error_count += 1
                logger.error(f"Fetch error for {source_id}: {e}")
            await asyncio.sleep(config.interval)

    async def _fetch_source(self, source_id: str):
        config = self._sources.get(source_id)
        if not config:
            return
        news_list = []
        try:
            if config.source_type == DataSourceType.CLS:
                news_list = await self._fetch_cls()
            elif config.source_type == DataSourceType.EASTMONEY:
                news_list = await self._fetch_eastmoney()
            elif config.source_type == DataSourceType.SINA:
                news_list = await self._fetch_sina()
            elif config.source_type == DataSourceType.CNINFO:
                news_list = await self._fetch_cninfo()
        except Exception as e:
            logger.error(f"Fetch {source_id} failed: {e}")
            return
        if news_list:
            await self._process_news(news_list, source_id)
    
    async def _fetch_cls(self) -> List[Dict]:
        """获取财联社电报"""
        try:
            import akshare as ak
            loop = asyncio.get_event_loop()
            news_list = []

            # 财联社全球资讯 stock_info_global_cls
            try:
                df = await loop.run_in_executor(self._executor, ak.stock_info_global_cls)
                if df is not None and not df.empty:
                    for _, row in df.iterrows():
                        title = str(row.get("标题", ""))
                        if title:
                            news_list.append({
                                "title": title,
                                "content": str(row.get("内容", ""))[:1000],
                                "pub_time": str(row.get("发布日期", "")) + " " + str(row.get("发布时间", "")),
                                "source": "财联社",
                                "url": ""
                            })
                    logger.info(f"财联社电报获取: {len(news_list)}条")
            except Exception as e:
                logger.debug(f"财联社失败: {e}")

            return news_list
        except Exception as e:
            logger.error(f"Fetch CLS failed: {e}")
            return []

    async def _fetch_eastmoney(self) -> List[Dict]:
        """
        获取东方财富新闻 - 包含多个接口:
        1. stock_info_global_em - 东方财富全球资讯
        2. stock_news_em - 个股新闻(多只股票)
        3. stock_info_cjzc_em - 财经早餐
        4. stock_info_global_futu - 富途牛牛
        5. stock_info_global_ths - 同花顺
        6. stock_info_global_sina - 新浪财经
        7. stock_js_weibo_report - 微博热议
        8. news_cctv - 新闻联播
        9. news_economic_baidu - 百度财经
        """
        try:
            import akshare as ak
            loop = asyncio.get_event_loop()
            news_list = []

            # 1. 东方财富全球资讯 stock_info_global_em
            try:
                df = await loop.run_in_executor(self._executor, ak.stock_info_global_em)
                if df is not None and not df.empty:
                    for _, row in df.iterrows():
                        title = str(row.get("标题", ""))
                        if title:
                            news_list.append({
                                "title": title,
                                "content": str(row.get("摘要", row.get("内容", "")))[:1000],
                                "pub_time": str(row.get("发布时间", "")),
                                "source": "东方财富",
                                "url": str(row.get("链接", ""))
                            })
                    logger.info(f"东方财富全球资讯: {len(news_list)}条")
            except Exception as e:
                logger.debug(f"stock_info_global_em失败: {e}")

            # 2. 个股新闻 stock_news_em - 多只热门股票
            hot_stocks = [
                "000001", "600519", "000858", "601318", "600036", "000333", "002594", "300750",
                "600000", "601166", "000002", "600030", "601398", "600016", "601288", "000651",
                "600276", "000725", "601012", "600887", "000568", "002415", "600309", "601888",
                "002304", "000063", "601601", "600900", "000100", "002475"
            ]
            stock_news_count = 0
            for symbol in hot_stocks:
                try:
                    df = await loop.run_in_executor(self._executor, lambda s=symbol: ak.stock_news_em(symbol=s))
                    if df is not None and not df.empty:
                        for _, row in df.iterrows():
                            title = str(row.get("新闻标题", ""))
                            if title:
                                news_list.append({
                                    "title": title,
                                    "content": str(row.get("新闻内容", ""))[:1000],
                                    "pub_time": str(row.get("发布时间", "")),
                                    "source": f"东财个股",
                                    "url": str(row.get("新闻链接", ""))
                                })
                                stock_news_count += 1
                except Exception as e:
                    logger.debug(f"stock_news_em({symbol})失败: {e}")
                    continue
            if stock_news_count > 0:
                logger.info(f"东财个股新闻: {stock_news_count}条")

            # 3. 财经早餐 stock_info_cjzc_em
            try:
                df = await loop.run_in_executor(self._executor, ak.stock_info_cjzc_em)
                if df is not None and not df.empty:
                    count = 0
                    for _, row in df.iterrows():
                        title = str(row.get("标题", ""))
                        if title:
                            news_list.append({
                                "title": title,
                                "content": str(row.get("内容", ""))[:1000],
                                "pub_time": str(row.get("发布时间", "")),
                                "source": "财经早餐",
                                "url": ""
                            })
                            count += 1
                    logger.info(f"财经早餐: {count}条")
            except Exception as e:
                logger.debug(f"stock_info_cjzc_em失败: {e}")

            # 4. 富途牛牛 stock_info_global_futu
            try:
                df = await loop.run_in_executor(self._executor, ak.stock_info_global_futu)
                if df is not None and not df.empty:
                    count = 0
                    for _, row in df.iterrows():
                        title = str(row.get("标题", ""))
                        if title:
                            news_list.append({
                                "title": title,
                                "content": str(row.get("内容", ""))[:1000],
                                "pub_time": str(row.get("发布时间", "")),
                                "source": "富途牛牛",
                                "url": str(row.get("链接", ""))
                            })
                            count += 1
                    logger.info(f"富途牛牛: {count}条")
            except Exception as e:
                logger.debug(f"stock_info_global_futu失败: {e}")

            # 5. 同花顺 stock_info_global_ths
            try:
                df = await loop.run_in_executor(self._executor, ak.stock_info_global_ths)
                if df is not None and not df.empty:
                    count = 0
                    for _, row in df.iterrows():
                        title = str(row.get("标题", ""))
                        if title:
                            news_list.append({
                                "title": title,
                                "content": str(row.get("内容", ""))[:1000],
                                "pub_time": str(row.get("发布时间", "")),
                                "source": "同花顺",
                                "url": str(row.get("链接", ""))
                            })
                            count += 1
                    logger.info(f"同花顺: {count}条")
            except Exception as e:
                logger.debug(f"stock_info_global_ths失败: {e}")

            # 6. 新浪财经 stock_info_global_sina - 列名: ['时间', '内容']
            try:
                df = await loop.run_in_executor(self._executor, ak.stock_info_global_sina)
                if df is not None and not df.empty:
                    count = 0
                    for _, row in df.iterrows():
                        # 新浪财经返回的列是 ['时间', '内容']，没有标题字段
                        content = str(row.get("内容", ""))
                        if content:
                            # 使用内容前50字符作为标题
                            title = content[:50] + "..." if len(content) > 50 else content
                            news_list.append({
                                "title": title,
                                "content": content[:1000],
                                "pub_time": str(row.get("时间", "")),
                                "source": "新浪财经",
                                "url": ""
                            })
                            count += 1
                    logger.info(f"新浪财经: {count}条")
            except Exception as e:
                logger.debug(f"stock_info_global_sina失败: {e}")

            # 7. 微博热议 stock_js_weibo_report
            try:
                df = await loop.run_in_executor(self._executor, ak.stock_js_weibo_report)
                if df is not None and not df.empty:
                    count = 0
                    for _, row in df.iterrows():
                        # 微博热议格式: name(股票名称), rate(涨跌幅)
                        stock_name = str(row.get("name", row.get("股票", "")))
                        rate = row.get("rate", row.get("涨跌幅", 0))
                        if stock_name:
                            # 格式化涨跌幅
                            try:
                                rate_val = float(rate)
                                rate_str = f"+{rate_val:.2f}%" if rate_val >= 0 else f"{rate_val:.2f}%"
                            except:
                                rate_str = str(rate)
                            news_list.append({
                                "title": f"[微博热议] {stock_name} {rate_str}",
                                "content": f"微博股票热议榜，当前涨跌幅: {rate_str}",
                                "pub_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "source": "微博热议",
                                "url": ""
                            })
                            count += 1
                    logger.info(f"微博热议: {count}条")
            except Exception as e:
                logger.debug(f"stock_js_weibo_report失败: {e}")

            # 8. 新闻联播 news_cctv
            try:
                today = datetime.now().strftime('%Y%m%d')
                df = await loop.run_in_executor(self._executor, lambda: ak.news_cctv(date=today))
                if df is not None and not df.empty:
                    count = 0
                    for _, row in df.iterrows():
                        title = str(row.get("title", ""))
                        if title:
                            news_list.append({
                                "title": title,
                                "content": str(row.get("content", ""))[:1000],
                                "pub_time": str(row.get("date", today)),
                                "source": "新闻联播",
                                "url": ""
                            })
                            count += 1
                    logger.info(f"新闻联播: {count}条")
            except Exception as e:
                logger.debug(f"news_cctv失败: {e}")

            # 9. 百度财经 news_economic_baidu - 列名: ['国家', '时间', '地区', '事件', '今值', '预期', '前值', '重要性']
            try:
                df = await loop.run_in_executor(self._executor, ak.news_economic_baidu)
                if df is not None and not df.empty:
                    count = 0
                    for _, row in df.iterrows():
                        # 百度财经返回的是经济日历数据，使用'事件'作为标题
                        event = str(row.get("事件", ""))
                        if event:
                            country = str(row.get("国家", ""))
                            title = f"[{country}] {event}" if country else event
                            # 组合今值/预期/前值/重要性作为内容
                            today_val = row.get("今值", "")
                            expect_val = row.get("预期", "")
                            prev_val = row.get("前值", "")
                            importance = row.get("重要性", "")
                            content = f"今值: {today_val} | 预期: {expect_val} | 前值: {prev_val} | 重要性: {importance}"
                            news_list.append({
                                "title": title,
                                "content": content,
                                "pub_time": str(row.get("时间", "")),
                                "source": "百度财经",
                                "url": ""
                            })
                            count += 1
                    logger.info(f"百度财经: {count}条")
            except Exception as e:
                logger.debug(f"news_economic_baidu失败: {e}")

            logger.info(f"东方财富源总计: {len(news_list)}条")
            return news_list
        except Exception as e:
            logger.error(f"Fetch eastmoney failed: {e}")
            return []

    async def _fetch_sina(self) -> List[Dict]:
        """
        获取新浪财经新闻 - 包含:
        1. 更多个股新闻
        2. 东方财富公告
        """
        try:
            import akshare as ak
            loop = asyncio.get_event_loop()
            news_list = []

            # 1. 更多个股新闻
            more_stocks = [
                "600519", "000858", "601318", "000001", "600036",
                "601166", "000002", "600030", "601398", "600016",
                "601288", "000651", "600276", "000725", "601012",
                "300059", "002230", "600104", "000538", "002352"
            ]
            stock_news_count = 0
            for symbol in more_stocks:
                try:
                    df = await loop.run_in_executor(self._executor, lambda s=symbol: ak.stock_news_em(symbol=s))
                    if df is not None and not df.empty:
                        for _, row in df.iterrows():
                            title = str(row.get("新闻标题", ""))
                            if title:
                                news_list.append({
                                    "title": title,
                                    "content": str(row.get("新闻内容", ""))[:1000],
                                    "pub_time": str(row.get("发布时间", "")),
                                    "source": f"新浪个股",
                                    "url": str(row.get("新闻链接", ""))
                                })
                                stock_news_count += 1
                except Exception as e:
                    logger.debug(f"新浪个股({symbol})失败: {e}")
                    continue
            if stock_news_count > 0:
                logger.info(f"新浪个股新闻: {stock_news_count}条")

            # 2. 东方财富公告 (作为新浪源的补充)
            try:
                # 尝试获取公告数据
                df = await loop.run_in_executor(self._executor, lambda: ak.stock_notice_report(symbol="全部", date="20241230"))
                if df is not None and not df.empty:
                    count = 0
                    for _, row in df.iterrows():
                        title = str(row.get("公告标题", row.get("标题", "")))
                        if title:
                            news_list.append({
                                "title": title,
                                "content": str(row.get("公告内容", ""))[:1000],
                                "pub_time": str(row.get("公告日期", "")),
                                "source": "东财公告",
                                "url": ""
                            })
                            count += 1
                    logger.info(f"东财公告: {count}条")
            except Exception as e:
                logger.debug(f"东财公告失败: {e}")

            logger.info(f"新浪财经源总计: {len(news_list)}条")
            return news_list
        except Exception as e:
            logger.error(f"Fetch sina failed: {e}")
            return []

    async def _fetch_eastmoney_global(self) -> List[Dict]:
        """获取东财全球资讯 - 已在 _fetch_eastmoney 中实现，这里作为补充"""
        try:
            import akshare as ak
            loop = asyncio.get_event_loop()
            news_list = []

            # 新浪财经新闻
            try:
                df = await loop.run_in_executor(self._executor, ak.stock_news_em, "000001")
                if df is not None and not df.empty:
                    for _, row in df.iterrows():
                        title = str(row.get("新闻标题", ""))
                        if title:
                            news_list.append({
                                "title": title,
                                "content": str(row.get("新闻内容", ""))[:1000],
                                "pub_time": str(row.get("发布时间", "")),
                                "source": "东财全球",
                                "url": str(row.get("新闻链接", ""))
                            })
                    logger.info(f"东财全球获取: {len(news_list)}条")
            except Exception as e:
                logger.debug(f"东财全球获取失败: {e}")

            return news_list
        except Exception as e:
            logger.error(f"Fetch eastmoney global failed: {e}")
            return []

    async def _fetch_cninfo(self) -> List[Dict]:
        """获取巨潮资讯网数据（使用官方API - 免费接口）"""
        try:
            from backend.dataflows.announcement.cninfo_api import get_cninfo_api_client, CninfoConfig

            # 检查是否配置了巨潮API
            if not CninfoConfig.is_configured():
                logger.debug("巨潮API未配置，跳过获取")
                return []

            client = get_cninfo_api_client()
            news_list = []

            # 1. 获取最新公告信息 (p_info3015) - 免费可用
            try:
                # 获取当天的公告
                today = datetime.now().strftime('%Y-%m-%d')
                announcement_result = await client.get_announcement_info(
                    start_date=today,
                    end_date=today,
                    page_size=1000
                )
                if announcement_result.get('success') and announcement_result.get('data'):
                    for item in announcement_result['data']:  # 不限制
                        title = item.get('F002V', '')  # 公告标题
                        if not title:
                            continue
                        pub_date = item.get('F001D', '')  # 公告日期
                        pdf_url = item.get('F003V', '')  # PDF地址
                        stock_code = item.get('SECCODE', '')
                        stock_name = item.get('SECNAME', '')
                        market = item.get('F010V', '')  # 市场名称
                        category = item.get('F006V', '')  # 信息分类

                        # 判断公告重要性
                        importance = 'low'
                        urgency = 'low'
                        if any(kw in title for kw in ['业绩预告', '业绩快报', '重大', '停牌', '复牌', '风险提示']):
                            importance = 'high'
                            urgency = 'high'
                        elif any(kw in title for kw in ['年报', '季报', '中报', '分红', '增持', '减持']):
                            importance = 'medium'
                            urgency = 'medium'

                        news_list.append({
                            "title": f"[{stock_name or '公告'}] {title}",
                            "content": f"证券代码: {stock_code} | 市场: {market} | 分类: {category}",
                            "pub_time": pub_date,
                            "source": "巨潮公告",
                            "url": pdf_url,
                            "announcement_type": "announcement",
                            "importance": importance,
                            "urgency": urgency,
                            "related_stocks": [stock_code] if stock_code else []
                        })
            except Exception as e:
                logger.warning(f"获取公告信息失败: {e}")

            # 2. 获取上市状态变动 (p_stock2117) - 免费可用，重要信息
            # 注意：此接口返回所有历史数据，只取最近100条
            try:
                status_result = await client.get_listing_status_changes()
                if status_result.get('success') and status_result.get('data'):
                    # 只取最近100条（按时间倒序）
                    data = status_result['data'][:100]
                    for item in data:
                        stock_code = item.get('SECCODE', '')
                        stock_name = item.get('SECNAME', '')
                        org_name = item.get('ORGNAME', '')
                        change_date = item.get('VARYDATE', '')
                        status = item.get('F002V', '')  # 上市状态
                        change_type = item.get('F006V', '')  # 变更类型
                        reason = item.get('F004V', '')  # 变更原因

                        if not stock_code or not change_type:
                            continue

                        # 判断重要性
                        urgency = 'medium'
                        if any(kw in str(change_type) for kw in ['退市', '暂停上市', '终止上市']):
                            urgency = 'critical'
                        elif any(kw in str(change_type) for kw in ['ST', '风险警示', '停牌']):
                            urgency = 'high'

                        news_list.append({
                            "title": f"[上市状态] {stock_name}({stock_code}) {change_type}",
                            "content": f"公司: {org_name} | 状态: {status} | 原因: {reason or '无'}",
                            "pub_time": change_date,
                            "source": "巨潮状态变动",
                            "url": "",
                            "announcement_type": "status_change",
                            "importance": "high" if urgency in ['critical', 'high'] else "medium",
                            "urgency": urgency,
                            "related_stocks": [stock_code] if stock_code else []
                        })
            except Exception as e:
                logger.warning(f"获取上市状态变动失败: {e}")

            if news_list:
                logger.info(f"从巨潮官方API获取 {len(news_list)} 条数据")
            return news_list

        except Exception as e:
            logger.error(f"Fetch cninfo failed: {e}")
            return []

    def _get_monitored_stocks(self) -> List[str]:
        """获取当前监控的股票列表"""
        try:
            # 尝试从监控服务获取
            from backend.services.realtime_monitor_service import get_realtime_monitor_service
            monitor = get_realtime_monitor_service()
            if hasattr(monitor, 'config') and monitor.config:
                stocks = monitor.config.get('stocks', [])
                if stocks:
                    return stocks
        except:
            pass
        # 默认返回一些热门股票
        return ["600519.SH", "000858.SZ", "601318.SH", "000001.SZ", "600036.SH"]

    def _get_monitored_stock_codes(self) -> Dict[str, str]:
        """获取监控股票代码映射 {纯代码: ts_code}"""
        try:
            from backend.services.alert_service import get_alert_service
            alert_service = get_alert_service()
            monitored = alert_service.get_monitored_stocks()
            # 构建映射: 600519 -> 600519.SH
            code_map = {}
            for ts_code, info in monitored.items():
                pure_code = ts_code.split('.')[0]
                code_map[pure_code] = ts_code
                # 也添加股票名称映射
                if info.get('name'):
                    code_map[info['name']] = ts_code
            return code_map
        except Exception as e:
            logger.debug(f"Failed to get monitored stock codes: {e}")
            return {}

    def _match_monitored_stocks(self, related_stocks: List[str], monitored_codes: Dict[str, str]) -> List[Dict]:
        """匹配新闻关联的股票与监控股票"""
        matched = []
        for stock in related_stocks:
            # 清理股票代码
            clean_code = str(stock).replace('.SH', '').replace('.SZ', '').replace('.BJ', '')
            clean_code = clean_code.replace('SH', '').replace('SZ', '').replace('BJ', '')

            if clean_code in monitored_codes:
                ts_code = monitored_codes[clean_code]
                matched.append({
                    'ts_code': ts_code,
                    'code': clean_code
                })
        return matched

    async def _create_alerts_for_monitored_stocks(self, news_list: List[Dict]):
        """为监控股票创建预警"""
        try:
            from backend.services.alert_service import get_alert_service
            alert_service = get_alert_service()

            for news in news_list:
                matched_stocks = news.get('matched_monitored_stocks', [])
                urgency = news.get('urgency', 'low')

                # 只为中等以上紧急程度的新闻创建预警
                if urgency not in ['critical', 'high', 'medium']:
                    continue

                for stock_info in matched_stocks:
                    ts_code = stock_info.get('ts_code', '')
                    stock_data = alert_service.get_stock_info(ts_code)
                    stock_name = stock_data.get('name', '') if stock_data else ''

                    await alert_service.create_alert_from_news(
                        news=news,
                        stock_code=ts_code,
                        stock_name=stock_name
                    )

            logger.info(f"Created alerts for {len(news_list)} monitored stock news")

        except Exception as e:
            logger.error(f"Failed to create alerts for monitored stocks: {e}")
    
    async def _process_news(self, news_list: List[Dict], source_id: str):
        """处理新闻列表 - 将CPU密集型操作移到线程池避免阻塞"""
        new_count = 0
        urgent_news = []
        monitored_stock_news = []  # 与监控股票相关的新闻
        loop = asyncio.get_event_loop()

        # 获取监控股票列表
        monitored_codes = self._get_monitored_stock_codes()

        for news_data in news_list:
            title = news_data.get("title", "")
            content = news_data.get("content", "")
            if not title:
                continue
            if self._cache.is_duplicate(title, news_data.get("pub_time", "")):
                self._stats["total_duplicates"] += 1
                continue

            # 将CPU密集型操作移到线程池中执行
            try:
                sentiment_result, related_stocks, impact = await loop.run_in_executor(
                    self._executor,
                    self._analyze_news_sync,
                    title,
                    content
                )
            except Exception as e:
                logger.debug(f"News analysis failed: {e}")
                sentiment_result = {"sentiment": "neutral", "score": 50, "urgency": "low"}
                related_stocks = []
                impact = type('Impact', (), {'urgency': 'low', 'score': 0})()

            enriched_news = {**news_data, "sentiment": sentiment_result.get("sentiment", "neutral"), "sentiment_score": sentiment_result.get("score", 50), "urgency": impact.urgency, "keywords": sentiment_result.get("keywords", []), "related_stocks": related_stocks, "impact_score": impact.score}
            result = self._cache.add_news_batch([enriched_news])
            if result["added"] > 0:
                new_count += 1
                self._stats["total_processed"] += 1
                if impact.urgency in ["critical", "high"]:
                    urgent_news.append(enriched_news)

                # 检查是否与监控股票相关
                if monitored_codes and related_stocks:
                    matched_codes = self._match_monitored_stocks(related_stocks, monitored_codes)
                    if matched_codes:
                        enriched_news['matched_monitored_stocks'] = matched_codes
                        monitored_stock_news.append(enriched_news)

        self._stats["total_fetched"] += len(news_list)
        self._stats["last_fetch_time"] = datetime.now().isoformat()
        if new_count > 0:
            logger.info(f"[{source_id}] Processed {new_count} new news")
            for callback in self._on_new_news:
                try:
                    callback(new_count, source_id)
                except:
                    pass
        if urgent_news:
            logger.warning(f"[{source_id}] Found {len(urgent_news)} urgent news!")
            for callback in self._on_urgent_news:
                try:
                    callback(urgent_news)
                except:
                    pass
            # WebSocket 推送紧急新闻
            ws_notify, ws_urgent = _get_ws_notifiers()
            if ws_urgent:
                try:
                    asyncio.create_task(ws_urgent(urgent_news))
                except:
                    pass
            # 发送通知（企业微信/钉钉/邮件等）
            try:
                asyncio.create_task(self._send_urgent_notification(urgent_news))
            except:
                pass

        # 处理与监控股票相关的新闻 - 创建预警
        if monitored_stock_news:
            logger.info(f"[{source_id}] Found {len(monitored_stock_news)} news related to monitored stocks")
            asyncio.create_task(self._create_alerts_for_monitored_stocks(monitored_stock_news))

    def _analyze_news_sync(self, title: str, content: str):
        """同步分析新闻（在线程池中执行）"""
        sentiment_result = {"sentiment": "neutral", "score": 50, "urgency": "low"}
        if self._sentiment_engine:
            try:
                sentiment_result = self._sentiment_engine.analyze(title, content)
            except:
                pass
        related_stocks = self._stock_analyzer.get_related_codes(title, content)
        impact = self._impact_assessor.assess(title, content, sentiment_result.get("score", 50))
        return sentiment_result, related_stocks, impact

    async def _send_urgent_notification(self, urgent_news: List[Dict]):
        """发送紧急新闻通知到配置的渠道"""
        try:
            from backend.services.notification_service import get_notification_service
            notification_service = get_notification_service()

            # 转换为预警格式
            alerts = []
            for news in urgent_news[:5]:  # 最多5条
                urgency = news.get('urgency', 'medium')
                level = 'critical' if urgency == 'critical' else 'high' if urgency == 'high' else 'medium'
                alerts.append({
                    'title': f"📰 {news.get('title', '重要新闻')[:50]}",
                    'message': news.get('content', '')[:200] if news.get('content') else news.get('title', ''),
                    'level': level,
                    'stock_code': ', '.join(news.get('related_stocks', [])[:3]) or '市场',
                    'suggestion': f"来源: {news.get('source', '未知')} | 情绪: {news.get('sentiment', 'neutral')}"
                })

            if alerts:
                result = await notification_service.send_alert_notification(alerts)
                if result.get('success'):
                    logger.info(f"✅ 紧急新闻通知发送成功: {len(alerts)}条")
                elif '0/0' in result.get('message', ''):
                    # 没有配置通知渠道，这是正常情况，不需要警告
                    logger.debug(f"紧急新闻通知: 未配置通知渠道，跳过发送")
                else:
                    logger.warning(f"⚠️ 紧急新闻通知发送部分失败: {result.get('message')}")
        except Exception as e:
            logger.error(f"发送紧急新闻通知失败: {e}")

    def get_latest_news(self, limit: int = 100, **filters) -> List[Dict]:
        news_list = self._cache.get_latest_news(limit, **filters)
        return [n.to_dict() for n in news_list]
    
    def get_urgent_news(self, limit: int = 20) -> List[Dict]:
        news_list = self._cache.get_urgent_news(limit)
        return [n.to_dict() for n in news_list]
    
    def get_news_for_stock(self, stock_code: str, limit: int = 30) -> List[Dict]:
        news_list = self._cache.get_news_for_stock(stock_code, limit)
        return [n.to_dict() for n in news_list]
    
    def get_stats(self) -> Dict[str, Any]:
        cache_stats = self._cache.get_stats()
        source_stats = {sid: {"name": cfg.name, "interval": cfg.interval, "enabled": cfg.enabled, "last_fetch": cfg.last_fetch, "fetch_count": cfg.fetch_count, "error_count": cfg.error_count} for sid, cfg in self._sources.items()}
        return {**self._stats, "cache": cache_stats, "sources": source_stats, "running": self._running}
    
    def set_source_interval(self, source_id: str, interval: int):
        if source_id in self._sources:
            self._sources[source_id].interval = max(10, interval)
            logger.info(f"Set {source_id} interval to {interval}s")
    
    def enable_source(self, source_id: str, enabled: bool = True):
        if source_id in self._sources:
            self._sources[source_id].enabled = enabled
            logger.info(f"Set {source_id} enabled={enabled}")
    
    def on_new_news(self, callback: Callable):
        self._on_new_news.append(callback)
    
    def on_urgent_news(self, callback: Callable):
        self._on_urgent_news.append(callback)
    
    async def fetch_now(self, source_id: str = None):
        if source_id:
            await self._fetch_source(source_id)
        else:
            for sid in self._sources:
                await self._fetch_source(sid)
    
    def cleanup(self):
        return self._cache.cleanup_expired()

    # ==================== 市场新闻获取（新闻中心/实时新闻流）====================

    async def fetch_market_news(self) -> List[Dict]:
        """
        获取市场新闻（用于新闻中心/实时新闻流）
        只调用市场级别的新闻接口，不调用个股新闻接口

        包含接口：
        1. stock_info_global_em - 东方财富全球资讯
        2. stock_info_global_cls - 财联社全球资讯
        3. stock_info_global_futu - 富途牛牛
        4. stock_info_global_ths - 同花顺
        5. stock_info_global_sina - 新浪财经
        6. stock_js_weibo_report - 微博热议
        7. stock_info_cjzc_em - 财经早餐
        8. news_cctv - 新闻联播
        9. news_economic_baidu - 百度财经
        10. 巨潮市场公告（不带个股参数）
        """
        try:
            import akshare as ak
            loop = asyncio.get_event_loop()
            news_list = []
            config = self._config_manager.config

            # 1. 东方财富全球资讯
            source_cfg = config.market_sources.get(NewsSourceType.EASTMONEY_GLOBAL.value)
            if source_cfg and source_cfg.enabled:
                try:
                    df = await loop.run_in_executor(self._executor, ak.stock_info_global_em)
                    if df is not None and not df.empty:
                        for _, row in df.iterrows():
                            title = str(row.get("标题", ""))
                            if title:
                                news_list.append({
                                    "title": title,
                                    "content": str(row.get("摘要", row.get("内容", "")))[:1000],
                                    "pub_time": str(row.get("发布时间", "")),
                                    "source": source_cfg.name,  # 使用配置中的名称
                                    "url": str(row.get("链接", ""))
                                })
                        logger.info(f"东方财富全球资讯: {len([n for n in news_list if n['source'] == source_cfg.name])}条")
                except Exception as e:
                    logger.debug(f"stock_info_global_em失败: {e}")

            # 2. 财联社全球资讯
            source_cfg = config.market_sources.get(NewsSourceType.CLS_GLOBAL.value)
            if source_cfg and source_cfg.enabled:
                try:
                    df = await loop.run_in_executor(self._executor, ak.stock_info_global_cls)
                    if df is not None and not df.empty:
                        count = 0
                        for _, row in df.iterrows():
                            title = str(row.get("标题", ""))
                            if title:
                                news_list.append({
                                    "title": title,
                                    "content": str(row.get("内容", ""))[:1000],
                                    "pub_time": str(row.get("发布日期", "")) + " " + str(row.get("发布时间", "")),
                                    "source": source_cfg.name,  # 使用配置中的名称
                                    "url": ""
                                })
                                count += 1
                        logger.info(f"财联社电报: {count}条")
                except Exception as e:
                    logger.debug(f"stock_info_global_cls失败: {e}")

            # 3. 富途牛牛
            source_cfg = config.market_sources.get(NewsSourceType.FUTU_GLOBAL.value)
            if source_cfg and source_cfg.enabled:
                try:
                    df = await loop.run_in_executor(self._executor, ak.stock_info_global_futu)
                    if df is not None and not df.empty:
                        count = 0
                        for _, row in df.iterrows():
                            title = str(row.get("标题", ""))
                            if title:
                                news_list.append({
                                    "title": title,
                                    "content": str(row.get("内容", ""))[:1000],
                                    "pub_time": str(row.get("发布时间", "")),
                                    "source": source_cfg.name,  # 使用配置中的名称
                                    "url": str(row.get("链接", ""))
                                })
                                count += 1
                        logger.info(f"富途牛牛: {count}条")
                except Exception as e:
                    logger.debug(f"stock_info_global_futu失败: {e}")

            # 4. 同花顺
            source_cfg = config.market_sources.get(NewsSourceType.THS_GLOBAL.value)
            if source_cfg and source_cfg.enabled:
                try:
                    df = await loop.run_in_executor(self._executor, ak.stock_info_global_ths)
                    if df is not None and not df.empty:
                        count = 0
                        for _, row in df.iterrows():
                            title = str(row.get("标题", ""))
                            if title:
                                news_list.append({
                                    "title": title,
                                    "content": str(row.get("内容", ""))[:1000],
                                    "pub_time": str(row.get("发布时间", "")),
                                    "source": source_cfg.name,  # 使用配置中的名称
                                    "url": str(row.get("链接", ""))
                                })
                                count += 1
                        logger.info(f"同花顺: {count}条")
                except Exception as e:
                    logger.debug(f"stock_info_global_ths失败: {e}")

            # 5. 新浪财经 - 列名: ['时间', '内容']
            source_cfg = config.market_sources.get(NewsSourceType.SINA_GLOBAL.value)
            if source_cfg and source_cfg.enabled:
                try:
                    df = await loop.run_in_executor(self._executor, ak.stock_info_global_sina)
                    if df is not None and not df.empty:
                        count = 0
                        for _, row in df.iterrows():
                            content = str(row.get("内容", ""))
                            if content:
                                # 新浪财经只有内容，没有标题，截取前50字作为标题
                                title = content[:50] + "..." if len(content) > 50 else content
                                news_list.append({
                                    "title": title,
                                    "content": content[:1000],
                                    "pub_time": str(row.get("时间", "")),
                                    "source": source_cfg.name,
                                    "url": ""
                                })
                                count += 1
                        logger.info(f"新浪财经: {count}条")
                except Exception as e:
                    logger.debug(f"stock_info_global_sina失败: {e}")

            # 6. 微博热议
            source_cfg = config.market_sources.get(NewsSourceType.WEIBO_HOT.value)
            if source_cfg and source_cfg.enabled:
                try:
                    df = await loop.run_in_executor(self._executor, ak.stock_js_weibo_report)
                    if df is not None and not df.empty:
                        count = 0
                        for _, row in df.iterrows():
                            stock_name = str(row.get("name", row.get("股票", "")))
                            rate = row.get("rate", row.get("涨跌幅", 0))
                            if stock_name:
                                # 格式化涨跌幅
                                try:
                                    rate_val = float(rate)
                                    rate_str = f"+{rate_val:.2f}%" if rate_val >= 0 else f"{rate_val:.2f}%"
                                except:
                                    rate_str = str(rate)
                                news_list.append({
                                    "title": f"[微博热议] {stock_name} {rate_str}",
                                    "content": f"微博股票热议榜，当前涨跌幅: {rate_str}",
                                    "pub_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "source": source_cfg.name,  # 使用配置中的名称
                                    "url": ""
                                })
                                count += 1
                        logger.info(f"微博热议: {count}条")
                except Exception as e:
                    logger.debug(f"stock_js_weibo_report失败: {e}")

            # 7. 财经早餐
            source_cfg = config.market_sources.get(NewsSourceType.CJZC.value)
            if source_cfg and source_cfg.enabled:
                try:
                    df = await loop.run_in_executor(self._executor, ak.stock_info_cjzc_em)
                    if df is not None and not df.empty:
                        count = 0
                        for _, row in df.iterrows():
                            title = str(row.get("标题", ""))
                            if title:
                                news_list.append({
                                    "title": title,
                                    "content": str(row.get("内容", ""))[:1000],
                                    "pub_time": str(row.get("发布时间", "")),
                                    "source": source_cfg.name,  # 使用配置中的名称
                                    "url": ""
                                })
                                count += 1
                        logger.info(f"财经早餐: {count}条")
                except Exception as e:
                    logger.debug(f"stock_info_cjzc_em失败: {e}")

            # 8. 新闻联播
            source_cfg = config.market_sources.get(NewsSourceType.CCTV.value)
            if source_cfg and source_cfg.enabled:
                try:
                    today = datetime.now().strftime('%Y%m%d')
                    df = await loop.run_in_executor(self._executor, lambda: ak.news_cctv(date=today))
                    if df is not None and not df.empty:
                        count = 0
                        for _, row in df.iterrows():
                            title = str(row.get("title", ""))
                            if title:
                                news_list.append({
                                    "title": title,
                                    "content": str(row.get("content", ""))[:1000],
                                    "pub_time": str(row.get("date", today)),
                                    "source": source_cfg.name,  # 使用配置中的名称
                                    "url": ""
                                })
                                count += 1
                        logger.info(f"新闻联播: {count}条")
                except Exception as e:
                    logger.debug(f"news_cctv失败: {e}")

            # 9. 百度财经 - 列名: ['国家', '时间', '地区', '事件', '今值', '预期', '前值', '重要性']
            source_cfg = config.market_sources.get(NewsSourceType.BAIDU.value)
            if source_cfg and source_cfg.enabled:
                try:
                    df = await loop.run_in_executor(self._executor, ak.news_economic_baidu)
                    if df is not None and not df.empty:
                        count = 0
                        for _, row in df.iterrows():
                            event = str(row.get("事件", ""))
                            if event:
                                # 构建标题：地区 + 事件
                                country = str(row.get("国家", ""))
                                region = str(row.get("地区", ""))
                                title = f"[{country}] {event}" if country else event
                                # 构建内容：今值、预期、前值
                                today_val = row.get("今值", "")
                                expect_val = row.get("预期", "")
                                prev_val = row.get("前值", "")
                                importance = row.get("重要性", "")
                                content = f"今值: {today_val} | 预期: {expect_val} | 前值: {prev_val} | 重要性: {importance}"
                                news_list.append({
                                    "title": title,
                                    "content": content,
                                    "pub_time": str(row.get("时间", "")),
                                    "source": source_cfg.name,
                                    "url": ""
                                })
                                count += 1
                        logger.info(f"百度财经: {count}条")
                except Exception as e:
                    logger.debug(f"news_economic_baidu失败: {e}")

            # 10. 巨潮市场公告（不带个股参数）
            source_cfg = config.market_sources.get(NewsSourceType.CNINFO_MARKET.value)
            if source_cfg and source_cfg.enabled:
                cninfo_news = await self._fetch_cninfo_market()
                news_list.extend(cninfo_news)

            # 11. 巨潮新闻数据（p_info3030）
            source_cfg = config.market_sources.get(NewsSourceType.CNINFO_NEWS.value)
            if source_cfg and source_cfg.enabled:
                cninfo_news_data = await self._fetch_cninfo_news(days_back=source_cfg.days_back)
                news_list.extend(cninfo_news_data)

            # 12. 巨潮研报摘要（p_info3097_inc）- VIP接口
            source_cfg = config.market_sources.get(NewsSourceType.CNINFO_RESEARCH.value)
            if source_cfg and source_cfg.enabled:
                research_data = await self._fetch_cninfo_research(limit=source_cfg.limit)
                news_list.extend(research_data)

            # 13. 巨潮高管变动（p_stock2102）
            source_cfg = config.market_sources.get(NewsSourceType.CNINFO_MANAGEMENT.value)
            if source_cfg and source_cfg.enabled:
                management_data = await self._fetch_cninfo_management(limit=source_cfg.limit)
                news_list.extend(management_data)

            # 对所有新闻进行情绪分析
            if news_list and self._sentiment_engine:
                for news_item in news_list:
                    if not news_item.get('sentiment'):  # 只分析没有情绪的新闻
                        try:
                            title = news_item.get('title', '')
                            content = news_item.get('content', '')
                            sentiment_result = self._sentiment_engine.analyze(title, content)
                            news_item['sentiment'] = sentiment_result.get('sentiment', 'neutral')
                            news_item['sentiment_score'] = sentiment_result.get('score', 50)
                        except Exception as e:
                            news_item['sentiment'] = 'neutral'
                            news_item['sentiment_score'] = 50

            # 保存到数据库
            if news_list:
                try:
                    from .news_storage import get_news_storage
                    storage = get_news_storage()
                    save_result = storage.save_news_batch(news_list)
                    logger.info(f"新闻已保存到数据库: 新增{save_result['saved']}条, 跳过{save_result['skipped']}条")
                except Exception as e:
                    logger.warning(f"保存新闻到数据库失败: {e}")

            logger.info(f"市场新闻获取完成，共 {len(news_list)} 条")
            return news_list

        except Exception as e:
            logger.error(f"获取市场新闻失败: {e}")
            return []

    async def _fetch_cninfo_management(self, limit: int = 100) -> List[Dict]:
        """获取巨潮高管变动（p_stock2102）"""
        try:
            from backend.dataflows.announcement.cninfo_api import get_cninfo_api_client, CninfoConfig

            if not CninfoConfig.is_configured():
                logger.debug("巨潮API未配置，跳过获取")
                return []

            client = get_cninfo_api_client()
            news_list = []

            # 获取数据源配置名称
            source_cfg = self._config_manager.config.market_sources.get(NewsSourceType.CNINFO_MANAGEMENT.value)
            source_name = source_cfg.name if source_cfg else "巨潮高管变动"

            try:
                # 获取热门股票的高管变动信息
                hot_stocks = self._config_manager.config.hot_stocks[:20]  # 取前20只热门股票
                if not hot_stocks:
                    hot_stocks = ["000001", "600519", "000858", "601318", "600036"]

                result = await client.get_management_personnel(hot_stocks, state=1)
                if result.get('success') and result.get('data'):
                    # 按公告日期排序，取最近的变动
                    data = result['data']
                    # 过滤出最近的任职变动（有离职日期或最近任职的）
                    recent_changes = []
                    for item in data:
                        declare_date = item.get('DECLAREDATE', '')
                        leave_date = item.get('F008D', '')
                        join_date = item.get('F007D', '')

                        # 如果有离职日期，说明是离职变动
                        if leave_date:
                            recent_changes.append({
                                'item': item,
                                'change_type': '离职',
                                'date': leave_date
                            })
                        # 如果任职日期在最近30天内，说明是新任职
                        elif join_date:
                            try:
                                from datetime import datetime
                                join_dt = datetime.strptime(str(join_date)[:10], '%Y-%m-%d')
                                if (datetime.now() - join_dt).days <= 30:
                                    recent_changes.append({
                                        'item': item,
                                        'change_type': '任职',
                                        'date': join_date
                                    })
                            except:
                                pass

                    # 取最近的变动
                    for change in recent_changes[:limit]:
                        item = change['item']
                        change_type = change['change_type']
                        stock_code = item.get('SECCODE', '')
                        stock_name = item.get('SECNAME', '')
                        org_name = item.get('ORGNAME', '')
                        person_name = item.get('F002V', '')
                        position = item.get('F009V', '')
                        join_date = item.get('F007D', '')
                        leave_date = item.get('F008D', '')
                        gender = item.get('F010V', '')
                        education = item.get('F011V', '')
                        resume = item.get('F019V', '')

                        if not person_name or not position:
                            continue

                        # 构建标题
                        if change_type == '离职':
                            title = f"[高管变动] {stock_name}({stock_code}) {person_name} 离任{position}"
                        else:
                            title = f"[高管变动] {stock_name}({stock_code}) {person_name} 就任{position}"

                        # 构建内容
                        content_parts = [f"公司: {org_name}"]
                        if join_date:
                            content_parts.append(f"任职日期: {join_date}")
                        if leave_date:
                            content_parts.append(f"离职日期: {leave_date}")
                        if gender:
                            content_parts.append(f"性别: {gender}")
                        if education:
                            content_parts.append(f"学历: {education}")
                        if resume:
                            content_parts.append(f"简历: {resume[:200]}...")

                        news_list.append({
                            "title": title,
                            "content": " | ".join(content_parts),
                            "pub_time": change['date'],
                            "source": source_name,  # 使用配置中的名称
                            "url": "",
                            "importance": "high",
                            "urgency": "medium",
                            "related_stocks": [stock_code] if stock_code else []
                        })

                    logger.info(f"巨潮高管变动: {len(news_list)}条")
            except Exception as e:
                logger.warning(f"获取巨潮高管变动失败: {e}")

            return news_list

        except Exception as e:
            logger.error(f"获取巨潮高管变动失败: {e}")
            return []

    async def _fetch_cninfo_news(self, days_back: int = 1, stock_code: str = '') -> List[Dict]:
        """获取巨潮新闻数据（p_info3030）"""
        try:
            from backend.dataflows.announcement.cninfo_api import get_cninfo_api_client, CninfoConfig

            if not CninfoConfig.is_configured():
                logger.debug("巨潮API未配置，跳过获取")
                return []

            client = get_cninfo_api_client()
            news_list = []

            # 获取数据源配置名称
            source_cfg = self._config_manager.config.market_sources.get(NewsSourceType.CNINFO_NEWS.value)
            source_name = source_cfg.name if source_cfg else "巨潮新闻数据(VIP)"

            try:
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=days_back-1)).strftime('%Y-%m-%d')

                result = await client.get_news_list(
                    stock_code=stock_code,
                    start_date=start_date,
                    end_date=end_date
                )
                if result.get('success') and result.get('data'):
                    for item in result['data']:
                        title = item.get('F004V', '')
                        if not title:
                            continue
                        pub_time = item.get('DECLAREDATE', '')
                        news_id = item.get('TEXTID', '')
                        sec_code = item.get('SECCODE', '')
                        keywords = item.get('F002V', '')
                        news_type = item.get('F003V', '')
                        author = item.get('F005V', '')

                        news_list.append({
                            "title": title,
                            "content": f"关键词: {keywords}" if keywords else "",
                            "pub_time": pub_time,
                            "source": source_name,  # 使用配置中的名称
                            "url": "",
                            "news_id": news_id,
                            "news_type": news_type,
                            "author": author,
                            "related_stocks": [sec_code] if sec_code else []
                        })
                    logger.info(f"巨潮新闻数据: {len(news_list)}条")
            except Exception as e:
                logger.warning(f"获取巨潮新闻数据失败: {e}")

            return news_list

        except Exception as e:
            logger.error(f"获取巨潮新闻数据失败: {e}")
            return []

    async def _fetch_cninfo_research(self, limit: int = 500) -> List[Dict]:
        """获取巨潮研报摘要（p_info3097_inc）"""
        try:
            from backend.dataflows.announcement.cninfo_api import get_cninfo_api_client, CninfoConfig

            if not CninfoConfig.is_configured():
                logger.debug("巨潮API未配置，跳过获取")
                return []

            client = get_cninfo_api_client()
            news_list = []

            # 获取数据源配置名称
            source_cfg = self._config_manager.config.market_sources.get(NewsSourceType.CNINFO_RESEARCH.value)
            source_name = source_cfg.name if source_cfg else "巨潮研报摘要(VIP)"

            try:
                result = await client.get_research_report_summary(
                    object_id=0,
                    row_count=min(limit, 2000)
                )
                if result.get('success') and result.get('data'):
                    for item in result['data']:
                        title = item.get('F002V', '')
                        if not title:
                            continue
                        content = item.get('F003V', '')
                        pub_date = item.get('F001D', '')
                        sec_code = item.get('SECCODE', '')
                        sec_name = item.get('SECNAME', '')
                        institution = item.get('F004V', '')
                        report_date = item.get('F005D', '')
                        category = item.get('F007V', '')

                        news_list.append({
                            "title": f"[研报] {title}",
                            "content": content[:500] if content else f"机构: {institution}",
                            "pub_time": pub_date,
                            "source": source_name,  # 使用配置中的名称
                            "url": "",
                            "report_date": report_date,
                            "category": category,
                            "importance": "medium",
                            "related_stocks": [sec_code] if sec_code else []
                        })
                    logger.info(f"巨潮研报摘要: {len(news_list)}条")
            except Exception as e:
                logger.warning(f"获取巨潮研报摘要失败: {e}")

            return news_list

        except Exception as e:
            logger.error(f"获取巨潮研报摘要失败: {e}")
            return []

    async def _fetch_cninfo_market(self) -> List[Dict]:
        """获取巨潮市场公告（不带个股参数）"""
        try:
            from backend.dataflows.announcement.cninfo_api import get_cninfo_api_client, CninfoConfig

            if not CninfoConfig.is_configured():
                logger.debug("巨潮API未配置，跳过获取")
                return []

            client = get_cninfo_api_client()
            news_list = []
            config = self._config_manager.config.cninfo

            # 获取数据源配置名称
            market_source_cfg = self._config_manager.config.market_sources.get(NewsSourceType.CNINFO_MARKET.value)
            source_name = market_source_cfg.name if market_source_cfg else "巨潮市场公告"

            # 获取公告信息
            if config.announcement_enabled:
                try:
                    days_back = config.announcement_days_back
                    end_date = datetime.now().strftime('%Y-%m-%d')
                    start_date = (datetime.now() - timedelta(days=days_back-1)).strftime('%Y-%m-%d')

                    announcement_result = await client.get_announcement_info(
                        start_date=start_date,
                        end_date=end_date,
                        page_size=config.announcement_page_size
                    )
                    if announcement_result.get('success') and announcement_result.get('data'):
                        for item in announcement_result['data']:
                            title = item.get('F002V', '')
                            if not title:
                                continue
                            pub_date = item.get('F001D', '')
                            pdf_url = item.get('F003V', '')
                            stock_code = item.get('SECCODE', '')
                            stock_name = item.get('SECNAME', '')
                            market = item.get('F010V', '')
                            category = item.get('F006V', '')

                            importance = 'low'
                            urgency = 'low'
                            if any(kw in title for kw in ['业绩预告', '业绩快报', '重大', '停牌', '复牌', '风险提示']):
                                importance = 'high'
                                urgency = 'high'
                            elif any(kw in title for kw in ['年报', '季报', '中报', '分红', '增持', '减持']):
                                importance = 'medium'
                                urgency = 'medium'

                            news_list.append({
                                "title": f"[{stock_name or '公告'}] {title}",
                                "content": f"证券代码: {stock_code} | 市场: {market} | 分类: {category}",
                                "pub_time": pub_date,
                                "source": source_name,  # 使用配置中的名称
                                "url": pdf_url,
                                "announcement_type": "announcement",
                                "importance": importance,
                                "urgency": urgency,
                                "related_stocks": [stock_code] if stock_code else []
                            })
                        logger.info(f"巨潮市场公告: {len(news_list)}条")
                except Exception as e:
                    logger.warning(f"获取巨潮公告信息失败: {e}")

            # 获取上市状态变动
            if config.status_change_enabled:
                try:
                    status_result = await client.get_listing_status_changes()
                    if status_result.get('success') and status_result.get('data'):
                        data = status_result['data'][:config.status_change_limit]
                        status_count = 0
                        for item in data:
                            stock_code = item.get('SECCODE', '')
                            stock_name = item.get('SECNAME', '')
                            org_name = item.get('ORGNAME', '')
                            change_date = item.get('VARYDATE', '')
                            status = item.get('F002V', '')
                            change_type = item.get('F006V', '')
                            reason = item.get('F004V', '')

                            if not stock_code or not change_type:
                                continue

                            urgency = 'medium'
                            if any(kw in str(change_type) for kw in ['退市', '暂停上市', '终止上市']):
                                urgency = 'critical'
                            elif any(kw in str(change_type) for kw in ['ST', '风险警示', '停牌']):
                                urgency = 'high'

                            news_list.append({
                                "title": f"[上市状态] {stock_name}({stock_code}) {change_type}",
                                "content": f"公司: {org_name} | 状态: {status} | 原因: {reason or '无'}",
                                "pub_time": change_date,
                                "source": source_name,  # 使用配置中的名称
                                "url": "",
                                "announcement_type": "status_change",
                                "importance": "high" if urgency in ['critical', 'high'] else "medium",
                                "urgency": urgency,
                                "related_stocks": [stock_code] if stock_code else []
                            })
                            status_count += 1
                        logger.info(f"巨潮状态变动: {status_count}条")
                except Exception as e:
                    logger.warning(f"获取上市状态变动失败: {e}")

            return news_list

        except Exception as e:
            logger.error(f"获取巨潮市场公告失败: {e}")
            return []

    # ==================== 个股新闻获取（智能分析/个股监控）====================

    async def fetch_stock_news(self, stock_code: str, stock_name: str = "") -> List[Dict]:
        """
        获取个股新闻（用于智能分析/个股监控）
        调用个股新闻接口，获取特定股票相关新闻

        包含接口：
        1. stock_news_em - 东方财富个股新闻
        2. 巨潮个股公告（带个股参数）

        Args:
            stock_code: 股票代码（6位数字，如 600519）
            stock_name: 股票名称（可选，用于日志）
        """
        try:
            import akshare as ak
            loop = asyncio.get_event_loop()
            news_list = []
            config = self._config_manager.config

            # 清理股票代码
            clean_code = stock_code.replace('.SH', '').replace('.SZ', '').replace('.BJ', '')

            # 1. 东方财富个股新闻
            source_cfg = config.stock_sources.get(NewsSourceType.STOCK_NEWS_EM.value)
            if source_cfg and source_cfg.enabled:
                try:
                    df = await loop.run_in_executor(
                        self._executor,
                        lambda: ak.stock_news_em(symbol=clean_code)
                    )
                    if df is not None and not df.empty:
                        limit = source_cfg.limit if source_cfg.limit > 0 else len(df)
                        for _, row in df.head(limit).iterrows():
                            title = str(row.get("新闻标题", ""))
                            if title:
                                news_list.append({
                                    "title": title,
                                    "content": str(row.get("新闻内容", ""))[:1000],
                                    "pub_time": str(row.get("发布时间", "")),
                                    "source": "东财个股",
                                    "url": str(row.get("新闻链接", "")),
                                    "related_stocks": [clean_code]
                                })
                        logger.info(f"东财个股新闻({stock_name or clean_code}): {len(news_list)}条")
                except Exception as e:
                    logger.debug(f"stock_news_em({clean_code})失败: {e}")

            # 2. 巨潮个股公告
            source_cfg = config.stock_sources.get(NewsSourceType.CNINFO_STOCK.value)
            if source_cfg and source_cfg.enabled:
                cninfo_news = await self._fetch_cninfo_stock(clean_code, source_cfg.days_back)
                news_list.extend(cninfo_news)

            # 3. 巨潮个股新闻（p_info3030带股票代码）
            source_cfg = config.stock_sources.get(NewsSourceType.CNINFO_STOCK_NEWS.value)
            if source_cfg and source_cfg.enabled:
                cninfo_stock_news = await self._fetch_cninfo_news(
                    days_back=source_cfg.days_back,
                    stock_code=clean_code
                )
                news_list.extend(cninfo_stock_news)

            # 对所有新闻进行情绪分析
            if news_list and self._sentiment_engine:
                for news_item in news_list:
                    if not news_item.get('sentiment'):
                        try:
                            title = news_item.get('title', '')
                            content = news_item.get('content', '')
                            sentiment_result = self._sentiment_engine.analyze(title, content)
                            news_item['sentiment'] = sentiment_result.get('sentiment', 'neutral')
                            news_item['sentiment_score'] = sentiment_result.get('score', 50)
                        except Exception as e:
                            news_item['sentiment'] = 'neutral'
                            news_item['sentiment_score'] = 50

            logger.info(f"个股新闻获取完成({stock_name or clean_code})，共 {len(news_list)} 条")
            return news_list

        except Exception as e:
            logger.error(f"获取个股新闻失败({stock_code}): {e}")
            return []

    async def _fetch_cninfo_stock(self, stock_code: str, days_back: int = 30) -> List[Dict]:
        """获取巨潮个股公告"""
        try:
            from backend.dataflows.announcement.cninfo_api import get_cninfo_api_client, CninfoConfig

            if not CninfoConfig.is_configured():
                logger.debug("巨潮API未配置，跳过获取")
                return []

            client = get_cninfo_api_client()
            news_list = []

            try:
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

                announcement_result = await client.get_announcement_info(
                    stock_code=stock_code,
                    start_date=start_date,
                    end_date=end_date,
                    page_size=100
                )
                if announcement_result.get('success') and announcement_result.get('data'):
                    for item in announcement_result['data']:
                        title = item.get('F002V', '')
                        if not title:
                            continue
                        pub_date = item.get('F001D', '')
                        pdf_url = item.get('F003V', '')
                        stock_name = item.get('SECNAME', '')
                        category = item.get('F006V', '')

                        importance = 'low'
                        urgency = 'low'
                        if any(kw in title for kw in ['业绩预告', '业绩快报', '重大', '停牌', '复牌', '风险提示']):
                            importance = 'high'
                            urgency = 'high'
                        elif any(kw in title for kw in ['年报', '季报', '中报', '分红', '增持', '减持']):
                            importance = 'medium'
                            urgency = 'medium'

                        news_list.append({
                            "title": f"[{stock_name or '公告'}] {title}",
                            "content": f"分类: {category}",
                            "pub_time": pub_date,
                            "source": "巨潮个股公告",
                            "url": pdf_url,
                            "announcement_type": "stock_announcement",
                            "importance": importance,
                            "urgency": urgency,
                            "related_stocks": [stock_code]
                        })
                    logger.info(f"巨潮个股公告({stock_code}): {len(news_list)}条")
            except Exception as e:
                logger.warning(f"获取巨潮个股公告失败({stock_code}): {e}")

            return news_list

        except Exception as e:
            logger.error(f"获取巨潮个股公告失败({stock_code}): {e}")
            return []

    async def fetch_hot_stocks_news(self) -> List[Dict]:
        """
        获取热门股票新闻（用于市场新闻中补充个股新闻）
        从配置的热门股票列表中获取新闻
        """
        try:
            import akshare as ak
            loop = asyncio.get_event_loop()
            news_list = []
            config = self._config_manager.config

            hot_stocks = config.hot_stocks
            if not hot_stocks:
                return []

            source_cfg = config.stock_sources.get(NewsSourceType.STOCK_NEWS_EM.value)
            if not source_cfg or not source_cfg.enabled:
                return []

            limit_per_stock = source_cfg.limit if source_cfg.limit > 0 else 20

            for symbol in hot_stocks:
                try:
                    df = await loop.run_in_executor(
                        self._executor,
                        lambda s=symbol: ak.stock_news_em(symbol=s)
                    )
                    if df is not None and not df.empty:
                        for _, row in df.head(limit_per_stock).iterrows():
                            title = str(row.get("新闻标题", ""))
                            if title:
                                news_list.append({
                                    "title": title,
                                    "content": str(row.get("新闻内容", ""))[:1000],
                                    "pub_time": str(row.get("发布时间", "")),
                                    "source": "东财个股",
                                    "url": str(row.get("新闻链接", "")),
                                    "related_stocks": [symbol]
                                })
                except Exception as e:
                    logger.debug(f"stock_news_em({symbol})失败: {e}")
                    continue

            logger.info(f"热门股票新闻: {len(news_list)}条 (来自{len(hot_stocks)}只股票)")
            return news_list

        except Exception as e:
            logger.error(f"获取热门股票新闻失败: {e}")
            return []

    # ==================== 配置管理 ====================

    def get_news_config(self) -> Dict:
        """获取新闻配置"""
        return self._config_manager.get_config()

    def update_news_config(self, data: Dict) -> bool:
        """更新新闻配置"""
        return self._config_manager.update_config(data)

    def update_source_config(self, source_type: str, updates: Dict) -> bool:
        """更新单个数据源配置"""
        return self._config_manager.update_source_config(source_type, updates)

    def update_cninfo_config(self, updates: Dict) -> bool:
        """更新巨潮配置"""
        return self._config_manager.update_cninfo_config(updates)

    def update_hot_stocks(self, stocks: List[str]) -> bool:
        """更新热门股票列表"""
        return self._config_manager.update_hot_stocks(stocks)

_monitor_center = None

def get_news_monitor_center() -> NewsMonitorCenter:
    global _monitor_center
    if _monitor_center is None:
        _monitor_center = NewsMonitorCenter()
    return _monitor_center
