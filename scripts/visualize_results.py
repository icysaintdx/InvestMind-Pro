#!/usr/bin/env python3
"""
回测结果可视化工具
生成收益对比图、净值曲线等
"""

import sys
import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 无GUI环境

from pathlib import Path
from typing import Dict, List

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

def load_latest_results(results_dir: Path) -> Dict:
    """加载最新的回测结果"""
    json_files = sorted(results_dir.glob("ema_v2_backtest_real_*.json"))
    if not json_files:
        print("❌ 未找到回测结果文件")
        return None
    
    latest_file = json_files[-1]
    print(f"📊 加载: {latest_file.name}")
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def plot_returns_bar(data: Dict, output_file: Path):
    """绘制收益柱状图"""
    results = data.get('results', [])
    if not results:
        return
    
    symbols = [r['symbol'] for r in results]
    returns = [r['total_return'] * 100 if r['total_return'] < 10 else r['total_return'] for r in results]
    colors = ['green' if r > 0 else 'red' for r in returns]
    
    fig, ax = plt.subplots(figsize=(14, 6))
    bars = ax.bar(symbols, returns, color=colors, alpha=0.7)
    
    # 添加数值标签
    for bar, ret in zip(bars, returns):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{ret:.1f}%', ha='center', va='bottom', fontsize=8)
    
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax.set_xlabel('Stock Symbol')
    ax.set_ylabel('Total Return (%)')
    ax.set_title('EMA V2.1 Backtest Returns (20 Stocks)')
    ax.tick_params(axis='x', rotation=45)
    plt.tight_layout()
    
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"📈 保存收益图: {output_file.name}")

def plot_winrate_scatter(data: Dict, output_file: Path):
    """绘制胜率-收益散点图"""
    results = data.get('results', [])
    if not results:
        return
    
    win_rates = [r['win_rate'] * 100 for r in results]
    returns = [r['total_return'] * 100 for r in results]
    symbols = [r['symbol'] for r in results]
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # 按波动类型着色
    high_vol = ['002460', '002594', '300014', '300750', '300124', '601888']
    low_vol = ['600519', '601398', '601318', '000001', '600036', '600900', '601288']
    
    colors = []
    for s in symbols:
        if s in high_vol:
            colors.append('red')
        elif s in low_vol:
            colors.append('green')
        else:
            colors.append('orange')
    
    scatter = ax.scatter(win_rates, returns, c=colors, s=100, alpha=0.6)
    
    # 添加标签
    for i, symbol in enumerate(symbols):
        ax.annotate(symbol, (win_rates[i], returns[i]), fontsize=8, alpha=0.7)
    
    ax.set_xlabel('Win Rate (%)')
    ax.set_ylabel('Total Return (%)')
    ax.set_title('Win Rate vs Return (Red=High Vol, Orange=Med, Green=Low)')
    ax.axhline(y=0, color='black', linestyle='--', alpha=0.3)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"📈 保存散点图: {output_file.name}")

def generate_summary_table(data: Dict, output_file: Path):
    """生成汇总表格"""
    results = data.get('results', [])
    if not results:
        return
    
    # 统计
    total_stocks = len(results)
    profitable = sum(1 for r in results if r['total_return'] > 0)
    avg_return = sum(r['total_return'] for r in results) / total_stocks
    avg_winrate = sum(r['win_rate'] for r in results) / total_stocks
    
    # 分类统计
    high_vol = ['002460', '002594', '300014', '300750', '300124', '601888']
    low_vol = ['600519', '601398', '601318', '000001', '600036', '600900', '601288']
    
    high_returns = [r['total_return'] for r in results if r['symbol'] in high_vol]
    low_returns = [r['total_return'] for r in results if r['symbol'] in low_vol]
    med_returns = [r['total_return'] for r in results 
                   if r['symbol'] not in high_vol and r['symbol'] not in low_vol]
    
    content = f"""# EMA V2.1 回测汇总

## 总体统计

| 指标 | 数值 |
|------|------|
| 股票数量 | {total_stocks} |
| 盈利股票 | {profitable}/{total_stocks} ({profitable/total_stocks*100:.1f}%) |
| 平均收益率 | {avg_return*100:.2f}% |
| 平均胜率 | {avg_winrate*100:.1f}% |

## 按波动率分类

| 类型 | 股票数 | 平均收益 | 说明 |
|------|--------|----------|------|
| 高波动 | {len(high_returns)} | {sum(high_returns)/len(high_returns)*100:.2f}% | 新能源/科技股 |
| 中波动 | {len(med_returns)} | {sum(med_returns)/len(med_returns)*100:.2f}% | 消费/医药 |
| 低波动 | {len(low_returns)} | {sum(low_returns)/len(low_returns)*100:.2f}% | 银行/白酒 |

## Top 5 收益

"""
    
    sorted_results = sorted(results, key=lambda x: x['total_return'], reverse=True)
    for i, r in enumerate(sorted_results[:5], 1):
        content += f"{i}. **{r['symbol']}**: {r['total_return']*100:.2f}% (胜率{r['win_rate']*100:.1f}%)\n"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"📝 保存汇总表: {output_file.name}")

def main():
    """主函数"""
    results_dir = Path(__file__).parent.parent / "results"
    
    data = load_latest_results(results_dir)
    if not data:
        return
    
    print(f"\n📊 生成可视化图表...\n")
    
    # 生成图表
    plot_returns_bar(data, results_dir / "returns_chart.png")
    plot_winrate_scatter(data, results_dir / "winrate_scatter.png")
    generate_summary_table(data, results_dir / "SUMMARY.md")
    
    print(f"\n✅ 完成! 图表保存在: {results_dir}")

if __name__ == "__main__":
    main()
