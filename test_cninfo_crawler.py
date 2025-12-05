#!/usr/bin/env python3
"""
测试巨潮资讯网爬虫
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.dataflows.announcement.cninfo_crawler import get_cninfo_crawler
from backend.utils.logging_config import get_logger

logger = get_logger("test_cninfo")


def test_get_announcements():
    """测试获取公告"""
    logger.info("=" * 60)
    logger.info("测试1: 获取公司公告")
    logger.info("=" * 60)
    
    crawler = get_cninfo_crawler()
    
    # 测试多个股票
    test_stocks = [
        ("600519.SH", "贵州茅台"),
        ("000001.SZ", "平安银行"),
        ("300750.SZ", "宁德时代"),
    ]
    
    for stock_code, company_name in test_stocks:
        logger.info(f"\n{'='*50}")
        logger.info(f"测试股票: {company_name} ({stock_code})")
        logger.info(f"{'='*50}")
        
        try:
            # 获取最近7天的公告
            announcements = crawler.get_company_announcements(
                stock_code=stock_code,
                days=7
            )
            
            if announcements:
                logger.info(f"✅ 成功获取 {len(announcements)} 条公告")
                
                # 显示前3条
                for i, ann in enumerate(announcements[:3], 1):
                    logger.info(f"\n公告 {i}:")
                    logger.info(f"  标题: {ann.get('title', 'N/A')}")
                    logger.info(f"  类型: {ann.get('type', 'N/A')}")
                    logger.info(f"  日期: {ann.get('publish_date', 'N/A')}")
                    logger.info(f"  重要性: {ann.get('importance', 'N/A')}")
                    logger.info(f"  URL: {ann.get('url', 'N/A')[:80]}...")
            else:
                logger.warning(f"⚠️ 未获取到公告数据")
                
        except Exception as e:
            logger.error(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()


def test_filter_important():
    """测试过滤重要公告"""
    logger.info("\n" + "=" * 60)
    logger.info("测试2: 过滤重要公告")
    logger.info("=" * 60)
    
    crawler = get_cninfo_crawler()
    
    # 获取公告
    announcements = crawler.get_company_announcements(
        stock_code="600519.SH",
        days=30
    )
    
    if announcements:
        # 过滤重要公告
        important = crawler.filter_important_announcements(announcements)
        
        logger.info(f"\n总公告数: {len(announcements)}")
        logger.info(f"重要公告数: {len(important)}")
        
        if important:
            logger.info("\n重要公告列表:")
            for i, ann in enumerate(important[:5], 1):
                logger.info(f"\n{i}. {ann.get('title', 'N/A')}")
                logger.info(f"   类型: {ann.get('type', 'N/A')}")
                logger.info(f"   日期: {ann.get('publish_date', 'N/A')}")
    else:
        logger.warning("⚠️ 无公告数据可供过滤")


def test_analyze_announcements():
    """测试公告分析"""
    logger.info("\n" + "=" * 60)
    logger.info("测试3: 公告分析")
    logger.info("=" * 60)
    
    crawler = get_cninfo_crawler()
    
    # 获取公告
    announcements = crawler.get_company_announcements(
        stock_code="600519.SH",
        days=30
    )
    
    if announcements:
        # 分析公告
        analysis = crawler.analyze_announcements(announcements)
        
        logger.info(f"\n分析结果:")
        logger.info(f"  总公告数: {analysis.get('total', 0)}")
        logger.info(f"  重要公告数: {analysis.get('important_count', 0)}")
        logger.info(f"  摘要: {analysis.get('summary', 'N/A')}")
        
        logger.info(f"\n公告类型分布:")
        for ann_type, count in analysis.get('types', {}).items():
            logger.info(f"  {ann_type}: {count}条")
    else:
        logger.warning("⚠️ 无公告数据可供分析")


def test_announcement_types():
    """测试不同公告类型"""
    logger.info("\n" + "=" * 60)
    logger.info("测试4: 不同公告类型")
    logger.info("=" * 60)
    
    crawler = get_cninfo_crawler()
    
    # 测试不同类型
    types_to_test = [
        None,  # 全部
        # 可以添加具体类型代码
    ]
    
    for ann_type in types_to_test:
        type_name = ann_type if ann_type else "全部类型"
        logger.info(f"\n测试类型: {type_name}")
        
        announcements = crawler.get_company_announcements(
            stock_code="600519.SH",
            days=30,
            announcement_type=ann_type
        )
        
        logger.info(f"获取到 {len(announcements)} 条公告")


def main():
    """主函数"""
    logger.info("🚀 开始测试巨潮资讯网爬虫")
    logger.info("=" * 60)
    
    try:
        # 运行所有测试
        test_get_announcements()
        test_filter_important()
        test_analyze_announcements()
        test_announcement_types()
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ 所有测试完成")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ 测试过程出错: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
