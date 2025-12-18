"""
测试所有17个AKShare接口
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from backend.dataflows.comprehensive_stock_data import get_comprehensive_service

def test_akshare_interfaces():
    print("="*100)
    print("🧪 测试所有17个AKShare接口")
    print("="*100)
    
    service = get_comprehensive_service()
    ts_code = '600519.SH'
    
    # 测试所有AKShare接口
    akshare_tests = [
        ('stock_zh_a_st_em', lambda: service._get_st_status(ts_code), 'ST状态'),
        ('stock_dzjy_mrmx', lambda: service._get_block_trade(ts_code), '大宗交易'),
        ('stock_notice_report', lambda: service._get_announcements_akshare(ts_code), '公告'),
        ('stock_news_main_cx', lambda: service._get_news_sina(ts_code), '主力资金'),
        ('news_economic_baidu', lambda: service._get_market_news_cninfo(), '百度财经'),
        ('stock_zh_a_disclosure_report_cninfo', lambda: service._get_cninfo_news(), '巨潮资讯'),
        ('stock_news_em', lambda: service._get_news_data(ts_code), '东方财富新闻'),
        ('stock_zh_a_st_em (详情)', lambda: service._get_stock_st_info_ak(ts_code), 'ST详情'),
        ('stock_zh_a_stop_em', lambda: service._get_suspension_info_ak(ts_code), '停复牌'),
        ('stock_zh_a_pledge_ratio', lambda: service._get_pledge_detail_ak(ts_code), '质押详情'),
        ('stock_restricted_release_queue_sina', lambda: service._get_restricted_shares_ak(ts_code), '限售股'),
        ('stock_zh_a_gdhs', lambda: service._get_shareholder_change_ak(ts_code), '股东增减持'),
        ('stock_lhb_detail_em', lambda: service._get_dragon_tiger_ak(ts_code), '龙虎榜'),
        ('stock_yjyg_em', lambda: service._get_performance_forecast_ak(ts_code), '业绩预告'),
        ('stock_audit_result_cninfo', lambda: service._get_audit_opinion_ak(ts_code), '审计意见'),
        ('stock_margin_underlying_info_szse', lambda: service._get_margin_trading_ak(ts_code), '融资融券'),
        ('stock_industry_pe_ratio_cninfo', lambda: service._get_industry_policy(), '行业政策'),
    ]
    
    results = []
    success_count = 0
    
    for i, (interface_name, test_func, desc) in enumerate(akshare_tests, 1):
        print(f"\n{'='*100}")
        print(f"测试 {i}/17: {interface_name} ({desc})")
        print(f"{'='*100}")
        
        try:
            result = test_func()
            status = result.get('status', 'unknown')
            
            if status == 'success':
                count = result.get('count', len(result.get('data', [])))
                print(f"✅ 成功 - 获取到 {count} 条数据")
                success_count += 1
                results.append({
                    'interface': interface_name,
                    'desc': desc,
                    'status': '✅ 成功',
                    'count': count
                })
            elif status == 'no_data':
                message = result.get('message', '无数据')
                print(f"⚠️  无数据 - {message}")
                results.append({
                    'interface': interface_name,
                    'desc': desc,
                    'status': '⚠️ 无数据',
                    'message': message
                })
            else:
                message = result.get('message', '未知错误')
                print(f"❌ 失败 - {message}")
                results.append({
                    'interface': interface_name,
                    'desc': desc,
                    'status': '❌ 失败',
                    'message': message
                })
                
        except Exception as e:
            print(f"❌ 异常 - {str(e)[:100]}")
            results.append({
                'interface': interface_name,
                'desc': desc,
                'status': '❌ 异常',
                'error': str(e)[:100]
            })
    
    # 打印统计结果
    print("\n" + "="*100)
    print("📊 测试结果统计")
    print("="*100)
    
    print(f"\n{'序号':<5} {'接口名':<45} {'描述':<15} {'状态':<15} {'详情'}")
    print("-"*100)
    
    for i, r in enumerate(results, 1):
        detail = ''
        if '成功' in r['status']:
            detail = f"{r.get('count', 0)}条数据"
        elif '无数据' in r['status']:
            detail = r.get('message', '')
        else:
            detail = r.get('message', r.get('error', ''))
        
        print(f"{i:<5} {r['interface']:<45} {r['desc']:<15} {r['status']:<15} {detail}")
    
    print("\n" + "="*100)
    print(f"成功: {success_count}/17 ({success_count/17*100:.1f}%)")
    print("="*100)
    
    # 验证必须成功的接口
    critical_interfaces = ['stock_zh_a_st_em', 'stock_dzjy_mrmx', 'stock_notice_report', 
                          'news_economic_baidu', 'stock_zh_a_disclosure_report_cninfo']
    
    critical_success = sum(1 for r in results if r['interface'] in critical_interfaces and '成功' in r['status'])
    
    print(f"\n关键接口成功率: {critical_success}/{len(critical_interfaces)}")
    
    if critical_success == len(critical_interfaces):
        print("🎉 所有关键接口测试通过！")
    else:
        print("⚠️  部分关键接口失败，请检查！")

if __name__ == '__main__':
    test_akshare_interfaces()
