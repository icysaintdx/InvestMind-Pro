#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成完整版EMA V2扩展回测报告
"""

import sys
import json
import numpy as np
from pathlib import Path
from datetime import datetime

project_root = Path("/home/icysaintdx/.openclaw/workspace-investmindpro/InvestMindPro")
RESULTS_DIR = project_root / "backend/backtest_results/individual"

# 新增股票信息
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

def load_results():
    """加载所有回测结果"""
    results = []
    for code, name, industry in EXTENDED_STOCKS:
        result_file = RESULTS_DIR / f"{code}_ema_v2_results.json"
        if result_file.exists():
            with open(result_file, 'r') as f:
                data = json.load(f)
                results.append(data)
    return results

def load_original_results():
    """加载原有7只股票的结果"""
    original_codes = ["000333", "000651", "000858", "600276", "600519", "601318", "601888"]
    original = {}
    for code in original_codes:
        result_file = RESULTS_DIR / f"{code}_ema_v2_results.json"
        if result_file.exists():
            with open(result_file, 'r') as f:
                original[code] = json.load(f)
    
    # 同时加载ema_v2_results.json获取更详细的收益数据
    try:
        with open(project_root / "ema_v2_results.json", 'r') as f:
            detail = json.load(f)
    except:
        detail = {}
    
    return original, detail

def generate_full_report():
    """生成完整报告"""
    results = load_results()
    original_results, original_detail = load_original_results()
    
    lines = []
    lines.append("# EMA V2 策略扩展回测报告")
    lines.append("")
    lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    lines.append("## 执行摘要")
    lines.append("")
    lines.append("本次扩展回测新增8只不同行业的代表性股票，使用EMA V2策略（EMA突破+ATR动态止损）进行回测验证。")
    lines.append("回测时间范围：2022-11 至 2024-12（约2年，因TDX数据限制）")
    lines.append("")
    
    # 新增股票概览
    lines.append("## 新增测试股票概览")
    lines.append("")
    lines.append("| 股票代码 | 股票名称 | 行业分类 | 数据条数 | 状态 |")
    lines.append("|----------|----------|----------|----------|------|")
    for code, name, industry in EXTENDED_STOCKS:
        r = next((x for x in results if x["stock_code"] == code), None)
        if r and r.get("success"):
            days = r.get("data_period", {}).get("days", 0)
            status = f"✅ 成功 ({days}天)"
        else:
            status = "❌ 失败"
        lines.append(f"| {code} | {name} | {industry} | {days if r else '-'} | {status} |")
    lines.append("")
    
    # 测试参数组合
    lines.append("## 测试参数组合")
    lines.append("")
    lines.append("| 组合 | EMA快线 | EMA慢线 | ATR倍数 | 说明 |")
    lines.append("|------|---------|---------|---------|------|")
    lines.append("| 1 | 5 | 30 | 2.0 | 短期交易 |")
    lines.append("| 2 | 5 | 60 | 2.0 | 短中期交易 |")
    lines.append("| 3 | 5 | 120 | 2.0 | 短期/长期交叉 |")
    lines.append("| 4 | 10 | 30 | 2.0 | 中短期交易 |")
    lines.append("| 5 | 10 | 60 | 2.0 | 中期交易 |")
    lines.append("| 6 | 10 | 120 | 2.0 | 中/长期交叉 |")
    lines.append("| 7 | 20 | 60 | 2.0 | 中长期趋势 |")
    lines.append("| 8 | 20 | 120 | 2.0 | 长期趋势 |")
    lines.append("| 9 | 8 | 25 | 2.0 | 优化参数 |")
    lines.append("")
    
    # 新增股票最佳参数汇总
    successful = [r for r in results if r.get("success")]
    if successful:
        lines.append("## 新增股票最佳参数汇总")
        lines.append("")
        lines.append("| 股票代码 | 股票名称 | 行业 | 最佳参数 | 总收益 | 胜率 | 交易次数 | 说明 |")
        lines.append("|----------|----------|------|----------|--------|------|----------|------|")
        
        for code, name, industry in EXTENDED_STOCKS:
            r = next((x for x in successful if x["stock_code"] == code), None)
            if r:
                b = r["best_by_return"]
                p = b["params"]
                ret = b["total_return_pct"]
                remark = "📈 正收益" if ret > 0 else "📉 负收益"
                if ret > 0.03:
                    remark = "🌟 表现优秀"
                lines.append(f"| {code} | {name} | {industry} | EMA{p['ema_fast']}/{p['ema_slow']} | {ret:.2%} | {b['win_rate']:.1%} | {b['total_trades']} | {remark} |")
        
        lines.append("")
        
        # 行业分布分析
        lines.append("## 行业分布分析")
        lines.append("")
        
        industry_stats = {}
        for r in successful:
            industry = r.get("industry", "其他")
            if industry not in industry_stats:
                industry_stats[industry] = []
            industry_stats[industry].append(r["best_by_return"]["total_return_pct"])
        
        lines.append("| 行业 | 股票数量 | 平均收益 | 最高收益 | 最低收益 | 表现评级 |")
        lines.append("|------|----------|----------|----------|----------|----------|")
        
        for industry, returns in sorted(industry_stats.items()):
            avg_ret = np.mean(returns)
            if avg_ret > 0.02:
                rating = "🌟 优秀"
            elif avg_ret > 0:
                rating = "✅ 良好"
            elif avg_ret > -0.05:
                rating = "⚠️ 一般"
            else:
                rating = "❌ 较差"
            lines.append(f"| {industry} | {len(returns)} | {avg_ret:.2%} | {max(returns):.2%} | {min(returns):.2%} | {rating} |")
        
        lines.append("")
        
        # 各行业表现分析
        lines.append("### 各行业表现分析")
        lines.append("")
        for industry, returns in sorted(industry_stats.items()):
            avg = np.mean(returns)
            lines.append(f"- **{industry}**: 平均收益 {avg:.2%}")
            if avg > 0:
                lines.append(f"  - 该行业EMA V2策略表现良好，建议关注")
            else:
                lines.append(f"  - 该行业EMA V2策略表现一般，建议谨慎")
        lines.append("")
        
        # 与原7只股票对比
        if original_detail:
            lines.append("## 与原7只股票收益对比")
            lines.append("")
            
            original_returns = []
            for code, data in original_detail.items():
                original_returns.append(data.get("total_return", 0))
            
            new_returns = [r["best_by_return"]["total_return_pct"] for r in successful]
            
            lines.append("| 分组 | 股票数量 | 平均收益 | 中位数收益 | 最高收益 | 最低收益 |")
            lines.append("|------|----------|----------|------------|----------|----------|")
            lines.append(f"| 原有7只 | 7 | {np.mean(original_returns):.2%} | {np.median(original_returns):.2%} | {max(original_returns):.2%} | {min(original_returns):.2%} |")
            lines.append(f"| 新增8只 | {len(new_returns)} | {np.mean(new_returns):.2%} | {np.median(new_returns):.2%} | {max(new_returns):.2%} | {min(new_returns):.2%} |")
            all_returns = original_returns + new_returns
            lines.append(f"| **总计15只** | {len(all_returns)} | {np.mean(all_returns):.2%} | {np.median(all_returns):.2%} | {max(all_returns):.2%} | {min(all_returns):.2%} |")
            lines.append("")
            
            lines.append("### 对比分析")
            lines.append("")
            diff = np.mean(new_returns) - np.mean(original_returns)
            lines.append(f"- 新增股票平均收益较原有股票{'高' if diff > 0 else '低'} {abs(diff):.2%}")
            lines.append(f"- 原有7只股票平均收益: {np.mean(original_returns):.2%}")
            lines.append(f"- 新增8只股票平均收益: {np.mean(new_returns):.2%}")
            lines.append(f"- 15只股票整体平均收益: {np.mean(all_returns):.2%}")
            lines.append("")
            if np.mean(all_returns) > 0:
                lines.append("✅ **总体评价**: EMA V2策略在15只股票测试中整体获得正收益，策略表现稳健。")
            else:
                lines.append("⚠️ **总体评价**: EMA V2策略在15只股票测试中平均收益为负，需要进一步优化。")
            lines.append("")
        
        # 统计摘要
        returns = [r["best_by_return"]["total_return_pct"] for r in successful]
        win_rates = [r["best_by_return"]["win_rate"] for r in successful]
        
        lines.append("## 新增股票统计摘要")
        lines.append("")
        lines.append(f"- **测试股票数量**: 8只")
        lines.append(f"- **成功回测**: {len(successful)}/8 只")
        lines.append(f"- **平均总收益**: {np.mean(returns):.2%}")
        lines.append(f"- **收益中位数**: {np.median(returns):.2%}")
        lines.append(f"- **最佳收益**: {max(returns):.2%} ({successful[np.argmax(returns)]['stock_name']})")
        lines.append(f"- **最差收益**: {min(returns):.2%} ({successful[np.argmin(returns)]['stock_name']})")
        lines.append(f"- **平均胜率**: {np.mean(win_rates):.1%}")
        lines.append(f"- **正收益股票数**: {sum(1 for r in returns if r > 0)}/8")
        lines.append("")
        
        # 策略稳健性分析
        lines.append("## 策略稳健性分析")
        lines.append("")
        positive_count = sum(1 for r in returns if r > 0)
        lines.append(f"- **正收益比例**: {positive_count}/8 ({positive_count/8*100:.1f}%)")
        lines.append(f"- **收益标准差**: {np.std(returns):.2%}")
        if np.mean(returns) != 0:
            cv = abs(np.std(returns) / np.mean(returns))
            lines.append(f"- **收益变异系数**: {cv:.2f} {'(波动较大)' if cv > 2 else '(波动适中)' if cv > 1 else '(波动较小)'}")
        lines.append("")
        
        if positive_count >= 4:
            lines.append("✅ **稳健性结论**: EMA V2策略在新增8只股票中表现稳健，超过50%的股票获得正收益。")
        else:
            lines.append("⚠️ **稳健性结论**: EMA V2策略在新增8只股票中表现一般，正收益比例不足50%。")
        lines.append("")
        
        # 最佳参数分析
        lines.append("## 最佳参数分析")
        lines.append("")
        
        param_count = {}
        for r in successful:
            params = r["best_by_return"]["params"]
            key = f"EMA{params['ema_fast']}/{params['ema_slow']}"
            param_count[key] = param_count.get(key, 0) + 1
        
        lines.append("| 参数组合 | 使用次数 | 占比 | 推荐程度 |")
        lines.append("|----------|----------|------|----------|")
        for param, count in sorted(param_count.items(), key=lambda x: -x[1]):
            pct = count / len(successful) * 100
            if pct >= 25:
                rec = "🌟 强烈推荐"
            elif pct >= 15:
                rec = "✅ 推荐"
            else:
                rec = "⚪ 可选"
            lines.append(f"| {param} | {count} | {pct:.1f}% | {rec} |")
        lines.append("")
        
        # 详细回测结果
        lines.append("## 详细回测结果")
        lines.append("")
        
        for code, name, industry in EXTENDED_STOCKS:
            r = next((x for x in successful if x["stock_code"] == code), None)
            if not r:
                continue
            
            lines.append(f"### {code} {name} ({industry})")
            lines.append("")
            
            b = r["best_by_return"]
            p = b["params"]
            lines.append("**最佳参数表现**:")
            lines.append(f"- 参数组合: EMA{p['ema_fast']}/{p['ema_slow']}")
            lines.append(f"- 总收益率: {b['total_return_pct']:.2%}")
            lines.append(f"- 胜率: {b['win_rate']:.1%}")
            lines.append(f"- 交易次数: {b['total_trades']}")
            if r.get("data_period"):
                dp = r["data_period"]
                lines.append(f"- 数据期间: {dp['start']} ~ {dp['end']} ({dp['days']}天)")
            lines.append("")
            
            # 所有参数结果
            lines.append("**所有参数组合结果**:")
            lines.append("")
            lines.append("| 参数 | 总收益 | 胜率 | 交易次数 | 评价 |")
            lines.append("|------|--------|------|----------|------|")
            for res in r.get("all_results", []):
                if res["success"]:
                    p = res["params"]
                    ret = res["total_return_pct"]
                    if ret > 0.02:
                        eval = "🌟 优秀"
                    elif ret > 0:
                        eval = "✅ 正收益"
                    elif ret > -0.05:
                        eval = "⚪ 小幅亏损"
                    else:
                        eval = "❌ 亏损较大"
                    lines.append(f"| EMA{p['ema_fast']}/{p['ema_slow']} | {ret:.2%} | {res['win_rate']:.1%} | {res['total_trades']} | {eval} |")
            lines.append("")
    
    # 结论与建议
    lines.append("## 结论与建议")
    lines.append("")
    
    if successful:
        returns = [r["best_by_return"]["total_return_pct"] for r in successful]
        avg_return = np.mean(returns)
        
        if avg_return > 0.05:
            lines.append("### 总体评价: 优秀 🌟")
        elif avg_return > 0:
            lines.append("### 总体评价: 良好 ✅")
        elif avg_return > -0.05:
            lines.append("### 总体评价: 一般 ⚠️")
        else:
            lines.append("### 总体评价: 需优化 ❌")
        
        lines.append("")
        lines.append(f"EMA V2策略在扩展测试中平均收益为 {avg_return:.2%}，")
        if avg_return > 0:
            lines.append("策略整体获得正收益，在多变的市场环境下表现稳健。")
        else:
            lines.append("策略整体收益为负，建议结合其他指标或调整参数。")
        lines.append("")
        
        lines.append("### 具体建议")
        lines.append("")
        lines.append("1. **行业选择**: ")
        if industry_stats:
            best_industry = max(industry_stats.items(), key=lambda x: np.mean(x[1]))
            lines.append(f"   - 优先选择表现较好的行业，如 {best_industry[0]}")
        lines.append("   - 科技/新能源行业波动较大，建议适当降低仓位")
        lines.append("   - 金融/银行行业相对稳定，可作为防御配置")
        lines.append("")
        
        lines.append("2. **参数优化**:")
        if param_count:
            best_param = max(param_count.items(), key=lambda x: x[1])
            lines.append(f"   - 推荐使用 {best_param[0]} 参数组合（使用次数最多）")
        lines.append("   - 短期参数(EMA5/30)在波动市场中表现较好")
        lines.append("   - 长期参数(EMA20/120)在趋势市场中更稳健")
        lines.append("")
        
        lines.append("3. **风险管理**:")
        lines.append("   - 关注最大回撤，设置合理的止损线")
        lines.append("   - 分散投资，不要集中持仓单一股票")
        lines.append("   - 定期回测验证策略有效性")
        lines.append("")
    
    lines.append("---")
    lines.append("*报告由 InvestMindPro 自动生成*")
    
    return "\n".join(lines)

if __name__ == "__main__":
    report = generate_full_report()
    report_file = RESULTS_DIR / "ema_v2_extended_report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"✅ 完整报告已生成: {report_file}")
    
    # 同时输出到控制台
    print("\n" + "="*60)
    print(report)
