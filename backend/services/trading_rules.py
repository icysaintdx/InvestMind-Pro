"""
中国A股交易规则服务
包含：交易时间管理、T+1规则、涨跌停规则等
"""

from datetime import datetime, date, time, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MarketType(Enum):
    """市场类型"""
    MAIN_BOARD = "main_board"  # 主板（沪深）
    GEM = "gem"  # 创业板
    STAR = "star"  # 科创板
    BSE = "bse"  # 北交所
    

class TradingSession(Enum):
    """交易时段"""
    PRE_MARKET = "pre_market"  # 盘前集合竞价
    MORNING = "morning"  # 上午连续竞价
    LUNCH_BREAK = "lunch_break"  # 午间休市
    AFTERNOON = "afternoon"  # 下午连续竞价
    CLOSING_CALL = "closing_call"  # 收盘集合竞价
    AFTER_HOURS = "after_hours"  # 盘后
    CLOSED = "closed"  # 休市


@dataclass
class TradingTimeRange:
    """交易时间段"""
    start: time
    end: time
    session: TradingSession
    can_trade: bool  # 是否可以交易
    can_cancel: bool  # 是否可以撤单
    description: str


class TradingTimeManager:
    """交易时间管理器"""
    
    # 交易时间配置
    TRADING_TIMES = [
        TradingTimeRange(
            start=time(9, 15),
            end=time(9, 20),
            session=TradingSession.PRE_MARKET,
            can_trade=True,
            can_cancel=True,
            description="集合竞价（可挂单可撤单）"
        ),
        TradingTimeRange(
            start=time(9, 20),
            end=time(9, 25),
            session=TradingSession.PRE_MARKET,
            can_trade=True,
            can_cancel=False,
            description="集合竞价（可挂单不可撤单）"
        ),
        TradingTimeRange(
            start=time(9, 25),
            end=time(9, 30),
            session=TradingSession.PRE_MARKET,
            can_trade=False,
            can_cancel=False,
            description="集合竞价撮合"
        ),
        TradingTimeRange(
            start=time(9, 30),
            end=time(11, 30),
            session=TradingSession.MORNING,
            can_trade=True,
            can_cancel=True,
            description="上午连续竞价"
        ),
        TradingTimeRange(
            start=time(11, 30),
            end=time(13, 0),
            session=TradingSession.LUNCH_BREAK,
            can_trade=False,
            can_cancel=False,
            description="午间休市"
        ),
        TradingTimeRange(
            start=time(13, 0),
            end=time(14, 57),
            session=TradingSession.AFTERNOON,
            can_trade=True,
            can_cancel=True,
            description="下午连续竞价"
        ),
        TradingTimeRange(
            start=time(14, 57),
            end=time(15, 0),
            session=TradingSession.CLOSING_CALL,
            can_trade=True,
            can_cancel=False,
            description="收盘集合竞价"
        ),
    ]
    
    # 2024-2025年法定节假日（需要定期更新）
    HOLIDAYS_2024 = [
        # 元旦
        date(2024, 1, 1),
        # 春节
        date(2024, 2, 9), date(2024, 2, 10), date(2024, 2, 11),
        date(2024, 2, 12), date(2024, 2, 13), date(2024, 2, 14),
        date(2024, 2, 15), date(2024, 2, 16), date(2024, 2, 17),
        # 清明节
        date(2024, 4, 4), date(2024, 4, 5), date(2024, 4, 6),
        # 劳动节
        date(2024, 5, 1), date(2024, 5, 2), date(2024, 5, 3),
        date(2024, 5, 4), date(2024, 5, 5),
        # 端午节
        date(2024, 6, 8), date(2024, 6, 9), date(2024, 6, 10),
        # 中秋节
        date(2024, 9, 15), date(2024, 9, 16), date(2024, 9, 17),
        # 国庆节
        date(2024, 10, 1), date(2024, 10, 2), date(2024, 10, 3),
        date(2024, 10, 4), date(2024, 10, 5), date(2024, 10, 6),
        date(2024, 10, 7),
    ]
    
    HOLIDAYS_2025 = [
        # 元旦
        date(2025, 1, 1),
        # 春节（预估）
        date(2025, 1, 28), date(2025, 1, 29), date(2025, 1, 30),
        date(2025, 1, 31), date(2025, 2, 1), date(2025, 2, 2),
        date(2025, 2, 3), date(2025, 2, 4),
        # 清明节（预估）
        date(2025, 4, 4), date(2025, 4, 5), date(2025, 4, 6),
        # 劳动节（预估）
        date(2025, 5, 1), date(2025, 5, 2), date(2025, 5, 3),
        date(2025, 5, 4), date(2025, 5, 5),
        # 端午节（预估）
        date(2025, 5, 31), date(2025, 6, 1), date(2025, 6, 2),
        # 中秋节（预估）
        date(2025, 10, 6),
        # 国庆节（预估）
        date(2025, 10, 1), date(2025, 10, 2), date(2025, 10, 3),
        date(2025, 10, 4), date(2025, 10, 5), date(2025, 10, 6),
        date(2025, 10, 7),
    ]
    
    def __init__(self):
        self.holidays = set(self.HOLIDAYS_2024 + self.HOLIDAYS_2025)
    
    def is_trading_day(self, check_date: date = None) -> bool:
        """判断是否为交易日"""
        if check_date is None:
            check_date = date.today()
        
        # 周末不交易
        if check_date.weekday() >= 5:
            return False
        
        # 节假日不交易
        if check_date in self.holidays:
            return False
        
        return True
    
    def get_current_session(self, check_time: datetime = None) -> TradingTimeRange:
        """获取当前交易时段"""
        if check_time is None:
            check_time = datetime.now()
        
        current_time = check_time.time()
        
        for time_range in self.TRADING_TIMES:
            if time_range.start <= current_time < time_range.end:
                return time_range
        
        # 不在任何交易时段
        if current_time < time(9, 15):
            return TradingTimeRange(
                start=time(0, 0),
                end=time(9, 15),
                session=TradingSession.CLOSED,
                can_trade=False,
                can_cancel=False,
                description="盘前休市"
            )
        else:
            return TradingTimeRange(
                start=time(15, 0),
                end=time(23, 59),
                session=TradingSession.AFTER_HOURS,
                can_trade=False,
                can_cancel=False,
                description="盘后"
            )
    
    def can_trade_now(self) -> Tuple[bool, str]:
        """判断当前是否可以交易"""
        now = datetime.now()
        
        if not self.is_trading_day(now.date()):
            return False, "今日非交易日"
        
        session = self.get_current_session(now)
        
        if session.can_trade:
            return True, session.description
        else:
            return False, f"当前时段不可交易: {session.description}"
    
    def get_next_trading_day(self, from_date: date = None) -> date:
        """获取下一个交易日"""
        if from_date is None:
            from_date = date.today()
        
        next_day = from_date + timedelta(days=1)
        
        while not self.is_trading_day(next_day):
            next_day += timedelta(days=1)
            # 防止无限循环
            if (next_day - from_date).days > 30:
                break
        
        return next_day
    
    def get_trading_days_between(self, start_date: date, end_date: date) -> List[date]:
        """获取两个日期之间的所有交易日"""
        trading_days = []
        current = start_date
        
        while current <= end_date:
            if self.is_trading_day(current):
                trading_days.append(current)
            current += timedelta(days=1)
        
        return trading_days
    
    def get_time_to_next_session(self) -> Tuple[TradingSession, timedelta]:
        """获取距离下一个交易时段的时间"""
        now = datetime.now()
        current_time = now.time()
        
        for time_range in self.TRADING_TIMES:
            if current_time < time_range.start:
                next_session_start = datetime.combine(now.date(), time_range.start)
                return time_range.session, next_session_start - now
        
        # 今天交易已结束，返回明天开盘时间
        next_trading_day = self.get_next_trading_day(now.date())
        next_open = datetime.combine(next_trading_day, time(9, 30))
        return TradingSession.MORNING, next_open - now


