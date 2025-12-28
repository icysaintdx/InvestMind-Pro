"""
tradingagents.config.config_manager 兼容层
提供配置管理器的兼容实现
"""
import os
from pathlib import Path
from backend.dataflows.utils.config import get_config, set_config, get_data_dir, DEFAULT_CONFIG

class ConfigManager:
    """配置管理器（兼容层）"""

    def __init__(self):
        self._config = DEFAULT_CONFIG.copy()

    def get_data_dir(self) -> str:
        """获取数据目录"""
        return get_data_dir()

    def load_settings(self) -> dict:
        """加载设置"""
        return get_config()

    def save_settings(self, config: dict):
        """保存设置"""
        set_config(config)

    def get(self, key: str, default=None):
        """获取配置项"""
        return get_config().get(key, default)

# 创建全局实例
config_manager = ConfigManager()

__all__ = ['config_manager', 'ConfigManager']
