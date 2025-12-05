#!/usr/bin/env python3
"""
修复后的数据源测试脚本
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 加载环境变量
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ 已加载环境变量: {env_path}\n")
else:
    print(f"⚠️ 未找到 .env 文件: {env_path}\n")

print("=" * 80)
print("🧪 AlphaCouncil 数据源测试 (修复版)")
print("=" * 80)
print()

# ==================== 测试1: 股票数据 ====================
print("📊 测试1: 股票实时数据获取")
print("-" * 80)

try:
    from backend.dataflows.data_source_manager import DataSourceManager
    
    manager = DataSourceManager()
    test_symbol = "600519"  # 贵州茅台
    
    print(f"正在获取 {test_symbol} 的数据...")
    result = manager.get_stock_data(test_symbol)
    
    if "❌" not in result and "错误" not in result:
        print("✅ 股票数据获取成功!")
        print(result[:500])  # 只显示前500字符
    else:
        print("❌ 股票数据获取失败!")
        print(result)
        
except Exception as e:
    print(f"❌ 股票数据测试失败: {e}")
    import traceback
    traceback.print_exc()

print()
print()

# ==================== 测试2: 中国财经新闻 ====================
print("🇨🇳 测试2: 中国财经新闻")
print("-" * 80)

try:
    # 先检查函数签名
    from backend.dataflows.news import chinese_finance
    import inspect
    
    # 获取所有可用函数
    functions = [name for name in dir(chinese_finance) if not name.startswith('_')]
    print(f"可用函数: {functions}")
    
    # 尝试使用正确的函数
    if hasattr(chinese_finance, 'get_chinese_finance_news'):
        func = chinese_finance.get_chinese_finance_news
        sig = inspect.signature(func)
        print(f"函数签名: {sig}")
        
        # 根据签名调用
        test_symbol = "600519"
        print(f"正在获取 {test_symbol} 的中国财经新闻...")
        
        # 直接调用，不使用 await（因为函数返回 str）
        try:
            news = func(test_symbol)
        except TypeError as te:
            print(f"  尝试其他参数组合...")
            news = func(test_symbol, datetime.now().strftime('%Y-%m-%d'))
        
        if news and len(news) > 0:
            print(f"✅ 中国财经新闻获取成功!")
            print(f"结果类型: {type(news)}")
            print(f"结果长度: {len(news)} 字符")
            print(f"前500字符:\n{str(news)[:500]}")
        else:
            print("⚠️ 未获取到中国财经新闻")
    else:
        print("❌ 未找到 get_chinese_finance_news 函数")
        
except Exception as e:
    print(f"❌ 中国财经新闻测试失败: {e}")
    import traceback
    traceback.print_exc()

print()
print()

# ==================== 测试3: 实时新闻 ====================
print("⚡ 测试3: 实时新闻")
print("-" * 80)

try:
    from backend.dataflows.news import realtime_news
    import inspect
    
    # 获取所有可用函数
    functions = [name for name in dir(realtime_news) if not name.startswith('_')]
    print(f"可用函数: {functions[:10]}")  # 只显示前10个
    
    # 尝试使用正确的函数
    if hasattr(realtime_news, 'get_realtime_stock_news'):
        func = realtime_news.get_realtime_stock_news
        sig = inspect.signature(func)
        print(f"函数签名: {sig}")
        
        test_symbol = "600519"
        curr_date = datetime.now().strftime('%Y-%m-%d')
        print(f"正在获取 {test_symbol} 的实时新闻 (日期: {curr_date})...")
        
        # 直接调用，不使用 await
        news = func(test_symbol, curr_date)
        
        if news and len(news) > 0:
            print(f"✅ 实时新闻获取成功!")
            print(f"结果类型: {type(news)}")
            print(f"结果长度: {len(news)} 字符")
            print(f"前500字符:\n{str(news)[:500]}")
        else:
            print("⚠️ 未获取到实时新闻")
    else:
        print("❌ 未找到 get_realtime_stock_news 函数")
        
except Exception as e:
    print(f"❌ 实时新闻测试失败: {e}")
    import traceback
    traceback.print_exc()

print()
print()

# ==================== 测试4: 统一新闻工具 ====================
print("📰 测试4: 统一新闻工具")
print("-" * 80)

try:
    from backend.dataflows.news import unified_news_tool
    import inspect
    
    # 检查函数签名
    if hasattr(unified_news_tool, 'create_unified_news_tool'):
        func = unified_news_tool.create_unified_news_tool
        sig = inspect.signature(func)
        print(f"函数签名: {sig}")
        
        # 根据签名创建工具
        params = sig.parameters
        if 'toolkit' in params:
            print("  需要 toolkit 参数，跳过此测试")
            print("  (需要在实际环境中使用)")
        else:
            tool = func()
            print("✅ 统一新闻工具创建成功")
    else:
        print("❌ 未找到 create_unified_news_tool 函数")
        
except Exception as e:
    print(f"❌ 统一新闻工具测试失败: {e}")
    import traceback
    traceback.print_exc()

print()
print()

# ==================== 测试总结 ====================
print("=" * 80)
print("📋 测试总结")
print("=" * 80)
print()
print("✅ = 测试通过")
print("⚠️ = 测试通过但无数据")
print("❌ = 测试失败")
print()
print("下一步:")
print("1. 修复失败的接口")
print("2. 补充缺失的函数")
print("3. 从 TradingAgents-CN-main 复制缺失脚本")
print()
