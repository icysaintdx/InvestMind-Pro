#!/usr/bin/env python3
"""
巨潮资讯网爬虫
获取上市公司公告信息
"""

import requests
from typing import List, Dict, Any
from datetime import datetime, timedelta
from backend.utils.logging_config import get_logger

logger = get_logger("cninfo_crawler")


class CninfoCrawler:
    """巨潮资讯网爬虫"""
    
    def __init__(self):
        """初始化"""
        self.session = requests.Session()
        # 根据巨潮资讯网真实接口要求设置请求头
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'http://www.cninfo.com.cn/new/disclosure',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'http://www.cninfo.com.cn',
            'Connection': 'keep-alive'
        })
        
        # 巨潮资讯网API
        self.base_url = "http://www.cninfo.com.cn"
        self.api_url = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
        self.static_url = "http://static.cninfo.com.cn"
        
        logger.info("巨潮资讯网爬虫初始化完成")
    
    def get_company_announcements(
        self, 
        stock_code: str, 
        days: int = 30,
        announcement_type: str = None
    ) -> List[Dict[str, Any]]:
        """
        获取公司公告
        
        Args:
            stock_code: 股票代码
            days: 回溯天数
            announcement_type: 公告类型（如：年报、季报、重大事项等）
            
        Returns:
            公告列表
        """
        try:
            logger.info(f"获取{stock_code}的公司公告...")
            
            # 清理股票代码
            clean_code = stock_code.replace('.SH', '').replace('.SZ', '')
            
            # 判断市场（上交所/深交所）
            if clean_code.startswith('6'):
                plate = 'sh'  # 上交所
                column = 'sse'  # 上海证券交易所
            else:
                plate = 'sz'  # 深交所
                column = 'szse'  # 深圳证券交易所
            
            # 计算日期范围（缩短到最近7天）
            end_date = datetime.now()
            start_date = end_date - timedelta(days=min(days, 7))
            
            # 根据巨潮资讯网真实接口构建请求参数
            params = {
                'pageNum': '1',
                'pageSize': '10',  # 减小数量
                'stock': clean_code,
                'searchkey': '',  # 搜索关键词
                'category': announcement_type or '',  # 公告类型
                'trade': '',
                'column': column,
                'columnTitle': '历史公告查询',
                'pageNum': '1',
                'pageSize': '10',
                'tabName': 'fulltext',
                'plate': plate,
                'seDate': f"{start_date.strftime('%Y-%m-%d')}~{end_date.strftime('%Y-%m-%d')}",
                'sortName': '',
                'sortType': '',
                'isHLtitle': 'true'
            }
            
            logger.info(f"请求参数: stock={clean_code}, plate={plate}, column={column}, 日期={params['seDate']}")
            
            # 发送真实的API请求
            try:
                response = self.session.post(self.api_url, data=params, timeout=10)
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"原始API响应: {result}")
                logger.info(f"响应类型: {type(result)}")
                logger.info(f"响应keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
                
                # 解析响应数据
                announcements = self._parse_announcements(result, stock_code)
                
                if announcements:
                    logger.info(f"✅ 获取到{len(announcements)}条公告")
                else:
                    logger.warning(f"⚠️ 未获取到{stock_code}的公告数据")
                
                return announcements
                
            except requests.exceptions.RequestException as e:
                logger.error(f"❌ API请求失败: {e}")
                # 如果真实API失败，返回空列表
                return []
            
        except Exception as e:
            logger.error(f"❌ 获取公告失败: {e}")
            return []
    
    def _parse_announcements(self, result: dict, stock_code: str) -> List[Dict[str, Any]]:
        """
        解析API响应数据
        
        Args:
            result: API响应结果
            stock_code: 股票代码
            
        Returns:
            公告列表
        """
        try:
            announcements = []
            
            # 检查响应格式
            if not isinstance(result, dict):
                logger.error("❌ API响应格式错误")
                return []
            
            # 巨潮资讯网API响应格式: {"announcements": [...], "totalAnnouncement": N}
            # 或者: {"hasMore": true, "announcements": [...]}
            ann_list = result.get('announcements', [])
            
            if not ann_list:
                logger.warning("⚠️ API返回空数据")
                return []
            
            for ann in ann_list:
                try:
                    # 解析单条公告
                    # 根据巨潮资讯网真实接口，PDF下载地址需要拼接static.cninfo.com.cn
                    adjunct_url = ann.get('adjunctUrl', '')
                    if adjunct_url:
                        full_url = f"{self.static_url}{adjunct_url}"
                    else:
                        full_url = ''
                    
                    parsed = {
                        'announcement_id': ann.get('announcementId', ''),
                        'stock_code': stock_code,
                        'title': ann.get('announcementTitle', ''),
                        'type': ann.get('announcementType', '其他'),
                        'publish_date': ann.get('adjunctPublishDate', ''),
                        'url': full_url,
                        'summary': ann.get('announcementContent', '')[:200] if ann.get('announcementContent') else '',
                        'importance': self._judge_importance(ann.get('announcementType', ''))
                    }
                    announcements.append(parsed)
                except Exception as e:
                    logger.warning(f"⚠️ 解析单条公告失败: {e}")
                    continue
            
            return announcements
            
        except Exception as e:
            logger.error(f"❌ 解析公告数据失败: {e}")
            return []
    
    def _judge_importance(self, announcement_type: str) -> str:
        """
        判断公告重要程度
        
        Args:
            announcement_type: 公告类型
            
        Returns:
            重要程度: high/medium/low
        """
        high_priority = ['定期报告', '业绩预告', '业绩快报', '重大事项', '重组', '诉讼', '处罚', '立案调查']
        medium_priority = ['股东大会', '董事会', '增发', '配股', '分红']
        
        for keyword in high_priority:
            if keyword in announcement_type:
                return 'high'
        
        for keyword in medium_priority:
            if keyword in announcement_type:
                return 'medium'
        
        return 'low'
    
    def _mock_announcements(self, stock_code: str) -> List[Dict[str, Any]]:
        """
        模拟公告数据（用于测试）
        实际使用时需要替换为真实的API调用
        """
        return [
            {
                'announcement_id': 'MOCK001',
                'stock_code': stock_code,
                'title': '2024年第三季度报告',
                'type': '定期报告',
                'publish_date': '2024-10-30',
                'url': 'http://www.cninfo.com.cn/mock/001.pdf',
                'summary': '公司2024年第三季度营业收入...',
                'importance': 'high'
            },
            {
                'announcement_id': 'MOCK002',
                'stock_code': stock_code,
                'title': '关于董事会决议的公告',
                'type': '重大事项',
                'publish_date': '2024-11-15',
                'url': 'http://www.cninfo.com.cn/mock/002.pdf',
                'summary': '公司董事会审议通过...',
                'importance': 'medium'
            },
            {
                'announcement_id': 'MOCK003',
                'stock_code': stock_code,
                'title': '股东大会决议公告',
                'type': '股东大会',
                'publish_date': '2024-11-20',
                'url': 'http://www.cninfo.com.cn/mock/003.pdf',
                'summary': '公司股东大会审议通过...',
                'importance': 'high'
            }
        ]
    
    def filter_important_announcements(
        self, 
        announcements: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        过滤重要公告
        
        Args:
            announcements: 公告列表
            
        Returns:
            重要公告列表
        """
        # 重要公告类型
        important_types = [
            '定期报告', '业绩预告', '业绩快报',
            '重大事项', '股东大会', '董事会',
            '增发', '配股', '分红', '重组',
            '诉讼', '仲裁', '处罚', '立案调查'
        ]
        
        important = []
        for ann in announcements:
            ann_type = ann.get('type', '')
            if any(t in ann_type for t in important_types):
                important.append(ann)
        
        logger.info(f"过滤出{len(important)}条重要公告")
        return important
    
    def analyze_announcements(
        self, 
        announcements: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        分析公告
        
        Args:
            announcements: 公告列表
            
        Returns:
            分析结果
        """
        if not announcements:
            return {
                'total': 0,
                'important_count': 0,
                'types': {},
                'summary': '暂无公告'
            }
        
        # 统计公告类型
        types = {}
        for ann in announcements:
            ann_type = ann.get('type', '其他')
            types[ann_type] = types.get(ann_type, 0) + 1
        
        # 过滤重要公告
        important = self.filter_important_announcements(announcements)
        
        return {
            'total': len(announcements),
            'important_count': len(important),
            'types': types,
            'recent_announcements': announcements[:5],
            'important_announcements': important[:5],
            'summary': f'共{len(announcements)}条公告，其中重要公告{len(important)}条'
        }


# 全局实例
_cninfo_crawler = None

def get_cninfo_crawler():
    """获取巨潮资讯网爬虫实例（单例）"""
    global _cninfo_crawler
    if _cninfo_crawler is None:
        _cninfo_crawler = CninfoCrawler()
    return _cninfo_crawler
