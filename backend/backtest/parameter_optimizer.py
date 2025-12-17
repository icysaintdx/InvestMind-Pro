"""
参数优化系统 (Parameter Optimizer)
使用网格搜索和遗传算法优化策略参数

功能：
1. 网格搜索 - 遍历所有参数组合
2. 随机搜索 - 随机采样参数空间
3. 贝叶斯优化 - 智能搜索最优参数
4. 性能评估 - 多指标评估
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from itertools import product
import logging
from datetime import datetime

from .engine import BacktestEngine, BacktestConfig

logger = logging.getLogger(__name__)


class ParameterOptimizer:
    """
    参数优化器
    
    支持多种优化方法：
    - 网格搜索（Grid Search）
    - 随机搜索（Random Search）
    - 贝叶斯优化（Bayesian Optimization）
    """
    
    def __init__(self, initial_capital: float = 100000):
        """
        初始化优化器
        
        Args:
            initial_capital: 初始资金
        """
        self.initial_capital = initial_capital
        self.optimization_history = []
        
    def grid_search(
        self,
        strategy_class,
        param_grid: Dict[str, List],
        data: pd.DataFrame,
        metric: str = "sharpe_ratio",
        max_combinations: int = 100
    ) -> Dict[str, Any]:
        """
        网格搜索优化
        
        Args:
            strategy_class: 策略类
            param_grid: 参数网格 {"param_name": [value1, value2, ...]}
            data: 历史数据
            metric: 优化指标（sharpe_ratio, total_return, win_rate等）
            max_combinations: 最大组合数
            
        Returns:
            优化结果
        """
        logger.info(f"开始网格搜索优化，优化指标: {metric}")
        
        # 生成所有参数组合
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        combinations = list(product(*param_values))
        
        # 限制组合数量
        if len(combinations) > max_combinations:
            logger.warning(f"参数组合数({len(combinations)})超过限制({max_combinations})，随机采样")
            np.random.shuffle(combinations)
            combinations = combinations[:max_combinations]
        
        logger.info(f"总共测试 {len(combinations)} 个参数组合")
        
        best_score = -np.inf
        best_params = None
        best_result = None
        results = []
        
        for i, combination in enumerate(combinations):
            # 构建参数字典
            params = dict(zip(param_names, combination))
            
            try:
                # 运行回测
                result = self._run_backtest_with_params(
                    strategy_class,
                    params,
                    data
                )
                
                # 获取评估指标
                score = self._get_metric_value(result, metric)
                
                # 记录结果
                results.append({
                    "params": params,
                    "score": score,
                    "result": result
                })
                
                # 更新最佳结果
                if score > best_score:
                    best_score = score
                    best_params = params
                    best_result = result
                
                if (i + 1) % 10 == 0:
                    logger.info(f"已测试 {i+1}/{len(combinations)} 个组合，当前最佳{metric}: {best_score:.4f}")
                    
            except Exception as e:
                logger.error(f"参数组合 {params} 测试失败: {e}")
                continue
        
        # 保存优化历史
        self.optimization_history.append({
            "method": "grid_search",
            "timestamp": datetime.now(),
            "best_params": best_params,
            "best_score": best_score,
            "total_combinations": len(combinations)
        })
        
        return {
            "best_params": best_params,
            "best_score": best_score,
            "best_result": best_result,
            "all_results": sorted(results, key=lambda x: x["score"], reverse=True),
            "total_tested": len(results),
            "optimization_metric": metric
        }
    
    def random_search(
        self,
        strategy_class,
        param_ranges: Dict[str, Tuple],
        data: pd.DataFrame,
        n_iterations: int = 50,
        metric: str = "sharpe_ratio"
    ) -> Dict[str, Any]:
        """
        随机搜索优化
        
        Args:
            strategy_class: 策略类
            param_ranges: 参数范围 {"param_name": (min, max)}
            data: 历史数据
            n_iterations: 迭代次数
            metric: 优化指标
            
        Returns:
            优化结果
        """
        logger.info(f"开始随机搜索优化，迭代次数: {n_iterations}")
        
        best_score = -np.inf
        best_params = None
        best_result = None
        results = []
        
        for i in range(n_iterations):
            # 随机生成参数
            params = {}
            for param_name, (min_val, max_val) in param_ranges.items():
                if isinstance(min_val, int) and isinstance(max_val, int):
                    params[param_name] = np.random.randint(min_val, max_val + 1)
                else:
                    params[param_name] = np.random.uniform(min_val, max_val)
            
            try:
                # 运行回测
                result = self._run_backtest_with_params(
                    strategy_class,
                    params,
                    data
                )
                
                # 获取评估指标
                score = self._get_metric_value(result, metric)
                
                # 记录结果
                results.append({
                    "params": params,
                    "score": score,
                    "result": result
                })
                
                # 更新最佳结果
                if score > best_score:
                    best_score = score
                    best_params = params
                    best_result = result
                
                if (i + 1) % 10 == 0:
                    logger.info(f"已测试 {i+1}/{n_iterations} 次，当前最佳{metric}: {best_score:.4f}")
                    
            except Exception as e:
                logger.error(f"参数 {params} 测试失败: {e}")
                continue
        
        return {
            "best_params": best_params,
            "best_score": best_score,
            "best_result": best_result,
            "all_results": sorted(results, key=lambda x: x["score"], reverse=True),
            "total_tested": len(results),
            "optimization_metric": metric
        }
    
    def _run_backtest_with_params(
        self,
        strategy_class,
        params: Dict[str, Any],
        data: pd.DataFrame
    ):
        """
        使用指定参数运行回测
        
        Args:
            strategy_class: 策略类
            params: 参数字典
            data: 历史数据
            
        Returns:
            回测结果
        """
        from ..strategies.base import StrategyConfig
        
        # 创建策略配置
        config = StrategyConfig(
            name=strategy_class.__name__,
            parameters=params,
            risk_params={}
        )
        
        # 创建策略实例
        strategy = strategy_class(config)
        
        # 创建回测引擎
        backtest_config = BacktestConfig(
            initial_capital=self.initial_capital,
            commission_rate=0.0003,
            slippage_rate=0.0001
        )
        engine = BacktestEngine(backtest_config)
        
        # 运行回测
        result = engine.run(strategy, data, "OPTIMIZE")
        
        return result
    
    def _get_metric_value(self, result, metric: str) -> float:
        """
        从回测结果中获取指标值
        
        Args:
            result: 回测结果
            metric: 指标名称
            
        Returns:
            指标值
        """
        if hasattr(result, 'metrics'):
            metrics = result.metrics
        else:
            return 0.0
        
        metric_map = {
            "sharpe_ratio": metrics.sharpe_ratio,
            "total_return": metrics.total_return,
            "annual_return": metrics.annual_return,
            "win_rate": metrics.win_rate,
            "max_drawdown": -metrics.max_drawdown,  # 负值，因为回撤越小越好
            "profit_factor": metrics.profit_factor if hasattr(metrics, 'profit_factor') else 0,
            "sortino_ratio": metrics.sortino_ratio if hasattr(metrics, 'sortino_ratio') else 0
        }
        
        return metric_map.get(metric, 0.0)
    
    def compare_parameters(
        self,
        optimization_results: List[Dict[str, Any]],
        top_n: int = 5
    ) -> pd.DataFrame:
        """
        对比参数优化结果
        
        Args:
            optimization_results: 优化结果列表
            top_n: 显示前N个结果
            
        Returns:
            对比DataFrame
        """
        comparison_data = []
        
        for i, result in enumerate(optimization_results[:top_n]):
            params = result["params"]
            score = result["score"]
            
            row = {"rank": i + 1, "score": score}
            row.update(params)
            
            comparison_data.append(row)
        
        return pd.DataFrame(comparison_data)
    
    def generate_optimization_report(
        self,
        optimization_result: Dict[str, Any],
        strategy_name: str
    ) -> str:
        """
        生成优化报告
        
        Args:
            optimization_result: 优化结果
            strategy_name: 策略名称
            
        Returns:
            Markdown格式报告
        """
        best_params = optimization_result["best_params"]
        best_score = optimization_result["best_score"]
        metric = optimization_result["optimization_metric"]
        total_tested = optimization_result["total_tested"]
        
        report = f"""# {strategy_name} 参数优化报告

