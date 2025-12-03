"""
中国市场数据爬虫
集成东方财富、新浪财经、雪球、财联社等数据源
"""

import os
import re
import json
import time
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import akshare as ak
import tushare as ts

from backend.utils.logging_config import get_logger
from backend.utils.tool_logging import log_data_fetch

logger = get_logger("china_market_crawler")


class ChinaMarketCrawler:
    """中国市场数据爬虫"""
    
    def __init__(self):
        """初始化爬虫"""
        # Tushare配置
        self.tushare_token = os.getenv('TUSHARE_TOKEN')
        self.pro = None
        if self.tushare_token:
            ts.set_token(self.tushare_token)
            self.pro = ts.pro_api()
            logger.info("Tushare API已初始化")
        else:
            logger.warning("未配置TUSHARE_TOKEN，部分功能受限")
            
        # 请求头配置
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }
        
        # 会话管理
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
    @log_data_fetch("东方财富新闻")
    def get_eastmoney_news(self, stock_code: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取东方财富网新闻
        
        Args:
            stock_code: 股票代码
            limit: 获取数量限制
            
        Returns:
            新闻列表
        """
        try:
            news_list = []
            
            # 清理股票代码
            clean_code = stock_code.replace('.SH', '').replace('.SZ', '').replace('.HK', '')
            
            # 判断市场
            if clean_code.startswith(('60', '68')):
                market = '1'  # 上证
            else:
                market = '0'  # 深证
                
            # 东方财富新闻API
            url = f"https://emweb.securities.eastmoney.com/PC_HSF10/NewsBulletin/PageAjax"
            
            params = {
                'code': f"{clean_code}{market}",
                'pageSize': limit,
                'pageIndex': 1,
                'type': '0'  # 0:全部, 1:公告, 2:新闻
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('result') and data['result'].get('data'):
                    for item in data['result']['data']:
                        news_item = {
                            'title': item.get('title', ''),
                            'source': '东方财富',
                            'publish_time': item.get('publishTime', ''),
                            'url': item.get('url', ''),
                            'content': item.get('content', ''),
                            'type': item.get('type', '新闻')
                        }
                        news_list.append(news_item)
                        
            logger.success(f"获取东方财富新闻 {len(news_list)} 条")
            return news_list
            
        except Exception as e:
            logger.error(f"获取东方财富新闻失败: {str(e)}")
            return []
            
    @log_data_fetch("新浪财经新闻")
    def get_sina_news(self, stock_code: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取新浪财经新闻
        
        Args:
            stock_code: 股票代码
            limit: 获取数量限制
            
        Returns:
            新闻列表
        """
        try:
            news_list = []
            
            # 清理股票代码
            clean_code = stock_code.replace('.SH', '').replace('.SZ', '').replace('.HK', '')
            
            # 判断市场前缀
            if clean_code.startswith(('60', '68')):
                sina_code = f"sh{clean_code}"
            else:
                sina_code = f"sz{clean_code}"
                
            # 新浪财经API
            url = "https://vip.stock.finance.sina.com.cn/corp/view/vCB_AllNewsStock.php"
            params = {
                'symbol': sina_code,
                'num': limit
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.encoding = 'gb2312'
            
            if response.status_code == 200:
                # 解析HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                news_items = soup.find_all('div', class_='datelist')
                
                for item in news_items[:limit]:
                    link = item.find('a')
                    if link:
                        news_item = {
                            'title': link.text.strip(),
                            'source': '新浪财经',
                            'url': link.get('href', ''),
                            'publish_time': item.find('span').text if item.find('span') else '',
                            'type': '新闻'
                        }
                        news_list.append(news_item)
                        
            logger.success(f"获取新浪财经新闻 {len(news_list)} 条")
            return news_list
            
        except Exception as e:
            logger.error(f"获取新浪财经新闻失败: {str(e)}")
            return []
            
    @log_data_fetch("雪球评论")
    def get_xueqiu_comments(self, stock_code: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取雪球网评论舆情
        
        Args:
            stock_code: 股票代码
            limit: 获取数量限制
            
        Returns:
            评论列表
        """
        try:
            comments_list = []
            
            # 清理股票代码
            clean_code = stock_code.replace('.SH', '').replace('.SZ', '').replace('.HK', '')
            
            # 判断市场前缀
            if clean_code.startswith(('60', '68')):
                xq_symbol = f"SH{clean_code}"
            elif clean_code.startswith(('00', '30')):
                xq_symbol = f"SZ{clean_code}"
            else:
                xq_symbol = clean_code
                
            # 雪球API (需要cookie认证)
            url = f"https://xueqiu.com/statuses/stock_timeline.json"
            
            params = {
                'symbol_id': xq_symbol,
                'count': limit,
                'source': 'all',
                'page': 1
            }
            
            # 需要先访问主页获取cookie
            self.session.get("https://xueqiu.com", timeout=10)
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('list'):
                    for item in data['list']:
                        comment = {
                            'content': item.get('text', ''),
                            'author': item.get('user', {}).get('screen_name', ''),
                            'publish_time': datetime.fromtimestamp(
                                item.get('created_at', 0) / 1000
                            ).strftime('%Y-%m-%d %H:%M:%S'),
                            'likes': item.get('like_count', 0),
                            'comments': item.get('reply_count', 0),
                            'source': '雪球',
                            'type': '评论'
                        }
                        comments_list.append(comment)
                        
            logger.success(f"获取雪球评论 {len(comments_list)} 条")
            return comments_list
            
        except Exception as e:
            logger.error(f"获取雪球评论失败: {str(e)}")
            return []
            
    @log_data_fetch("财联社快讯")
    def get_cls_news(self, keywords: Optional[str] = None, limit: int = 30) -> List[Dict[str, Any]]:
        """
        获取财联社7x24小时快讯
        
        Args:
            keywords: 关键词筛选
            limit: 获取数量限制
            
        Returns:
            快讯列表
        """
        try:
            news_list = []
            
            # 财联社快讯API
            url = "https://www.cls.cn/api/telegraph"
            
            params = {
                'app': 'CailianpressWeb',
                'category': '',
                'lastTime': '',
                'limit': limit,
                'os': 'web',
                'refresh_type': 0,
                'rn': limit
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('data') and data['data'].get('roll_data'):
                    for item in data['data']['roll_data']:
                        # 如果指定了关键词，进行筛选
                        content = item.get('content', '')
                        if keywords and keywords not in content:
                            continue
                            
                        news_item = {
                            'title': item.get('title', '')[:50] if item.get('title') else content[:50],
                            'content': content,
                            'source': '财联社',
                            'publish_time': datetime.fromtimestamp(
                                item.get('ctime', 0)
                            ).strftime('%Y-%m-%d %H:%M:%S'),
                            'importance': item.get('level', 0),
                            'type': '快讯'
                        }
                        news_list.append(news_item)
                        
            logger.success(f"获取财联社快讯 {len(news_list)} 条")
            return news_list
            
        except Exception as e:
            logger.error(f"获取财联社快讯失败: {str(e)}")
            return []
            
    @log_data_fetch("Tushare新闻")
    def get_tushare_news(self, stock_code: str, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """
        获取Tushare财经新闻
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            
        Returns:
            新闻列表
        """
        if not self.pro:
            logger.warning("Tushare未初始化，跳过")
            return []
            
        try:
            news_list = []
            
            # 设置日期范围
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
                
            # 获取新闻
            df = self.pro.news(
                src='sina',  # 新浪财经
                start_date=start_date,
                end_date=end_date
            )
            
            if df is not None and not df.empty:
                # 筛选相关新闻
                clean_code = stock_code.replace('.SH', '').replace('.SZ', '')
                
                for _, row in df.iterrows():
                    # 检查内容是否包含股票代码
                    if clean_code in str(row.get('title', '')) or clean_code in str(row.get('content', '')):
                        news_item = {
                            'title': row.get('title', ''),
                            'content': row.get('content', ''),
                            'source': 'Tushare-' + row.get('src', '新浪'),
                            'publish_time': row.get('datetime', ''),
                            'type': '新闻'
                        }
                        news_list.append(news_item)
                        
            logger.success(f"获取Tushare新闻 {len(news_list)} 条")
            return news_list
            
        except Exception as e:
            logger.error(f"获取Tushare新闻失败: {str(e)}")
            return []
            
    @log_data_fetch("AkShare新闻")
    def get_akshare_news(self, stock_code: str) -> List[Dict[str, Any]]:
        """
        使用AkShare获取股票新闻
        
        Args:
            stock_code: 股票代码
            
        Returns:
            新闻列表
        """
        try:
            news_list = []
            
            # 获取个股新闻
            df = ak.stock_news_em(symbol=stock_code)
            
            if df is not None and not df.empty:
                for _, row in df.iterrows():
                    news_item = {
                        'title': row.get('新闻标题', ''),
                        'content': row.get('新闻内容', ''),
                        'source': 'AkShare-东财',
                        'publish_time': str(row.get('发布时间', '')),
                        'url': row.get('新闻链接', ''),
                        'type': '新闻'
                    }
                    news_list.append(news_item)
                    
            logger.success(f"获取AkShare新闻 {len(news_list)} 条")
            return news_list
            
        except Exception as e:
            logger.error(f"获取AkShare新闻失败: {str(e)}")
            return []
            
    def get_all_news(self, stock_code: str, sources: List[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        从所有源获取新闻
        
        Args:
            stock_code: 股票代码
            sources: 指定数据源列表，None表示全部
            
        Returns:
            分源新闻字典
        """
        all_news = {}
        
        # 默认获取所有源
        if sources is None:
            sources = ['eastmoney', 'sina', 'xueqiu', 'cls', 'tushare', 'akshare']
            
        # 逐个获取
        if 'eastmoney' in sources:
            all_news['eastmoney'] = self.get_eastmoney_news(stock_code)
            
        if 'sina' in sources:
            all_news['sina'] = self.get_sina_news(stock_code)
            
        if 'xueqiu' in sources:
            all_news['xueqiu'] = self.get_xueqiu_comments(stock_code)
            
        if 'cls' in sources:
            all_news['cls'] = self.get_cls_news(keywords=stock_code[:6])
            
        if 'tushare' in sources and self.pro:
            all_news['tushare'] = self.get_tushare_news(stock_code)
            
        if 'akshare' in sources:
            all_news['akshare'] = self.get_akshare_news(stock_code)
            
        # 统计
        total_count = sum(len(news) for news in all_news.values())
        logger.info(f"共获取 {total_count} 条新闻，来自 {len(all_news)} 个数据源")
        
        return all_news
        
    def analyze_sentiment(self, text: str) -> float:
        """
        简单的情绪分析
        
        Args:
            text: 文本内容
            
        Returns:
            情绪分数 (-1 到 1)
        """
        # 正面词汇
        positive_words = [
            '上涨', '增长', '突破', '新高', '利好', '强势', '买入', '看涨',
            '增持', '超预期', '创新高', '大涨', '反弹', '拉升', '涨停',
            '牛市', '向好', '改善', '提升', '优秀', '领先'
        ]
        
        # 负面词汇
        negative_words = [
            '下跌', '下降', '破位', '新低', '利空', '弱势', '卖出', '看跌',
            '减持', '低于预期', '创新低', '大跌', '回调', '杀跌', '跌停',
            '熊市', '恶化', '下滑', '亏损', '风险', '警惕'
        ]
        
        # 计算情绪分数
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count + negative_count == 0:
            return 0.0
            
        sentiment = (positive_count - negative_count) / (positive_count + negative_count)
        
        return max(-1.0, min(1.0, sentiment))


# 测试代码
if __name__ == "__main__":
    # 创建爬虫实例
    crawler = ChinaMarketCrawler()
    
    # 测试股票代码
    test_stock = "600519"  # 茅台
    
    print(f"测试获取 {test_stock} 的新闻数据")
    print("=" * 60)
    
    # 测试各个数据源
    print("\n1. 东方财富新闻:")
    eastmoney_news = crawler.get_eastmoney_news(test_stock, limit=3)
    for news in eastmoney_news[:2]:
        print(f"  - {news['title'][:30]}...")
        
    print("\n2. 新浪财经新闻:")
    sina_news = crawler.get_sina_news(test_stock, limit=3)
    for news in sina_news[:2]:
        print(f"  - {news['title'][:30]}...")
        
    print("\n3. 财联社快讯:")
    cls_news = crawler.get_cls_news(limit=5)
    for news in cls_news[:2]:
        print(f"  - {news['title'][:30]}...")
        
    # 测试情绪分析
    print("\n4. 情绪分析测试:")
    test_texts = [
        "股价大涨，突破新高，强势买入",
        "股价下跌，风险加大，建议卖出",
        "公司发布财报，业绩符合预期"
    ]
    
    for text in test_texts:
        sentiment = crawler.analyze_sentiment(text)
        print(f"  文本: {text}")
        print(f"  情绪: {sentiment:.2f}")
        
    print("\n测试完成！")
