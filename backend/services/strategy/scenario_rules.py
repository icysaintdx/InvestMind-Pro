"""
场景化规则引擎
根据市场环境、股票类型、分析结果动态生成引导规则
"""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class ScenarioRuleEngine:
    """场景化规则引擎"""
    
    def get_scenario_guidance(
        self,
        stock_analysis: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> List[str]:
        """
        根据场景返回差异化的LLM引导规则
        
        Args:
            stock_analysis: 股票分析结果
            market_data: 市场数据
            
        Returns:
            场景化规则列表
        """
        scenario_rules = []
        
        # 1. 市场场景规则
        market_rules = self._get_market_scenario_rules(market_data)
        scenario_rules.extend(market_rules)
        
        # 2. 股票类型规则
        stock_type_rules = self._get_stock_type_rules(stock_analysis)
        scenario_rules.extend(stock_type_rules)
        
        # 3. 分析结果特征规则
        analysis_rules = self._get_analysis_feature_rules(stock_analysis)
        scenario_rules.extend(analysis_rules)
        
        # 4. 风险等级规则
        risk_rules = self._get_risk_level_rules(stock_analysis)
        scenario_rules.extend(risk_rules)
        
        logger.info(f"生成了 {len(scenario_rules)} 条场景化规则")
        return scenario_rules
    
    def _get_market_scenario_rules(self, market_data: Dict[str, Any]) -> List[str]:
        """获取市场场景规则"""
        rules = []
        
        # 波动率场景
        volatility = market_data.get("volatility", 0)
        if volatility > 0.08:  # 8%
            rules.append(
                "高波动率场景：优先选择止损严格、仓位低的保守型策略，避免杠杆类策略"
            )
        elif volatility < 0.03:  # 3%
            rules.append(
                "低波动率场景：可适当提高仓位，优先选择趋势跟踪策略"
            )
        
        # 市场趋势场景
        trend = market_data.get("trend", "").lower()
        if trend == "sideways" or trend == "震荡":
            rules.append(
                "震荡市场场景：优先选择区间交易、高抛低吸类策略，避免趋势跟踪策略"
            )
        elif trend == "down" or trend == "下跌" or trend == "熊市":
            rules.append(
                "熊市场景：最大仓位不超过20%，优先选择空头策略或空仓，禁止选择进攻型策略"
            )
        elif trend == "up" or trend == "上涨" or trend == "牛市":
            rules.append(
                "牛市场景：可适当提高仓位，优先选择趋势跟踪策略，关注动量指标"
            )
        
        # 成交量场景
        volume_trend = market_data.get("volume_trend", "")
        if volume_trend == "surge" or volume_trend == "放量":
            rules.append(
                "成交量放大场景：关注量价配合，优先选择突破类策略"
            )
        elif volume_trend == "shrink" or volume_trend == "缩量":
            rules.append(
                "成交量萎缩场景：谨慎操作，避免追涨杀跌，优先观望"
            )
        
        return rules
    
    def _get_stock_type_rules(self, stock_analysis: Dict[str, Any]) -> List[str]:
        """获取股票类型规则"""
        rules = []
        
        stock_type = stock_analysis.get("stock_type", "").lower()
        
        if "成长" in stock_type or "growth" in stock_type:
            rules.append(
                "成长股场景：优先选择中长期策略（≥30天），关注业绩预告相关的新闻敏感度"
            )
        
        if "价值" in stock_type or "value" in stock_type:
            rules.append(
                "价值股场景：优先选择低估值策略，关注分红、回购等价值信号"
            )
        
        if "周期" in stock_type or "cyclical" in stock_type:
            rules.append(
                "周期股场景：优先选择与行业轮动匹配的策略，关注宏观经济指标匹配度"
            )
        
        if "科技" in stock_type or "tech" in stock_type:
            rules.append(
                "科技股场景：波动较大，优先选择止损严格的策略，关注政策和行业新闻"
            )
        
        if "蓝筹" in stock_type or "blue_chip" in stock_type:
            rules.append(
                "蓝筹股场景：波动较小，可适当提高仓位，优先选择稳健型策略"
            )
        
        return rules
    
    def _get_analysis_feature_rules(self, stock_analysis: Dict[str, Any]) -> List[str]:
        """获取分析结果特征规则"""
        rules = []
        
        # 获取评分
        fundamental_score = stock_analysis.get("fundamental_score", 50)
        technical_score = stock_analysis.get("technical_score", 50)
        
        # 基本面vs技术面
        if fundamental_score > 80 and technical_score < 60:
            rules.append(
                "基本面优但技术面弱：优先选择低频率建仓的中长期策略，避免短期交易"
            )
        elif fundamental_score < 60 and technical_score > 80:
            rules.append(
                "技术面优但基本面弱：优先选择短线策略（≤7天），严格设置止损，快进快出"
            )
        elif fundamental_score > 70 and technical_score > 70:
            rules.append(
                "基本面和技术面双优：可选择中期策略，适当提高仓位"
            )
        elif fundamental_score < 50 and technical_score < 50:
            rules.append(
                "基本面和技术面双弱：建议观望，如必须操作则选择最保守策略，最小仓位"
            )
        
        # 估值水平
        valuation = stock_analysis.get("valuation", "")
        if "高估" in valuation or "overvalued" in valuation.lower():
            rules.append(
                "高估值场景：谨慎追高，优先选择止盈及时的策略"
            )
        elif "低估" in valuation or "undervalued" in valuation.lower():
            rules.append(
                "低估值场景：可适当提高仓位，优先选择价值回归策略"
            )
        
        # 盈利能力
        profitability = stock_analysis.get("profitability", "")
        if "优秀" in profitability or "excellent" in profitability.lower():
            rules.append(
                "盈利能力优秀：可选择较长持有周期，关注业绩持续性"
            )
        elif "较差" in profitability or "poor" in profitability.lower():
            rules.append(
                "盈利能力较差：谨慎操作，优先选择短期策略，严格止损"
            )
        
        return rules
    
    def _get_risk_level_rules(self, stock_analysis: Dict[str, Any]) -> List[str]:
        """获取风险等级规则"""
        rules = []
        
        risk_level = stock_analysis.get("risk_level", "medium").lower()
        fundamental_score = stock_analysis.get("fundamental_score", 50)
        
        if risk_level == "high" or risk_level == "高":
            rules.append(
                "高风险场景：最大仓位≤50%，必须设置严格止损，优先选择灵活的短期策略"
            )
            
            if fundamental_score < 70:
                rules.append(
                    "高风险+基本面差：禁止选择任何高仓位策略，最大仓位≤15%"
                )
        
        elif risk_level == "medium" or risk_level == "中":
            rules.append(
                "中等风险场景：最大仓位≤30%，平衡收益与风险，优先选择中期策略"
            )
        
        elif risk_level == "low" or risk_level == "低":
            rules.append(
                "低风险场景：最大仓位≤15%，优先选择稳健型策略，可适当延长持有周期"
            )
        
        # 风险预警
        risk_warning = stock_analysis.get("risk_warning", [])
        if risk_warning:
            if isinstance(risk_warning, list) and len(risk_warning) > 0:
                rules.append(
                    f"存在风险预警：{', '.join(risk_warning[:3])}，必须设置止损并降低仓位"
                )
        
        return rules


# 全局单例
_scenario_engine_instance = None


def get_scenario_rule_engine() -> ScenarioRuleEngine:
    """获取场景规则引擎单例"""
    global _scenario_engine_instance
    if _scenario_engine_instance is None:
        _scenario_engine_instance = ScenarioRuleEngine()
    return _scenario_engine_instance


# 便捷函数
def get_scenario_guidance(
    stock_analysis: Dict[str, Any],
    market_data: Dict[str, Any]
) -> List[str]:
    """
    获取场景化引导规则的便捷函数
    
    Args:
        stock_analysis: 股票分析结果
        market_data: 市场数据
        
    Returns:
        场景化规则列表
    """
    engine = get_scenario_rule_engine()
    return engine.get_scenario_guidance(stock_analysis, market_data)
