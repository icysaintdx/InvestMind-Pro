"""
统一的LLM调用服务
为策略选择、交易决策、跟踪决策等模块提供真实的LLM调用能力
集成前端LLM配置，支持动态切换模型
"""

import httpx
import json
import os
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from backend.utils.logging_config import get_logger

logger = get_logger("services.llm")

# API URLs
API_URLS = {
    "siliconflow": "https://api.siliconflow.cn/v1/chat/completions",
    "deepseek": "https://api.deepseek.com/v1/chat/completions",
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
}

# 默认模型配置（当配置文件不可用时使用）
DEFAULT_MODELS = {
    "siliconflow": "Qwen/Qwen2.5-7B-Instruct",
    "deepseek": "deepseek-chat",
    "qwen": "qwen-turbo",
    "gemini": "gemini-pro",
}


def get_api_key(provider: str) -> str:
    """获取API Key - 优先从环境变量读取"""
    env_keys = {
        "siliconflow": "SILICONFLOW_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "qwen": "DASHSCOPE_API_KEY",
        "gemini": "GOOGLE_API_KEY",
    }
    return os.getenv(env_keys.get(provider, ""), "")


class LLMService:
    """统一的LLM调用服务 - 集成前端配置"""

    def __init__(self):
        self.timeout = httpx.Timeout(
            timeout=60.0,
            connect=15.0,
            read=45.0,
            write=15.0
        )
        self._config_cache = {}
        self._config_cache_time = None

    def _infer_provider_from_model(self, model: str) -> Optional[str]:
        """
        根据模型名称推断正确的provider

        Args:
            model: 模型名称

        Returns:
            provider名称，如果无法推断则返回None
        """
        if not model:
            return None

        # 包含斜杠的模型名（如 Qwen/Qwen3-8B）都是SiliconFlow托管的
        if "/" in model:
            return "siliconflow"

        # 官方直连模型
        model_lower = model.lower()
        if model_lower.startswith("gemini"):
            return "gemini"
        elif model_lower in ["deepseek-chat", "deepseek-coder", "deepseek-reasoner"]:
            return "deepseek"
        elif model_lower in ["qwen-max", "qwen-plus", "qwen-turbo", "qwen-max-longcontext", "qwen-turbo-latest"]:
            return "qwen"
        elif model_lower.startswith("qwen"):
            # qwen2.5-7b-instruct 等阿里云模型
            return "qwen"

        # 默认使用siliconflow
        return "siliconflow"

    def get_task_config(self, task_name: str) -> Dict[str, Any]:
        """
        获取任务的LLM配置 - 从前端配置文件读取

        Args:
            task_name: 任务名称 (strategy_selector/trade_decision/market_analyzer)

        Returns:
            配置字典
        """
        try:
            from backend.api.trading_llm_config_api import get_trading_llm_config
            config = get_trading_llm_config(task_name)
            logger.debug(f"获取任务配置: {task_name} -> {config}")
            return config
        except Exception as e:
            logger.warning(f"获取任务配置失败: {task_name}, {e}")
            # 返回默认配置
            return {
                "provider": "siliconflow",
                "model": DEFAULT_MODELS.get("siliconflow"),
                "enabled": True,
                "temperature": 0.7,
                "max_tokens": 2048
            }

    async def call_llm(
        self,
        prompt: str,
        system_prompt: str = "你是一个专业的量化交易分析师。",
        task_name: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: str = "json"
    ) -> Dict[str, Any]:
        """
        调用LLM API - 支持从前端配置读取参数

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            task_name: 任务名称（用于读取前端配置）
            provider: API提供商 (覆盖配置)
            model: 模型名称 (覆盖配置)
            temperature: 温度参数 (覆盖配置)
            max_tokens: 最大token数 (覆盖配置)
            response_format: 响应格式 (json/text)

        Returns:
            LLM响应结果
        """
        # 如果指定了task_name，从前端配置读取参数
        if task_name:
            config = self.get_task_config(task_name)
            if not config.get("enabled", True):
                raise ValueError(f"任务 {task_name} 的LLM已禁用")
            model = model or config.get("model")
            temperature = temperature if temperature is not None else config.get("temperature", 0.7)
            max_tokens = max_tokens or config.get("max_tokens", 2048)
            # 根据model自动推断provider（优先级高于配置文件中的provider）
            provider = provider or self._infer_provider_from_model(model) or config.get("provider", "siliconflow")
        else:
            provider = provider or "siliconflow"
            temperature = temperature if temperature is not None else 0.7
            max_tokens = max_tokens or 2048

        api_key = get_api_key(provider)
        api_url = API_URLS.get(provider)

        if not api_key:
            logger.warning(f"未配置 {provider} API Key，尝试使用备用提供商")
            # 尝试备用提供商
            for backup_provider in ["siliconflow", "deepseek", "qwen"]:
                if backup_provider != provider and get_api_key(backup_provider):
                    provider = backup_provider
                    api_key = get_api_key(provider)
                    api_url = API_URLS[provider]
                    logger.info(f"使用备用提供商: {provider}")
                    break

            if not api_key:
                raise ValueError("未配置任何可用的LLM API Key，请在环境变量中设置")

        model = model or DEFAULT_MODELS.get(provider)

        # 如果需要JSON响应，在提示词中强调
        if response_format == "json":
            system_prompt += "\n\n重要：请严格以JSON格式返回结果，不要包含任何其他文字说明。"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                logger.info(f"调用LLM: provider={provider}, model={model}")
                response = await client.post(api_url, headers=headers, json=data)
                response.raise_for_status()

                result = response.json()
                content = result["choices"][0]["message"]["content"]

                # 尝试解析JSON
                if response_format == "json":
                    try:
                        # 清理可能的markdown代码块
                        content = content.strip()
                        if content.startswith("```json"):
                            content = content[7:]
                        if content.startswith("```"):
                            content = content[3:]
                        if content.endswith("```"):
                            content = content[:-3]
                        content = content.strip()

                        parsed = json.loads(content)
                        return {
                            "success": True,
                            "data": parsed,
                            "raw": content,
                            "provider": provider,
                            "model": model
                        }
                    except json.JSONDecodeError as e:
                        logger.warning(f"JSON解析失败: {e}, 返回原始文本")
                        return {
                            "success": True,
                            "data": content,
                            "raw": content,
                            "provider": provider,
                            "model": model,
                            "parse_error": str(e)
                        }

                return {
                    "success": True,
                    "data": content,
                    "raw": content,
                    "provider": provider,
                    "model": model
                }

            except httpx.TimeoutException as e:
                logger.error(f"LLM调用超时: {e}")
                raise
            except httpx.HTTPStatusError as e:
                logger.error(f"LLM调用HTTP错误: {e}")
                raise
            except Exception as e:
                logger.error(f"LLM调用失败: {e}")
                raise


