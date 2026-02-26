#!/usr/bin/env python3
"""
InvestMindPro 自动模拟交易主控脚本

用法:
    # 早盘扫描（9:15前运行）
    python -m backend.scripts.auto_trading.main --mode=pre_market

    # 实时交易（9:30后运行，会自动轮询到收盘）
    python -m backend.scripts.auto_trading.main --mode=realtime

    # 完整流程（先扫描再交易）
    python -m backend.scripts.auto_trading.main --mode=full

    # 指定参数
    python -m backend.scripts.auto_trading.main --mode=full \\
        --capital=1000000 --interval=30 --api=http://localhost:8000

LLM配置: kirocpa代理 https://kirocpa.zeabur.app/v1 key=icysaintdx model=kimi-k2.5
"""

import os
import sys
import json
import signal
import logging
import argparse
from datetime import datetime
from pathlib import Path

# 确保项目根目录在path中
project_root = Path(__file__).resolve().parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.scripts.auto_trading.pre_market_scanner import PreMarketScanner
from backend.scripts.auto_trading.trading_engine import TradingEngine
from backend.scripts.auto_trading.monitor_reporter import MonitorReporter

# ==================== 日志配置 ====================

LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

log_file = LOG_DIR / f"auto_trading_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(log_file), encoding="utf-8"),
    ],
)
logger = logging.getLogger("auto_trading.main")

# ==================== 数据目录 ====================

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)


def parse_args():
    parser = argparse.ArgumentParser(description="InvestMindPro 自动模拟交易系统")
    parser.add_argument(
        "--mode",
        choices=["pre_market", "realtime", "full"],
        default="full",
        help="运行模式: pre_market=早盘扫描, realtime=实时交易, full=完整流程",
    )
    parser.add_argument("--api", default="http://localhost:8000", help="后端API地址")
    parser.add_argument("--capital", type=float, default=1_000_000, help="初始资金（默认100万）")
    parser.add_argument("--interval", type=int, default=30, help="轮询间隔秒数（默认30）")
    parser.add_argument("--confidence", type=float, default=0.55, help="最低置信度（默认0.55）")
    parser.add_argument("--strategy", default=None, help="指定策略ID（默认自动选择）")
    parser.add_argument(
        "--stocks",
        default=None,
        help="自定义选股池，逗号分隔（如 600519,000858,601318）",
    )
    parser.add_argument(
        "--candidates-file",
        default=None,
        help="直接加载候选列表文件（跳过扫描）",
    )
    return parser.parse_args()


def run_pre_market(args) -> list:
    """早盘扫描"""
    logger.info("=" * 60)
    logger.info("阶段1: 早盘扫描")
    logger.info("=" * 60)

    stock_pool = None
    if args.stocks:
        stock_pool = [s.strip() for s in args.stocks.split(",") if s.strip()]

    scanner = PreMarketScanner(
        api_base=args.api,
        stock_pool=stock_pool,
        strategy_id=args.strategy,
        min_confidence=args.confidence,
    )

    candidates = scanner.scan()

    # 保存候选列表
    candidates_file = str(DATA_DIR / f"candidates_{datetime.now().strftime('%Y%m%d')}.json")
    scanner.save_candidates(candidates, candidates_file)

    if not candidates:
        logger.warning("早盘扫描未发现候选标的")

    return candidates


def run_realtime(args, candidates: list):
    """实时交易"""
    logger.info("=" * 60)
    logger.info("阶段2: 实时交易")
    logger.info("=" * 60)

    if not candidates:
        logger.error("无候选标的，无法启动交易引擎")
        return None, None

    engine = TradingEngine(
        api_base=args.api,
        initial_capital=args.capital,
        poll_interval=args.interval,
    )

    monitor = MonitorReporter(engine=engine)

    # 注册信号处理（Ctrl+C优雅退出）
    def signal_handler(sig, frame):
        logger.info("\n收到中断信号，正在停止引擎...")
        engine.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 启动引擎
    try:
        engine.run(candidates)
    except KeyboardInterrupt:
        logger.info("用户中断")
        engine.stop()
    except Exception as e:
        logger.error(f"引擎异常: {e}", exc_info=True)
        engine.stop()

    return engine, monitor


def run_report(engine, monitor):
    """生成收盘报告"""
    logger.info("=" * 60)
    logger.info("阶段3: 生成收盘报告")
    logger.info("=" * 60)

    if not monitor:
        logger.warning("监控模块未初始化，跳过报告")
        return

    # 打印持仓
    monitor.print_positions()

    # 打印交易日志
    monitor.print_trade_log()

    # 生成并打印报告
    report = monitor.generate_report()
    monitor.print_report(report)

    # 保存
    report_file = str(DATA_DIR / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    monitor.save_report(report, report_file)

    # 保存交易日志
    trade_log_file = str(DATA_DIR / f"trade_log_{datetime.now().strftime('%Y%m%d')}.json")
    engine.save_trade_log(trade_log_file)

    return report


def main():
    args = parse_args()

    logger.info(f"{'#'*60}")
    logger.info(f"  InvestMindPro 自动模拟交易系统")
    logger.info(f"  模式: {args.mode}")
    logger.info(f"  API: {args.api}")
    logger.info(f"  资金: {args.capital:,.0f}")
    logger.info(f"  轮询: {args.interval}秒")
    logger.info(f"  日志: {log_file}")
    logger.info(f"{'#'*60}")

    candidates = []

    # 加载已有候选列表
    if args.candidates_file:
        logger.info(f"从文件加载候选列表: {args.candidates_file}")
        candidates = PreMarketScanner.load_candidates(args.candidates_file)
        logger.info(f"加载了 {len(candidates)} 个候选")

    if args.mode == "pre_market":
        candidates = run_pre_market(args)
        logger.info(f"早盘扫描完成，候选数量: {len(candidates)}")

    elif args.mode == "realtime":
        if not candidates:
            # 尝试加载今天的候选文件
            today_file = DATA_DIR / f"candidates_{datetime.now().strftime('%Y%m%d')}.json"
            if today_file.exists():
                candidates = PreMarketScanner.load_candidates(str(today_file))
                logger.info(f"加载今日候选: {len(candidates)}个")
            else:
                logger.error("无候选列表，请先运行 --mode=pre_market 或指定 --candidates-file")
                sys.exit(1)

        engine, monitor = run_realtime(args, candidates)
        run_report(engine, monitor)

    elif args.mode == "full":
        # 完整流程
        if not candidates:
            candidates = run_pre_market(args)

        if candidates:
            engine, monitor = run_realtime(args, candidates)
            run_report(engine, monitor)
        else:
            logger.warning("无候选标的，跳过交易和报告阶段")

    logger.info("自动模拟交易系统运行结束")


if __name__ == "__main__":
    main()
