"""
数据流配置模块
提供默认配置，不依赖外部模块
"""

import os
from typing import Dict, Optional
from pathlib import Path

# 默认配置
DEFAULT_CONFIG = {
    "data_dir": os.path.join(os.path.dirname(__file__), "data"),
    "cache_dir": os.path.join(os.path.dirname(__file__), "cache"),
    "log_dir": os.path.join(os.path.dirname(__file__), "..", "..", "logs"),
    "max_cache_days": 7,
    "enable_cache": True,
    "api_timeout": 30,
    "retry_times": 3,
    "retry_delay": 1,
}

# Use default config but allow it to be overridden
_config: Optional[Dict] = None
DATA_DIR: Optional[str] = None


def initialize_config():
    """Initialize the configuration with default values."""
    global _config, DATA_DIR
    if _config is None:
        _config = DEFAULT_CONFIG.copy()
        DATA_DIR = _config["data_dir"]
        
        # 确保目录存在
        for key in ["data_dir", "cache_dir", "log_dir"]:
            dir_path = _config.get(key)
            if dir_path:
                Path(dir_path).mkdir(parents=True, exist_ok=True)


def set_config(config: Dict):
    """Update the configuration with custom values."""
    global _config, DATA_DIR
    if _config is None:
        _config = DEFAULT_CONFIG.copy()
    
    _config.update(config)
    DATA_DIR = _config["data_dir"]
    
    # 确保新目录存在
    if "data_dir" in config:
        Path(config["data_dir"]).mkdir(parents=True, exist_ok=True)


def get_config() -> Dict:
    """Get the current configuration."""
    if _config is None:
        initialize_config()

    return _config.copy()


def get_data_dir() -> str:
    """获取数据目录路径"""
    if _config is None:
        initialize_config()
    return _config.get("data_dir", DEFAULT_CONFIG["data_dir"])


def set_data_dir(data_dir: str):
    """设置数据目录路径"""
    set_config({"data_dir": data_dir})


# Initialize with default config
initialize_config()
