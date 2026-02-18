#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻舆情接口状态检测脚本
检测项目中实际使用的所有新闻/舆情相关接口的可用性

运行方式: python test_news_interfaces.py
"""

import os
import sys
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 接口测试结果
test_results = []


def log_result(
    platform: str,
    interface_name: str,
    akshare_func: str,
    data_type: str,
    sub_type: str,
    module_usage: str,
    status: str,
    count: int = 0,
    error: str = "",
):
    """记录测试结果"""
    test_results.append(
        {
            "平台": platform,
            "接口名称": interface_name,
            "AKShare函数": akshare_func,
            "数据类型": data_type,
            "二级分类": sub_type,
            "使用模块": module_usage,
            "状态": status,
            "数据量": count,
            "错误信息": error,
        }
    )

    status_icon = "✅" if status == "正常" else "❌"
    print(f"{status_icon} [{platform}] {interface_name}: {status} (数据量: {count})")
    if error:
        print(f"   错误: {error}")


def test_akshare_interfaces():
    """测试AKShare新闻接口"""
    print("\n" + "=" * 60)
    print("📊 AKShare 新闻接口测试")
    print("=" * 60)

    try:
        import akshare as ak

        print(f"AKShare版本: {ak.__version__}")
    except ImportError:
        print("❌ AKShare未安装")
        return

    # 1. 东方财富个股新闻 - stock_news_em
    print("\n--- 个股新闻接口 ---")
    try:
        df = ak.stock_news_em(symbol="600519")
        if df is not None and not df.empty:
            log_result(
                "AKShare",
                "东方财富个股新闻",
                "ak.stock_news_em(symbol)",
                "个股数据",
                "新闻",
                "个股详情模态框、多源新闻聚合器",
                "正常",
                len(df),
            )
        else:
            log_result(
                "AKShare",
                "东方财富个股新闻",
                "ak.stock_news_em(symbol)",
                "个股数据",
                "新闻",
                "个股详情模态框、多源新闻聚合器",
                "无数据",
                0,
            )
    except Exception as e:
        log_result(
            "AKShare",
            "东方财富个股新闻",
            "ak.stock_news_em(symbol)",
            "个股数据",
            "新闻",
            "个股详情模态框、多源新闻聚合器",
            "异常",
            0,
            str(e),
        )

    # 2. 东方财富全球资讯 - stock_info_global_em
    print("\n--- 市场新闻接口 ---")
    try:
        df = ak.stock_info_global_em()
        if df is not None and not df.empty:
            log_result(
                "AKShare",
                "东方财富全球资讯",
                "ak.stock_info_global_em()",
                "市场数据",
                "新闻",
                "新闻中心、数据流实时新闻流",
                "正常",
                len(df),
            )
        else:
            log_result(
                "AKShare",
                "东方财富全球资讯",
                "ak.stock_info_global_em()",
                "市场数据",
                "新闻",
                "新闻中心、数据流实时新闻流",
                "无数据",
                0,
            )
    except Exception as e:
        log_result(
            "AKShare",
            "东方财富全球资讯",
            "ak.stock_info_global_em()",
            "市场数据",
            "新闻",
            "新闻中心、数据流实时新闻流",
            "异常",
            0,
            str(e),
        )

    # 3. 财联社电报 - stock_info_global_cls
    try:
        df = ak.stock_info_global_cls()
        if df is not None and not df.empty:
            log_result(
                "AKShare",
                "财联社电报",
                "ak.stock_info_global_cls()",
                "市场数据",
                "快讯",
                "新闻中心、数据流实时新闻流、多源新闻聚合器",
                "正常",
                len(df),
            )
        else:
            log_result(
                "AKShare",
                "财联社电报",
                "ak.stock_info_global_cls()",
                "市场数据",
                "快讯",
                "新闻中心、数据流实时新闻流、多源新闻聚合器",
                "无数据",
                0,
            )
    except Exception as e:
        log_result(
            "AKShare",
            "财联社电报",
            "ak.stock_info_global_cls()",
            "市场数据",
            "快讯",
            "新闻中心、数据流实时新闻流、多源新闻聚合器",
            "异常",
            0,
            str(e),
        )

    # 4. 富途牛牛 - stock_info_global_futu
    try:
        df = ak.stock_info_global_futu()
        if df is not None and not df.empty:
            log_result(
                "AKShare",
                "富途牛牛全球资讯",
                "ak.stock_info_global_futu()",
                "市场数据",
                "新闻",
                "新闻中心、数据流实时新闻流",
                "正常",
                len(df),
            )
        else:
            log_result(
                "AKShare",
                "富途牛牛全球资讯",
                "ak.stock_info_global_futu()",
                "市场数据",
                "新闻",
                "新闻中心、数据流实时新闻流",
                "无数据",
                0,
            )
    except Exception as e:
        log_result(
            "AKShare",
            "富途牛牛全球资讯",
            "ak.stock_info_global_futu()",
            "市场数据",
            "新闻",
            "新闻中心、数据流实时新闻流",
            "异常",
            0,
            str(e),
        )

    # 5. 同花顺 - stock_info_global_ths
    try:
        df = ak.stock_info_global_ths()
        if df is not None and not df.empty:
            log_result(
                "AKShare",
                "同花顺全球资讯",
                "ak.stock_info_global_ths()",
                "市场数据",
                "新闻",
                "新闻中心、数据流实时新闻流",
                "正常",
                len(df),
            )
        else:
            log_result(
                "AKShare",
                "同花顺全球资讯",
                "ak.stock_info_global_ths()",
                "市场数据",
                "新闻",
                "新闻中心、数据流实时新闻流",
                "无数据",
                0,
            )
    except Exception as e:
        log_result(
            "AKShare",
            "同花顺全球资讯",
            "ak.stock_info_global_ths()",
            "市场数据",
            "新闻",
            "新闻中心、数据流实时新闻流",
            "异常",
            0,
            str(e),
        )

    # 6. 新浪财经 - stock_info_global_sina
    try:
        df = ak.stock_info_global_sina()
        if df is not None and not df.empty:
            log_result(
                "AKShare",
                "新浪财经快讯",
                "ak.stock_info_global_sina()",
                "市场数据",
                "快讯",
                "新闻中心、数据流实时新闻流",
                "正常",
                len(df),
            )
        else:
            log_result(
                "AKShare",
                "新浪财经快讯",
                "ak.stock_info_global_sina()",
                "市场数据",
                "快讯",
                "新闻中心、数据流实时新闻流",
                "无数据",
                0,
            )
    except Exception as e:
        log_result(
            "AKShare",
            "新浪财经快讯",
            "ak.stock_info_global_sina()",
            "市场数据",
            "快讯",
            "新闻中心、数据流实时新闻流",
            "异常",
            0,
            str(e),
        )

    # 7. 微博热议 - stock_js_weibo_report
    print("\n--- 社交媒体接口 ---")
    try:
        df = ak.stock_js_weibo_report()
        if df is not None and not df.empty:
            log_result(
                "AKShare",
                "微博股票热议",
                "ak.stock_js_weibo_report()",
                "市场数据",
                "社交热议",
                "新闻中心、数据流实时新闻流、新闻舆情面板",
                "正常",
                len(df),
            )
        else:
            log_result(
                "AKShare",
                "微博股票热议",
                "ak.stock_js_weibo_report()",
                "市场数据",
                "社交热议",
                "新闻中心、数据流实时新闻流、新闻舆情面板",
                "无数据",
                0,
            )
    except Exception as e:
        log_result(
            "AKShare",
            "微博股票热议",
            "ak.stock_js_weibo_report()",
            "市场数据",
            "社交热议",
            "新闻中心、数据流实时新闻流、新闻舆情面板",
            "异常",
            0,
            str(e),
        )

    # 8. 财经早餐 - stock_info_cjzc_em
    print("\n--- 财经资讯接口 ---")
    try:
        df = ak.stock_info_cjzc_em()
        if df is not None and not df.empty:
            log_result(
                "AKShare",
                "东方财富财经早餐",
                "ak.stock_info_cjzc_em()",
                "市场数据",
                "财经早餐",
                "新闻中心、数据流实时新闻流",
                "正常",
                len(df),
            )
        else:
            log_result(
                "AKShare",
                "东方财富财经早餐",
                "ak.stock_info_cjzc_em()",
                "市场数据",
                "财经早餐",
                "新闻中心、数据流实时新闻流",
                "无数据",
                0,
            )
    except Exception as e:
        log_result(
            "AKShare",
            "东方财富财经早餐",
            "ak.stock_info_cjzc_em()",
            "市场数据",
            "财经早餐",
            "新闻中心、数据流实时新闻流",
            "异常",
            0,
            str(e),
        )

    # 9. 新闻联播 - news_cctv
    try:
        today = datetime.now().strftime("%Y%m%d")
        df = ak.news_cctv(date=today)
        if df is not None and not df.empty:
            log_result(
                "AKShare",
                "央视新闻联播",
                "ak.news_cctv(date)",
                "市场数据",
                "政策新闻",
                "新闻中心、数据流实时新闻流",
                "正常",
                len(df),
            )
        else:
            log_result(
                "AKShare",
                "央视新闻联播",
                "ak.news_cctv(date)",
                "市场数据",
                "政策新闻",
                "新闻中心、数据流实时新闻流",
                "无数据",
                0,
            )
    except Exception as e:
        log_result(
            "AKShare",
            "央视新闻联播",
            "ak.news_cctv(date)",
            "市场数据",
            "政策新闻",
            "新闻中心、数据流实时新闻流",
            "异常",
            0,
            str(e),
        )

    # 10. 百度财经 - news_economic_baidu
    try:
        df = ak.news_economic_baidu()
        if df is not None and not df.empty:
            log_result(
                "AKShare",
                "百度财经日历",
                "ak.news_economic_baidu()",
                "市场数据",
                "财经日历",
                "新闻中心、数据流实时新闻流、多源新闻聚合器",
                "正常",
                len(df),
            )
        else:
            log_result(
                "AKShare",
                "百度财经日历",
                "ak.news_economic_baidu()",
                "市场数据",
                "财经日历",
                "新闻中心、数据流实时新闻流、多源新闻聚合器",
                "无数据",
                0,
            )
    except Exception as e:
        log_result(
            "AKShare",
            "百度财经日历",
            "ak.news_economic_baidu()",
            "市场数据",
            "财经日历",
            "新闻中心、数据流实时新闻流、多源新闻聚合器",
            "异常",
            0,
            str(e),
        )


async def test_cninfo_interfaces():
    """测试巨潮资讯接口"""
    print("\n" + "=" * 60)
    print("📊 巨潮资讯 官方API 测试")
    print("=" * 60)

    try:
        from backend.dataflows.announcement.cninfo_api import (
            get_cninfo_api_client,
            CninfoConfig,
        )

        if not CninfoConfig.is_configured():
            print("⚠️ 巨潮API未配置 (需要 CNINFO_ACCESS_KEY 和 CNINFO_ACCESS_SECRET)")
            log_result(
                "巨潮资讯",
                "公告基本信息",
                "p_info3015",
                "个股数据",
                "公告",
                "新闻中心、个股详情模态框",
                "未配置",
                0,
                "需要配置API密钥",
            )
            log_result(
                "巨潮资讯",
                "上市状态变动",
                "p_stock2117",
                "市场数据",
                "公告",
                "数据流实时新闻流",
                "未配置",
                0,
                "需要配置API密钥",
            )
            log_result(
                "巨潮资讯",
                "高管变动",
                "p_stock2102",
                "市场数据",
                "公告",
                "数据流实时新闻流",
                "未配置",
                0,
                "需要配置API密钥",
            )
            return

        client = get_cninfo_api_client()

        # 1. 公告基本信息 - p_info3015
        print("\n--- 公告接口 ---")
        try:
            result = await client.get_announcement_info(
                start_date=(datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
                end_date=datetime.now().strftime("%Y-%m-%d"),
                page_size=10,
            )
            if result.get("success") and result.get("data"):
                log_result(
                    "巨潮资讯",
                    "公告基本信息",
                    "p_info3015",
                    "市场数据",
                    "公告",
                    "新闻中心、个股详情模态框",
                    "正常",
                    len(result["data"]),
                )
            else:
                log_result(
                    "巨潮资讯",
                    "公告基本信息",
                    "p_info3015",
                    "市场数据",
                    "公告",
                    "新闻中心、个股详情模态框",
                    "无数据",
                    0,
                    result.get("error", ""),
                )
        except Exception as e:
            log_result(
                "巨潮资讯",
                "公告基本信息",
                "p_info3015",
                "市场数据",
                "公告",
                "新闻中心、个股详情模态框",
                "异常",
                0,
                str(e),
            )

        # 2. 上市状态变动 - p_stock2117
        try:
            result = await client.get_listing_status_changes()
            if result.get("success") and result.get("data"):
                log_result(
                    "巨潮资讯",
                    "上市状态变动",
                    "p_stock2117",
                    "市场数据",
                    "公告",
                    "数据流实时新闻流",
                    "正常",
                    len(result["data"]),
                )
            else:
                log_result(
                    "巨潮资讯",
                    "上市状态变动",
                    "p_stock2117",
                    "市场数据",
                    "公告",
                    "数据流实时新闻流",
                    "无数据",
                    0,
                    result.get("error", ""),
                )
        except Exception as e:
            log_result(
                "巨潮资讯",
                "上市状态变动",
                "p_stock2117",
                "市场数据",
                "公告",
                "数据流实时新闻流",
                "异常",
                0,
                str(e),
            )

        # 3. 高管变动 - p_stock2102
        try:
            result = await client.get_management_personnel(
                ["000001", "600519"], state=1
            )
            if result.get("success") and result.get("data"):
                log_result(
                    "巨潮资讯",
                    "高管变动",
                    "p_stock2102",
                    "市场数据",
                    "公告",
                    "数据流实时新闻流",
                    "正常",
                    len(result["data"]),
                )
            else:
                log_result(
                    "巨潮资讯",
                    "高管变动",
                    "p_stock2102",
                    "市场数据",
                    "公告",
                    "数据流实时新闻流",
                    "无数据",
                    0,
                    result.get("error", ""),
                )
        except Exception as e:
            log_result(
                "巨潮资讯",
                "高管变动",
                "p_stock2102",
                "市场数据",
                "公告",
                "数据流实时新闻流",
                "异常",
                0,
                str(e),
            )

        await client.close()

    except ImportError as e:
        print(f"❌ 导入巨潮API模块失败: {e}")
    except Exception as e:
        print(f"❌ 巨潮API测试失败: {e}")


def test_tushare_interfaces():
    """测试Tushare新闻接口"""
    print("\n" + "=" * 60)
    print("📊 Tushare 新闻接口测试")
    print("=" * 60)

    tushare_token = os.getenv("TUSHARE_TOKEN", "")
    if not tushare_token:
        print("⚠️ Tushare未配置 (需要 TUSHARE_TOKEN)")
        log_result(
            "Tushare",
            "新闻聚合接口",
            "news_list API",
            "市场数据",
            "新闻",
            "多源新闻聚合器(可选)",
            "未配置",
            0,
            "需要配置TUSHARE_TOKEN",
        )
        return

    try:
        import tushare as ts

        ts.set_token(tushare_token)
        pro = ts.pro_api()

        # Tushare新闻接口需要5000积分，大多数用户无法使用
        # 这里只测试是否能连接
        print("ℹ️ Tushare新闻接口需要5000积分，跳过实际测试")
        log_result(
            "Tushare",
            "新闻聚合接口",
            "news_list API",
            "市场数据",
            "新闻",
            "多源新闻聚合器(可选)",
            "需要积分",
            0,
            "需要5000积分",
        )

    except ImportError:
        print("❌ Tushare未安装")
        log_result(
            "Tushare",
            "新闻聚合接口",
            "news_list API",
            "市场数据",
            "新闻",
            "多源新闻聚合器(可选)",
            "未安装",
            0,
            "需要安装tushare",
        )
    except Exception as e:
        log_result(
            "Tushare",
            "新闻聚合接口",
            "news_list API",
            "市场数据",
            "新闻",
            "多源新闻聚合器(可选)",
            "异常",
            0,
            str(e),
        )


def generate_summary_report():
    """生成汇总报告"""
    print("\n" + "=" * 80)
    print("📋 新闻舆情接口汇总报告")
    print("=" * 80)
    print(f"检测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 80)

    # 统计
    total = len(test_results)
    normal = sum(1 for r in test_results if r["状态"] == "正常")
    abnormal = sum(1 for r in test_results if r["状态"] in ["异常", "无数据"])
    unconfigured = sum(
        1 for r in test_results if r["状态"] in ["未配置", "未安装", "需要积分"]
    )

    print(f"\n📊 统计概览:")
    print(f"   总接口数: {total}")
    print(f"   ✅ 正常: {normal}")
    print(f"   ❌ 异常/无数据: {abnormal}")
    print(f"   ⚠️ 未配置/需要权限: {unconfigured}")

    # 按平台分组
    print(f"\n📋 接口详情:")
    print("-" * 80)

    # 表头
    header = f"{'平台':<12} | {'接口名称':<20} | {'数据类型':<10} | {'二级分类':<10} | {'状态':<8} | {'数据量':<6}"
    print(header)
    print("-" * 80)

    for r in test_results:
        row = f"{r['平台']:<12} | {r['接口名称']:<20} | {r['数据类型']:<10} | {r['二级分类']:<10} | {r['状态']:<8} | {r['数据量']:<6}"
        print(row)

    print("-" * 80)

    # 使用模块汇总
    print(f"\n📍 使用模块分布:")
    modules = {}
    for r in test_results:
        for module in r["使用模块"].split("、"):
            module = module.strip()
            if module not in modules:
                modules[module] = []
            modules[module].append(r["接口名称"])

    for module, interfaces in modules.items():
        print(f"   {module}: {len(interfaces)}个接口")
        for iface in interfaces:
            print(f"      - {iface}")

    # 保存JSON报告
    report = {
        "检测时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "统计": {
            "总接口数": total,
            "正常": normal,
            "异常": abnormal,
            "未配置": unconfigured,
        },
        "接口详情": test_results,
    }

    report_path = os.path.join(os.path.dirname(__file__), "news_interface_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n📄 详细报告已保存至: {report_path}")


async def main():
    """主函数"""
    # 设置控制台编码
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    print("=" * 80)
    print("[检测] InvestMind Pro 新闻舆情接口状态检测")
    print("=" * 80)

    # 1. 测试AKShare接口
    test_akshare_interfaces()

    # 2. 测试巨潮资讯接口
    await test_cninfo_interfaces()

    # 3. 测试Tushare接口
    test_tushare_interfaces()

    # 4. 生成汇总报告
    generate_summary_report()


if __name__ == "__main__":
    asyncio.run(main())
