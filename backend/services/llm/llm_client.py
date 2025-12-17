"""
LLM客户端
支持多种LLM模型：GPT-4, DeepSeek, Qwen等
"""

import os
import json
import asyncio
from typing import Dict, Any, Optional, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """LLM提供商"""
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    QWEN = "qwen"
    OLLAMA = "ollama"  # 本地模型


class LLMClient:
    """LLM客户端"""
    
    def __init__(
        self,
        provider: str = "ollama",
        model: str = "qwen2.5:latest",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """
        初始化LLM客户端
        
        Args:
            provider: LLM提供商 (openai/deepseek/qwen/ollama)
            model: 模型名称
            api_key: API密钥（如需要）
            base_url: API基础URL（如需要）
        """
        self.provider = provider
        self.model = model
        self.api_key = api_key or os.getenv(f"{provider.upper()}_API_KEY")
        self.base_url = base_url or os.getenv(f"{provider.upper()}_BASE_URL")
        
        # 根据提供商初始化客户端
        self._init_client()
    
    def _init_client(self):
        """初始化具体的客户端"""
        if self.provider == "openai":
            self._init_openai()
        elif self.provider == "deepseek":
            self._init_deepseek()
        elif self.provider == "qwen":
            self._init_qwen()
        elif self.provider == "ollama":
            self._init_ollama()
        else:
            raise ValueError(f"不支持的LLM提供商: {self.provider}")
    
    def _init_openai(self):
        """初始化OpenAI客户端"""
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            logger.info(f"OpenAI客户端初始化成功，模型: {self.model}")
        except ImportError:
            logger.warning("OpenAI库未安装，请运行: pip install openai")
            self.client = None
    
    def _init_deepseek(self):
        """初始化DeepSeek客户端"""
        try:
            from openai import AsyncOpenAI
            # DeepSeek使用OpenAI兼容接口
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url or "https://api.deepseek.com/v1"
            )
            logger.info(f"DeepSeek客户端初始化成功，模型: {self.model}")
        except ImportError:
            logger.warning("OpenAI库未安装，请运行: pip install openai")
            self.client = None
    
    def _init_qwen(self):
        """初始化通义千问客户端"""
        try:
            import dashscope
            dashscope.api_key = self.api_key
            self.client = dashscope
            logger.info(f"通义千问客户端初始化成功，模型: {self.model}")
        except ImportError:
            logger.warning("DashScope库未安装，请运行: pip install dashscope")
            self.client = None
    
    def _init_ollama(self):
        """初始化Ollama客户端（本地模型）"""
        try:
            import httpx
            self.client = httpx.AsyncClient(
                base_url=self.base_url or "http://localhost:11434"
            )
            logger.info(f"Ollama客户端初始化成功，模型: {self.model}")
        except ImportError:
            logger.warning("httpx库未安装，请运行: pip install httpx")
            self.client = None
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        format: str = "text"
    ) -> str:
        """
        生成文本
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            temperature: 温度参数
            max_tokens: 最大token数
            format: 输出格式 (text/json)
            
        Returns:
            生成的文本
        """
        if self.client is None:
            raise RuntimeError(f"{self.provider}客户端未初始化")
        
        try:
            if self.provider in ["openai", "deepseek"]:
                return await self._generate_openai_compatible(
                    prompt, system_prompt, temperature, max_tokens, format
                )
            elif self.provider == "qwen":
                return await self._generate_qwen(
                    prompt, system_prompt, temperature, max_tokens
                )
            elif self.provider == "ollama":
                return await self._generate_ollama(
                    prompt, system_prompt, temperature, max_tokens, format
                )
        except Exception as e:
            logger.error(f"LLM生成失败: {e}")
            raise
    
    async def _generate_openai_compatible(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
        format: str
    ) -> str:
        """OpenAI兼容接口生成"""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # 如果需要JSON格式
        if format == "json":
            kwargs["response_format"] = {"type": "json_object"}
        
        response = await self.client.chat.completions.create(**kwargs)
        
        return response.choices[0].message.content
    
    async def _generate_qwen(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> str:
        """通义千问生成"""
        from dashscope import Generation
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = Generation.call(
            model=self.model,
            messages=messages,
            result_format='message',
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        if response.status_code == 200:
            return response.output.choices[0].message.content
        else:
            raise RuntimeError(f"通义千问调用失败: {response.message}")
    
    async def _generate_ollama(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
        format: str
    ) -> str:
        """Ollama本地模型生成"""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        # 如果需要JSON格式
        if format == "json":
            payload["format"] = "json"
        
        response = await self.client.post("/api/chat", json=payload)
        response.raise_for_status()
        
        result = response.json()
        return result["message"]["content"]


# 全局LLM客户端实例
_llm_client_instance = None


def get_llm_client(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    task_name: Optional[str] = None
) -> LLMClient:
    """
    获取LLM客户端单例
    
    Args:
        provider: LLM提供商（可选）
        model: 模型名称（可选）
        task_name: 任务名称（可选，优先从配置文件读取）
        
    Returns:
        LLM客户端实例
    """
    global _llm_client_instance
    
    if _llm_client_instance is None:
        # 优先从配置管理器读取
        if task_name:
            try:
                from backend.services.llm.llm_config_manager import get_llm_config_manager
                manager = get_llm_config_manager()
                params = manager.get_llm_client_params(task_name)
                provider = params.get("provider")
                model = params.get("model")
                logger.info(f"使用任务 {task_name} 的配置: {provider}/{model}")
            except Exception as e:
                logger.warning(f"从配置管理器读取失败: {e}")
        
        # 如果没有指定，从环境变量读取
        if not provider:
            provider = provider or os.getenv("LLM_PROVIDER", "ollama")
        if not model:
            model = model or os.getenv("LLM_MODEL", "qwen2.5:latest")
        
        _llm_client_instance = LLMClient(provider=provider, model=model)
    
    return _llm_client_instance


def get_llm_client_for_task(task_name: str) -> LLMClient:
    """
    为特定任务获取LLM客户端
    
    Args:
        task_name: 任务名称（如 strategy_selection, text_summarization）
        
    Returns:
        配置好的LLM客户端
    """
    try:
        from backend.services.llm.llm_config_manager import get_llm_config_manager
        manager = get_llm_config_manager()
        params = manager.get_llm_client_params(task_name)
        
        return LLMClient(
            provider=params["provider"],
            model=params["model"]
        )
    except Exception as e:
        logger.error(f"为任务 {task_name} 创建 LLM 客户端失败: {e}")
        # 降级为默认配置
        return get_llm_client()


async def test_llm_client():
    """测试LLM客户端"""
    print("=" * 60)
    print("LLM客户端测试")
    print("=" * 60)
    
    # 测试Ollama（本地模型）
    print("\n【测试1】Ollama本地模型")
    try:
        client = LLMClient(provider="ollama", model="qwen2.5:latest")
        
        prompt = "请用一句话介绍什么是量化交易策略。"
        response = await client.generate(prompt, temperature=0.7)
        
        print(f"✅ Ollama调用成功")
        print(f"   提示词: {prompt}")
        print(f"   响应: {response[:100]}...")
    except Exception as e:
        print(f"❌ Ollama调用失败: {e}")
    
    # 测试JSON格式输出
    print("\n【测试2】JSON格式输出")
    try:
        client = get_llm_client()
        
        prompt = """
请分析以下股票情况并以JSON格式返回：
- 股票代码：600519
- 当前价格：1650元
- 趋势：上涨
- 风险等级：中等

返回格式：
{
  "recommendation": "买入/持有/卖出",
  "confidence": 0.8,
  "reason": "分析理由"
}
"""
        
        response = await client.generate(prompt, format="json", temperature=0.3)
        
        print(f"✅ JSON格式输出成功")
        print(f"   响应: {response[:200]}...")
        
        # 尝试解析JSON
        try:
            data = json.loads(response)
            print(f"   解析成功: {list(data.keys())}")
        except:
            print(f"   ⚠️ JSON解析失败，但生成成功")
            
    except Exception as e:
        print(f"❌ JSON格式测试失败: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_llm_client())
