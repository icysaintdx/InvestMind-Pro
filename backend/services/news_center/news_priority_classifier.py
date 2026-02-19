# -*- coding: utf-8 -*-
"""
新闻优先级分类器
基于收益率潜力对新闻进行分级处理

分级标准:
- P0 (紧急): 可能产生5%+收益的新闻，<5秒响应
- P1 (重要): 可能产生2-5%收益的新闻，<30秒响应  
- P2 (一般): 影响<1%的新闻，常规处理

Author: 臭宝
Date: 2026-02-19
"""

import re
from typing import Tuple, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class NewsPriority(str, Enum):
    """新闻优先级枚举"""
    P0 = "P0"  # 紧急 - 立即处理
    P1 = "P1"  # 重要 - 优先处理
    P2 = "P2"  # 一般 - 常规处理


class NewsCategory(str, Enum):
    """新闻类别枚举"""
    # P0 级别
    EARNINGS = "业绩"           # 业绩预告/快报/正式财报
    POLICY = "政策"             # 重大政策/监管
    RESTRUCTURE = "重组"        # 并购/重组/借壳
    SUSPENSION = "停牌"         # 停牌/复牌/退市
    
    # P1 级别
    DRAGON_LIST = "龙虎榜"      # 龙虎榜数据
    SHAREHOLDER = "股东"        # 增减持/质押
    BLOCK_TRADE = "大宗交易"    # 大宗交易
    ANNOUNCEMENT = "公告"       # 重要公告
    
    # P2 级别
    INDUSTRY = "行业"           # 行业新闻
    MARKET = "市场"             # 市场资讯
    GENERAL = "一般"            # 其他


@dataclass
class NewsClassification:
    """新闻分类结果"""
    priority: NewsPriority
    category: NewsCategory
    sub_category: str           # 子分类
    confidence: float          # 置信度 0-1
    expected_return: float     # 预期收益率 %
    urgency_score: float       # 紧急程度 0-100
    keywords_matched: List[str] # 匹配的关键词
    reason: str                # 分类理由


