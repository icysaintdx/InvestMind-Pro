#!/usr/bin/env python3
"""
百度热搜API
获取百度热搜榜，过滤股票相关话题
"""

import requests
import logging
from typing import List, Dict, Any
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("baidu_hot_search")


class BaiduHotSearchAPI:
    """百度热搜API"""
    
    # 使用百度官方API
    BASE_URL = "https://top.baidu.com/api/board"
    
    def __init__(self):
        """初始化"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://top.baidu.com/board'
        })
        
        # 股票相关关键词
        self.stock_keywords = [
            # 市场相关
            '股票', '股市', 'A股', '港股', '美股',
            '上证', '深证', '创业板', '科创板', '北交所',
            '牛市', '熊市', '涨停', '跌停', '暴涨', '暴跌',
            '大盘', '指数', '行情',
            
            # 知名公司
            '茅台', '比亚迪', '宁德时代', '腾讯', '阿里',
            '美团', '京东', '拼多多', '小米', '华为',
            '中国平安', '招商银行', '工商银行', '建设银行',
            '贵州茅台', '五粮液', '隆基绿能', '宁德时代',
            
            # 行业相关
            '新能源', '光伏', '锂电池', '芯片', '半导体',
            '房地产', '银行', '保险', '证券', '基金',
            '医药', '白酒', '科技', '人工智能', 'AI',
            
            # 人物相关
            '巴菲特', '马斯克', '任正非', '马云', '雷军'
        ]
    
    def get_hot_search(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取百度热搜榜
        
        Args:
            limit: 返回热搜数量
            
        Returns:
            热搜列表
        """
        try:
            response = self.session.get(
                self.BASE_URL,
                params={
                    'platform': 'wise',
                    'tab': 'realtime'
                },
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            # 解析百度热搜数据
            cards = data.get('data', {}).get('cards', [])
            if not cards:
                logger.warning("百度热搜返回空数据")
                return []
            
            # 获取热搜列表 - 处理嵌套结构
            # cards[0].content 是分类列表，每个分类有content字段包含实际热搜
            hot_list = []
            rank = 1
            for category in cards[0].get('content', []):
                category_content = category.get('content', [])
                for item in category_content:
                    if rank > limit:
                        break
                    hot_list.append({
                        'rank': rank,
                        'title': item.get('word', ''),
                        'desc': item.get('desc', ''),
                        'hot': item.get('hotScore', item.get('hotTag', '')),
                        'url': item.get('url', item.get('rawUrl', '')),
                        'tag': item.get('newHotName', ''),
                        'is_top': item.get('isTop', False)
                    })
                    rank += 1
            
            logger.info(f"获取到 {len(hot_list)} 条百度热搜")
            
            return hot_list
            
        except Exception as e:
            logger.error(f"获取百度热搜失败: {e}")
            return []
    
    def filter_stock_topics(self, hot_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        过滤股票相关话题
        
        Args:
            hot_list: 热搜列表
            
        Returns:
            股票相关话题列表
        """
        stock_topics = []
        
        for item in hot_list:
            title = item.get('title', '')
            desc = item.get('desc', '')
            
            # 检查是否包含股票关键词
            text = f"{title} {desc}"
            if any(keyword in text for keyword in self.stock_keywords):
                stock_topics.append({
                    'rank': item.get('rank'),
                    'title': title,
                    'desc': desc,
                    'hot': item.get('hot'),
                    'url': item.get('url'),
                    'timestamp': datetime.now().isoformat()
                })
        
        logger.info(f"过滤出 {len(stock_topics)} 条股票相关热搜")
        return stock_topics
    
    def get_stock_hot_search(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取股票相关热搜
        
        Args:
            limit: 返回热搜数量
            
        Returns:
            股票相关热搜列表
        """
        hot_list = self.get_hot_search(limit)
        return self.filter_stock_topics(hot_list)
    
    def format_for_display(self, topics: List[Dict[str, Any]]) -> str:
        """
        格式化为显示文本
        
        Args:
            topics: 话题列表
            
        Returns:
            格式化文本
        """
        if not topics:
            return "暂无股票相关热搜"
        
        lines = ["📊 百度股票热搜", "=" * 40]
        
        for topic in topics[:10]:  # 只显示前10条
            rank = topic.get('rank', '-')
            title = topic.get('title', '')
            hot = topic.get('hot', '')
            
            lines.append(f"{rank}. {title}")
            if hot:
                lines.append(f"   🔥 {hot}")
        
        return "\n".join(lines)


# 便捷函数
def get_baidu_stock_hot_search(limit: int = 50) -> List[Dict[str, Any]]:
    """获取百度股票热搜"""
    api = BaiduHotSearchAPI()
    return api.get_stock_hot_search(limit)


if __name__ == '__main__':
    # 测试
    api = BaiduHotSearchAPI()
    stock_topics = api.get_stock_hot_search()
    print(api.format_for_display(stock_topics))
