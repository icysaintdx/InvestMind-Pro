#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tushare 新闻接口测试脚本
测试所有Tushare新闻相关接口的可用性

运行方式: python test_tushare_news_interfaces.py
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any

# 设置编码
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 从.env加载配置
from dotenv import load_dotenv

load_dotenv()

TUSHARE_TOKEN = os.getenv("TUSHARE_TOKEN", "")

# 测试结果
test_results = []


def log_result(
    interface_name: str,
    api_code: str,
    data_sources: str,
    permission: str,
    status: str,
    count: int = 0,
    sample_data: Any = None,
    error: str = "",
):
    """记录测试结果"""
    test_results.append(
        {
            "接口名称": interface_name,
            "接口代码": api_code,
            "数据源": data_sources,
            "权限要求": permission,
            "状态": status,
            "数据量": count,
            "错误信息": error,
        }
    )

    status_icon = "✅" if status == "正常" else ("⚠️" if status == "需要权限" else "❌")
    print(f"{status_icon} [{api_code}] {interface_name}: {status} (数据量: {count})")
    if error:
        print(f"   错误: {error[:100]}...")
    if sample_data and count > 0:
        print(f"   示例: {str(sample_data)[:150]}...")


def test_news_list_hidden_api():
    """测试隐藏的新闻聚合接口 (免费)"""
    print("\n" + "=" * 60)
    print("📰 测试 news_list 隐藏接口 (免费)")
    print("=" * 60)

    url = "https://api.tushare.pro/news/news_list"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/json;charset=UTF-8",
    }

    # 测试各个平台
    platforms = [
        (0, "全平台聚合"),
        (1, "东方财富"),
        (2, "财联社"),
        (3, "同花顺"),
        (4, "新浪财经"),
        (5, "金融界"),
        (6, "雪球"),
        (7, "第一财经"),
        (8, "凤凰财经"),
        (9, "云财经"),
        (10, "华尔街见闻"),
    ]

    for source_id, name in platforms:
        try:
            data = {
                "api_name": "news_list",
                "token": TUSHARE_TOKEN,
                "params": {
                    "source_id": source_id,
                    "page_size": 10,
                    "page_num": 1,
                    "start_time": "",
                    "end_time": "",
                },
            }

            response = requests.post(url, headers=headers, json=data, timeout=30)
            result = response.json()

            if result.get("code") == 0 and result.get("data"):
                news_data = result["data"]
                sample = news_data[0] if news_data else None
                log_result(
                    f"新闻聚合-{name}",
                    f"news_list(source_id={source_id})",
                    name,
                    "免费",
                    "正常",
                    len(news_data),
                    sample,
                )
            else:
                log_result(
                    f"新闻聚合-{name}",
                    f"news_list(source_id={source_id})",
                    name,
                    "免费",
                    "无数据",
                    0,
                    error=result.get("msg", "未知错误"),
                )
        except Exception as e:
            log_result(
                f"新闻聚合-{name}",
                f"news_list(source_id={source_id})",
                name,
                "免费",
                "异常",
                0,
                error=str(e),
            )