class NewsPriorityClassifier:
    """
    新闻优先级分类器
    
    核心逻辑:
    1. 基于关键词匹配进行初步分类
    2. 根据历史数据训练的调整权重
    3. 输出优先级和预期收益率
    """
    
    # P0 关键词 - 可能产生5%+收益
    P0_KEYWORDS = {
        NewsCategory.EARNINGS: {
            'high_positive': [
                '预增', '预计增长', '暴增', '大幅增长', '超预期', '净利润大增',
                '业绩增长', '扭亏为盈', '盈利大增', '业绩大增', '增长50%', 
                '增长超', '净利润增长', '业绩增长', '同比增', '同比大增',
                '业绩预增', '净利润预增', '业绩暴增'
            ],
            'high_negative': [
                '预减', '预亏', '暴雷', '大幅亏损', '业绩下滑',
                '亏损扩大', '由盈转亏', '业绩暴雷', '预降', '预计下降',
                '净利润下降', '业绩亏损', '同比降', '同比下降'
            ],
            'formal': [
                '年报', '半年报', '季报', '业绩快报', '业绩预告',
                '年度报告', '季度报告', '年度报告', '半年度报告'
            ]
        },
        NewsCategory.POLICY: {
            'national': [
                '国务院', '证监会', '银保监会', '央行', '发改委',
                '重大政策', '国家级', '顶层设计'
            ],
            'regulatory': [
                '监管', '整顿', '规范', '准入', '牌照',
                '政策利好', '政策出台'
            ],
            'industry_policy': [
                '行业政策', '产业扶持', '补贴', '税收优惠',
                '十四五规划', '新基建'
            ]
        },
        NewsCategory.RESTRUCTURE: {
            'ma': [
                '并购', '收购', '重组', '借壳', '资产注入',
                '重大资产重组', '要约收购', '战略收购'
            ],
            'restructure': [
                '分拆上市', '股权转让', '控制权变更', '实控人变更',
                '战略投资', '引入战投', '战略合作协议', '重大合同',
                '中标', '大订单', '供货协议'
            ]
        },
        NewsCategory.SUSPENSION: {
            'suspension': [
                '停牌', '临时停牌', '紧急停牌'
            ],
            'resumption': [
                '复牌', '恢复交易'
            ],
            'risk': [
                '退市', 'ST', '风险警示', '暂停上市',
                '终止上市', '面值退市'
            ]
        }
    }
    
    # P1 关键词 - 可能产生2-5%收益
    P1_KEYWORDS = {
        NewsCategory.DRAGON_LIST: {
            'list': [
                '龙虎榜', '登榜', '上榜', '营业部买入',
                '机构席位', '游资买入'
            ],
            'institution': [
                '机构买入', '机构卖出', '机构专用',
                '深股通买入', '沪股通买入'
            ]
        },
        NewsCategory.SHAREHOLDER: {
            'increase': [
                '增持', '大股东增持', '实控人增持',
                '回购', '股票回购'
            ],
            'decrease': [
                '减持', '大股东减持', '清仓减持',
                '减持计划', '减持完毕'
            ],
            'pledge': [
                '股权质押', '解押', '质押解除',
                '高质押', '质押风险'
            ]
        },
        NewsCategory.BLOCK_TRADE: {
            'block': [
                '大宗交易', '大宗买入', '大宗卖出',
                '溢价大宗', '折价大宗'
            ]
        },
        NewsCategory.ANNOUNCEMENT: {
            'important': [
                '重大合同', '中标', '订单', '战略合作协议',
                '获得认证', '产品获批'
            ],
            'investment': [
                '对外投资', '设立子公司', '扩产', '新建项目',
                '产能扩张'
            ]
        }
    }
    
    # P2 关键词 - 一般影响
    P2_KEYWORDS = {
        NewsCategory.INDUSTRY: [
            '行业', '产业链', '上下游', '供需', '景气度',
            '行业趋势', '行业发展'
        ],
        NewsCategory.MARKET: [
            '市场', '大盘', '板块', '概念股',
            '资金流向', '市场情绪'
        ]
    }
    
    # 预期收益率映射
    EXPECTED_RETURN = {
        NewsPriority.P0: {
            'high_positive': 8.0,    # 业绩暴增等正面
            'high_negative': -5.0,   # 暴雷等负面（做空或避险）
            'ma': 10.0,              # 并购重组
            'policy': 7.0,           # 重大政策
        },
        NewsPriority.P1: {
            'dragon_list': 3.0,      # 龙虎榜
            'shareholder': 2.5,      # 股东动作
            'block_trade': 2.0,      # 大宗交易
            'announcement': 2.0,     # 重要公告
        },
        NewsPriority.P2: {
            'default': 0.5,          # 一般影响
        }
    }
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("新闻优先级分类器初始化完成")
        
    def classify(self, title: str, content: str = "") -> NewsClassification:
        """
        对新闻进行分类
        
        Args:
            title: 新闻标题
            content: 新闻内容（可选）
            
        Returns:
            NewsClassification: 分类结果
        """
        text = f"{title} {content}".lower()
        
        # 1. 检查P0级别关键词
        p0_result = self._check_p0_keywords(text)
        if p0_result:
            return self._create_classification(
                NewsPriority.P0, 
                p0_result['category'],
                p0_result['sub_category'],
                p0_result['keywords'],
                text
            )
        
        # 2. 检查P1级别关键词
        p1_result = self._check_p1_keywords(text)
        if p1_result:
            return self._create_classification(
                NewsPriority.P1,
                p1_result['category'],
                p1_result['sub_category'],
                p1_result['keywords'],
                text
            )
        
        # 3. 检查P2级别关键词
        p2_result = self._check_p2_keywords(text)
        if p2_result:
            return self._create_classification(
                NewsPriority.P2,
                p2_result['category'],
                'general',
                p2_result['keywords'],
                text
            )
        
        # 4. 默认P2
        return self._create_classification(
            NewsPriority.P2,
            NewsCategory.GENERAL,
            'unknown',
            [],
            text,
            confidence=0.5
        )
    
    def _check_p0_keywords(self, text: str) -> Optional[Dict]:
        """检查P0级别关键词"""
        for category, keyword_groups in self.P0_KEYWORDS.items():
            for sub_category, keywords in keyword_groups.items():
                matched = [kw for kw in keywords if kw in text]
                if matched:
                    return {
                        'category': category,
                        'sub_category': sub_category,
                        'keywords': matched
                    }
        return None
    
    def _check_p1_keywords(self, text: str) -> Optional[Dict]:
        """检查P1级别关键词"""
        for category, keyword_groups in self.P1_KEYWORDS.items():
            for sub_category, keywords in keyword_groups.items():
                matched = [kw for kw in keywords if kw in text]
                if matched:
                    return {
                        'category': category,
                        'sub_category': sub_category,
                        'keywords': matched
                    }
        return None
    
    def _check_p2_keywords(self, text: str) -> Optional[Dict]:
        """检查P2级别关键词"""
        for category, keywords in self.P2_KEYWORDS.items():
            matched = [kw for kw in keywords if kw in text]
            if matched:
                return {
                    'category': category,
                    'keywords': matched
                }
        return None
    
    def _create_classification(
        self,
        priority: NewsPriority,
        category: NewsCategory,
        sub_category: str,
        keywords: List[str],
        text: str,
        confidence: float = None
    ) -> NewsClassification:
        """创建分类结果"""
        
        # 计算置信度
        if confidence is None:
            confidence = min(0.5 + len(keywords) * 0.15, 0.95)
        
        # 计算预期收益率
        expected_return = self._calculate_expected_return(
            priority, sub_category, text
        )
        
        # 计算紧急程度
        urgency_score = self._calculate_urgency(
            priority, category, sub_category, len(keywords)
        )
        
        # 生成理由
        reason = self._generate_reason(priority, category, sub_category, keywords)
        
        return NewsClassification(
            priority=priority,
            category=category,
            sub_category=sub_category,
            confidence=confidence,
            expected_return=expected_return,
            urgency_score=urgency_score,
            keywords_matched=keywords,
            reason=reason
        )
    
    def _calculate_expected_return(
        self, 
        priority: NewsPriority, 
        sub_category: str,
        text: str
    ) -> float:
        """计算预期收益率"""
        base_return = self.EXPECTED_RETURN.get(priority, {}).get('default', 0.5)
        
        # 根据子类别调整
        if priority == NewsPriority.P0:
            if sub_category in ['high_positive', 'ma', 'policy']:
                base_return = self.EXPECTED_RETURN[NewsPriority.P0].get(sub_category, 8.0)
            elif sub_category == 'high_negative':
                # 负面新闻可能是做空机会或避险
                base_return = -5.0
        elif priority == NewsPriority.P1:
            base_return = self.EXPECTED_RETURN[NewsPriority.P1].get(sub_category, 2.0)
        
        # 根据文本强度微调
        if '大幅' in text or '超' in text:
            base_return *= 1.3
        elif '小幅' in text:
            base_return *= 0.7
            
        return round(base_return, 2)
    
    def _calculate_urgency(
        self,
        priority: NewsPriority,
        category: NewsCategory,
        sub_category: str,
        keyword_count: int
    ) -> float:
        """计算紧急程度分数 0-100"""
        base_scores = {
            NewsPriority.P0: 80,
            NewsPriority.P1: 50,
            NewsPriority.P2: 20
        }
        
        score = base_scores.get(priority, 20)
        
        # 关键词越多越紧急
        score += min(keyword_count * 5, 15)
        
        # 特定类别加分
        if category in [NewsCategory.EARNINGS, NewsCategory.SUSPENSION]:
            score += 10
        
        return min(score, 100)
    
    def _generate_reason(
        self,
        priority: NewsPriority,
        category: NewsCategory,
        sub_category: str,
        keywords: List[str]
    ) -> str:
        """生成分类理由"""
        kw_str = '、'.join(keywords[:3])  # 最多显示3个关键词
        
        reasons = {
            NewsPriority.P0: {
                NewsCategory.EARNINGS: f"业绩重大变化[{kw_str}]，可能产生5%+收益",
                NewsCategory.POLICY: f"重大政策[{kw_str}]，影响深远",
                NewsCategory.RESTRUCTURE: f"资本运作[{kw_str}]，重大机遇",
                NewsCategory.SUSPENSION: f"交易状态变更[{kw_str}]，需立即关注",
            },
            NewsPriority.P1: {
                NewsCategory.DRAGON_LIST: f"龙虎榜数据[{kw_str}]，资金动向",
                NewsCategory.SHAREHOLDER: f"股东动作[{kw_str}]，信心信号",
                NewsCategory.BLOCK_TRADE: f"大宗交易[{kw_str}]，机构布局",
                NewsCategory.ANNOUNCEMENT: f"重要公告[{kw_str}]，业务进展",
            }
        }
        
        return reasons.get(priority, {}).get(
            category, 
            f"匹配关键词[{kw_str}]，{priority.value}级处理"
        )
    
    def batch_classify(self, news_list: List[Dict]) -> List[NewsClassification]:
        """
        批量分类新闻
        
        Args:
            news_list: 新闻列表，每项包含title和content
            
        Returns:
            分类结果列表
        """
        results = []
        for news in news_list:
            try:
                classification = self.classify(
                    news.get('title', ''),
                    news.get('content', '')
                )
                results.append(classification)
            except Exception as e:
                self.logger.error(f"分类新闻失败: {e}")
                # 失败时返回默认P2
                results.append(NewsClassification(
                    priority=NewsPriority.P2,
                    category=NewsCategory.GENERAL,
                    sub_category='error',
                    confidence=0.0,
                    expected_return=0.0,
                    urgency_score=0,
                    keywords_matched=[],
                    reason=f"分类失败: {e}"
                ))
        return results


