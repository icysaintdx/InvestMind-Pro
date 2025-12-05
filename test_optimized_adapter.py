"""
测试优化后的股票数据适配器
验证AKShare的稳定性
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
import time
from backend.dataflows.stock_data_adapter_optimized import StockDataAdapter

async def test_adapter():
    """测试优化后的适配器"""
    adapter = StockDataAdapter()
    
    print("="*70)
    print(" 测试优化后的股票数据适配器")
    print("="*70)
    print("优化策略：")
    print("1. 优先使用 stock_individual_info_em() - 单个股票信息")
    print("2. 备用 stock_zh_a_hist() - 历史数据（含最新）")
    print("3. 最后才用 stock_zh_a_spot_em() - 全市场数据")
    print("-"*70)
    
    test_stocks = {
        "000001": "平安银行",
        "600519": "贵州茅台",
        "002230": "科大讯飞",
        "300750": "宁德时代",
        "000002": "万科A"
    }
    
    # 测试每个股票
    success_count = 0
    akshare_count = 0
    total_time = 0
    
    print("\n【逐个测试】")
    print("-"*40)
    for code, expected_name in test_stocks.items():
        try:
            start = time.time()
            result = await adapter.get_stock_data_async(code)
            elapsed = time.time() - start
            total_time += elapsed
            
            if result.get('success'):
                success_count += 1
                source = result.get('data_source')
                if source == 'akshare':
                    akshare_count += 1
                    
                print(f"✅ {code} ({expected_name}): {result.get('name')} - ¥{result.get('price'):.2f}")
                print(f"   数据源: {source} (耗时: {elapsed:.2f}秒)")
                print(f"   涨跌幅: {result.get('change'):.2f}%")
            else:
                print(f"❌ {code}: 获取失败")
        except Exception as e:
            print(f"❌ {code}: 异常 - {str(e)[:50]}")
    
    # 批量测试性能
    print("\n【批量测试性能】")
    print("-"*40)
    start = time.time()
    tasks = [adapter.get_stock_data_async(code) for code in test_stocks.keys()]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    batch_time = time.time() - start
    
    batch_success = sum(1 for r in results if isinstance(r, dict) and r.get('success'))
    batch_akshare = sum(1 for r in results if isinstance(r, dict) and r.get('data_source') == 'akshare')
    
    print(f"批量获取 {len(test_stocks)} 只股票")
    print(f"总耗时: {batch_time:.2f}秒")
    print(f"平均耗时: {batch_time/len(test_stocks):.2f}秒/股")
    print(f"成功率: {batch_success}/{len(test_stocks)}")
    print(f"AKShare使用率: {batch_akshare}/{batch_success}")
    
    # 测试同步方法
    print("\n【测试同步方法】")
    print("-"*40)
    try:
        sync_adapter = StockDataAdapter()
        sync_result = sync_adapter.get_stock_data("000001")
        if sync_result.get('success'):
            print(f"✅ 同步方法成功")
            print(f"   数据源: {sync_result.get('data_source')}")
            print(f"   股票: {sync_result.get('name')}")
        else:
            print(f"❌ 同步方法失败")
    except Exception as e:
        print(f"❌ 同步方法异常: {str(e)[:100]}")
    
    # 总结
    print("\n" + "="*70)
    print(" 测试结果总结")
    print("="*70)
    print(f"✅ 成功获取: {success_count}/{len(test_stocks)}")
    print(f"📊 AKShare成功率: {akshare_count}/{success_count} ({akshare_count/success_count*100:.1f}%)")
    print(f"⏱️ 平均响应时间: {total_time/len(test_stocks):.2f}秒")
    
    if akshare_count == success_count:
        print("\n🎉 优秀！AKShare 100%成功率")
        print("   优化策略有效，AKShare现在很稳定")
    elif akshare_count > 0:
        print(f"\n✅ 良好！AKShare部分成功 ({akshare_count}/{success_count})")
        print("   自动降级机制正常工作")
    else:
        print("\n⚠️ 注意！AKShare完全失败")
        print("   但系统通过备用数据源正常工作")
    
    # 数据源统计
    print("\n【数据源使用统计】")
    source_stats = {}
    for r in results:
        if isinstance(r, dict) and r.get('success'):
            source = r.get('data_source')
            source_stats[source] = source_stats.get(source, 0) + 1
    
    for source, count in source_stats.items():
        print(f"   {source}: {count}次")

if __name__ == "__main__":
    asyncio.run(test_adapter())
