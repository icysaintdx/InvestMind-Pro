#!/usr/bin/env python3
"""
测试法律风险和公司公告爬虫
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("🧪 测试法律风险和公司公告爬虫")
print("=" * 80)
print()

# 测试1: 中国裁判文书网爬虫
print("⚖️ 测试1: 中国裁判文书网爬虫")
print("-" * 80)

try:
    from backend.dataflows.legal.wenshu_crawler import get_wenshu_crawler
    
    crawler = get_wenshu_crawler()
    company_name = "贵州茅台酒股份有限公司"
    
    print(f"搜索公司: {company_name}")
    print()
    
    # 搜索案件
    cases = crawler.search_company_cases(company_name, days=365)
    
    if cases:
        print(f"✅ 找到 {len(cases)} 个案件")
        print()
        
        # 显示案件详情
        for i, case in enumerate(cases[:3], 1):
            print(f"{i}. {case['case_name']}")
            print(f"   案件类型: {case['case_type']}")
            print(f"   法院: {case['court']}")
            print(f"   日期: {case['case_date']}")
            print(f"   风险等级: {case['risk_level']}")
            print()
        
        # 风险分析
        risk_analysis = crawler.analyze_legal_risk(cases)
        print("📊 风险分析:")
        print(f"   总案件数: {risk_analysis['total_cases']}")
        print(f"   风险等级: {risk_analysis['risk_level']}")
        print(f"   风险评分: {risk_analysis['risk_score']}")
        print(f"   总结: {risk_analysis['summary']}")
    else:
        print("⚠️ 未找到相关案件")
        
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n")

# 测试2: 巨潮资讯网爬虫
print("📢 测试2: 巨潮资讯网爬虫")
print("-" * 80)

try:
    from backend.dataflows.announcement.cninfo_crawler import get_cninfo_crawler
    
    crawler = get_cninfo_crawler()
    stock_code = "600519"
    
    print(f"获取股票: {stock_code} 的公告")
    print()
    
    # 获取公告
    announcements = crawler.get_company_announcements(stock_code, days=30)
    
    if announcements:
        print(f"✅ 获取到 {len(announcements)} 条公告")
        print()
        
        # 显示公告详情
        for i, ann in enumerate(announcements[:3], 1):
            print(f"{i}. {ann['title']}")
            print(f"   类型: {ann['type']}")
            print(f"   日期: {ann['publish_date']}")
            print(f"   重要性: {ann['importance']}")
            print()
        
        # 公告分析
        analysis = crawler.analyze_announcements(announcements)
        print("📊 公告分析:")
        print(f"   总公告数: {analysis['total']}")
        print(f"   重要公告: {analysis['important_count']}")
        print(f"   公告类型: {analysis['types']}")
        print(f"   总结: {analysis['summary']}")
    else:
        print("⚠️ 未获取到公告")
        
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
print("⚠️ = 无数据（使用模拟数据）")
print("❌ = 测试失败")
print()
print("注意:")
print("1. 当前使用模拟数据进行测试")
print("2. 实际使用需要实现真实的API调用")
print("3. 中国裁判文书网需要复杂的认证和反爬虫处理")
print("4. 巨潮资讯网API需要根据官方文档调整")
print()
print("下一步:")
print("1. 实现真实的API调用")
print("2. 处理认证和反爬虫")
print("3. 集成到统一API")
print()
