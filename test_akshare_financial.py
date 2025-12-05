#!/usr/bin/env python3
"""
AKShare财务数据测试脚本
测试为基本面分析师提供的财务数据接口
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from dataflows.akshare.financial_data import get_financial_data


def test_balance_sheet():
    """测试资产负债表"""
    print("\n" + "="*60)
    print("测试1: 资产负债表（贵州茅台 600519）")
    print("="*60)
    
    financial = get_financial_data()
    
    # 按报告期
    data = financial.get_balance_sheet_by_report("600519")
    if data:
        print(f"\n✅ 获取到 {len(data)} 期资产负债表（按报告期）")
        latest = data[0]
        print(f"\n最新一期 ({latest.get('REPORT_DATE')}):")
        print(f"  - 总资产: {latest.get('TOTAL_ASSETS')}")
        print(f"  - 总负债: {latest.get('TOTAL_LIABILITIES')}")
        print(f"  - 净资产: {latest.get('TOTAL_EQUITY')}")
        print(f"  - 资产负债率: {latest.get('ASSET_LIAB_RATIO')}")
    else:
        print("❌ 未获取到数据")


def test_profit_sheet():
    """测试利润表"""
    print("\n" + "="*60)
    print("测试2: 利润表（贵州茅台 600519）")
    print("="*60)
    
    financial = get_financial_data()
    
    # 按报告期
    data = financial.get_profit_sheet_by_report("600519")
    if data:
        print(f"\n✅ 获取到 {len(data)} 期利润表（按报告期）")
        latest = data[0]
        print(f"\n最新一期 ({latest.get('REPORT_DATE')}):")
        print(f"  - 营业收入: {latest.get('TOTAL_OPERATE_INCOME')}")
        print(f"  - 净利润: {latest.get('NETPROFIT')}")
        print(f"  - 毛利率: {latest.get('GROSS_PROFIT_RATIO')}")
        print(f"  - 净利率: {latest.get('NETPROFIT_RATIO')}")
    else:
        print("❌ 未获取到数据")
    
    # 按单季度
    print("\n" + "-"*60)
    data_q = financial.get_profit_sheet_by_quarterly("600519")
    if data_q:
        print(f"\n✅ 获取到 {len(data_q)} 季利润表（按单季度）")
        latest_q = data_q[0]
        print(f"\n最新一季 ({latest_q.get('REPORT_DATE')}):")
        print(f"  - 营业收入: {latest_q.get('TOTAL_OPERATE_INCOME')}")
        print(f"  - 净利润: {latest_q.get('NETPROFIT')}")


def test_cash_flow_sheet():
    """测试现金流量表"""
    print("\n" + "="*60)
    print("测试3: 现金流量表（贵州茅台 600519）")
    print("="*60)
    
    financial = get_financial_data()
    
    # 按报告期
    data = financial.get_cash_flow_sheet_by_report("600519")
    if data:
        print(f"\n✅ 获取到 {len(data)} 期现金流量表（按报告期）")
        latest = data[0]
        print(f"\n最新一期 ({latest.get('REPORT_DATE')}):")
        print(f"  - 经营活动现金流: {latest.get('OPERATE_CASH_FLOW_NET')}")
        print(f"  - 投资活动现金流: {latest.get('INVEST_CASH_FLOW_NET')}")
        print(f"  - 筹资活动现金流: {latest.get('FINANCE_CASH_FLOW_NET')}")
    else:
        print("❌ 未获取到数据")


def test_comprehensive_financial():
    """测试综合财务数据"""
    print("\n" + "="*60)
    print("测试4: 综合财务数据（贵州茅台 600519）")
    print("="*60)
    
    financial = get_financial_data()
    data = financial.get_comprehensive_financial_data("600519", period="report")
    
    print(f"\n✅ 综合财务数据:")
    print(f"  - 资产负债表: {len(data.get('balance_sheet', []))} 期")
    print(f"  - 利润表: {len(data.get('profit_sheet', []))} 期")
    print(f"  - 现金流量表: {len(data.get('cash_flow_sheet', []))} 期")


def test_latest_summary():
    """测试最新财务摘要"""
    print("\n" + "="*60)
    print("测试5: 最新财务摘要（贵州茅台 600519）")
    print("="*60)
    
    financial = get_financial_data()
    summary = financial.get_latest_financial_summary("600519")
    
    if summary:
        print(f"\n✅ 最新财务摘要 ({summary.get('报告期')}):")
        print(f"\n资产负债:")
        print(f"  - 总资产: {summary.get('总资产')}")
        print(f"  - 总负债: {summary.get('总负债')}")
        print(f"  - 净资产: {summary.get('净资产')}")
        print(f"  - 资产负债率: {summary.get('资产负债率')}")
        
        print(f"\n盈利能力:")
        print(f"  - 营业收入: {summary.get('营业收入')}")
        print(f"  - 净利润: {summary.get('净利润')}")
        print(f"  - 毛利率: {summary.get('毛利率')}")
        print(f"  - 净利率: {summary.get('净利率')}")
        
        print(f"\n现金流:")
        print(f"  - 经营活动现金流: {summary.get('经营活动现金流')}")
        print(f"  - 投资活动现金流: {summary.get('投资活动现金流')}")
        print(f"  - 筹资活动现金流: {summary.get('筹资活动现金流')}")
    else:
        print("❌ 未获取到数据")


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("AKShare财务数据测试")
    print("为基本面估值分析师提供数据支持")
    print("="*60)
    
    try:
        # 测试1: 资产负债表
        test_balance_sheet()
        
        # 测试2: 利润表
        test_profit_sheet()
        
        # 测试3: 现金流量表
        test_cash_flow_sheet()
        
        # 测试4: 综合财务数据
        test_comprehensive_financial()
        
        # 测试5: 最新财务摘要
        test_latest_summary()
        
        print("\n" + "="*60)
        print("✅ 所有测试完成")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
