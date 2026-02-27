#!/usr/bin/env python3
"""
遗传算法参数优化器 - EMA V2策略
针对亏损股票进行参数优化

优化参数:
- fast_ema: 2-20 (整数)
- slow_ema: 10-60 (整数)
- atr_multiplier: 1.0-4.0 (浮点数)

目标函数: 最大化收益 + 最小化回撤惩罚
"""

import sys
import random
import copy
import json
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

sys.path.insert(0, '/home/icysaintdx/.openclaw/workspace/InvestMindPro')

import pandas as pd
import numpy as np
from strategies.ema_v2 import EMAV2Strategy, BacktestResult


@dataclass
class Individual:
    """遗传算法个体"""
    fast_ema: int
    slow_ema: int
    atr_multiplier: float
    fitness: float = 0.0
    backtest_result: Optional[BacktestResult] = None
    
    def to_params(self) -> Dict:
        return {
            "fast_ema": self.fast_ema,
            "slow_ema": self.slow_ema,
            "atr_period": 14,
            "atr_multiplier": self.atr_multiplier,
            "market_filter": True
        }
    
    @classmethod
    def from_params(cls, params: Dict) -> 'Individual':
        return cls(
            fast_ema=params.get('fast_ema', 10),
            slow_ema=params.get('slow_ema', 30),
            atr_multiplier=params.get('atr_multiplier', 2.0)
        )