# 全局实例
_llm_service = None


def get_llm_service() -> LLMService:
    """获取LLM服务实例"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


async def call_strategy_selector_llm(
    stock_code: str,
    stock_name: str,
    analysis_summary: str,
    technical_score: float,
    fundamental_score: float,
    sentiment_score: float,
    risk_level: str,
    risk_preference: str,
    available_strategies: List[Dict]
) -> Dict[str, Any]:
    """
    调用LLM进行策略选择

    Args:
        stock_code: 股票代码
        stock_name: 股票名称
        analysis_summary: 分析摘要
        technical_score: 技术面评分
        fundamental_score: 基本面评分
        sentiment_score: 情绪评分
        risk_level: 风险等级
        risk_preference: 风险偏好
        available_strategies: 可用策略列表

    Returns:
        策略推荐结果
    """
    llm = get_llm_service()

    # 构建策略列表描述
    strategies_desc = "\n".join([
        f"- {s['strategy_id']}: {s['name']} ({s['category']}) - {s['description']}"
        for s in available_strategies
    ])

    prompt = f"""请根据以下股票分析结果，从可用策略中推荐最适合的交易策略。

## 股票信息
- 代码：{stock_code}
- 名称：{stock_name}

## 分析结果
{analysis_summary}

## 评分
- 技术面评分：{technical_score:.2f} (0-1)
- 基本面评分：{fundamental_score:.2f} (0-1)
- 情绪评分：{sentiment_score:.2f} (0-1)
- 风险等级：{risk_level}

## 用户风险偏好
{risk_preference} (conservative=保守/moderate=稳健/aggressive=激进)

## 可用策略列表
{strategies_desc}

## 要求
请分析并推荐1-3个最适合的策略，返回JSON格式：
{{
    "recommendations": [
        {{
            "strategy_id": "策略ID",
            "confidence": 0.85,
            "reason": "推荐理由（结合分析结果说明为什么这个策略适合）",
            "parameters": {{"参数名": "建议值"}}
        }}
    ],
    "reasoning": "整体推荐逻辑说明"
}}
"""

    system_prompt = """你是一个专业的量化交易策略顾问，擅长根据股票分析结果推荐合适的交易策略。
你需要综合考虑：
1. 股票的技术面、基本面、情绪面特征
2. 用户的风险偏好
3. 各策略的适用场景和特点
4. 当前市场环境

