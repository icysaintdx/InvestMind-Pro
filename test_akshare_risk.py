#!/usr/bin/env python3
"""
测试AKShare风险数据
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.dataflows.risk.akshare_risk import get_akshare_risk
from backend.utils.logging_config import get_logger

logger = get_logger("test_akshare_risk")


def test_dishonest_persons():
    """测试失信被执行人查询"""
    logger.info("=" * 60)
    logger.info("测试1: 失信被执行人查询")
    logger.info("=" * 60)
    
    risk_data = get_akshare_risk()
    
    # 测试多个公司
    test_companies = [
        "贵州茅台",
        "乐视网",  # 可能有风险记录
        "中国平安",
    ]
    
    for company in test_companies:
        logger.info(f"\n{'='*50}")
        logger.info(f"测试公司: {company}")
        logger.info(f"{'='*50}")
        
        try:
            records = risk_data.get_dishonest_persons(company)
            
            if records:
                logger.info(f"✅ 找到 {len(records)} 条失信记录")
                # 显示第一条
                if len(records) > 0:
                    logger.info(f"\n第一条记录:")
                    for key, value in list(records[0].items())[:5]:
                        logger.info(f"  {key}: {value}")
            else:
                logger.info(f"✅ {company}无失信记录")
                
        except Exception as e:
            logger.error(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()


def test_executed_persons():
    """测试被执行人查询"""
    logger.info("\n" + "=" * 60)
    logger.info("测试2: 被执行人查询")
    logger.info("=" * 60)
    
    risk_data = get_akshare_risk()
    
    test_companies = [
        "贵州茅台",
        "乐视网",
        "中国平安",
    ]
    
    for company in test_companies:
        logger.info(f"\n{'='*50}")
        logger.info(f"测试公司: {company}")
        logger.info(f"{'='*50}")
        
        try:
            records = risk_data.get_executed_persons(company)
            
            if records:
                logger.info(f"✅ 找到 {len(records)} 条被执行记录")
                if len(records) > 0:
                    logger.info(f"\n第一条记录:")
                    for key, value in list(records[0].items())[:5]:
                        logger.info(f"  {key}: {value}")
            else:
                logger.info(f"✅ {company}无被执行记录")
                
        except Exception as e:
            logger.error(f"❌ 测试失败: {e}")


def test_lawsuits():
    """测试裁判文书查询"""
    logger.info("\n" + "=" * 60)
    logger.info("测试3: 裁判文书查询")
    logger.info("=" * 60)
    
    risk_data = get_akshare_risk()
    
    test_stocks = [
        ("600519.SH", "贵州茅台"),
        ("300104.SZ", "乐视网"),
        ("601318.SH", "中国平安"),
    ]
    
    for stock_code, company_name in test_stocks:
        logger.info(f"\n{'='*50}")
        logger.info(f"测试股票: {company_name} ({stock_code})")
        logger.info(f"{'='*50}")
        
        try:
            records = risk_data.get_lawsuits(stock_code)
            
            if records:
                logger.info(f"✅ 找到 {len(records)} 条裁判文书")
                if len(records) > 0:
                    logger.info(f"\n第一条记录:")
                    for key, value in list(records[0].items())[:5]:
                        logger.info(f"  {key}: {value}")
            else:
                logger.info(f"✅ {company_name}无裁判文书记录")
                
        except Exception as e:
            logger.error(f"❌ 测试失败: {e}")


def test_risk_analysis():
    """测试综合风险分析"""
    logger.info("\n" + "=" * 60)
    logger.info("测试4: 综合风险分析")
    logger.info("=" * 60)
    
    risk_data = get_akshare_risk()
    
    test_cases = [
        ("贵州茅台", "600519.SH"),
        ("乐视网", "300104.SZ"),
        ("中国平安", "601318.SH"),
    ]
    
    for company_name, stock_code in test_cases:
        logger.info(f"\n{'='*50}")
        logger.info(f"分析公司: {company_name} ({stock_code})")
        logger.info(f"{'='*50}")
        
        try:
            result = risk_data.analyze_risk(company_name, stock_code)
            
            logger.info(f"\n风险分析结果:")
            logger.info(f"  公司名称: {result['company_name']}")
            logger.info(f"  风险评分: {result['risk_score']}/100")
            logger.info(f"  风险等级: {result['risk_level']}")
            logger.info(f"  失信记录: {result['details']['dishonest_count']}条")
            logger.info(f"  被执行记录: {result['details']['executed_count']}条")
            logger.info(f"  裁判文书: {result['details']['lawsuit_count']}条")
            logger.info(f"  摘要: {result['summary']}")
            logger.info(f"  分析时间: {result['analysis_time']}")
            
        except Exception as e:
            logger.error(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()


def main():
    """主函数"""
    logger.info("🚀 开始测试AKShare风险数据")
    logger.info("=" * 60)
    
    try:
        # 运行所有测试
        test_dishonest_persons()
        test_executed_persons()
        test_lawsuits()
        test_risk_analysis()
        
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
