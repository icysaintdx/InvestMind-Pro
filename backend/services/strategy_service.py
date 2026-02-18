"""
策略服务层
提供策略的CRUD操作、执行引擎、信号生成等功能
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import uuid
import json

from backend.database.strategy_models import (
    Strategy, StrategyIndicator, StrategyRule, 
    StrategyRiskParams, StrategyPrompt, TradeSignal
)
from backend.utils.logging_config import get_logger

logger = get_logger("services.strategy")


class StrategyService:
    """策略服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== CRUD 操作 ====================
    
    def create_strategy(self, data: Dict[str, Any], created_by: str = None) -> Strategy:
        """创建策略"""
        strategy = Strategy(
            id=str(uuid.uuid4()),
            name=data.get("name"),
            description=data.get("description", ""),
            category=data.get("category", "custom"),
            source=data.get("source", "user"),
            icon=data.get("icon", "📊"),
            is_active=data.get("is_active", True),
            version=data.get("version", "1.0"),
            created_by=created_by
        )
        
        self.db.add(strategy)
        
        # 添加指标
        for idx, ind_data in enumerate(data.get("indicators", [])):
            indicator = StrategyIndicator(
                strategy_id=strategy.id,
                name=ind_data.get("name"),
                type=ind_data.get("type"),
                params=ind_data.get("params", {}),
                weight=ind_data.get("weight", 1.0),
                description=ind_data.get("description", ""),
                sort_order=idx
            )
            self.db.add(indicator)
        
        # 添加入场规则
        for idx, rule_data in enumerate(data.get("entry_conditions", [])):
            rule = StrategyRule(
                strategy_id=strategy.id,
                rule_type="entry",
                name=rule_data.get("name", f"入场规则{idx+1}"),
                logic=rule_data.get("logic", "AND"),
                conditions=self._normalize_conditions(rule_data),
                weight=rule_data.get("weight", 1.0),
                priority=idx,
                description=rule_data.get("description", "")
            )
            self.db.add(rule)
        
        # 添加出场规则
        for idx, rule_data in enumerate(data.get("exit_conditions", [])):
            rule = StrategyRule(
                strategy_id=strategy.id,
                rule_type="exit",
                name=rule_data.get("name", f"出场规则{idx+1}"),
                logic=rule_data.get("logic", "AND"),
                conditions=self._normalize_conditions(rule_data),
                weight=rule_data.get("weight", 1.0),
                priority=idx,
                description=rule_data.get("description", "")
            )
            self.db.add(rule)
        
        # 添加风险参数
        risk_data = data.get("risk_params", {})
        if risk_data:
            risk_params = StrategyRiskParams(
                strategy_id=strategy.id,
                stop_loss_type=risk_data.get("stop_loss_type", "percentage"),
                stop_loss_value=risk_data.get("stop_loss", 0.05),
                trailing_stop=risk_data.get("trailing_stop", False),
                trailing_step=risk_data.get("trailing_step", 0.01),
                take_profit_type=risk_data.get("take_profit_type", "percentage"),
                take_profit_value=risk_data.get("take_profit", 0.15),
                partial_exits=risk_data.get("partial_exits", []),
                position_type=risk_data.get("position_type", "fixed"),
                max_position=risk_data.get("max_position", 0.3),
                risk_per_trade=risk_data.get("risk_per_trade", 0.02)
            )
            self.db.add(risk_params)
        
        self.db.commit()
        self.db.refresh(strategy)
        
        logger.info(f"创建策略成功: {strategy.id} - {strategy.name}")
        return strategy
    
    def _normalize_conditions(self, rule_data: Dict) -> List[Dict]:
        """标准化条件格式"""
        # 如果已经是conditions列表格式
        if "conditions" in rule_data:
            return rule_data["conditions"]
        
        # 如果是旧格式（单个条件）
        if "indicator" in rule_data:
            return [{
                "indicator": rule_data.get("indicator"),
                "operator": rule_data.get("operator"),
                "value": rule_data.get("value"),
                "compare_to": rule_data.get("compare_to")
            }]
        
        return []
    
    def get_strategy(self, strategy_id: str) -> Optional[Strategy]:
        """获取策略详情"""
        return self.db.query(Strategy).filter(Strategy.id == strategy_id).first()
    
    def get_strategies(
        self, 
        category: str = None, 
        source: str = None,
        is_active: bool = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Strategy]:
        """获取策略列表"""
        query = self.db.query(Strategy)
        
        if category:
            query = query.filter(Strategy.category == category)
        if source:
            query = query.filter(Strategy.source == source)
        if is_active is not None:
            query = query.filter(Strategy.is_active == is_active)
        
        return query.order_by(Strategy.created_at.desc()).offset(offset).limit(limit).all()
    
    def update_strategy(self, strategy_id: str, data: Dict[str, Any]) -> Optional[Strategy]:
        """更新策略"""
        strategy = self.get_strategy(strategy_id)
        if not strategy:
            return None
        
        # 更新基本信息
        for field in ["name", "description", "category", "icon", "is_active", "version"]:
            if field in data:
                setattr(strategy, field, data[field])
        
        strategy.updated_at = datetime.utcnow()
        
        # 更新指标（先删除再添加）
        if "indicators" in data:
            self.db.query(StrategyIndicator).filter(
                StrategyIndicator.strategy_id == strategy_id
            ).delete()
            
            for idx, ind_data in enumerate(data["indicators"]):
                indicator = StrategyIndicator(
                    strategy_id=strategy_id,
                    name=ind_data.get("name"),
                    type=ind_data.get("type"),
                    params=ind_data.get("params", {}),
                    weight=ind_data.get("weight", 1.0),
                    description=ind_data.get("description", ""),
                    sort_order=idx
                )
                self.db.add(indicator)
        
        # 更新规则
        if "entry_conditions" in data:
            self.db.query(StrategyRule).filter(
                and_(StrategyRule.strategy_id == strategy_id, StrategyRule.rule_type == "entry")
            ).delete()
            
            for idx, rule_data in enumerate(data["entry_conditions"]):
                rule = StrategyRule(
                    strategy_id=strategy_id,
                    rule_type="entry",
                    name=rule_data.get("name", f"入场规则{idx+1}"),
                    logic=rule_data.get("logic", "AND"),
                    conditions=self._normalize_conditions(rule_data),
                    weight=rule_data.get("weight", 1.0),
                    priority=idx,
                    description=rule_data.get("description", "")
                )
                self.db.add(rule)
        
        if "exit_conditions" in data:
            self.db.query(StrategyRule).filter(
                and_(StrategyRule.strategy_id == strategy_id, StrategyRule.rule_type == "exit")
            ).delete()
            
            for idx, rule_data in enumerate(data["exit_conditions"]):
                rule = StrategyRule(
                    strategy_id=strategy_id,
                    rule_type="exit",
                    name=rule_data.get("name", f"出场规则{idx+1}"),
                    logic=rule_data.get("logic", "AND"),
                    conditions=self._normalize_conditions(rule_data),
                    weight=rule_data.get("weight", 1.0),
                    priority=idx,
                    description=rule_data.get("description", "")
                )
                self.db.add(rule)
        
        # 更新风险参数
        if "risk_params" in data:
            risk_data = data["risk_params"]
            risk_params = self.db.query(StrategyRiskParams).filter(
                StrategyRiskParams.strategy_id == strategy_id
            ).first()
            
            if risk_params:
                risk_params.stop_loss_type = risk_data.get("stop_loss_type", risk_params.stop_loss_type)
                risk_params.stop_loss_value = risk_data.get("stop_loss", risk_params.stop_loss_value)
                risk_params.trailing_stop = risk_data.get("trailing_stop", risk_params.trailing_stop)
                risk_params.take_profit_value = risk_data.get("take_profit", risk_params.take_profit_value)
                risk_params.max_position = risk_data.get("max_position", risk_params.max_position)
            else:
                risk_params = StrategyRiskParams(
                    strategy_id=strategy_id,
                    stop_loss_value=risk_data.get("stop_loss", 0.05),
                    take_profit_value=risk_data.get("take_profit", 0.15),
                    max_position=risk_data.get("max_position", 0.3)
                )
                self.db.add(risk_params)
        
        self.db.commit()
        self.db.refresh(strategy)
        
        logger.info(f"更新策略成功: {strategy_id}")
        return strategy
    
    def delete_strategy(self, strategy_id: str) -> bool:
        """删除策略"""
        strategy = self.get_strategy(strategy_id)
        if not strategy:
            return False
        
        # 预设策略不能删除
        if strategy.source == "preset":
            logger.warning(f"尝试删除预设策略: {strategy_id}")
            return False
        
        self.db.delete(strategy)
        self.db.commit()
        
        logger.info(f"删除策略成功: {strategy_id}")
        return True
    
    def clone_strategy(self, strategy_id: str, new_name: str = None) -> Optional[Strategy]:
        """克隆策略"""
        original = self.get_strategy(strategy_id)
        if not original:
            return None
        
        data = original.to_dict()
        data["name"] = new_name or f"{original.name} (副本)"
        data["source"] = "user"
        del data["id"]
        del data["created_at"]
        del data["updated_at"]
        
        return self.create_strategy(data)
    
    # ==================== 策略分类统计 ====================
    
    def get_category_stats(self) -> Dict[str, Any]:
        """获取策略分类统计"""
        from sqlalchemy import func
        
        stats = self.db.query(
            Strategy.category,
            func.count(Strategy.id).label("count")
        ).filter(Strategy.is_active == True).group_by(Strategy.category).all()
        
        category_info = {
            "technical": {"name": "技术分析", "icon": "📊"},
            "fundamental": {"name": "基本面", "icon": "💎"},
            "institutional": {"name": "机构持仓", "icon": "🏛️"},
            "folk": {"name": "民间策略", "icon": "🚀"},
            "ai": {"name": "AI策略", "icon": "🤖"},
            "custom": {"name": "自定义", "icon": "📝"}
        }
        
        result = {}
        for cat, count in stats:
            if cat in category_info:
                result[cat] = {
                    **category_info[cat],
                    "count": count
                }
        
        return result
    
    # ==================== 预设策略初始化 ====================
    
    def init_preset_strategies(self):
        """初始化预设策略到数据库"""
        from backend.services.preset_strategies import PRESET_STRATEGIES
        
        for preset in PRESET_STRATEGIES:
            # 检查是否已存在
            existing = self.db.query(Strategy).filter(
                and_(Strategy.name == preset["name"], Strategy.source == "preset")
            ).first()
            
            if not existing:
                preset["source"] = "preset"
                self.create_strategy(preset)
                logger.info(f"初始化预设策略: {preset['name']}")


