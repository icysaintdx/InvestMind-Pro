"""
数据质量管控模块
负责策略选择输入数据的校验、清洗和标准化
"""

import numpy as np
from datetime import datetime
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class DataValidator:
    """数据验证器"""
    
    def __init__(self):
        self.required_analysis_fields = [
            "macroeconomic",
            "technical", 
            "fundamental",
            "risk_level",
            "period_suggestion"
        ]
        
        self.required_market_fields = [
            "price",
            "volume",
            "trend",
            "volatility"
        ]
    
    def validate_strategy_inputs(
        self,
        stock_analysis: Dict[str, Any],
        market_data: Dict[str, Any],
        news_sentiment: float
    ) -> Dict[str, Any]:
        """
        校验并清洗策略选择的输入数据
        
        Args:
            stock_analysis: 智能体分析结果
            market_data: 市场数据
            news_sentiment: 新闻情绪指数
            
        Returns:
            验证后的数据字典
            
        Raises:
            ValueError: 数据验证失败
        """
        logger.info("开始验证策略选择输入数据")
        
        # 1. 分析结果完整性校验
        self._validate_analysis_completeness(stock_analysis)
        
        # 2. 市场数据完整性校验
        self._validate_market_completeness(market_data)
        
        # 3. 行情数据异常值过滤
        cleaned_market_data = self._clean_market_data(market_data)
        
        # 4. 情绪指数标准化
        normalized_sentiment = self._normalize_sentiment(news_sentiment)
        
        # 5. 数据类型转换和验证
        validated_analysis = self._validate_analysis_values(stock_analysis)
        
        validated_data = {
            "stock_analysis": validated_analysis,
            "market_data": cleaned_market_data,
            "news_sentiment": normalized_sentiment,
            "validated_at": datetime.now().isoformat()
        }
        
        logger.info("数据验证完成")
        return validated_data
    
    def _validate_analysis_completeness(self, stock_analysis: Dict[str, Any]):
        """验证分析结果完整性"""
        missing_fields = [
            field for field in self.required_analysis_fields
            if field not in stock_analysis
        ]
        
        if missing_fields:
            raise ValueError(f"分析结果缺失关键字段：{missing_fields}")
        
        # 验证风险等级有效性
        valid_risk_levels = ["high", "medium", "low", "高", "中", "低"]
        risk_level = stock_analysis.get("risk_level", "")
        if risk_level not in valid_risk_levels:
            raise ValueError(f"无效的风险等级：{risk_level}，必须是 {valid_risk_levels} 之一")
    
    def _validate_market_completeness(self, market_data: Dict[str, Any]):
        """验证市场数据完整性"""
        missing_fields = [
            field for field in self.required_market_fields
            if field not in market_data
        ]
        
        if missing_fields:
            raise ValueError(f"市场数据缺失关键字段：{missing_fields}")
    
    def _clean_market_data(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        清洗市场数据
        - 使用3σ原则过滤异常值
        - 填充缺失值
        """
        cleaned_data = market_data.copy()
        
        # 价格异常值过滤（3σ原则）
        if "price" in cleaned_data and isinstance(cleaned_data["price"], (list, np.ndarray)):
            cleaned_data["price"] = self._filter_outliers(
                cleaned_data["price"],
                threshold=3
            )
        
        # 成交量异常值过滤和缺失值填充
        if "volume" in cleaned_data and isinstance(cleaned_data["volume"], (list, np.ndarray)):
            cleaned_data["volume"] = self._filter_outliers(
                cleaned_data["volume"],
                threshold=3
            )
            cleaned_data["volume"] = self._fill_missing_data(
                cleaned_data["volume"],
                method="linear"
            )
        
        # 波动率范围检查
        if "volatility" in cleaned_data:
            volatility = cleaned_data["volatility"]
            if volatility < 0:
                logger.warning(f"波动率为负值 {volatility}，设置为0")
                cleaned_data["volatility"] = 0
            elif volatility > 1:
                logger.warning(f"波动率超过100% {volatility}，可能异常")
        
        return cleaned_data
    
    def _filter_outliers(
        self,
        data: List[float],
        threshold: float = 3
    ) -> List[float]:
        """
        使用3σ原则过滤异常值
        
        Args:
            data: 数据列表
            threshold: 标准差倍数阈值
            
        Returns:
            过滤后的数据
        """
        if not data or len(data) < 3:
            return data
        
        data_array = np.array(data)
        mean = np.mean(data_array)
        std = np.std(data_array)
        
        if std == 0:
            return data
        
        # 计算z-score
        z_scores = np.abs((data_array - mean) / std)
        
        # 过滤超过阈值的异常值
        filtered_data = data_array[z_scores < threshold]
        
        if len(filtered_data) < len(data):
            logger.info(f"过滤了 {len(data) - len(filtered_data)} 个异常值")
        
        return filtered_data.tolist()
    
    def _fill_missing_data(
        self,
        data: List[float],
        method: str = "linear"
    ) -> List[float]:
        """
        填充缺失数据
        
        Args:
            data: 数据列表（可能包含None或NaN）
            method: 填充方法（linear/forward/backward）
            
        Returns:
            填充后的数据
        """
        if not data:
            return data
        
        data_array = np.array(data, dtype=float)
        
        # 检查是否有缺失值
        if not np.any(np.isnan(data_array)):
            return data
        
        if method == "linear":
            # 线性插值
            nans = np.isnan(data_array)
            if np.all(nans):
                return [0.0] * len(data)
            
            x = np.arange(len(data_array))
            data_array[nans] = np.interp(x[nans], x[~nans], data_array[~nans])
        
        elif method == "forward":
            # 前向填充
            for i in range(1, len(data_array)):
                if np.isnan(data_array[i]):
                    data_array[i] = data_array[i-1]
        
        elif method == "backward":
            # 后向填充
            for i in range(len(data_array)-2, -1, -1):
                if np.isnan(data_array[i]):
                    data_array[i] = data_array[i+1]
        
        return data_array.tolist()
    
    def _normalize_sentiment(self, news_sentiment: float) -> float:
        """
        标准化情绪指数到[-1, 1]区间
        
        Args:
            news_sentiment: 原始情绪指数
            
        Returns:
            标准化后的情绪指数
        """
        # 确保在[-1, 1]范围内
        normalized = max(min(news_sentiment, 1.0), -1.0)
        
        if normalized != news_sentiment:
            logger.info(f"情绪指数从 {news_sentiment} 标准化为 {normalized}")
        
        return normalized
    
    def _validate_analysis_values(self, stock_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """验证分析结果的数值范围"""
        validated = stock_analysis.copy()
        
        # 验证周期建议
        if "period_suggestion" in validated:
            period = validated["period_suggestion"]
            if isinstance(period, (int, float)):
                if period < 1:
                    logger.warning(f"周期建议 {period} 小于1天，设置为1")
                    validated["period_suggestion"] = 1
                elif period > 365:
                    logger.warning(f"周期建议 {period} 超过1年，设置为365")
                    validated["period_suggestion"] = 365
        
        # 验证评分范围（如果存在）
        for score_field in ["fundamental_score", "technical_score"]:
            if score_field in validated:
                score = validated[score_field]
                if isinstance(score, (int, float)):
                    validated[score_field] = max(0, min(100, score))
        
        # 标准化风险等级
        risk_mapping = {
            "高": "high",
            "中": "medium",
            "低": "low"
        }
        if "risk_level" in validated:
            risk = validated["risk_level"]
            validated["risk_level"] = risk_mapping.get(risk, risk)
        
        return validated


# 全局单例
_validator_instance = None


def get_data_validator() -> DataValidator:
    """获取数据验证器单例"""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = DataValidator()
    return _validator_instance


# 便捷函数
def validate_strategy_inputs(
    stock_analysis: Dict[str, Any],
    market_data: Dict[str, Any],
    news_sentiment: float
) -> Dict[str, Any]:
    """
    验证策略选择输入数据的便捷函数
    
    Args:
        stock_analysis: 智能体分析结果
        market_data: 市场数据
        news_sentiment: 新闻情绪指数
        
    Returns:
        验证后的数据字典
    """
    validator = get_data_validator()
    return validator.validate_strategy_inputs(
        stock_analysis,
        market_data,
        news_sentiment
    )
