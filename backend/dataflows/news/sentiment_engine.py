"""
新闻情绪分析引擎
基于关键词、情感词典和NLP技术进行情绪打分
"""

from typing import List, Dict, Optional
import re
from datetime import datetime

from backend.utils.logging_config import get_logger

logger = get_logger("news.sentiment")


class SentimentEngine:
    """情绪分析引擎 - 增强版"""
    
    def __init__(self):
        """初始化情感词典"""
        
        # ==================== 正面词汇词典 ====================
        
        # 业绩利好类
        self.positive_performance = {
            '增长', '上涨', '盈利', '突破', '创新高', '超预期', '大涨', '暴涨',
            '翻倍', '翻番', '高增长', '爆发式增长', '大幅增长', '高位运行',
            '业绩亮眼', '业绩优秀', '业绩翻番', '业绩双击', '业绩变脸',
            '净利润增长', '营收增长', '毛利率提升', '利润率上升',
            '扭亏为盈', '首次盈利', '绩优', '超额完成', '稳步增长'
        }
        
        # 市场情绪积极类
        self.positive_market = {
            '利好', '受益', '看好', '乐观', '强劲', '回升', '复苏', '提升',
            '改善', '优化', '突出', '领先', '优势', '扩张', '增持', '买入',
            '热点', '活跃', '爆发', '机会', '潜力', '价值', '低估', '支撑',
            '稳定', '强势', '放量', '拉升', '反弹', '反转', '突破', '加速',
            '牛市', '上攻', '量价齐升', '量能放大', '主力入场', '资金流入',
            '多头排列', '多头强势', '消息面利好', '政策支持', '行业复苏'
        }
        
        # 公司运营正面类
        self.positive_operation = {
            '中标', '合作', '协议', '订单', '并购', '重组', '分红', '回购',
            '签约', '签订', '得标', '大单', '超大订单', '核心产品',
            '新品发布', '产品升级', '技术突破', '创新产品',
            '战略合作', '深度合作', '长期合作', '框架协议',
            '股权激励', '员工持股', '管理层增持', '大股东增持',
            '市场份额提升', '品牌价值上升', '竞争力增强'
        }
        
        # 行业政策利好类
        self.positive_policy = {
            '政策支持', '补贴', '激励', '鼓励', '推进', '推动', '支持',
            '减税', '免税', '退税', '优惠', '扫障', '放开', '放宽',
            '顶层设计', '国家战略', '行业规划', '发展规划',
            '重点支持', '重点培育', '示范工程', '试点项目'
        }
        
        # 技术创新类
        self.positive_innovation = {
            '创新', '研发', '突破', '领先', '首发', '自主知识产权',
            '专利', '核心技术', '关键技术', '前沿技术', '高科技',
            '智能化', '数字化', '自动化', '升级改造', '转型升级',
            'AI', '人工智能', '大数据', '云计算', '物联网', '5G', '区块链'
        }
        
        # 合并所有正面词汇
        self.positive_words = (
            self.positive_performance | self.positive_market | 
            self.positive_operation | self.positive_policy | self.positive_innovation
        )
        
        # ==================== 负面词汇词典 ====================
        
        # 业绩利空类
        self.negative_performance = {
            '下跌', '亏损', '减少', '下滑', '暴跌', '大跌', '跳水', '闪崩',
            '巨亏', '亏损额', '净利润下滑', '营收下降', '业绩变脸',
            '业绩亏损', '业绩大幅下滑', '业绩不及预期', '首亏',
            '毛利率下降', '利润率下滑', '盈利能力下降'
        }
        
        # 市场情绪消极类
        self.negative_market = {
            '利空', '不及预期', '萎缩', '下行', '疲软', '恶化', '衰退', '警告',
            '减持', '抛售', '卖出', '看空', '悲观', '担忧', '风险', '危机',
            '缩量', '跌破', '失守', '套牢', '割肉', '踩雷', '爆雷', '黑天鹅',
            '破位', '低迷', '疲弱', '承压', '拖累', '杀跌', '恐慌', '调整',
            '熊市', '下攻', '量价齐跌', '量能萎缩', '主力出逃', '资金流出',
            '空头排列', '空头强势', '消息面利空', '政策收紧', '行业低迷'
        }
        
        # 公司问题类
        self.negative_operation = {
            '违规', '处罚', '调查', '停牌', 'ST', '退市', '诉讼', '纠纷',
            '质疑', '质押', '冻结', '封门', '查封', '稽查', '立案',
            '财务造假', '财务虚假', '会计失误', '内控缺陷',
            '高管离职', '高管辩职', '核心人员离职', '团队动荡',
            '债务违约', '资金链紧张', '现金流问题', '经营困难',
            '产品召回', '质量问题', '安全隐患', '事故'
        }
        
        # 监管风险类
        self.negative_regulation = {
            '问询函', '监管函', '警示函', '关注函', '批复',
            '不予批准', '终止审查', '停止交易', '强制退市',
            '公开谴责', '通报批评', '行政处罚', '罚款',
            '限制消费', '失信被执行人', '限制高消费'
        }
        
        # 合并所有负面词汇
        self.negative_words = (
            self.negative_performance | self.negative_market | 
            self.negative_operation | self.negative_regulation
        )
        
        # ==================== 强化词（加权） ====================
        self.intensifiers = {
            # 程度强化
            '大幅': 1.5, '显著': 1.4, '明显': 1.3, '大': 1.2,
            '超': 1.4, '极': 1.5, '非常': 1.3, '十分': 1.3,
            '极度': 1.5, '极其': 1.4, '相当': 1.2, '比较': 1.1,
            # 时间强化
            '突然': 1.3, '急剧': 1.4, '迅速': 1.3, '快速': 1.2,
            '持续': 1.2, '连续': 1.3, '一直': 1.2,
            # 范围强化
            '全面': 1.3, '全部': 1.3, '所有': 1.2, '多个': 1.2,
            '普遍': 1.2, '大量': 1.3, '大规模': 1.4,
            # 确定性强化
            '确定': 1.2, '明确': 1.2, '肯定': 1.2, '必然': 1.3,
            '一定': 1.2, '必须': 1.2, '完全': 1.3
        }
        
        # ==================== 否定词 ====================
        self.negation_words = {
            # 基础否定词
            '不', '没', '无', '未', '非', '否', '别', '莫',
            # 复合否定词
            '不是', '没有', '无法', '未能', '不能', '不会',
            '不可', '不要', '不应', '不应该', '不必',
            # 程度否定
            '几乎不', '几乎没', '几乎无', '极少',
            '很少', '少有', '难以', '难于'
        }
        
        # ==================== 紧急程度关键词 ====================
        self.urgency_levels = {
            'critical': {  # 特别紧急
                '特别重大', '特大', '特大型', '特大事故', '特大灾害',
                '特别提示', '紧急通知', '紧急公告', '紧急停牌',
                '强制退市', '停止交易', '重大违法', '重大违规'
            },
            'high': {  # 高度重要
                '重大', '重要', '严重', '严峻', '重点', '关键',
                '核心', '重大事项', '重大资产重组', '重大合同',
                '重大诉讼', '重大亏损', '重大风险'
            },
            'medium': {  # 一般重要
                '较大', '较多', '不小', '一定程度',
                '值得关注', '需要关注', '应当注意'
            },
            'low': {  # 一般
                '普通', '常规', '日常', '一般', '正常'
            }
        }
        
        # ==================== 报告类型关键词 ====================
        self.report_types = {
            'financial': {  # 财务报告
                '财报', '财务报告', '年报', '半年报', '季报',
                '业绩预告', '业绩快报', '业绩修正', '业绩说明',
                '利润表', '资产负债表', '现金流量表'
            },
            'research': {  # 研究报告
                '研报', '研究报告', '分析师', '机构研究',
                '深度研究', '行业研究', '公司研究', '调研',
                '买入', '增持', '中性', '减持', '卖出', '目标价'
            },
            'announcement': {  # 公告文件
                '公告', '提示性公告', '风险提示', '澄清公告',
                '问询函回复', '补充公告', '更正公告', '进展公告'
            },
            'news': {  # 新闻资讯
                '新闻', '资讯', '快讯', '快讯', '速递',
                '专访', '采访', '采访', '报道', '媒体',
                '官方', '官网', '官微', '声明'
            },
            'policy': {  # 政策文件
                '政策', '通知', '意见', '指导', '规划',
                '办法', '条例', '规定', '规章', '法规',
                '国务院', '证监会', '发改委', '工信部'
            }
        }
        
        logger.info("✅ 情绪分析引擎初始化完成")
        logger.info(f"   正面词汇: {len(self.positive_words)}个")
        logger.info(f"   负面词汇: {len(self.negative_words)}个")
        logger.info(f"   强化词: {len(self.intensifiers)}个")
        logger.info(f"   否定词: {len(self.negation_words)}个")
    
    def analyze_text(self, text: str, weight_title: bool = False) -> Dict:
        """
        分析单条文本的情绪
        
        Args:
            text: 待分析文本
            weight_title: 是否为标题（标题权重更高）
            
        Returns:
            {
                'score': float,  # 情绪得分 0-100
                'sentiment': str,  # 'positive'/'negative'/'neutral'
                'positive_count': int,
                'negative_count': int,
                'keywords': list,
                'urgency': str,  # 紧急程度
                'report_type': str  # 报告类型
            }
        """
        if not text:
            return {
                'score': 50,
                'sentiment': 'neutral',
                'positive_count': 0,
                'negative_count': 0,
                'keywords': [],
                'urgency': 'low',
                'report_type': 'unknown'
            }
        
        # 分词（简单实现，实际可用jieba）
        words = list(text)
        
        positive_score = 0
        negative_score = 0
        keywords = []
        
        # 分析正面词汇
        for word in self.positive_words:
            count = text.count(word)
            if count > 0:
                # 检查强化词
                weight = 1.0
                for intensifier, mult in self.intensifiers.items():
                    try:
                        if intensifier in text:
                            int_idx = text.find(intensifier)
                            word_idx = text.find(word)
                            # 强化词在目标词前面3个字符内
                            if 0 <= word_idx - int_idx <= 3:
                                weight = mult
                                break
                    except:
                        pass
                
                # 检查否定
                is_negated = self._check_negation(text, word)
                if is_negated:
                    negative_score += count * weight
                else:
                    positive_score += count * weight
                    keywords.append(word)
        
        # 分析负面词汇
        for word in self.negative_words:
            count = text.count(word)
            if count > 0:
                weight = 1.0
                for intensifier, mult in self.intensifiers.items():
                    try:
                        if intensifier in text:
                            int_idx = text.find(intensifier)
                            word_idx = text.find(word)
                            if 0 <= word_idx - int_idx <= 3:
                                weight = mult
                                break
                    except:
                        pass
                
                is_negated = self._check_negation(text, word)
                if is_negated:
                    positive_score += count * weight
                else:
                    negative_score += count * weight
                    keywords.append(word)
        
        # 标题权重加成
        if weight_title:
            positive_score *= 1.5
            negative_score *= 1.5
        
        # 计算情绪得分 (0-100)
        total = positive_score + negative_score
        if total == 0:
            score = 50  # 中性
        else:
            score = (positive_score / total) * 100
        
        # 确定情绪倾向
        if score >= 60:
            sentiment = 'positive'
        elif score <= 40:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        # 评估紧急程度
        urgency = self._assess_urgency(text)
        
        # 识别报告类型
        report_type = self._identify_report_type(text)
        
        return {
            'score': round(score, 2),
            'sentiment': sentiment,
            'positive_count': int(positive_score),
            'negative_count': int(negative_score),
            'keywords': keywords[:10],  # 最多返回10个关键词
            'urgency': urgency,
            'report_type': report_type
        }
    
    def _assess_urgency(self, text: str) -> str:
        """
        评估文本紧急程度
        
        Returns:
            'critical' / 'high' / 'medium' / 'low'
        """
        # 检查各级别关键词
        for level, keywords in self.urgency_levels.items():
            for keyword in keywords:
                if keyword in text:
                    return level
        return 'low'
    
    def _identify_report_type(self, text: str) -> str:
        """
        识别报告类型
        
        Returns:
            'financial' / 'research' / 'announcement' / 'news' / 'policy' / 'unknown'
        """
        # 统计各类型关键词出现次数
        type_scores = {}
        for report_type, keywords in self.report_types.items():
            count = sum(1 for kw in keywords if kw in text)
            if count > 0:
                type_scores[report_type] = count
        
        if not type_scores:
            return 'unknown'
        
        # 返回得分最高的类型
        return max(type_scores.items(), key=lambda x: x[1])[0]
    
    def analyze_news_list(self, news_list: List[Dict]) -> Dict:
        """
        分析新闻列表的整体情绪
        
        Args:
            news_list: 新闻列表，每条新闻包含title和content
            
        Returns:
            {
                'overall_score': float,  # 总体情绪得分
                'overall_sentiment': str,
                'positive_count': int,  # 正面新闻数
                'negative_count': int,  # 负面新闻数
                'neutral_count': int,   # 中性新闻数
                'news_sentiments': list,  # 每条新闻的情绪分析
                'urgency_stats': dict,  # 紧急程度统计
                'report_type_stats': dict,  # 报告类型统计
                'time_series': list  # 时间序列情绪
            }
        """
        if not news_list:
            return {
                'overall_score': 50,
                'overall_sentiment': 'neutral',
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
                'news_sentiments': [],
                'urgency_stats': {},
                'report_type_stats': {},
                'time_series': []
            }
        
        logger.info(f"📊 开始分析{len(news_list)}条新闻的情绪...")
        
        news_sentiments = []
        scores = []
        
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        # 统计紧急程度和报告类型
        urgency_stats = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        report_type_stats = {
            'financial': 0, 'research': 0, 'announcement': 0,
            'news': 0, 'policy': 0, 'unknown': 0
        }
        
        for news in news_list:
            # 合并标题和内容进行分析
            title = news.get('title', '')
            content = news.get('content', '')
            
            # 先分析标题（高权重）
            title_sentiment = self.analyze_text(title, weight_title=True) if title else None
            
            # 再分析全文
            text = f"{title} {content}"
            full_sentiment = self.analyze_text(text)
            
            # 综合评分：标题60% + 全文40%
            if title_sentiment:
                final_score = title_sentiment['score'] * 0.6 + full_sentiment['score'] * 0.4
                final_sentiment = title_sentiment['sentiment'] if title_sentiment['score'] != 50 else full_sentiment['sentiment']
                # 合并关键词
                keywords = list(set(title_sentiment['keywords'] + full_sentiment['keywords']))[:10]
            else:
                final_score = full_sentiment['score']
                final_sentiment = full_sentiment['sentiment']
                keywords = full_sentiment['keywords']
            
            # 统计情绪分布
            if final_sentiment == 'positive':
                positive_count += 1
            elif final_sentiment == 'negative':
                negative_count += 1
            else:
                neutral_count += 1
            
            # 统计紧急程度
            urgency = full_sentiment.get('urgency', 'low')
            urgency_stats[urgency] = urgency_stats.get(urgency, 0) + 1
            
            # 统计报告类型
            report_type = full_sentiment.get('report_type', 'unknown')
            report_type_stats[report_type] = report_type_stats.get(report_type, 0) + 1
            
            scores.append(final_score)
            
            news_sentiments.append({
                'title': title,
                'pub_time': news.get('pub_time', ''),
                'source': news.get('source', ''),
                'score': round(final_score, 2),
                'sentiment': final_sentiment,
                'keywords': keywords,
                'urgency': urgency,
                'report_type': report_type
            })
        
        # 计算总体得分
        overall_score = sum(scores) / len(scores) if scores else 50
        
        if overall_score >= 60:
            overall_sentiment = 'positive'
        elif overall_score <= 40:
            overall_sentiment = 'negative'
        else:
            overall_sentiment = 'neutral'
        
        # 按时间排序的情绪趋势
        time_series = sorted(
            news_sentiments,
            key=lambda x: x.get('pub_time', ''),
            reverse=True
        )[:20]  # 最多20条
        
        logger.info(f"✅ 情绪分析完成: 总体得分={overall_score:.2f}, 正面={positive_count}, 负面={negative_count}")
        
        return {
            'overall_score': round(overall_score, 2),
            'overall_sentiment': overall_sentiment,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count,
            'news_sentiments': news_sentiments,
            'urgency_stats': urgency_stats,
            'report_type_stats': report_type_stats,
            'time_series': time_series
        }
        
    def _check_negation(self, text: str, word: str) -> bool:
        """检查词汇前是否有否定词"""
        try:
            word_index = text.index(word)
            # 检查前5个字符内是否有否定词
            preceding_text = text[max(0, word_index-5):word_index]
            
            for neg_word in self.negation_words:
                if neg_word in preceding_text:
                    return True
            
            return False
        except:
            return False
    
    def format_sentiment_report(self, sentiment_data: Dict) -> str:
        """
        格式化情绪分析报告
        
        Args:
            sentiment_data: analyze_news_list返回的数据
            
        Returns:
            格式化的文本报告
        """
        overall_score = sentiment_data.get('overall_score', 50)
        overall_sentiment = sentiment_data.get('overall_sentiment', 'neutral')
        
        # 情绪emoji
        emoji_map = {
            'positive': '😊',
            'neutral': '😐',
            'negative': '😟'
        }
        emoji = emoji_map.get(overall_sentiment, '😐')
        
        report = f"📊 舆情情绪分析报告\n"
        report += f"=" * 60 + "\n"
        report += f"{emoji} 总体情绪: {overall_sentiment.upper()} (得分: {overall_score:.2f}/100)\n\n"
        
        report += f"📈 情绪分布:\n"
        report += f"  - 正面新闻: {sentiment_data.get('positive_count', 0)}条\n"
        report += f"  - 中性新闻: {sentiment_data.get('neutral_count', 0)}条\n"
        report += f"  - 负面新闻: {sentiment_data.get('negative_count', 0)}条\n\n"
        
        # 显示部分新闻情绪
        news_sentiments = sentiment_data.get('news_sentiments', [])
        if news_sentiments:
            report += f"📰 新闻情绪详情（前5条）:\n"
            report += "-" * 60 + "\n"
            
            for i, item in enumerate(news_sentiments[:5], 1):
                sentiment = item['sentiment']
                emoji = emoji_map.get(sentiment['sentiment'], '😐')
                
                report += f"\n[{i}] {emoji} {sentiment['sentiment']} (得分: {sentiment['score']})\n"
                report += f"    标题: {item['title'][:50]}...\n"
                if sentiment['keywords']:
                    report += f"    关键词: {', '.join(sentiment['keywords'][:5])}\n"
        
        return report


# 全局实例
_sentiment_engine = None


def get_sentiment_engine() -> SentimentEngine:
    """获取全局情绪分析引擎实例"""
    global _sentiment_engine
    if _sentiment_engine is None:
        _sentiment_engine = SentimentEngine()
    return _sentiment_engine


# 便捷函数
def analyze_news_sentiment(news_list: List[Dict]) -> Dict:
    """分析新闻列表情绪"""
    engine = get_sentiment_engine()
    return engine.analyze_news_list(news_list)


def get_sentiment_score(news_list: List[Dict]) -> float:
    """获取情绪得分"""
    engine = get_sentiment_engine()
    result = engine.analyze_news_list(news_list)
    return result.get('overall_score', 50)
