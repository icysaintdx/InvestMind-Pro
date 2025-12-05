#!/usr/bin/env python3
"""
修复爬虫问题
根据测试结果修复各个爬虫的问题
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("🔧 修复爬虫问题")
print("=" * 80)
print()

# 问题1: dataflow_utils 缺少 save_output 函数
print("📝 问题1: dataflow_utils 缺少 save_output 函数")
print("-" * 80)

try:
    from backend.utils import dataflow_utils
    
    # 检查是否有 save_output 函数
    if not hasattr(dataflow_utils, 'save_output'):
        print("⚠️ 缺少 save_output 函数，正在添加...")
        
        # 读取文件
        file_path = "backend/utils/dataflow_utils.py"
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 添加函数
        new_function = '''

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
'''
        
        # 写入文件
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(new_function)
        
        print("✅ 已添加 save_output 函数")
    else:
        print("✅ save_output 函数已存在")
        
except Exception as e:
    print(f"❌ 修复失败: {e}")

print()

# 问题2: AKShare 和 Tushare 参数问题
print("📝 问题2: 检查 AKShare 和 Tushare 函数签名")
print("-" * 80)

try:
    from backend.dataflows.news.china_market_crawler import ChinaMarketCrawler
    import inspect
    
    crawler = ChinaMarketCrawler()
    
    # 检查 get_akshare_news 签名
    if hasattr(crawler, 'get_akshare_news'):
        sig = inspect.signature(crawler.get_akshare_news)
        print(f"get_akshare_news 签名: {sig}")
        
        # 检查是否有 limit 参数
        if 'limit' not in sig.parameters:
            print("⚠️ get_akshare_news 不支持 limit 参数")
    
    # 检查 get_tushare_news 签名
    if hasattr(crawler, 'get_tushare_news'):
        sig = inspect.signature(crawler.get_tushare_news)
        print(f"get_tushare_news 签名: {sig}")
        
        # 检查是否有 limit 参数
        if 'limit' not in sig.parameters:
            print("⚠️ get_tushare_news 不支持 limit 参数")
    
    print("✅ 函数签名检查完成")
    
except Exception as e:
    print(f"❌ 检查失败: {e}")

print()

# 问题3: 雪球评论 JSON 解析错误
print("📝 问题3: 雪球评论反爬虫问题")
print("-" * 80)
print("⚠️ 雪球网站有反爬虫机制，需要：")
print("  1. 使用 curl_cffi 模拟真实浏览器")
print("  2. 添加完整的请求头")
print("  3. 处理 Cookie")
print("  4. 控制请求频率")
print("建议：稍后单独修复")

print()

print("=" * 80)
print("📋 修复总结")
print("=" * 80)
print()
print("✅ = 已修复")
print("⚠️ = 需要手动修复")
print("❌ = 修复失败")
print()
print("下一步:")
print("1. 重新运行测试: python test_crawlers.py")
print("2. 修复雪球评论爬虫")
print("3. 优化东方财富新闻API")
print()
