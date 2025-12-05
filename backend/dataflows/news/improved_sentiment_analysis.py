#!/usr/bin/env python3
"""
改进的情绪分析模块
集成真实新闻数据进行情绪分析
"""

import re
from typing import List, Dict
from datetime import datetime
from backend.utils.logging_config import get_logger

logger = get_logger("sentiment_analysis")


class ImprovedSentimentAnalyzer:
    """改进的情绪分析器"""
    
    def __init__(self):
        # 扩展的情绪词典
        self.positive_words = [
            '上涨', '增长', '利好', '看好', '买入', '推荐', '强势', '突破', '创新高',
            '盈利', '增收', '扩张', '领先', '优势', '机会', '积极', '乐观', '提升',
            '改善', '回暖', '复苏', '繁荣', '稳定', '增强', '超预期', '超额', '优质',
            '创新', '突破', '领涨', '大涨', '飙升', '暴涨', '涨停', '涨幅', '涨势'
        ]
        
        self.negative_words = [
            '下跌', '下降', '利空', '看空', '卖出', '风险', '跌破', '创新低', '亏损',
            '下滑', '萎缩', '困难', '压力', '危机', '警告', '担忧', '悲观', '下行',
            '恶化', '衰退', '疲软', '低迷', '减少', '缩水', '暴跌', '跌停', '跌幅',
            '崩盘', '暴跌', '大跌', '重挫', '挫败', '失败', '问题', '隐患', '风波'
        ]
        
        # 强度词
        self.intensity_words = {
            '大幅': 1.5,
            '显著': 1.3,
            '明显': 1.2,
            '持续': 1.2,
            '快速': 1.3,
            '急剧': 1.5,
            '暴': 2.0,
            '猛': 1.8,
            '强劲': 1.5,
            '稳健': 1.2
        }
        
        # 否定词
        self.negation_words = ['不', '没', '无', '非', '未', '否', '别', '莫']
    
    def analyze_news_sentiment(self, news_list: List[Dict]) -> Dict:
        """
        分析新闻列表的整体情绪
        
        Args:
            news_list: 新闻列表，每条新闻包含 title 和 content
            
        Returns:
            情绪分析结果
        """
        if not news_list:
            return {
                'sentiment_score': 0.0,
                'sentiment_label': '中性',
                'confidence': 0.0,
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
                'news_count': 0
            }
        
        scores = []
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        for news in news_list:
            title = news.get('title', '')
            content = news.get('content', '')
            text = f"{title} {content}"
            
            score = self.analyze_text_sentiment(text)
            scores.append(score)
            
            if score > 0.2:
                positive_count += 1
            elif score < -0.2:
                negative_count += 1
            else:
                neutral_count += 1
        
        # 计算平均情绪分数
        avg_score = sum(scores) / len(scores) if scores else 0.0
        
        # 确定情绪标签
        if avg_score > 0.3:
            label = '积极'
        elif avg_score > 0.1:
            label = '偏积极'
        elif avg_score < -0.3:
            label = '消极'
        elif avg_score < -0.1:
            label = '偏消极'
        else:
            label = '中性'
        
        # 计算置信度（基于新闻数量和情绪一致性）
        confidence = self._calculate_confidence(scores, len(news_list))
        
        return {
            'sentiment_score': round(avg_score, 2),
            'sentiment_label': label,
            'confidence': round(confidence, 2),
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count,
            'news_count': len(news_list),
            'positive_ratio': round(positive_count / len(news_list), 2),
            'negative_ratio': round(negative_count / len(news_list), 2)
        }
    
    def analyze_text_sentiment(self, text: str) -> float:
        """
        分析单条文本的情绪
        
        Args:
            text: 待分析文本
            
        Returns:
            情绪分数 (-1.0 到 1.0)
        """
        if not text:
            return 0.0
        
        text = text.lower()
        
        # 计算正面词和负面词的数量
        positive_score = 0
        negative_score = 0
        
        # 检查每个词
        words = list(text)
        for i, char in enumerate(words):
            # 检查正面词
            for pos_word in self.positive_words:
                if text[i:i+len(pos_word)] == pos_word:
                    intensity = self._get_intensity(text, i)
                    is_negated = self._is_negated(text, i)
                    
                    if is_negated:
                        negative_score += intensity
                    else:
                        positive_score += intensity
            
            # 检查负面词
            for neg_word in self.negative_words:
                if text[i:i+len(neg_word)] == neg_word:
                    intensity = self._get_intensity(text, i)
                    is_negated = self._is_negated(text, i)
                    
                    if is_negated:
                        positive_score += intensity
                    else:
                        negative_score += intensity
        
        # 计算最终分数
        total = positive_score + negative_score
        if total == 0:
            return 0.0
        
        score = (positive_score - negative_score) / total
        
        # 限制在 -1 到 1 之间
        return max(-1.0, min(1.0, score))
    
    def _get_intensity(self, text: str, position: int) -> float:
        """获取情绪强度"""
        # 检查前面是否有强度词
        window = text[max(0, position-10):position]
        
        for intensity_word, multiplier in self.intensity_words.items():
            if intensity_word in window:
                return multiplier
        
        return 1.0
    
    def _is_negated(self, text: str, position: int) -> bool:
        """检查是否被否定"""
        # 检查前面是否有否定词
        window = text[max(0, position-5):position]
        
        for neg_word in self.negation_words:
            if neg_word in window:
                return True
        
        return False
    
    def _calculate_confidence(self, scores: List[float], news_count: int) -> float:
        """
        计算置信度
        
        基于：
        1. 新闻数量（越多越可信）
        2. 情绪一致性（越一致越可信）
        """
        if not scores:
            return 0.0
        
        # 基于数量的置信度（最多10条新闻达到满分）
        count_confidence = min(news_count / 10.0, 1.0)
        
        # 基于一致性的置信度
        avg_score = sum(scores) / len(scores)
        variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
        consistency_confidence = 1.0 - min(variance, 1.0)
        
        # 综合置信度
        return (count_confidence * 0.6 + consistency_confidence * 0.4)


# 创建全局实例
_sentiment_analyzer = None

def get_sentiment_analyzer():
    """获取情绪分析器实例（单例）"""
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        _sentiment_analyzer = ImprovedSentimentAnalyzer()
    return _sentiment_analyzer
