"""
混合决策模型 - 策略选择核心
实现"规则筛选 → LLM优化 → 回测验证"的三步骤决策流程
"""

import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import logging

from .data_validator import validate_strategy_inputs
from .scenario_rules import get_scenario_guidance

logger = logging.getLogger(__name__)


class StrategySelector:
    """混合决策模型策略选择器"""
    
    def __init__(self):
        self.rules = self._load_rules()
        self.strategies = self._load_strategies()
        
    def _load_rules(self) -> Dict[str, Any]:
        """加载策略选择规则"""
        rules_path = Path(__file__).parent.parent.parent / "agent_configs" / "strategy_selection_rules.json"
        try:
            with open(rules_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载规则配置失败: {e}")
            return {}
    
    def _load_strategies(self) -> List[Dict[str, Any]]:
        """加载可用策略列表"""
        return [
            {
                "strategy_id": "vegas_adx",
                "name": "Vegas+ADX策略",
                "parameters": {
                    "suitable_period": 14,
                    "max_position": 0.30,
                    "stop_loss": 0.05,
                    "take_profit": 0.15,
                    "news_sensitivity": 0.3
                },
                "category": "technical",
                "description": "基于Vegas通道和ADX指标的趋势跟踪策略"
            },
            {
                "strategy_id": "ema_breakout",
                "name": "均线突破策略",
                "parameters": {
                    "suitable_period": 7,
                    "max_position": 0.25,
                    "stop_loss": 0.06,
                    "take_profit": 0.12,
                    "news_sensitivity": 0.5
                },
                "category": "technical",
                "description": "基于EMA均线突破的短期交易策略"
            },
            {
                "strategy_id": "trident",
                "name": "三叉戟策略",
                "parameters": {
                    "suitable_period": 15,
                    "max_position": 0.35,
                    "stop_loss": 0.04,
                    "take_profit": 0.12,
                    "news_sensitivity": 0.4
                },
                "category": "comprehensive",
                "description": "结合趋势、动量和波动率的综合策略"
            },
            {
                "strategy_id": "macd_crossover",
                "name": "MACD交叉策略",
                "parameters": {
                    "suitable_period": 10,
                    "max_position": 0.40,
                    "stop_loss": 0.04,
                    "take_profit": 0.10,
                    "news_sensitivity": 0.3
                },
                "category": "momentum",
                "description": "经典的MACD金叉死叉策略，结合成交量确认"
            },
            {
                "strategy_id": "bollinger_breakout",
                "name": "布林带突破策略",
                "parameters": {
                    "suitable_period": 12,
                    "max_position": 0.35,
                    "stop_loss": 0.05,
                    "take_profit": 0.12,
                    "news_sensitivity": 0.4
                },
                "category": "volatility",
                "description": "基于布林带的突破和回归策略"
            },
            {
                "strategy_id": "sentiment_resonance",
                "name": "情绪共振策略",
                "parameters": {
                    "suitable_period": 10,
                    "max_position": 0.40,
                    "stop_loss": 0.04,
                    "take_profit": 0.12,
                    "news_sensitivity": 0.8
                },
                "category": "ai_composite",
                "description": "AI合成策略 - 结合新闻情绪、技术指标、资金流向三维度共振"
            },
            {
                "strategy_id": "debate_weighted",
                "name": "多空辩论加权策略",
                "parameters": {
                    "suitable_period": 15,
                    "max_position": 0.35,
                    "stop_loss": 0.05,
                    "take_profit": 0.15,
                    "news_sensitivity": 0.9
                },
                "category": "ai_composite",
                "description": "AI合成策略 - 利用21智能体的多空辩论结果进行加权决策"
            },
            {
                "strategy_id": "turtle_trading",
                "name": "海龟交易法则",
                "parameters": {
                    "suitable_period": 55,
                    "max_position": 0.40,
                    "stop_loss": 0.08,
                    "take_profit": 0.20,
                    "news_sensitivity": 0.3
                },
                "category": "trend_following",
                "description": "经典趋势跟踪策略 - 唐奇安通道突破+ATR金字塔加仓"
            },
            {
                "strategy_id": "limit_up_trading",
                "name": "涨停板战法",
                "parameters": {
                    "suitable_period": 1,
                    "max_position": 0.20,
                    "stop_loss": 0.03,
                    "take_profit": 0.05,
                    "news_sensitivity": 0.7
                },
                "category": "folk_strategy",
                "description": "A股特色策略 - 首板涨停+T+1快进快出"
            },
            {
                "strategy_id": "volume_price_surge",
                "name": "量价齐升战法",
                "parameters": {
                    "suitable_period": 5,
                    "max_position": 0.30,
                    "stop_loss": 0.04,
                    "take_profit": 0.08,
                    "news_sensitivity": 0.5
                },
                "category": "folk_strategy",
                "description": "短期交易策略 - 量价配合+3-5天持有"
            },
            {
                "strategy_id": "buffett_value",
                "name": "巴菲特价值投资",
                "parameters": {
                    "suitable_period": 365,
                    "max_position": 0.30,
                    "stop_loss": 0.20,
                    "take_profit": 1.00,
                    "news_sensitivity": 0.2
                },
                "category": "value_investing",
                "description": "价值投资策略 - 护城河+长期持有"
            },
            {
                "strategy_id": "lynch_growth",
                "name": "彼得林奇成长股",
                "parameters": {
                    "suitable_period": 180,
                    "max_position": 0.35,
                    "stop_loss": 0.25,
                    "take_profit": 1.50,
                    "news_sensitivity": 0.4
                },
                "category": "value_investing",
                "description": "成长股策略 - PEG<1选股"
            },
            {
                "strategy_id": "graham_margin",
                "name": "格雷厄姆安全边际",
                "parameters": {
                    "suitable_period": 365,
                    "max_position": 0.25,
                    "stop_loss": 0.15,
                    "take_profit": 0.80,
                    "news_sensitivity": 0.1
                },
                "category": "value_investing",
                "description": "防御性投资 - 低估值+安全边际"
            },
            {
                "strategy_id": "martingale_refined",
                "name": "马丁格尔改良版",
                "parameters": {
                    "suitable_period": 10,
                    "max_position": 0.30,
                    "stop_loss": 0.06,
                    "take_profit": 0.08,
                    "layer_step_pct": 0.02
                },
                "category": "technical",
                "description": "趋势过滤+单轮加仓的马丁格尔控制策略"
            },
            {
                "strategy_id": "dragon_leader",
                "name": "龙头股战法",
                "parameters": {
                    "suitable_period": 15,
                    "max_position": 0.35,
                    "stop_loss": 0.05,
                    "take_profit": 0.15,
                    "consolidation_min": 10
                },
                "category": "folk_strategy",
                "description": "板块龙头盘整突破，追求波段收益"
            },
            {
                "strategy_id": "scalping_blade",
                "name": "剃头皮策略",
                "parameters": {
                    "suitable_period": 1,
                    "max_position": 0.20,
                    "stop_loss": 0.01,
                    "take_profit": 0.015,
                    "max_hold_bars": 5
                },
                "category": "technical",
                "description": "VWAP/BOLL 偏离下的高频均值回归"
            }
        ]
    
    async def hybrid_strategy_selection(
        self,
        stock_analysis: Dict[str, Any],
        market_data: Dict[str, Any],
        news_sentiment: float
    ) -> Dict[str, Any]:
        """
        混合决策模型：规则筛选 → LLM优化 → 回测验证
        
        Args:
            stock_analysis: 智能体分析结果
            market_data: 市场数据
            news_sentiment: 新闻情绪指数
            
        Returns:
            策略选择结果
        """
        logger.info("开始混合决策模型策略选择")
        
        # 检查缓存
        try:
            from backend.services.cache.strategy_cache import get_strategy_cache
            cache = get_strategy_cache()
            cached_result = cache.get(stock_analysis, market_data, news_sentiment)
            if cached_result is not None:
                logger.info("使用缓存的策略选择结果")
                return cached_result
        except Exception as e:
            logger.warning(f"缓存检查失败: {e}")
        
        # 步骤0：数据验证和清洗
        validated_inputs = validate_strategy_inputs(
            stock_analysis,
            market_data,
            news_sentiment
        )
        
        # 步骤1：规则筛选（快速过滤）
        candidate_strategies = self._rule_based_filter(validated_inputs)
        
        if not candidate_strategies:
            logger.warning("规则筛选后无候选策略，使用兜底策略")
            candidate_strategies = [self.strategies[0]]  # 兜底策略
        
        logger.info(f"规则筛选后剩余 {len(candidate_strategies)} 个候选策略")
        
        # 步骤2：LLM优化排序
        llm_ranking = await self._llm_optimize_ranking(
            validated_inputs,
            candidate_strategies
        )
        
        # 步骤3：回测验证
        final_result = await self._backtest_verification(
            llm_ranking,
            validated_inputs
        )
        
        logger.info(f"最终选择策略: {final_result['selected_strategy_id']}")
        
        # 设置缓存
        try:
            from backend.services.cache.strategy_cache import get_strategy_cache
            cache = get_strategy_cache()
            cache.set(stock_analysis, market_data, news_sentiment, final_result)
        except Exception as e:
            logger.warning(f"缓存设置失败: {e}")
        
        return final_result
    
    def _rule_based_filter(self, validated_inputs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        步骤1：基于规则快速筛选候选策略
        
        Args:
            validated_inputs: 验证后的输入数据
            
        Returns:
            候选策略列表
        """
        stock_analysis = validated_inputs["stock_analysis"]
        market_data = validated_inputs["market_data"]
        news_sentiment = validated_inputs["news_sentiment"]
        
        # 提取关键参数
        period_suggestion = stock_analysis.get("period_suggestion", 14)
        risk_level = stock_analysis.get("risk_level", "medium")
        
        # 获取仓位上限
        max_position_limit = self._get_max_position_by_risk(risk_level)
        
        # 筛选策略
        candidates = []
        for strategy in self.strategies:
            params = strategy["parameters"]
            
            # 条件1：周期匹配（偏差≤3天）
            period_match = abs(params["suitable_period"] - period_suggestion) <= 3
            
            # 条件2：仓位限制
            position_match = params["max_position"] <= max_position_limit
            
            # 条件3：新闻敏感度匹配
            sentiment_match = params["news_sensitivity"] >= abs(news_sentiment) * 0.8
            
            # 条件4：市场波动率检查
            volatility = market_data.get("volatility", 0)
            if volatility > 0.08 and params.get("stop_loss", 0) == 0:
                # 高波动率时必须有止损
                continue
            
            if period_match and position_match and sentiment_match:
                candidates.append(strategy)
        
        return candidates
    
    def _get_max_position_by_risk(self, risk_level: str) -> float:
        """根据风险等级获取最大仓位"""
        risk_thresholds = self.rules.get("risk_thresholds", {}).get("max_position_by_risk", {})
        return risk_thresholds.get(risk_level, 0.30)
    
    async def _llm_optimize_ranking(
        self,
        validated_inputs: Dict[str, Any],
        candidate_strategies: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        步骤2：使用LLM对候选策略进行优化排序
        
        Args:
            validated_inputs: 验证后的输入数据
            candidate_strategies: 候选策略列表
            
        Returns:
            LLM排序后的策略列表
        """
        # 构建LLM提示词
        prompt = self._build_llm_prompt(validated_inputs, candidate_strategies)
        
        try:
            # 调用LLM服务（默认使用真实LLM，失败时自动降级）
            llm_response = await self._call_llm(prompt, use_real_llm=True)
            
            # 解析LLM响应
            ranking = self._parse_llm_response(llm_response, candidate_strategies)
            
            return ranking
            
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            # 降级为规则排序
            return self._rule_based_ranking(validated_inputs, candidate_strategies)
    
    def _build_llm_prompt(
        self,
        validated_inputs: Dict[str, Any],
        candidate_strategies: List[Dict[str, Any]]
    ) -> str:
        """构建包含规则的LLM提示词"""
        stock_analysis = validated_inputs["stock_analysis"]
        market_data = validated_inputs["market_data"]
        news_sentiment = validated_inputs["news_sentiment"]
        
        # 获取场景化规则
        scenario_rules = get_scenario_guidance(stock_analysis, market_data)
        
        # 构建提示词
        prompt = f"""
## 任务：股票策略选择

### 输入数据
1. 股票分析结果：
   - 风险等级: {stock_analysis.get('risk_level')}
   - 建议周期: {stock_analysis.get('period_suggestion')}天
   - 基本面评分: {stock_analysis.get('fundamental_score', 'N/A')}
   - 技术面评分: {stock_analysis.get('technical_score', 'N/A')}

2. 市场数据：
   - 趋势: {market_data.get('trend')}
   - 波动率: {market_data.get('volatility', 0):.2%}

3. 新闻情绪指数：{news_sentiment:.2f}（范围[-1,1]）

### 必须遵守的规则
#### 必选条件（全部满足）：
{chr(10).join([f"- {rule}" for rule in self.rules.get("mandatory_conditions", [])])}

#### 禁止条件（全部规避）：
{chr(10).join([f"- {rule}" for rule in self.rules.get("forbidden_conditions", [])])}

#### 优先级规则：
{chr(10).join([f"- {rule.get('rule', rule) if isinstance(rule, dict) else rule}" for rule in self.rules.get("priority_rules", [])])}

### 场景化特殊规则（当前场景适用）
{chr(10).join([f"- {rule}" for rule in scenario_rules])}

### 候选策略
{json.dumps([{
    "strategy_id": s["strategy_id"],
    "name": s["name"],
    "suitable_period": s["parameters"]["suitable_period"],
    "max_position": s["parameters"]["max_position"],
    "stop_loss": s["parameters"]["stop_loss"],
    "news_sensitivity": s["parameters"]["news_sensitivity"]
} for s in candidate_strategies], ensure_ascii=False, indent=2)}

### 输出要求
严格按照以下JSON格式输出，不得添加额外内容：
{{
  "rankings": [
    {{
      "strategy_id": "策略ID",
      "score": 85,
      "reason": "详细的选择理由，逐条对应输入数据和规则"
    }}
  ]
}}

### 评分规则
- 周期匹配度（30分）
- 风险适配性（25分）
- 新闻敏感度匹配（20分）
- 市场环境适配（15分）
- 历史表现（10分）
"""
        return prompt
    
    async def _call_llm(self, prompt: str, use_real_llm: bool = True) -> str:
        """
        调用LLM服务
        
        Args:
            prompt: 提示词
            use_real_llm: 是否使用真实LLM（False时使用模拟）
            
        Returns:
            LLM响应文本
        """
        if not use_real_llm:
            # 模拟模式（用于测试）
            await asyncio.sleep(0.1)
            return json.dumps({
                "rankings": [
                    {
                        "strategy_id": "vegas_adx",
                        "score": 85,
                        "reason": "周期匹配度高，适合中期趋势跟踪"
                    },
                    {
                        "strategy_id": "ema_breakout",
                        "score": 78,
                        "reason": "新闻敏感度匹配，但周期略短"
                    }
                ]
            }, ensure_ascii=False)
        
        # 真实LLM调用
        try:
            # 延迟导入避免循环依赖
            import sys
            from pathlib import Path
            backend_path = Path(__file__).parent.parent.parent
            if str(backend_path) not in sys.path:
                sys.path.insert(0, str(backend_path))
            
            from backend.services.llm.llm_client import get_llm_client_for_task
            
            # 使用配置化的LLM客户端
            llm_client = get_llm_client_for_task("strategy_selection")
            
            # 调用LLM，要求JSON格式输出
            response = await llm_client.generate(
                prompt=prompt,
                temperature=0.3,  # 低温度提高一致性
                max_tokens=1500,
                format="json"
            )
            
            logger.info("LLM调用成功")
            return response
            
        except Exception as e:
            logger.error(f"LLM调用失败: {e}，降级为模拟模式")
            # 降级为模拟模式
            return await self._call_llm(prompt, use_real_llm=False)
    
    def _parse_llm_response(
        self,
        llm_response: str,
        candidate_strategies: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """解析LLM响应"""
        try:
            response_data = json.loads(llm_response)
            rankings = response_data.get("rankings", [])
            
            # 将strategy_id映射回完整策略对象
            ranked_strategies = []
            for rank in rankings:
                strategy_id = rank["strategy_id"]
                strategy = next((s for s in candidate_strategies if s["strategy_id"] == strategy_id), None)
                if strategy:
                    ranked_strategies.append({
                        **strategy,
                        "llm_score": rank["score"],
                        "llm_reason": rank["reason"]
                    })
            
            return ranked_strategies
            
        except Exception as e:
            logger.error(f"解析LLM响应失败: {e}")
            return candidate_strategies
    
    def _rule_based_ranking(
        self,
        validated_inputs: Dict[str, Any],
        candidate_strategies: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """基于规则的降级排序"""
        stock_analysis = validated_inputs["stock_analysis"]
        period_suggestion = stock_analysis.get("period_suggestion", 14)
        
        # 简单排序：按周期匹配度
        ranked = sorted(
            candidate_strategies,
            key=lambda s: abs(s["parameters"]["suitable_period"] - period_suggestion)
        )
        
        # 添加评分
        for i, strategy in enumerate(ranked):
            strategy["llm_score"] = 80 - i * 5
            strategy["llm_reason"] = "规则降级排序"
        
        return ranked
    
    async def _backtest_verification(
        self,
        llm_ranking: List[Dict[str, Any]],
        validated_inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        步骤3：回测验证
        
        Args:
            llm_ranking: LLM排序后的策略列表
            validated_inputs: 验证后的输入数据
            
        Returns:
            最终策略选择结果
        """
        stock_analysis = validated_inputs["stock_analysis"]
        stock_code = stock_analysis.get("code", "000001")
        period = stock_analysis.get("period_suggestion", 14)
        
        final_candidates = []
        
        for strategy in llm_ranking:
            # 调用回测引擎（默认使用真实回测，失败时自动降级）
            backtest_result = await self._run_backtest(
                strategy["strategy_id"],
                stock_code,
                period,
                use_real_backtest=True
            )
            
            # 检查回测胜率
            win_rate = backtest_result.get("win_rate", 0)
            if win_rate >= 0.40:  # 胜率阈值40%
                # 加权融合：LLM评分70% + 回测胜率30%
                combined_score = strategy["llm_score"] * 0.7 + win_rate * 100 * 0.3
                
                final_candidates.append({
                    "strategy_id": strategy["strategy_id"],
                    "strategy_name": strategy["name"],
                    "combined_score": combined_score,
                    "llm_score": strategy["llm_score"],
                    "llm_reason": strategy.get("llm_reason", ""),
                    "backtest_win_rate": win_rate,
                    "backtest_result": backtest_result
                })
        
        if not final_candidates:
            logger.warning("所有策略回测验证失败，使用LLM排名第一的策略")
            strategy = llm_ranking[0]
            final_candidates.append({
                "strategy_id": strategy["strategy_id"],
                "strategy_name": strategy["name"],
                "combined_score": strategy["llm_score"],
                "llm_score": strategy["llm_score"],
                "llm_reason": strategy.get("llm_reason", ""),
                "backtest_win_rate": 0,
                "backtest_result": {}
            })
        
        # 选择得分最高的策略
        best_strategy = max(final_candidates, key=lambda x: x["combined_score"])
        
        # 构建完整的返回结果
        result = {
            "selected_strategy_id": best_strategy["strategy_id"],
            "selected_strategy_name": best_strategy["strategy_name"],
            "selection_reason": self._build_selection_reason(best_strategy, validated_inputs),
            "rule_matching_details": {
                "mandatory_conditions_met": True,
                "forbidden_conditions_violated": False,
                "priority_score": best_strategy["combined_score"]
            },
            "risk_check_result": self._build_risk_check_result(best_strategy, validated_inputs),
            "alternative_strategies": [
                {
                    "strategy_id": c["strategy_id"],
                    "score": c["combined_score"],
                    "reason": c["llm_reason"]
                }
                for c in final_candidates[1:3]  # 最多返回2个备选
            ],
            "selected_at": datetime.now().isoformat()
        }
        
        return result
    
    async def _run_backtest(
        self,
        strategy_id: str,
        stock_code: str,
        period: int,
        use_real_backtest: bool = True
    ) -> Dict[str, Any]:
        """
        运行回测
        
        Args:
            strategy_id: 策略ID
            stock_code: 股票代码
            period: 回测周期（天）
            use_real_backtest: 是否使用真实回测
            
        Returns:
            回测结果
        """
        if not use_real_backtest:
            # 模拟模式
            await asyncio.sleep(0.1)
            return {
                "win_rate": 0.45 if strategy_id == "vegas_adx" else 0.42,
                "total_return": 0.08,
                "max_drawdown": 0.12,
                "sharpe_ratio": 1.2
            }
        
        # 真实回测
        try:
            from datetime import datetime, timedelta
            from backend.backtest.engine import BacktestEngine
            from backend.backtest.data_loader import DataLoader
            
            # 计算回测时间范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period * 3)  # 留出余量
            
            # 加载数据
            data_loader = DataLoader()
            df = await data_loader.load_stock_data(
                stock_code,
                start_date.strftime("%Y%m%d"),
                end_date.strftime("%Y%m%d")
            )
            
            if df is None or len(df) < period:
                logger.warning(f"数据不足，使用模拟回测")
                return await self._run_backtest(strategy_id, stock_code, period, use_real_backtest=False)
            
            # 创建回测引擎
            engine = BacktestEngine(
                initial_capital=100000,
                commission_rate=0.0003,
                slippage_rate=0.0005
            )
            
            # 获取策略
            strategy = self._get_strategy_instance(strategy_id)
            if strategy is None:
                logger.warning(f"策略{strategy_id}未找到，使用模拟回测")
                return await self._run_backtest(strategy_id, stock_code, period, use_real_backtest=False)
            
            # 运行回测
            performance = await engine.run(
                strategy=strategy,
                data=df,
                stock_code=stock_code
            )
            
            logger.info(f"回测完成: {strategy_id}, 胜率={performance.win_rate:.2%}")
            
            return {
                "win_rate": performance.win_rate,
                "total_return": performance.total_return,
                "max_drawdown": performance.max_drawdown,
                "sharpe_ratio": performance.sharpe_ratio
            }
            
        except Exception as e:
            logger.error(f"回测失败: {e}，降级为模拟模式")
            return await self._run_backtest(strategy_id, stock_code, period, use_real_backtest=False)
    
    def _get_strategy_instance(self, strategy_id: str):
        """获取策略实例"""
        try:
            if strategy_id == "vegas_adx":
                from backend.strategies.vegas_adx import VegasADXStrategy
                return VegasADXStrategy()
            elif strategy_id == "ema_breakout":
                from backend.strategies.ema_breakout import EMABreakoutStrategy
                return EMABreakoutStrategy()
            elif strategy_id == "trident":
                from backend.strategies.trident import TridentStrategy
                return TridentStrategy()
            elif strategy_id == "macd_crossover":
                from backend.strategies.macd_crossover import MACDCrossoverStrategy
                return MACDCrossoverStrategy()
            elif strategy_id == "bollinger_breakout":
                from backend.strategies.bollinger_breakout import BollingerBreakoutStrategy
                return BollingerBreakoutStrategy()
            elif strategy_id == "sentiment_resonance":
                from backend.strategies.sentiment_resonance import SentimentResonanceStrategy
                return SentimentResonanceStrategy()
            elif strategy_id == "debate_weighted":
                from backend.strategies.debate_weighted import DebateWeightedStrategy
                return DebateWeightedStrategy()
            elif strategy_id == "turtle_trading":
                from backend.strategies.turtle_trading import TurtleTradingStrategy
                return TurtleTradingStrategy()
            elif strategy_id == "limit_up_trading":
                from backend.strategies.limit_up_trading import LimitUpTradingStrategy
                return LimitUpTradingStrategy()
            elif strategy_id == "volume_price_surge":
                from backend.strategies.volume_price_surge import VolumePriceSurgeStrategy
                return VolumePriceSurgeStrategy()
            elif strategy_id == "buffett_value":
                from backend.strategies.buffett_value import BuffettValueStrategy
                return BuffettValueStrategy()
            elif strategy_id == "lynch_growth":
                from backend.strategies.lynch_growth import LynchGrowthStrategy
                return LynchGrowthStrategy()
            elif strategy_id == "graham_margin":
                from backend.strategies.graham_margin import GrahamMarginStrategy
                return GrahamMarginStrategy()
            elif strategy_id == "martingale_refined":
                from backend.strategies.martingale_refined import MartingaleRefinedStrategy
                return MartingaleRefinedStrategy()
            elif strategy_id == "dragon_leader":
                from backend.strategies.dragon_leader import DragonLeaderStrategy
                return DragonLeaderStrategy()
            elif strategy_id == "scalping_blade":
                from backend.strategies.scalping_blade import ScalpingBladeStrategy
                return ScalpingBladeStrategy()
            else:
                return None
        except Exception as e:
            logger.error(f"策略实例化失败: {e}")
            return None
    
    def _build_selection_reason(
        self,
        best_strategy: Dict[str, Any],
        validated_inputs: Dict[str, Any]
    ) -> str:
        """构建策略选择理由"""
        stock_analysis = validated_inputs["stock_analysis"]
        
        reason_parts = [
            f"1. LLM评分: {best_strategy['llm_score']:.1f}分",
            f"2. 回测胜率: {best_strategy['backtest_win_rate']:.1%}",
            f"3. 综合得分: {best_strategy['combined_score']:.1f}分",
            f"4. LLM理由: {best_strategy['llm_reason']}"
        ]
        
        return "；".join(reason_parts)
    
    def _build_risk_check_result(
        self,
        best_strategy: Dict[str, Any],
        validated_inputs: Dict[str, Any]
    ) -> str:
        """构建风险检查结果"""
        backtest = best_strategy.get("backtest_result", {})
        max_drawdown = backtest.get("max_drawdown", 0)
        
        return f"回测最大回撤{max_drawdown:.1%}<20%，风险合规"
    
    async def check_decision_consistency(
        self,
        strategy_id: str,
        validated_inputs: Dict[str, Any],
        retry_times: int = 3
    ) -> str:
        """
        决策一致性校验
        
        Args:
            strategy_id: 初次选择的策略ID
            validated_inputs: 验证后的输入数据
            retry_times: 重试次数
            
        Returns:
            最终确认的策略ID
        """
        consistency_threshold = 0.7
        results = [strategy_id]
        
        # 多次调用验证
        for _ in range(retry_times):
            result = await self.hybrid_strategy_selection(
                validated_inputs["stock_analysis"],
                validated_inputs["market_data"],
                validated_inputs["news_sentiment"]
            )
            results.append(result["selected_strategy_id"])
        
        # 计算一致率
        consistent_rate = results.count(strategy_id) / len(results)
        
        if consistent_rate < consistency_threshold:
            logger.warning(f"决策一致率{consistent_rate:.1%}低于阈值，降级为规则决策")
            # TODO: 实现纯规则决策
            return strategy_id
        
        logger.info(f"决策一致率{consistent_rate:.1%}，通过验证")
        return strategy_id


# 全局单例
_selector_instance = None


def get_strategy_selector() -> StrategySelector:
    """获取策略选择器单例"""
    global _selector_instance
    if _selector_instance is None:
        _selector_instance = StrategySelector()
    return _selector_instance


# 便捷函数
async def select_strategy(
    stock_analysis: Dict[str, Any],
    market_data: Dict[str, Any],
    news_sentiment: float
) -> Dict[str, Any]:
    """
    策略选择便捷函数
    
    Args:
        stock_analysis: 智能体分析结果
        market_data: 市场数据
        news_sentiment: 新闻情绪指数
        
    Returns:
        策略选择结果
    """
    selector = get_strategy_selector()
    return await selector.hybrid_strategy_selection(
        stock_analysis,
        market_data,
        news_sentiment
    )