def test_tushare_pro_api():
    """测试Tushare Pro API接口"""
    print("\n" + "=" * 60)
    print("📰 测试 Tushare Pro API 接口")
    print("=" * 60)

    if not TUSHARE_TOKEN:
        print("❌ TUSHARE_TOKEN 未配置")
        return

    try:
        import tushare as ts

        ts.set_token(TUSHARE_TOKEN)
        pro = ts.pro_api()
        print(f"Tushare版本: {ts.__version__}")
    except ImportError:
        print("❌ Tushare未安装")
        return
    except Exception as e:
        print(f"❌ Tushare初始化失败: {e}")
        return

    # 1. 新闻快讯 news
    print("\n--- 新闻快讯 (news) ---")
    try:
        end_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        start_date = (datetime.now() - timedelta(hours=24)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # 测试不同数据源
        sources = ["sina", "eastmoney", "cls", "10jqka", "wallstreetcn"]
        for src in sources:
            try:
                df = pro.news(src=src, start_date=start_date, end_date=end_date)
                if df is not None and not df.empty:
                    sample = df.iloc[0].to_dict() if len(df) > 0 else None
                    log_result(
                        f"新闻快讯-{src}",
                        f"news(src={src})",
                        src,
                        "单独开权限",
                        "正常",
                        len(df),
                        sample,
                    )
                else:
                    log_result(
                        f"新闻快讯-{src}",
                        f"news(src={src})",
                        src,
                        "单独开权限",
                        "无数据",
                        0,
                    )
            except Exception as e:
                error_msg = str(e)
                if (
                    "权限" in error_msg
                    or "permission" in error_msg.lower()
                    or "抱歉" in error_msg
                ):
                    log_result(
                        f"新闻快讯-{src}",
                        f"news(src={src})",
                        src,
                        "单独开权限",
                        "需要权限",
                        0,
                        error=error_msg,
                    )
                else:
                    log_result(
                        f"新闻快讯-{src}",
                        f"news(src={src})",
                        src,
                        "单独开权限",
                        "异常",
                        0,
                        error=error_msg,
                    )
    except Exception as e:
        print(f"   新闻快讯测试失败: {e}")

    # 2. 新闻通讯 major_news
    print("\n--- 新闻通讯 (major_news) ---")
    try:
        end_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        start_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")

        sources = ["新浪财经", "财联社", "同花顺", "华尔街见闻"]
        for src in sources:
            try:
                df = pro.major_news(src=src, start_date=start_date, end_date=end_date)
                if df is not None and not df.empty:
                    sample = df.iloc[0].to_dict() if len(df) > 0 else None
                    log_result(
                        f"新闻通讯-{src}",
                        f"major_news(src={src})",
                        src,
                        "单独开权限",
                        "正常",
                        len(df),
                        sample,
                    )
                else:
                    log_result(
                        f"新闻通讯-{src}",
                        f"major_news(src={src})",
                        src,
                        "单独开权限",
                        "无数据",
                        0,
                    )
            except Exception as e:
                error_msg = str(e)
                if (
                    "权限" in error_msg
                    or "permission" in error_msg.lower()
                    or "抱歉" in error_msg
                ):
                    log_result(
                        f"新闻通讯-{src}",
                        f"major_news(src={src})",
                        src,
                        "单独开权限",
                        "需要权限",
                        0,
                        error=error_msg,
                    )
                else:
                    log_result(
                        f"新闻通讯-{src}",
                        f"major_news(src={src})",
                        src,
                        "单独开权限",
                        "异常",
                        0,
                        error=error_msg,
                    )
    except Exception as e:
        print(f"   新闻通讯测试失败: {e}")

    # 3. 新闻联播 cctv_news
    print("\n--- 新闻联播 (cctv_news) ---")
    try:
        today = datetime.now().strftime("%Y%m%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")

        for date in [today, yesterday]:
            try:
                df = pro.cctv_news(date=date)
                if df is not None and not df.empty:
                    sample = df.iloc[0].to_dict() if len(df) > 0 else None
                    log_result(
                        f"新闻联播-{date}",
                        f"cctv_news(date={date})",
                        "央视新闻联播",
                        "单独开权限",
                        "正常",
                        len(df),
                        sample,
                    )
                    break  # 只要有一天有数据就行
                else:
                    log_result(
                        f"新闻联播-{date}",
                        f"cctv_news(date={date})",
                        "央视新闻联播",
                        "单独开权限",
                        "无数据",
                        0,
                    )
            except Exception as e:
                error_msg = str(e)
                if (
                    "权限" in error_msg
                    or "permission" in error_msg.lower()
                    or "抱歉" in error_msg
                ):
                    log_result(
                        f"新闻联播-{date}",
                        f"cctv_news(date={date})",
                        "央视新闻联播",
                        "单独开权限",
                        "需要权限",
                        0,
                        error=error_msg,
                    )
                else:
                    log_result(
                        f"新闻联播-{date}",
                        f"cctv_news(date={date})",
                        "央视新闻联播",
                        "单独开权限",
                        "异常",
                        0,
                        error=error_msg,
                    )
    except Exception as e:
        print(f"   新闻联播测试失败: {e}")

    # 4. 上市公司公告 anns_d
    print("\n--- 上市公司公告 (anns_d) ---")
    try:
        today = datetime.now().strftime("%Y%m%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")

        for date in [today, yesterday]:
            try:
                df = pro.anns_d(ann_date=date)
                if df is not None and not df.empty:
                    sample = df.iloc[0].to_dict() if len(df) > 0 else None
                    log_result(
                        f"上市公司公告-{date}",
                        f"anns_d(ann_date={date})",
                        "上市公司公告",
                        "单独开权限",
                        "正常",
                        len(df),
                        sample,
                    )
                    break
                else:
                    log_result(
                        f"上市公司公告-{date}",
                        f"anns_d(ann_date={date})",
                        "上市公司公告",
                        "单独开权限",
                        "无数据",
                        0,
                    )
            except Exception as e:
                error_msg = str(e)
                if (
                    "权限" in error_msg
                    or "permission" in error_msg.lower()
                    or "抱歉" in error_msg
                ):
                    log_result(
                        f"上市公司公告-{date}",
                        f"anns_d(ann_date={date})",
                        "上市公司公告",
                        "单独开权限",
                        "需要权限",
                        0,
                        error=error_msg,
                    )
                else:
                    log_result(
                        f"上市公司公告-{date}",
                        f"anns_d(ann_date={date})",
                        "上市公司公告",
                        "单独开权限",
                        "异常",
                        0,
                        error=error_msg,
                    )
    except Exception as e:
        print(f"   上市公司公告测试失败: {e}")

    # 5. 国家政策法规 npr
    print("\n--- 国家政策法规 (npr) ---")
    try:
        df = pro.npr(ptype="科技")
        if df is not None and not df.empty:
            sample = df.iloc[0].to_dict() if len(df) > 0 else None
            log_result(
                "国家政策法规",
                "npr(ptype=科技)",
                "国务院等政府机关",
                "单独开权限",
                "正常",
                len(df),
                sample,
            )
        else:
            log_result(
                "国家政策法规",
                "npr(ptype=科技)",
                "国务院等政府机关",
                "单独开权限",
                "无数据",
                0,
            )
    except Exception as e:
        error_msg = str(e)
        if (
            "权限" in error_msg
            or "permission" in error_msg.lower()
            or "抱歉" in error_msg
        ):
            log_result(
                "国家政策法规",
                "npr(ptype=科技)",
                "国务院等政府机关",
                "单独开权限",
                "需要权限",
                0,
                error=error_msg,
            )
        else:
            log_result(
                "国家政策法规",
                "npr(ptype=科技)",
                "国务院等政府机关",
                "单独开权限",
                "异常",
                0,
                error=error_msg,
            )

    # 6. 上证E互动 irm_qa_sh
    print("\n--- 上证E互动 (irm_qa_sh) ---")
    try:
        today = datetime.now().strftime("%Y%m%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")

        for date in [today, yesterday]:
            try:
                df = pro.irm_qa_sh(trade_date=date)
                if df is not None and not df.empty:
                    sample = df.iloc[0].to_dict() if len(df) > 0 else None
                    log_result(
                        f"上证E互动-{date}",
                        f"irm_qa_sh(trade_date={date})",
                        "上交所e互动",
                        "120积分试用/10000积分正式",
                        "正常",
                        len(df),
                        sample,
                    )
                    break
                else:
                    log_result(
                        f"上证E互动-{date}",
                        f"irm_qa_sh(trade_date={date})",
                        "上交所e互动",
                        "120积分试用/10000积分正式",
                        "无数据",
                        0,
                    )
            except Exception as e:
                error_msg = str(e)
                if (
                    "权限" in error_msg
                    or "permission" in error_msg.lower()
                    or "抱歉" in error_msg
                    or "积分" in error_msg
                ):
                    log_result(
                        f"上证E互动-{date}",
                        f"irm_qa_sh(trade_date={date})",
                        "上交所e互动",
                        "120积分试用/10000积分正式",
                        "需要权限",
                        0,
                        error=error_msg,
                    )
                else:
                    log_result(
                        f"上证E互动-{date}",
                        f"irm_qa_sh(trade_date={date})",
                        "上交所e互动",
                        "120积分试用/10000积分正式",
                        "异常",
                        0,
                        error=error_msg,
                    )
    except Exception as e:
        print(f"   上证E互动测试失败: {e}")

    # 7. 深证互动易 irm_qa_sz
    print("\n--- 深证互动易 (irm_qa_sz) ---")
    try:
        today = datetime.now().strftime("%Y%m%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")

        for date in [today, yesterday]:
            try:
                df = pro.irm_qa_sz(trade_date=date)
                if df is not None and not df.empty:
                    sample = df.iloc[0].to_dict() if len(df) > 0 else None
                    log_result(
                        f"深证互动易-{date}",
                        f"irm_qa_sz(trade_date={date})",
                        "深交所互动易",
                        "120积分试用/10000积分正式",
                        "正常",
                        len(df),
                        sample,
                    )
                    break
                else:
                    log_result(
                        f"深证互动易-{date}",
                        f"irm_qa_sz(trade_date={date})",
                        "深交所互动易",
                        "120积分试用/10000积分正式",
                        "无数据",
                        0,
                    )
            except Exception as e:
                error_msg = str(e)
                if (
                    "权限" in error_msg
                    or "permission" in error_msg.lower()
                    or "抱歉" in error_msg
                    or "积分" in error_msg
                ):
                    log_result(
                        f"深证互动易-{date}",
                        f"irm_qa_sz(trade_date={date})",
                        "深交所互动易",
                        "120积分试用/10000积分正式",
                        "需要权限",
                        0,
                        error=error_msg,
                    )
                else:
                    log_result(
                        f"深证互动易-{date}",
                        f"irm_qa_sz(trade_date={date})",
                        "深交所互动易",
                        "120积分试用/10000积分正式",
                        "异常",
                        0,
                        error=error_msg,
                    )
    except Exception as e:
        print(f"   深证互动易测试失败: {e}")


def generate_summary_report():
    """生成汇总报告"""
    print("\n" + "=" * 80)
    print("📋 Tushare 新闻接口测试汇总报告")
    print("=" * 80)
    print(f"检测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(
        f"Tushare Token: {TUSHARE_TOKEN[:8]}...{TUSHARE_TOKEN[-4:]}"
        if TUSHARE_TOKEN
        else "未配置"
    )
    print("-" * 80)

    # 统计
    total = len(test_results)
    normal = sum(1 for r in test_results if r["状态"] == "正常")
    need_permission = sum(1 for r in test_results if r["状态"] == "需要权限")
    abnormal = sum(1 for r in test_results if r["状态"] in ["异常", "无数据"])

    print(f"\n📊 统计概览:")
    print(f"   总接口数: {total}")
    print(f"   ✅ 正常可用: {normal}")
    print(f"   ⚠️ 需要权限: {need_permission}")
    print(f"   ❌ 异常/无数据: {abnormal}")

    # 分类显示
    print(f"\n📋 可用接口 (免费/已有权限):")
    print("-" * 80)
    for r in test_results:
        if r["状态"] == "正常":
            print(f"   ✅ {r['接口名称']} | {r['接口代码']} | 数据量: {r['数据量']}")

    print(f"\n📋 需要权限的接口:")
    print("-" * 80)
    for r in test_results:
        if r["状态"] == "需要权限":
            print(f"   ⚠️ {r['接口名称']} | {r['权限要求']}")

    print(f"\n📋 异常接口:")
    print("-" * 80)
    for r in test_results:
        if r["状态"] in ["异常", "无数据"]:
            print(f"   ❌ {r['接口名称']} | {r['错误信息'][:50]}...")

    # 保存JSON报告
    report = {
        "检测时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Token": f"{TUSHARE_TOKEN[:8]}...{TUSHARE_TOKEN[-4:]}"
        if TUSHARE_TOKEN
        else "未配置",
        "统计": {
            "总接口数": total,
            "正常可用": normal,
            "需要权限": need_permission,
            "异常": abnormal,
        },
        "接口详情": test_results,
    }

    report_path = os.path.join(
        os.path.dirname(__file__), "tushare_news_interface_report.json"
    )
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n📄 详细报告已保存至: {report_path}")


def main():
    """主函数"""
    print("=" * 80)
    print("[检测] Tushare 新闻接口可用性测试")
    print("=" * 80)

    if not TUSHARE_TOKEN:
        print("❌ 错误: TUSHARE_TOKEN 未配置，请在 .env 文件中设置")
        return

    print(f"Token: {TUSHARE_TOKEN[:8]}...{TUSHARE_TOKEN[-4:]}")

    # 1. 测试隐藏的新闻聚合接口 (免费)
    test_news_list_hidden_api()

    # 2. 测试Tushare Pro API接口
    test_tushare_pro_api()

    # 3. 生成汇总报告
    generate_summary_report()


if __name__ == "__main__":
    main()
