#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tushare 新闻接口封装模块
封装所有可用的Tushare新闻相关接口

可用接口（按优先级排序）:
1. news(src=sina) - 新浪财经快讯 (免费，数据量大)
2. major_news - 长篇新闻通讯 (新浪/财联社/同花顺/华尔街见闻)
3. cctv_news - 新闻联播文字稿
4. irm_qa_sh - 上证E互动问答
5. irm_qa_sz - 深证互动易问答

使用方式:
    from backend.dataflows.news.tushare_news_api import get_tushare_news_api

    api = get_tushare_news_api()

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

    # 获取所有市场新闻（聚合）
    all_news = api.get_all_market_news()
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd

from backend.utils.logging_config import get_logger

logger = get_logger("tushare_news")


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
                # 处理时间格式：YYYYMMDD -> YYYY-MM-DD HH:MM:SS
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

    # ==================== 聚合接口 ====================

    def get_all_market_news(
        self,
        hours_back: int = 24,
        include_sina: bool = True,
        include_major_news: bool = True,
        include_cctv: bool = True,
        include_irm: bool = False,
        limit_per_source: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        获取所有市场新闻（聚合）

        Args:
            hours_back: 获取多少小时内的新闻
            include_sina: 是否包含新浪财经快讯
            include_major_news: 是否包含长篇新闻通讯
            include_cctv: 是否包含新闻联播
            include_irm: 是否包含互动问答
            limit_per_source: 每个来源的数量限制

        Returns:
            新闻列表
        """
        all_news = []

        # 1. 新浪财经快讯 (优先级最高，数据量大)
        if include_sina:
            try:
                sina_news = self.get_sina_news(
                    hours_back=hours_back, limit=limit_per_source
                )
                all_news.extend(sina_news)
            except Exception as e:
                logger.warning(f"获取新浪财经快讯失败: {e}")

        # 2. 长篇新闻通讯
        if include_major_news:
            try:
                major_news = self.get_all_major_news(
                    hours_back=hours_back, limit_per_source=limit_per_source // 4
                )
                all_news.extend(major_news)
            except Exception as e:
                logger.warning(f"获取新闻通讯失败: {e}")

        # 3. 新闻联播
        if include_cctv:
            try:
                cctv_news = self.get_cctv_news()
                all_news.extend(cctv_news)
            except Exception as e:
                logger.warning(f"获取新闻联播失败: {e}")

        # 4. 互动问答 (可选，数据量大)
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

        # 按时间排序
        all_news.sort(key=lambda x: x.get("pub_time", ""), reverse=True)

        logger.info(f"✅ Tushare市场新闻聚合: 共{len(all_news)}条")
        return all_news

    def get_stock_news(
        self, stock_code: str, hours_back: int = 72
    ) -> List[Dict[str, Any]]:
        """
        获取个股相关新闻和互动问答

        Args:
            stock_code: 股票代码，如 600519.SH 或 000001.SZ
            hours_back: 获取多少小时内的数据

        Returns:
            新闻和问答列表
        """
        all_data = []

        # 判断是上交所还是深交所
        if stock_code.endswith(".SH"):
            # 上证E互动
            try:
                qa = self.get_irm_qa_sh(stock_code=stock_code, limit=20)
                all_data.extend(qa)
            except Exception as e:
                logger.warning(f"获取{stock_code}上证E互动失败: {e}")
        elif stock_code.endswith(".SZ"):
            # 深证互动易
            try:
                qa = self.get_irm_qa_sz(stock_code=stock_code, limit=20)
                all_data.extend(qa)
            except Exception as e:
                logger.warning(f"获取{stock_code}深证互动易失败: {e}")

        # 按时间排序
        all_data.sort(key=lambda x: x.get("pub_time", ""), reverse=True)

        return all_data


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