请给出专业、客观的策略推荐。"""

    try:
        # 使用task_name读取前端配置
        result = await llm.call_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            task_name="strategy_selector",  # 对应前端配置
            temperature=0.5,
            max_tokens=2048,
            response_format="json"
        )

        if result["success"] and isinstance(result["data"], dict):
            return result["data"]
        else:
            logger.warning("LLM返回格式不正确，使用默认推荐")
            return _get_default_strategy_recommendation(
                technical_score, fundamental_score, sentiment_score, risk_preference
            )

    except Exception as e:
        logger.error(f"策略选择LLM调用失败: {e}")
        return _get_default_strategy_recommendation(
            technical_score, fundamental_score, sentiment_score, risk_preference
        )


def _get_default_strategy_recommendation(
    technical_score: float,
    fundamental_score: float,
    sentiment_score: float,
    risk_preference: str
) -> Dict[str, Any]:
    """获取默认策略推荐（LLM调用失败时的降级方案）"""
    recommendations = []

    # 根据评分选择策略
    if fundamental_score >= 0.7:
        recommendations.append({
            "strategy_id": "buffett_value",
            "confidence": 0.7,
            "reason": "基本面评分较高，适合价值投资策略",
            "parameters": {}
        })

    if technical_score >= 0.6:
        recommendations.append({
            "strategy_id": "vegas_adx",
            "confidence": 0.65,
            "reason": "技术面评分良好，适合趋势跟踪策略",
            "parameters": {}
        })

    if not recommendations:
        recommendations.append({
            "strategy_id": "macd_crossover",
            "confidence": 0.6,
            "reason": "通用技术策略，适合大多数市场环境",
            "parameters": {}
        })

    return {
        "recommendations": recommendations[:3],
        "reasoning": "基于规则的默认推荐（LLM服务暂时不可用）"
    }


async def call_trading_decision_llm(
    stock_code: str,
    current_price: float,
    change_rate: float,
    volume: float,
    analysis_result: Optional[Dict],
    current_position: Optional[Dict],
    strategy_id: Optional[str],
    news_summary: Optional[str] = None
) -> Dict[str, Any]:
    """
    调用LLM进行交易决策

    Args:
        stock_code: 股票代码
        current_price: 当前价格
        change_rate: 涨跌幅
        volume: 成交量
        analysis_result: 分析结果
        current_position: 当前持仓
        strategy_id: 策略ID
        news_summary: 新闻摘要

    Returns:
        交易决策
    """
    llm = get_llm_service()

    position_desc = "无持仓"
    if current_position:
        position_desc = f"""
- 持仓数量：{current_position.get('quantity', 0)}股
- 成本价：{current_position.get('avg_cost', 0):.2f}元
- 当前盈亏：{((current_price - current_position.get('avg_cost', current_price)) / current_position.get('avg_cost', current_price) * 100):.2f}%
"""

    analysis_desc = "无历史分析"
    if analysis_result:
        analysis_desc = json.dumps(analysis_result, ensure_ascii=False, indent=2)

    # 根据持仓情况调整提示词
    position_guidance = ""
    if not current_position:
        position_guidance = """
## 重要提示
当前无持仓，这是一个建仓机会。请积极考虑买入，除非有明显的利空因素。
建议买入数量：300-500股（小仓位试探）
"""
    else:
        position_guidance = """
## 重要提示
当前有持仓，请根据盈亏情况决定是否调整仓位。
"""

    prompt = f"""请根据以下信息，决定是否进行交易。

## 股票信息
- 代码：{stock_code}
- 当前价格：{current_price:.2f}元
- 今日涨跌幅：{change_rate:.2f}%
- 成交量：{volume:,.0f}

## 当前持仓
{position_desc}
{position_guidance}

## 使用策略
{strategy_id or '自动选择'}

## 历史分析结果
{analysis_desc}

## 最新新闻
{news_summary or '无最新新闻'}

## 要求
请分析并决定交易操作，返回JSON格式：
{{
    "action": "buy/sell/hold",
    "quantity": 300,
    "reason": "详细的决策理由",
    "confidence": 0.75,
    "risk_level": "low/medium/high",
    "stop_loss": 95.0,
    "take_profit": 110.0
}}

注意：
1. 数量必须是100的整数倍
2. 如果是hold，quantity为0
3. 止损止盈价格可选
"""

    system_prompt = """你是一个专业的量化交易决策系统，需要根据市场数据和分析结果做出交易决策。
