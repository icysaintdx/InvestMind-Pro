"""
自定义日志处理器，将日志推送到 SSE 流
"""
import logging
import re
from typing import Optional


class AgentLogStreamHandler(logging.Handler):
    """自定义日志处理器，将日志推送到前端"""
    
    def __init__(self, agent_id: str, level=logging.INFO):
        """
        初始化日志流处理器
        
        Args:
            agent_id: 智能体ID
            level: 日志级别（默认 INFO）
        """
        super().__init__(level)
        self.agent_id = agent_id
        
    def emit(self, record: logging.LogRecord):
        """拦截日志并推送到前端"""
        try:
            # 只处理 INFO 级别及以上的日志
            if record.levelno < logging.INFO:
                return
            
            # 格式化日志消息
            message = self.format(record)
            
            # 提取关键信息
            clean_message = self._clean_message(message)
            
            # 解析日志类型
            log_type = self._parse_log_type(clean_message, record.levelno)
            
            # 推送到前端
            from backend.api.agent_logs_api import push_agent_log
            push_agent_log(self.agent_id, log_type, clean_message)
            
        except Exception as e:
            # 避免日志处理器本身出错影响主流程
            print(f"[LogStreamHandler] 日志推送失败: {e}")
    
    def _clean_message(self, message: str) -> str:
        """
        清理日志消息，只保留关键信息
        
        移除：
        - 时间戳
        - 日志级别
        - 模块名（部分）
        """
        # 移除时间戳 (2025-12-08 02:44:18,022)
        message = re.sub(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}', '', message)
        
        # 移除管道符号前的模块名
        if '|' in message:
            parts = message.split('|')
            # 保留最后一部分（实际消息）
            if len(parts) >= 3:
                message = parts[-1].strip()
        
        # 移除日志级别标记
        message = re.sub(r'\b(INFO|DEBUG|WARNING|ERROR|CRITICAL)\b', '', message)
        
        # 移除多余空格
        message = ' '.join(message.split())
        
        return message.strip()
    
    def _parse_log_type(self, message: str, level: int) -> str:
        """
        根据日志内容和级别判断类型
        
        Args:
            message: 日志消息
            level: 日志级别
        
        Returns:
            str: 日志类型 ("info", "success", "error", "progress", "warning")
        """
        # 错误级别
        if level >= logging.ERROR:
            return "error"
        
        # 警告级别
        if level >= logging.WARNING:
            return "warning"
        
        # 根据消息内容判断
        if "✅" in message or "成功" in message or "完成" in message:
            return "success"
        elif "❌" in message or "失败" in message or "错误" in message:
            return "error"
        elif "⚠️" in message or "警告" in message:
            return "warning"
        elif "获取" in message or "开始" in message or "正在" in message or "处理" in message:
            return "progress"
        else:
            return "info"


def create_agent_log_handler(agent_id: str) -> AgentLogStreamHandler:
    """
    创建智能体日志流处理器的工厂函数
    
    Args:
        agent_id: 智能体ID
    
    Returns:
        AgentLogStreamHandler: 日志流处理器实例
    """
    handler = AgentLogStreamHandler(agent_id)
    
    # 设置简单的格式器（因为我们会在 _clean_message 中清理）
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    
    return handler


def attach_log_stream(logger_name: str, agent_id: str) -> AgentLogStreamHandler:
    """
    为指定 logger 附加日志流处理器
    
    Args:
        logger_name: Logger 名称
        agent_id: 智能体ID
    
    Returns:
        AgentLogStreamHandler: 已附加的处理器
    """
    logger = logging.getLogger(logger_name)
    handler = create_agent_log_handler(agent_id)
    logger.addHandler(handler)
    return handler


def detach_log_stream(logger_name: str, handler: AgentLogStreamHandler):
    """
    从指定 logger 移除日志流处理器
    
    Args:
        logger_name: Logger 名称
        handler: 要移除的处理器
    """
    logger = logging.getLogger(logger_name)
    logger.removeHandler(handler)