class IndicatorEngine:
    """指标计算引擎"""
    
    @staticmethod
    def calculate_all(kline_data: List[Dict], indicator_configs: List[Dict]) -> Dict[str, Any]:
        """根据配置计算所有指标"""
        result = {}
        
        for config in indicator_configs:
            name = config.get("name")
            params = config.get("params", {})
            
            if name == "MA":
                periods = params.get("periods", [5, 10, 20, 60])
                for period in periods:
                    result[f"MA{period}"] = IndicatorEngine.calculate_ma(kline_data, period)
            
            elif name == "EMA":
                periods = params.get("periods", [12, 26])
                for period in periods:
                    result[f"EMA{period}"] = IndicatorEngine.calculate_ema(kline_data, period)
            
            elif name == "MACD":
                fast = params.get("fast_period", 12)
                slow = params.get("slow_period", 26)
                signal = params.get("signal_period", 9)
                macd_result = IndicatorEngine.calculate_macd(kline_data, fast, slow, signal)
                result["MACD_DIF"] = macd_result["dif"]
                result["MACD_DEA"] = macd_result["dea"]
                result["MACD_HIST"] = macd_result["hist"]
            
            elif name == "RSI":
                period = params.get("period", 14)
                result["RSI"] = IndicatorEngine.calculate_rsi(kline_data, period)
            
            elif name == "BOLL":
                period = params.get("period", 20)
                std_dev = params.get("std_dev", 2)
                boll_result = IndicatorEngine.calculate_boll(kline_data, period, std_dev)
                result["BOLL_UPPER"] = boll_result["upper"]
                result["BOLL_MIDDLE"] = boll_result["middle"]
                result["BOLL_LOWER"] = boll_result["lower"]
            
            elif name == "KDJ":
                n = params.get("n", 9)
                kdj_result = IndicatorEngine.calculate_kdj(kline_data, n)
                result["KDJ_K"] = kdj_result["k"]
                result["KDJ_D"] = kdj_result["d"]
                result["KDJ_J"] = kdj_result["j"]
            
            elif name == "Volume":
                ma_periods = params.get("ma_periods", [5, 10])
                for period in ma_periods:
                    result[f"VOL_MA{period}"] = IndicatorEngine.calculate_volume_ma(kline_data, period)
        
        return result
    
    @staticmethod
    def calculate_ma(data: List[Dict], period: int) -> List[float]:
        """计算移动平均线"""
        closes = [d["close"] for d in data]
        result = []
        for i in range(len(closes)):
            if i < period - 1:
                result.append(None)
            else:
                result.append(sum(closes[i-period+1:i+1]) / period)
        return result
    
    @staticmethod
    def calculate_ema(data: List[Dict], period: int) -> List[float]:
        """计算指数移动平均"""
        closes = [d["close"] for d in data]
        result = []
        multiplier = 2 / (period + 1)
        
        for i, close in enumerate(closes):
            if i == 0:
                result.append(close)
            else:
                result.append((close - result[-1]) * multiplier + result[-1])
        
        return result
    
    @staticmethod
    def calculate_macd(data: List[Dict], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        """计算MACD"""
        ema_fast = IndicatorEngine.calculate_ema(data, fast)
        ema_slow = IndicatorEngine.calculate_ema(data, slow)
        
        dif = [f - s if f and s else None for f, s in zip(ema_fast, ema_slow)]
        
        # 计算DEA (DIF的EMA)
        dea = []
        multiplier = 2 / (signal + 1)
        for i, d in enumerate(dif):
            if d is None:
                dea.append(None)
            elif i == 0 or dea[-1] is None:
                dea.append(d)
            else:
                dea.append((d - dea[-1]) * multiplier + dea[-1])
        
        # 计算柱状图
        hist = [(d - e) * 2 if d and e else None for d, e in zip(dif, dea)]
        
        return {"dif": dif, "dea": dea, "hist": hist}
    
    @staticmethod
    def calculate_rsi(data: List[Dict], period: int = 14) -> List[float]:
        """计算RSI"""
        closes = [d["close"] for d in data]
        result = []
        gains = []
        losses = []
        
        for i in range(len(closes)):
            if i == 0:
                gains.append(0)
                losses.append(0)
                result.append(None)
                continue
            
            change = closes[i] - closes[i-1]
            gains.append(max(change, 0))
            losses.append(max(-change, 0))
            
            if i < period:
                result.append(None)
            else:
                avg_gain = sum(gains[i-period+1:i+1]) / period
                avg_loss = sum(losses[i-period+1:i+1]) / period
                
                if avg_loss == 0:
                    result.append(100)
                else:
                    rs = avg_gain / avg_loss
                    result.append(100 - (100 / (1 + rs)))
        
        return result
    
    @staticmethod
    def calculate_boll(data: List[Dict], period: int = 20, std_dev: float = 2) -> Dict:
        """计算布林带"""
        import math
        
        closes = [d["close"] for d in data]
        middle = IndicatorEngine.calculate_ma(data, period)
        upper = []
        lower = []
        
        for i in range(len(closes)):
            if i < period - 1:
                upper.append(None)
                lower.append(None)
            else:
                window = closes[i-period+1:i+1]
                mean = middle[i]
                variance = sum((x - mean) ** 2 for x in window) / period
                std = math.sqrt(variance)
                upper.append(mean + std_dev * std)
                lower.append(mean - std_dev * std)
        
        return {"upper": upper, "middle": middle, "lower": lower}
    
    @staticmethod
    def calculate_kdj(data: List[Dict], n: int = 9) -> Dict:
        """计算KDJ"""
        k_values = []
        d_values = []
        j_values = []
        
        for i in range(len(data)):
            if i < n - 1:
                k_values.append(50)
                d_values.append(50)
                j_values.append(50)
                continue
            
            window = data[i-n+1:i+1]
            high = max(d["high"] for d in window)
            low = min(d["low"] for d in window)
            close = data[i]["close"]
            
            if high == low:
                rsv = 50
            else:
                rsv = (close - low) / (high - low) * 100
            
            prev_k = k_values[-1] if k_values else 50
            prev_d = d_values[-1] if d_values else 50
            
            k = 2/3 * prev_k + 1/3 * rsv
            d = 2/3 * prev_d + 1/3 * k
            j = 3 * k - 2 * d
            
            k_values.append(k)
            d_values.append(d)
            j_values.append(j)
        
        return {"k": k_values, "d": d_values, "j": j_values}
    
    @staticmethod
    def calculate_volume_ma(data: List[Dict], period: int) -> List[float]:
        """计算成交量均线"""
        volumes = [d["volume"] for d in data]
        result = []
        for i in range(len(volumes)):
            if i < period - 1:
                result.append(None)
            else:
                result.append(sum(volumes[i-period+1:i+1]) / period)
        return result


class RuleEngine:
    """规则评估引擎"""
    
    @staticmethod
    def evaluate_rules(rules: List[Dict], indicators: Dict, current_price: float) -> Dict[str, Any]:
        """评估规则列表"""
        matched_rules = []
        total_weight = 0
        matched_weight = 0
        
        for rule in rules:
            conditions = rule.get("conditions", [])
            logic = rule.get("logic", "AND")
            weight = rule.get("weight", 1.0)
            
            total_weight += weight
            
            if RuleEngine._evaluate_conditions(conditions, logic, indicators, current_price):
                matched_rules.append(rule)
                matched_weight += weight
        
        signal_strength = matched_weight / total_weight if total_weight > 0 else 0
        
        return {
            "matched": len(matched_rules) > 0,
            "matched_rules": matched_rules,
            "signal_strength": signal_strength,
            "total_rules": len(rules),
            "matched_count": len(matched_rules)
        }
    
    @staticmethod
    def _evaluate_conditions(conditions: List[Dict], logic: str, indicators: Dict, current_price: float) -> bool:
        """评估条件组"""
        if not conditions:
            return False
        
        results = []
        for cond in conditions:
            result = RuleEngine._evaluate_single_condition(cond, indicators, current_price)
            results.append(result)
        
        if logic == "AND":
            return all(results)
        elif logic == "OR":
            return any(results)
        
        return False
    
    @staticmethod
    def _evaluate_single_condition(condition: Dict, indicators: Dict, current_price: float) -> bool:
        """评估单个条件"""
        indicator_name = condition.get("indicator")
        operator = condition.get("operator")
        value = condition.get("value")
        compare_to = condition.get("compare_to")
        
        # 获取指标值
        if indicator_name == "price":
            indicator_value = current_price
        else:
            indicator_values = indicators.get(indicator_name, [])
            indicator_value = indicator_values[-1] if indicator_values else None
        
        if indicator_value is None:
            return False
        
        # 获取比较值
        if compare_to:
            compare_values = indicators.get(compare_to, [])
            compare_value = compare_values[-1] if compare_values else None
        else:
            compare_value = value
        
        if compare_value is None:
            return False
        
        # 执行比较
        if operator == ">":
            return indicator_value > compare_value
        elif operator == "<":
            return indicator_value < compare_value
        elif operator == ">=":
            return indicator_value >= compare_value
        elif operator == "<=":
            return indicator_value <= compare_value
        elif operator == "==":
            return indicator_value == compare_value
        elif operator == "cross_above":
            # 需要前一个值来判断交叉
            if indicator_name == "price":
                return False  # 价格交叉需要特殊处理
            prev_indicator = indicators.get(indicator_name, [])[-2] if len(indicators.get(indicator_name, [])) > 1 else None
            prev_compare = indicators.get(compare_to, [])[-2] if compare_to and len(indicators.get(compare_to, [])) > 1 else compare_value
            if prev_indicator is None or prev_compare is None:
                return False
            return prev_indicator <= prev_compare and indicator_value > compare_value
        elif operator == "cross_below":
            prev_indicator = indicators.get(indicator_name, [])[-2] if len(indicators.get(indicator_name, [])) > 1 else None
            prev_compare = indicators.get(compare_to, [])[-2] if compare_to and len(indicators.get(compare_to, [])) > 1 else compare_value
            if prev_indicator is None or prev_compare is None:
                return False
            return prev_indicator >= prev_compare and indicator_value < compare_value
        
        return False