# -*- coding: utf-8 -*-
"""
新闻情绪分析引擎
使用LLM (SiliconFlow Qwen) 进行深度情绪分析

Author: 臭宝
Date: 2026-02-19
"""

import json
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class SentimentAnalysis:
    """情绪分析结果"""
    sentiment: str          # positive/negative/neutral
    score: float           # -1.0 ~ 1.0
    confidence: float      # 0.0 ~ 1.0
    
    # 事件分类
    event_type: str        # 业绩/政策/重组/股东/其他
    event_subtype: str     # 子类型
    
    # 影响评估
    impact_level: str      # high/medium/low
    impact_duration: str   # short/medium/long (短期1-3天/中期1-4周/长期1-6月)
    affected_sectors: List[str]  # 影响板块
    
    # 摘要和关键词
    summary: str           # AI摘要
    key_points: List[str]  # 关键要点
    risk_factors: List[str] # 风险因素
    
    # 原始响应
    raw_response: Dict[str, Any]


class NewsEmotionAnalyzer:
    """
    新闻情绪分析器
    
    使用配置的LLM (SiliconFlow Qwen 38B) 进行深度分析
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._llm_client = None
        self._init_llm()
        
    def _init_llm(self):
        """初始化LLM客户端"""
        try:
            # 尝试使用已配置的LLM
            from backend.services.llm.llm_service import get_llm_service
            self._llm_client = get_llm_service()
            self.logger.info("LLM client initialized via llm_service")
        except Exception as e:
            self.logger.warning(f"Failed to init via llm_service: {e}")
            # 备用：直接初始化
            try:
                self._llm_client = self._create_direct_llm_client()
                self.logger.info("LLM client initialized directly")
            except Exception as e2:
                self.logger.error(f"Failed to init LLM client: {e2}")
                self._llm_client = None
    
    def _create_direct_llm_client(self):
        """直接创建LLM客户端（备用方案）"""
        import os
        from pathlib import Path
        from dotenv import load_dotenv
        
        # 加载.env文件
        env_path = Path(__file__).parent.parent.parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        
        api_key = os.getenv("SILICONFLOW_API_KEY")
        if not api_key:
            raise ValueError("SILICONFLOW_API_KEY not configured")
        
        from openai import OpenAI
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.siliconflow.cn/v1"
        )
        return client
    
    async def analyze(self, title: str, content: str = "", stock_code: str = None) -> SentimentAnalysis:
        """
        分析新闻情绪
        
        Args:
            title: 新闻标题
            content: 新闻内容
            stock_code: 股票代码（可选，用于上下文）
            
        Returns:
            SentimentAnalysis: 分析结果
        """
        if not self._llm_client:
            self.logger.warning("LLM client not available, using fallback")
            return self._fallback_analysis(title)
        
        try:
            # 构建提示词
            prompt = self._build_prompt(title, content, stock_code)
            
            # 调用LLM
            response = await self._call_llm(prompt)
            
            # 解析结果
            analysis = self._parse_response(response, title)
            
            self.logger.info(f"Analyzed: {title[:50]}... | Score: {analysis.score}")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            return self._fallback_analysis(title)
    
    def _build_prompt(self, title: str, content: str, stock_code: str = None) -> str:
        """构建分析提示词"""
        
        stock_context = f"相关股票: {stock_code}\n" if stock_code else ""
        
        prompt = f"""你是一位专业的金融新闻分析师。请分析以下新闻的情绪、事件类型和影响。

新闻标题: {title}
{stock_context}
新闻内容: {content[:500] if content else title}

请输出JSON格式的分析结果:
{{
    "sentiment": "positive/negative/neutral",
    "score": 0.0,  // -1.0到1.0，-1极负面，1极正面，0中性
    "confidence": 0.0,  // 0-1，置信度
    
    "event_type": "业绩/政策/重组/并购/股东/龙虎榜/公告/行业/其他",
    "event_subtype": "具体子类型",
    
    "impact_level": "high/medium/low",
    "impact_duration": "short/medium/long",  // short=1-3天, medium=1-4周, long=1-6月
    "affected_sectors": ["板块1", "板块2"],
    
    "summary": "100字以内的新闻摘要",
    "key_points": ["要点1", "要点2", "要点3"],
    "risk_factors": ["风险1", "风险2"]
}}

