"""
动态LLM客户端
根据数据库中配置的提供商动态路由LLM请求，失败自动切换
"""

import time
import asyncio
from typing import Dict, Any, Optional, List

import httpx

from backend.utils.logging_config import get_logger

logger = get_logger("services.llm.dynamic")

# 提供商列表缓存（避免每次请求都查数据库）
_providers_cache: Optional[List[Dict[str, Any]]] = None
_cache_time: float = 0
_CACHE_TTL = 60  # 缓存60秒


def _get_enabled_providers() -> List[Dict[str, Any]]:
    """获取已启用的提供商列表（带缓存）"""
    global _providers_cache, _cache_time

    now = time.time()
    if _providers_cache is not None and (now - _cache_time) < _CACHE_TTL:
        return _providers_cache

    try:
        from backend.services.api_provider_service import list_providers
        _providers_cache = list_providers(enabled_only=True)
        _cache_time = now
        return _providers_cache
    except Exception as e:
        logger.error(f"加载提供商列表失败: {e}")
        return _providers_cache or []


def invalidate_cache():
    """手动失效缓存（提供商配置变更时调用）"""
    global _providers_cache, _cache_time
    _providers_cache = None
    _cache_time = 0


def _find_provider_for_model(model: str, providers: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """查找包含指定模型的提供商"""
    for p in providers:
        if model in p.get("models", []):
            return p
    return None


class DynamicLLMClient:
    """
    动态LLM客户端

    根据数据库中配置的提供商动态路由请求。
    支持 OpenAI兼容 / Anthropic / Google 三种SDK类型。
    请求失败时自动切换到下一个可用提供商。
    """

    def __init__(self, timeout: float = 120.0):
        self.timeout = httpx.Timeout(
            timeout=timeout,
            connect=15.0,
            read=timeout,
            write=15.0,
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: str = "你是一个专业的AI助手。",
        model: Optional[str] = None,
        provider_id: Optional[int] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """
        发送LLM请求，支持动态路由和故障切换

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            model: 指定模型（可选，会自动匹配提供商）
            provider_id: 指定提供商ID（可选，最高优先级）
            temperature: 温度参数
            max_tokens: 最大token数
            max_retries: 最大尝试提供商数

        Returns:
            {"success": True, "text": "...", "provider": "...", "model": "...", "latency_ms": ...}
        """
        providers = _get_enabled_providers()
        if not providers:
            return {"success": False, "error": "没有可用的API提供商，请先在设置中添加"}

        # 构建尝试顺序
        ordered = self._build_provider_order(providers, provider_id, model)
        if not ordered:
            return {"success": False, "error": f"未找到支持模型 {model} 的提供商"}

        last_error = ""
        for i, (provider, use_model) in enumerate(ordered[:max_retries]):
            try:
                logger.info(f"尝试提供商 [{provider['name']}] 模型 [{use_model}] ({i+1}/{min(len(ordered), max_retries)})")
                result = await self._call_provider(
                    provider, use_model, prompt, system_prompt, temperature, max_tokens
                )
                if result["success"]:
                    return result
                last_error = result.get("error", "未知错误")
                logger.warning(f"提供商 [{provider['name']}] 失败: {last_error}")
            except Exception as e:
                last_error = f"{type(e).__name__}: {str(e)}"
                logger.warning(f"提供商 [{provider['name']}] 异常: {last_error}")

        return {"success": False, "error": f"所有提供商均失败，最后错误: {last_error}"}

    def _build_provider_order(
        self,
        providers: List[Dict[str, Any]],
        provider_id: Optional[int],
        model: Optional[str],
    ) -> List[tuple]:
        """
        构建提供商尝试顺序

        Returns:
            [(provider_dict, model_to_use), ...]
        """
        result = []

        # 1. 如果指定了 provider_id，优先使用
        if provider_id:
            for p in providers:
                if p["id"] == provider_id:
                    use_model = model or (p["models"][0] if p.get("models") else None)
                    if use_model:
                        result.append((p, use_model))
                    break

        # 2. 如果指定了 model，查找包含该模型的提供商
        if model:
            for p in providers:
                if model in p.get("models", []) and (p, model) not in result:
                    result.append((p, model))

        # 3. 按优先级添加剩余提供商（使用其第一个模型）
        for p in providers:
            if p.get("models"):
                entry = (p, p["models"][0])
                if entry not in result:
                    result.append(entry)

        return result

    async def _call_provider(
        self,
        provider: Dict[str, Any],
        model: str,
        prompt: str,
        system_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> Dict[str, Any]:
        """调用单个提供商"""
        sdk_type = provider.get("sdk_type", "openai")
        base_url = provider["base_url"].rstrip("/")
        api_key = provider["api_key"]

        start_time = time.time()

        if sdk_type == "openai":
            return await self._call_openai_compatible(
                base_url, api_key, model, prompt, system_prompt, temperature, max_tokens, provider["name"], start_time
            )
        elif sdk_type == "anthropic":
            return await self._call_anthropic(
                base_url, api_key, model, prompt, system_prompt, temperature, max_tokens, provider["name"], start_time
            )
        elif sdk_type == "google":
            return await self._call_google(
                base_url, api_key, model, prompt, system_prompt, temperature, max_tokens, provider["name"], start_time
            )
        else:
            return {"success": False, "error": f"不支持的SDK类型: {sdk_type}"}

    async def _call_openai_compatible(
        self, base_url: str, api_key: str, model: str,
        prompt: str, system_prompt: str, temperature: float, max_tokens: int,
        provider_name: str, start_time: float,
    ) -> Dict[str, Any]:
        """调用 OpenAI 兼容 API"""
        if base_url.endswith("/v1"):
            url = f"{base_url}/chat/completions"
        else:
            url = f"{base_url}/v1/chat/completions"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": False,
                },
            )

        latency_ms = int((time.time() - start_time) * 1000)

        if response.status_code != 200:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text[:200]}", "latency_ms": latency_ms}

        result = response.json()
        text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        usage = result.get("usage", {})

        return {
            "success": True,
            "text": text,
            "provider": provider_name,
            "model": model,
            "usage": usage,
            "latency_ms": latency_ms,
        }

    async def _call_anthropic(
        self, base_url: str, api_key: str, model: str,
        prompt: str, system_prompt: str, temperature: float, max_tokens: int,
        provider_name: str, start_time: float,
    ) -> Dict[str, Any]:
        """调用 Anthropic API"""
        url = f"{base_url}/v1/messages" if not base_url.endswith("/v1") else f"{base_url}/messages"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url,
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "system": system_prompt,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )

        latency_ms = int((time.time() - start_time) * 1000)

        if response.status_code != 200:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text[:200]}", "latency_ms": latency_ms}

        result = response.json()
        text = ""
        for block in result.get("content", []):
            if block.get("type") == "text":
                text += block.get("text", "")

        usage = result.get("usage", {})

        return {
            "success": True,
            "text": text,
            "provider": provider_name,
            "model": model,
            "usage": usage,
            "latency_ms": latency_ms,
        }

    async def _call_google(
        self, base_url: str, api_key: str, model: str,
        prompt: str, system_prompt: str, temperature: float, max_tokens: int,
        provider_name: str, start_time: float,
    ) -> Dict[str, Any]:
        """调用 Google Gemini API（OpenAI兼容模式）"""
        url = f"{base_url}/v1beta/openai/chat/completions"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )

        latency_ms = int((time.time() - start_time) * 1000)

        if response.status_code != 200:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text[:200]}", "latency_ms": latency_ms}

        result = response.json()
        text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        usage = result.get("usage", {})

        return {
            "success": True,
            "text": text,
            "provider": provider_name,
            "model": model,
            "usage": usage,
            "latency_ms": latency_ms,
        }


# ==================== 全局单例 ====================

_dynamic_client: Optional[DynamicLLMClient] = None


def get_dynamic_llm_client() -> DynamicLLMClient:
    """获取动态LLM客户端单例"""
    global _dynamic_client
    if _dynamic_client is None:
        _dynamic_client = DynamicLLMClient()
    return _dynamic_client