class GeneticOptimizer:
    """遗传算法优化器"""
    
    def __init__(self, 
                 population_size: int = 30,
                 generations: int = 50,
                 crossover_rate: float = 0.8,
                 mutation_rate: float = 0.15,
                 elitism_count: int = 3,
                 fast_ema_range: Tuple[int, int] = (2, 20),
                 slow_ema_range: Tuple[int, int] = (10, 60),
                 atr_mult_range: Tuple[float, float] = (1.0, 4.0)):
        
        self.population_size = population_size
        self.generations = generations
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.elitism_count = elitism_count
        
        self.fast_ema_range = fast_ema_range
        self.slow_ema_range = slow_ema_range
        self.atr_mult_range = atr_mult_range
        
        self.best_individuals = []
        self.fitness_history = []
    
    def create_individual(self) -> Individual:
        """创建随机个体"""
        fast_ema = random.randint(self.fast_ema_range[0], self.fast_ema_range[1])
        slow_ema = random.randint(self.slow_ema_range[0], self.slow_ema_range[1])
        
        # 确保 fast_ema < slow_ema
        while fast_ema >= slow_ema:
            fast_ema = random.randint(self.fast_ema_range[0], self.fast_ema_range[1])
            slow_ema = random.randint(self.slow_ema_range[0], self.slow_ema_range[1])
        
        atr_mult = random.uniform(self.atr_mult_range[0], self.atr_mult_range[1])
        
        return Individual(fast_ema, slow_ema, round(atr_mult, 2))
    
    def create_population(self) -> List[Individual]:
        """创建初始种群"""
        return [self.create_individual() for _ in range(self.population_size)]
    
    def evaluate_fitness(self, individual: Individual, df: pd.DataFrame, 
                        market_data: Optional[pd.DataFrame] = None) -> float:
        """
        评估个体适应度
        
        目标函数: 收益 - 回撤惩罚 + 交易次数奖励
        - 收益权重: 1.0
        - 回撤惩罚权重: 0.5
        - 最低交易次数: 3次（避免过拟合）
        """
        try:
            strategy = EMAV2Strategy(params=individual.to_params())
            result = strategy.run_backtest(df, market_data)
            
            individual.backtest_result = result
            
            # 基础适应度 = 总收益
            fitness = result.total_return
            
            # 回撤惩罚 (回撤越大，惩罚越重)
            drawdown_penalty = abs(result.max_drawdown) * 0.5
            fitness -= drawdown_penalty
            
            # 交易次数惩罚（少于3次认为过拟合）
            if result.total_trades < 3:
                fitness -= 50  # 严重惩罚
            elif result.total_trades < 5:
                fitness -= 20  # 轻微惩罚
            
            # 夏普比率奖励
            if result.sharpe_ratio > 0:
                fitness += result.sharpe_ratio * 5
            
            individual.fitness = fitness
            return fitness
            
        except Exception as e:
            individual.fitness = -1000  # 错误时给予很低适应度
            return -1000
    
    def tournament_selection(self, population: List[Individual], 
                            tournament_size: int = 3) -> Individual:
        """锦标赛选择"""
        tournament = random.sample(population, min(tournament_size, len(population)))
        return max(tournament, key=lambda x: x.fitness)
    
    def crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        """交叉操作"""
        if random.random() > self.crossover_rate:
            return copy.copy(parent1), copy.copy(parent2)
        
        child1 = copy.copy(parent1)
        child2 = copy.copy(parent2)
        
        # 单点交叉 - fast_ema
        if random.random() < 0.5:
            child1.fast_ema, child2.fast_ema = child2.fast_ema, child1.fast_ema
        
        # 单点交叉 - slow_ema
        if random.random() < 0.5:
            child1.slow_ema, child2.slow_ema = child2.slow_ema, child1.slow_ema
        
        # 算术交叉 - atr_multiplier
        if random.random() < 0.5:
            alpha = random.random()
            child1.atr_multiplier = round(alpha * parent1.atr_multiplier + 
                                         (1-alpha) * parent2.atr_multiplier, 2)
            child2.atr_multiplier = round(alpha * parent2.atr_multiplier + 
                                         (1-alpha) * parent1.atr_multiplier, 2)
        
        # 确保 fast_ema < slow_ema
        for child in [child1, child2]:
            if child.fast_ema >= child.slow_ema:
                child.slow_ema = child.fast_ema + random.randint(5, 20)
                if child.slow_ema > self.slow_ema_range[1]:
                    child.slow_ema = self.slow_ema_range[1]
                    child.fast_ema = child.slow_ema - random.randint(5, 15)
        
        return child1, child2
    
    def mutate(self, individual: Individual) -> Individual:
        """变异操作"""
        mutant = copy.copy(individual)
        
        # fast_ema 变异
        if random.random() < self.mutation_rate:
            delta = random.randint(-3, 3)
            mutant.fast_ema += delta
            mutant.fast_ema = max(self.fast_ema_range[0], 
                                 min(self.fast_ema_range[1], mutant.fast_ema))
        
        # slow_ema 变异
        if random.random() < self.mutation_rate:
            delta = random.randint(-5, 5)
            mutant.slow_ema += delta
            mutant.slow_ema = max(self.slow_ema_range[0], 
                                 min(self.slow_ema_range[1], mutant.slow_ema))
        
        # atr_multiplier 变异
        if random.random() < self.mutation_rate:
            delta = random.uniform(-0.5, 0.5)
            mutant.atr_multiplier += delta
            mutant.atr_multiplier = round(max(self.atr_mult_range[0], 
                                             min(self.atr_mult_range[1], 
                                                 mutant.atr_multiplier)), 2)
        
        # 确保 fast_ema < slow_ema
        if mutant.fast_ema >= mutant.slow_ema:
            mutant.slow_ema = mutant.fast_ema + random.randint(5, 20)
            if mutant.slow_ema > self.slow_ema_range[1]:
                mutant.slow_ema = self.slow_ema_range[1]
                mutant.fast_ema = max(self.fast_ema_range[0], mutant.slow_ema - 15)
        
        return mutant
    
    def optimize(self, df: pd.DataFrame, market_data: Optional[pd.DataFrame] = None,
                verbose: bool = True) -> Dict:
        """
        执行遗传算法优化
        
        Returns:
            Dict 包含最优个体和优化历史
        """
        # 创建初始种群
        population = self.create_population()
        
        if verbose:
            print(f"\n开始遗传算法优化:")
            print(f"  种群大小: {self.population_size}")
            print(f"  迭代代数: {self.generations}")
            print(f"  交叉概率: {self.crossover_rate}")
            print(f"  变异概率: {self.mutation_rate}")
        
        for generation in range(self.generations):
            # 评估适应度
            for individual in population:
                if individual.fitness == 0:  # 未评估的个体
                    self.evaluate_fitness(individual, df, market_data)
            
            # 按适应度排序
            population.sort(key=lambda x: x.fitness, reverse=True)
            
            # 记录最佳个体
            best = population[0]
            self.best_individuals.append(copy.copy(best))
            self.fitness_history.append(best.fitness)
            
            if verbose and (generation % 10 == 0 or generation == self.generations - 1):
                result = best.backtest_result
                if result:
                    print(f"  Gen {generation:3d}: "
                          f"Fitness={best.fitness:8.2f}, "
                          f"Return={result.total_return:7.2f}%, "
                          f"DD={result.max_drawdown:6.2f}%, "
                          f"Trades={result.total_trades}")
            
            # 创建新一代
            new_population = []
            
            # 精英保留
            new_population.extend(population[:self.elitism_count])
            
            # 生成新个体
            while len(new_population) < self.population_size:
                parent1 = self.tournament_selection(population)
                parent2 = self.tournament_selection(population)
                
                child1, child2 = self.crossover(parent1, parent2)
                child1 = self.mutate(child1)
                child2 = self.mutate(child2)
                
                new_population.extend([child1, child2])
            
            population = new_population[:self.population_size]
        
        # 最终排序
        for individual in population:
            if individual.fitness == 0:
                self.evaluate_fitness(individual, df, market_data)
        
        population.sort(key=lambda x: x.fitness, reverse=True)
        
        return {
            'best_individual': population[0],
            'best_result': population[0].backtest_result,
            'fitness_history': self.fitness_history,
            'final_population': population
        }


