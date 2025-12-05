#!/usr/bin/env python3
"""
统一新闻API接口
整合现有自制接口和AKShare接口
"""

from typing import List, Dict, Any
from datetime import datetime

from backend.dataflows.news.realtime_news import get_realtime_stock_news
from backend.dataflows.news.akshare_news_api import get_akshare_news_api
from backend.dataflows.news.improved_sentiment_analysis import get_sentiment_analyzer
from backend.utils.logging_config import get_logger

logger = get_logger("unified_news")


class UnifiedNewsAPI:
    """统一新闻API"""
    
    def __init__(self):
        """初始化"""
        self.akshare_api = get_akshare_news_api()
        self.sentiment_analyzer = get_sentiment_analyzer()
        logger.info("统一新闻API初始化完成")
    
    def get_stock_news_comprehensive(self, ticker: str) -> Dict[str, Any]:
        """
        获取股票的综合新闻数据
        整合多个数据源
        
        Args:
            ticker: 股票代码
            
        Returns:
            综合新闻数据
        """
        logger.info(f"开始获取{ticker}的综合新闻数据...")
        
        result = {
            'ticker': ticker,
            'timestamp': datetime.now().isoformat(),
            'sources': {},
            'summary': {}
        }
        
        # 数据源1: 实时新闻聚合器（已验证可用）
        try:
            logger.info(f"[数据源1] 实时新闻聚合器...")
            realtime_news = get_realtime_stock_news(
                ticker=ticker,
                curr_date=datetime.now().strftime('%Y-%m-%d'),
                hours_back=6
            )
            
            if realtime_news:
                # 解析新闻数量（从报告中提取）
                news_count = 0
                if isinstance(realtime_news, str):
                    # 从报告中提取新闻数量
                    import re
                    match = re.search(r'(获取到|\d+)条', realtime_news)
                    if match:
                        try:
                            news_count = int(re.search(r'\d+', match.group(0)).group())
                        except:
                            news_count = 10  # 默认值
                
                result['sources']['realtime_news'] = {
                    'status': 'success',
                    'data': realtime_news,
                    'count': news_count,
                    'source': '实时新闻聚合器（东方财富）'
                }
                logger.info(f"✅ 实时新闻聚合器成功: {news_count}条")
            else:
                result['sources']['realtime_news'] = {
                    'status': 'no_data',
                    'message': '未获取到数据'
                }
                logger.warning(f"⚠️ 实时新闻聚合器无数据")
                
        except Exception as e:
            logger.error(f"❌ 实时新闻聚合器失败: {e}")
            result['sources']['realtime_news'] = {
                'status': 'error',
                'message': str(e)
            }
        
        # 数据源2: AKShare个股新闻（已验证可用）
        try:
            logger.info(f"[数据源2] AKShare个股新闻...")
            akshare_news = self.akshare_api.get_stock_news(ticker, limit=20)
            
            if akshare_news:
                result['sources']['akshare_stock_news'] = {
                    'status': 'success',
                    'data': akshare_news,
                    'count': len(akshare_news),
                    'source': 'AKShare（东方财富）'
                }
                logger.info(f"✅ AKShare个股新闻成功: {len(akshare_news)}条")
            else:
                result['sources']['akshare_stock_news'] = {
                    'status': 'no_data',
                    'message': '未获取到数据'
                }
                logger.warning(f"⚠️ AKShare个股新闻无数据")
                
        except Exception as e:
            logger.error(f"❌ AKShare个股新闻失败: {e}")
            result['sources']['akshare_stock_news'] = {
                'status': 'error',
                'message': str(e)
            }
        
        # 数据源3: 财联社快讯（已验证可用）
        try:
            logger.info(f"[数据源3] 财联社快讯...")
            cls_news = self.akshare_api.get_cls_telegraph(limit=10)
            
            if cls_news:
                result['sources']['cls_telegraph'] = {
                    'status': 'success',
                    'data': cls_news,
                    'count': len(cls_news),
                    'source': '财联社'
                }
                logger.info(f"✅ 财联社快讯成功: {len(cls_news)}条")
            else:
                result['sources']['cls_telegraph'] = {
                    'status': 'no_data',
                    'message': '未获取到数据'
                }
                logger.warning(f"⚠️ 财联社快讯无数据")
                
        except Exception as e:
            logger.error(f"❌ 财联社快讯失败: {e}")
            result['sources']['cls_telegraph'] = {
                'status': 'error',
                'message': str(e)
            }
        
        # 数据源4: 微博热议（已验证可用）
        try:
            logger.info(f"[数据源4] 微博热议...")
            weibo_hot = self.akshare_api.get_weibo_stock_hot()
            
            if weibo_hot:
                result['sources']['weibo_hot'] = {
                    'status': 'success',
                    'data': weibo_hot,
                    'count': len(weibo_hot),
                    'source': '微博热议'
                }
                logger.info(f"✅ 微博热议成功: {len(weibo_hot)}条")
            else:
                result['sources']['weibo_hot'] = {
                    'status': 'no_data',
                    'message': '未获取到数据'
                }
                logger.warning(f"⚠️ 微博热议无数据")
                
        except Exception as e:
            logger.error(f"❌ 微博热议失败: {e}")
            result['sources']['weibo_hot'] = {
                'status': 'error',
                'message': str(e)
            }
        
        # 数据源5: 财经早餐（东方财富）
        try:
            logger.info(f"[数据源5] 财经早餐...")
            morning_news = self.akshare_api.get_morning_news()
            
            if morning_news:
                result['sources']['morning_news'] = {
                    'status': 'success',
                    'data': morning_news[:10],
                    'count': len(morning_news),
                    'source': '东方财富财经早餐'
                }
                logger.info(f"✅ 财经早餐成功: {len(morning_news)}条")
            else:
                result['sources']['morning_news'] = {
                    'status': 'no_data',
                    'message': '未获取到数据'
                }
                logger.warning(f"⚠️ 财经早餐无数据")
        except Exception as e:
            logger.error(f"❌ 财经早餐失败: {e}")
            result['sources']['morning_news'] = {'status': 'error', 'message': str(e)}
        
        # 数据源6: 全球财经新闻（东方财富）
        try:
            logger.info(f"[数据源6] 全球财经新闻...")
            global_news = self.akshare_api.get_global_news_em(limit=10)
            
            if global_news:
                result['sources']['global_news_em'] = {
                    'status': 'success',
                    'data': global_news,
                    'count': len(global_news),
                    'source': '东方财富全球新闻'
                }
                logger.info(f"✅ 全球财经新闻成功: {len(global_news)}条")
            else:
                result['sources']['global_news_em'] = {'status': 'no_data', 'message': '未获取到数据'}
        except Exception as e:
            logger.error(f"❌ 全球财经新闻失败: {e}")
            result['sources']['global_news_em'] = {'status': 'error', 'message': str(e)}
        
        # 数据源7: 新浪财经全球新闻
        try:
            logger.info(f"[数据源7] 新浪财经全球新闻...")
            sina_news = self.akshare_api.get_global_news_sina(limit=10)
            
            if sina_news:
                result['sources']['global_news_sina'] = {
                    'status': 'success',
                    'data': sina_news,
                    'count': len(sina_news),
                    'source': '新浪财经'
                }
                logger.info(f"✅ 新浪财经成功: {len(sina_news)}条")
            else:
                result['sources']['global_news_sina'] = {'status': 'no_data', 'message': '未获取到数据'}
        except Exception as e:
            logger.error(f"❌ 新浪财经失败: {e}")
            result['sources']['global_news_sina'] = {'status': 'error', 'message': str(e)}
        
        # 数据源8: 富途牛牛全球财经
        try:
            logger.info(f"[数据源8] 富途牛牛全球财经...")
            futu_news = self.akshare_api.get_futu_global_news(limit=10)
            
            if futu_news:
                result['sources']['futu_news'] = {
                    'status': 'success',
                    'data': futu_news,
                    'count': len(futu_news),
                    'source': '富途牛牛'
                }
                logger.info(f"✅ 富途牛牛成功: {len(futu_news)}条")
            else:
                result['sources']['futu_news'] = {'status': 'no_data', 'message': '未获取到数据'}
        except Exception as e:
            logger.error(f"❌ 富途牛牛失败: {e}")
            result['sources']['futu_news'] = {'status': 'error', 'message': str(e)}
        
        # 数据源9: 同花顺全球财经
        try:
            logger.info(f"[数据源9] 同花顺全球财经...")
            ths_news = self.akshare_api.get_ths_global_news(limit=10)
            
            if ths_news:
                result['sources']['ths_news'] = {
                    'status': 'success',
                    'data': ths_news,
                    'count': len(ths_news),
                    'source': '同花顺'
                }
                logger.info(f"✅ 同花顺成功: {len(ths_news)}条")
            else:
                result['sources']['ths_news'] = {'status': 'no_data', 'message': '未获取到数据'}
        except Exception as e:
            logger.error(f"❌ 同花顺失败: {e}")
            result['sources']['ths_news'] = {'status': 'error', 'message': str(e)}
        
        # 情绪分析
        try:
            logger.info(f"[情绪分析] 开始分析...")
            
            # 收集所有新闻用于情绪分析
            all_news = []
            
            # 从AKShare个股新闻提取
            if result['sources'].get('akshare_stock_news', {}).get('status') == 'success':
                all_news.extend(result['sources']['akshare_stock_news']['data'])
            
            # 进行情绪分析
            if all_news:
                sentiment = self.sentiment_analyzer.analyze_news_sentiment(all_news)
                result['summary']['sentiment'] = sentiment
                logger.info(f"✅ 情绪分析完成: {sentiment.get('sentiment_label')}")
            else:
                result['summary']['sentiment'] = {
                    'sentiment_score': 0.0,
                    'sentiment_label': '无数据',
                    'confidence': 0.0
                }
                logger.warning(f"⚠️ 情绪分析无数据")
                
        except Exception as e:
            logger.error(f"❌ 情绪分析失败: {e}")
            result['summary']['sentiment'] = {
                'error': str(e)
            }
        
        # 统计总结
        success_count = sum(1 for s in result['sources'].values() if s.get('status') == 'success')
        total_count = len(result['sources'])
        
        result['summary']['data_sources'] = {
            'total': total_count,
            'success': success_count,
            'success_rate': f"{success_count/total_count*100:.1f}%"
        }
        
        logger.info(f"✅ 综合新闻数据获取完成: {success_count}/{total_count} 个数据源成功")
        
        return result
    
    def get_market_news(self) -> Dict[str, Any]:
        """
        获取市场新闻
        
        Returns:
            市场新闻数据
        """
        logger.info("开始获取市场新闻...")
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'sources': {}
        }
        
        # 财经早餐
        try:
            morning_news = self.akshare_api.get_morning_news()
            if morning_news:
                result['sources']['morning_news'] = {
                    'status': 'success',
                    'data': morning_news[:10],  # 只取前10条
                    'count': len(morning_news),
                    'source': '东方财富财经早餐'
                }
                logger.info(f"✅ 财经早餐成功: {len(morning_news)}条")
        except Exception as e:
            logger.error(f"❌ 财经早餐失败: {e}")
            result['sources']['morning_news'] = {'status': 'error', 'message': str(e)}
        
        # 全球财经新闻
        try:
            global_news = self.akshare_api.get_global_news_em(limit=10)
            if global_news:
                result['sources']['global_news'] = {
                    'status': 'success',
                    'data': global_news,
                    'count': len(global_news),
                    'source': '东方财富全球新闻'
                }
                logger.info(f"✅ 全球新闻成功: {len(global_news)}条")
        except Exception as e:
            logger.error(f"❌ 全球新闻失败: {e}")
            result['sources']['global_news'] = {'status': 'error', 'message': str(e)}
        
        return result


# 全局实例
_unified_news_api = None

def get_unified_news_api():
    """获取统一新闻API实例（单例）"""
    global _unified_news_api
    if _unified_news_api is None:
        _unified_news_api = UnifiedNewsAPI()
    return _unified_news_api
