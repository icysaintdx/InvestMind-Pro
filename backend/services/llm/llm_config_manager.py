"""
LLM配置管理器
统一管理所有LLM调用的配置，类似智能体配置
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class LLMConfigManager:
    """LLM配置管理器"""
    
    def __init__(self):
        self.config_path = Path(__file__).parent.parent.parent / "agent_configs" / "llm_configs.json"
        self.config = self._load_config()
        logger.info("LLM配置管理器初始化完成")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"LLM配置加载成功，版本: {config.get('version')}")
            return config
        except Exception as e:
            logger.error(f"加载LLM配置失败: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "version": "1.0.0",
            "default_provider": "ollama",
            "default_model": "qwen2.5:latest",
            "providers": {},
            "llm_tasks": {},
            "fallback_config": {"enabled": False},
            "monitoring": {"log_requests": True}
        }
    
    def reload_config(self):
        """重新加载配置"""
        self.config = self._load_config()
        logger.info("LLM配置已重新加载")
    
    def get_task_config(self, task_name: str) -> Optional[Dict[str, Any]]:
        """
        获取特定任务的LLM配置
        
        Args:
            task_name: 任务名称（如 strategy_selection, text_summarization）
            
        Returns:
            任务配置字典，如果任务未启用或不存在返回None
        """
        tasks = self.config.get("llm_tasks", {})
        task_config = tasks.get(task_name)
        
        if task_config is None:
            logger.warning(f"任务 {task_name} 配置不存在")
            return None
        
        if not task_config.get("enabled", True):
            logger.warning(f"任务 {task_name} 已禁用")
            return None
        
        return task_config
    
    def get_provider_config(self, provider_name: str) -> Optional[Dict[str, Any]]:
        """
        获取提供商配置
        
        Args:
            provider_name: 提供商名称（如 ollama, openai）
            
        Returns:
            提供商配置字典
        """
        providers = self.config.get("providers", {})
        return providers.get(provider_name)
    
    def get_llm_client_params(self, task_name: str) -> Dict[str, Any]:
        """
        获取LLM客户端初始化参数
        
        Args:
            task_name: 任务名称
            
        Returns:
            客户端参数字典
        """
        task_config = self.get_task_config(task_name)
        
        if task_config is None:
            # 使用默认配置
            return {
                "provider": self.config.get("default_provider", "ollama"),
                "model": self.config.get("default_model", "qwen2.5:latest"),
                "temperature": 0.7,
                "max_tokens": 2000,
                "timeout": 30
            }
        
        provider = task_config.get("provider", self.config.get("default_provider"))
        model = task_config.get("model")
        
        # 如果任务没有指定模型，使用提供商的默认模型
        if not model:
            provider_config = self.get_provider_config(provider)
            if provider_config:
                model = provider_config.get("default_model")
        
        return {
            "provider": provider,
            "model": model,
            "temperature": task_config.get("temperature", 0.7),
            "max_tokens": task_config.get("max_tokens", 2000),
            "timeout": task_config.get("timeout", 30),
            "format": task_config.get("format", "text"),
            "retry_times": task_config.get("retry_times", 2)
        }
    
    def get_fallback_config(self) -> Dict[str, Any]:
        """获取降级配置"""
        return self.config.get("fallback_config", {})
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """获取监控配置"""
        return self.config.get("monitoring", {})
    
    def is_task_enabled(self, task_name: str) -> bool:
        """检查任务是否启用"""
        task_config = self.config.get("llm_tasks", {}).get(task_name)
        if task_config is None:
            return False
        return task_config.get("enabled", True)
    
    def get_all_tasks(self) -> Dict[str, Dict[str, Any]]:
        """获取所有任务配置"""
        return self.config.get("llm_tasks", {})
    
    def get_all_providers(self) -> Dict[str, Dict[str, Any]]:
        """获取所有提供商配置"""
        return self.config.get("providers", {})
    
    def update_task_config(
        self,
        task_name: str,
        updates: Dict[str, Any],
        save: bool = True
    ):
        """
        更新任务配置
        
        Args:
            task_name: 任务名称
            updates: 要更新的配置项
            save: 是否保存到文件
        """
        if "llm_tasks" not in self.config:
            self.config["llm_tasks"] = {}
        
        if task_name not in self.config["llm_tasks"]:
            self.config["llm_tasks"][task_name] = {}
        
        self.config["llm_tasks"][task_name].update(updates)
        
        if save:
            self._save_config()
        
        logger.info(f"任务 {task_name} 配置已更新")
    
    def _save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            logger.info("LLM配置已保存")
        except Exception as e:
            logger.error(f"保存LLM配置失败: {e}")


# 全局单例
_config_manager_instance = None


def get_llm_config_manager() -> LLMConfigManager:
    """获取LLM配置管理器单例"""
    global _config_manager_instance
    if _config_manager_instance is None:
        _config_manager_instance = LLMConfigManager()
    return _config_manager_instance


# 便捷函数
def get_task_llm_params(task_name: str) -> Dict[str, Any]:
    """
    获取任务的LLM参数（便捷函数）
    
    Args:
        task_name: 任务名称
        
    Returns:
        LLM客户端参数
    """
    manager = get_llm_config_manager()
    return manager.get_llm_client_params(task_name)


def is_llm_task_enabled(task_name: str) -> bool:
    """
    检查LLM任务是否启用（便捷函数）
    
    Args:
        task_name: 任务名称
        
    Returns:
        是否启用
    """
    manager = get_llm_config_manager()
    return manager.is_task_enabled(task_name)


# 测试函数
def test_config_manager():
    """测试配置管理器"""
    print("=" * 60)
    print("LLM配置管理器测试")
    print("=" * 60)
    
    manager = get_llm_config_manager()
    
    # 测试1：获取任务配置
    print("\n【测试1】获取策略选择任务配置")
    params = manager.get_llm_client_params("strategy_selection")
    print(f"提供商: {params['provider']}")
    print(f"模型: {params['model']}")
    print(f"温度: {params['temperature']}")
    print(f"最大tokens: {params['max_tokens']}")
    
    # 测试2：获取所有任务
    print("\n【测试2】所有LLM任务")
    tasks = manager.get_all_tasks()
    for task_name, task_config in tasks.items():
        status = "✅ 启用" if task_config.get("enabled") else "❌ 禁用"
        print(f"  {status} {task_name}: {task_config.get('description')}")
    
    # 测试3：获取所有提供商
    print("\n【测试3】所有LLM提供商")
    providers = manager.get_all_providers()
    for provider_name, provider_config in providers.items():
        print(f"  - {provider_name}: {provider_config.get('name')}")
        print(f"    默认模型: {provider_config.get('default_model')}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_config_manager()
