"""
多源新闻聚合器
整合Tushare、AKShare、东方财富等多个数据源的新闻
支持智能内容截取和关键词高亮
"""

import os
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd

from backend.utils.logging_config import get_logger

logger = get_logger("news.multi_source")


def extract_relevant_content(content: str, stock_code: str, stock_name: str = '', max_length: int = 300) -> str:
    """
    智能提取与股票相关的内容片段

    Args:
        content: 原始新闻内容
        stock_code: 股票代码 (如 600519)
        stock_name: 股票名称 (如 贵州茅台)
        max_length: 最大返回长度

    Returns:
        与股票相关的内容片段
    """
    if not content:
        return ''

    # 构建关键词列表
    keywords = [stock_code]
    if stock_name:
        keywords.append(stock_name)
        # 添加简称 (如 "茅台")
        if len(stock_name) >= 4:
            keywords.append(stock_name[2:])

    # 按句子分割
    sentences = re.split(r'[。！？\n]', content)

    # 查找包含关键词的句子
    relevant_sentences = []
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence or len(sentence) < 5:
            continue
        if any(kw in sentence for kw in keywords):
            relevant_sentences.append(sentence)

    # 如果找到相关句子，返回这些句子
    if relevant_sentences:
        result = '。'.join(relevant_sentences[:3])
        if len(result) > max_length:
            result = result[:max_length] + '...'
        return result + '。'

    # 如果没有找到相关句子，返回开头内容
    if len(content) > max_length:
        return content[:max_length] + '...'
    return content


