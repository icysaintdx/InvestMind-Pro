"""
测试综合股票数据获取
验证所有接口是否正常工作
"""

import asyncio
import json
from backend.dataflows.comprehensive_stock_data import get_comprehensive_service


async def test_comprehensive_data():
    """测试600519的综合数据获取"""
    
    print("="*60)
    print("测试综合股票数据获取服务")
    print("="*60)
    
    service = get_comprehensive_service()
    
    # 获取600519的全部数据
    result = service.get_all_stock_data('600519.SH')
    
    print("\n📊 数据摘要:")
    print("-"*60)
    for key, value in result['data_summary'].items():
        print(f"  {key}: {value}")
    
    print("\n\n💰 实时行情:")
    print("-"*60)
    print(json.dumps(result['realtime'], indent=2, ensure_ascii=False))
    
    print("\n\n🚫 停复牌信息:")
    print("-"*60)
    print(json.dumps(result['suspend'], indent=2, ensure_ascii=False))
    
    print("\n\n⚠️  ST状态:")
    print("-"*60)
    print(json.dumps(result['st_status'], indent=2, ensure_ascii=False))
    
    print("\n\n📈 财务数据:")
    print("-"*60)
    if result['financial'].get('income'):
        print(f"  利润表: {len(result['financial']['income'])}期")
        for item in result['financial']['income']:
            print(f"    {item['period']}: 营收{item['total_revenue']:.2f}万 净利{item['net_profit']:.2f}万")
    
    if result['financial'].get('balance'):
        print(f"  资产负债表: {len(result['financial']['balance'])}期")
        for item in result['financial']['balance']:
            print(f"    {item['period']}: 总资产{item['total_assets']:.2f}万 负债{item['total_liab']:.2f}万")
    
    if result['financial'].get('cashflow'):
        print(f"  现金流量表: {len(result['financial']['cashflow'])}期")
        for item in result['financial']['cashflow']:
            print(f"    {item['period']}: 经营现金流{item['operating_cash']:.2f}万")
    
    print("\n\n📰 新闻数据:")
    print("-"*60)
    print(f"  总计: {len(result['news'])}条")
    for i, news in enumerate(result['news'][:5], 1):
        print(f"  {i}. {news.get('title', '')[:50]}...")
    
    print("\n\n✅ 测试完成！")
    print("="*60)
    
    # 保存完整数据到文件
    with open('test_comprehensive_result.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    
    print("\n完整数据已保存到: test_comprehensive_result.json")


if __name__ == "__main__":
    asyncio.run(test_comprehensive_data())
