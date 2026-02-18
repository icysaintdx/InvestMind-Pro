#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tushare 新闻接口封装模块
封装所有可用的Tushare新闻相关接口

可用接口（按优先级排序）:
★★★ 免费接口（推荐优先使用）:
1. news_list (隐藏接口) - 全平台新闻聚合 (免费，无需权限，10个平台)
   - 雪球、第一财经、凤凰、同花顺、金融界、新浪、云财经、财联社、东方财富、华尔街见闻

★★ 付费接口（需要单独开权限）:
2. news(src=sina) - 新浪财经快讯 (需要权限)
3. major_news - 长篇新闻通讯 (需要权限)
4. cctv_news - 新闻联播文字稿 (需要权限)
5. irm_qa_sh - 上证E互动问答 (需要积分)
6. irm_qa_sz - 深证互动易问答 (需要积分)

使用方式:
    from backend.dataflows.news.tushare_news_api import get_tushare_news_api

    api = get_tushare_news_api()

    # ★★★ 推荐：使用免费的新闻聚合接口
    # 获取全平台聚合新闻（免费）
    news = api.get_news_list_all(page_size=50)

    # 获取指定平台新闻（免费）
    news = api.get_news_list_by_source(source_id=6)  # 雪球

    # 获取多个平台新闻（免费）
    news = api.get_news_list_multi_sources([1, 2, 6])  # 东方财富+财联社+雪球

    # ★★ 付费接口（需要权限）
    # 获取新浪财经快讯
    news = api.get_sina_news(hours_back=24)

    # 获取长篇新闻通讯
    news = api.get_major_news(source='财联社', hours_back=24)

    # 获取新闻联播
    news = api.get_cctv_news()

    # 获取上证E互动
    qa = api.get_irm_qa_sh()

    # 获取深证互动易
    qa = api.get_irm_qa_sz()

    # 获取所有市场新闻（聚合，优先使用免费接口）
    all_news = api.get_all_market_news()