def load_stock_data(symbol: str) -> pd.DataFrame:
    """加载股票数据"""
    df = pd.read_csv(f'/home/icysaintdx/.openclaw/workspace/InvestMindPro/data/{symbol}.csv')
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    df.set_index('date', inplace=True)
    df.attrs['symbol'] = symbol
    return df


def run_default_backtest(symbol: str, name: str) -> Dict:
    """使用默认参数运行回测"""
    df = load_stock_data(symbol)
    
    # 使用中等波动率默认参数
    strategy = EMAV2Strategy(volatility_type="medium_volatility")
    result = strategy.run_backtest(df, initial_capital=100000)
    
    return {
        'symbol': symbol,
        'name': name,
        'return': result.total_return,
        'win_rate': result.win_rate,
        'trades': result.total_trades,
        'max_drawdown': result.max_drawdown,
        'sharpe': result.sharpe_ratio,
        'params': strategy.params
    }


def run_genetic_optimization(symbol: str, name: str) -> Dict:
    """对单只股票执行遗传算法优化"""
    print(f"\n{'='*70}")
    print(f"优化股票: {symbol} - {name}")
    print(f"{'='*70}")
    
    # 加载数据
    df = load_stock_data(symbol)
    print(f"数据范围: {df.index[0].strftime('%Y-%m-%d')} ~ {df.index[-1].strftime('%Y-%m-%d')}")
    print(f"数据条数: {len(df)}")
    
    # 执行遗传算法优化
    optimizer = GeneticOptimizer(
        population_size=30,
        generations=50,
        crossover_rate=0.8,
        mutation_rate=0.15,
        elitism_count=3,
        fast_ema_range=(2, 20),
        slow_ema_range=(10, 60),
        atr_mult_range=(1.0, 4.0)
    )
    
    result = optimizer.optimize(df, verbose=True)
    
    best = result['best_individual']
    bt_result = result['best_result']
    
    print(f"\n优化完成!")
    print(f"最优参数: {best.to_params()}")
    print(f"最优收益: {bt_result.total_return:.2f}%")
    print(f"胜率: {bt_result.win_rate:.1f}%")
    print(f"交易次数: {bt_result.total_trades}")
    print(f"最大回撤: {bt_result.max_drawdown:.2f}%")
    
    return {
        'symbol': symbol,
        'name': name,
        'optimized_params': best.to_params(),
        'fitness': best.fitness,
        'total_return': bt_result.total_return,
        'win_rate': bt_result.win_rate,
        'total_trades': bt_result.total_trades,
        'max_drawdown': bt_result.max_drawdown,
        'sharpe_ratio': bt_result.sharpe_ratio,
        'fitness_history': result['fitness_history']
    }


