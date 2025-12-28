#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试市场数据接口可用性和速度
"""

import sys
import os
import time
import io

# 设置标准输出编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_api(name, func, *args, **kwargs):
    """测试单个API"""
    print(f"\n{'='*60}")
    print(f"测试: {name}")
    print('='*60)

    start = time.time()
    try:
        result = func(*args, **kwargs)
        elapsed = time.time() - start

        if result:
            if isinstance(result, list):
                print(f"✅ 成功! 返回 {len(result)} 条数据")
                if len(result) > 0:
                    print(f"   示例数据: {list(result[0].keys()) if isinstance(result[0], dict) else result[0]}")
            elif isinstance(result, dict):
                print(f"✅ 成功! 返回字典数据")
                print(f"   键: {list(result.keys())}")
            else:
                print(f"✅ 成功! 返回: {type(result)}")
        else:
            print(f"⚠️ 返回空数据")

        print(f"⏱️ 耗时: {elapsed:.2f}秒")
        return elapsed, True, result
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ 失败: {e}")
        print(f"⏱️ 耗时: {elapsed:.2f}秒")
        return elapsed, False, None


def main():
    print("="*60)
    print("市场数据接口测试")
    print("="*60)

    results = {}

    # 1. 测试 TDX Native Provider
    print("\n\n" + "="*60)
    print("【1】TDX Native Provider 测试")
    print("="*60)

    try:
        from dataflows.providers.tdx_native_provider import get_tdx_native_provider
        tdx = get_tdx_native_provider()

        # 测试可用性
        if tdx.is_available():
            print("✅ TDX Native Provider 可用")

            # 测试实时行情（单只）
            results['TDX-实时行情(单只)'] = test_api(
                "TDX 实时行情(单只股票)",
                tdx.get_realtime_quote, "000001"
            )

            # 测试批量行情
            results['TDX-批量行情'] = test_api(
                "TDX 批量行情(10只)",
                tdx.get_realtime_quotes,
                ["000001", "000002", "600000", "600036", "601318",
                 "000858", "002415", "300750", "601012", "600519"]
            )

            # 测试成交明细
            results['TDX-成交明细'] = test_api(
                "TDX 成交明细",
                tdx.get_transaction_data, "000001", 0, 100
            )

            # 测试盘口数据（检查是否有五档）
            print("\n检查盘口数据字段...")
            quote = tdx.get_realtime_quote("000001")
            if quote:
                bid_ask_fields = [k for k in quote.keys() if 'bid' in k or 'ask' in k]
                print(f"   盘口字段: {bid_ask_fields}")
        else:
            print("❌ TDX Native Provider 不可用")
    except Exception as e:
        print(f"❌ TDX Native Provider 初始化失败: {e}")

    # 2. 测试 AKShare 股票数据
    print("\n\n" + "="*60)
    print("【2】AKShare 股票数据测试")
    print("="*60)

    try:
        from dataflows.akshare.stock_data import get_stock_data
        stock_data = get_stock_data()

        # 测试全市场行情（用于涨跌幅排行、成交额排行）
        results['AKShare-全市场行情'] = test_api(
            "AKShare 全市场实时行情 (涨跌幅/成交额排行数据源)",
            stock_data.get_realtime_quotes
        )
    except Exception as e:
        print(f"❌ AKShare 股票数据测试失败: {e}")

    # 3. 测试 AKShare 板块数据
    print("\n\n" + "="*60)
    print("【3】AKShare 板块数据测试")
    print("="*60)

    try:
        from dataflows.akshare.sector_data import get_sector_data
        sector_data = get_sector_data()

        # 测试行业板块列表（热点板块）
        results['AKShare-行业板块列表'] = test_api(
            "AKShare 行业板块列表 (热点板块数据源)",
            sector_data.get_industry_list
        )

        # 测试板块成分股
        results['AKShare-板块成分股'] = test_api(
            "AKShare 板块成分股 (半导体)",
            sector_data.get_industry_cons, "半导体"
        )
    except Exception as e:
        print(f"❌ AKShare 板块数据测试失败: {e}")

    # 4. 测试 AKShare 热榜数据
    print("\n\n" + "="*60)
    print("【4】AKShare 热榜数据测试")
    print("="*60)

    try:
        from dataflows.akshare.hot_rank_data import get_hot_rank_data
        hot_rank = get_hot_rank_data()

        # 测试东财热门
        results['AKShare-东财热门'] = test_api(
            "AKShare 东财热门股票",
            hot_rank.get_eastmoney_hot_rank
        )
    except Exception as e:
        print(f"❌ AKShare 热榜数据测试失败: {e}")

    # 5. 测试直接调用 AKShare 获取五档盘口
    print("\n\n" + "="*60)
    print("【5】AKShare 五档盘口测试")
    print("="*60)

    try:
        import akshare as ak

        # 测试 stock_bid_ask_em（五档盘口）
        print("\n测试 ak.stock_bid_ask_em (五档盘口)...")
        start = time.time()
        try:
            df = ak.stock_bid_ask_em(symbol="000001")
            elapsed = time.time() - start
            if df is not None and not df.empty:
                print(f"✅ 成功! 返回 {len(df)} 行数据")
                print(f"   列: {list(df.columns)}")
                print(f"   数据:\n{df}")
                results['AKShare-五档盘口'] = (elapsed, True, df)
            else:
                print("⚠️ 返回空数据")
                results['AKShare-五档盘口'] = (elapsed, False, None)
            print(f"⏱️ 耗时: {elapsed:.2f}秒")
        except Exception as e:
            elapsed = time.time() - start
            print(f"❌ 失败: {e}")
            results['AKShare-五档盘口'] = (elapsed, False, None)
    except Exception as e:
        print(f"❌ AKShare 五档盘口测试失败: {e}")

    # 6. 测试概念板块
    print("\n\n" + "="*60)
    print("【6】AKShare 概念板块测试")
    print("="*60)

    try:
        import akshare as ak

        # 测试概念板块列表
        print("\n测试 ak.stock_board_concept_name_em (概念板块)...")
        start = time.time()
        try:
            df = ak.stock_board_concept_name_em()
            elapsed = time.time() - start
            if df is not None and not df.empty:
                print(f"✅ 成功! 返回 {len(df)} 个概念板块")
                print(f"   列: {list(df.columns)}")
                print(f"   前5个板块:\n{df.head()}")
                results['AKShare-概念板块'] = (elapsed, True, df)
            else:
                print("⚠️ 返回空数据")
            print(f"⏱️ 耗时: {elapsed:.2f}秒")
        except Exception as e:
            elapsed = time.time() - start
            print(f"❌ 失败: {e}")
    except Exception as e:
        print(f"❌ AKShare 概念板块测试失败: {e}")

    # 汇总结果
    print("\n\n" + "="*60)
    print("测试结果汇总（按速度排序）")
    print("="*60)

    # 按耗时排序
    sorted_results = sorted(
        [(k, v[0], v[1]) for k, v in results.items()],
        key=lambda x: x[1]
    )

    print(f"\n{'接口名称':<30} {'耗时(秒)':<10} {'状态':<10}")
    print("-"*50)
    for name, elapsed, success in sorted_results:
        status = "✅ 成功" if success else "❌ 失败"
        print(f"{name:<30} {elapsed:<10.2f} {status:<10}")

    print("\n" + "="*60)
    print("数据接口优先级建议")
    print("="*60)
    print("""
    1. 盘口信息: TDX (仅买一卖一) → 需扩展或使用 AKShare stock_bid_ask_em
    2. 热点板块: AKShare stock_board_industry_name_em ✅
    3. 板块成分股: AKShare stock_board_industry_cons_em ✅
    4. 成交额排行: AKShare stock_zh_a_spot_em 排序 ✅
    5. 成交明细: TDX get_transaction_data ✅
    6. 涨幅排名: AKShare stock_zh_a_spot_em 排序 ✅
    7. 跌幅排名: AKShare stock_zh_a_spot_em 排序 ✅
    """)


if __name__ == "__main__":
    main()
