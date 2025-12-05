#!/usr/bin/env python3
"""
微博热搜API
获取微博热搜榜，过滤股票相关话题
"""

import requests
from typing import List, Dict, Any
from datetime import datetime

from backend.utils.logging_config import get_logger

logger = get_logger("weibo_hot_search")


class WeiboHotSearchAPI:
    """微博热搜API"""
    
    BASE_URL = "https://api.aa1.cn/api/weibo-rs"
    
    def __init__(self):
        """初始化"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # 股票相关关键词
        self.stock_keywords = [
            # 市场相关
            '股票', '股市', 'A股', '港股', '美股',
            '上证', '深证', '创业板', '科创板', '北交所',
            '牛市', '熊市', '涨停', '跌停', '暴涨', '暴跌',
            
            # 知名公司
            '茅台', '比亚迪', '宁德时代', '腾讯', '阿里',
            '美团', '京东', '拼多多', '小米', '华为',
            '中国平安', '招商银行', '工商银行', '建设银行',
            
            # 行业相关
            '新能源', '芯片', '半导体', '锂电池', '光伏',
            '医药', '白酒', '地产', '金融', '科技',
            
            # 投资相关
            '基金', '证券', '期货', '投资', '理财',
            '券商', '机构', '北向资金', '外资',
        ]
    
    def get_hot_search(self) -> List[Dict[str, Any]]:
        """
        获取微博热搜榜
        
        Returns:
            热搜列表
        """
        try:
            logger.info("开始获取微博热搜...")
            
            response = self.session.get(self.BASE_URL, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # 解析数据
            if isinstance(data, dict) and 'data' in data:
                hot_list = data['data']
            elif isinstance(data, list):
                hot_list = data
            else:
                logger.warning(f"未知的数据格式: {type(data)}")
                return []
            
            logger.info(f"✅ 成功获取微博热搜 {len(hot_list)} 条")
            return hot_list
            
        except Exception as e:
            logger.error(f"❌ 获取微博热搜失败: {e}")
            return []
    
    def filter_stock_topics(self, hot_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        过滤股票相关话题
        
        Args:
            hot_list: 热搜列表
            
        Returns:
            股票相关话题列表
        """
        filtered = []
        
        for item in hot_list:
            title = item.get('title', '') or item.get('word', '') or item.get('query', '')
            
            # 检查是否包含股票关键词
            if any(kw in title for kw in self.stock_keywords):
                # 添加标记
                item['is_stock_related'] = True
                item['matched_keywords'] = [kw for kw in self.stock_keywords if kw in title]
                filtered.append(item)
        
        logger.info(f"过滤出股票相关话题 {len(filtered)} 条")
        return filtered
    
    def get_stock_hot_topics(self) -> Dict[str, Any]:
        """
        获取股票相关热搜话题（完整流程）
        
        Returns:
            包含热搜数据和分析结果的字典
        """
        # 获取热搜
        hot_list = self.get_hot_search()
        
        if not hot_list:
            return {
                'success': False,
                'message': '获取热搜失败',
                'timestamp': datetime.now().isoformat()
            }
        
        # 过滤股票相关
        stock_topics = self.filter_stock_topics(hot_list)
        
        # 分析热度
        total_heat = sum(int(item.get('热度', 0) or item.get('heat', 0) or 0) for item in stock_topics)
        
        return {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'total_count': len(hot_list),
            'stock_count': len(stock_topics),
            'stock_ratio': len(stock_topics) / len(hot_list) if hot_list else 0,
            'total_heat': total_heat,
            'topics': stock_topics,
            'summary': f"微博热搜共{len(hot_list)}条，股票相关{len(stock_topics)}条"
        }


# 全局实例
_weibo_hot_search_api = None

def get_weibo_hot_search_api():
    """获取微博热搜API实例（单例）"""
    global _weibo_hot_search_api
    if _weibo_hot_search_api is None:
        _weibo_hot_search_api = WeiboHotSearchAPI()
    return _weibo_hot_search_api