class PriceLimitManager:
    """涨跌停管理器"""
    
    # 涨跌停配置
    PRICE_LIMITS = {
        MarketType.MAIN_BOARD: {
            "normal": 0.10,  # 普通股票10%
            "st": 0.05,  # ST股票5%
            "new_stock_first_day": None,  # 新股首日无涨跌幅（有临停）
        },
        MarketType.GEM: {
            "normal": 0.20,  # 创业板20%
            "new_stock_first_5_days": None,  # 新股前5日无涨跌幅
        },
        MarketType.STAR: {
            "normal": 0.20,  # 科创板20%
            "new_stock_first_5_days": None,  # 新股前5日无涨跌幅
        },
        MarketType.BSE: {
            "normal": 0.30,  # 北交所30%
            "new_stock_first_day": None,  # 新股首日无涨跌幅
        },
    }
    
    @classmethod
    def get_market_type(cls, stock_code: str) -> MarketType:
        """根据股票代码判断市场类型"""
        if stock_code.startswith('688'):
            return MarketType.STAR  # 科创板
        elif stock_code.startswith('300') or stock_code.startswith('301'):
            return MarketType.GEM  # 创业板
        elif stock_code.startswith('8') or stock_code.startswith('4'):
            return MarketType.BSE  # 北交所
        else:
            return MarketType.MAIN_BOARD  # 主板
    
    @classmethod
    def is_st_stock(cls, stock_name: str) -> bool:
        """判断是否为ST股票"""
        return 'ST' in stock_name.upper()
    
    @classmethod
    def get_price_limit(cls, stock_code: str, stock_name: str = "", 
                        is_new_stock: bool = False, listing_days: int = 100) -> Optional[float]:
        """获取涨跌停幅度"""
        market_type = cls.get_market_type(stock_code)
        limits = cls.PRICE_LIMITS[market_type]
        
        # 新股特殊处理
        if is_new_stock:
            if market_type in [MarketType.GEM, MarketType.STAR] and listing_days <= 5:
                return None  # 无涨跌幅限制
            elif market_type in [MarketType.MAIN_BOARD, MarketType.BSE] and listing_days <= 1:
                return None  # 首日无涨跌幅限制
        
        # ST股票
        if cls.is_st_stock(stock_name) and market_type == MarketType.MAIN_BOARD:
            return limits.get("st", 0.05)
        
        return limits.get("normal", 0.10)
    
    @classmethod
    def calculate_limit_prices(cls, stock_code: str, prev_close: float, 
                               stock_name: str = "") -> Tuple[float, float]:
        """计算涨停价和跌停价"""
        limit_pct = cls.get_price_limit(stock_code, stock_name)
        
        if limit_pct is None:
            # 无涨跌幅限制
            return float('inf'), 0.0
        
        # 计算涨跌停价（四舍五入到分）
        limit_up = round(prev_close * (1 + limit_pct), 2)
        limit_down = round(prev_close * (1 - limit_pct), 2)
        
        return limit_up, limit_down
    
    @classmethod
    def is_at_limit(cls, stock_code: str, current_price: float, prev_close: float,
                    stock_name: str = "") -> Tuple[bool, str]:
        """判断是否涨跌停"""
        limit_up, limit_down = cls.calculate_limit_prices(stock_code, prev_close, stock_name)
        
        if current_price >= limit_up:
            return True, "涨停"
        elif current_price <= limit_down:
            return True, "跌停"
        else:
            return False, "正常"