def main():
    """主函数"""
    print("="*70)
    print("EMA V2 策略 - 遗传算法参数优化")
    print("="*70)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 5只亏损股票
    stocks = [
        ('300033', '同花顺', -45.62),
        ('000651', '格力电器', -31.56),
        ('688981', '中芯国际', -27.84),
        ('002714', '牧原股份', -26.23),
        ('603288', '海天味业', -10.84)
    ]
    
    results = {
        'optimization_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'stocks': []
    }
    
    for symbol, name, original_return in stocks:
        # 先运行默认参数回测
        default_result = run_default_backtest(symbol, name)
        print(f"\n默认参数回测: {symbol} {name}")
        print(f"  收益: {default_result['return']:.2f}%, 胜率: {default_result['win_rate']:.1f}%, 交易: {default_result['trades']}")
        
        # 执行遗传算法优化
        opt_result = run_genetic_optimization(symbol, name)
        opt_result['original_return'] = original_return
        opt_result['default_return'] = default_result['return']
        opt_result['improvement'] = opt_result['total_return'] - original_return
        opt_result['vs_default'] = opt_result['total_return'] - default_result['return']
        
        results['stocks'].append({
            'symbol': symbol,
            'name': name,
            'default_result': default_result,
            'optimized_result': opt_result
        })
    
    # 保存结果
    results_dir = '/home/icysaintdx/.openclaw/workspace/InvestMindPro/results'
    
    # JSON格式保存详细数据
    json_path = f'{results_dir}/genetic_optimization_detail.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n详细结果已保存: {json_path}")
    
    # 生成Markdown报告
    generate_report(results)
    
    return results


