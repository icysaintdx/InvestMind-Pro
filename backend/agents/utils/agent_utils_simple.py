"""
简化版的agent_utils，移除LangChain依赖
"""

from typing import List, Dict, Any, Optional
from datetime import date, timedelta, datetime
import functools
import pandas as pd
import os
from dateutil.relativedelta import relativedelta
import backend.dataflows.interface as interface

# 导入统一日志系统和工具日志装饰器
from backend.utils.logging_config import get_logger
from backend.utils.tool_logging import log_tool_call

# 获取logger实例
logger = get_logger('agents')

# 创建默认配置
DEFAULT_CONFIG = {
    "model": "deepseek-chat",
    "temperature": 0.3,
    "max_tokens": 4000,
    "api_key": os.getenv("DEEPSEEK_API_KEY", "")
}

# 简化的消息类（替代LangChain的消息类）
class BaseMessage:
    """基础消息类"""
    def __init__(self, content: str, **kwargs):
        self.content = content
        self.id = kwargs.get('id', None)
        self.metadata = kwargs

class HumanMessage(BaseMessage):
    """用户消息"""
    role = "user"
    
class AIMessage(BaseMessage):
    """AI消息"""
    role = "assistant"
    
class ToolMessage(BaseMessage):
    """工具消息"""
    role = "tool"

class RemoveMessage:
    """删除消息操作"""
    def __init__(self, id: str):
        self.id = id


def create_msg_delete():
    """创建消息删除函数"""
    def delete_messages(state):
        """Clear messages and add placeholder"""
        messages = state.get("messages", [])
        
        # Remove all messages
        removal_operations = [RemoveMessage(id=m.id) for m in messages if hasattr(m, 'id')]
        
        # Add a minimal placeholder message
        placeholder = HumanMessage(content="Continue")
        
        return {"messages": removal_operations + [placeholder]}
    
    return delete_messages


class Toolkit:
    """工具包类"""
    _config = DEFAULT_CONFIG.copy()
    
    @classmethod
    def update_config(cls, config: Dict[str, Any]):
        """更新配置"""
        cls._config.update(config)
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """获取配置"""
        return cls._config.copy()
    
    @staticmethod
    def create_tools():
        """创建工具列表"""
        tools = []
        
        # 可以在这里添加具体的工具
        # 例如: tools.append(get_stock_data_tool())
        
        return tools
    
    @staticmethod
    def wrap_tool(func):
        """工具包装器"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Tool error: {str(e)}")
                return {"error": str(e)}
        return wrapper


# 工具装饰器（简化版）
def tool(func=None, *, name: Optional[str] = None, description: Optional[str] = None):
    """工具装饰器，用于标记函数为工具"""
    def decorator(f):
        # 添加工具元数据
        f.is_tool = True
        f.tool_name = name or f.__name__
        f.tool_description = description or f.__doc__
        
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        
        return wrapper
    
    if func is None:
        return decorator
    else:
        return decorator(func)


# 简化的Prompt模板
class ChatPromptTemplate:
    """聊天提示模板"""
    def __init__(self, messages: List[Any]):
        self.messages = messages
    
    @classmethod
    def from_messages(cls, messages: List[Any]):
        """从消息列表创建模板"""
        return cls(messages)
    
    def format_messages(self, **kwargs) -> List[BaseMessage]:
        """格式化消息"""
        formatted = []
        for msg in self.messages:
            if isinstance(msg, tuple):
                role, content = msg
                if role == "system":
                    formatted.append(AIMessage(content=content.format(**kwargs)))
                elif role == "human":
                    formatted.append(HumanMessage(content=content.format(**kwargs)))
            elif isinstance(msg, BaseMessage):
                formatted.append(msg)
        return formatted


class MessagesPlaceholder:
    """消息占位符"""
    def __init__(self, variable_name: str):
        self.variable_name = variable_name


# 导出
__all__ = [
    'BaseMessage',
    'HumanMessage', 
    'AIMessage',
    'ToolMessage',
    'RemoveMessage',
    'create_msg_delete',
    'Toolkit',
    'tool',
    'ChatPromptTemplate',
    'MessagesPlaceholder',
    'DEFAULT_CONFIG',
    'logger'
]
