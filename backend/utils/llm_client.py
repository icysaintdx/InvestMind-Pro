"""
统一LLM客户端
为所有智能体提供统一的语言模型调用接口
支持多种后端：Gemini、DeepSeek、通义千问、SiliconFlow
"""

import os
import httpx
import json
from typing import Dict, Any, Optional, List, AsyncGenerator
from enum import Enum
from backend.utils.logging_config import get_logger
from backend.utils.tool_logging import log_tool_call
import asyncio

logger = get_logger("llm_client")

class LLMProvider(Enum):
    """LLM提供商"""
    GEMINI = "gemini"
    DEEPSEEK = "deepseek"
    QWEN = "qwen"
    SILICONFLOW = "siliconflow"
    LOCAL = "local"  # 预留本地模型接口

class LLMConfig:
    """LLM配置"""
    def __init__(self, 
                 provider: LLMProvider = LLMProvider.DEEPSEEK,
                 model: str = "deepseek-chat",
                 temperature: float = 0.7,
                 max_tokens: int = 4000,
                 api_key: Optional[str] = None):
        self.provider = provider
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.api_key = api_key or self._get_api_key(provider)
        
    def _get_api_key(self, provider: LLMProvider) -> str:
        """获取API密钥"""
        key_map = {
            LLMProvider.GEMINI: "GEMINI_API_KEY",
            LLMProvider.DEEPSEEK: "DEEPSEEK_API_KEY",
            LLMProvider.QWEN: "DASHSCOPE_API_KEY",
            LLMProvider.SILICONFLOW: "SILICONFLOW_API_KEY"
        }
        return os.getenv(key_map.get(provider, ""), "")

