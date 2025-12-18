"""
测试所有30+个数据接口
"""
import asyncio
import json
from datetime import datetime
from backend.dataflows.comprehensive_stock_data import get_comprehensive_service

async def test_all_interfaces():
    """测试所有接口"""
    print("=" * 80)
    print("🚀 开始测试所有30+个数据接口")
    print("=" * 80)
    
    # 使用贵州茅台作为测试样本
    ts_code = '600519.SH'
    
    service = get_comprehensive_service()
    
    print(f"\n📊 正在获取 {ts_code} 的全面数据...\n")
    
    try:
        result = service.get_all_stock_data(ts_code)
        
        # 打印数据摘要
        print("\n" + "=" * 80)
        print("📋 数据摘要")
        print("=" * 80)
        for idx, (key, value) in enumerate(result['data_summary'].items(), 1):
            print(f"{idx:2d}. {key:20s}: {value}")
        
        # 打印详细数据统计
        print("\n" + "=" * 80)
        print("📈 详细数据统计")
        print("=" * 80)
        
        # 1. 实时行情
        if result['realtime'].get('status') == 'success':
            data = result['realtime']['data']
            print(f"\n1️⃣  实时行情:")
            print(f"   名称: {data.get('name', 'N/A')}")
            print(f"   价格: {data.get('price', 'N/A')}")
            print(f"   涨跌幅: {data.get('pct_change', 'N/A')}%")
        
        # 2. 实时成交
        if result['realtime_tick'].get('status') == 'success':
            print(f"\n2️⃣  实时成交: {result['realtime_tick']['count']}条记录")
        
        # 3. 停复牌
        if result['suspend'].get('status') == 'has_suspend':
            print(f"\n3️⃣  停复牌: {result['suspend']['count']}条记录")
        
        # 4. ST状态
        if result['st_status'].get('is_st'):
            print(f"\n4️⃣  ST状态: {result['st_status']['message']}")
        
        # 5. 财务数据
        if result['financial'].get('status') == 'success':
            print(f"\n5️⃣  财务数据:")
            print(f"   利润表: {len(result['financial']['income'])}期")
            print(f"   资产负债表: {len(result['financial']['balance'])}期")
            print(f"   现金流量表: {len(result['financial']['cashflow'])}期")
        
        # 6. 审计意见
        if result['audit'].get('status') == 'success':
            count = result['audit'].get('count', len(result['audit'].get('data', [])))
            print(f"\n6️⃣  审计意见: {count}条")
        
        # 7. 业绩预告
        if result['forecast'].get('status') == 'success':
            print(f"\n7️⃣  业绩预告:")
            print(f"   预告: {len(result['forecast']['forecast'])}条")
            print(f"   快报: {len(result['forecast']['express'])}条")
        
        # 8. 分红送股
        if result['dividend'].get('status') == 'success':
            print(f"\n8️⃣  分红送股: {result['dividend']['count']}条")
        
        # 9. 限售解禁
        if result['restricted'].get('status') == 'success':
            print(f"\n9️⃣  限售解禁: {result['restricted']['count']}条")
        
        # 10. 股权质押
        if result['pledge'].get('status') == 'success':
            print(f"\n🔟 股权质押: 质押比例 {result['pledge']['pledge_ratio']}%")
        
        # 11. 股东增减持
        if result['holder_trade'].get('status') == 'success':
            print(f"\n1️⃣1️⃣ 股东增减持: {result['holder_trade']['count']}条")
        
        # 12. 龙虎榜
        if result['dragon_tiger'].get('status') == 'success':
            print(f"\n1️⃣2️⃣ 龙虎榜: {result['dragon_tiger']['count']}次")
        
        # 13. 涨跌停
        if result['limit_list'].get('status') == 'success':
            print(f"\n1️⃣3️⃣ 涨跌停: {result['limit_list']['count']}次")
        
        # 14. 融资融券
        if result['margin'].get('status') == 'success':
            print(f"\n1️⃣4️⃣ 融资融券: {result['margin']['count']}条记录")
            if result['margin'].get('latest'):
                latest = result['margin']['latest']
                print(f"   最新日期: {latest.get('trade_date', 'N/A')}")
        
        # 15. 公司基本信息
        if result['company_info'].get('status') == 'success':
            info = result['company_info']['data']
            print(f"\n1️⃣5️⃣ 公司基本信息:")
            print(f"   董事长: {info.get('chairman', 'N/A')}")
            print(f"   总经理: {info.get('manager', 'N/A')}")
            print(f"   注册资本: {info.get('reg_capital', 'N/A')}")
            print(f"   员工数: {info.get('employees', 'N/A')}")
        
        # 16. 管理层
        if result['managers'].get('status') == 'success':
            print(f"\n1️⃣6️⃣ 管理层: {result['managers']['count']}人")
        
        # 17. 管理层薪酬
        if result['manager_rewards'].get('status') == 'success':
            print(f"\n1️⃣7️⃣ 管理层薪酬: {result['manager_rewards']['count']}条记录")
        
        # 18. 主营业务构成
        if result['main_business'].get('status') == 'success':
            print(f"\n1️⃣8️⃣ 主营业务构成: {result['main_business']['count']}条")
        
        # 19. 沪深港通持股
        if result['hsgt_holding'].get('status') == 'success':
            print(f"\n1️⃣9️⃣ 沪深港通持股: {result['hsgt_holding']['count']}条")
        
        # 20. 上市公司公告
        if result['announcements'].get('status') == 'success':
            print(f"\n2️⃣0️⃣ 上市公司公告: {result['announcements']['count']}条")
        
        # 21. 新闻数据
        if result['news']:
            print(f"\n2️⃣1️⃣ 新闻数据: {len(result['news'])}条")
        
        # 保存完整结果
        output_file = 'test_all_interfaces_result.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        
        print("\n" + "=" * 80)
        print(f"✅ 测试完成！完整数据已保存到: {output_file}")
        print("=" * 80)
        
        # 统计接口成功率
        total_interfaces = 21
        success_count = len([v for v in result['data_summary'].values() if '✅' in str(v)])
        success_rate = (success_count / total_interfaces) * 100
        
        print(f"\n📊 接口成功率: {success_count}/{total_interfaces} ({success_rate:.1f}%)")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_all_interfaces())
