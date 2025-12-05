"""
测试修复后的股票数据适配器
按优先级测试: AKShare > 新浪财经 > 聚合数据 > Tushare > BaoStock
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from backend.dataflows.stock_data_adapter_fixed import StockDataAdapter

async def test_adapter():
    """测试股票数据适配器"""
    adapter = StockDataAdapter()
    test_symbol = "000001"  # 平安银行
    
    print("="*60)
    print("测试股票数据适配器")
    print("="*60)
    print(f"测试股票: {test_symbol}")
    print("数据源优先级: AKShare > 新浪财经 > 聚合数据 > Tushare > BaoStock")
    print("-"*60)
    
    # 测试同步方法
    print("\n1. 测试同步方法 get_stock_data():")
    try:
        result = adapter.get_stock_data(test_symbol)
        if result.get('success'):
            print(f"✅ 成功获取数据")
            print(f"   数据源: {result.get('data_source')}")
            print(f"   股票名称: {result.get('name')}")
            print(f"   当前价: ¥{result.get('price')}")
            print(f"   涨跌幅: {result.get('change')}%")
            print(f"   涨跌额: ¥{result.get('change_amount')}")
        else:
            print(f"❌ 获取失败: {result.get('error')}")
    except Exception as e:
        print(f"❌ 同步方法失败: {str(e)}")
    
    # 测试异步方法
    print("\n2. 测试异步方法 get_stock_data_async():")
    try:
        result = await adapter.get_stock_data_async(test_symbol)
        if result.get('success'):
            print(f"✅ 成功获取数据")
            print(f"   数据源: {result.get('data_source')}")
            print(f"   股票名称: {result.get('name')}")
            print(f"   当前价: ¥{result.get('price')}")
            print(f"   涨跌幅: {result.get('change')}%")
            print(f"   涨跌额: ¥{result.get('change_amount')}")
        else:
            print(f"❌ 获取失败: {result.get('error')}")
    except Exception as e:
        print(f"❌ 异步方法失败: {str(e)}")
    
    # 测试其他股票
    print("\n3. 测试其他股票代码:")
    test_codes = ["600519", "002230", "300750"]  # 贵州茅台、科大讯飞、宁德时代
    
    for code in test_codes:
        try:
            result = await adapter.get_stock_data_async(code)
            if result.get('success'):
                print(f"   {code}: {result.get('name')} - ¥{result.get('price')} ({result.get('data_source')})")
            else:
                print(f"   {code}: 获取失败")
        except Exception as e:
            print(f"   {code}: 异常 - {str(e)}")
    
    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_adapter())
