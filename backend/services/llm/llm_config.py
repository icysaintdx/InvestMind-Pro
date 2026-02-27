"""
统一LLM配置模块

提供统一的LLM客户端配置和接口，确保整个系统使用一致的模型和参数。
"""
from typing import Dict, Any, Optional
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)

# 默认配置
DEFAULT_LLM_CONFIG = {
    "base_url": "https://kirocpa.zeabur.app/v1",
    "api_key": "icysaintdx",
    "default_model": "kimi-k2.5",
    "fallback_model": "minimax-m2.1",
    "temperature": 0.3,
    "max_tokens": 800,
    "timeout": 30
}

# 模型特定配置
MODEL_CONFIGS = {
    "kimi-k2.5": {
        "temperature": 0.3,
        "max_tokens": 800,
    },
    "minimax-m2.1": {
        "temperature": 0.3,
        "max_tokens": 800,
    }
}


class LLMClient:
    """
    统一LLM客户端
    
    使用方法:
        client = LLMClient()
        response = client.chat([
            {"role": "system", "content": "你是金融分析师"},
            {"role": "user", "content": "分析这条新闻"}
        ])
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化LLM客户端
        
        Args:
            config: 自定义配置，会覆盖默认配置
        """
        self.config = {**DEFAULT_LLM_CONFIG, **(config or {})}
        self.client = OpenAI(
            api_key=self.config["api_key"],
            base_url=self.config["base_url"],
            timeout=self.config.get("timeout", 30)
        )
        self._fallback_used = False
    
    def chat(self, 
             messages: list, 
             model: str = None, 
             temperature: float = None,
             max_tokens: int = None,
             **kwargs) -> str:
        """
        统一聊天接口
        
        Args:
            messages: 消息列表
            model: 模型名称，默认使用配置中的default_model
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数
            
        Returns:
            LLM响应文本
            
        Raises:
            Exception: 当主要模型和fallback模型都失败时
        """
        model = model or self.config["default_model"]
        model_config = MODEL_CONFIGS.get(model, {})
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature or model_config.get("temperature", self.config["temperature"]),
                max_tokens=max_tokens or model_config.get("max_tokens", self.config["max_tokens"]),
                **kwargs
            )
            content = response.choices[0].message.content
            self._fallback_used = False
            return content
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # 检查是否是余额不足或配额限制
            if any(keyword in error_msg for keyword in ["balance", "insufficient", "quota", "30001"]):
                logger.warning(f"模型 {model} 余额不足或配额限制，尝试fallback模型")
                
                # 尝试fallback模型
                if model != self.config["fallback_model"]:
                    logger.info(f"降级到fallback模型: {self.config['fallback_model']}")
                    self._fallback_used = True
                    return self.chat(
                        messages, 
                        model=self.config["fallback_model"],
                        temperature=temperature,
                        max_tokens=max_tokens,
                        **kwargs
                    )
            
            # 其他错误或fallback也失败
            logger.error(f"LLM调用失败: {e}")
            raise
    
    def chat_with_json(self,
                       messages: list,
                       model: str = None,
                       **kwargs) -> Dict[str, Any]:
        """
        聊天接口，返回JSON格式响应
        
        Args:
            messages: 消息列表
            model: 模型名称
            **kwargs: 其他参数
            
        Returns:
            解析后的JSON字典
        """
        import json
        import re
        
        response = self.chat(messages, model=model, **kwargs)
        
        # 尝试直接解析JSON
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # 尝试从代码块中提取JSON
        json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # 尝试从文本中提取JSON对象
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        # 无法解析，返回原始文本包装
        logger.warning(f"无法解析JSON响应，返回原始文本: {response[:200]}")
        return {"raw_text": response, "parse_error": True}
    
    def is_fallback_used(self) -> bool:
        """检查上一次调用是否使用了fallback模型"""
        return self._fallback_used
    
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return self.config.copy()


# 全局客户端实例（单例模式）
_global_client: Optional[LLMClient] = None


def get_llm_client(config: Dict[str, Any] = None) -> LLMClient:
    """
    获取全局LLM客户端实例
    
    Args:
        config: 自定义配置
        
    Returns:
        LLMClient实例
    """
    global _global_client
    if _global_client is None or config:
        _global_client = LLMClient(config)
    return _global_client


def reset_llm_client():
    """重置全局客户端实例"""
    global _global_client
    _global_client = None