class TPlusOneManager:
    """T+1规则管理器"""
    
    def __init__(self, trading_time_manager: TradingTimeManager = None):
        self.trading_time_manager = trading_time_manager or TradingTimeManager()
        # 冻结持仓记录: {stock_code: [(quantity, buy_date, unfreeze_date), ...]}
        self.frozen_positions: Dict[str, List[Tuple[int, date, date]]] = {}
    
    def freeze_position(self, stock_code: str, quantity: int, buy_date: date = None):
        """冻结持仓（买入时调用）"""
        if buy_date is None:
            buy_date = date.today()
        
        unfreeze_date = self.trading_time_manager.get_next_trading_day(buy_date)
        
        if stock_code not in self.frozen_positions:
            self.frozen_positions[stock_code] = []
        
        self.frozen_positions[stock_code].append((quantity, buy_date, unfreeze_date))
        
        logger.info(f"冻结持仓: {stock_code} {quantity}股, 买入日期: {buy_date}, 解冻日期: {unfreeze_date}")
    
    def get_frozen_quantity(self, stock_code: str, check_date: date = None) -> int:
        """获取冻结数量"""
        if check_date is None:
            check_date = date.today()
        
        if stock_code not in self.frozen_positions:
            return 0
        
        frozen_qty = 0
        for qty, buy_date, unfreeze_date in self.frozen_positions[stock_code]:
            if check_date < unfreeze_date:
                frozen_qty += qty
        
        return frozen_qty
    
    def unfreeze_positions(self, check_date: date = None):
        """解冻到期的持仓（每日开盘前调用）"""
        if check_date is None:
            check_date = date.today()
        
        unfrozen_count = 0
        
        for stock_code in list(self.frozen_positions.keys()):
            remaining = []
            for qty, buy_date, unfreeze_date in self.frozen_positions[stock_code]:
                if check_date >= unfreeze_date:
                    logger.info(f"解冻持仓: {stock_code} {qty}股")
                    unfrozen_count += 1
                else:
                    remaining.append((qty, buy_date, unfreeze_date))
            
            if remaining:
                self.frozen_positions[stock_code] = remaining
            else:
                del self.frozen_positions[stock_code]
        
        return unfrozen_count
    
    def can_sell(self, stock_code: str, quantity: int, total_position: int) -> Tuple[bool, str]:
        """检查是否可以卖出"""
        frozen_qty = self.get_frozen_quantity(stock_code)
        available_qty = total_position - frozen_qty
        
        if quantity > available_qty:
            return False, f"可卖数量不足: 持仓{total_position}股, 冻结{frozen_qty}股, 可卖{available_qty}股"
        
        return True, f"可卖出: {quantity}股"
    
    def get_available_quantity(self, stock_code: str, total_position: int) -> int:
        """获取可卖数量"""
        frozen_qty = self.get_frozen_quantity(stock_code)
        return max(0, total_position - frozen_qty)


