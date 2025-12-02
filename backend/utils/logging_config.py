#!/usr/bin/env python3
"""
统一日志配置系统
替代原有的 tradingagents.utils.logging_init
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler
import colorlog

# 创建日志目录
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# 日志级别配置
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

# 日志格式配置
CONSOLE_FORMAT = "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s%(reset)s"
FILE_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# 颜色配置
LOG_COLORS = {
    'DEBUG': 'cyan',
    'INFO': 'green',
    'WARNING': 'yellow',
    'ERROR': 'red',
    'CRITICAL': 'red,bg_white',
}

def setup_logging(level="INFO", console_output=True, file_output=True):
    """
    配置全局日志系统
    
    Args:
        level: 日志级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL)
        console_output: 是否输出到控制台
        file_output: 是否输出到文件
    """
    # 获取根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVELS.get(level, logging.INFO))
    
    # 清除已有的处理器
    root_logger.handlers.clear()
    
    # 控制台处理器
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(LOG_LEVELS.get(level, logging.INFO))
        
        # 使用彩色格式
        console_formatter = colorlog.ColoredFormatter(
            CONSOLE_FORMAT,
            log_colors=LOG_COLORS,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # 文件处理器
    if file_output:
        # 创建按日期命名的日志文件
        log_file = LOG_DIR / f"trading_{datetime.now():%Y%m%d}.log"
        
        # 使用循环文件处理器，最大10MB，保留5个备份
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(LOG_LEVELS.get(level, logging.INFO))
        
        # 文件格式（不需要颜色）
        file_formatter = logging.Formatter(
            FILE_FORMAT,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # 设置第三方库的日志级别
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    
    return root_logger

def get_logger(name="trading"):
    """
    获取指定名称的日志器
    
    Args:
        name: 日志器名称
        
    Returns:
        logging.Logger: 配置好的日志器
    """
    # 如果根日志器没有处理器，先进行基础配置
    if not logging.getLogger().handlers:
        setup_logging()
    
    # 返回指定名称的日志器
    logger = logging.getLogger(name)
    
    # 添加一些便利方法
    def log_with_emoji(level, emoji, message, *args, **kwargs):
        """带emoji的日志输出"""
        formatted_message = f"{emoji} {message}"
        getattr(logger, level)(formatted_message, *args, **kwargs)
    
    # 添加便利方法
    logger.success = lambda msg, *args, **kwargs: log_with_emoji('info', '✅', msg, *args, **kwargs)
    logger.fail = lambda msg, *args, **kwargs: log_with_emoji('error', '❌', msg, *args, **kwargs)
    logger.start = lambda msg, *args, **kwargs: log_with_emoji('info', '🚀', msg, *args, **kwargs)
    logger.complete = lambda msg, *args, **kwargs: log_with_emoji('info', '🎯', msg, *args, **kwargs)
    logger.progress = lambda msg, *args, **kwargs: log_with_emoji('info', '📊', msg, *args, **kwargs)
    
    return logger

class LoggerManager:
    """日志管理器（单例模式）"""
    
    _instance = None
    _loggers = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # 初始化日志系统
        setup_logging(level="INFO")
        self._initialized = True
    
    def get_logger(self, name="trading"):
        """获取或创建日志器"""
        if name not in self._loggers:
            self._loggers[name] = get_logger(name)
        return self._loggers[name]
    
    def set_level(self, level):
        """设置全局日志级别"""
        root_logger = logging.getLogger()
        root_logger.setLevel(LOG_LEVELS.get(level, logging.INFO))
        for handler in root_logger.handlers:
            handler.setLevel(LOG_LEVELS.get(level, logging.INFO))
    
    def add_file_handler(self, filename, level="INFO"):
        """添加额外的文件处理器"""
        root_logger = logging.getLogger()
        
        file_handler = logging.FileHandler(
            LOG_DIR / filename,
            encoding='utf-8'
        )
        file_handler.setLevel(LOG_LEVELS.get(level, logging.INFO))
        
        formatter = logging.Formatter(
            FILE_FORMAT,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

# 创建全局日志管理器实例
logger_manager = LoggerManager()

# 导出便利函数
def init_logging(level="INFO", console=True, file=True):
    """初始化日志系统的便利函数"""
    setup_logging(level=level, console_output=console, file_output=file)

def get_module_logger(module_name):
    """获取模块专用日志器"""
    return logger_manager.get_logger(f"trading.{module_name}")

# 测试代码
if __name__ == "__main__":
    # 初始化日志
    init_logging(level="DEBUG")
    
    # 测试不同级别的日志
    logger = get_logger("test")
    
    logger.debug("这是调试信息")
    logger.info("这是普通信息")
    logger.warning("这是警告信息")
    logger.error("这是错误信息")
    logger.critical("这是严重错误")
    
    # 测试自定义方法
    logger.success("操作成功！")
    logger.fail("操作失败！")
    logger.start("开始处理...")
    logger.complete("处理完成！")
    logger.progress("处理进度 50%")
    
    print(f"\n日志已保存到: {LOG_DIR}")