def generate_report(results: Dict):
    """生成Markdown格式的优化报告"""
    
    report = f"""# 遗传算法参数优化报告

**生成时间**: {results['optimization_date']}  
**优化方法**: 遗传算法  
**种群大小**: 30  
**迭代代数**: 50  

---

## 执行摘要

本次优化针对5只EMA V2策略下表现亏损的股票，使用遗传算法搜索最优参数组合。

### 优化参数范围
| 参数 | 最小值 | 最大值 |
|------|--------|--------|
| fast_ema | 2 | 20 |
| slow_ema | 10 | 60 |
| atr_multiplier | 1.0 | 4.0 |

### 目标函数
```
Fitness = 总收益 - 0.5×|最大回撤| + 5×夏普比率 - 交易次数惩罚
```

---

## 优化结果详情

"""
    
    # 汇总表
    report += "### 优化前后对比\n\n"
    report += "| 股票代码 | 股票名称 | 原收益 | 默认参数收益 | 优化后收益 | 改进幅度 | 交易次数 | 最大回撤 | 建议 |\n"
    report += "|----------|----------|--------|--------------|------------|----------|----------|----------|------|\n"
    
    for stock in results['stocks']:
        symbol = stock['symbol']
        name = stock['name']
        opt = stock['optimized_result']
        
        original = opt['original_return']
        default = opt['default_return']
        optimized = opt['total_return']
        improvement = opt['improvement']
        trades = opt['total_trades']
        dd = opt['max_drawdown']
        
        # 建议
        if optimized > 0:
            recommendation = "✅ 保留"
        elif improvement > 20:
            recommendation = "⚠️ 观察"
        else:
            recommendation = "❌ 移除"
        
        report += f"| {symbol} | {name} | {original:.2f}% | {default:.2f}% | **{optimized:.2f}%** | {improvement:+.2f}% | {trades} | {dd:.2f}% | {recommendation} |\n"
    
    report += "\n---\n\n"
    
    # 详细结果
    report += "## 各股票详细分析\n\n"
    
    for stock in results['stocks']:
        symbol = stock['symbol']
        name = stock['name']
        opt = stock['optimized_result']
        default = stock['default_result']
        
        report += f"### {symbol} - {name}\n\n"
        
        # 收益对比
        report += "#### 收益对比\n\n"
        report += f"- **原始回测收益**: {opt['original_return']:.2f}%\n"
        report += f"- **默认参数收益**: {default['return']:.2f}%\n"
        report += f"- **优化后收益**: **{opt['total_return']:.2f}%**\n"
        report += f"- **改进幅度**: {opt['improvement']:+.2f}%\n\n"
        
        # 最优参数
        params = opt['optimized_params']
        report += "#### 推荐参数组合\n\n"
        report += "```python\n"
        report += f'{symbol}_PARAMS = {{\n'
        report += f'    "fast_ema": {params["fast_ema"]},\n'
        report += f'    "slow_ema": {params["slow_ema"]},\n'
        report += f'    "atr_period": {params["atr_period"]},\n'
        report += f'    "atr_multiplier": {params["atr_multiplier"]},\n'
        report += f'    "market_filter": {params["market_filter"]}\n'
        report += '}\n'
        report += "```\n\n"
        
        # 回测指标
        report += "#### 回测指标\n\n"
        report += f"| 指标 | 数值 |\n"
        report += f"|------|------|\n"
        report += f"| 总收益率 | {opt['total_return']:.2f}% |\n"
        report += f"| 胜率 | {opt['win_rate']:.1f}% |\n"
        report += f"| 交易次数 | {opt['total_trades']} |\n"
        report += f"| 最大回撤 | {opt['max_drawdown']:.2f}% |\n"
        report += f"| 夏普比率 | {opt['sharpe_ratio']:.2f} |\n"
        report += f"| 适应度得分 | {opt['fitness']:.2f} |\n\n"
        
        # 建议
        report += "#### 投资建议\n\n"
        if opt['total_return'] > 0:
            report += f"✅ **建议保留**: 优化后获得正收益 ({opt['total_return']:.2f}%)，参数有效。\n\n"
        elif opt['improvement'] > 30:
            report += f"⚠️ **建议观察**: 虽仍为负收益，但改进显著 ({opt['improvement']:+.2f}%)，可继续观察。\n\n"
        else:
            report += f"❌ **策略不适配**: 无论如何优化都无法获得正收益，建议从交易池中移除。\n\n"
        
        report += "---\n\n"
    
    # 总体建议
    report += "## 总体建议\n\n"
    report += "### 交易池调整建议\n\n"
    
    keep_list = []
    observe_list = []
    remove_list = []
    
    for stock in results['stocks']:
        symbol = stock['symbol']
        name = stock['name']
        opt = stock['optimized_result']
        
        if opt['total_return'] > 0:
            keep_list.append(f"{symbol} ({name})")
        elif opt['improvement'] > 30:
            observe_list.append(f"{symbol} ({name})")
        else:
            remove_list.append(f"{symbol} ({name})")
    
    if keep_list:
        report += "**✅ 建议保留（优化后正收益）**:\n"
        for item in keep_list:
            report += f"- {item}\n"
        report += "\n"
    
    if observe_list:
        report += "**⚠️ 建议观察（改进显著但仍亏损）**:\n"
        for item in observe_list:
            report += f"- {item}\n"
        report += "\n"
    
    if remove_list:
        report += "**❌ 建议移除（策略不适配）**:\n"
        for item in remove_list:
            report += f"- {item}\n"
        report += "\n"
    
    # 技术说明
    report += """## 技术说明

### 遗传算法配置
- **种群大小**: 30
- **迭代代数**: 50
- **交叉概率**: 0.8
- **变异概率**: 0.15
- **精英保留**: 3个最佳个体

### 参数编码
- `fast_ema`: 整数，范围 [2, 20]
- `slow_ema`: 整数，范围 [10, 60]
- `atr_multiplier`: 浮点数，范围 [1.0, 4.0]

### 约束条件
- 必须满足: fast_ema < slow_ema
- 最小交易次数: 3次（避免过拟合）

### 选择算子
锦标赛选择 (Tournament Selection)，锦标赛大小为3

### 交叉算子
- EMA参数: 单点交叉
- ATR倍数: 算术交叉

### 变异算子
- EMA参数: 随机整数偏移 [-3, 3] 和 [-5, 5]
- ATR倍数: 随机浮点偏移 [-0.5, 0.5]

---

*报告由 InvestMindPro 自动生成*
"""
    
    # 保存报告
    report_path = '/home/icysaintdx/.openclaw/workspace/InvestMindPro/results/GENETIC_OPTIMIZATION_REPORT.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n优化报告已生成: {report_path}")


if __name__ == '__main__':
    main()
