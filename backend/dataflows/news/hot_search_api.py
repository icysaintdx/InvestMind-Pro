#!/usr/bin/env python3
"""
热搜API接口
使用第三方免费API
"""

import requests
from typing import List, Dict, Any
from backend.utils.logging_config import get_logger

logger = get_logger("hot_search")


class HotSearchAPI:
    """热搜API"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # 股票关键词
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
    
    def get_weibo_hot(self) -> List[Dict[str, Any]]:
        """
        获取微博热搜
        尝试多个API地址
        
        Returns:
            热搜列表
        """
        # 多个备用API地址
        urls = [
            "https://api.vvhan.com/api/hotlist/wbHot",
            "https://tenapi.cn/v2/wbhot",
            "https://api.aa1.cn/api/weibo-rs"
        ]
        
        for url in urls:
            try:
                logger.info(f"尝试获取微博热搜: {url}")
                
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    # 尝试解析JSON
                    try:
                        data = response.json()
                    except:
                        logger.warning(f"该API返回JSON解析失败")
                        continue
                    
                    # 处理不同的返回格式
                    hot_list = []
                    
                    if isinstance(data, list):
                        hot_list = data
                    elif isinstance(data, dict):
                        # 尝试各种可能的字段
                        for key in ['data', 'result', 'list', 'items']:
                            if key in data:
                                hot_list = data[key]
                                break
                    
                    if hot_list and len(hot_list) > 0:
                        logger.info(f"✅ 获取微博热搜成功: {len(hot_list)} 条 (API: {url})")
                        return hot_list
                    else:
                        logger.warning(f"该API返回空数据")
                        
            except Exception as e:
                logger.warning(f"该API失败: {e}")
                continue
        
        logger.error("❌ 所有微博热搜API都失败")
        return []
    
    def get_baidu_hot(self) -> List[Dict[str, Any]]:
        """
        获取百度热搜
        尝试多个API地址
        
        Returns:
            热搜列表
        """
        # 多个备用API地址
        urls = [
            "https://api.vvhan.com/api/hotlist/baiduRD",
            "https://tenapi.cn/v2/baiduhot",
            "https://api.aa1.cn/api/baidu-rs"
        ]
        
        for url in urls:
            try:
                logger.info(f"尝试获取百度热搜: {url}")
                
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    # 尝试解析JSON
                    try:
                        data = response.json()
                    except:
                        logger.warning(f"该API返回JSON解析失败")
                        continue
                    
                    # 处理不同的返回格式
                    hot_list = []
                    
                    if isinstance(data, list):
                        hot_list = data
                    elif isinstance(data, dict):
                        # 尝试各种可能的字段
                        for key in ['data', 'result', 'list', 'items']:
                            if key in data:
                                hot_list = data[key]
                                break
                    
                    if hot_list and len(hot_list) > 0:
                        logger.info(f"✅ 获取百度热搜成功: {len(hot_list)} 条 (API: {url})")
                        return hot_list
                    else:
                        logger.warning(f"该API返回空数据")
                        
            except Exception as e:
                logger.warning(f"该API失败: {e}")
                continue
        
        logger.error("❌ 所有百度热搜API都失败")
        return []
    
    def filter_stock_topics(self, hot_list: List[Dict]) -> List[Dict]:
        """
        过滤股票相关话题
        
        Args:
            hot_list: 热搜列表
            
        Returns:
            股票相关话题列表
        """
        filtered = []
        
        for item in hot_list:
            # 获取标题（支持多种字段名）
            title = str(item.get('title', '') or 
                       item.get('word', '') or 
                       item.get('query', '') or 
                       item.get('标题', ''))
            
            # 检查是否包含股票关键词
            if any(kw in title for kw in self.stock_keywords):
                item['is_stock_related'] = True
                item['matched_keywords'] = [kw for kw in self.stock_keywords if kw in title]
                filtered.append(item)
        
        logger.info(f"过滤出股票相关话题 {len(filtered)} 条")
        return filtered
    
    def get_all_stock_hot_topics(self) -> Dict[str, Any]:
        """
        获取所有平台的股票热搜话题
        
        Returns:
            包含所有平台热搜的字典
        """
        result = {
            'weibo': {'total': 0, 'stock_related': 0, 'topics': []},
            'baidu': {'total': 0, 'stock_related': 0, 'topics': []}
        }
        
        # 微博热搜
        weibo_hot = self.get_weibo_hot()
        if weibo_hot:
            result['weibo']['total'] = len(weibo_hot)
            result['weibo']['topics'] = self.filter_stock_topics(weibo_hot)
            result['weibo']['stock_related'] = len(result['weibo']['topics'])
        
        # 百度热搜
        baidu_hot = self.get_baidu_hot()
        if baidu_hot:
            result['baidu']['total'] = len(baidu_hot)
            result['baidu']['topics'] = self.filter_stock_topics(baidu_hot)
            result['baidu']['stock_related'] = len(result['baidu']['topics'])
        
        return result


# 全局实例
_hot_search_api = None

def get_hot_search_api():
    """获取热搜API实例（单例）"""
    global _hot_search_api
    if _hot_search_api is None:
        _hot_search_api = HotSearchAPI()
    return _hot_search_api
