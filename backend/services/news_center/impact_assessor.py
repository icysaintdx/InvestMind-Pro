# -*- coding: utf-8 -*-
"""
影响评估器 - AI驱动版本
使用LLM (kirocpa kimi-k2.5) 评估新闻对股票的影响程度
保留关键词匹配作为降级方案

Author: AI升级
Date: 2026-02-22
"""
import re
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
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
    # AI增强字段
    event_type: str = ""           # 事件类型
    impact_duration: str = ""      # 影响时效 short/medium/long
    affected_sectors: List[str] = field(default_factory=list)
    ai_analyzed: bool = False      # 是否经过AI分析

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "level": self.level.value,
            "urgency": self.urgency,
            "factors": self.factors,
            "recommendation": self.recommendation,
            "event_type": self.event_type,
            "impact_duration": self.impact_duration,
            "affected_sectors": self.affected_sectors,
            "ai_analyzed": self.ai_analyzed,
        }


class ImpactAssessor:
    """影响评估器 - AI驱动 + 关键词降级"""
    
    def __init__(self):
        self._llm_client = None
        self._init_llm()
        
        # === 降级用关键词（保留原有逻辑作为fallback） ===
        self._critical_keywords = {
            "退市", "强制退市", "暂停上市", "终止上市",
            "立案调查", "证监会调查", "涉嫌违法",
            "重大亏损", "巨额亏损", "资不抵债",
            "破产", "破产重整", "债务违约",
            "实控人被捕", "董事长被查", "高管失联",
            "财务造假", "虚假陈述", "信息披露违规",
            "停牌", "紧急停牌", "临时停牌",
        }
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
        self._medium_keywords = {
            "业绩预告", "业绩快报", "季报", "年报",
            "增发", "配股", "可转债", "定向增发",
            "股权激励", "员工持股", "回购",
            "并购", "重组", "资产注入", "资产剥离",
            "战略合作", "签署协议", "中标",
            "新产品", "新技术", "专利", "研发突破",
            "高管变动", "董事会换届", "管理层调整",
        }
        self._low_keywords = {
            "股东大会", "董事会决议", "监事会决议",
            "分红", "派息", "送股", "转增",
            "投资者关系", "调研", "路演",
            "评级", "研报", "目标价",
            "行业动态", "政策解读", "市场分析",
        }
        self._positive_keywords = {
            "业绩大增", "净利润增长", "营收增长", "超预期",
            "中标", "大单", "订单", "签约",
            "突破", "创新", "领先", "首发",
            "增持", "回购", "分红", "派息",
            "利好", "政策支持", "补贴", "减税",
        }
        self._negative_keywords = {
            "亏损", "下滑", "下降", "减少",
            "减持", "抛售", "清仓",
            "违规", "处罚", "罚款", "警告",
            "诉讼", "仲裁", "纠纷",
            "利空", "风险", "危机", "困难",
        }
        
        logger.info("ImpactAssessor initialized (AI-enhanced)")
    
    def _init_llm(self):
        """初始化LLM客户端 (kirocpa kimi-k2.5)"""
        try:
            from openai import OpenAI
            self._llm_client = OpenAI(
                api_key="icysaintdx",
                base_url="https://kirocpa.zeabur.app/v1"
            )
            logger.info("ImpactAssessor LLM client initialized (kirocpa/kimi-k2.5)")
        except Exception as e:
            logger.warning(f"Failed to init LLM client: {e}")
            self._llm_client = None
    
    async def assess_with_ai(
        self, title: str, content: str = "", stock_code: str = ""
    ) -> ImpactAssessment:
        """
        AI驱动的影响评估（主方法）
        
        失败时自动降级到关键词匹配
        """
        if not self._llm_client:
            return self.assess(title, content)
        
        try:
            prompt = self._build_assessment_prompt(title, content, stock_code)
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._llm_client.chat.completions.create(
                    model="kimi-k2.5",
                    messages=[
                        {"role": "system", "content": "你是专业的A股金融新闻影响评估分析师。只输出JSON，不要其他内容。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    max_tokens=600
                )
            )
            
            if not response or not response.choices:
                logger.warning("LLM returned empty response, falling back to keywords")
                return self.assess(title, content)
            
            result_text = response.choices[0].message.content
            return self._parse_ai_response(result_text, title)
            
        except Exception as e:
            error_msg = str(e)
            if "balance" in error_msg.lower() or "insufficient" in error_msg.lower():
                logger.warning("LLM balance insufficient, using keyword fallback")
            else:
                logger.error(f"AI assessment failed: {e}")
            return self.assess(title, content)
    
    def _build_assessment_prompt(self, title: str, content: str, stock_code: str) -> str:
        stock_ctx = f"\n相关股票: {stock_code}" if stock_code else ""
        return f"""评估以下A股新闻对股票的影响程度。

新闻标题: {title}{stock_ctx}
新闻内容: {content[:400] if content else "无"}

输出JSON:
{{
    "score": 0.0,
    "urgency": "low",
    "event_type": "",
    "impact_duration": "",
    "affected_sectors": [],
    "factors": [],
    "recommendation": "",
    "sentiment": ""
}}

评分标准:
- 9-10: 退市/立案调查/财务造假/破产等重大事件
- 7-8: 业绩大幅变动/大股东清仓减持/重大诉讼/ST
- 4-6: 业绩预告/并购重组/战略合作/增发配股
- 1-3: 分红/研报/调研/常规公告
- 0: 无实质影响"""
    
    def _parse_ai_response(self, text: str, title: str) -> ImpactAssessment:
        """解析AI响应"""
        try:
            json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_match = re.search(r'\{.*\}', text, re.DOTALL)
                json_str = json_match.group(0) if json_match else text
            
            data = json.loads(json_str)
            score = max(0, min(10, float(data.get("score", 0))))
            
            if score >= 9:
                level = ImpactLevel.CRITICAL
            elif score >= 7:
                level = ImpactLevel.HIGH
            elif score >= 4:
                level = ImpactLevel.MEDIUM
            elif score >= 1:
                level = ImpactLevel.LOW
            else:
                level = ImpactLevel.NONE
            
            return ImpactAssessment(
                score=round(score, 1),
                level=level,
                urgency=data.get("urgency", "low"),
                factors=data.get("factors", []),
                recommendation=data.get("recommendation", ""),
                event_type=data.get("event_type", "其他"),
                impact_duration=data.get("impact_duration", "short"),
                affected_sectors=data.get("affected_sectors", []),
                ai_analyzed=True
            )
        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            return self.assess(title)
    
    def assess(self, title: str, content: str = "", sentiment_score: float = 50.0) -> ImpactAssessment:
        """
        关键词匹配评估（降级方案，保持原有逻辑）
        """
        text = f"{title} {content}"
        factors = []
        base_score = 0.0
        
        for kw in self._critical_keywords:
            if kw in text:
                base_score = max(base_score, 9.0)
                factors.append(f"重大事件: {kw}")
                break
        
        if base_score < 7:
            for kw in self._high_keywords:
                if kw in text:
                    base_score = max(base_score, 7.0)
                    factors.append(f"重要事件: {kw}")
                    break
        
        if base_score < 4:
            for kw in self._medium_keywords:
                if kw in text:
                    base_score = max(base_score, 4.0)
                    factors.append(f"一般事件: {kw}")
                    break
        
        if base_score < 1:
            for kw in self._low_keywords:
                if kw in text:
                    base_score = max(base_score, 1.0)
                    factors.append(f"常规事件: {kw}")
                    break
        
        positive_count = sum(1 for kw in self._positive_keywords if kw in text)
        negative_count = sum(1 for kw in self._negative_keywords if kw in text)
        
        if positive_count > negative_count:
            factors.append(f"正面因素: {positive_count}个")
        elif negative_count > positive_count:
            factors.append(f"负面因素: {negative_count}个")
            base_score = min(base_score + 1, 10)
        
        if sentiment_score < 30:
            base_score = min(base_score + 1, 10)
            factors.append("情绪极度负面")
        elif sentiment_score > 70:
            factors.append("情绪积极正面")
        
        title_boost = 0
        for kw in list(self._critical_keywords) + list(self._high_keywords):
            if kw in title:
                title_boost = 1
                factors.append("标题含关键信息")
                break
        base_score = min(base_score + title_boost, 10)
        
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
            recommendation=recommendation,
            ai_analyzed=False
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
