#!/usr/bin/env python3
"""
AKShare资金流向数据测试脚本
测试为资金流向分析师提供的数据接口
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from dataflows.akshare.fund_flow_data import get_fund_flow_data


def test_north_bound_realtime():
    """测试北向资金实时数据"""
    print("\n" + "="*60)
    print("测试1: 北向资金实时数据（分钟级）")
    print("="*60)
    
    fund_flow = get_fund_flow_data()
    data = fund_flow.get_hsgt_realtime("北向资金")
    
    if data:
        print(f"\n✅ 获取到 {len(data)} 条北向资金实时数据")
        print("\n最新5条数据:")
        for item in data[:5]:
            print(f"  {item.get('日期')} {item.get('时间')} - "
                  f"北向资金: {item.get('北向资金')}万元, "
                  f"沪股通: {item.get('沪股通')}万元, "
                  f"深股通: {item.get('深股通')}万元")
    else:
        print("❌ 未获取到数据")


def test_north_bound_history():
    """测试北向资金历史数据"""
    print("\n" + "="*60)
    print("测试2: 北向资金历史数据")
    print("="*60)
    
    fund_flow = get_fund_flow_data()
    data = fund_flow.get_hsgt_history("北向资金")
    
    if data:
        print(f"\n✅ 获取到 {len(data)} 条北向资金历史数据")
        print("\n最近5个交易日:")
        for item in data[:5]:
            print(f"  {item.get('日期')} - "
                  f"当日成交净买额: {item.get('当日成交净买额')}亿元, "
                  f"当日资金流入: {item.get('当日资金流入')}亿元")
    else:
        print("❌ 未获取到数据")


def test_north_bound_top10():
    """测试北向资金持股排名"""
    print("\n" + "="*60)
    print("测试3: 北向资金持股TOP10")
    print("="*60)
    
    fund_flow = get_fund_flow_data()
    data = fund_flow.get_hsgt_top10("北向", "今日排行")
    
    if data:
        print(f"\n✅ 获取到 {len(data)} 条持股排名")
        print("\nTOP10持股:")
        for i, item in enumerate(data[:10], 1):
            print(f"  {i}. {item.get('名称')} ({item.get('代码')}) - "
                  f"持股数: {item.get('持股数')}股, "
                  f"持股市值: {item.get('持股市值')}元")
    else:
        print("❌ 未获取到数据")


def test_individual_fund_flow():
    """测试个股资金流"""
    print("\n" + "="*60)
    print("测试4: 个股资金流向（即时）")
    print("="*60)
    
    fund_flow = get_fund_flow_data()
    data = fund_flow.get_individual_fund_flow("即时")
    
    if data:
        print(f"\n✅ 获取到 {len(data)} 条个股资金流向")
        print("\n资金净流入TOP10:")
        # 按净额排序
        sorted_data = sorted(data, key=lambda x: float(str(x.get('净额', '0')).replace('亿', '').replace('万', '').replace(',', '') or 0), reverse=True)
        for i, item in enumerate(sorted_data[:10], 1):
            print(f"  {i}. {item.get('股票简称')} ({item.get('股票代码')}) - "
                  f"净额: {item.get('净额')}, "
                  f"涨跌幅: {item.get('涨跌幅')}")
    else:
        print("❌ 未获取到数据")


def test_stock_fund_flow():
    """测试单个股票资金流向"""
    print("\n" + "="*60)
    print("测试5: 单个股票资金流向（贵州茅台 600519）")
    print("="*60)
    
    fund_flow = get_fund_flow_data()
    data = fund_flow.get_stock_fund_flow("600519")
    
    if data:
        print(f"\n✅ 获取到贵州茅台资金流向:")
        print(f"  股票名称: {data.get('股票简称')}")
        print(f"  最新价: {data.get('最新价')}")
        print(f"  涨跌幅: {data.get('涨跌幅')}")
        print(f"  流入资金: {data.get('流入资金')}")
        print(f"  流出资金: {data.get('流出资金')}")
        print(f"  净额: {data.get('净额')}")
        print(f"  成交额: {data.get('成交额')}")
    else:
        print("❌ 未获取到数据")


def test_industry_fund_flow():
    """测试行业资金流"""
    print("\n" + "="*60)
    print("测试6: 行业资金流向（即时）")
    print("="*60)
    
    fund_flow = get_fund_flow_data()
    data = fund_flow.get_industry_fund_flow("即时")
    
    if data:
        print(f"\n✅ 获取到 {len(data)} 条行业资金流向")
        print("\n资金净流入TOP5行业:")
        # 按净额排序
        sorted_data = sorted(data, key=lambda x: float(x.get('净额', 0)), reverse=True)
        for i, item in enumerate(sorted_data[:5], 1):
            print(f"  {i}. {item.get('行业')} - "
                  f"净额: {item.get('净额')}亿, "
                  f"涨跌幅: {item.get('行业-涨跌幅')}, "
                  f"领涨股: {item.get('领涨股')}")
    else:
        print("❌ 未获取到数据")


def test_concept_fund_flow():
    """测试概念资金流"""
    print("\n" + "="*60)
    print("测试7: 概念资金流向（即时）")
    print("="*60)
    
    fund_flow = get_fund_flow_data()
    data = fund_flow.get_concept_fund_flow("即时")
    
    if data:
        print(f"\n✅ 获取到 {len(data)} 条概念资金流向")
        print("\n资金净流入TOP5概念:")
        # 按净额排序
        sorted_data = sorted(data, key=lambda x: float(x.get('净额', 0)), reverse=True)
        for i, item in enumerate(sorted_data[:5], 1):
            print(f"  {i}. {item.get('行业')} - "
                  f"净额: {item.get('净额')}亿, "
                  f"涨跌幅: {item.get('行业-涨跌幅')}, "
                  f"领涨股: {item.get('领涨股')}")
    else:
        print("❌ 未获取到数据")


def test_margin_trading():
    """测试融资融券"""
    print("\n" + "="*60)
    print("测试8: 融资融券汇总（最近30天）")
    print("="*60)
    
    fund_flow = get_fund_flow_data()
    data = fund_flow.get_margin_trading_summary()
    
    if data:
        print(f"\n✅ 获取到 {len(data)} 条融资融券汇总")
        print("\n最近5个交易日:")
        for item in data[:5]:
            print(f"  {item.get('信用交易日期')} - "
                  f"融资余额: {item.get('融资余额')}, "
                  f"融券余量金额: {item.get('融券余量金额')}")
    else:
        print("❌ 未获取到数据")


def test_comprehensive_fund_flow():
    """测试综合资金流向分析"""
    print("\n" + "="*60)
    print("测试9: 综合资金流向分析（为资金流向分析师提供）")
    print("="*60)
    
    fund_flow = get_fund_flow_data()
    data = fund_flow.get_comprehensive_fund_flow("600519")
    
    print("\n✅ 综合资金流向数据:")
    print(f"  - 北向资金实时: {len(data.get('north_bound_realtime', []))} 条")
    print(f"  - 北向资金历史: {len(data.get('north_bound_history', []))} 条")
    print(f"  - 北向资金TOP10: {len(data.get('north_bound_top10', []))} 条")
    print(f"  - 行业资金流: {len(data.get('industry_flow', []))} 条")
    print(f"  - 概念资金流: {len(data.get('concept_flow', []))} 条")
    print(f"  - 个股资金流TOP50: {len(data.get('individual_flow_top', []))} 条")
    print(f"  - 融资融券汇总: {len(data.get('margin_summary', []))} 条")
    
    if data.get('stock_detail'):
        print(f"\n  个股详情（600519）:")
        fund_flow_detail = data['stock_detail'].get('fund_flow', {})
        if fund_flow_detail:
            print(f"    - 资金流向: 净额 {fund_flow_detail.get('净额')}")
        margin_detail = data['stock_detail'].get('margin', [])
        if margin_detail:
            print(f"    - 融资融券: {len(margin_detail)} 条历史记录")


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("AKShare资金流向数据测试")
    print("为资金流向分析师(Fund Flow Analyst)提供数据支持")
    print("="*60)
    
    try:
        # 测试1: 北向资金实时
        test_north_bound_realtime()
        
        # 测试2: 北向资金历史
        test_north_bound_history()
        
        # 测试3: 北向资金持股排名
        test_north_bound_top10()
        
        # 测试4: 个股资金流
        test_individual_fund_flow()
        
        # 测试5: 单个股票资金流向
        test_stock_fund_flow()
        
        # 测试6: 行业资金流
        test_industry_fund_flow()
        
        # 测试7: 概念资金流
        test_concept_fund_flow()
        
        # 测试8: 融资融券
        test_margin_trading()
        
        # 测试9: 综合资金流向分析
        test_comprehensive_fund_flow()
        
        print("\n" + "="*60)
        print("✅ 所有测试完成")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