"""

import os
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd

from backend.utils.logging_config import get_logger

logger = get_logger("tushare_news")


# ==================== 免费新闻聚合接口配置 ====================

# news_list 隐藏接口的 source_id 映射
NEWS_LIST_SOURCE_MAP = {
    0: "全平台聚合",
    1: "东方财富",
    2: "财联社",
    3: "同花顺",
    4: "新浪财经",
    5: "金融界",
    6: "雪球",
    7: "第一财经",
    8: "凤凰财经",
    9: "云财经",
    10: "华尔街见闻",
    11: "每日经济新闻",
    12: "证券时报",
    13: "中证网",
}

# 反向映射：平台名称 -> source_id
NEWS_LIST_SOURCE_NAME_MAP = {v: k for k, v in NEWS_LIST_SOURCE_MAP.items()}

# 推荐的平台组合（按重要性排序）
RECOMMENDED_SOURCES = [1, 2, 6, 10, 7]  # 东方财富、财联社、雪球、华尔街见闻、第一财经

# news_list 接口配置
NEWS_LIST_API_URL = "https://api.tushare.pro/news/news_list"
NEWS_LIST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/json;charset=UTF-8",
}


class TushareNewsAPI:
    """Tushare新闻API封装类"""

    def __init__(self):
        self.token = os.getenv("TUSHARE_TOKEN", "")
        self.pro = None
        self._initialized = False
        self._init_api()

    def _init_api(self):
        """初始化Tushare API"""
        if not self.token:
            logger.warning("TUSHARE_TOKEN 未配置，Tushare新闻接口不可用")
            return

        try:
            import tushare as ts

            ts.set_token(self.token)
            self.pro = ts.pro_api()
            self._initialized = True
            logger.info(f"Tushare新闻API初始化成功，版本: {ts.__version__}")
        except ImportError:
            logger.error("Tushare未安装，请运行: pip install tushare")
        except Exception as e:
            logger.error(f"Tushare初始化失败: {e}")

    def is_available(self) -> bool:
        """检查API是否可用"""
        return self._initialized and self.pro is not None

    # ==================== 新闻快讯 (news) ====================

    def get_sina_news(
        self, hours_back: int = 24, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取新浪财经快讯

        Args:
            hours_back: 获取多少小时内的新闻
            limit: 返回数量限制

        Returns:
            新闻列表
        """
        if not self.is_available():
            return []

        try:
            end_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            start_date = (datetime.now() - timedelta(hours=hours_back)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            df = self.pro.news(src="sina", start_date=start_date, end_date=end_date)

            if df is None or df.empty:
                logger.info("新浪财经快讯: 无数据")
                return []

            # 限制数量
            df = df.head(limit)

            # 转换为标准格式
            news_list = []
            for _, row in df.iterrows():
                news_list.append(
                    {
                        "title": str(row.get("title", row.get("content", "")[:50])),
                        "content": str(row.get("content", "")),
                        "pub_time": str(row.get("datetime", "")),
                        "source": "Tushare-新浪财经",
                        "source_key": "tushare_sina",
                        "category": str(row.get("channels", "快讯")),
                        "url": "",
                    }
                )

            logger.info(f"✅ 新浪财经快讯: {len(news_list)}条")
            return news_list

        except Exception as e:
            error_msg = str(e)
            if "每分钟最多访问" in error_msg:
                logger.warning("新浪财经快讯: 频率限制")
            else:
                logger.error(f"新浪财经快讯获取失败: {e}")
            return []

    # ==================== 新闻通讯 (major_news) ====================

    def get_major_news(
        self, source: str = "新浪财经", hours_back: int = 24, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        获取长篇新闻通讯

        Args:
            source: 数据源 (新浪财经/财联社/同花顺/华尔街见闻/新华网/凤凰财经/中证网/财新网/第一财经)
            hours_back: 获取多少小时内的新闻
            limit: 返回数量限制

        Returns:
            新闻列表
        """
        if not self.is_available():
            return []

        try:
            end_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            start_date = (datetime.now() - timedelta(hours=hours_back)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            df = self.pro.major_news(
                src=source, start_date=start_date, end_date=end_date
            )

            if df is None or df.empty:
                logger.info(f"新闻通讯-{source}: 无数据")
                return []

            # 限制数量
            df = df.head(limit)

            # 转换为标准格式
            news_list = []
            for _, row in df.iterrows():
                news_list.append(
                    {
                        "title": str(row.get("title", "")),
                        "content": str(row.get("content", ""))[:500]
                        if row.get("content")
                        else "",
                        "pub_time": str(row.get("pub_time", "")),
                        "source": f"Tushare-{source}",
                        "source_key": f"tushare_{source}",
                        "category": "新闻通讯",
                        "url": str(row.get("url", "")),
                    }
                )

            logger.info(f"✅ 新闻通讯-{source}: {len(news_list)}条")
            return news_list

        except Exception as e:
            error_msg = str(e)
            if "每分钟最多访问" in error_msg:
                logger.warning(f"新闻通讯-{source}: 频率限制")
            else:
                logger.error(f"新闻通讯-{source}获取失败: {e}")
            return []

    def get_all_major_news(
        self, hours_back: int = 24, limit_per_source: int = 20
    ) -> List[Dict[str, Any]]:
        """
        获取所有来源的长篇新闻通讯

        Args:
            hours_back: 获取多少小时内的新闻
            limit_per_source: 每个来源的数量限制

        Returns:
            新闻列表
        """
        all_news = []
        sources = ["新浪财经", "财联社", "同花顺", "华尔街见闻"]

        for source in sources:
            try:
                news = self.get_major_news(
                    source=source, hours_back=hours_back, limit=limit_per_source
                )
                all_news.extend(news)
            except Exception as e:
                logger.warning(f"获取{source}新闻失败: {e}")

        # 按时间排序
        all_news.sort(key=lambda x: x.get("pub_time", ""), reverse=True)

        return all_news

    # ==================== 新闻联播 (cctv_news) ====================

    def get_cctv_news(self, date: str = None) -> List[Dict[str, Any]]:
        """
        获取新闻联播文字稿

        Args:
            date: 日期，格式YYYYMMDD，默认今天

        Returns:
            新闻列表
        """
        if not self.is_available():
            return []

        try:
            if date is None:
                date = datetime.now().strftime("%Y%m%d")

            df = self.pro.cctv_news(date=date)

            if df is None or df.empty:
                # 尝试昨天
                yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
                df = self.pro.cctv_news(date=yesterday)
                date = yesterday

            if df is None or df.empty:
                logger.info("新闻联播: 无数据")
                return []

            # 转换为标准格式
            news_list = []
            for _, row in df.iterrows():
                # 处理时间格式：YYYYMMDD -> YYYY-MM-DD HH:MM:SS（新闻联播通常19:00播出）
                raw_date = str(row.get("date", date))
                if len(raw_date) == 8 and raw_date.isdigit():
                    formatted_date = (
                        f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:8]} 19:00:00"
                    )
                else:
                    formatted_date = raw_date

                news_list.append(
                    {
                        "title": str(row.get("title", "")),
                        "content": str(row.get("content", ""))[:500],
                        "pub_time": formatted_date,
                        "source": "Tushare-新闻联播",
                        "source_key": "tushare_cctv",
                        "category": "政策新闻",
                        "url": "",
                    }
                )

            logger.info(f"✅ 新闻联播: {len(news_list)}条")
            return news_list

        except Exception as e:
            error_msg = str(e)
            if "权限" in error_msg or "抱歉" in error_msg:
                logger.warning("新闻联播: 需要权限")
            else:
                logger.error(f"新闻联播获取失败: {e}")
            return []

    # ==================== 上证E互动 (irm_qa_sh) ====================

    def get_irm_qa_sh(
        self, stock_code: str = None, date: str = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        获取上证E互动问答

        Args:
            stock_code: 股票代码，如 600519.SH
            date: 日期，格式YYYYMMDD
            limit: 返回数量限制

        Returns:
            问答列表
        """
        if not self.is_available():
            return []

        try:
            params = {}
            if stock_code:
                params["ts_code"] = stock_code
            if date:
                params["trade_date"] = date
            else:
                params["trade_date"] = datetime.now().strftime("%Y%m%d")

            df = self.pro.irm_qa_sh(**params)

            if df is None or df.empty:
                # 尝试昨天
                params["trade_date"] = (datetime.now() - timedelta(days=1)).strftime(
                    "%Y%m%d"
                )
                df = self.pro.irm_qa_sh(**params)

            if df is None or df.empty:
                logger.info("上证E互动: 无数据")
                return []

            # 限制数量
            df = df.head(limit)

            # 转换为标准格式
            qa_list = []
            for _, row in df.iterrows():
                qa_list.append(
                    {
                        "title": f"[{row.get('name', '')}] {str(row.get('q', ''))[:50]}...",
                        "content": f"问: {row.get('q', '')}\n答: {row.get('a', '')}",
                        "pub_time": str(row.get("pub_time", row.get("trade_date", ""))),
                        "source": "Tushare-上证E互动",
                        "source_key": "tushare_irm_sh",
                        "category": "互动问答",
                        "stock_code": str(row.get("ts_code", "")),
                        "stock_name": str(row.get("name", "")),
                        "url": "",
                    }
                )

            logger.info(f"✅ 上证E互动: {len(qa_list)}条")
            return qa_list

        except Exception as e:
            error_msg = str(e)
            if "权限" in error_msg or "积分" in error_msg or "抱歉" in error_msg:
                logger.warning("上证E互动: 需要权限/积分")
            else:
                logger.error(f"上证E互动获取失败: {e}")
            return []

    # ==================== 深证互动易 (irm_qa_sz) ====================

    def get_irm_qa_sz(
        self, stock_code: str = None, date: str = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        获取深证互动易问答

        Args:
            stock_code: 股票代码，如 000001.SZ
            date: 日期，格式YYYYMMDD
            limit: 返回数量限制

        Returns:
            问答列表
        """
        if not self.is_available():
            return []

        try:
            params = {}
            if stock_code:
                params["ts_code"] = stock_code
            if date:
                params["trade_date"] = date
            else:
                params["trade_date"] = datetime.now().strftime("%Y%m%d")

            df = self.pro.irm_qa_sz(**params)

            if df is None or df.empty:
                # 尝试昨天
                params["trade_date"] = (datetime.now() - timedelta(days=1)).strftime(
                    "%Y%m%d"
                )
                df = self.pro.irm_qa_sz(**params)

            if df is None or df.empty:
                logger.info("深证互动易: 无数据")
                return []

            # 限制数量
            df = df.head(limit)

            # 转换为标准格式
            qa_list = []
            for _, row in df.iterrows():
                qa_list.append(
                    {
                        "title": f"[{row.get('name', '')}] {str(row.get('q', ''))[:50]}...",
                        "content": f"问: {row.get('q', '')}\n答: {row.get('a', '')}",
                        "pub_time": str(row.get("pub_time", row.get("trade_date", ""))),
                        "source": "Tushare-深证互动易",
                        "source_key": "tushare_irm_sz",
                        "category": "互动问答",
                        "stock_code": str(row.get("ts_code", "")),
                        "stock_name": str(row.get("name", "")),
                        "industry": str(row.get("industry", "")),
                        "url": "",
                    }
                )

            logger.info(f"✅ 深证互动易: {len(qa_list)}条")
            return qa_list

        except Exception as e:
            error_msg = str(e)
            if "权限" in error_msg or "积分" in error_msg or "抱歉" in error_msg:
                logger.warning("深证互动易: 需要权限/积分")
            else:
                logger.error(f"深证互动易获取失败: {e}")
            return []

    # ==================== 国家政策法规库 (npr) ====================

    def get_npr_news(
        self, ptype: str = None, days_back: int = 30, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取国家政策法规库

        Args:
            ptype: 政策类型（科技/财政/金融/环保/教育/医疗/农业/交通/能源/其他）
            days_back: 获取多少天内的政策
            limit: 返回数量限制

        Returns:
            政策新闻列表
        """
        if not self.is_available():
            return []

        try:
            params = {}
            if ptype:
                params["ptype"] = ptype

            df = self.pro.npr(**params)

            if df is None or df.empty:
                logger.info(f"国家政策法规库{f'-{ptype}' if ptype else ''}: 无数据")
                return []

            # 限制数量
            df = df.head(limit)

            # 转换为标准格式
            news_list = []
            for _, row in df.iterrows():
                title = str(row.get("title", ""))
                if not title:
                    continue

                news_list.append(
                    {
                        "title": f"[政策] {title}",
                        "content": str(row.get("content", ""))[:1000],
                        "pub_time": str(row.get("pub_date", "")),
                        "source": "Tushare-国家政策法规库",
                        "source_key": "tushare_npr",
                        "category": "政策新闻",
                        "policy_type": str(row.get("ptype", ptype or "")),
                        "org": str(row.get("org", "")),  # 发布机构
                        "url": str(row.get("url", "")),
                        "importance": "high",
                    }
                )

            logger.info(
                f"✅ 国家政策法规库{f'-{ptype}' if ptype else ''}: {len(news_list)}条"
            )
            return news_list

        except Exception as e:
            error_msg = str(e)
            if "权限" in error_msg or "抱歉" in error_msg:
                logger.warning("国家政策法规库: 需要权限")
            else:
                logger.error(f"国家政策法规库获取失败: {e}")
            return []

    def get_all_npr_news(self, limit_per_type: int = 20) -> List[Dict[str, Any]]:
        """
        获取所有类型的国家政策法规

        Args:
            limit_per_type: 每个类型的数量限制

        Returns:
            政策新闻列表
        """
        all_news = []
        policy_types = ["科技", "财政", "金融", "环保", "医疗", "农业", "能源"]

        for ptype in policy_types:
            try:
                news = self.get_npr_news(ptype=ptype, limit=limit_per_type)
                all_news.extend(news)
            except Exception as e:
                logger.warning(f"获取{ptype}政策失败: {e}")

        # 按时间排序
        all_news.sort(key=lambda x: x.get("pub_time", ""), reverse=True)

        return all_news

    # ==================== 上市公司全量公告 (anns_d) ====================

    def get_anns_d(
        self,
        ts_code: str = None,
        ann_date: str = None,
        start_date: str = None,
        end_date: str = None,
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        """
        获取上市公司全量公告

        Args:
            ts_code: 股票代码（如 600519.SH），为空获取全市场
            ann_date: 公告日期（YYYYMMDD）
            start_date: 开始日期（YYYYMMDD）
            end_date: 结束日期（YYYYMMDD）
            limit: 返回数量限制

        Returns:
            公告列表
        """
        if not self.is_available():
            return []

        try:
            params = {}
            if ts_code:
                params["ts_code"] = ts_code
            if ann_date:
                params["ann_date"] = ann_date
            elif start_date and end_date:
                params["start_date"] = start_date
                params["end_date"] = end_date
            else:
                # 默认获取今天的公告
                params["ann_date"] = datetime.now().strftime("%Y%m%d")

            df = self.pro.anns_d(**params)

            if df is None or df.empty:
                # 尝试昨天
                if not start_date:
                    params["ann_date"] = (datetime.now() - timedelta(days=1)).strftime(
                        "%Y%m%d"
                    )
                    df = self.pro.anns_d(**params)

            if df is None or df.empty:
                logger.info(f"上市公司公告{f'-{ts_code}' if ts_code else ''}: 无数据")
                return []

            # 限制数量
            df = df.head(limit)

            # 转换为标准格式
            news_list = []
            for _, row in df.iterrows():
                title = str(row.get("title", ""))
                if not title:
                    continue

                stock_code = str(row.get("ts_code", ""))
                stock_name = str(row.get("name", ""))
                ann_type = str(row.get("ann_type", ""))

                # 判断重要性
                importance = "low"
                urgency = "low"
                if any(
                    kw in title
                    for kw in [
                        "业绩预告",
                        "业绩快报",
                        "重大",
                        "停牌",
                        "复牌",
                        "风险提示",
                        "退市",
                    ]
                ):
                    importance = "high"
                    urgency = "high"
                elif any(
                    kw in title
                    for kw in [
                        "年报",
                        "季报",
                        "中报",
                        "分红",
                        "增持",
                        "减持",
                        "股权质押",
                    ]
                ):
                    importance = "medium"
                    urgency = "medium"

                news_list.append(
                    {
                        "title": f"[{stock_name or '公告'}] {title}",
                        "content": str(row.get("content", ""))[:1000]
                        if row.get("content")
                        else f"公告类型: {ann_type}",
                        "pub_time": str(row.get("ann_date", "")),
                        "source": "Tushare-上市公司公告",
                        "source_key": "tushare_anns_d",
                        "category": "公司公告",
                        "stock_code": stock_code,
                        "stock_name": stock_name,
                        "ann_type": ann_type,
                        "url": str(row.get("url", "")),
                        "importance": importance,
                        "urgency": urgency,
                        "related_stocks": [stock_code] if stock_code else [],
                    }
                )

            logger.info(
                f"✅ 上市公司公告{f'-{ts_code}' if ts_code else ''}: {len(news_list)}条"
            )
            return news_list

        except Exception as e:
            error_msg = str(e)
            if "权限" in error_msg or "抱歉" in error_msg:
                logger.warning("上市公司公告: 需要权限")
            else:
                logger.error(f"上市公司公告获取失败: {e}")
            return []

    def get_stock_announcements(
        self, stock_code: str, days_back: int = 30, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        获取个股公告（用于个股详情页）

        Args:
            stock_code: 股票代码（6位数字或带后缀）
            days_back: 获取多少天内的公告
            limit: 返回数量限制

        Returns:
            公告列表
        """
        # 标准化股票代码
        if not stock_code:
            return []

        ts_code = stock_code
        if not ("." in stock_code):
            # 添加后缀
            if stock_code.startswith(("60", "68", "90")):
                ts_code = f"{stock_code}.SH"
            else:
                ts_code = f"{stock_code}.SZ"

        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y%m%d")

        return self.get_anns_d(
            ts_code=ts_code, start_date=start_date, end_date=end_date, limit=limit
        )

    # ==================== 新闻快讯多源 (news) ====================

    def get_news_by_source(
        self, src: str = "sina", hours_back: int = 24, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取指定来源的新闻快讯

        Args:
            src: 数据源 (sina/eastmoney/cls/10jqka/wallstreetcn/yicai/jinrongjie/yuncaijing/fenghuang)
            hours_back: 获取多少小时内的新闻
            limit: 返回数量限制

        Returns:
            新闻列表
        """
        if not self.is_available():
            return []

        source_name_map = {
            "sina": "新浪财经",
            "eastmoney": "东方财富",
            "cls": "财联社",
            "10jqka": "同花顺",
            "wallstreetcn": "华尔街见闻",
            "yicai": "第一财经",
            "jinrongjie": "金融界",
            "yuncaijing": "云财经",
            "fenghuang": "凤凰财经",
        }

        try:
            end_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            start_date = (datetime.now() - timedelta(hours=hours_back)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            df = self.pro.news(src=src, start_date=start_date, end_date=end_date)

            if df is None or df.empty:
                logger.info(f"新闻快讯-{src}: 无数据")
                return []

            # 限制数量
            df = df.head(limit)

            # 转换为标准格式
            source_name = source_name_map.get(src, src)
            news_list = []
            for _, row in df.iterrows():
                news_list.append(
                    {
                        "title": str(row.get("title", row.get("content", "")[:50])),
                        "content": str(row.get("content", "")),
                        "pub_time": str(row.get("datetime", "")),
                        "source": f"Tushare-{source_name}",
                        "source_key": f"tushare_news_{src}",
                        "category": str(row.get("channels", "快讯")),
                        "url": "",
                    }
                )

            logger.info(f"✅ 新闻快讯-{source_name}: {len(news_list)}条")
            return news_list

        except Exception as e:
            error_msg = str(e)
            if "每分钟最多访问" in error_msg:
                logger.warning(f"新闻快讯-{src}: 频率限制")
            elif "权限" in error_msg or "抱歉" in error_msg:
                logger.warning(f"新闻快讯-{src}: 需要权限")
            else:
                logger.error(f"新闻快讯-{src}获取失败: {e}")
            return []

    def get_all_news_sources(
        self, hours_back: int = 24, limit_per_source: int = 30
    ) -> List[Dict[str, Any]]:
        """
        获取所有来源的新闻快讯

        Args:
            hours_back: 获取多少小时内的新闻
            limit_per_source: 每个来源的数量限制

        Returns:
            新闻列表
        """
        all_news = []
        sources = ["sina", "eastmoney", "cls", "10jqka", "wallstreetcn"]

        for src in sources:
            try:
                news = self.get_news_by_source(
                    src=src, hours_back=hours_back, limit=limit_per_source
                )
                all_news.extend(news)
            except Exception as e:
                logger.warning(f"获取{src}新闻失败: {e}")

        # 按时间排序
        all_news.sort(key=lambda x: x.get("pub_time", ""), reverse=True)

        return all_news

    # ==================== 聚合接口 ====================

    def get_all_market_news(
        self,
        hours_back: int = 24,
        include_free_api: bool = True,
        include_news: bool = True,
        include_major_news: bool = True,
        include_cctv: bool = True,
        include_npr: bool = True,
        include_anns: bool = True,
        include_irm: bool = False,
        limit_per_source: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        获取所有市场新闻（聚合）- 优先使用免费接口

        Args:
            hours_back: 获取多少小时内的新闻
            include_free_api: 是否包含免费的 news_list 接口（优先）
            include_news: 是否包含新闻快讯（付费）
            include_major_news: 是否包含长篇新闻通讯（付费）
            include_cctv: 是否包含新闻联播（付费）
            include_npr: 是否包含国家政策法规（付费）
            include_anns: 是否包含上市公司公告（付费）
            include_irm: 是否包含互动问答（付费）
            limit_per_source: 每个来源的数量限制

        Returns:
            新闻列表
        """
        all_news = []

        # ★★★ 1. 优先使用免费的 news_list 接口
        if include_free_api:
            try:
                free_news = self.get_news_list_all(page_size=limit_per_source)
                if free_news:
                    all_news.extend(free_news)
                    logger.info(f"✅ 免费接口 news_list: {len(free_news)}条")
            except Exception as e:
                logger.warning(f"免费接口 news_list 失败: {e}")

        # ★★ 2. 付费接口作为补充

        # 2.1 新闻快讯 (多源)
        if include_news:
            try:
                news = self.get_all_news_sources(
                    hours_back=hours_back, limit_per_source=limit_per_source // 5
                )
                all_news.extend(news)
            except Exception as e:
                logger.warning(f"获取新闻快讯失败: {e}")

        # 2.2 长篇新闻通讯
        if include_major_news:
            try:
                major_news = self.get_all_major_news(
                    hours_back=hours_back, limit_per_source=limit_per_source // 4
                )
                all_news.extend(major_news)
            except Exception as e:
                logger.warning(f"获取新闻通讯失败: {e}")

        # 2.3 新闻联播
        if include_cctv:
            try:
                cctv_news = self.get_cctv_news()
                all_news.extend(cctv_news)
            except Exception as e:
                logger.warning(f"获取新闻联播失败: {e}")

        # 2.4 国家政策法规
        if include_npr:
            try:
                npr_news = self.get_npr_news(limit=limit_per_source // 2)
                all_news.extend(npr_news)
            except Exception as e:
                logger.warning(f"获取国家政策法规失败: {e}")

        # 2.5 上市公司公告
        if include_anns:
            try:
                anns = self.get_anns_d(limit=limit_per_source)
                all_news.extend(anns)
            except Exception as e:
                logger.warning(f"获取上市公司公告失败: {e}")

        # 2.6 互动问答 (可选，数据量大)
        if include_irm:
            try:
                irm_sh = self.get_irm_qa_sh(limit=limit_per_source // 2)
                all_news.extend(irm_sh)
            except Exception as e:
                logger.warning(f"获取上证E互动失败: {e}")

            try:
                irm_sz = self.get_irm_qa_sz(limit=limit_per_source // 2)
                all_news.extend(irm_sz)
            except Exception as e:
                logger.warning(f"获取深证互动易失败: {e}")

        # 去重（按标题）
        seen_titles = set()
        unique_news = []
        for item in all_news:
            title = item.get("title", "")
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_news.append(item)

        # 按时间排序
        unique_news.sort(key=lambda x: x.get("pub_time", ""), reverse=True)

        logger.info(f"✅ Tushare市场新闻聚合: 共{len(unique_news)}条（去重后）")
        return unique_news

    def get_stock_news(
        self, stock_code: str, hours_back: int = 72, include_anns: bool = True
    ) -> List[Dict[str, Any]]:
        """
        获取个股相关新闻和互动问答

        Args:
            stock_code: 股票代码，如 600519.SH 或 000001.SZ 或 600519
            hours_back: 获取多少小时内的数据
            include_anns: 是否包含公告

        Returns:
            新闻和问答列表
        """
        all_data = []

        # 标准化股票代码
        ts_code = stock_code
        if not ("." in stock_code):
            if stock_code.startswith(("60", "68", "90")):
                ts_code = f"{stock_code}.SH"
            else:
                ts_code = f"{stock_code}.SZ"

        # 1. 上市公司公告
        if include_anns:
            try:
                anns = self.get_stock_announcements(
                    stock_code=ts_code, days_back=30, limit=30
                )
                all_data.extend(anns)
            except Exception as e:
                logger.warning(f"获取{ts_code}公告失败: {e}")

        # 2. 互动问答
        if ts_code.endswith(".SH"):
            # 上证E互动
            try:
                qa = self.get_irm_qa_sh(stock_code=ts_code, limit=20)
                all_data.extend(qa)
            except Exception as e:
                logger.warning(f"获取{ts_code}上证E互动失败: {e}")
        elif ts_code.endswith(".SZ"):
            # 深证互动易
            try:
                qa = self.get_irm_qa_sz(stock_code=ts_code, limit=20)
                all_data.extend(qa)
            except Exception as e:
                logger.warning(f"获取{ts_code}深证互动易失败: {e}")

        # 按时间排序
        all_data.sort(key=lambda x: x.get("pub_time", ""), reverse=True)

        return all_data

    # ==================== ★★★ 免费新闻聚合接口 (major_news) ★★★ ====================
    # major_news 是 Tushare 的长篇新闻通讯接口，支持多个平台
    # 注意：news_list 接口已不可用，使用 major_news 替代

    def get_news_list_by_source(
        self,
        source_id: int = 0,
        page_size: int = 20,
        page_num: int = 1,
        start_time: str = "",
        end_time: str = "",
    ) -> List[Dict[str, Any]]:
        """
        ★★★ 获取指定平台的新闻（使用 major_news 接口）

        注意：major_news 接口实际只支持以下4个源：
        - 新浪财经、财联社、同花顺、华尔街见闻
        其他源会映射到最接近的可用源

        Args:
            source_id: 平台ID (0=全平台聚合, 2=财联社, 3=同花顺,
                       4=新浪财经, 10=华尔街见闻)
                       其他ID会映射到最接近的可用源
            page_size: 每页数量
            page_num: 页码，从1开始
            start_time: 开始时间，格式 YYYY-MM-DD
            end_time: 结束时间，格式 YYYY-MM-DD

        Returns:
            新闻列表
        """
        if not self.is_available():
            return []

        # major_news 接口实际支持的源（经测试验证）
        # 其他源映射到最接近的可用源
        source_map = {
            0: None,  # 全平台聚合
            1: "新浪财经",  # 东方财富 -> 新浪财经（无东方财富源）
            2: "财联社",
            3: "同花顺",
            4: "新浪财经",
            5: "新浪财经",  # 金融界 -> 新浪财经
            6: "同花顺",  # 雪球 -> 同花顺（无雪球源）
            7: "财联社",  # 第一财经 -> 财联社（无第一财经源）
            8: "新浪财经",  # 凤凰财经 -> 新浪财经
            9: "同花顺",  # 云财经 -> 同花顺
            10: "华尔街见闻",
            11: "新浪财经",  # 每日经济新闻 -> 新浪财经
            12: "财联社",  # 证券时报 -> 财联社
            13: "财联社",  # 中证网 -> 财联社
        }

        source_name = source_map.get(source_id)

        # 如果是全平台聚合，获取多个平台的新闻
        # 修复：每个源获取 page_size 条，而不是 page_size // 4
        if source_id == 0:
            return self.get_all_major_news(hours_back=24, limit_per_source=page_size)

        # 获取指定平台的新闻
        try:
            news = self.get_major_news(
                source=source_name or "新浪财经", hours_back=24, limit=page_size
            )

            # 添加 source_id 标记
            for item in news:
                item["source_id"] = source_id
                item["is_free"] = True

            return news

        except Exception as e:
            logger.warning(f"获取平台 {source_name} 新闻失败: {e}")
            return []

    def get_news_list_all(
        self, page_size: int = 50, page_num: int = 1
    ) -> List[Dict[str, Any]]:
        """
        ★★★ 获取全平台聚合新闻（使用 major_news 接口）

        Args:
            page_size: 每页数量（每个源获取的数量，总数约为 page_size * 4）
            page_num: 页码

        Returns:
            新闻列表（按时间倒序，混合所有平台）
        """
        # 每个源获取 page_size 条，而不是除以4
        return self.get_all_major_news(hours_back=24, limit_per_source=page_size)

    def get_news_list_multi_sources(
        self, source_ids: List[int] = None, page_size_per_source: int = 10
    ) -> List[Dict[str, Any]]:
        """
        ★★★ 免费接口：获取多个指定平台的新闻

        Args:
            source_ids: 平台ID列表，默认使用推荐平台
            page_size_per_source: 每个平台获取的数量

        Returns:
            新闻列表（按时间倒序）
        """
        if source_ids is None:
            source_ids = RECOMMENDED_SOURCES

        all_news = []
        for source_id in source_ids:
            try:
                news = self.get_news_list_by_source(
                    source_id=source_id, page_size=page_size_per_source
                )
                all_news.extend(news)
            except Exception as e:
                source_name = NEWS_LIST_SOURCE_MAP.get(source_id, f"平台{source_id}")
                logger.warning(f"获取 {source_name} 新闻失败: {e}")

        # 按时间排序
        all_news.sort(key=lambda x: x.get("pub_time", ""), reverse=True)

        logger.info(f"✅ news_list 多平台聚合: 共{len(all_news)}条")
        return all_news

    def get_news_list_paginated(
        self, source_id: int = 0, total_pages: int = 5, page_size: int = 50
    ) -> List[Dict[str, Any]]:
        """
        ★★★ 免费接口：分页获取新闻（获取更多历史数据）

        Args:
            source_id: 平台ID
            total_pages: 获取的总页数
            page_size: 每页数量

        Returns:
            新闻列表
        """
        all_news = []
        for page in range(1, total_pages + 1):
            try:
                news = self.get_news_list_by_source(
                    source_id=source_id, page_size=page_size, page_num=page
                )
                if not news:
                    break  # 没有更多数据
                all_news.extend(news)
            except Exception as e:
                logger.warning(f"获取第{page}页新闻失败: {e}")
                break

        # 去重（按标题）
        seen_titles = set()
        unique_news = []
        for item in all_news:
            title = item.get("title", "")
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_news.append(item)

        logger.info(f"✅ news_list 分页获取: 共{len(unique_news)}条（去重后）")
        return unique_news

    def get_all_market_news_v2(
        self,
        use_free_api: bool = True,
        page_size: int = 50,
        fallback_to_paid: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        ★★★ 推荐：获取市场新闻（优先使用免费接口）

        Args:
            use_free_api: 是否使用免费的 news_list 接口
            page_size: 获取数量
            fallback_to_paid: 免费接口失败时是否降级到付费接口

        Returns:
            新闻列表
        """
        all_news = []

        # 1. 优先使用免费的 news_list 接口
        if use_free_api:
            try:
                free_news = self.get_news_list_all(page_size=page_size)
                if free_news:
                    all_news.extend(free_news)
                    logger.info(
                        f"✅ 使用免费 news_list 接口获取 {len(free_news)} 条新闻"
                    )
            except Exception as e:
                logger.warning(f"免费 news_list 接口失败: {e}")

        # 2. 如果免费接口没有数据，降级到付费接口
        if not all_news and fallback_to_paid:
            logger.info("免费接口无数据，尝试付费接口...")
            try:
                paid_news = self.get_all_market_news(
                    include_sina=True,
                    include_major_news=True,
                    include_cctv=True,
                    include_irm=False,
                    limit_per_source=page_size // 3,
                )
                all_news.extend(paid_news)
            except Exception as e:
                logger.warning(f"付费接口也失败: {e}")

        # 按时间排序
        all_news.sort(key=lambda x: x.get("pub_time", ""), reverse=True)

        return all_news


# 全局实例
_tushare_news_api = None


def get_tushare_news_api() -> TushareNewsAPI:
    """获取Tushare新闻API实例（单例）"""
    global _tushare_news_api
    if _tushare_news_api is None:
        _tushare_news_api = TushareNewsAPI()
    return _tushare_news_api


# 便捷函数
def get_tushare_market_news(hours_back: int = 24) -> List[Dict[str, Any]]:
    """获取Tushare市场新闻"""
    api = get_tushare_news_api()
    return api.get_all_market_news(hours_back=hours_back)


def get_tushare_stock_news(stock_code: str) -> List[Dict[str, Any]]:
    """获取Tushare个股新闻"""
    api = get_tushare_news_api()
    return api.get_stock_news(stock_code=stock_code)


# ==================== 免费新闻聚合接口便捷函数 ====================


def get_tushare_news_list_all(page_size: int = 50) -> List[Dict[str, Any]]:
    """获取全平台聚合新闻（免费接口）"""
    api = get_tushare_news_api()
    return api.get_news_list_all(page_size=page_size)


def get_tushare_news_list_by_source(
    source_id: int, page_size: int = 20
) -> List[Dict[str, Any]]:
    """获取指定平台新闻（免费接口）"""
    api = get_tushare_news_api()
    return api.get_news_list_by_source(source_id=source_id, page_size=page_size)


def get_tushare_news_list_recommended(
    page_size_per_source: int = 10,
) -> List[Dict[str, Any]]:
    """获取推荐平台新闻（免费接口）"""
    api = get_tushare_news_api()
    return api.get_news_list_multi_sources(
        source_ids=RECOMMENDED_SOURCES, page_size_per_source=page_size_per_source
    )
