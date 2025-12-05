"""
数据流工具模块
提供数据流相关的辅助功能
"""

from backend.utils.logging_config import get_logger

logger = get_logger("dataflow_utils")


def format_stock_data(data):
    """
    格式化股票数据
    
    Args:
        data: 原始股票数据
        
    Returns:
        格式化后的数据
    """
    if not data:
        return None
    
    # 简单的格式化逻辑
    return data


def validate_ticker(ticker):
    """
    验证股票代码格式
    
    Args:
        ticker: 股票代码
        
    Returns:
        bool: 是否有效
    """
    if not ticker or not isinstance(ticker, str):
        return False
    
    # 简单验证
    return len(ticker) >= 4


def save_output(data, filename: str):
    """
    保存输出数据到文件
    
    Args:
        data: 要保存的数据
        filename: 文件名
    """
    import json
    import os
    
    # 确保目录存在
    os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
    
    # 保存数据
    with open(filename, 'w', encoding='utf-8') as f:
        if isinstance(data, (dict, list)):
            json.dump(data, f, ensure_ascii=False, indent=2)
        else:
            f.write(str(data))
    
    logger.info(f"数据已保存到: {filename}")
