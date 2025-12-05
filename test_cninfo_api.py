#!/usr/bin/env python3
"""
测试巨潮资讯网真实API
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("🧪 测试巨潮资讯网真实API")
print("=" * 80)
print()

try:
    from backend.dataflows.announcement.cninfo_crawler import get_cninfo_crawler
    
    # 创建爬虫实例
    crawler = get_cninfo_crawler()
    
    # 测试股票代码
    test_codes = ['600519', '000001', '000002']
    
    for stock_code in test_codes:
        print(f"\n{'='*80}")
        print(f"📊 测试股票: {stock_code}")
        print(f"{'='*80}\n")
        
        # 获取公告
        announcements = crawler.get_company_announcements(stock_code, days=30)
        
        if announcements:
            print(f"✅ 成功获取 {len(announcements)} 条公告\n")
            
            # 显示前3条
            for i, ann in enumerate(announcements[:3], 1):
                print(f"{i}. {ann['title']}")
                print(f"   类型: {ann['type']}")
                print(f"   日期: {ann['publish_date']}")
                print(f"   重要性: {ann['importance']}")
                print(f"   URL: {ann['url']}")
                print()
            
            # 过滤重要公告
            important = crawler.filter_important_announcements(announcements)
            print(f"📌 重要公告: {len(important)} 条")
            
            # 分析公告
            analysis = crawler.analyze_announcements(announcements)
            print(f"\n📈 公告分析:")
            print(f"   总数: {analysis['total']}")
            print(f"   重要公告: {analysis['important_count']}")
            print(f"   类型分布: {analysis['types']}")
            
        else:
            print(f"⚠️ 未获取到公告数据")
            print(f"   可能原因:")
            print(f"   1. API接口变化")
            print(f"   2. 网络连接问题")
            print(f"   3. 股票代码不存在")
            print(f"   4. 反爬虫限制")
    
    print("\n" + "=" * 80)
    print("📋 测试总结")
    print("=" * 80)
    print()
    print("如果所有测试都失败，可能需要:")
    print("1. 检查网络连接")
    print("2. 更新User-Agent")
    print("3. 添加代理")
    print("4. 检查API接口是否变化")
    print()
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