# 便捷函数
def classify_news(title: str, content: str = "") -> NewsClassification:
    """便捷函数：快速分类单条新闻"""
    classifier = NewsPriorityClassifier()
    return classifier.classify(title, content)


def get_priority_from_classification(classification: NewsClassification) -> str:
    """获取优先级字符串"""
    return classification.priority.value


# 测试代码
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    classifier = NewsPriorityClassifier()
    
    # 测试用例
    test_news = [
        "贵州茅台：预计2025年净利润同比增长50%以上",
        "宁德时代：与特斯拉签订重大供货协议",
        "XX股份：实控人计划减持不超过5%股份",
        "YY科技：今日登陆龙虎榜，机构买入2亿元",
        "ZZ银行：发布2024年年度报告",
        "今日A股市场震荡整理，板块轮动加快",
    ]
    
    print("=" * 80)
    print("新闻优先级分类测试")
    print("=" * 80)
    
    for news in test_news:
        result = classifier.classify(news)
        print(f"\n新闻: {news}")
        print(f"  优先级: {result.priority.value}")
        print(f"  类别: {result.category.value}")
        print(f"  预期收益: {result.expected_return}%")
        print(f"  紧急程度: {result.urgency_score}")
        print(f"  置信度: {result.confidence}")
        print(f"  理由: {result.reason}")
        print(f"  关键词: {result.keywords_matched}")
