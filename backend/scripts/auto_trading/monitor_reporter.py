"""
监控报告模块 - MonitorReporter
实时显示持仓盈亏，收盘后生成交易报告（交易笔数/盈亏/胜率）
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger("auto_trading.monitor")


class MonitorReporter:
    """监控与报告"""

    def __init__(self, engine=None):
        """
        Args:
            engine: TradingEngine 实例（用于获取实时数据）
        """
        self.engine = engine

    # ==================== 实时监控 ====================

    def print_positions(self):
        """打印当前持仓盈亏"""
        if not self.engine or not self.engine.account_id:
            logger.warning("[监控] 引擎未初始化")
            return

        info = self.engine.get_account_info()
        if not info or not info.get("success"):
            logger.error("[监控] 获取账户信息失败")
            return

        account = info["account"]
        positions = info.get("positions", [])

        print(f"\n{'='*70}")
        print(f"  账户: {account.get('account_name', '')}  "
              f"ID: {self.engine.account_id[:8]}...")
        print(f"  初始资金: {account['initial_capital']:>12,.2f}")
        print(f"  可用资金: {account['available_cash']:>12,.2f}")
        print(f"  总资产:   {account['total_assets']:>12,.2f}")
        print(f"  总盈亏:   {account['total_profit']:>+12,.2f}  "
              f"({account['profit_rate']*100:+.2f}%)")
        print(f"{'='*70}")

        if not positions:
            print("  (无持仓)")
        else:
            print(f"  {'代码':<8} {'名称':<8} {'数量':>6} {'成本':>8} "
                  f"{'现价':>8} {'市值':>10} {'盈亏':>10} {'盈亏%':>8}")
            print(f"  {'-'*66}")
            for p in positions:
                print(
                    f"  {p['stock_code']:<8} {p['stock_name']:<8} "
                    f"{p['quantity']:>6} {p['avg_cost']:>8.2f} "
                    f"{p['current_price']:>8.2f} {p['market_value']:>10,.2f} "
                    f"{p['profit']:>+10,.2f} {p['profit_rate']*100:>+7.2f}%"
                )

        # 活跃持仓（引擎内部跟踪的止损止盈）
        if self.engine.active_positions:
            print(f"\n  止损/止盈监控:")
            for code, pos in self.engine.active_positions.items():
                print(
                    f"    {code} 入场={pos.entry_price:.2f} "
                    f"止损={pos.stop_loss:.2f} 止盈={pos.take_profit:.2f}"
                )
        print(f"{'='*70}\n")

    def print_trade_log(self):
        """打印交易日志"""
        if not self.engine:
            return

        logs = self.engine.trade_log
        if not logs:
            print("  (无交易记录)")
            return

        print(f"\n{'='*70}")
        print(f"  交易日志 ({len(logs)}笔)")
        print(f"{'='*70}")
        print(f"  {'时间':<20} {'操作':<5} {'代码':<8} {'名称':<8} "
              f"{'数量':>6} {'价格':>8} {'原因'}")
        print(f"  {'-'*66}")
        for t in logs:
            ts = t['time'][:19] if len(t['time']) > 19 else t['time']
            print(
                f"  {ts:<20} {t['action']:<5} {t['stock_code']:<8} "
                f"{t['stock_name']:<8} {t['quantity']:>6} {t['price']:>8.2f} "
                f"{t.get('reason', '')[:30]}"
            )
        print(f"{'='*70}\n")

    # ==================== 收盘报告 ====================

    def generate_report(self) -> Dict[str, Any]:
        """
        生成收盘交易报告

        Returns:
            报告字典
        """
        if not self.engine:
            return {"error": "引擎未初始化"}

        trade_log = self.engine.trade_log
        account_info = self.engine.get_account_info()
        trades_api = self.engine.get_trades()

        # 基础统计
        total_trades = len(trade_log)
        buy_trades = [t for t in trade_log if t["action"] == "BUY"]
        sell_trades = [t for t in trade_log if t["action"] == "SELL"]

        # 盈亏统计
        wins = 0
        losses = 0
        total_pnl = 0.0
        pnl_list = []

        for t in sell_trades:
            reason = t.get("reason", "")
            # 从reason中提取盈亏
            if "盈亏=" in reason:
                try:
                    pnl_str = reason.split("盈亏=")[1].split()[0].replace(",", "").replace("+", "")
                    pnl = float(pnl_str)
                    pnl_list.append(pnl)
                    total_pnl += pnl
                    if pnl > 0:
                        wins += 1
                    else:
                        losses += 1
                except (ValueError, IndexError):
                    pass

        # 账户盈亏
        account_pnl = 0.0
        account_pnl_rate = 0.0
        initial_capital = self.engine.initial_capital
        if account_info and account_info.get("success"):
            acc = account_info["account"]
            account_pnl = acc.get("total_profit", 0)
            account_pnl_rate = acc.get("profit_rate", 0)
            initial_capital = acc.get("initial_capital", self.engine.initial_capital)

        win_rate = wins / (wins + losses) if (wins + losses) > 0 else 0
        avg_win = sum(p for p in pnl_list if p > 0) / wins if wins > 0 else 0
        avg_loss = sum(p for p in pnl_list if p <= 0) / losses if losses > 0 else 0

        report = {
            "report_date": datetime.now().strftime("%Y-%m-%d"),
            "report_time": datetime.now().strftime("%H:%M:%S"),
            "account_id": self.engine.account_id,
            "initial_capital": initial_capital,
            "summary": {
                "total_trades": total_trades,
                "buy_count": len(buy_trades),
                "sell_count": len(sell_trades),
                "win_count": wins,
                "loss_count": losses,
                "win_rate": win_rate,
                "total_pnl": total_pnl,
                "account_pnl": account_pnl,
                "account_pnl_rate": account_pnl_rate,
                "avg_win": avg_win,
                "avg_loss": avg_loss,
            },
            "trades": trade_log,
            "positions": self.engine.get_positions(),
            "api_trades": trades_api,
        }

        return report

    def print_report(self, report: Optional[Dict] = None):
        """打印收盘报告"""
        if report is None:
            report = self.generate_report()

        s = report.get("summary", {})

        print(f"\n{'#'*70}")
        print(f"  收盘交易报告 - {report.get('report_date', '')}")
        print(f"{'#'*70}")
        print(f"  账户ID:     {report.get('account_id', 'N/A')}")
        print(f"  初始资金:   {report.get('initial_capital', 0):>12,.2f}")
        print(f"")
        print(f"  --- 交易统计 ---")
        print(f"  总交易笔数: {s.get('total_trades', 0)}")
        print(f"  买入:       {s.get('buy_count', 0)}笔")
        print(f"  卖出:       {s.get('sell_count', 0)}笔")
        print(f"  盈利:       {s.get('win_count', 0)}笔")
        print(f"  亏损:       {s.get('loss_count', 0)}笔")
        print(f"  胜率:       {s.get('win_rate', 0)*100:.1f}%")
        print(f"")
        print(f"  --- 盈亏统计 ---")
        print(f"  交易盈亏:   {s.get('total_pnl', 0):>+12,.2f}")
        print(f"  账户盈亏:   {s.get('account_pnl', 0):>+12,.2f}")
        print(f"  收益率:     {s.get('account_pnl_rate', 0)*100:>+.2f}%")
        print(f"  平均盈利:   {s.get('avg_win', 0):>+12,.2f}")
        print(f"  平均亏损:   {s.get('avg_loss', 0):>+12,.2f}")
        print(f"{'#'*70}\n")

    def save_report(self, report: Optional[Dict] = None, filepath: str = "trading_report.json"):
        """保存报告到文件"""
        if report is None:
            report = self.generate_report()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info(f"[报告] 已保存: {filepath}")