class MultiSourceNewsAggregator:
    """多源新闻聚合器"""
    
    def __init__(self):
        self.tushare_token = os.getenv('TUSHARE_TOKEN', '')
        self.tushare_api = None
        
        # 初始化Tushare
        if self.tushare_token:
            try:
                import tushare as ts
                ts.set_token(self.tushare_token)
                self.tushare_api = ts.pro_api()
                logger.info("✅ Tushare新闻API初始化成功")
            except Exception as e:
                logger.error(f"❌ Tushare初始化失败: {e}")
        
        logger.info("多源新闻聚合器初始化完成")
    
    def get_stock_news_tushare(
        self, 
        ts_code: str, 
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        从Tushare获取股票新闻
        
        注意: Tushare的新闻接口需要较高积分(5000+)
        接口: news (需要5000积分)
        
        Args:
            ts_code: 股票代码，如600519.SH
            start_date: 开始日期 YYYYMMDD
            end_date: 结束日期 YYYYMMDD
            limit: 返回数量限制
        """
        if not self.tushare_api:
            logger.warning("⚠️ Tushare API不可用")
            return []
        
        try:
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
            
            logger.info(f"📰 获取{ts_code}的Tushare新闻...")
            
            # 调用Tushare新闻接口
            df = self.tushare_api.news(
                src='sina',  # 新浪财经
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
            
            if df is None or df.empty:
                logger.info("ℹ️ Tushare未返回新闻数据")
                return []
            
            # 过滤与目标股票相关的新闻
            # Tushare新闻包含content字段，可以搜索股票代码
            stock_code = ts_code.split('.')[0]  # 提取纯代码
            filtered_df = df[df['content'].str.contains(stock_code, na=False)]
            
            news_list = []
            for _, row in filtered_df.iterrows():
                news_list.append({
                    'title': row.get('title', ''),
                    'content': row.get('content', '')[:200],  # 截取前200字
                    'pub_time': row.get('datetime', ''),
                    'source': 'Tushare-' + row.get('channels', 'Unknown'),
                    'url': row.get('url', '')
                })
            
            logger.info(f"✅ Tushare获取新闻: {len(news_list)}条")
            return news_list[:limit]
            
        except Exception as e:
            error_msg = str(e)
            if '权限' in error_msg or 'permission' in error_msg.lower():
                logger.warning("⚠️ Tushare新闻接口需要5000积分")
            else:
                logger.error(f"❌ Tushare获取新闻失败: {e}")
            return []
    
    def get_stock_news_akshare(
        self,
        symbol: str,
        stock_name: str = '',
        limit: int = 20
    ) -> List[Dict]:
        """
        从AKShare获取股票新闻(多接口降级策略)

        接口优先级:
        1. stock_news_em - 东方财富个股新闻
        2. stock_info_global_em - 东方财富全球资讯(关键词过滤)
        3. stock_info_global_cls - 财联社全球资讯(关键词过滤)
        4. news_economic_baidu - 百度财经新闻(关键词过滤)

        Args:
            symbol: 股票代码(6位数字)，如603777
            stock_name: 股票名称，用于关键词过滤
            limit: 返回数量限制
        """
        try:
            import akshare as ak

            # 转换股票代码格式
            if '.' in symbol:
                symbol = symbol.split('.')[0]

            logger.info(f"📰 获取{symbol}的AKShare新闻...")
            news_list = []

            # 方法1: 调用stock_news_em接口 (东方财富个股新闻)
            try:
                df = ak.stock_news_em(symbol=symbol)
                if df is not None and not df.empty:
                    news_list = self._parse_news_dataframe(df, limit, 'AKShare-东方财富', symbol, stock_name)
                    if news_list:
                        logger.info(f"✅ stock_news_em获取新闻: {len(news_list)}条")
                        return news_list
            except Exception as e:
                logger.debug(f"stock_news_em接口调用失败: {e}")

            # 方法2: 使用东方财富全球资讯 (关键词过滤)
            try:
                df = ak.stock_info_global_em()
                if df is not None and not df.empty:
                    # 过滤包含股票代码或名称的新闻
                    keywords = [symbol]
                    if stock_name:
                        keywords.append(stock_name)
                        if len(stock_name) >= 4:
                            keywords.append(stock_name[2:])

                    filtered_news = []
                    for _, row in df.iterrows():
                        title = str(row.get('标题', ''))
                        summary = str(row.get('摘要', ''))
                        if any(kw in title or kw in summary for kw in keywords):
                            filtered_news.append({
                                'title': title,
                                'content': extract_relevant_content(summary, symbol, stock_name),
                                'pub_time': str(row.get('发布时间', '')),
                                'source': 'AKShare-东方财富全球',
                                'url': str(row.get('链接', ''))
                            })
                        if len(filtered_news) >= limit:
                            break

                    if filtered_news:
                        logger.info(f"✅ stock_info_global_em过滤获取: {len(filtered_news)}条")
                        return filtered_news
            except Exception as e:
                logger.debug(f"stock_info_global_em失败: {e}")

            # 方法3: 使用财联社全球资讯 (关键词过滤)
            try:
                df = ak.stock_info_global_cls()
                if df is not None and not df.empty:
                    keywords = [symbol]
                    if stock_name:
                        keywords.append(stock_name)
                        if len(stock_name) >= 4:
                            keywords.append(stock_name[2:])

                    filtered_news = []
                    for _, row in df.iterrows():
                        title = str(row.get('标题', ''))
                        content = str(row.get('内容', ''))
                        if any(kw in title or kw in content for kw in keywords):
                            filtered_news.append({
                                'title': title,
                                'content': extract_relevant_content(content, symbol, stock_name),
                                'pub_time': str(row.get('发布日期', '')) + ' ' + str(row.get('发布时间', '')),
                                'source': 'AKShare-财联社',
                                'url': ''
                            })
                        if len(filtered_news) >= limit:
                            break

                    if filtered_news:
                        logger.info(f"✅ stock_info_global_cls过滤获取: {len(filtered_news)}条")
                        return filtered_news
            except Exception as e:
                logger.debug(f"stock_info_global_cls失败: {e}")

            # 方法4: 使用百度财经新闻 (关键词过滤)
            try:
                df = ak.news_economic_baidu()
                if df is not None and not df.empty:
                    keywords = [symbol]
                    if stock_name:
                        keywords.append(stock_name)
                        if len(stock_name) >= 4:
                            keywords.append(stock_name[2:])

                    filtered_news = []
                    for _, row in df.iterrows():
                        title = str(row.get('标题', ''))
                        content = str(row.get('内容', ''))
                        if any(kw in title or kw in content for kw in keywords):
                            filtered_news.append({
                                'title': title,
                                'content': extract_relevant_content(content, symbol, stock_name),
                                'pub_time': str(row.get('发布时间', '')),
                                'source': 'AKShare-百度财经',
                                'url': str(row.get('链接', ''))
                            })
                        if len(filtered_news) >= limit:
                            break

                    if filtered_news:
                        logger.info(f"✅ news_economic_baidu过滤获取: {len(filtered_news)}条")
                        return filtered_news
            except Exception as e:
                logger.debug(f"news_economic_baidu失败: {e}")

            # 方法5: 使用已有的realtime_news作为备选
            logger.info("尝试使用备用新闻源...")
            return self._get_news_from_realtime(symbol, limit)

        except ImportError:
            logger.error("❌ AKShare库未安装")
            return []
        except Exception as e:
            logger.error(f"❌ AKShare获取新闻失败: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return []

    def _parse_news_dataframe(self, df, limit: int, source: str, stock_code: str = '', stock_name: str = '') -> List[Dict]:
        """解析新闻DataFrame为列表，支持智能内容截取"""
        news_list = []
        for _, row in df.head(limit).iterrows():
            try:
                # 确保所有字段都转换为字符串
                title = str(row.get('新闻标题', row.get('标题', '')) or '')
                content = str(row.get('新闻内容', row.get('内容', '')) or '')
                pub_time = str(row.get('发布时间', row.get('时间', '')) or '')
                url = str(row.get('新闻链接', row.get('链接', '')) or '')

                if not title:  # 跳过空标题
                    continue

                # 使用智能内容截取
                if stock_code or stock_name:
                    processed_content = extract_relevant_content(content, stock_code, stock_name)
                else:
                    processed_content = content[:300] + '...' if len(content) > 300 else content

                news_list.append({
                    'title': title,
                    'content': processed_content,
                    'pub_time': pub_time,
                    'source': source,
                    'url': url
                })
            except Exception as e:
                logger.debug(f"跳过一条新闻: {e}")
                continue
        return news_list
    
    def _get_news_from_realtime(self, symbol: str, limit: int = 10) -> List[Dict]:
        """
        使用已有的realtime_news作为备用新闻源
        尝试解析出独立的新闻条目
        """
        try:
            from backend.dataflows.news.realtime_news import get_realtime_stock_news
            from datetime import datetime
            import re

            logger.info("🔄 使用备用新闻源(realtime_news)")

            # 调用已有的realtime_news接口
            news_report = get_realtime_stock_news(
                ticker=symbol,
                curr_date=datetime.now().strftime('%Y-%m-%d'),
                hours_back=24
            )

            if not news_report or not isinstance(news_report, str):
                return []

            news_list = []

            # 解析新闻报告格式：
            # ### 新闻标题
            # 📅 发布时间
            # 🔗 新闻链接
            # 新闻内容

            lines = news_report.split('\n')
            current_news = None

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # 检测新闻标题行（以 ### 开头）
                if line.startswith('### '):
                    # 保存之前的新闻
                    if current_news and current_news.get('title'):
                        news_list.append(current_news)
                        if len(news_list) >= limit:
                            break

                    # 开始新的新闻条目
                    title = line[4:].strip()
                    # 跳过无效标题（时间、URL等）
                    if title and not title.startswith('http') and not re.match(r'^\d{4}-\d{2}-\d{2}', title):
                        current_news = {
                            'title': title,
                            'content': '',
                            'pub_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'source': 'RealTime-东方财富',
                            'url': ''
                        }
                    else:
                        current_news = None
                    continue

                # 如果当前没有有效的新闻条目，跳过
                if not current_news:
                    continue

                # 解析发布时间
                if line.startswith('📅 '):
                    current_news['pub_time'] = line[2:].strip()
                    continue

                # 解析新闻链接
                if line.startswith('🔗 '):
                    current_news['url'] = line[2:].strip()
                    continue

                # 跳过标题行、分隔线和元数据行
                if line.startswith('#') or line.startswith('=') or line.startswith('-'):
                    continue
                if line.startswith('📅') or line.startswith('📊') or line.startswith('🕒'):
                    continue

                # 其他内容作为新闻内容
                if current_news and len(line) > 5:
                    if current_news['content']:
                        current_news['content'] += ' ' + line
                    else:
                        current_news['content'] = line

            # 保存最后一条新闻
            if current_news and current_news.get('title'):
                news_list.append(current_news)

            # 如果没有解析出独立条目，返回整体摘要
            if not news_list and news_report:
                # 尝试提取第一个有效标题
                title_match = re.search(r'### (.+?)(?:\n|$)', news_report)
                title = title_match.group(1).strip() if title_match else f'{symbol} 今日新闻动态'

                # 跳过无效标题
                if title.startswith('http') or re.match(r'^\d{4}-\d{2}-\d{2}', title):
                    title = f'{symbol} 今日新闻动态'

                news_list = [{
                    'title': title,
                    'content': news_report[:500],
                    'pub_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'source': 'RealTime-东方财富',
                    'url': f'https://so.eastmoney.com/news/s?keyword={symbol}'
                }]

            logger.info(f"✅ 备用源获取成功: {len(news_list)}条")
            return news_list

        except Exception as e:
            logger.debug(f"备用源也失败: {e}")
            return []
    
    def get_market_news_akshare(self, limit: int = 20) -> List[Dict]:
        """
        从AKShare获取市场要闻
        使用多个接口作为备选，确保至少有一个可用

        接口优先级:
        1. stock_info_global_em - 东方财富全球资讯 (最稳定)
        2. stock_info_global_cls - 财联社全球资讯
        3. news_cctv - 央视新闻
        4. news_economic_baidu - 百度财经新闻
        """
        try:
            import akshare as ak
            from datetime import datetime

            logger.info("📰 获取市场要闻...")
            news_list = []

            # 方法1: 东方财富全球资讯 (最稳定)
            try:
                df = ak.stock_info_global_em()
                if df is not None and not df.empty:
                    for _, row in df.head(limit).iterrows():
                        title = str(row.get('标题', ''))
                        if title:
                            news_list.append({
                                'title': title,
                                'content': str(row.get('摘要', ''))[:300],
                                'pub_time': str(row.get('发布时间', '')),
                                'source': 'AKShare-东方财富',
                                'url': str(row.get('链接', ''))
                            })
                    if news_list:
                        logger.info(f"✅ stock_info_global_em获取: {len(news_list)}条")
                        return news_list
            except Exception as e:
                logger.debug(f"stock_info_global_em失败: {e}")

            # 方法2: 财联社全球资讯
            try:
                df = ak.stock_info_global_cls()
                if df is not None and not df.empty:
                    for _, row in df.head(limit).iterrows():
                        title = str(row.get('标题', ''))
                        if title:
                            news_list.append({
                                'title': title,
                                'content': str(row.get('内容', ''))[:300],
                                'pub_time': str(row.get('发布日期', '')) + ' ' + str(row.get('发布时间', '')),
                                'source': 'AKShare-财联社',
                                'url': ''
                            })
                    if news_list:
                        logger.info(f"✅ stock_info_global_cls获取: {len(news_list)}条")
                        return news_list
            except Exception as e:
                logger.debug(f"stock_info_global_cls失败: {e}")

            # 方法3: news_cctv (央视新闻)
            try:
                today = datetime.now().strftime('%Y%m%d')
                df = ak.news_cctv(date=today)
                if df is not None and not df.empty:
                    for _, row in df.head(limit).iterrows():
                        title = str(row.get('title', ''))
                        if title:
                            news_list.append({
                                'title': title,
                                'content': str(row.get('content', ''))[:300],
                                'pub_time': str(row.get('date', today)),
                                'source': 'AKShare-央视新闻',
                                'url': ''
                            })
                    if news_list:
                        logger.info(f"✅ news_cctv获取: {len(news_list)}条")
                        return news_list
            except Exception as e:
                logger.debug(f"news_cctv失败: {e}")

            # 方法4: 百度财经新闻
            try:
                df = ak.news_economic_baidu()
                if df is not None and not df.empty:
                    for _, row in df.head(limit).iterrows():
                        title = str(row.get('标题', ''))
                        if title:
                            news_list.append({
                                'title': title,
                                'content': str(row.get('内容', ''))[:300],
                                'pub_time': str(row.get('发布时间', '')),
                                'source': 'AKShare-百度财经',
                                'url': str(row.get('链接', ''))
                            })
                    if news_list:
                        logger.info(f"✅ news_economic_baidu获取: {len(news_list)}条")
                        return news_list
            except Exception as e:
                logger.debug(f"news_economic_baidu失败: {e}")

            # 如果所有接口都失败，返回空列表
            if not news_list:
                logger.warning("⚠️ 所有市场新闻接口暂不可用")

            return news_list

        except Exception as e:
            logger.error(f"❌ 获取市场要闻失败: {e}")
            return []
    
    def aggregate_news(
        self, 
        ts_code: str,
        include_tushare: bool = True,
        include_akshare: bool = True,
        include_market_news: bool = False,
        limit_per_source: int = 10
    ) -> Dict:
        """
        聚合多个数据源的新闻
        
        Args:
            ts_code: 股票代码
            include_tushare: 是否包含Tushare新闻
            include_akshare: 是否包含AKShare新闻
            include_market_news: 是否包含市场要闻
            limit_per_source: 每个数据源的数量限制
            
        Returns:
            {
                'ts_code': str,
                'total_count': int,
                'sources': {
                    'tushare': [...],
                    'akshare': [...],
                    'market': [...]
                },
                'merged_news': [...],  # 合并后的新闻列表
                'timestamp': str
            }
        """
        logger.info(f"🔍 开始聚合{ts_code}的新闻...")
        
        result = {
            'ts_code': ts_code,
            'total_count': 0,
            'sources': {},
            'merged_news': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # 1. Tushare新闻
        if include_tushare:
            try:
                tushare_news = self.get_stock_news_tushare(
                    ts_code, 
                    limit=limit_per_source
                )
                result['sources']['tushare'] = tushare_news
                result['merged_news'].extend(tushare_news)
                logger.info(f"✅ Tushare新闻: {len(tushare_news)}条")
            except Exception as e:
                logger.error(f"❌ Tushare新闻获取失败: {e}")
                result['sources']['tushare'] = []
        
        # 2. AKShare个股新闻
        if include_akshare:
            try:
                symbol = ts_code.split('.')[0]
                akshare_news = self.get_stock_news_akshare(
                    symbol, 
                    limit=limit_per_source
                )
                result['sources']['akshare'] = akshare_news
                result['merged_news'].extend(akshare_news)
                logger.info(f"✅ AKShare新闻: {len(akshare_news)}条")
            except Exception as e:
                logger.error(f"❌ AKShare新闻获取失败: {e}")
                result['sources']['akshare'] = []
        
        # 3. 市场要闻（可选）
        if include_market_news:
            try:
                market_news = self.get_market_news_akshare(limit=limit_per_source)
                result['sources']['market'] = market_news
                result['merged_news'].extend(market_news)
                logger.info(f"✅ 市场要闻: {len(market_news)}条")
            except Exception as e:
                logger.error(f"❌ 市场要闻获取失败: {e}")
                result['sources']['market'] = []
        
        # 统计总数
        result['total_count'] = len(result['merged_news'])
        
        # 按时间排序
        result['merged_news'] = self._sort_news_by_time(result['merged_news'])
        
        logger.info(f"✅ 新闻聚合完成: 共{result['total_count']}条")
        
        return result
    
    def _sort_news_by_time(self, news_list: List[Dict]) -> List[Dict]:
        """按发布时间排序新闻"""
        try:
            # 尝试解析时间并排序
            def parse_time(news):
                try:
                    time_str = news.get('pub_time', '')
                    if time_str:
                        # 尝试多种时间格式
                        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y%m%d %H:%M:%S', '%Y-%m-%d']:
                            try:
                                return datetime.strptime(str(time_str), fmt)
                            except:
                                continue
                except:
                    pass
                return datetime.min
            
            sorted_news = sorted(
                news_list, 
                key=parse_time, 
                reverse=True  # 最新的在前
            )
            return sorted_news
        except Exception as e:
            logger.warning(f"排序失败，返回原列表: {e}")
            return news_list
    
    def format_news_summary(self, news_data: Dict) -> str:
        """
        格式化新闻摘要为文本报告
        
        Args:
            news_data: aggregate_news返回的数据
            
        Returns:
            格式化的文本报告
        """
        ts_code = news_data.get('ts_code', 'Unknown')
        total = news_data.get('total_count', 0)
        
        report = f"📰 {ts_code} 新闻汇总\n"
        report += f"=" * 60 + "\n"
        report += f"总计: {total}条新闻\n"
        report += f"时间: {news_data.get('timestamp', '')}\n\n"
        
        # 按数据源统计
        sources = news_data.get('sources', {})
        if sources:
            report += "📊 数据源统计:\n"
            for source_name, news_list in sources.items():
                report += f"  - {source_name}: {len(news_list)}条\n"
            report += "\n"
        
        # 显示最新的新闻
        merged_news = news_data.get('merged_news', [])
        if merged_news:
            report += "📋 最新新闻:\n"
            report += "-" * 60 + "\n"
            
            for i, news in enumerate(merged_news[:10], 1):
                report += f"\n[{i}] {news.get('title', 'Unknown')}\n"
                report += f"    来源: {news.get('source', 'Unknown')}\n"
                report += f"    时间: {news.get('pub_time', 'Unknown')}\n"
                if news.get('content'):
                    content = news['content'][:100]
                    report += f"    内容: {content}...\n"
        
        return report


# 全局实例
_news_aggregator = None


def get_news_aggregator() -> MultiSourceNewsAggregator:
    """获取全局新闻聚合器实例"""
    global _news_aggregator
    if _news_aggregator is None:
        _news_aggregator = MultiSourceNewsAggregator()
    return _news_aggregator


# 便捷函数
def get_stock_news(
    ts_code: str, 
    include_tushare: bool = True,
    include_akshare: bool = True,
    limit_per_source: int = 10
) -> Dict:
    """获取股票新闻"""
    aggregator = get_news_aggregator()
    return aggregator.aggregate_news(
        ts_code, 
        include_tushare=include_tushare,
        include_akshare=include_akshare,
        limit_per_source=limit_per_source
    )


def get_news_summary(ts_code: str) -> str:
    """获取股票新闻摘要文本"""
    aggregator = get_news_aggregator()
    news_data = aggregator.aggregate_news(ts_code)
    return aggregator.format_news_summary(news_data)
