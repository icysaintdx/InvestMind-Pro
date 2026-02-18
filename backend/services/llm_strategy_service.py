"""
LLM策略分析服务
负责使用大语言模型进行策略分析、信号生成和图像识别
"""

import json
import base64
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class LLMStrategyService:
    """LLM策略分析服务"""
    
    def __init__(self, model_config: Optional[Dict] = None):
        """
        初始化LLM策略服务
        
        Args:
            model_config: 模型配置，从模型管理模块获取
        """
        self.model_config = model_config
        self.llm_client = None
        
    def set_model_config(self, model_config: Dict):
        """设置模型配置"""
        self.model_config = model_config
        self._init_llm_client()
        
    def _init_llm_client(self):
        """初始化LLM客户端"""
        if not self.model_config:
            logger.warning("未配置模型，LLM功能不可用")
            return
            
        # 根据模型类型初始化不同的客户端
        model_type = self.model_config.get("type", "openai")
        
        try:
            if model_type == "openai":
                from openai import OpenAI
                self.llm_client = OpenAI(
                    api_key=self.model_config.get("api_key"),
                    base_url=self.model_config.get("base_url")
                )
            elif model_type == "deepseek":
                from openai import OpenAI
                self.llm_client = OpenAI(
                    api_key=self.model_config.get("api_key"),
                    base_url=self.model_config.get("base_url", "https://api.deepseek.com")
                )
            elif model_type == "dashscope":
                import dashscope
                dashscope.api_key = self.model_config.get("api_key")
                self.llm_client = dashscope
            else:
                logger.warning(f"不支持的模型类型: {model_type}")
        except Exception as e:
            logger.error(f"初始化LLM客户端失败: {e}")
            
    async def parse_strategy_text(self, text: str) -> Dict[str, Any]:
        """
        解析用户输入的策略文本，转换为标准策略格式
        
        Args:
            text: 用户输入的策略描述文本
            
        Returns:
            标准化的策略字典
        """
        if not self.llm_client:
            raise ValueError("LLM客户端未初始化，请先配置模型")
            
        prompt = f"""你是一个专业的量化交易策略分析师。请分析以下交易策略描述，并将其转换为标准的JSON格式。

用户输入的策略描述：
{text}

请按照以下JSON格式输出策略：
{{
    "name": "策略名称",
    "description": "策略描述",
    "category": "策略分类(technical/fundamental/institutional/folk/ai)",
    "indicators": [
        {{
            "name": "指标名称",
            "type": "指标类型(trend/momentum/volatility/oscillator/volume/valuation/growth/profitability/institutional/sentiment/flow/ai)",
            "params": {{"参数名": "参数值"}},
            "weight": 0.5,
            "description": "指标说明"
        }}
    ],
    "entry_conditions": [
        {{
            "name": "条件名称",
            "logic": "AND或OR",
            "conditions": [
                {{
                    "indicator": "指标名",
                    "operator": "比较运算符(>, <, ==, >=, <=, cross_above, cross_below, in)",
                    "value": "比较值(数值或布尔)",
                    "compare_to": "比较的另一个指标(可选)"
                }}
            ],
            "weight": 1.0,
            "description": "条件说明"
        }}
    ],
    "exit_conditions": [
        {{
            "name": "条件名称",
            "conditions": [
                {{
                    "indicator": "指标名",
                    "operator": "比较运算符",
                    "value": "比较值"
                }}
            ],
            "description": "条件说明"
        }}
    ],
    "risk_params": {{
        "stop_loss": 0.05,
        "take_profit": 0.15,
        "max_position": 0.30
    }}
}}

注意事项：
1. 仔细分析用户描述中的买入条件、卖出条件、止损止盈等信息
2. 识别所有提到的技术指标和基本面指标
3. 将模糊的描述转换为具体的数值条件
4. 如果用户没有明确指定某些参数，使用合理的默认值
5. 只输出JSON，不要有其他文字

请输出标准化的策略JSON："""

        try:
            response = await self._call_llm(prompt)
            # 解析JSON响应
            strategy = json.loads(response)
            return strategy
        except json.JSONDecodeError as e:
            logger.error(f"解析策略JSON失败: {e}")
            raise ValueError(f"策略解析失败: {e}")
        except Exception as e:
            logger.error(f"调用LLM解析策略失败: {e}")
            raise
            
    async def analyze_with_strategy(
        self,
        strategy: Dict[str, Any],
        market_data: Dict[str, Any],
        news_data: Optional[List[Dict]] = None,
        chart_image: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """
        使用策略分析市场数据，生成交易信号
        
        Args:
            strategy: 策略配置
            market_data: 市场数据（K线、指标等）
            news_data: 新闻数据（可选）
            chart_image: K线图截图（可选，用于图像分析）
            
        Returns:
            分析结果和交易信号
        """
        if not self.llm_client:
            raise ValueError("LLM客户端未初始化，请先配置模型")
            
        # 构建分析提示词
        prompt = self._build_analysis_prompt(strategy, market_data, news_data)
        
        # 如果有图像，使用多模态分析
        if chart_image:
            result = await self._analyze_with_image(prompt, chart_image)
        else:
            result = await self._call_llm(prompt)
            
        # 解析分析结果
        try:
            analysis = json.loads(result)
            return analysis
        except json.JSONDecodeError:
            # 如果不是JSON格式，尝试提取关键信息
            return self._parse_text_analysis(result)
            
    def _build_analysis_prompt(
        self,
        strategy: Dict[str, Any],
        market_data: Dict[str, Any],
        news_data: Optional[List[Dict]] = None
    ) -> str:
        """构建分析提示词"""
        
        prompt = f"""你是一个专业的量化交易分析师。请根据以下策略和市场数据进行分析，给出具体的交易建议。

## 策略信息
策略名称：{strategy.get('name', '未命名策略')}
策略描述：{strategy.get('description', '')}
策略类型：{strategy.get('category', 'technical')}

### 使用的指标
{json.dumps(strategy.get('indicators', []), ensure_ascii=False, indent=2)}

### 入场条件
{json.dumps(strategy.get('entry_conditions', []), ensure_ascii=False, indent=2)}

### 出场条件
{json.dumps(strategy.get('exit_conditions', []), ensure_ascii=False, indent=2)}

### 风险参数
{json.dumps(strategy.get('risk_params', {}), ensure_ascii=False, indent=2)}

## 市场数据
股票代码：{market_data.get('symbol', '')}
股票名称：{market_data.get('name', '')}
当前价格：{market_data.get('current_price', 0)}
今日涨跌幅：{market_data.get('change_pct', 0)}%

### K线数据（最近20日）
{json.dumps(market_data.get('kline_data', [])[-20:], ensure_ascii=False, indent=2)}

### 技术指标
{json.dumps(market_data.get('indicators', {}), ensure_ascii=False, indent=2)}

### 基本面数据
{json.dumps(market_data.get('fundamentals', {}), ensure_ascii=False, indent=2)}
"""

        if news_data:
            prompt += f"""
## 相关新闻
{json.dumps(news_data[:5], ensure_ascii=False, indent=2)}
"""

        prompt += """
## 分析要求
请根据上述策略和数据进行分析，输出以下JSON格式的结果：

{
    "signal": "BUY/SELL/HOLD",
    "confidence": 0.85,
    "analysis": {
        "technical": "技术面分析结论",
        "fundamental": "基本面分析结论（如适用）",
        "sentiment": "市场情绪分析（如适用）",
        "entry_conditions_met": ["满足的入场条件列表"],
        "exit_conditions_met": ["满足的出场条件列表"]
    },
    "trade_instruction": {
        "action": "BUY/SELL/HOLD",
        "price": 建议价格,
        "quantity_pct": 建议仓位比例(0-1),
        "stop_loss": 止损价格,
        "take_profit": 止盈价格,
        "reason": "交易理由"
    },
    "risk_assessment": {
        "level": "LOW/MEDIUM/HIGH",
        "factors": ["风险因素列表"],
        "suggestions": ["风险控制建议"]
    },
    "key_levels": {
        "support": [支撑位列表],
        "resistance": [阻力位列表]
    }
}

请只输出JSON，不要有其他文字。"""

        return prompt
        
    async def _analyze_with_image(self, prompt: str, image_data: bytes) -> str:
        """使用图像进行多模态分析"""
        
        if not self.model_config:
            raise ValueError("模型未配置")
            
        model_type = self.model_config.get("type", "openai")
        model_name = self.model_config.get("model", "gpt-4-vision-preview")
        
        # 将图像转换为base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        enhanced_prompt = f"""{prompt}

## K线图分析
请同时分析附带的K线图截图，识别以下内容：
1. 图表形态（如双底、头肩顶、三角形等）
2. 趋势方向和强度
3. 关键支撑位和阻力位
4. 成交量特征
5. 指标信号（如MACD、RSI等）

将图表分析结果整合到上述JSON输出中。"""

        try:
            if model_type in ["openai", "deepseek"]:
                response = self.llm_client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": enhanced_prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{image_base64}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=4096
                )
                return response.choices[0].message.content
            elif model_type == "dashscope":
                from dashscope import MultiModalConversation
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"text": enhanced_prompt},
                            {"image": f"data:image/png;base64,{image_base64}"}
                        ]
                    }
                ]
                response = MultiModalConversation.call(
                    model=model_name,
                    messages=messages
                )
                return response.output.choices[0].message.content[0]["text"]
            else:
                raise ValueError(f"不支持的模型类型: {model_type}")
        except Exception as e:
            logger.error(f"图像分析失败: {e}")
            raise
            
    async def _call_llm(self, prompt: str) -> str:
        """调用LLM"""
        
        if not self.model_config:
            raise ValueError("模型未配置")
            
        model_type = self.model_config.get("type", "openai")
        model_name = self.model_config.get("model", "gpt-4")
        
        try:
            if model_type in ["openai", "deepseek"]:
                response = self.llm_client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "你是一个专业的量化交易分析师，擅长技术分析和策略制定。"},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=4096,
                    temperature=0.3
                )
                return response.choices[0].message.content
            elif model_type == "dashscope":
                from dashscope import Generation
                response = Generation.call(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "你是一个专业的量化交易分析师，擅长技术分析和策略制定。"},
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.output.text
            else:
                raise ValueError(f"不支持的模型类型: {model_type}")
        except Exception as e:
            logger.error(f"调用LLM失败: {e}")
            raise
            
    def _parse_text_analysis(self, text: str) -> Dict[str, Any]:
        """解析文本格式的分析结果"""
        
        # 尝试从文本中提取关键信息
        result = {
            "signal": "HOLD",
            "confidence": 0.5,
            "analysis": {
                "technical": text,
                "fundamental": "",
                "sentiment": ""
            },
            "trade_instruction": {
                "action": "HOLD",
                "reason": "无法解析详细分析结果"
            },
            "risk_assessment": {
                "level": "MEDIUM",
                "factors": [],
                "suggestions": []
            }
        }
        
        # 简单的关键词匹配
        text_lower = text.lower()
        if "买入" in text or "buy" in text_lower:
            result["signal"] = "BUY"
            result["trade_instruction"]["action"] = "BUY"
        elif "卖出" in text or "sell" in text_lower:
            result["signal"] = "SELL"
            result["trade_instruction"]["action"] = "SELL"
            
        return result
        
    async def generate_trade_signal(
        self,
        strategy_id: int,
        symbol: str,
        market_data: Dict[str, Any],
        news_data: Optional[List[Dict]] = None,
        chart_image: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """
        生成交易信号
        
        Args:
            strategy_id: 策略ID
            symbol: 股票代码
            market_data: 市场数据
            news_data: 新闻数据
            chart_image: K线图截图
            
        Returns:
            交易信号
        """
        # 这里需要从数据库获取策略
        # 暂时使用传入的market_data中的strategy
        strategy = market_data.get("strategy", {})
        
        if not strategy:
            raise ValueError(f"未找到策略ID: {strategy_id}")
            
        # 执行分析
        analysis = await self.analyze_with_strategy(
            strategy=strategy,
            market_data=market_data,
            news_data=news_data,
            chart_image=chart_image
        )
        
        # 构建交易信号
        signal = {
            "strategy_id": strategy_id,
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "signal": analysis.get("signal", "HOLD"),
            "confidence": analysis.get("confidence", 0.5),
            "trade_instruction": analysis.get("trade_instruction", {}),
            "analysis": analysis.get("analysis", {}),
            "risk_assessment": analysis.get("risk_assessment", {}),
            "key_levels": analysis.get("key_levels", {})
        }
        
        return signal


# 创建全局实例
llm_strategy_service = LLMStrategyService()


def get_llm_strategy_service() -> LLMStrategyService:
    """获取LLM策略服务实例"""
    return llm_strategy_service