class TradingUnit:
    """交易单位管理"""
    
    MIN_BUY_UNIT = 100  # 最小买入单位（1手）
    MIN_SELL_UNIT = 1  # 最小卖出单位（可卖零股）
    MAX_ORDER_QUANTITY = 1000000  # 单笔最大委托数量
    MIN_PRICE_TICK = 0.01  # 最小价格变动单位
    
    @classmethod
    def validate_buy_quantity(cls, quantity: int) -> Tuple[bool, str]:
        """验证买入数量"""
        if quantity < cls.MIN_BUY_UNIT:
            return False, f"买入数量不能少于{cls.MIN_BUY_UNIT}股（1手）"
        
        if quantity % cls.MIN_BUY_UNIT != 0:
            return False, f"买入数量必须是{cls.MIN_BUY_UNIT}的整数倍"
        
        if quantity > cls.MAX_ORDER_QUANTITY:
            return False, f"单笔买入数量不能超过{cls.MAX_ORDER_QUANTITY}股"
        
        return True, "数量有效"
    
    @classmethod
    def validate_sell_quantity(cls, quantity: int, available: int) -> Tuple[bool, str]:
        """验证卖出数量"""
        if quantity < cls.MIN_SELL_UNIT:
            return False, f"卖出数量不能少于{cls.MIN_SELL_UNIT}股"
        
        if quantity > available:
            return False, f"卖出数量不能超过可卖数量{available}股"
        
        if quantity > cls.MAX_ORDER_QUANTITY:
            return False, f"单笔卖出数量不能超过{cls.MAX_ORDER_QUANTITY}股"
        
        return True, "数量有效"
    
    @classmethod
    def round_price(cls, price: float) -> float:
        """价格取整到分"""
        return round(price / cls.MIN_PRICE_TICK) * cls.MIN_PRICE_TICK
    
    @classmethod
    def calculate_buy_quantity(cls, available_cash: float, price: float, 
                               commission_rate: float = 0.0003) -> int:
        """计算可买数量"""
        # 考虑手续费
        total_cost_per_share = price * (1 + commission_rate)
        max_shares = int(available_cash / total_cost_per_share)
        
        # 取整到手
        return (max_shares // cls.MIN_BUY_UNIT) * cls.MIN_BUY_UNIT


# 创建全局实例
trading_time_manager = TradingTimeManager()
price_limit_manager = PriceLimitManager()
t_plus_one_manager = TPlusOneManager(trading_time_manager)


def get_trading_time_manager() -> TradingTimeManager:
    """获取交易时间管理器"""
    return trading_time_manager


def get_price_limit_manager() -> PriceLimitManager:
    """获取涨跌停管理器"""
    return price_limit_manager


def get_t_plus_one_manager() -> TPlusOneManager:
    """获取T+1管理器"""
    return t_plus_one_manager