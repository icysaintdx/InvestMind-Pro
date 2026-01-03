# -*- coding: utf-8 -*-
"""
新闻获取配置模块
支持前端动态配置各数据源参数
"""
import json
import os
import threading
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

import logging
logger = logging.getLogger(__name__)


class NewsSourceType(str, Enum):
    """新闻数据源类型"""
    # 市场新闻源（不需要个股参数）
    EASTMONEY_GLOBAL = "eastmoney_global"      # 东方财富全球资讯
    CLS_GLOBAL = "cls_global"                  # 财联社全球资讯
    FUTU_GLOBAL = "futu_global"                # 富途牛牛
    THS_GLOBAL = "ths_global"                  # 同花顺
    SINA_GLOBAL = "sina_global"                # 新浪财经
    WEIBO_HOT = "weibo_hot"                    # 微博热议
    CJZC = "cjzc"                              # 财经早餐
    CCTV = "cctv"                              # 新闻联播
    BAIDU = "baidu"                            # 百度财经
    CNINFO_MARKET = "cninfo_market"            # 巨潮市场公告（不带个股）
    CNINFO_NEWS = "cninfo_news"                # 巨潮新闻数据（p_info3030）- VIP
    CNINFO_RESEARCH = "cninfo_research"        # 巨潮研报摘要（p_info3097_inc）- VIP
    CNINFO_MANAGEMENT = "cninfo_management"    # 巨潮高管变动（p_stock2102）

    # 个股新闻源（需要股票代码参数）
    STOCK_NEWS_EM = "stock_news_em"            # 东方财富个股新闻
    CNINFO_STOCK = "cninfo_stock"              # 巨潮个股公告
    CNINFO_STOCK_NEWS = "cninfo_stock_news"    # 巨潮个股新闻（p_info3030带股票代码）- VIP


@dataclass
class SourceConfig:
    """单个数据源配置"""
    source_type: str
    name: str
    enabled: bool = True
    interval: int = 60          # 刷新间隔（秒）
    priority: int = 5           # 优先级 1-10
    # 可配置参数
    limit: int = 0              # 返回数量限制，0表示不限制
    days_back: int = 1          # 获取多少天的数据
    # 个股相关
    stock_codes: List[str] = field(default_factory=list)  # 监控的股票列表（用于个股新闻源）

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class CninfoConfig:
    """巨潮API专用配置"""
    enabled: bool = True
    # 公告配置
    announcement_enabled: bool = True
    announcement_days_back: int = 1      # 获取多少天的公告
    announcement_page_size: int = 1000   # 每页数量
    announcement_markets: List[str] = field(default_factory=list)  # 市场筛选
    # 状态变动配置
    status_change_enabled: bool = True
    status_change_limit: int = 100       # 状态变动获取数量

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class NewsConfig:
    """新闻获取总配置"""
    # 市场新闻配置（用于新闻中心/实时新闻流）
    market_sources: Dict[str, SourceConfig] = field(default_factory=dict)

    # 个股新闻配置（用于智能分析/个股监控）
    stock_sources: Dict[str, SourceConfig] = field(default_factory=dict)

    # 巨潮API配置
    cninfo: CninfoConfig = field(default_factory=CninfoConfig)

    # 热门股票列表（用于市场新闻中的个股新闻采集）
    hot_stocks: List[str] = field(default_factory=list)

    # 全局配置
    max_news_per_fetch: int = 5000       # 单次获取最大新闻数
    dedup_enabled: bool = True           # 是否启用去重
    sentiment_enabled: bool = True       # 是否启用情感分析

    def to_dict(self) -> Dict:
        result = {
            'market_sources': {k: v.to_dict() for k, v in self.market_sources.items()},
            'stock_sources': {k: v.to_dict() for k, v in self.stock_sources.items()},
            'cninfo': self.cninfo.to_dict(),
            'hot_stocks': self.hot_stocks,
            'max_news_per_fetch': self.max_news_per_fetch,
            'dedup_enabled': self.dedup_enabled,
            'sentiment_enabled': self.sentiment_enabled,
        }
        return result


