# -*- coding: utf-8 -*-
"""影响评估器 - 评估新闻对股票的影响程度"""
import re
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ImpactLevel(str, Enum):
    """影响级别"""
    CRITICAL = "critical"   # 重大影响 (9-10分)
    HIGH = "high"           # 高度影响 (7-8分)
    MEDIUM = "medium"       # 中等影响 (4-6分)
    LOW = "low"             # 低影响 (1-3分)
    NONE = "none"           # 无影响 (0分)


@dataclass
class ImpactAssessment:
    """影响评估结果"""
    score: float            # 影响分数 0-10
    level: ImpactLevel      # 影响级别
    urgency: str            # 紧急程度
    factors: List[str]      # 影响因素
    recommendation: str     # 建议操作


class ImpactAssessor:
    """影响评估器"""
    
    def __init__(self):
        # 重大影响关键词 (9-10分)
        self._critical_keywords = {
            "退市", "强制退市", "暂停上市", "终止上市",
            "立案调查", "证监会调查", "涉嫌违法",
            "重大亏损", "巨额亏损", "资不抵债",
            "破产", "破产重整", "债务违约",
            "实控人被捕", "董事长被查", "高管失联",
            "财务造假", "虚假陈述", "信息披露违规",
            "停牌", "紧急停牌", "临时停牌",
        }
        
        # 高度影响关键词 (7-8分)
        self._high_keywords = {
            "业绩预亏", "业绩大幅下滑", "净利润下降",
            "重大诉讼", "重大仲裁", "巨额赔偿",
            "大股东减持", "高管减持", "清仓式减持",
            "股权质押", "质押爆仓", "强制平仓",
            "问询函", "监管函", "警示函", "关注函",
            "ST", "*ST", "风险警示",
            "重大合同终止", "订单取消", "客户流失",
            "产品召回", "安全事故", "环保处罚",
        }
        
        # 中等影响关键词 (4-6分)
        self._medium_keywords = {
            "业绩预告", "业绩快报", "季报", "年报",
            "增发", "配股", "可转债", "定向增发",
            "股权激励", "员工持股", "回购",
            "并购", "重组", "资产注入", "资产剥离",
            "战略合作", "签署协议", "中标",
            "新产品", "新技术", "专利", "研发突破",
            "高管变动", "董事会换届", "管理层调整",
        }
        
        # 低影响关键词 (1-3分)
        self._low_keywords = {
            "股东大会", "董事会决议", "监事会决议",
            "分红", "派息", "送股", "转增",
            "投资者关系", "调研", "路演",
            "评级", "研报", "目标价",
            "行业动态", "政策解读", "市场分析",
        }
        
        # 正面影响关键词 (加分)
        self._positive_keywords = {
            "业绩大增", "净利润增长", "营收增长", "超预期",
            "中标", "大单", "订单", "签约",
            "突破", "创新", "领先", "首发",
            "增持", "回购", "分红", "派息",
            "利好", "政策支持", "补贴", "减税",
        }
        
        # 负面影响关键词 (减分)
        self._negative_keywords = {
            "亏损", "下滑", "下降", "减少",
            "减持", "抛售", "清仓",
            "违规", "处罚", "罚款", "警告",
            "诉讼", "仲裁", "纠纷",
            "利空", "风险", "危机", "困难",
        }
        
        logger.info("ImpactAssessor initialized")
    
    def assess(self, title: str, content: str = "", sentiment_score: float = 50.0) -> ImpactAssessment:
        """
        评估新闻影响
        
        Args:
            title: 新闻标题
            content: 新闻内容
            sentiment_score: 情绪分数 (0-100)
            
        Returns:
            影响评估结果
        """
        text = f"{title} {content}"
        factors = []
        base_score = 0.0
        
        # 1. 检查重大影响关键词
        for kw in self._critical_keywords:
            if kw in text:
                base_score = max(base_score, 9.0)
                factors.append(f"重大事件: {kw}")
                break
        
        # 2. 检查高度影响关键词
        if base_score < 7:
            for kw in self._high_keywords:
                if kw in text:
                    base_score = max(base_score, 7.0)
                    factors.append(f"重要事件: {kw}")
                    break
        
        # 3. 检查中等影响关键词
        if base_score < 4:
            for kw in self._medium_keywords:
                if kw in text:
                    base_score = max(base_score, 4.0)
                    factors.append(f"一般事件: {kw}")
                    break
        
        # 4. 检查低影响关键词
        if base_score < 1:
            for kw in self._low_keywords:
                if kw in text:
                    base_score = max(base_score, 1.0)
                    factors.append(f"常规事件: {kw}")
                    break
        
        # 5. 正负面调整
        positive_count = sum(1 for kw in self._positive_keywords if kw in text)
        negative_count = sum(1 for kw in self._negative_keywords if kw in text)
        
        if positive_count > negative_count:
            factors.append(f"正面因素: {positive_count}个")
        elif negative_count > positive_count:
            factors.append(f"负面因素: {negative_count}个")
            base_score = min(base_score + 1, 10)  # 负面消息加分
        
        # 6. 情绪分数调整
        if sentiment_score < 30:
            base_score = min(base_score + 1, 10)
            factors.append("情绪极度负面")
        elif sentiment_score > 70:
            factors.append("情绪积极正面")
        
        # 7. 标题权重 (标题中出现关键词更重要)
        title_boost = 0
        for kw in list(self._critical_keywords) + list(self._high_keywords):
            if kw in title:
                title_boost = 1
                factors.append("标题含关键信息")
                break
        base_score = min(base_score + title_boost, 10)
        
        # 确定影响级别
        if base_score >= 9:
            level = ImpactLevel.CRITICAL
            urgency = "critical"
            recommendation = "立即关注，可能需要紧急操作"
        elif base_score >= 7:
            level = ImpactLevel.HIGH
            urgency = "high"
            recommendation = "高度关注，建议尽快评估"
        elif base_score >= 4:
            level = ImpactLevel.MEDIUM
            urgency = "medium"
            recommendation = "适度关注，纳入观察"
        elif base_score >= 1:
            level = ImpactLevel.LOW
            urgency = "low"
            recommendation = "一般关注，常规跟踪"
        else:
            level = ImpactLevel.NONE
            urgency = "low"
            recommendation = "无需特别关注"
        
        return ImpactAssessment(
            score=round(base_score, 1),
            level=level,
            urgency=urgency,
            factors=factors,
            recommendation=recommendation
        )
    
    def get_urgency(self, title: str, content: str = "") -> str:
        """快速获取紧急程度"""
        assessment = self.assess(title, content)
        return assessment.urgency
    
    def get_impact_score(self, title: str, content: str = "") -> float:
        """快速获取影响分数"""
        assessment = self.assess(title, content)
        return assessment.score


# 全局实例
_assessor = None

def get_impact_assessor() -> ImpactAssessor:
    global _assessor
    if _assessor is None:
        _assessor = ImpactAssessor()
    return _assessor
