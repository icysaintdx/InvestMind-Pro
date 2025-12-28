"""
tradingagents.config.providers_config 兼容层
提供数据源配置
"""
import os

def get_provider_config(provider_name: str) -> dict:
    """获取数据源配置"""
    configs = {
        'tushare': {
            'token': os.environ.get('TUSHARE_TOKEN', ''),
            'enabled': bool(os.environ.get('TUSHARE_TOKEN')),
        },
        'akshare': {
            'enabled': True,
        },
        'juhe': {
            'api_key': os.environ.get('JUHE_API_KEY', ''),
            'enabled': bool(os.environ.get('JUHE_API_KEY')),
        },
        'alpha_vantage': {
            'api_key': os.environ.get('ALPHA_VANTAGE_API_KEY', ''),
            'enabled': bool(os.environ.get('ALPHA_VANTAGE_API_KEY')),
        },
    }
    return configs.get(provider_name, {})

__all__ = ['get_provider_config']