class NewsConfigManager:
    """新闻配置管理器（单例）"""
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
        self._config_file = os.path.join(
            os.path.dirname(__file__),
            '..', '..', '..', 'data', 'news_center_cache', 'news_config.json'
        )
        self._config: NewsConfig = self._load_default_config()
        self._load_from_file()
        logger.info("NewsConfigManager initialized")

    def _load_default_config(self) -> NewsConfig:
        """加载默认配置"""
        config = NewsConfig()

        # 市场新闻源配置
        config.market_sources = {
            NewsSourceType.EASTMONEY_GLOBAL.value: SourceConfig(
                source_type=NewsSourceType.EASTMONEY_GLOBAL.value,
                name="东方财富全球资讯",
                enabled=True,
                interval=60,
                priority=10,
            ),
            NewsSourceType.CLS_GLOBAL.value: SourceConfig(
                source_type=NewsSourceType.CLS_GLOBAL.value,
                name="财联社电报",
                enabled=True,
                interval=30,
                priority=10,
            ),
            NewsSourceType.FUTU_GLOBAL.value: SourceConfig(
                source_type=NewsSourceType.FUTU_GLOBAL.value,
                name="富途牛牛",
                enabled=True,
                interval=60,
                priority=7,
            ),
            NewsSourceType.THS_GLOBAL.value: SourceConfig(
                source_type=NewsSourceType.THS_GLOBAL.value,
                name="同花顺",
                enabled=True,
                interval=60,
                priority=7,
            ),
            NewsSourceType.SINA_GLOBAL.value: SourceConfig(
                source_type=NewsSourceType.SINA_GLOBAL.value,
                name="新浪财经",
                enabled=True,
                interval=60,
                priority=7,
            ),
            NewsSourceType.WEIBO_HOT.value: SourceConfig(
                source_type=NewsSourceType.WEIBO_HOT.value,
                name="微博热议",
                enabled=True,
                interval=120,
                priority=5,
            ),
            NewsSourceType.CJZC.value: SourceConfig(
                source_type=NewsSourceType.CJZC.value,
                name="财经早餐",
                enabled=True,
                interval=300,
                priority=6,
            ),
            NewsSourceType.CCTV.value: SourceConfig(
                source_type=NewsSourceType.CCTV.value,
                name="新闻联播",
                enabled=True,
                interval=600,
                priority=5,
            ),
            NewsSourceType.BAIDU.value: SourceConfig(
                source_type=NewsSourceType.BAIDU.value,
                name="百度财经",
                enabled=True,
                interval=120,
                priority=6,
            ),
            NewsSourceType.CNINFO_MARKET.value: SourceConfig(
                source_type=NewsSourceType.CNINFO_MARKET.value,
                name="巨潮市场公告",
                enabled=True,
                interval=300,
                priority=8,
            ),
            NewsSourceType.CNINFO_NEWS.value: SourceConfig(
                source_type=NewsSourceType.CNINFO_NEWS.value,
                name="巨潮新闻数据(VIP)",
                enabled=False,  # VIP接口，默认禁用
                interval=120,
                priority=8,
                days_back=1,
            ),
            NewsSourceType.CNINFO_RESEARCH.value: SourceConfig(
                source_type=NewsSourceType.CNINFO_RESEARCH.value,
                name="巨潮研报摘要(VIP)",
                enabled=False,  # VIP接口，默认禁用
                interval=300,
                priority=7,
                limit=500,
            ),
            NewsSourceType.CNINFO_MANAGEMENT.value: SourceConfig(
                source_type=NewsSourceType.CNINFO_MANAGEMENT.value,
                name="巨潮高管变动",
                enabled=True,
                interval=600,  # 10分钟刷新一次
                priority=7,
                limit=100,  # 获取最近100条
            ),
        }

        # 个股新闻源配置
        config.stock_sources = {
            NewsSourceType.STOCK_NEWS_EM.value: SourceConfig(
                source_type=NewsSourceType.STOCK_NEWS_EM.value,
                name="东方财富个股新闻",
                enabled=True,
                interval=60,
                priority=10,
                limit=50,  # 每只股票获取50条
            ),
            NewsSourceType.CNINFO_STOCK.value: SourceConfig(
                source_type=NewsSourceType.CNINFO_STOCK.value,
                name="巨潮个股公告",
                enabled=True,
                interval=300,
                priority=9,
                days_back=30,  # 获取30天的公告
            ),
            NewsSourceType.CNINFO_STOCK_NEWS.value: SourceConfig(
                source_type=NewsSourceType.CNINFO_STOCK_NEWS.value,
                name="巨潮个股新闻(VIP)",
                enabled=False,  # VIP接口，默认禁用
                interval=120,
                priority=8,
                days_back=7,  # 获取7天的新闻
            ),
        }

        # 巨潮配置
        config.cninfo = CninfoConfig(
            enabled=True,
            announcement_enabled=True,
            announcement_days_back=1,
            announcement_page_size=1000,
            status_change_enabled=True,
            status_change_limit=100,
        )

        # 热门股票列表（用于市场新闻采集时获取个股新闻）
        config.hot_stocks = [
            "000001", "600519", "000858", "601318", "600036", "000333", "002594", "300750",
            "600000", "601166", "000002", "600030", "601398", "600016", "601288", "000651",
            "600276", "000725", "601012", "600887", "000568", "002415", "600309", "601888",
            "002304", "000063", "601601", "600900", "000100", "002475"
        ]

        return config

    def _load_from_file(self):
        """从文件加载配置"""
        try:
            if os.path.exists(self._config_file):
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._apply_config_data(data)
                logger.info(f"Loaded news config from {self._config_file}")
        except Exception as e:
            logger.warning(f"Failed to load news config: {e}")

    def _apply_config_data(self, data: Dict):
        """应用配置数据"""
        if 'market_sources' in data:
            for key, value in data['market_sources'].items():
                if key in self._config.market_sources:
                    for k, v in value.items():
                        if hasattr(self._config.market_sources[key], k):
                            setattr(self._config.market_sources[key], k, v)

        if 'stock_sources' in data:
            for key, value in data['stock_sources'].items():
                if key in self._config.stock_sources:
                    for k, v in value.items():
                        if hasattr(self._config.stock_sources[key], k):
                            setattr(self._config.stock_sources[key], k, v)

        if 'cninfo' in data:
            for k, v in data['cninfo'].items():
                if hasattr(self._config.cninfo, k):
                    setattr(self._config.cninfo, k, v)

        if 'hot_stocks' in data:
            self._config.hot_stocks = data['hot_stocks']

        for key in ['max_news_per_fetch', 'dedup_enabled', 'sentiment_enabled']:
            if key in data:
                setattr(self._config, key, data[key])

    def save_to_file(self):
        """保存配置到文件"""
        try:
            os.makedirs(os.path.dirname(self._config_file), exist_ok=True)
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config.to_dict(), f, ensure_ascii=False, indent=2)
            logger.info(f"Saved news config to {self._config_file}")
        except Exception as e:
            logger.error(f"Failed to save news config: {e}")

    @property
    def config(self) -> NewsConfig:
        return self._config

    def get_config(self) -> Dict:
        """获取配置（用于API返回）"""
        return self._config.to_dict()

    def update_config(self, data: Dict) -> bool:
        """更新配置"""
        try:
            self._apply_config_data(data)
            self.save_to_file()
            return True
        except Exception as e:
            logger.error(f"Failed to update config: {e}")
            return False

    def update_source_config(self, source_type: str, updates: Dict) -> bool:
        """更新单个数据源配置"""
        try:
            # 检查市场源
            if source_type in self._config.market_sources:
                source = self._config.market_sources[source_type]
                for k, v in updates.items():
                    if hasattr(source, k):
                        setattr(source, k, v)
                self.save_to_file()
                return True

            # 检查个股源
            if source_type in self._config.stock_sources:
                source = self._config.stock_sources[source_type]
                for k, v in updates.items():
                    if hasattr(source, k):
                        setattr(source, k, v)
                self.save_to_file()
                return True

            return False
        except Exception as e:
            logger.error(f"Failed to update source config: {e}")
            return False

    def update_cninfo_config(self, updates: Dict) -> bool:
        """更新巨潮配置"""
        try:
            for k, v in updates.items():
                if hasattr(self._config.cninfo, k):
                    setattr(self._config.cninfo, k, v)
            self.save_to_file()
            return True
        except Exception as e:
            logger.error(f"Failed to update cninfo config: {e}")
            return False

    def update_hot_stocks(self, stocks: List[str]) -> bool:
        """更新热门股票列表"""
        try:
            self._config.hot_stocks = stocks
            self.save_to_file()
            return True
        except Exception as e:
            logger.error(f"Failed to update hot stocks: {e}")
            return False


# 全局实例
_config_manager = None

def get_news_config_manager() -> NewsConfigManager:
    global _config_manager
    if _config_manager is None:
        _config_manager = NewsConfigManager()
    return _config_manager
