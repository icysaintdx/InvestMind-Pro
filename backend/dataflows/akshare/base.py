#!/usr/bin/env python3
"""
AKShare数据基类
提供统一的错误处理和日志记录
"""

from typing import Any, Callable
from backend.utils.logging_config import get_logger

try:
    import akshare as ak
    HAS_AKSHARE = True
except ImportError:
    HAS_AKSHARE = False


class AKShareBase:
    """AKShare数据基类"""
    
    def __init__(self):
        """初始化"""
        if not HAS_AKSHARE:
            raise ImportError("❌ AKShare未安装，请运行: pip install akshare")
        
        self.logger = get_logger(self.__class__.__name__)
        self.logger.info(f"✅ {self.__class__.__name__} 初始化完成")
    
    def safe_call(self, func: Callable, *args, **kwargs) -> Any:
        """
        安全调用AKShare接口
        
        Args:
            func: AKShare函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            函数返回值，失败时返回None
        """
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            self.logger.error(f"❌ {func.__name__} 调用失败: {e}")
            return None
    
    def df_to_dict(self, df, orient='records'):
        """
        DataFrame转字典
        
        Args:
            df: pandas DataFrame
            orient: 转换方向
            
        Returns:
            字典列表
        """
        if df is None:
            return []
        
        try:
            # 处理NaN值
            df = df.fillna('')
            # 转换为字典
            return df.to_dict(orient=orient)
        except Exception as e:
            self.logger.error(f"❌ DataFrame转换失败: {e}")
            return []