class UnifiedLLMClient:
    """统一LLM客户端"""
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """
        初始化LLM客户端
        Args:
            config: LLM配置，如果为None则使用默认配置
        """
        self.config = config or LLMConfig()
        self.base_url = "http://localhost:8000"  # 使用本地FastAPI服务器
        self._client = None
        
    @property
    def client(self):
        """获取HTTP客户端（懒加载）"""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=180.0)
        return self._client
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self._client:
            await self._client.aclose()
            
    @log_tool_call("LLM调用")
    async def generate(self, 
                       prompt: str,
                       system_prompt: str = "",
                       temperature: Optional[float] = None,
                       max_tokens: Optional[int] = None) -> str:
        """
        生成文本响应
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            temperature: 温度参数（可选，覆盖配置）
            max_tokens: 最大token数（可选，覆盖配置）
            
        Returns:
            生成的文本
        """
        temperature = temperature or self.config.temperature
        max_tokens = max_tokens or self.config.max_tokens
        
        try:
            # 根据provider选择API端点
            endpoint = self._get_endpoint()
            
            # 构建请求数据
            if self.config.provider == LLMProvider.GEMINI:
                data = {
                    "model": self.config.model,
                    "prompt": prompt,
                    "temperature": temperature,
                    "apiKey": self.config.api_key
                }
            else:
                data = {
                    "model": self.config.model,
                    "systemPrompt": system_prompt,
                    "prompt": prompt,
                    "temperature": temperature,
                    "apiKey": self.config.api_key
                }
                
            # 发送请求
            response = await self.client.post(
                f"{self.base_url}{endpoint}",
                json=data
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get("success"):
                return result.get("text", "")
            else:
                error_msg = result.get("error", "未知错误")
                logger.error(f"LLM调用失败: {error_msg}")
                return f"错误: {error_msg}"
                
        except Exception as e:
            logger.error(f"LLM调用异常: {str(e)}", exc_info=True)
            return f"调用失败: {str(e)}"
            
    def _get_endpoint(self) -> str:
        """获取API端点"""
        endpoint_map = {
            LLMProvider.GEMINI: "/api/ai/gemini",
            LLMProvider.DEEPSEEK: "/api/ai/deepseek",
            LLMProvider.QWEN: "/api/ai/qwen",
            LLMProvider.SILICONFLOW: "/api/ai/siliconflow"
        }
        return endpoint_map.get(self.config.provider, "/api/ai/siliconflow")
        
    async def generate_with_tools(self,
                                  prompt: str,
                                  tools: List[Dict[str, Any]],
                                  system_prompt: str = "") -> Dict[str, Any]:
        """
        生成带工具调用的响应（用于函数调用场景）
        
        Args:
            prompt: 用户提示词
            tools: 工具定义列表
            system_prompt: 系统提示词
            
        Returns:
            包含文本和工具调用的响应
        """
        # TODO: 实现工具调用逻辑
        # 目前先返回普通文本响应
        text = await self.generate(prompt, system_prompt)
        return {"text": text, "tool_calls": []}
        
    async def stream_generate(self,
                             prompt: str,
                             system_prompt: str = "",
                             temperature: Optional[float] = None) -> AsyncGenerator[str, None]:
        """
        流式生成文本响应
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            temperature: 温度参数
            
        Yields:
            生成的文本片段
        """
        # TODO: 实现流式响应
        # 目前先返回完整响应
        result = await self.generate(prompt, system_prompt, temperature)
        yield result


class AgentLLM:
    """
    为智能体提供的LLM接口适配器
    兼容原TradingAgents-CN的接口
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self.client = UnifiedLLMClient(config)
        
    def bind_tools(self, tools: List[Any]) -> "AgentLLM":
        """绑定工具（兼容接口）"""
        self.tools = tools
        return self
        
    async def ainvoke(self, messages: List[Dict[str, str]]) -> Any:
        """异步调用（兼容接口）"""
        # 将输入转换为prompt，兼容字符串和消息列表两种形式
        system_prompt = ""
        user_prompt = ""

        if isinstance(messages, str):
            user_prompt = messages
        else:
            for msg in messages:
                if isinstance(msg, dict):
                    role = msg.get("role")
                    content = msg.get("content", "")
                else:
                    role = getattr(msg, "role", "user")
                    content = getattr(msg, "content", str(msg))

                if role == "system":
                    system_prompt = content
                elif role == "user":
                    user_prompt = content
                
        response = await self.client.generate(user_prompt, system_prompt)
        
        # 模拟原接口的返回格式
        class MockResponse:
            def __init__(self, content):
                self.content = content
                self.tool_calls = []
                
        return MockResponse(response)
        
    def invoke(self, messages: List[Dict[str, str]]) -> Any:
        """同步调用（兼容接口）"""
        # 在同步环境中运行异步代码
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        return loop.run_until_complete(self.ainvoke(messages))


# 工厂函数
def create_llm_client(provider: str = "deepseek",
                     model: Optional[str] = None,
                     temperature: float = 0.7) -> UnifiedLLMClient:
    """
    创建LLM客户端
    
    Args:
        provider: 提供商名称
        model: 模型名称
        temperature: 温度参数
        
    Returns:
        LLM客户端实例
    """
    # 默认模型映射
    default_models = {
        "gemini": "gemini-2.0-flash-exp",
        "deepseek": "deepseek-chat",
        "qwen": "qwen-plus",
        "siliconflow": "Qwen/Qwen2.5-7B-Instruct"
    }
    
    try:
        provider_enum = LLMProvider(provider.lower())
    except ValueError:
        logger.warning(f"未知的provider: {provider}，使用默认DeepSeek")
        provider_enum = LLMProvider.DEEPSEEK
        
    model = model or default_models.get(provider_enum.value, "deepseek-chat")
    
    config = LLMConfig(
        provider=provider_enum,
        model=model,
        temperature=temperature
    )
    
    return UnifiedLLMClient(config)


def create_agent_llm(provider: str = "deepseek",
                    model: Optional[str] = None,
                    temperature: float = 0.3) -> AgentLLM:
    """
    创建智能体专用的LLM适配器
    
    Args:
        provider: 提供商名称
        model: 模型名称
        temperature: 温度参数（默认0.3，更适合分析任务）
        
    Returns:
        AgentLLM实例
    """
    # 智能体默认使用较低的temperature
    config = LLMConfig(
        provider=LLMProvider(provider.lower()) if provider else LLMProvider.DEEPSEEK,
        model=model or "deepseek-chat",
        temperature=temperature
    )
    
    return AgentLLM(config)


# 单例模式的全局客户端
_global_client: Optional[UnifiedLLMClient] = None

def get_global_llm_client() -> UnifiedLLMClient:
    """获取全局LLM客户端（单例）"""
    global _global_client
    if _global_client is None:
        _global_client = create_llm_client()
    return _global_client


# 导出
__all__ = [
    "LLMProvider",
    "LLMConfig",
    "UnifiedLLMClient",
    "AgentLLM",
    "create_llm_client",
    "create_agent_llm",
    "get_global_llm_client"
]
