# -*- coding: utf-8 -*-
"""
巨潮资讯公告抓取器
使用AKShare获取公告，支持自动分类和情绪分析

Author: 臭宝
Date: 2026-02-19
"""

import akshare as ak
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class CninfoAnnouncement:
    """巨潮公告数据模型"""
    stock_code: str
    stock_name: str
    title: str
    announcement_type: str
    publish_date: str
    url: str
    
    # 扩展字段
    content: str = ""  # 公告内容（需要额外抓取）
    priority: str = "P2"
    sentiment: str = "neutral"
    sentiment_score: float = 0.0


class CninfoCrawler:
    """
    巨潮资讯公告抓取器
    
    使用AKShare获取公告数据，支持：
    - 按日期获取全部公告
    - 按股票代码获取公告
    - 自动优先级分类
    - 情绪分析
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._priority_classifier = None
        self._emotion_analyzer = None
        self._init_analyzers()
    
    def _init_analyzers(self):
        """初始化分析器"""
        try:
            from backend.services.news_center.news_priority_classifier import NewsPriorityClassifier
            self._priority_classifier = NewsPriorityClassifier()
            self.logger.info("Priority classifier initialized")
        except Exception as e:
            self.logger.warning(f"Failed to init priority classifier: {e}")
        
        try:
            from backend.services.news_center.news_emotion_analyzer import get_emotion_analyzer
            self._emotion_analyzer = get_emotion_analyzer()
            self.logger.info("Emotion analyzer initialized")
        except Exception as e:
            self.logger.warning(f"Failed to init emotion analyzer: {e}")
    
    def fetch_by_date(self, date: str = None) -> List[CninfoAnnouncement]:
        """
        按日期获取全部公告
        
        Args:
            date: 日期格式 YYYYMMDD，默认今天
            
        Returns:
            公告列表
        """
        # 如果系统时间在未来，使用最近的交易日
        now = datetime.now()
        if now.year > 2025:
            # 使用最近的有效交易日
            test_date = "20250219"
        else:
            test_date = now.strftime('%Y%m%d')
        
        if date is None:
            date = test_date
        
        # AKShare需要交易日日期，如果今天没数据就用昨天
        max_retries = 5
        for i in range(max_retries):
            try:
                if i == 0:
                    current_date = date
                else:
                    # 回退到前几天
                    current_date = (datetime.strptime(date, '%Y%m%d') - timedelta(days=i)).strftime('%Y%m%d')
                
                self.logger.info(f"Fetching announcements for {current_date}")
                
                df = ak.stock_notice_report(symbol='全部', date=current_date)
                
                if len(df) == 0:
                    self.logger.warning(f"No data for {current_date}")
                    continue
                
                announcements = []
                for _, row in df.iterrows():
                    announcement = CninfoAnnouncement(
                        stock_code=str(row.get('代码', '')),
                        stock_name=row.get('名称', ''),
                        title=row.get('公告标题', ''),
                        announcement_type=row.get('公告类型', ''),
                        publish_date=row.get('公告日期', ''),
                        url=row.get('网址', '')
                    )
                    announcements.append(announcement)
                
                self.logger.info(f"Fetched {len(announcements)} announcements for {current_date}")
                return announcements
                
            except Exception as e:
                self.logger.warning(f"Failed to fetch for {current_date}: {e}")
                continue
        
        self.logger.error("Failed to fetch announcements after retries")
        return []
    
    def fetch_by_stock(self, stock_code: str, days: int = 7) -> List[CninfoAnnouncement]:
        """
        按股票代码获取近期公告
        
        Args:
            stock_code: 股票代码
            days: 最近多少天
            
        Returns:
            公告列表
        """
        announcements = []
        
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y%m%d')
            try:
                df = ak.stock_notice_report(symbol=stock_code, date=date)
                for _, row in df.iterrows():
                    announcement = CninfoAnnouncement(
                        stock_code=str(row['代码']),
                        stock_name=row['名称'],
                        title=row['公告标题'],
                        announcement_type=row['公告类型'],
                        publish_date=row['公告日期'],
                        url=row['网址']
                    )
                    announcements.append(announcement)
            except Exception as e:
                self.logger.debug(f"No data for {date}: {e}")
                continue
        
        self.logger.info(f"Fetched {len(announcements)} announcements for {stock_code}")
        return announcements
    
    def classify_priority(self, announcement: CninfoAnnouncement) -> CninfoAnnouncement:
        """
        对公告进行优先级分类
        
        Args:
            announcement: 公告对象
            
        Returns:
            分类后的公告
        """
        if not self._priority_classifier:
            return announcement
        
        try:
            # 使用标题+类型进行分类
            text = f"{announcement.title} {announcement.announcement_type}"
            classification = self._priority_classifier.classify(text)
            
            announcement.priority = classification.priority.value
            
            self.logger.debug(
                f"Classified: {announcement.title[:40]}... -> {announcement.priority}"
            )
            
        except Exception as e:
            self.logger.debug(f"Classification failed: {e}")
        
        return announcement
    
    def analyze_emotion(self, announcement: CninfoAnnouncement) -> CninfoAnnouncement:
        """
        分析公告情绪
        
        Args:
            announcement: 公告对象
            
        Returns:
            分析后的公告
        """
        if not self._emotion_analyzer:
            return announcement
        
        try:
            import asyncio
            
            # 使用标题+类型进行情绪分析
            text = f"{announcement.title} {announcement.announcement_type}"
            
            # 运行异步分析
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self._emotion_analyzer.analyze(
                    title=announcement.title,
                    content=announcement.announcement_type,
                    stock_code=announcement.stock_code
                )
            )
            loop.close()
            
            announcement.sentiment = result.sentiment
            announcement.sentiment_score = result.score
            
            self.logger.debug(
                f"Analyzed: {announcement.title[:40]}... -> "
                f"{announcement.sentiment} ({announcement.sentiment_score})"
            )
            
        except Exception as e:
            self.logger.debug(f"Emotion analysis failed: {e}")
            # 备用：简单关键词分析
            announcement = self._simple_emotion_analysis(announcement)
        
        return announcement
    
    def _simple_emotion_analysis(self, announcement: CninfoAnnouncement) -> CninfoAnnouncement:
        """简单的关键词情绪分析（备用）"""
        text = f"{announcement.title} {announcement.announcement_type}".lower()
        
        positive_words = ['预增', '增长', '盈利', '中标', '订单', '增持', '回购', '分红', '高送转']
        negative_words = ['预减', '亏损', '下滑', '减持', '质押', '违约', '处罚', '立案调查']
        
        pos_count = sum(1 for w in positive_words if w in text)
        neg_count = sum(1 for w in negative_words if w in text)
        
        if pos_count > neg_count:
            announcement.sentiment = "positive"
            announcement.sentiment_score = min(0.2 + pos_count * 0.1, 0.6)
        elif neg_count > pos_count:
            announcement.sentiment = "negative"
            announcement.sentiment_score = max(-0.2 - neg_count * 0.1, -0.6)
        else:
            announcement.sentiment = "neutral"
            announcement.sentiment_score = 0.0
        
        return announcement
    
    def process_announcements(
        self, 
        announcements: List[CninfoAnnouncement],
        classify: bool = True,
        analyze_emotion: bool = True
    ) -> List[CninfoAnnouncement]:
        """
        批量处理公告（分类+情绪分析）
        
        Args:
            announcements: 公告列表
            classify: 是否进行分类
            analyze_emotion: 是否进行情绪分析
            
        Returns:
            处理后的公告列表
        """
        processed = []
        
        for announcement in announcements:
            if classify:
                announcement = self.classify_priority(announcement)
            
            if analyze_emotion:
                announcement = self.analyze_emotion(announcement)
            
            processed.append(announcement)
        
        return processed
    
    def get_high_priority_announcements(
        self, 
        date: str = None,
        min_priority: str = "P1"
    ) -> List[CninfoAnnouncement]:
        """
        获取高优先级公告
        
        Args:
            date: 日期
            min_priority: 最低优先级（P0/P1/P2）
            
        Returns:
            高优先级公告列表
        """
        announcements = self.fetch_by_date(date)
        processed = self.process_announcements(announcements)
        
        # 过滤优先级
        priority_map = {"P0": 0, "P1": 1, "P2": 2}
        min_level = priority_map.get(min_priority, 1)
        
        high_priority = [
            a for a in processed 
            if priority_map.get(a.priority, 2) <= min_level
        ]
        
        # 按优先级排序
        high_priority.sort(key=lambda x: priority_map.get(x.priority, 2))
        
        return high_priority


# 全局实例
_cninfo_crawler = None

def get_cninfo_crawler() -> CninfoCrawler:
    """获取巨潮资讯抓取器实例（单例）"""
    global _cninfo_crawler
    if _cninfo_crawler is None:
        _cninfo_crawler = CninfoCrawler()
    return _cninfo_crawler


# 便捷函数
def fetch_today_announcements() -> List[Dict[str, Any]]:
    """便捷函数：获取今日公告"""
    crawler = get_cninfo_crawler()
    announcements = crawler.fetch_by_date()
    return [a.__dict__ for a in announcements]


def fetch_high_priority_today() -> List[Dict[str, Any]]:
    """便捷函数：获取今日高优先级公告"""
    crawler = get_cninfo_crawler()
    announcements = crawler.get_high_priority_announcements(min_priority="P1")
    return [a.__dict__ for a in announcements]


# 测试代码
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    crawler = CninfoCrawler()
    
    # 测试获取今日公告
    print("=" * 80)
    print("获取今日公告")
    print("=" * 80)
    
    announcements = crawler.fetch_by_date()
    print(f"\n共获取 {len(announcements)} 条公告\n")
    
    # 处理前5条
    if announcements:
        sample = announcements[:5]
        processed = crawler.process_announcements(sample)
        
        print("前5条公告（已分类+情绪分析）：")
        for i, a in enumerate(processed, 1):
            print(f"\n[{i}] {a.title}")
            print(f"    股票: {a.stock_name} ({a.stock_code})")
            print(f"    类型: {a.announcement_type}")
            print(f"    优先级: {a.priority} | 情绪: {a.sentiment} ({a.sentiment_score})")
        
        # 统计
        p0_count = sum(1 for a in processed if a.priority == "P0")
        p1_count = sum(1 for a in processed if a.priority == "P1")
        p2_count = sum(1 for a in processed if a.priority == "P2")
        
        print(f"\n优先级统计: P0={p0_count}, P1={p1_count}, P2={p2_count}")
