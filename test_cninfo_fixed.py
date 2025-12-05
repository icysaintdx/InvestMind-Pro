#!/usr/bin/env python3
"""
测试修复后的巨潮资讯网API
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("🧪 测试修复后的巨潮资讯网API")
print("=" * 80)
print()

try:
    from backend.dataflows.announcement.cninfo_crawler import get_cninfo_crawler
    
    # 创建爬虫实例
    crawler = get_cninfo_crawler()
    
    # 测试股票代码
    test_codes = [
        ('600519', '贵州茅台 - 上交所'),
        ('000001', '平安银行 - 深交所'),
        ('000002', '万科A - 深交所')
    ]
    
    for stock_code, name in test_codes:
        print(f"\n{'='*80}")
        print(f"📊 测试股票: {stock_code} ({name})")
        print(f"{'='*80}\n")
        
        # 获取公告（最近7天）
        announcements = crawler.get_company_announcements(stock_code, days=7)
        
        if announcements:
            print(f"✅ 成功获取 {len(announcements)} 条公告\n")
            
            # 显示前3条
            for i, ann in enumerate(announcements[:3], 1):
                print(f"{i}. {ann['title']}")
                print(f"   类型: {ann['type']}")
                print(f"   日期: {ann['publish_date']}")
                print(f"   重要性: {ann['importance']}")
                print(f"   URL: {ann['url'][:80]}..." if len(ann['url']) > 80 else f"   URL: {ann['url']}")
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
            print(f"   1. 最近7天没有公告")
            print(f"   2. API参数需要进一步调整")
            print(f"   3. 网络连接问题")
            print(f"   4. 反爬虫限制")
    
    print("\n" + "=" * 80)
    print("📋 测试总结")
    print("=" * 80)
    print()
    print("修复内容:")
    print("1. ✅ 更新请求头（模拟真实浏览器）")
    print("2. ✅ 修复参数构建（根据真实接口）")
    print("3. ✅ 修复URL拼接（使用static.cninfo.com.cn）")
    print("4. ✅ 缩短日期范围（最近7天）")
    print("5. ✅ 减小每页数量（10条）")
    print()
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
