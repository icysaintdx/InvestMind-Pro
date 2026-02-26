#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
备用免费新闻数据源
当 Tushare 额度用完时使用的替代方案

包含以下免费数据源:
1. 网易财经新闻
2. 腾讯财经新闻  
3. 搜狐财经
4. 和讯网
5. 中证网
6. 证券时报
7. 上海证券报
8. 人民网财经
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class AlternativeNewsAPI:
    """备用新闻数据源 API"""
    
    def __init__(self):
        self.session = None
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建 HTTP session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(headers=self.headers)
        return self.session
    
    async def close(self):
        """关闭 session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    # ==================== 网易财经 ====================
    
    async def get_163_news(self, limit: int = 20) -> List[Dict]:
        """
        获取网易财经新闻
        API: https://api.money.126.net/data/feed/XXX
        """
        news_list = []
        try:
            session = await self._get_session()
            
            # 网易财经 API
            url = "https://api.money.126.net/data/feed/0000001,1399001,1399300,HSI,IXIC"
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    # 解析 JSONP 格式
                    if text.startswith("_ntes_quote_callback("):
                        json_str = text[len("_ntes_quote_quote_callback("):text.rfind(")")]
                        data = json.loads(json_str)
                        # 提取相关新闻
                        for code, info in data.items():
                            if isinstance(info, dict) and "news" in info:
                                for item in info["news"]:
                                    news_list.append({
                                        "title": item.get("title", ""),
                                        "content": item.get("content", "")[:500],
                                        "pub_time": item.get("time", datetime.now().isoformat()),
                                        "source": "网易财经",
                                        "url": item.get("url", ""),
                                    })
                                    if len(news_list) >= limit:
                                        break
            
            logger.info(f"网易财经: {len(news_list)}条")
            return news_list[:limit]
            
        except Exception as e:
            logger.warning(f"网易财经获取失败: {e}")
            return []
    
    # ==================== 腾讯财经 ====================
    
    async def get_qq_news(self, limit: int = 20) -> List[Dict]:
        """
        获取腾讯财经新闻
        """
        news_list = []
        try:
            session = await self._get_session()
            
            # 腾讯财经 API
            url = "https://i.news.qq.com/trpc.qqnews_web.kv_srv.kv_srv_http_proxy/list"
            params = {
                "sub_srv_id": "finance",
                "srv_id": "pc",
                "limit": limit,
                "page": 1,
            }
            
            async with session.get(url, params=params, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    items = data.get("data", {}).get("list", [])
                    
                    for item in items:
                        news_list.append({
                            "title": item.get("title", ""),
                            "content": item.get("abstract", "")[:500],
                            "pub_time": item.get("publish_time", datetime.now().isoformat()),
                            "source": "腾讯财经",
                            "url": item.get("url", ""),
                        })
            
            logger.info(f"腾讯财经: {len(news_list)}条")
            return news_list
            
        except Exception as e:
            logger.warning(f"腾讯财经获取失败: {e}")
            return []
    
    # ==================== 搜狐财经 ====================
    
    async def get_sohu_news(self, limit: int = 20) -> List[Dict]:
        """
        获取搜狐财经新闻
        """
        news_list = []
        try:
            session = await self._get_session()
            
            # 搜狐财经 API
            url = "https://v2.sohu.com/public-api/feed"
            params = {
                "scene": "CATEGORY",
                "sceneId": "1353",  # 财经分类
                "page": 1,
                "size": limit,
            }
            
            async with session.get(url, params=params, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    items = data.get("data", [])
                    
                    for item in items:
                        news_list.append({
                            "title": item.get("title", ""),
                            "content": item.get("content", "")[:500],
                            "pub_time": item.get("publicTime", datetime.now().isoformat()),
                            "source": "搜狐财经",
                            "url": item.get("url", ""),
                        })
            
            logger.info(f"搜狐财经: {len(news_list)}条")
            return news_list
            
        except Exception as e:
            logger.warning(f"搜狐财经获取失败: {e}")
            return []
    
    # ==================== 和讯网 ====================
    
    async def get_hexun_news(self, limit: int = 20) -> List[Dict]:
        """
        获取和讯财经新闻
        """
        news_list = []
        try:
            session = await self._get_session()
            
            # 和讯财经 RSS/API
            url = "https://api.hexun.com/api2/news/getNewsList"
            params = {
                "type": "1",
                "page": 1,
                "pageSize": limit,
            }
            
            async with session.get(url, params=params, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    items = data.get("data", {}).get("list", [])
                    
                    for item in items:
                        news_list.append({
                            "title": item.get("title", ""),
                            "content": item.get("summary", "")[:500],
                            "pub_time": item.get("createTime", datetime.now().isoformat()),
                            "source": "和讯网",
                            "url": item.get("link", ""),
                        })
            
            logger.info(f"和讯网: {len(news_list)}条")
            return news_list
            
        except Exception as e:
            logger.warning(f"和讯网获取失败: {e}")
            return []
    
    # ==================== 中证网 ====================
    
    async def get_cs_news(self, limit: int = 20) -> List[Dict]:
        """
        获取中证网新闻
        """
        news_list = []
        try:
            session = await self._get_session()
            
            # 中证网 API
            url = "https://www.cs.com.cn/api/v1/news/list"
            params = {
                "channel": "zqxw",
                "page": 1,
                "size": limit,
            }
            
            async with session.get(url, params=params, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    items = data.get("data", {}).get("list", [])
                    
                    for item in items:
                        news_list.append({
                            "title": item.get("title", ""),
                            "content": item.get("summary", "")[:500],
                            "pub_time": item.get("publishTime", datetime.now().isoformat()),
                            "source": "中证网",
                            "url": item.get("url", ""),
                        })
            
            logger.info(f"中证网: {len(news_list)}条")
            return news_list
            
        except Exception as e:
            logger.warning(f"中证网获取失败: {e}")
            return []
    
    # ==================== 聚合获取 ====================
    
    async def get_all_alternative_news(self, limit_per_source: int = 10) -> List[Dict]:
        """
        获取所有备用新闻源的聚合数据
        
        Returns:
            合并后的新闻列表
        """
        all_news = []
        
        # 定义要获取的源
        sources = [
            ("网易财经", self.get_163_news),
            ("腾讯财经", self.get_qq_news),
            ("搜狐财经", self.get_sohu_news),
            ("和讯网", self.get_hexun_news),
            ("中证网", self.get_cs_news),
        ]
        
        # 并发获取
        tasks = []
        for name, func in sources:
            tasks.append(func(limit=limit_per_source))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for (name, _), result in zip(sources, results):
            if isinstance(result, list):
                all_news.extend(result)
                logger.info(f"备用源 {name}: {len(result)}条")
            elif isinstance(result, Exception):
                logger.warning(f"备用源 {name} 失败: {result}")
        
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
        
        logger.info(f"备用新闻源总计: {len(unique_news)}条（去重后）")
        return unique_news


# 全局实例
_alt_api = None

def get_alternative_news_api() -> AlternativeNewsAPI:
    """获取全局备用API实例"""
    global _alt_api
    if _alt_api is None:
        _alt_api = AlternativeNewsAPI()
    return _alt_api
