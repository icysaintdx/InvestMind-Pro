#!/usr/bin/env python3
"""
工具日志装饰器
用于记录智能体模块的执行时间和状态
"""

import time
import functools
import asyncio
from datetime import datetime
from typing import Any, Callable
from backend.utils.logging_config import get_logger

logger = get_logger("tool_logging")

def log_tool_call(tool_name: str = None):
    """
    工具调用日志装饰器
    
    Args:
        tool_name: 工具名称
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 获取工具名称
            name = tool_name or func.__name__
            
            # 记录开始
            start_time = time.time()
            logger.info(f"🔧 [工具调用] {name} - 开始执行")
            
            try:
                # 执行函数
                result = func(*args, **kwargs)
                
                # 记录成功
                elapsed = time.time() - start_time
                logger.success(f"[工具调用] {name} - 执行成功 (耗时: {elapsed:.2f}秒)")
                
                return result
                
            except Exception as e:
                # 记录失败
                elapsed = time.time() - start_time
                logger.fail(f"[工具调用] {name} - 执行失败 (耗时: {elapsed:.2f}秒)")
                logger.error(f"错误详情: {str(e)}")
                raise
                
        return wrapper
    return decorator

def log_analyst_module(module_name: str):
    """
    分析师模块日志装饰器
    
    Args:
        module_name: 模块名称（如 "news", "fundamentals" 等）
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(state: dict) -> dict:
            # 获取状态信息
            ticker = state.get("company_of_interest", "未知")
            date = state.get("trade_date", datetime.now().strftime("%Y-%m-%d"))
            session_id = state.get("session_id", "未知会话")
            
            # 记录开始
            start_time = time.time()
            logger.start(f"[{module_name.upper()}分析师] 开始分析 {ticker} | 日期: {date} | 会话: {session_id}")
            
            try:
                # 执行分析
                result = func(state)
                
                # 记录完成
                elapsed = time.time() - start_time
                logger.complete(f"[{module_name.upper()}分析师] {ticker} 分析完成 (耗时: {elapsed:.2f}秒)")
                
                # 记录关键结果
                if isinstance(result, dict):
                    if "sentiment" in result:
                        logger.info(f"  情绪评分: {result['sentiment']}")
                    if "recommendation" in result:
                        logger.info(f"  推荐操作: {result['recommendation']}")
                    if "confidence" in result:
                        logger.info(f"  信心指数: {result['confidence']}")
                
                return result
                
            except Exception as e:
                # 记录失败
                elapsed = time.time() - start_time
                logger.fail(f"[{module_name.upper()}分析师] {ticker} 分析失败 (耗时: {elapsed:.2f}秒)")
                logger.error(f"错误详情: {str(e)}", exc_info=True)
                
                # 返回错误状态
                return {
                    "error": True,
                    "error_message": str(e),
                    "module": module_name,
                    "ticker": ticker
                }
                
        return wrapper
    return decorator

def log_debate_round(debate_type: str, round_num: int = None, content: str = None):
    """辩论回合日志

    支持两种用法：
    1. 作为装饰器：@log_debate_round("research")
    2. 直接调用记录单回合：log_debate_round("bull", 1, "本轮观点内容...")
    """

    # 如果只传入 debate_type，则按旧逻辑返回装饰器，保持向后兼容
    if round_num is None and content is None:
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                # 记录辩论开始
                start_time = time.time()
                logger.info(f"💬 [{debate_type.upper()}辩论] 开始新回合")
                
                try:
                    # 执行辩论
                    result = func(*args, **kwargs)
                    
                    # 记录辩论结果
                    elapsed = time.time() - start_time
                    logger.success(f"[{debate_type.upper()}辩论] 回合结束 (耗时: {elapsed:.2f}秒)")
                    
                    # 记录辩论要点
                    if isinstance(result, dict):
                        if "bull_view" in result and "bear_view" in result:
                            logger.info(f"  看涨观点强度: {result.get('bull_strength', 'N/A')}")
                            logger.info(f"  看跌观点强度: {result.get('bear_strength', 'N/A')}")
                        if "risk_level" in result:
                            logger.info(f"  风险等级: {result['risk_level']}")
                    
                    return result
                    
                except Exception as e:
                    # 记录失败
                    elapsed = time.time() - start_time
                    logger.fail(f"[{debate_type.upper()}辩论] 回合失败 (耗时: {elapsed:.2f}秒)")
                    logger.error(f"错误详情: {str(e)}")
                    raise
                    
            return wrapper
        return decorator

    # 直接调用模式：简单记录一条辩论回合日志
    snippet = (content or "").replace("\n", " ")
    if len(snippet) > 120:
        snippet = snippet[:117] + "..."
    logger.info(f"💬 [{debate_type}] 第 {round_num} 轮发言摘要: {snippet}")

