#!/usr/bin/env python3
"""
测试爬虫功能
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.dataflows.news.china_market_crawler import ChinaMarketCrawler
from backend.utils.logging_config import get_logger

logger = get_logger("test_crawlers")

print("=" * 80)
print("🧪 测试中国市场爬虫")
print("=" * 80)
print()

# 测试股票代码
test_stock = "600519"

# 创建爬虫实例
crawler = ChinaMarketCrawler()

# 测试1: 东方财富新闻
print("📰 测试1: 东方财富新闻")
print("-" * 80)
try:
    news_list = crawler.get_eastmoney_news(test_stock, limit=5)
    if news_list:
        print(f"✅ 成功获取 {len(news_list)} 条新闻")
        for i, news in enumerate(news_list[:3], 1):
            print(f"\n{i}. {news.get('title', 'N/A')}")
            print(f"   时间: {news.get('publish_time', 'N/A')}")
            print(f"   来源: {news.get('source', 'N/A')}")
    else:
        print("⚠️ 未获取到新闻")
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n")

# 测试2: 新浪财经新闻
print("📰 测试2: 新浪财经新闻")
print("-" * 80)
try:
    news_list = crawler.get_sina_news(test_stock, limit=5)
    if news_list:
        print(f"✅ 成功获取 {len(news_list)} 条新闻")
        for i, news in enumerate(news_list[:3], 1):
            print(f"\n{i}. {news.get('title', 'N/A')}")
            print(f"   时间: {news.get('publish_time', 'N/A')}")
    else:
        print("⚠️ 未获取到新闻")
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n")

# 测试3: 雪球评论
print("💬 测试3: 雪球评论")
print("-" * 80)
try:
    comments = crawler.get_xueqiu_comments(test_stock, limit=5)
    if comments:
        print(f"✅ 成功获取 {len(comments)} 条评论")
        for i, comment in enumerate(comments[:3], 1):
            print(f"\n{i}. {comment.get('text', 'N/A')[:100]}")
            print(f"   作者: {comment.get('user_name', 'N/A')}")
            print(f"   点赞: {comment.get('like_count', 0)}")
    else:
        print("⚠️ 未获取到评论")
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n")

# 测试4: 财联社快讯
print("⚡ 测试4: 财联社快讯")
print("-" * 80)
try:
    news_list = crawler.get_cls_news(limit=5)
    if news_list:
        print(f"✅ 成功获取 {len(news_list)} 条快讯")
        for i, news in enumerate(news_list[:3], 1):
            print(f"\n{i}. {news.get('title', 'N/A')}")
            print(f"   时间: {news.get('publish_time', 'N/A')}")
    else:
        print("⚠️ 未获取到快讯")
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n")

# 测试5: AKShare新闻
print("📊 测试5: AKShare新闻")
print("-" * 80)
try:
    # AKShare 不支持 limit 参数
    news_list = crawler.get_akshare_news(test_stock)
    if news_list:
        print(f"✅ 成功获取 {len(news_list)} 条新闻")
        for i, news in enumerate(news_list[:3], 1):
            print(f"\n{i}. {news.get('title', 'N/A')}")
            print(f"   时间: {news.get('publish_time', 'N/A')}")
    else:
        print("⚠️ 未获取到新闻")
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n")

# 测试6: Tushare新闻（如果配置了token）
print("📈 测试6: Tushare新闻")
print("-" * 80)
try:
    if crawler.pro:
        # Tushare 不支持 limit 参数，使用日期范围
        from datetime import datetime, timedelta
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        news_list = crawler.get_tushare_news(test_stock, start_date, end_date)
        if news_list:
            print(f"✅ 成功获取 {len(news_list)} 条新闻")
            for i, news in enumerate(news_list[:3], 1):
                print(f"\n{i}. {news.get('title', 'N/A')}")
                print(f"   时间: {news.get('publish_time', 'N/A')}")
        else:
            print("⚠️ 未获取到新闻")
    else:
        print("⚠️ 未配置TUSHARE_TOKEN，跳过测试")
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n")
print("=" * 80)
print("📋 测试总结")
print("=" * 80)
print()
print("✅ = 测试通过")
print("⚠️ = 测试通过但无数据")
print("❌ = 测试失败")
print()
print("下一步:")
print("1. 修复失败的爬虫")
print("2. 优化数据解析")
print("3. 集成到统一接口")
print()
