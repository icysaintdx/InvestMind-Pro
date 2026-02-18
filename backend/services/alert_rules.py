# -*- coding: utf-8 -*-
"""
预警规则引擎
实现智能预警算法：历史异常检测、多因子综合预警、预警聚合
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import statistics
import hashlib
import json

from backend.utils.logging_config import get_logger

logger = get_logger("services.alert_rules")


class RuleType(Enum):
    """规则类型"""
    PRICE_CHANGE = "price_change"           # 价格变动
    VOLUME_CHANGE = "volume_change"         # 成交量变动
    PLEDGE_RATIO = "pledge_ratio"           # 质押比例
    RESTRICTED_RELEASE = "restricted_release"  # 限售解禁
    HOLDER_CHANGE = "holder_change"         # 股东变动
    ST_WARNING = "st_warning"               # ST风险
    SUSPEND = "suspend"                     # 停复牌
    NEWS_SENTIMENT = "news_sentiment"       # 新闻情绪
    ANOMALY_DETECTION = "anomaly_detection" # 异常检测
    MULTI_FACTOR = "multi_factor"           # 多因子综合
    CUSTOM = "custom"                       # 自定义


@dataclass
class AlertCondition:
    """预警条件"""
    field: str                    # 字段名
    operator: str                 # 操作符: >, >=, <, <=, ==, !=, contains, not_contains
    value: Any                    # 阈值
    weight: float = 1.0           # 权重（用于多因子）


@dataclass
class AlertRule:
    """预警规则"""
    id: int
    name: str
    rule_type: RuleType
    conditions: List[AlertCondition]
    alert_level: str = "medium"   # critical, high, medium, low
    apply_to_all: bool = True
    stock_codes: List[str] = field(default_factory=list)
    is_enabled: bool = True
    cooldown_minutes: int = 30    # 冷却时间（分钟）
    description: str = ""


@dataclass
class AggregatedAlert:
    """聚合后的预警"""
    alert_id: str                 # 聚合ID
    alerts: List[Dict]            # 原始预警列表
    count: int                    # 预警数量
    first_time: datetime          # 首次触发时间
    last_time: datetime           # 最后触发时间
    stock_codes: List[str]        # 涉及的股票
    alert_types: List[str]        # 涉及的预警类型
    summary: str                  # 聚合摘要


class AlertRulesEngine:
    """预警规则引擎"""

    def __init__(self):
        self._rules: Dict[int, AlertRule] = {}
        self._cooldown_cache: Dict[str, datetime] = {}  # 冷却缓存
        self._history_cache: Dict[str, List[float]] = {}  # 历史数据缓存
        self._pending_alerts: List[Dict] = []  # 待聚合的预警
        self._aggregation_config = {
            'enabled': True,
            'time_window': 5,       # 聚合时间窗口（分钟）
            'max_count': 10,        # 最大聚合数量
            'same_stock_only': True,
            'same_type_only': False,
            'cooldown': 30          # 通知冷却时间（分钟）
        }

    # ==================== 规则管理 ====================

    def add_rule(self, rule: AlertRule) -> None:
        """添加规则"""
        self._rules[rule.id] = rule
        logger.info(f"添加预警规则: {rule.name} (ID: {rule.id})")

    def remove_rule(self, rule_id: int) -> bool:
        """移除规则"""
        if rule_id in self._rules:
            del self._rules[rule_id]
            logger.info(f"移除预警规则: ID {rule_id}")
            return True
        return False

    def get_rule(self, rule_id: int) -> Optional[AlertRule]:
        """获取规则"""
        return self._rules.get(rule_id)

    def get_all_rules(self) -> List[AlertRule]:
        """获取所有规则"""
        return list(self._rules.values())

    def set_aggregation_config(self, config: Dict) -> None:
        """设置聚合配置"""
        self._aggregation_config.update(config)

    # ==================== 规则评估 ====================

    def evaluate_rules(self, stock_code: str, data: Dict) -> List[Dict]:
        """
        评估所有规则

        Args:
            stock_code: 股票代码
            data: 股票数据（包含价格、成交量、财务等）

        Returns:
            触发的预警列表
        """
        triggered_alerts = []

        for rule in self._rules.values():
            if not rule.is_enabled:
                continue

            # 检查是否适用于该股票
            if not rule.apply_to_all and stock_code not in rule.stock_codes:
                continue

            # 检查冷却时间
            cooldown_key = f"{stock_code}_{rule.id}"
            if self._is_in_cooldown(cooldown_key, rule.cooldown_minutes):
                continue

            # 评估规则
            is_triggered, details = self._evaluate_single_rule(rule, data)

            if is_triggered:
                alert = {
                    'rule_id': rule.id,
                    'rule_name': rule.name,
                    'rule_type': rule.rule_type.value,
                    'stock_code': stock_code,
                    'alert_level': rule.alert_level,
                    'trigger_time': datetime.now().isoformat(),
                    'details': details,
                    'description': rule.description
                }
                triggered_alerts.append(alert)

                # 设置冷却
                self._set_cooldown(cooldown_key)

        return triggered_alerts

    def _evaluate_single_rule(self, rule: AlertRule, data: Dict) -> Tuple[bool, Dict]:
        """评估单个规则"""
        details = {}

        if rule.rule_type == RuleType.PRICE_CHANGE:
            return self._evaluate_price_change(rule, data, details)
        elif rule.rule_type == RuleType.VOLUME_CHANGE:
            return self._evaluate_volume_change(rule, data, details)
        elif rule.rule_type == RuleType.PLEDGE_RATIO:
            return self._evaluate_pledge_ratio(rule, data, details)
        elif rule.rule_type == RuleType.NEWS_SENTIMENT:
            return self._evaluate_news_sentiment(rule, data, details)
        elif rule.rule_type == RuleType.ANOMALY_DETECTION:
            return self._evaluate_anomaly(rule, data, details)
        elif rule.rule_type == RuleType.MULTI_FACTOR:
            return self._evaluate_multi_factor(rule, data, details)
        elif rule.rule_type == RuleType.CUSTOM:
            return self._evaluate_custom(rule, data, details)
        else:
            return self._evaluate_generic(rule, data, details)

    def _evaluate_price_change(self, rule: AlertRule, data: Dict, details: Dict) -> Tuple[bool, Dict]:
        """评估价格变动规则"""
        change_pct = data.get('change_pct', data.get('pct_chg', 0))
        if change_pct is None:
            return False, details

        for condition in rule.conditions:
            threshold = condition.value
            operator = condition.operator

            details['current_value'] = change_pct
            details['threshold'] = threshold
            details['operator'] = operator

            if self._compare(change_pct, operator, threshold):
                details['message'] = f"涨跌幅 {change_pct:.2f}% {operator} {threshold}%"
                return True, details

        return False, details

    def _evaluate_volume_change(self, rule: AlertRule, data: Dict, details: Dict) -> Tuple[bool, Dict]:
        """评估成交量变动规则"""
        volume = data.get('volume', 0)
        avg_volume = data.get('avg_volume', data.get('volume_ma5', 0))

        if not volume or not avg_volume:
            return False, details

        volume_ratio = volume / avg_volume if avg_volume > 0 else 0

        for condition in rule.conditions:
            threshold = condition.value
            operator = condition.operator

            details['current_volume'] = volume
            details['avg_volume'] = avg_volume
            details['volume_ratio'] = volume_ratio
            details['threshold'] = threshold

            if self._compare(volume_ratio, operator, threshold):
                details['message'] = f"成交量是均量的 {volume_ratio:.2f} 倍"
                return True, details

        return False, details

    def _evaluate_pledge_ratio(self, rule: AlertRule, data: Dict, details: Dict) -> Tuple[bool, Dict]:
        """评估质押比例规则"""
        pledge_ratio = data.get('pledge_ratio', 0)
        if pledge_ratio is None:
            return False, details

        for condition in rule.conditions:
            threshold = condition.value
            operator = condition.operator

            details['pledge_ratio'] = pledge_ratio
            details['threshold'] = threshold

            if self._compare(pledge_ratio, operator, threshold):
                details['message'] = f"质押比例 {pledge_ratio:.2f}% {operator} {threshold}%"
                return True, details

        return False, details

    def _evaluate_news_sentiment(self, rule: AlertRule, data: Dict, details: Dict) -> Tuple[bool, Dict]:
        """评估新闻情绪规则"""
        sentiment_score = data.get('sentiment_score', 50)
        negative_count = data.get('negative_news_count', 0)

        for condition in rule.conditions:
            field = condition.field
            threshold = condition.value
            operator = condition.operator

            if field == 'sentiment_score':
                details['sentiment_score'] = sentiment_score
                if self._compare(sentiment_score, operator, threshold):
                    details['message'] = f"情绪评分 {sentiment_score} {operator} {threshold}"
                    return True, details
            elif field == 'negative_count':
                details['negative_count'] = negative_count
                if self._compare(negative_count, operator, threshold):
                    details['message'] = f"负面新闻数量 {negative_count} {operator} {threshold}"
                    return True, details

        return False, details

    # ==================== 智能预警：异常检测 ====================

    def _evaluate_anomaly(self, rule: AlertRule, data: Dict, details: Dict) -> Tuple[bool, Dict]:
        """
        基于历史数据的异常检测

        使用Z-Score方法检测异常值：
        - 计算历史数据的均值和标准差
        - 当前值偏离均值超过N个标准差时触发预警
        """
        stock_code = data.get('stock_code', '')
        field = rule.conditions[0].field if rule.conditions else 'change_pct'
        current_value = data.get(field, 0)

        if current_value is None:
            return False, details

        # 获取历史数据
        history_key = f"{stock_code}_{field}"
        history = self._history_cache.get(history_key, [])

        # 需要至少20个历史数据点
        if len(history) < 20:
            # 添加当前值到历史
            history.append(current_value)
            self._history_cache[history_key] = history[-100:]  # 保留最近100个
            return False, details

        # 计算统计量
        mean = statistics.mean(history)
        stdev = statistics.stdev(history)

        if stdev == 0:
            return False, details

        # 计算Z-Score
        z_score = (current_value - mean) / stdev

        # 默认阈值：3个标准差
        threshold = rule.conditions[0].value if rule.conditions else 3.0

        details['current_value'] = current_value
        details['mean'] = mean
        details['stdev'] = stdev
        details['z_score'] = z_score
        details['threshold'] = threshold

        # 添加当前值到历史
        history.append(current_value)
        self._history_cache[history_key] = history[-100:]

        if abs(z_score) > threshold:
            direction = "异常高" if z_score > 0 else "异常低"
            details['message'] = f"{field} {direction}，Z-Score: {z_score:.2f}"
            return True, details

        return False, details

    def update_history(self, stock_code: str, field: str, value: float) -> None:
        """更新历史数据缓存"""
        history_key = f"{stock_code}_{field}"
        history = self._history_cache.get(history_key, [])
        history.append(value)
        self._history_cache[history_key] = history[-100:]

    # ==================== 智能预警：多因子综合 ====================

    def _evaluate_multi_factor(self, rule: AlertRule, data: Dict, details: Dict) -> Tuple[bool, Dict]:
        """
        多因子综合预警

        综合多个因子的加权评分：
        - 价格因子：涨跌幅、波动率
        - 成交量因子：量比、换手率
        - 资金因子：主力净流入、北向资金
        - 情绪因子：新闻情绪、舆情热度
        - 风险因子：质押比例、ST状态
        """
        factors = {}
        total_score = 0
        total_weight = 0

        # 价格因子
        change_pct = data.get('change_pct', 0) or 0
        price_score = self._normalize_score(abs(change_pct), 0, 10)
        factors['price'] = {'value': change_pct, 'score': price_score, 'weight': 1.5}
        total_score += price_score * 1.5
        total_weight += 1.5

        # 成交量因子
        volume_ratio = data.get('volume_ratio', 1) or 1
        volume_score = self._normalize_score(volume_ratio, 0, 5)
        factors['volume'] = {'value': volume_ratio, 'score': volume_score, 'weight': 1.0}
        total_score += volume_score * 1.0
        total_weight += 1.0

        # 资金因子
        net_inflow = data.get('net_inflow', 0) or 0
        inflow_score = self._normalize_score(abs(net_inflow / 1e8), 0, 10)  # 以亿为单位
        factors['fund'] = {'value': net_inflow, 'score': inflow_score, 'weight': 1.2}
        total_score += inflow_score * 1.2
        total_weight += 1.2

        # 情绪因子
        sentiment_score = data.get('sentiment_score', 50) or 50
        sentiment_deviation = abs(sentiment_score - 50) / 50  # 偏离中性的程度
        sentiment_factor_score = sentiment_deviation * 100
        factors['sentiment'] = {'value': sentiment_score, 'score': sentiment_factor_score, 'weight': 0.8}
        total_score += sentiment_factor_score * 0.8
        total_weight += 0.8

        # 风险因子
        pledge_ratio = data.get('pledge_ratio', 0) or 0
        risk_score = self._normalize_score(pledge_ratio, 0, 80)
        factors['risk'] = {'value': pledge_ratio, 'score': risk_score, 'weight': 1.0}
        total_score += risk_score * 1.0
        total_weight += 1.0

        # 计算综合评分
        final_score = total_score / total_weight if total_weight > 0 else 0

        details['factors'] = factors
        details['final_score'] = final_score

        # 默认阈值：综合评分超过60触发预警
        threshold = rule.conditions[0].value if rule.conditions else 60

        if final_score >= threshold:
            # 找出主要触发因子
            main_factors = sorted(factors.items(), key=lambda x: x[1]['score'] * x[1]['weight'], reverse=True)[:3]
            main_factor_names = [f[0] for f in main_factors]
            details['message'] = f"多因子综合评分 {final_score:.1f}，主要因子: {', '.join(main_factor_names)}"
            return True, details

        return False, details

    def _normalize_score(self, value: float, min_val: float, max_val: float) -> float:
        """将值归一化到0-100"""
        if max_val <= min_val:
            return 0
        normalized = (value - min_val) / (max_val - min_val)
        return max(0, min(100, normalized * 100))

    def _evaluate_custom(self, rule: AlertRule, data: Dict, details: Dict) -> Tuple[bool, Dict]:
        """评估自定义规则"""
        return self._evaluate_generic(rule, data, details)

    def _evaluate_generic(self, rule: AlertRule, data: Dict, details: Dict) -> Tuple[bool, Dict]:
        """通用规则评估"""
        for condition in rule.conditions:
            field = condition.field
            value = data.get(field)

            if value is None:
                continue

            threshold = condition.value
            operator = condition.operator

            details[field] = value
            details['threshold'] = threshold

            if self._compare(value, operator, threshold):
                details['message'] = f"{field} {value} {operator} {threshold}"
                return True, details

        return False, details

    # ==================== 预警聚合 ====================

    def aggregate_alerts(self, alerts: List[Dict]) -> List[AggregatedAlert]:
        """
        聚合预警

        避免通知轰炸，将相似预警合并：
        - 同一股票的预警合并
        - 同类型预警合并
        - 时间窗口内的预警合并
        """
        if not self._aggregation_config.get('enabled', True):
            # 不聚合，直接返回
            return [self._create_single_aggregation(alert) for alert in alerts]

        # 添加到待聚合列表
        self._pending_alerts.extend(alerts)

        # 清理过期的待聚合预警
        self._cleanup_pending_alerts()

        # 执行聚合
        aggregated = self._do_aggregate()

        return aggregated

    def _do_aggregate(self) -> List[AggregatedAlert]:
        """执行聚合逻辑"""
        if not self._pending_alerts:
            return []

        config = self._aggregation_config
        time_window = timedelta(minutes=config.get('time_window', 5))
        max_count = config.get('max_count', 10)
        same_stock_only = config.get('same_stock_only', True)
        same_type_only = config.get('same_type_only', False)

        # 按聚合键分组
        groups: Dict[str, List[Dict]] = {}

        for alert in self._pending_alerts:
            key_parts = []

            if same_stock_only:
                key_parts.append(alert.get('stock_code', ''))
            if same_type_only:
                key_parts.append(alert.get('rule_type', ''))

            key = '_'.join(key_parts) if key_parts else 'all'

            if key not in groups:
                groups[key] = []
            groups[key].append(alert)

        # 生成聚合结果
        aggregated = []
        now = datetime.now()

        for key, group_alerts in groups.items():
            # 限制每组最大数量
            group_alerts = group_alerts[:max_count]

            if len(group_alerts) == 1:
                # 单个预警不聚合
                aggregated.append(self._create_single_aggregation(group_alerts[0]))
            else:
                # 多个预警聚合
                stock_codes = list(set(a.get('stock_code', '') for a in group_alerts))
                alert_types = list(set(a.get('rule_type', '') for a in group_alerts))

                # 解析时间
                times = []
                for a in group_alerts:
                    try:
                        t = datetime.fromisoformat(a.get('trigger_time', now.isoformat()))
                        times.append(t)
                    except:
                        times.append(now)

                first_time = min(times) if times else now
                last_time = max(times) if times else now

                # 生成摘要
                if len(stock_codes) == 1:
                    summary = f"{stock_codes[0]} 触发 {len(group_alerts)} 条预警"
                else:
                    summary = f"{len(stock_codes)} 只股票触发 {len(group_alerts)} 条预警"

                aggregated.append(AggregatedAlert(
                    alert_id=self._generate_aggregation_id(group_alerts),
                    alerts=group_alerts,
                    count=len(group_alerts),
                    first_time=first_time,
                    last_time=last_time,
                    stock_codes=stock_codes,
                    alert_types=alert_types,
                    summary=summary
                ))

        # 清空已处理的预警
        self._pending_alerts.clear()

        return aggregated

    def _create_single_aggregation(self, alert: Dict) -> AggregatedAlert:
        """创建单个预警的聚合对象"""
        now = datetime.now()
        try:
            trigger_time = datetime.fromisoformat(alert.get('trigger_time', now.isoformat()))
        except:
            trigger_time = now

        return AggregatedAlert(
            alert_id=self._generate_aggregation_id([alert]),
            alerts=[alert],
            count=1,
            first_time=trigger_time,
            last_time=trigger_time,
            stock_codes=[alert.get('stock_code', '')],
            alert_types=[alert.get('rule_type', '')],
            summary=alert.get('details', {}).get('message', alert.get('rule_name', ''))
        )

    def _generate_aggregation_id(self, alerts: List[Dict]) -> str:
        """生成聚合ID"""
        content = json.dumps(alerts, sort_keys=True, default=str)
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def _cleanup_pending_alerts(self) -> None:
        """清理过期的待聚合预警"""
        time_window = timedelta(minutes=self._aggregation_config.get('time_window', 5))
        cutoff = datetime.now() - time_window

        self._pending_alerts = [
            a for a in self._pending_alerts
            if self._parse_time(a.get('trigger_time')) > cutoff
        ]

    def _parse_time(self, time_str: str) -> datetime:
        """解析时间字符串"""
        try:
            return datetime.fromisoformat(time_str)
        except:
            return datetime.now()

    # ==================== 冷却管理 ====================

    def _is_in_cooldown(self, key: str, cooldown_minutes: int) -> bool:
        """检查是否在冷却期"""
        if key not in self._cooldown_cache:
            return False

        last_trigger = self._cooldown_cache[key]
        cooldown = timedelta(minutes=cooldown_minutes)

        return datetime.now() - last_trigger < cooldown

    def _set_cooldown(self, key: str) -> None:
        """设置冷却"""
        self._cooldown_cache[key] = datetime.now()

    def clear_cooldown(self, key: str = None) -> None:
        """清除冷却"""
        if key:
            self._cooldown_cache.pop(key, None)
        else:
            self._cooldown_cache.clear()

    # ==================== 辅助方法 ====================

    def _compare(self, value: Any, operator: str, threshold: Any) -> bool:
        """比较操作"""
        try:
            if operator == '>':
                return value > threshold
            elif operator == '>=':
                return value >= threshold
            elif operator == '<':
                return value < threshold
            elif operator == '<=':
                return value <= threshold
            elif operator == '==':
                return value == threshold
            elif operator == '!=':
                return value != threshold
            elif operator == 'contains':
                return str(threshold) in str(value)
            elif operator == 'not_contains':
                return str(threshold) not in str(value)
            else:
                return False
        except:
            return False


# 单例
_alert_rules_engine: Optional[AlertRulesEngine] = None


def get_alert_rules_engine() -> AlertRulesEngine:
    """获取预警规则引擎单例"""
    global _alert_rules_engine
    if _alert_rules_engine is None:
        _alert_rules_engine = AlertRulesEngine()
    return _alert_rules_engine