分析要求:
1. score要精确到小数点后2位
2. 必须基于新闻内容，不要过度推断
3. 如果是业绩类新闻，score应该反映业绩好坏（预增=positive，预减=negative）
4. 如果是政策类，考虑对行业和公司的影响
5. 如果是股东增减持，增持=positive，减持=negative
6. confidence反映你的确定程度，信息越明确confidence越高"""
        
        return prompt
    
    async def _call_llm(self, prompt: str) -> str:
        """调用LLM"""
        try:
            # 方式1: 通过llm_service
            if hasattr(self._llm_client, 'generate'):
                return await self._llm_client.generate(prompt)
            
            # 方式2: 直接调用OpenAI格式
            import asyncio
            loop = asyncio.get_event_loop()
            
            response = await loop.run_in_executor(
                None,
                lambda: self._llm_client.chat.completions.create(
                    model="Qwen/Qwen2.5-32B-Instruct",  # 使用配置的38B模型
                    messages=[
                        {"role": "system", "content": "你是一个专业的金融新闻分析师。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,  # 低温度，更确定性的输出
                    max_tokens=800
                )
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"LLM call failed: {e}")
            raise
    
    def _parse_response(self, response: str, title: str) -> SentimentAnalysis:
        """解析LLM响应"""
        try:
            # 提取JSON
            json_str = self._extract_json(response)
            data = json.loads(json_str)
            
            return SentimentAnalysis(
                sentiment=data.get("sentiment", "neutral"),
                score=float(data.get("score", 0)),
                confidence=float(data.get("confidence", 0.5)),
                event_type=data.get("event_type", "其他"),
                event_subtype=data.get("event_subtype", ""),
                impact_level=data.get("impact_level", "low"),
                impact_duration=data.get("impact_duration", "short"),
                affected_sectors=data.get("affected_sectors", []),
                summary=data.get("summary", title[:100]),
                key_points=data.get("key_points", []),
                risk_factors=data.get("risk_factors", []),
                raw_response=data
            )
            
        except Exception as e:
            self.logger.error(f"Parse response failed: {e}")
            return self._fallback_analysis(title)
    
    def _extract_json(self, text: str) -> str:
        """从文本中提取JSON"""
        # 尝试找到JSON块
        import re
        
        # 寻找```json ... ```格式
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        # 寻找``` ... ```格式
        json_match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        # 寻找{...}格式
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json_match.group(0)
        
        # 如果没有找到，假设整个文本就是JSON
        return text
    
    def _fallback_analysis(self, title: str) -> SentimentAnalysis:
        """备用分析（基于关键词）"""
        title_lower = title.lower()
        
        # 简单关键词匹配
        positive_words = ['预增', '增长', '利好', '突破', '创新高', '中标', '订单']
        negative_words = ['预减', '亏损', '下滑', '利空', '减持', '跌停', '暴雷']
        
        pos_count = sum(1 for w in positive_words if w in title_lower)
        neg_count = sum(1 for w in negative_words if w in title_lower)
        
        if pos_count > neg_count:
            sentiment = "positive"
            score = min(0.3 + pos_count * 0.1, 0.8)
        elif neg_count > pos_count:
            sentiment = "negative"
            score = max(-0.3 - neg_count * 0.1, -0.8)
        else:
            sentiment = "neutral"
            score = 0.0
        
        return SentimentAnalysis(
            sentiment=sentiment,
            score=round(score, 2),
            confidence=0.5,
            event_type="其他",
            event_subtype="",
            impact_level="low",
            impact_duration="short",
            affected_sectors=[],
            summary=title[:100],
            key_points=[],
            risk_factors=[],
            raw_response={"fallback": True}
        )
    
    async def batch_analyze(self, news_list: List[Dict]) -> List[SentimentAnalysis]:
        """
        批量分析新闻
        
        Args:
            news_list: 新闻列表，每项包含title和content
            
        Returns:
            分析结果列表
        """
        tasks = []
        for news in news_list:
            task = self.analyze(
                title=news.get("title", ""),
                content=news.get("content", ""),
                stock_code=news.get("stock_code")
            )
            tasks.append(task)
        
        return await asyncio.gather(*tasks)


# 全局实例
_emotion_analyzer = None

def get_emotion_analyzer() -> NewsEmotionAnalyzer:
    """获取情绪分析器实例（单例）"""
    global _emotion_analyzer
    if _emotion_analyzer is None:
        _emotion_analyzer = NewsEmotionAnalyzer()
    return _emotion_analyzer


# 便捷函数
async def analyze_news_emotion(title: str, content: str = "", stock_code: str = None) -> Dict[str, Any]:
    """便捷函数：快速分析新闻情绪"""
    analyzer = get_emotion_analyzer()
    result = await analyzer.analyze(title, content, stock_code)
    return {
        "sentiment": result.sentiment,
        "score": result.score,
        "confidence": result.confidence,
        "event_type": result.event_type,
        "impact_level": result.impact_level,
        "impact_duration": result.impact_duration,
        "summary": result.summary
    }


# 测试代码
if __name__ == "__main__":
    import os
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 检查API key
    if not os.getenv("SILICONFLOW_API_KEY"):
        print("⚠️  SILICONFLOW_API_KEY not set, using fallback analysis")
    
    analyzer = NewsEmotionAnalyzer()
    
    # 测试用例
    test_news = [
        {
            "title": "贵州茅台：预计2025年净利润同比增长50%以上",
            "content": "贵州茅台发布业绩预告，预计2025年净利润同比增长50%以上，主要得益于..."
        },
        {
            "title": "XX股份：实控人计划减持不超过5%股份",
            "content": "公司公告，实控人因个人资金需求，计划减持不超过5%股份..."
        },
        {
            "title": "宁德时代：与特斯拉签订重大供货协议",
            "content": "宁德时代宣布与特斯拉签订长期供货协议，预计订单金额达100亿元..."
        }
    ]
    
    print("=" * 80)
    print("新闻情绪分析测试")
    print("=" * 80)
    
    async def run_tests():
        for news in test_news:
            print(f"\n新闻: {news['title']}")
            try:
                result = await analyzer.analyze(news['title'], news.get('content', ''))
                print(f"  情绪: {result.sentiment} | 分数: {result.score}")
                print(f"  事件类型: {result.event_type}")
                print(f"  影响级别: {result.impact_level} | 持续时间: {result.impact_duration}")
                print(f"  置信度: {result.confidence}")
                print(f"  摘要: {result.summary}")
            except Exception as e:
                print(f"  ❌ 分析失败: {e}")
    
    asyncio.run(run_tests())
