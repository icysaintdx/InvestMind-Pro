"""
市场规则引擎
定义不同市场（A股、港股、美股）的交易规则
"""

from enum import Enum
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, time
import pytz


class MarketType(str, Enum):
    """市场类型"""
    CN = "CN"      # A股
    HK = "HK"      # 港股
    US = "US"      # 美股


class Currency(str, Enum):
    """货币类型"""
    CNY = "CNY"    # 人民币
    HKD = "HKD"    # 港币
    USD = "USD"    # 美元


@dataclass
class TradingSession:
    """交易时段"""
    open_time: time
    close_time: time
    name: str = ""


@dataclass
class CommissionRule:
    """手续费规则"""
    rate: float = 0.0003          # 佣金费率
    min_fee: float = 5.0          # 最低佣金
    stamp_duty: float = 0.001     # 印花税（仅卖出）
    stamp_duty_buy: bool = False  # 买入是否收印花税
    transaction_levy: float = 0.0 # 交易征费（港股）
    trading_fee: float = 0.0      # 交易费（港股）
    sec_fee: float = 0.0          # SEC费用（美股）


@dataclass
class PriceLimitRule:
    """涨跌停规则"""
    enabled: bool = True
    up_limit: float = 0.10        # 涨停幅度
    down_limit: float = -0.10     # 跌停幅度
    st_up_limit: float = 0.05     # ST股涨停
    st_down_limit: float = -0.05  # ST股跌停
    kcb_up_limit: float = 0.20    # 科创板涨停
    kcb_down_limit: float = -0.20 # 科创板跌停
    cyb_up_limit: float = 0.20    # 创业板涨停
    cyb_down_limit: float = -0.20 # 创业板跌停


@dataclass
class MarketRule:
    """市场规则"""
    market: MarketType
    currency: Currency
    name: str
    timezone: str

    # 交易规则
    t_plus: int = 1                    # T+N 交易
    lot_size: int = 100                # 最小交易单位（手）
    min_price_tick: float = 0.01       # 最小报价单位

    # 涨跌停规则
    price_limit: PriceLimitRule = field(default_factory=PriceLimitRule)

    # 手续费规则
    commission: CommissionRule = field(default_factory=CommissionRule)

    # 交易时段
    trading_sessions: List[TradingSession] = field(default_factory=list)

    # 其他规则
    short_selling: bool = False        # 是否支持做空
    margin_trading: bool = False       # 是否支持融资融券


# 预定义市场规则
MARKET_RULES: Dict[MarketType, MarketRule] = {
    MarketType.CN: MarketRule(
        market=MarketType.CN,
        currency=Currency.CNY,
        name="A股市场",
        timezone="Asia/Shanghai",
        t_plus=1,
        lot_size=100,
        min_price_tick=0.01,
        price_limit=PriceLimitRule(
            enabled=True,
            up_limit=0.10,
            down_limit=-0.10,
            st_up_limit=0.05,
            st_down_limit=-0.05,
            kcb_up_limit=0.20,
            kcb_down_limit=-0.20,
            cyb_up_limit=0.20,
            cyb_down_limit=-0.20
        ),
        commission=CommissionRule(
            rate=0.0003,      # 万三佣金
            min_fee=5.0,      # 最低5元
            stamp_duty=0.001, # 印花税千一（仅卖出）
            stamp_duty_buy=False
        ),
        trading_sessions=[
            TradingSession(time(9, 30), time(11, 30), "上午盘"),
            TradingSession(time(13, 0), time(15, 0), "下午盘")
        ],
        short_selling=False,
        margin_trading=True
    ),

    MarketType.HK: MarketRule(
        market=MarketType.HK,
        currency=Currency.HKD,
        name="港股市场",
        timezone="Asia/Hong_Kong",
        t_plus=0,
        lot_size=100,  # 港股每只股票手数不同，这里用默认值
        min_price_tick=0.01,
        price_limit=PriceLimitRule(enabled=False),  # 港股无涨跌停
        commission=CommissionRule(
            rate=0.0003,
            min_fee=3.0,
            stamp_duty=0.0013,        # 印花税 0.13%
            stamp_duty_buy=True,      # 买卖都收
            transaction_levy=0.00005, # 交易征费 0.005%
            trading_fee=0.00005       # 交易费 0.005%
        ),
        trading_sessions=[
            TradingSession(time(9, 30), time(12, 0), "上午盘"),
            TradingSession(time(13, 0), time(16, 0), "下午盘")
        ],
        short_selling=True,
        margin_trading=True
    ),

    MarketType.US: MarketRule(
        market=MarketType.US,
        currency=Currency.USD,
        name="美股市场",
        timezone="America/New_York",
        t_plus=0,
        lot_size=1,  # 美股1股起
        min_price_tick=0.01,
        price_limit=PriceLimitRule(enabled=False),  # 美股无涨跌停
        commission=CommissionRule(
            rate=0.0,         # 零佣金
            min_fee=0.0,
            stamp_duty=0.0,
            sec_fee=0.0000278 # SEC费用
        ),
        trading_sessions=[
            TradingSession(time(9, 30), time(16, 0), "常规交易")
        ],
        short_selling=True,
        margin_trading=True
    )
}


