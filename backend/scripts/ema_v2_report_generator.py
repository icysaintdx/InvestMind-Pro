#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EMA V2 扩展回测报告生成器
"""

import numpy as np
from datetime import datetime
from typing import Dict, List, Any

# 新增股票列表
EXTENDED_STOCKS = [
    ("002594", "比亚迪", "科技/新能源"),
    ("300750", "宁德时代", "科技/新能源"),
    ("600887", "伊利股份", "消费/食品饮料"),
    ("002271", "东方雨虹", "消费/建材"),
    ("600436", "片仔癀", "医药"),
    ("000538", "云南白药", "医药"),
    ("600036", "招商银行", "金融/银行"),
    ("601398", "工商银行", "金融/银行"),
]

def generate_extended_report(all_results: List[Dict[str, Any]], original_results: Dict = None) -> str:
    """生成扩展回测报告"""
    
    lines = []
    lines.append("# EMA V2 策略扩展回测报告")
    lines.append("")
    lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    lines.append("## 执行摘要")
    lines.append("")
    lines.append("本次扩展回测新增8只不同行业的代表性股票，验证EMA V2策略在多行业环境下的稳健性。")
    lines.append("")
    
    # 新增股票概览
    lines.append("## 新增测试股票概览")
    lines.append("")
    lines.append("| 股票代码 | 股票名称 | 行业分类 | 状态 |")
    lines.append("|----------|----------|----------|------|")
    
    for stock_code, stock_name, industry in EXTENDED_STOCKS:
        result = next((r for r in all_results if r["stock_code"] == stock_code), None)
        status = "✅ 成功" if result and result.get("success") else "❌ 失败"
        lines.append(f"| {stock_code} | {stock_name} | {industry} | {status} |")
    
    lines.append("")
    
    # 参数组合列表
    lines.append("## 测试参数组合")
    lines.append("")
    lines.append("- 初始资金: ¥100,000")
    lines.append("- 参数组合数: 9 种")
    lines.append("")
    lines.append("| 组合 | EMA快线 | EMA慢线 | ATR倍数 |")
    lines.append("|------|---------|---------|---------|")
    param_combinations = [
        {"ema_fast": 5, "ema_slow": 30},
        {"ema_fast": 5, "ema_slow": 60},
        {"ema_fast": 5, "ema_slow": 120},
        {"ema_fast": 10, "ema_slow": 30},
        {"ema_fast": 10, "ema_slow": 60},
        {"ema_fast": 10, "ema_slow": 120},
        {"ema_fast": 20, "ema_slow": 60},
        {"ema_fast": 20, "ema_slow": 120},
        {"ema_fast": 8, "ema_slow": 25},
    ]
    for i, params in enumerate(param_combinations, 1):
        lines.append(f"| {i} | {params['ema_fast']} | {params['ema_slow']} | 2.0 |")
    lines.append("")
    
    # 新增股票最佳参数汇总
    lines.append("## 新增股票最佳参数汇总")
    lines.append("")
    lines.append("| 股票代码 | 股票名称 | 行业 | 最佳参数 | 总收益 | 年化收益 | 夏普比率 | 最大回撤 | 胜率 | 交易次数 |")
    lines.append("|----------|----------|------|----------|--------|----------|----------|----------|------|----------|")
    
    successful_stocks = [r for r in all_results if r.get("success")]
    
    for result in successful_stocks:
        stock_code = result["stock_code"]
        stock_name = result.get("stock_name", "")
        industry = result.get("industry", "")
        best = result["best_by_return"]
        params = best["params"]
        param_str = f"{params['ema_fast']}/{params['ema_slow']}"
        
        # 计算年化收益
        days = result.get("data_period", {}).get("days", 365)
        years = days / 365
        annual_return = (1 + best["total_return_pct"]) ** (1/years) - 1 if years > 0 else 0
        
        lines.append(
            f"| {stock_code} | {stock_name} | {industry} | {param_str} | "
            f"{best['total_return_pct']:.2%} | {annual_return:.2%} | "
            f"{best['sharpe_ratio']:.2f} | {best['max_drawdown']:.2%} | "
            f"{best['win_rate']:.1%} | {best['total_trades']} |"
        )
    
    lines.append("")
    
    # 行业分析
    if successful_stocks:
        lines.append("## 行业分布分析")
        lines.append("")
        
        industry_stats = {}
        for r in successful_stocks:
            industry = r.get("industry", "其他")
            if industry not in industry_stats:
                industry_stats[industry] = []
            industry_stats[industry].append(r["best_by_return"]["total_return_pct"])
        
        lines.append("| 行业 | 股票数量 | 平均收益 | 最高收益 | 最低收益 |")
        lines.append("|------|----------|----------|----------|----------|")
        
        for industry, returns in sorted(industry_stats.items()):
            lines.append(
                f"| {industry} | {len(returns)} | {np.mean(returns):.2%} | "
                f"{max(returns):.2%} | {min(returns):.2%} |"
            )
        
        lines.append("")
        
        # 行业表现分析
        lines.append("### 行业表现分析")
        lines.append("")
        for industry, returns in sorted(industry_stats.items()):
            lines.append(f"- **{industry}**: 平均收益 {np.mean(returns):.2%}, 表现{'较好' if np.mean(returns) > 0 else '较弱'}")
        lines.append("")
    
    # 与原7只股票对比
    if original_results:
        lines.append("## 与原7只股票收益对比")
        lines.append("")
        
        # 原有股票
        original_returns = []
        for code, data in original_results.items():
            original_returns.append(data.get("total_return", 0))
        
        # 新增股票
        new_returns = [r["best_by_return"]["total_return_pct"] for r in successful_stocks]
        
        lines.append("| 分组 | 股票数量 | 平均收益 | 中位数收益 | 最高收益 | 最低收益 |")
        lines.append("|------|----------|----------|------------|----------|----------|")
        lines.append(f"| 原有7只 | 7 | {np.mean(original_returns):.2%} | {np.median(original_returns):.2%} | {max(original_returns):.2%} | {min(original_returns):.2%} |")
        if new_returns:
            lines.append(f"| 新增8只 | {len(new_returns)} | {np.mean(new_returns):.2%} | {np.median(new_returns):.2%} | {max(new_returns):.2%} | {min(new_returns):.2%} |")
            all_returns = original_returns + new_returns
            lines.append(f"| 总计15只 | {len(all_returns)} | {np.mean(all_returns):.2%} | {np.median(all_returns):.2%} | {max(all_returns):.2%} | {min(all_returns):.2%} |")
        lines.append("")
        
        # 对比分析
        lines.append("### 对比分析")
        lines.append("")
        if new_returns:
            diff = np.mean(new_returns) - np.mean(original_returns)
            lines.append(f"- 新增股票平均收益较原有股票{'高' if diff > 0 else '低'} {abs(diff):.2%}")
            lines.append(f"- 原有7只股票收益中位数: {np.median(original_returns):.2%}")
            lines.append(f"- 新增8只股票收益中位数: {np.median(new_returns):.2%}")
            lines.append(f"- 15只股票整体平均收益: {np.mean(all_returns):.2%}")
        lines.append("")
    
    # 统计摘要
    if successful_stocks:
        returns = [r["best_by_return"]["total_return_pct"] for r in successful_stocks]
        sharpes = [r["best_by_return"]["sharpe_ratio"] for r in successful_stocks]
        drawdowns = [r["best_by_return"]["max_drawdown"] for r in successful_stocks]
        win_rates = [r["best_by_return"]["win_rate"] for r in successful_stocks]
        
        lines.append("## 新增股票统计摘要")
        lines.append("")
        lines.append(f"- **平均总收益**: {np.mean(returns):.2%}")
        lines.append(f"- **收益中位数**: {np.median(returns):.2%}")
        lines.append(f"- **最佳收益**: {max(returns):.2%}")
        lines.append(f"- **最差收益**: {min(returns):.2%}")
        lines.append(f"- **平均夏普比率**: {np.mean(sharpes):.2f}")
        lines.append(f"- **平均最大回撤**: {np.mean(drawdowns):.2%}")
        lines.append(f"- **平均胜率**: {np.mean(win_rates):.1%}")
        lines.append("")
        
        # 策略稳健性分析
        positive_returns = sum(1 for r in returns if r > 0)
        lines.append("## 策略稳健性分析")
        lines.append("")
        lines.append(f"- **正收益比例**: {positive_returns}/{len(returns)} ({positive_returns/len(returns)*100:.1f}%)")
        lines.append(f"- **收益标准差**: {np.std(returns):.2%}")
        lines.append(f"- **收益变异系数**: {np.std(returns)/abs(np.mean(returns)):.2f}" if np.mean(returns) != 0 else "- **收益变异系数**: N/A")
        lines.append("")
        
        if positive_returns >= len(returns) * 0.5:
            lines.append("✅ **结论**: EMA V2策略在新增8只股票中表现稳健，超过50%的股票获得正收益。")
        else:
            lines.append("⚠️ **结论**: EMA V2策略在新增8只股票中表现一般，需进一步优化。")
        lines.append("")
    
    # 最佳参数分析
    if successful_stocks:
        lines.append("## 最佳参数分析")
        lines.append("")
        
        param_count = {}
        for r in successful_stocks:
            params = r["best_by_return"]["params"]
            key = f"EMA{params['ema_fast']}/{params['ema_slow']}"
            param_count[key] = param_count.get(key, 0) + 1
        
        lines.append("| 参数组合 | 使用次数 | 占比 |")
        lines.append("|----------|----------|------|")
        for param, count in sorted(param_count.items(), key=lambda x: -x[1]):
            pct = count / len(successful_stocks) * 100
            lines.append(f"| {param} | {count} | {pct:.1f}% |")
        lines.append("")
    
    # 详细结果
    lines.append("## 详细回测结果")
    lines.append("")
    
    for result in successful_stocks:
        stock_code = result["stock_code"]
        stock_name = result.get("stock_name", "")
        lines.append(f"### {stock_code} {stock_name}")
        lines.append("")
        
        # 最佳收益参数
        best_ret = result["best_by_return"]
        lines.append("**最佳收益参数**:")
        lines.append(f"- 参数: EMA{best_ret['params']['ema_fast']}/{best_ret['params']['ema_slow']}")
        lines.append(f"- 总收益: {best_ret['total_return_pct']:.2%}")
        lines.append(f"- 夏普比率: {best_ret['sharpe_ratio']:.2f}")
        lines.append(f"- 最大回撤: {best_ret['max_drawdown']:.2%}")
        lines.append(f"- 胜率: {best_ret['win_rate']:.1%}")
        lines.append(f"- 交易次数: {best_ret['total_trades']}")
        lines.append("")
        
        # 最佳夏普参数
        best_sharpe = result["best_by_sharpe"]
        lines.append("**最佳夏普比率参数**:")
        lines.append(f"- 参数: EMA{best_sharpe['params']['ema_fast']}/{best_sharpe['params']['ema_slow']}")
        lines.append(f"- 总收益: {best_sharpe['total_return_pct']:.2%}")
        lines.append(f"- 夏普比率: {best_sharpe['sharpe_ratio']:.2f}")
        lines.append(f"- 最大回撤: {best_sharpe['max_drawdown']:.2%}")
        lines.append(f"- 胜率: {best_sharpe['win_rate']:.1%}")
        lines.append("")
        
        # 所有参数结果
        lines.append("**所有参数组合结果**:")
        lines.append("")
        lines.append("| 参数 | 总收益 | 夏普比率 | 最大回撤 | 胜率 | 交易次数 |")
        lines.append("|------|--------|----------|----------|------|----------|")
        for r in result.get("all_results", []):
            if r["success"]:
                p = r["params"]
                lines.append(
                    f"| EMA{p['ema_fast']}/{p['ema_slow']} | "
                    f"{r['total_return_pct']:.2%} | {r['sharpe_ratio']:.2f} | "
                    f"{r['max_drawdown']:.2%} | {r['win_rate']:.1%} | {r['total_trades']} |"
                )
        lines.append("")
    
    # 结论与建议
    lines.append("## 结论与建议")
    lines.append("")
    
    if successful_stocks:
        returns = [r["best_by_return"]["total_return_pct"] for r in successful_stocks]
        avg_return = np.mean(returns)
        
        if avg_return > 0.05:
            lines.append("### 总体评价: 优秀 ✅")
            lines.append("")
            lines.append("EMA V2策略在扩展测试中表现优秀，平均收益超过5%，策略具有较强的稳健性。")
        elif avg_return > 0:
            lines.append("### 总体评价: 良好 ✅")
            lines.append("")
            lines.append("EMA V2策略在扩展测试中表现良好，平均收益为正，策略具有一定的稳健性。")
        else:
            lines.append("### 总体评价: 需优化 ⚠️")
            lines.append("")
            lines.append("EMA V2策略在扩展测试中表现一般，建议结合其他指标或调整参数。")
        
        lines.append("")
        lines.append("### 建议")
        lines.append("")
        lines.append("1. **参数优化**: 根据行业特点选择不同参数组合")
        lines.append("2. **风险管理**: 关注最大回撤，设置合理的止损线")
        lines.append("3. **行业配置**: 优先选择波动率适中的行业")
        lines.append("4. **持续监控**: 定期回测验证策略有效性")
    
    lines.append("")
    lines.append("---")
    lines.append("*报告由 InvestMindPro 自动生成*")
    
    return "\n".join(lines)


if __name__ == "__main__":
    # 测试报告生成
    print("报告生成器模块加载成功")
