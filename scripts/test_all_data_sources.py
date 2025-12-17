#!/usr/bin/env python3
"""
测试所有数据源接口
验证哪些能用，哪些需要修复
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 80)
print("🧪 InvestMindPro 数据源测试")
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
    
    if "❌" not in result:
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

# ==================== 测试2: 新闻数据 ====================
print("📰 测试2: 新闻数据获取")
print("-" * 80)

try:
    from backend.dataflows.news.unified_news_tool import create_unified_news_tool
    
    print("正在创建新闻工具...")
    tool = create_unified_news_tool()
    
    test_symbol = "600519"
    print(f"正在获取 {test_symbol} 的新闻...")
    
    # 这里需要异步调用
    async def test_news():
        news_list = await tool.get_news(test_symbol, days_back=3)
        return news_list
    
    news = asyncio.run(test_news())
    
    if news and len(news) > 0:
        print(f"✅ 新闻数据获取成功! 共 {len(news)} 条")
        for i, item in enumerate(news[:3], 1):
            print(f"  {i}. {item.get('title', 'N/A')} - {item.get('source', 'N/A')}")
    else:
        print("⚠️ 未获取到新闻数据")
        
except Exception as e:
    print(f"❌ 新闻数据测试失败: {e}")
    import traceback
    traceback.print_exc()

print()
print()

# ==================== 测试3: 中国财经新闻 ====================
print("🇨🇳 测试3: 中国财经新闻")
print("-" * 80)

try:
    from backend.dataflows.news.chinese_finance import get_chinese_finance_news
    
    test_symbol = "600519"
    print(f"正在获取 {test_symbol} 的中国财经新闻...")
    
    async def test_chinese_news():
        news_list = await get_chinese_finance_news(test_symbol, days_back=3)
        return news_list
    
    news = asyncio.run(test_chinese_news())
    
    if news and len(news) > 0:
        print(f"✅ 中国财经新闻获取成功! 共 {len(news)} 条")
        for i, item in enumerate(news[:3], 1):
            print(f"  {i}. {item.get('title', 'N/A')} - {item.get('source', 'N/A')}")
    else:
        print("⚠️ 未获取到中国财经新闻")
        
except Exception as e:
    print(f"❌ 中国财经新闻测试失败: {e}")
    import traceback
    traceback.print_exc()

print()
print()

# ==================== 测试4: 实时新闻 ====================
print("⚡ 测试4: 实时新闻")
print("-" * 80)

try:
    from backend.dataflows.news.realtime_news import get_realtime_news
    
    test_symbol = "600519"
    print(f"正在获取 {test_symbol} 的实时新闻...")
    
    async def test_realtime_news():
        news_list = await get_realtime_news(test_symbol)
        return news_list
    
    news = asyncio.run(test_realtime_news())
    
    if news and len(news) > 0:
        print(f"✅ 实时新闻获取成功! 共 {len(news)} 条")
        for i, item in enumerate(news[:3], 1):
            print(f"  {i}. {item.get('title', 'N/A')} - {item.get('source', 'N/A')}")
    else:
        print("⚠️ 未获取到实时新闻")
        
except Exception as e:
    print(f"❌ 实时新闻测试失败: {e}")
    import traceback
    traceback.print_exc()

print()
print()

# ==================== 测试5: 社交媒体数据 ====================
print("🗣️ 测试5: 社交媒体数据")
print("-" * 80)

try:
    from backend.dataflows.social_media_crawler import get_social_sentiment
    
    test_symbol = "600519"
    print(f"正在获取 {test_symbol} 的社交媒体数据...")
    
    sentiment = get_social_sentiment(test_symbol)
    
    if sentiment:
        print(f"✅ 社交媒体数据获取成功!")
        print(f"  情绪: {sentiment.get('sentiment', 'N/A')}")
        print(f"  评论数: {sentiment.get('comment_count', 'N/A')}")
    else:
        print("⚠️ 未获取到社交媒体数据")
        
except Exception as e:
    print(f"❌ 社交媒体数据测试失败: {e}")
    import traceback
    traceback.print_exc()

print()
print()

# ==================== 测试6: AKShare 工具 ====================
print("📈 测试6: AKShare 工具")
print("-" * 80)

try:
    from backend.dataflows.akshare_utils import get_stock_info
    
    test_symbol = "600519"
    print(f"正在使用 AKShare 获取 {test_symbol} 的数据...")
    
    info = get_stock_info(test_symbol)
    
    if info:
        print(f"✅ AKShare 数据获取成功!")
        print(f"  股票名称: {info.get('name', 'N/A')}")
        print(f"  最新价: {info.get('price', 'N/A')}")
    else:
        print("⚠️ 未获取到 AKShare 数据")
        
except Exception as e:
    print(f"❌ AKShare 工具测试失败: {e}")
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
print("请根据测试结果修复失败的接口")
print()
