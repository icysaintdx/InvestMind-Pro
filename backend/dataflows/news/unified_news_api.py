#!/usr/bin/env python3
"""
统一新闻API接口
整合现有自制接口和AKShare接口
"""

from typing import List, Dict, Any
from datetime import datetime
import time
import threading

from backend.dataflows.news.realtime_news import get_realtime_stock_news
from backend.dataflows.news.akshare_news_api import get_akshare_news_api
from backend.dataflows.news.improved_sentiment_analysis import get_sentiment_analyzer
from backend.utils.logging_config import get_logger

logger = get_logger("unified_news")


# ==================== 新闻缓存系统 ====================

class NewsCache:
    """
    新闻缓存类
    用于避免短时间内重复请求同一股票的新闻数据
    """
    
    def __init__(self, ttl_seconds: int = 300):
        """
        初始化缓存
        
        Args:
            ttl_seconds: 缓存有效期（秒），默认5分钟
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ttl = ttl_seconds
        self._lock = threading.Lock()
        logger.info(f"📦 新闻缓存初始化完成，TTL={ttl_seconds}秒")
    
    def _get_cache_key(self, ticker: str) -> str:
        """生成缓存键"""
        return f"news_{ticker}"
    
    def get(self, ticker: str) -> Dict[str, Any] | None:
        """
        获取缓存数据
        
        Args:
            ticker: 股票代码
            
        Returns:
            缓存的数据，如果不存在或已过期则返回None
        """
        cache_key = self._get_cache_key(ticker)
        
        with self._lock:
            if cache_key not in self._cache:
                return None
            
            cache_entry = self._cache[cache_key]
            cached_time = cache_entry.get('timestamp', 0)
            current_time = time.time()
            
            # 检查是否过期
            if (current_time - cached_time) > self._ttl:
                # 缓存已过期，删除并返回None
                del self._cache[cache_key]
                logger.info(f"⏰ 缓存已过期: {ticker}")
                return None
            
            # 缓存有效
            remaining_ttl = self._ttl - (current_time - cached_time)
            logger.info(f"✅ 命中缓存: {ticker} (剩余{remaining_ttl:.1f}秒)")
            return cache_entry.get('data')
    
    def set(self, ticker: str, data: Dict[str, Any]) -> None:
        """
        设置缓存数据
        
        Args:
            ticker: 股票代码
            data: 要缓存的数据
        """
        cache_key = self._get_cache_key(ticker)
        
        with self._lock:
            self._cache[cache_key] = {
                'data': data,
                'timestamp': time.time()
            }
            logger.info(f"💾 已缓存: {ticker} (TTL={self._ttl}秒)")
    
    def clear(self, ticker: str = None) -> None:
        """
        清除缓存
        
        Args:
            ticker: 股票代码，如果为None则清除所有缓存
        """
        with self._lock:
            if ticker:
                cache_key = self._get_cache_key(ticker)
                if cache_key in self._cache:
                    del self._cache[cache_key]
                    logger.info(f"🗑️ 已清除缓存: {ticker}")
            else:
                self._cache.clear()
                logger.info(f"🗑️ 已清除所有缓存")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        with self._lock:
            current_time = time.time()
            valid_count = 0
            expired_count = 0
            
            for cache_key, entry in list(self._cache.items()):
                if (current_time - entry.get('timestamp', 0)) <= self._ttl:
                    valid_count += 1
                else:
                    expired_count += 1
            
            return {
                'total_entries': len(self._cache),
                'valid_entries': valid_count,
                'expired_entries': expired_count,
                'ttl_seconds': self._ttl
            }


# 全局缓存实例
_news_cache = NewsCache(ttl_seconds=300)  # 5分钟缓存


class UnifiedNewsAPI:
    """统一新闻API"""
    
    def __init__(self):
        """初始化"""
        self.akshare_api = get_akshare_news_api()
        self.sentiment_analyzer = get_sentiment_analyzer()
        self.cache = _news_cache  # 使用全局缓存
        logger.info("统一新闻API初始化完成")
    
    def get_stock_news_comprehensive(self, ticker: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        获取股票的综合新闻数据
        整合多个数据源
        
        Args:
            ticker: 股票代码
            use_cache: 是否使用缓存，默认True
            
        Returns:
            综合新闻数据
        """
        # ==================== 缓存检查 ====================
        if use_cache:
            cached_data = self.cache.get(ticker)
            if cached_data:
                # 更新时间戳为当前时间（表示这是缓存数据）
                cached_data['from_cache'] = True
                cached_data['cache_timestamp'] = cached_data.get('timestamp')
                cached_data['timestamp'] = datetime.now().isoformat()
                return cached_data
        
        logger.info(f"开始获取{ticker}的综合新闻数据...")
        
        result = {
            'ticker': ticker,
            'timestamp': datetime.now().isoformat(),
            'sources': {},
            'summary': {},
            'from_cache': False
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
                
                # 智能过滤：优先显示非中性新闻，但不少于30篇
                filtered_news = self._filter_news_by_sentiment(all_news)
                result['summary']['filtered_news'] = filtered_news
                result['summary']['filter_info'] = {
                    'total_count': len(all_news),
                    'filtered_count': len(filtered_news['news']),
                    'positive_count': filtered_news['positive_count'],
                    'negative_count': filtered_news['negative_count'],
                    'neutral_count': filtered_news['neutral_count'],
                    'filter_strategy': filtered_news['strategy']
                }
                logger.info(f"✅ 新闻过滤完成: {len(all_news)}条 -> {len(filtered_news['news'])}条 ({filtered_news['strategy']})")
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
        
        # ==================== 存入缓存 ====================
        if use_cache:
            self.cache.set(ticker, result)
        
        return result
    
    def _filter_news_by_sentiment(self, news_list: List[Dict]) -> Dict:
        """
        智能过滤新闻：优先显示非中性新闻，但不少于30篇
        
        规则：
        1. 如果非中性新闻 >= 30篇，只显示非中性
        2. 如果非中性新闻 < 30篇，显示所有非中性 + 部分中性，总数达到30篇
        3. 如果总数 < 30篇，显示全部
        
        Args:
            news_list: 新闻列表
            
        Returns:
            过滤后的新闻和统计信息
        """
        if not news_list:
            return {
                'news': [],
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
                'strategy': '无数据'
            }
        
        # 分类新闻
        positive_news = []
        negative_news = []
        neutral_news = []
        
        for news in news_list:
            title = news.get('title', '')
            content = news.get('content', '')
            text = f"{title} {content}"
            
            # 分析情绪
            score = self.sentiment_analyzer.analyze_text_sentiment(text)
            news['sentiment_score'] = score
            
            if score > 0.2:
                positive_news.append(news)
            elif score < -0.2:
                negative_news.append(news)
            else:
                neutral_news.append(news)
        
        non_neutral_count = len(positive_news) + len(negative_news)
        total_count = len(news_list)
        min_count = 30
        
        # 决策逻辑
        if non_neutral_count >= min_count:
            # 情况1：非中性新闻足够，只显示非中性
            filtered = positive_news + negative_news
            strategy = f'只显示非中性新闻 ({non_neutral_count}篇)'
        elif total_count <= min_count:
            # 情况2：总数不足，显示全部
            filtered = news_list
            strategy = f'总数不足，显示全部 ({total_count}篇)'
        else:
            # 情况3：非中性不足，补充中性新闻
            need_neutral = min_count - non_neutral_count
            filtered = positive_news + negative_news + neutral_news[:need_neutral]
            strategy = f'非中性{non_neutral_count}篇 + 中性{need_neutral}篇 = {len(filtered)}篇'
        
        # 按时间排序（最新的在前）
        filtered.sort(key=lambda x: x.get('publish_time', ''), reverse=True)
        
        return {
            'news': filtered,
            'positive_count': len(positive_news),
            'negative_count': len(negative_news),
            'neutral_count': len(neutral_news),
            'strategy': strategy
        }
    
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
    
    def clear_cache(self, ticker: str = None) -> Dict[str, Any]:
        """
        清除缓存
        
        Args:
            ticker: 股票代码，如果为None则清除所有缓存
            
        Returns:
            操作结果
        """
        self.cache.clear(ticker)
        return {
            'success': True,
            'message': f'已清除缓存: {ticker if ticker else "全部"}'
        }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        return self.cache.get_stats()


# 全局实例
_unified_news_api = None

def get_unified_news_api():
    """获取统一新闻API实例（单例）"""
    global _unified_news_api
    if _unified_news_api is None:
        _unified_news_api = UnifiedNewsAPI()
    return _unified_news_api