决策原则：
1. 风险控制优先，避免追涨杀跌
2. 结合技术面和基本面综合判断
3. 考虑当前持仓情况，避免过度交易
4. 给出明确的止损止盈建议"""

    try:
        # 使用task_name读取前端配置
        result = await llm.call_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            task_name="trade_decision",  # 对应前端配置
            temperature=0.3,  # 交易决策需要更稳定
            max_tokens=1024,
            response_format="json"
        )

        if result["success"] and isinstance(result["data"], dict):
            decision = result["data"]
            # 确保必要字段存在
            decision.setdefault("action", "hold")
            decision.setdefault("quantity", 0)
            decision.setdefault("reason", "LLM决策")
            decision.setdefault("confidence", 0.5)
            decision.setdefault("risk_level", "medium")
            return decision
        else:
            return _get_default_trading_decision(change_rate, current_position)

    except Exception as e:
        logger.error(f"交易决策LLM调用失败: {e}")
        return _get_default_trading_decision(change_rate, current_position)


def _get_default_trading_decision(
    change_rate: float,
    current_position: Optional[Dict]
) -> Dict[str, Any]:
    """获取默认交易决策（LLM调用失败时的降级方案）"""
    # 简单的规则决策 - 更积极的策略
    if change_rate > 3:
        # 涨幅超过3%
        if current_position:
            action = "sell"
            quantity = min(current_position.get("quantity", 100), 500)
            reason = "涨幅较大，建议获利了结"
        else:
            action = "hold"
            quantity = 0
            reason = "涨幅较大，不建议追高"
    elif change_rate < -3:
        # 跌幅超过3%
        if not current_position:
            action = "buy"
            quantity = 500  # 买入500股
            reason = "跌幅较大，可能存在买入机会"
        else:
            action = "hold"
            quantity = 0
            reason = "已有持仓，建议观望"
    elif -1 <= change_rate <= 1:
        # 波动较小，适合建仓
        if not current_position:
            action = "buy"
            quantity = 300  # 小仓位试探
            reason = "市场平稳，适合小仓位建仓"
        else:
            action = "hold"
            quantity = 0
            reason = "已有持仓，继续持有"
    else:
        action = "hold"
        quantity = 0
        reason = "市场波动正常，建议继续观望"

    return {
        "action": action,
        "quantity": quantity,
        "reason": f"{reason}（规则决策，LLM服务暂时不可用）",
        "confidence": 0.5,
        "risk_level": "medium",
        "stop_loss": None,
        "take_profit": None
    }


async def call_tracking_decision_llm(
    stock_code: str,
    original_analysis: Dict,
    current_market_data: Dict,
    days_since_analysis: int
) -> Dict[str, Any]:
    """
    调用LLM进行跟踪决策

    Args:
        stock_code: 股票代码
        original_analysis: 原始分析结果
        current_market_data: 当前市场数据
        days_since_analysis: 距离分析的天数

    Returns:
        跟踪决策
    """
    llm = get_llm_service()

    prompt = f"""请根据以下信息，决定是否需要重新分析或调整策略。

## 股票代码
{stock_code}

## 原始分析结果（{days_since_analysis}天前）
{json.dumps(original_analysis, ensure_ascii=False, indent=2)}

## 当前市场数据
- 价格变化：{current_market_data.get('price_change', 0):.2f}%
- 成交量变化：{current_market_data.get('volume_change', 0):.2f}%
- 是否有重大新闻：{current_market_data.get('has_major_news', False)}
- 新闻摘要：{current_market_data.get('news_summary', '无')}

## 要求
请分析并决定下一步操作，返回JSON格式：
{{
    "decision": "hold/adjust/reanalyze/close",
    "reason": "决策理由",
    "confidence": 0.75,
    "urgency": "low/medium/high",
    "suggested_action": "具体建议"
}}

决策说明：
- hold: 继续持有观望
- adjust: 调整止损止盈或仓位
- reanalyze: 需要重新进行完整分析
- close: 建议平仓结束跟踪
"""

    system_prompt = """你是一个专业的投资跟踪系统，负责监控已分析股票的后续表现。
你需要判断：
1. 原始分析是否仍然有效
2. 市场是否发生重大变化
3. 是否需要调整策略或重新分析"""

    try:
        # 使用task_name读取前端配置
        result = await llm.call_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            task_name="market_analyzer",  # 对应前端配置
            temperature=0.4,
            max_tokens=1024,
            response_format="json"
        )

        if result["success"] and isinstance(result["data"], dict):
            return result["data"]
        else:
            return _get_default_tracking_decision(current_market_data)

    except Exception as e:
        logger.error(f"跟踪决策LLM调用失败: {e}")
        return _get_default_tracking_decision(current_market_data)


def _get_default_tracking_decision(market_data: Dict) -> Dict[str, Any]:
    """获取默认跟踪决策（LLM调用失败时的降级方案）"""
    price_change = abs(market_data.get('price_change', 0))

    if price_change > 10:
        decision = "reanalyze"
        reason = "价格变化超过10%，建议重新分析"
        urgency = "high"
    elif price_change > 5:
        decision = "adjust"
        reason = "价格变化较大，建议调整策略"
        urgency = "medium"
    else:
        decision = "hold"
        reason = "市场变化在正常范围内"
        urgency = "low"

    return {
        "decision": decision,
        "reason": f"{reason}（规则决策，LLM服务暂时不可用）",
        "confidence": 0.5,
        "urgency": urgency,
        "suggested_action": "继续监控"
    }