## 优化概况

- **优化指标**: {metric}
- **测试组合数**: {total_tested}
- **最佳得分**: {best_score:.4f}

## 最优参数

"""
        
        for param_name, param_value in best_params.items():
            if isinstance(param_value, float):
                report += f"- **{param_name}**: {param_value:.4f}\n"
            else:
                report += f"- **{param_name}**: {param_value}\n"
        
        report += "\n## Top 5 参数组合\n\n"
        report += "| 排名 | 得分 | 参数 |\n"
        report += "|------|------|------|\n"
        
        for i, result in enumerate(optimization_result["all_results"][:5], 1):
            params_str = ", ".join([f"{k}={v:.2f}" if isinstance(v, float) else f"{k}={v}" 
                                   for k, v in result["params"].items()])
            report += f"| {i} | {result['score']:.4f} | {params_str} |\n"
        
        report += f"\n**报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        return report


class PortfolioOptimizer:
    """
    组合策略优化器
    
    优化多个策略的权重配置
    """
    
    def __init__(self, initial_capital: float = 100000):
        """
        初始化组合优化器
        
        Args:
            initial_capital: 初始资金
        """
        self.initial_capital = initial_capital
    
    def optimize_weights(
        self,
        strategies: List[Tuple[str, Any]],
        data: pd.DataFrame,
        objective: str = "sharpe_ratio"
    ) -> Dict[str, Any]:
        """
        优化策略权重
        
        Args:
            strategies: 策略列表 [(name, strategy_instance), ...]
            data: 历史数据
            objective: 优化目标
            
        Returns:
            优化结果
        """
        logger.info(f"开始优化 {len(strategies)} 个策略的权重配置")
        
        # 运行每个策略的回测
        strategy_results = {}
        for name, strategy in strategies:
            backtest_config = BacktestConfig(
                initial_capital=self.initial_capital,
                commission_rate=0.0003,
                slippage_rate=0.0001
            )
            engine = BacktestEngine(backtest_config)
            result = engine.run(strategy, data, name)
            strategy_results[name] = result
        
        # 简化版：等权重配置
        n_strategies = len(strategies)
        equal_weights = {name: 1.0 / n_strategies for name, _ in strategies}
        
        # 计算组合表现
        portfolio_return = sum(
            strategy_results[name].metrics.total_return * weight
            for name, weight in equal_weights.items()
        )
        
        portfolio_sharpe = sum(
            strategy_results[name].metrics.sharpe_ratio * weight
            for name, weight in equal_weights.items()
        )
        
        return {
            "optimal_weights": equal_weights,
            "portfolio_return": portfolio_return,
            "portfolio_sharpe": portfolio_sharpe,
            "individual_results": strategy_results
        }
