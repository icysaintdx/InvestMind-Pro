#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
InvestMindPro 系统集成器 — 统一入口，整合所有模块

功能：
  - 一键分析：输入股票代码 → 自动采集新闻 → AI策略分析 → 巨潮数据 → 输出综合报告
  - 一键回测：输入股票代码+日期范围 → 自动回测 → 输出报告
  - 批量分析：支持多只股票批量分析

用法:
    python backend/system_integrator.py analyze --stock 600519
    python backend/system_integrator.py analyze --stock 600519 --skip-news --skip-cninfo
    python backend/system_integrator.py backtest --stock 600519 --start 2025-01-01 --end 2025-12-31
    python backend/system_integrator.py backtest --stock 600519 --start 2025-01-01 --end 2025-12-31 --capital 200000
    python backend/system_integrator.py batch --stocks 600519,000858,601318

Author: InvestMindPro
Date: 2026-02-20
"""

import sys
import os
import json
import time
import argparse
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from backend.utils.logging_config import get_logger

logger = get_logger("system_integrator")


# ==================== 一键分析 ====================


def full_analyze(
    stock_code: str,
    skip_news: bool = False,
    skip_cninfo: bool = False,
    news_days: int = 7,
    kline_days: int = 120,
    verbose: bool = False,
) -> dict:
    """
    一键综合分析：新闻采集 → AI策略 → 巨潮数据 → 综合报告

    Args:
        stock_code: 股票代码 (如 '600519')
        skip_news: 跳过新闻采集（使用数据库已有新闻）
        skip_cninfo: 跳过巨潮资讯数据获取
        news_days: 新闻回溯天数
        kline_days: K线回溯天数
        verbose: 详细输出

    Returns:
        综合分析报告字典
    """
    start_time = time.time()
    report = {
        "stock_code": stock_code,
        "timestamp": datetime.now().isoformat(),
        "news_collection": None,
        "strategy": None,
        "cninfo_data": None,
        "errors": [],
    }

    logger.info("=" * 65)
    logger.info(f"  InvestMindPro 综合分析 — {stock_code}")
    logger.info("=" * 65)

    # ---- 步骤1: 新闻采集 ----
    if not skip_news:
        try:
            logger.info("[1/3] 采集新闻数据...")
            from backend.news_collector import run_collection

            stats = run_collection(stock_codes=[stock_code], market_only=False)
            report["news_collection"] = stats
            logger.info(f"  新闻采集完成: 新增 {stats.get('total', 0)} 条")
        except Exception as e:
            msg = f"新闻采集失败: {e}"
            logger.warning(msg)
            report["errors"].append(msg)
    else:
        logger.info("[1/3] 跳过新闻采集 (--skip-news)")

    # ---- 步骤2: AI策略分析 ----
    try:
        logger.info("[2/3] 运行AI策略分析...")
        from backend.ai_strategy_generator import generate_strategy

        strategy = generate_strategy(
            stock_code=stock_code,
            days=kline_days,
            news_days=news_days,
            verbose=verbose,
        )
        report["strategy"] = strategy
        logger.info(f"  策略信号: {strategy.get('signal', 'N/A')} (得分 {strategy.get('score', 0):+.1f})")
    except Exception as e:
        msg = f"AI策略分析失败: {e}"
        logger.error(msg)
        report["errors"].append(msg)

    # ---- 步骤3: 巨潮资讯数据 ----
    if not skip_cninfo:
        try:
            logger.info("[3/3] 获取巨潮资讯数据...")
            from backend.cninfo_data_provider import CninfoDataProvider

            provider = CninfoDataProvider()
            cninfo = provider.get_all(stock_code)
            # 统计获取到的记录数
            total_records = sum(
                len(v) for k, v in cninfo.items()
                if isinstance(v, list)
            )
            report["cninfo_data"] = {
                "summary": {k: len(v) for k, v in cninfo.items() if isinstance(v, list)},
                "total_records": total_records,
            }
            logger.info(f"  巨潮数据: 共 {total_records} 条记录")
        except Exception as e:
            msg = f"巨潮数据获取失败: {e}"
            logger.warning(msg)
            report["errors"].append(msg)
    else:
        logger.info("[3/3] 跳过巨潮数据 (--skip-cninfo)")

    elapsed = round(time.time() - start_time, 1)
    report["time_cost"] = elapsed

    # ---- 打印综合报告 ----
    _print_analyze_report(report, verbose)

    return report


def _print_analyze_report(report: dict, verbose: bool = False):
    """打印综合分析报告"""
    stock = report["stock_code"]
    strategy = report.get("strategy") or {}
    signal = strategy.get("signal", "N/A")
    signal_emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}.get(signal, "⚪")

    print()
    print("=" * 65)
    print(f"  InvestMindPro 综合分析报告 — {stock}")
    print(f"  时间: {report['timestamp']}")
    print("=" * 65)

    # 策略结果
    if strategy:
        price_info = strategy.get("price", {})
        print(f"  收盘价: {price_info.get('close', 'N/A')}  |  日期: {price_info.get('date', 'N/A')}")
        print(f"  RSI: {price_info.get('rsi', 'N/A')}  |  MACD柱: {price_info.get('macd_hist', 'N/A')}")
        print("-" * 65)
        print(f"  {signal_emoji} 综合信号: {signal}")
        print(f"  📊 置信度: {strategy.get('confidence', 0):.0%}")
        print(f"  📈 综合得分: {strategy.get('score', 0):+.1f}")
        weights = strategy.get("weights", {})
        print(f"  ⚖️  权重: 技术面 {weights.get('technical', 0):.0%} / 消息面 {weights.get('sentiment', 0):.0%}")
        print("-" * 65)

        if verbose and strategy.get("reasons"):
            print("  分析理由:")
            for r in strategy["reasons"]:
                print(f"    {r}")
            print("-" * 65)

        sent = strategy.get("sentiment", {})
        print(f"  新闻: 正面{sent.get('positive', 0)} / 负面{sent.get('negative', 0)} / 共{sent.get('total', 0)}条")
    else:
        print("  ⚠ AI策略分析未完成")

    # 新闻采集统计
    news = report.get("news_collection")
    if news:
        print(f"  新闻采集: 新增 {news.get('total', 0)} 条 (耗时 {news.get('time_cost', 0)}s)")

    # 巨潮数据统计
    cninfo = report.get("cninfo_data")
    if cninfo:
        print(f"  巨潮数据: 共 {cninfo.get('total_records', 0)} 条记录")

    # 错误
    if report.get("errors"):
        print("-" * 65)
        print(f"  ⚠ 警告 ({len(report['errors'])} 项):")
        for err in report["errors"]:
            print(f"    · {err}")

    print(f"\n  总耗时: {report.get('time_cost', 0)}s")
    print("=" * 65)
    print()


# ==================== 一键回测 ====================


def full_backtest(
    stock_code: str,
    start_date: str,
    end_date: str,
    initial_capital: float = 100000.0,
    commission_rate: float = 0.0003,
    slippage_rate: float = 0.0005,
    collect_news: bool = True,
) -> dict:
    """
    一键回测：可选先采集新闻 → 运行新闻回测引擎

    Args:
        stock_code: 股票代码
        start_date: 回测开始日期 (YYYY-MM-DD)
        end_date: 回测结束日期 (YYYY-MM-DD)
        initial_capital: 初始资金
        commission_rate: 手续费率
        slippage_rate: 滑点率
        collect_news: 是否先采集新闻

    Returns:
        回测结果字典
    """
    logger.info("=" * 65)
    logger.info(f"  InvestMindPro 一键回测 — {stock_code} ({start_date} ~ {end_date})")
    logger.info("=" * 65)

    # 可选：先采集新闻
    if collect_news:
        try:
            logger.info("[预处理] 采集新闻数据...")
            from backend.news_collector import run_collection

            run_collection(stock_codes=[stock_code], market_only=False)
        except Exception as e:
            logger.warning(f"新闻采集失败（不影响回测）: {e}")

    # 运行回测
    from backend.news_backtest_engine import NewsBacktestEngine

    engine = NewsBacktestEngine(
        initial_capital=initial_capital,
        commission_rate=commission_rate,
        slippage_rate=slippage_rate,
    )
    result = engine.run(
        stock_code=stock_code,
        start_date=start_date,
        end_date=end_date,
    )

    return result


# ==================== 批量分析 ====================


def batch_analyze(
    stock_codes: list[str],
    skip_news: bool = False,
    skip_cninfo: bool = True,
    verbose: bool = False,
) -> list[dict]:
    """
    批量分析多只股票

    Args:
        stock_codes: 股票代码列表
        skip_news: 跳过新闻采集
        skip_cninfo: 跳过巨潮数据（批量模式默认跳过以节省时间）
        verbose: 详细输出

    Returns:
        各股票分析报告列表
    """
    start_time = time.time()
    results = []

    logger.info("=" * 65)
    logger.info(f"  InvestMindPro 批量分析 — {len(stock_codes)} 只股票")
    logger.info(f"  股票列表: {', '.join(stock_codes)}")
    logger.info("=" * 65)

    # 批量模式：先统一采集新闻
    if not skip_news:
        try:
            logger.info("[批量预处理] 统一采集新闻...")
            from backend.news_collector import run_collection

            run_collection(stock_codes=stock_codes, market_only=False)
        except Exception as e:
            logger.warning(f"批量新闻采集失败: {e}")

    # 逐只分析（新闻已采集，跳过重复采集）
    for i, code in enumerate(stock_codes, 1):
        logger.info(f"\n[{i}/{len(stock_codes)}] 分析 {code}...")
        try:
            report = full_analyze(
                stock_code=code,
                skip_news=True,  # 新闻已统一采集
                skip_cninfo=skip_cninfo,
                verbose=verbose,
            )
            results.append(report)
        except Exception as e:
            logger.error(f"{code} 分析失败: {e}")
            results.append({
                "stock_code": code,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            })

    elapsed = round(time.time() - start_time, 1)

    # 打印批量汇总
    _print_batch_summary(results, elapsed)

    return results


def _print_batch_summary(results: list[dict], elapsed: float):
    """打印批量分析汇总"""
    signal_emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}

    print()
    print("=" * 65)
    print(f"  InvestMindPro 批量分析汇总 — {len(results)} 只股票")
    print("=" * 65)

    for r in results:
        code = r.get("stock_code", "???")
        if "error" in r and r.get("strategy") is None:
            print(f"  {code}  ❌ 失败: {r['error']}")
            continue

        strategy = r.get("strategy") or {}
        signal = strategy.get("signal", "N/A")
        emoji = signal_emoji.get(signal, "⚪")
        score = strategy.get("score", 0)
        confidence = strategy.get("confidence", 0)
        price = strategy.get("price", {}).get("close", "N/A")

        print(f"  {code}  {emoji} {signal:4s}  得分 {score:+6.1f}  置信度 {confidence:.0%}  收盘 {price}")

    print("-" * 65)
    print(f"  总耗时: {elapsed}s")
    print("=" * 65)
    print()


# ==================== CLI ====================


def main():
    parser = argparse.ArgumentParser(
        description="InvestMindPro 系统集成器 — 统一入口",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python backend/system_integrator.py analyze --stock 600519
  python backend/system_integrator.py analyze --stock 600519 --verbose --skip-cninfo
  python backend/system_integrator.py backtest --stock 600519 --start 2025-01-01 --end 2025-12-31
  python backend/system_integrator.py backtest --stock 600519 --start 2025-01-01 --end 2025-12-31 --capital 200000
  python backend/system_integrator.py batch --stocks 600519,000858,601318
        """,
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # ---- analyze ----
    p_analyze = subparsers.add_parser("analyze", help="一键综合分析")
    p_analyze.add_argument("--stock", type=str, required=True, help="股票代码 (如 600519)")
    p_analyze.add_argument("--skip-news", action="store_true", help="跳过新闻采集")
    p_analyze.add_argument("--skip-cninfo", action="store_true", help="跳过巨潮数据")
    p_analyze.add_argument("--news-days", type=int, default=7, help="新闻回溯天数 (默认7)")
    p_analyze.add_argument("--kline-days", type=int, default=120, help="K线回溯天数 (默认120)")
    p_analyze.add_argument("--verbose", action="store_true", help="详细输出")
    p_analyze.add_argument("--json", action="store_true", help="输出JSON格式")

    # ---- backtest ----
    p_backtest = subparsers.add_parser("backtest", help="一键回测")
    p_backtest.add_argument("--stock", type=str, required=True, help="股票代码")
    p_backtest.add_argument("--start", type=str, required=True, help="回测开始日期 (YYYY-MM-DD)")
    p_backtest.add_argument("--end", type=str, required=True, help="回测结束日期 (YYYY-MM-DD)")
    p_backtest.add_argument("--capital", type=float, default=100000.0, help="初始资金 (默认100000)")
    p_backtest.add_argument("--commission", type=float, default=0.0003, help="手续费率 (默认0.0003)")
    p_backtest.add_argument("--slippage", type=float, default=0.0005, help="滑点率 (默认0.0005)")
    p_backtest.add_argument("--no-news", action="store_true", help="不预先采集新闻")
    p_backtest.add_argument("--json", action="store_true", help="输出JSON格式")

    # ---- batch ----
    p_batch = subparsers.add_parser("batch", help="批量分析")
    p_batch.add_argument("--stocks", type=str, required=True, help="股票代码列表，逗号分隔 (如 600519,000858,601318)")
    p_batch.add_argument("--skip-news", action="store_true", help="跳过新闻采集")
    p_batch.add_argument("--skip-cninfo", action="store_true", default=True, help="跳过巨潮数据 (默认跳过)")
    p_batch.add_argument("--verbose", action="store_true", help="详细输出")
    p_batch.add_argument("--json", action="store_true", help="输出JSON格式")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # ---- 执行命令 ----
    if args.command == "analyze":
        result = full_analyze(
            stock_code=args.stock,
            skip_news=args.skip_news,
            skip_cninfo=args.skip_cninfo,
            news_days=args.news_days,
            kline_days=args.kline_days,
            verbose=args.verbose,
        )
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2, default=str))

    elif args.command == "backtest":
        result = full_backtest(
            stock_code=args.stock,
            start_date=args.start,
            end_date=args.end,
            initial_capital=args.capital,
            commission_rate=args.commission,
            slippage_rate=args.slippage,
            collect_news=not args.no_news,
        )
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2, default=str))

    elif args.command == "batch":
        codes = [c.strip() for c in args.stocks.split(",") if c.strip()]
        if not codes:
            print("错误: 请提供至少一个股票代码")
            sys.exit(1)
        results = batch_analyze(
            stock_codes=codes,
            skip_news=args.skip_news,
            skip_cninfo=args.skip_cninfo,
            verbose=args.verbose,
        )
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