def log_data_fetch(source_name: str):
    """
    数据获取日志装饰器
    
    Args:
        source_name: 数据源名称
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 提取股票代码（如果有）
            stock_code = None
            if args:
                stock_code = args[0] if isinstance(args[0], str) else None
            if not stock_code and kwargs:
                stock_code = kwargs.get('stock_code') or kwargs.get('ticker') or kwargs.get('symbol')
            
            # 记录开始
            start_time = time.time()
            if stock_code:
                logger.info(f"📡 [{source_name}] 获取 {stock_code} 数据...")
            else:
                logger.info(f"📡 [{source_name}] 获取数据...")
            
            try:
                # 执行获取
                result = func(*args, **kwargs)
                
                # 记录成功
                elapsed = time.time() - start_time
                
                # 统计结果数量
                count = "未知"
                if isinstance(result, list):
                    count = len(result)
                elif isinstance(result, dict):
                    count = len(result.keys())
                elif isinstance(result, str):
                    count = f"{len(result)} 字符"
                
                logger.success(f"[{source_name}] 数据获取成功 (数量: {count}, 耗时: {elapsed:.2f}秒)")
                
                return result
                
            except Exception as e:
                # 记录失败
                elapsed = time.time() - start_time
                logger.fail(f"[{source_name}] 数据获取失败 (耗时: {elapsed:.2f}秒)")
                logger.error(f"错误详情: {str(e)}")
                
                # 返回空结果而不是抛出异常（降级处理）
                return None
                
        return wrapper
    return decorator

def log_cache_operation(operation: str):
    """
    缓存操作日志装饰器
    
    Args:
        operation: 操作类型（"get", "set", "delete" 等）
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 提取缓存键
            cache_key = args[0] if args else kwargs.get('key', '未知')
            
            # 记录操作
            logger.debug(f"💾 [缓存{operation.upper()}] 键: {cache_key}")
            
            try:
                # 执行操作
                result = func(*args, **kwargs)
                
                # 记录结果
                if operation == "get":
                    if result is not None:
                        logger.debug(f"[缓存命中] 键: {cache_key}")
                    else:
                        logger.debug(f"[缓存未命中] 键: {cache_key}")
                elif operation == "set":
                    logger.debug(f"[缓存设置成功] 键: {cache_key}")
                elif operation == "delete":
                    logger.debug(f"[缓存删除成功] 键: {cache_key}")
                
                return result
                
            except Exception as e:
                logger.error(f"[缓存{operation.upper()}失败] 键: {cache_key}, 错误: {str(e)}")
                raise
                
        return wrapper
    return decorator

def log_api_call(api_name: str):
    """
    API调用日志装饰器
    
    Args:
        api_name: API名称
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            # 记录请求
            start_time = time.time()
            logger.info(f"🌐 [API调用] {api_name} - 发送请求")
            
            try:
                # 执行调用
                result = await func(*args, **kwargs)
                
                # 记录响应
                elapsed = time.time() - start_time
                logger.success(f"[API调用] {api_name} - 响应成功 (耗时: {elapsed:.2f}秒)")
                
                return result
                
            except Exception as e:
                # 记录失败
                elapsed = time.time() - start_time
                logger.fail(f"[API调用] {api_name} - 调用失败 (耗时: {elapsed:.2f}秒)")
                logger.error(f"错误详情: {str(e)}")
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            # 记录请求
            start_time = time.time()
            logger.info(f"🌐 [API调用] {api_name} - 发送请求")
            
            try:
                # 执行调用
                result = func(*args, **kwargs)
                
                # 记录响应
                elapsed = time.time() - start_time
                logger.success(f"[API调用] {api_name} - 响应成功 (耗时: {elapsed:.2f}秒)")
                
                return result
                
            except Exception as e:
                # 记录失败
                elapsed = time.time() - start_time
                logger.fail(f"[API调用] {api_name} - 调用失败 (耗时: {elapsed:.2f}秒)")
                logger.error(f"错误详情: {str(e)}")
                raise
        
        # 根据函数类型返回对应的包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
            
    return decorator

# 测试代码
if __name__ == "__main__":
    import asyncio
    
    # 测试工具调用装饰器
    @log_tool_call("测试工具")
    def test_tool(param):
        time.sleep(0.5)
        return f"处理完成: {param}"
    
    # 测试分析师装饰器
    @log_analyst_module("test")
    def test_analyst(state):
        time.sleep(0.3)
        return {
            "sentiment": 0.75,
            "recommendation": "BUY",
            "confidence": 0.85
        }
    
    # 测试数据获取装饰器
    @log_data_fetch("测试数据源")
    def test_fetch(stock_code):
        time.sleep(0.2)
        return ["数据1", "数据2", "数据3"]
    
    # 测试API调用装饰器
    @log_api_call("测试API")
    async def test_api():
        await asyncio.sleep(0.1)
        return {"status": "success"}
    
    # 执行测试
    print("开始测试日志装饰器...\n")
    
    # 测试工具
    result = test_tool("参数123")
    print(f"工具结果: {result}\n")
    
    # 测试分析师
    state = {
        "company_of_interest": "000001",
        "trade_date": "2024-01-01",
        "session_id": "test-session"
    }
    result = test_analyst(state)
    print(f"分析结果: {result}\n")
    
    # 测试数据获取
    result = test_fetch("600519")
    print(f"数据结果: {result}\n")
    
    # 测试API调用
    async def run_api_test():
        result = await test_api()
        print(f"API结果: {result}\n")
    
    asyncio.run(run_api_test())
    
    print("测试完成！")

# 创建别名以保持向后兼容性
log_analysis_step = log_analyst_module
