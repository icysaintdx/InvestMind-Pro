"""
回测报告生成器 (Backtest Reporter)
生成详细的策略回测报告

功能：
1. 单策略详细报告
2. 多策略对比报告
3. Markdown格式输出
4. 图表数据准备
"""

from typing import Dict, Any, List
from datetime import datetime
import json


class BacktestReporter:
    """回测报告生成器"""
    
    @staticmethod
    def generate_single_strategy_report(result: Dict[str, Any]) -> str:
        """
        生成单策略回测报告
        
        Args:
            result: 回测结果
            
        Returns:
            Markdown格式报告
        """
        if not result.get("success"):
            return f"# 回测失败\n\n错误: {result.get('error', '未知错误')}"
        
        perf = result["performance"]
        period = result["backtest_period"]
        
        report = f"""# {result['strategy_name']} 回测报告

## 📊 基本信息

- **策略名称**: {result['strategy_name']}
- **策略ID**: {result['strategy_id']}
- **回测周期**: {period['start']} 至 {period['end']}
- **交易天数**: {period['days']}天

---

## 💰 收益表现

| 指标 | 数值 |
|------|------|
| **总收益** | ¥{perf['total_return']:,.2f} |
| **收益率** | {perf['total_return_pct']:.2%} |
| **初始资金** | ¥100,000.00 |
| **最终资金** | ¥{perf['final_capital']:,.2f} |

---

## 📈 交易统计

| 指标 | 数值 |
|------|------|
| **总交易次数** | {perf['total_trades']}次 |
| **买入次数** | {perf['buy_trades']}次 |
| **卖出次数** | {perf['sell_trades']}次 |
| **盈利交易** | {perf['profitable_trades']}次 |
| **胜率** | {perf['win_rate']:.2%} |

---

## 💵 盈亏分析

| 指标 | 数值 |
|------|------|
| **平均盈亏** | ¥{perf['avg_profit']:,.2f} |
| **平均盈亏率** | {perf['avg_profit_pct']:.2%} |
| **最大回撤** | {perf['max_drawdown']:.2%} |
| **夏普比率** | {perf['sharpe_ratio']:.2f} |

---

## 📝 交易记录

"""
        
        # 添加交易记录
        trades = result.get("trades", [])
        if trades:
            report += "\n| 日期 | 操作 | 价格 | 股数 | 盈亏 | 盈亏率 |\n"
            report += "|------|------|------|------|------|--------|\n"
            
            for trade in trades[-20:]:  # 最近20笔交易
                date = trade['date']
                action = trade['action']
                price = trade['price']
                shares = trade['shares']
                
                if action == "SELL":
                    profit = trade.get('profit', 0)
                    profit_pct = trade.get('profit_pct', 0)
                    report += f"| {date} | {action} | ¥{price:.2f} | {shares} | ¥{profit:,.2f} | {profit_pct:.2%} |\n"
                else:
                    report += f"| {date} | {action} | ¥{price:.2f} | {shares} | - | - |\n"
        
        report += "\n---\n\n"
        report += f"**报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        return report
    
    @staticmethod
    def generate_comparison_report(comparison_result: Dict[str, Any]) -> str:
        """
        生成多策略对比报告
        
        Args:
            comparison_result: 对比结果
            
        Returns:
            Markdown格式报告
        """
        if not comparison_result.get("success"):
            return f"# 对比失败\n\n错误: {comparison_result.get('error', '未知错误')}"
        
        period = comparison_result["backtest_period"]
        comparison = comparison_result["comparison"]
        
        report = f"""# 策略对比报告

## 📊 基本信息

- **对比策略数**: {comparison_result['strategies_count']}个
- **回测周期**: {period['start']} 至 {period['end']}
- **交易天数**: {period['days']}天

---

## 🏆 最佳策略

### 最高收益率
- **策略**: {comparison['best_return']['strategy_name']}
- **收益率**: {comparison['best_return']['total_return_pct']:.2%}
- **胜率**: {comparison['best_return']['win_rate']:.2%}

### 最高胜率
- **策略**: {comparison['best_win_rate']['strategy_name']}
- **胜率**: {comparison['best_win_rate']['win_rate']:.2%}
- **收益率**: {comparison['best_win_rate']['total_return_pct']:.2%}

### 最高夏普比率
- **策略**: {comparison['best_sharpe']['strategy_name']}
- **夏普比率**: {comparison['best_sharpe']['sharpe_ratio']:.2f}
- **收益率**: {comparison['best_sharpe']['total_return_pct']:.2%}

---

## 📊 收益率排名

| 排名 | 策略 | 收益率 | 胜率 | 夏普比率 | 最大回撤 |
|------|------|--------|------|----------|----------|
"""
        
        for i, strategy in enumerate(comparison['ranking_by_return'], 1):
            report += f"| {i} | {strategy['strategy_name']} | {strategy['total_return_pct']:.2%} | {strategy['win_rate']:.2%} | {strategy['sharpe_ratio']:.2f} | {strategy['max_drawdown']:.2%} |\n"
        
        report += "\n---\n\n## 📈 胜率排名\n\n"
        report += "| 排名 | 策略 | 胜率 | 收益率 | 交易次数 |\n"
        report += "|------|------|------|--------|----------|\n"
        
        for i, strategy in enumerate(comparison['ranking_by_win_rate'], 1):
            report += f"| {i} | {strategy['strategy_name']} | {strategy['win_rate']:.2%} | {strategy['total_return_pct']:.2%} | {strategy['total_trades']} |\n"
        
        report += "\n---\n\n## 💡 策略选择建议\n\n"
        
        # 生成建议
        best_return = comparison['best_return']
        best_win_rate = comparison['best_win_rate']
        best_sharpe = comparison['best_sharpe']
        
        report += f"### 激进型投资者\n"
        report += f"推荐使用 **{best_return['strategy_name']}**，该策略在回测期间获得了最高的收益率（{best_return['total_return_pct']:.2%}）。\n\n"
        
        report += f"### 稳健型投资者\n"
        report += f"推荐使用 **{best_sharpe['strategy_name']}**，该策略具有最高的夏普比率（{best_sharpe['sharpe_ratio']:.2f}），风险调整后收益最优。\n\n"
        
        report += f"### 保守型投资者\n"
        report += f"推荐使用 **{best_win_rate['strategy_name']}**，该策略具有最高的胜率（{best_win_rate['win_rate']:.2%}），交易成功率最高。\n\n"
        
        report += "---\n\n"
        report += f"**报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        return report
    
    @staticmethod
    def prepare_chart_data(result: Dict[str, Any]) -> Dict[str, Any]:
        """
        准备图表数据
        
        Args:
            result: 回测结果
            
        Returns:
            图表数据字典
        """
        trades = result.get("trades", [])
        
        # 资金曲线数据
        equity_data = {
            "dates": [],
            "values": []
        }
        
        current_capital = 100000.0
        for trade in trades:
            equity_data["dates"].append(str(trade["date"]))
            equity_data["values"].append(trade["capital_after"])
        
        # 盈亏分布数据
        profit_distribution = {
            "profits": [],
            "dates": []
        }
        
        for trade in trades:
            if trade["action"] == "SELL":
                profit_distribution["profits"].append(trade.get("profit", 0))
                profit_distribution["dates"].append(str(trade["date"]))
        
        return {
            "equity_curve": equity_data,
            "profit_distribution": profit_distribution
        }