class MarketRuleEngine:
    """市场规则引擎"""

    def __init__(self):
        self.rules = MARKET_RULES

    def get_rule(self, market: MarketType) -> MarketRule:
        """获取市场规则"""
        return self.rules.get(market, self.rules[MarketType.CN])

    def detect_market(self, code: str) -> MarketType:
        """根据股票代码识别市场类型"""
        code = code.upper().strip()

        # 美股：纯字母或字母+数字（如 AAPL, TSLA, BRK.A）
        if code.isalpha() or (code.replace('.', '').isalpha()):
            return MarketType.US

        # 港股：5位数字或以 .HK 结尾
        if code.endswith('.HK') or code.endswith('.hk'):
            return MarketType.HK
        if len(code) == 5 and code.isdigit():
            return MarketType.HK
        if len(code) == 4 and code.isdigit():
            # 4位数字可能是港股（如 0700）
            return MarketType.HK

        # A股：6位数字
        if len(code) == 6 and code.isdigit():
            return MarketType.CN

        # 默认A股
        return MarketType.CN

    def normalize_code(self, code: str, market: MarketType) -> str:
        """标准化股票代码"""
        code = code.upper().strip()

        if market == MarketType.CN:
            # A股：补齐6位
            code = code.replace('.SH', '').replace('.SZ', '')
            return code.zfill(6)

        elif market == MarketType.HK:
            # 港股：去掉 .HK 后缀
            code = code.replace('.HK', '').replace('.hk', '')
            return code.zfill(5)

        elif market == MarketType.US:
            # 美股：保持原样
            return code

        return code

    def calculate_commission(
        self,
        market: MarketType,
        side: str,
        amount: float
    ) -> float:
        """计算手续费"""
        rule = self.get_rule(market)
        comm = rule.commission
        total = 0.0

        # 佣金
        commission = amount * comm.rate
        total += max(commission, comm.min_fee)

        # 印花税
        if side == 'sell' or (side == 'buy' and comm.stamp_duty_buy):
            total += amount * comm.stamp_duty

        # 港股额外费用
        if market == MarketType.HK:
            total += amount * comm.transaction_levy
            total += amount * comm.trading_fee

        # 美股 SEC 费用
        if market == MarketType.US and side == 'sell':
            total += amount * comm.sec_fee

        return round(total, 2)

    def validate_quantity(
        self,
        market: MarketType,
        quantity: int,
        code: str = ""
    ) -> tuple[bool, str]:
        """验证交易数量"""
        rule = self.get_rule(market)

        if quantity <= 0:
            return False, "交易数量必须大于0"

        if market == MarketType.CN:
            # A股必须是100的整数倍
            if quantity % rule.lot_size != 0:
                return False, f"A股交易数量必须是{rule.lot_size}的整数倍"

        return True, ""

    def check_price_limit(
        self,
        market: MarketType,
        current_price: float,
        prev_close: float,
        code: str = ""
    ) -> tuple[bool, float, float]:
        """检查涨跌停限制，返回 (是否在限制内, 涨停价, 跌停价)"""
        rule = self.get_rule(market)

        if not rule.price_limit.enabled:
            return True, float('inf'), 0.0

        # 根据股票类型确定涨跌停幅度
        up_limit = rule.price_limit.up_limit
        down_limit = rule.price_limit.down_limit

        if code:
            # ST股票
            if code.startswith('ST') or code.startswith('*ST'):
                up_limit = rule.price_limit.st_up_limit
                down_limit = rule.price_limit.st_down_limit
            # 科创板（688开头）
            elif code.startswith('688'):
                up_limit = rule.price_limit.kcb_up_limit
                down_limit = rule.price_limit.kcb_down_limit
            # 创业板（300开头）
            elif code.startswith('300'):
                up_limit = rule.price_limit.cyb_up_limit
                down_limit = rule.price_limit.cyb_down_limit

        limit_up_price = round(prev_close * (1 + up_limit), 2)
        limit_down_price = round(prev_close * (1 + down_limit), 2)

        is_valid = limit_down_price <= current_price <= limit_up_price

        return is_valid, limit_up_price, limit_down_price

    def is_trading_time(self, market: MarketType, dt: datetime = None) -> bool:
        """检查是否在交易时间内"""
        rule = self.get_rule(market)

        if dt is None:
            tz = pytz.timezone(rule.timezone)
            dt = datetime.now(tz)

        current_time = dt.time()

        for session in rule.trading_sessions:
            if session.open_time <= current_time <= session.close_time:
                return True

        return False

    def can_sell_today(
        self,
        market: MarketType,
        buy_date: datetime,
        current_date: datetime = None
    ) -> bool:
        """检查今日买入的股票是否可以卖出（T+N规则）"""
        rule = self.get_rule(market)

        if current_date is None:
            current_date = datetime.now()

        # T+0 可以当日卖出
        if rule.t_plus == 0:
            return True

        # T+1 需要隔日
        buy_day = buy_date.date()
        current_day = current_date.date()

        return (current_day - buy_day).days >= rule.t_plus


# 全局实例
market_rule_engine = MarketRuleEngine()


def get_market_rule_engine() -> MarketRuleEngine:
    """获取市场规则引擎实例"""
    return market_rule_engine
