"""
测试数据流监控功能
测试停复牌监控、ST股票监控、实时数据和风险分析
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.dataflows.risk import (
    check_suspend_status,
    is_st_stock,
    get_stock_realtime_quote,
    analyze_stock_risk,
    get_today_suspended_stocks,
    get_today_st_stocks
)


def test_suspend_monitor():
    """测试停复牌监控"""
    print("\n" + "="*60)
    print("【1】测试停复牌监控")
    print("="*60)
    
    # 测试股票代码
    test_codes = ['600519.SH', '000001.SZ', '600036.SH']
    
    for code in test_codes:
        print(f"\n检查 {code} 的停复牌状态...")
        try:
            status = check_suspend_status(code)
            print(f"✅ 停复牌状态: {status.get('latest_status')}")
            print(f"   是否停牌: {status.get('is_suspended')}")
            print(f"   停牌次数: {status.get('suspend_count')}")
            print(f"   复牌次数: {status.get('resume_count')}")
            
            if status.get('suspend_records'):
                print(f"   最近记录: {status['suspend_records'][:3]}")
        except Exception as e:
            print(f"❌ 检查失败: {e}")
    
    # 获取今日停牌股票
    print("\n获取今日停牌股票列表...")
    try:
        suspended = get_today_suspended_stocks()
        if suspended:
            print(f"✅ 今日停牌股票: {len(suspended)}只")
            print(f"   前5只: {suspended[:5]}")
        else:
            print("ℹ️ 今日无停牌股票")
    except Exception as e:
        print(f"❌ 获取失败: {e}")


def test_st_monitor():
    """测试ST股票监控"""
    print("\n" + "="*60)
    print("【2】测试ST股票监控")
    print("="*60)
    
    # 测试股票代码
    test_codes = ['600519.SH', '000001.SZ']
    
    for code in test_codes:
        print(f"\n检查 {code} 是否为ST股票...")
        try:
            is_st = is_st_stock(code)
            print(f"{'⚠️ 是ST股票' if is_st else '✅ 非ST股票'}")
        except Exception as e:
            print(f"❌ 检查失败: {e}")
    
    # 获取今日ST股票
    print("\n获取今日ST股票列表...")
    try:
        st_stocks = get_today_st_stocks()
        if st_stocks:
            print(f"✅ 今日ST股票: {len(st_stocks)}只")
            print(f"   前10只: {st_stocks[:10]}")
        else:
            print("ℹ️ 今日无ST股票数据或积分不足")
    except Exception as e:
        print(f"❌ 获取失败: {e}")


def test_realtime_data():
    """测试实时数据"""
    print("\n" + "="*60)
    print("【3】测试实时数据获取")
    print("="*60)
    
    test_code = '600519.SH'  # 贵州茅台
    
    print(f"\n获取 {test_code} 的实时行情...")
    try:
        data = get_stock_realtime_quote(test_code)
        if data:
            print(f"✅ 实时行情获取成功:")
            print(f"   股票名称: {data.get('name')}")
            print(f"   当前价格: {data.get('price')}")
            print(f"   涨跌幅: {data.get('change_pct')}%")
            print(f"   成交量: {data.get('volume')}")
            print(f"   成交额: {data.get('amount')}")
            print(f"   买卖比: {data.get('buy_sell_pressure')}")
        else:
            print("⚠️ 未获取到实时数据")
    except Exception as e:
        print(f"❌ 获取失败: {e}")


def test_risk_analysis():
    """测试风险分析"""
    print("\n" + "="*60)
    print("【4】测试综合风险分析")
    print("="*60)
    
    test_codes = ['600519.SH', '000001.SZ']
    
    for code in test_codes:
        print(f"\n分析 {code} 的风险...")
        try:
            result = analyze_stock_risk(code, sentiment_score=55)
            
            print(f"✅ 风险分析完成:")
            print(f"   风险等级: {result.get('risk_level')}")
            print(f"   风险得分: {result.get('risk_score')}/100")
            
            risk_factors = result.get('risk_factors', {})
            
            # 停复牌风险
            suspend = risk_factors.get('suspend_risk', {})
            print(f"   停复牌风险: {suspend.get('level')} (得分:{suspend.get('score')})")
            
            # ST风险
            st = risk_factors.get('st_risk', {})
            print(f"   ST风险: {st.get('level')} (得分:{st.get('score')})")
            
            # 舆情风险
            sentiment = risk_factors.get('sentiment_risk', {})
            print(f"   舆情风险: {sentiment.get('level')} (得分:{sentiment.get('score')})")
            
            # 实时风险
            realtime = risk_factors.get('realtime_risk', {})
            if realtime and realtime.get('level') != 'unknown':
                print(f"   实时风险: {realtime.get('level')} (得分:{realtime.get('score')})")
            
            # 风险警告
            warnings = result.get('warnings', [])
            if warnings:
                print(f"   ⚠️ 风险警告:")
                for warning in warnings:
                    print(f"      - {warning}")
                    
        except Exception as e:
            print(f"❌ 分析失败: {e}")


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("数据流监控功能测试")
    print("="*60)
    print("\n注意: 需要配置TUSHARE_TOKEN环境变量")
    print("部分功能需要Tushare积分权限")
    
    try:
        # 1. 测试停复牌监控
        test_suspend_monitor()
        
        # 2. 测试ST股票监控
        test_st_monitor()
        
        # 3. 测试实时数据
        test_realtime_data()
        
        # 4. 测试风险分析
        test_risk_analysis()
        
        print("\n" + "="*60)
        print("✅ 测试完成!")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试已中断")
    except Exception as e:
        print(f"\n\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
