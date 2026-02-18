"""
自动交易服务
核心功能：交易计划管理、实时监控、自动执行
"""

import asyncio
from datetime import datetime, time, date, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
import uuid
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
import json

from .strategy_rule_engine import StrategyRuleEngine, TradeSignal, SignalType, get_strategy_rule_engine
from .virtual_trading import VirtualTradingService, get_virtual_trading_service
from .trading_rules import TradingTimeManager, get_trading_time_manager

logger = logging.getLogger(__name__)


class TradingTimeChecker:
    """交易时间检查器"""

    MORNING_START = time(9, 30)
    MORNING_END = time(11, 30)
    AFTERNOON_START = time(13, 0)
    AFTERNOON_END = time(15, 0)

    @classmethod
    def is_trading_time(cls) -> bool:
        """判断当前是否为交易时间"""
        now = datetime.now()

        # 周末不交易
        if now.weekday() >= 5:
            return False

        current_time = now.time()

        # 上午交易时段
        if cls.MORNING_START <= current_time <= cls.MORNING_END:
            return True

        # 下午交易时段
        if cls.AFTERNOON_START <= current_time <= cls.AFTERNOON_END:
            return True

        return False

    @classmethod
    def get_next_trading_time(cls) -> datetime:
        """获取下一个交易时间"""
        now = datetime.now()
        current_time = now.time()

        # 如果在交易时间内，返回当前时间
        if cls.is_trading_time():
            return now

        # 如果在上午开盘前
        if current_time < cls.MORNING_START:
            return datetime.combine(now.date(), cls.MORNING_START)

        # 如果在午休时间
        if cls.MORNING_END < current_time < cls.AFTERNOON_START:
            return datetime.combine(now.date(), cls.AFTERNOON_START)

        # 如果在收盘后，返回下一个交易日
        next_day = now.date()
        while True:
            next_day = next_day + timedelta(days=1)
            if next_day.weekday() < 5:  # 跳过周末
                break

        return datetime.combine(next_day, cls.MORNING_START)


@dataclass
class TradingPlanRuntime:
    """交易计划运行时状态"""
    plan_id: str
    strategy_id: str
    strategy_name: str
    strategy_config: Dict
    stock_code: str
    stock_name: str

    # 参数
    initial_capital: float = 100000
    max_position_ratio: float = 0.3
    entry_mode: str = "rule_only"
    exit_mode: str = "rule_only"
    check_interval: int = 30
    stop_loss_pct: float = 0.05
    take_profit_pct: float = 0.15

    # 状态
    status: str = "pending"
    is_running: bool = False

    # 持仓
    current_position: int = 0
    avg_cost: float = 0
    current_price: float = 0
    stop_loss_price: float = 0
    take_profit_price: float = 0

    # 统计
    signals_generated: int = 0
    trades_executed: int = 0
    total_profit_loss: float = 0

    # 时间
    started_at: Optional[datetime] = None
    last_check_at: Optional[datetime] = None

    # 最新数据
    last_indicators: Dict = field(default_factory=dict)
    entry_conditions_status: List[Dict] = field(default_factory=list)
    exit_conditions_status: List[Dict] = field(default_factory=list)


class AutoTradeService:
    """自动交易服务"""

    def __init__(self):
        self.rule_engine = get_strategy_rule_engine()
        self.trading_service = get_virtual_trading_service()
        self.trading_time_checker = TradingTimeChecker()

        # 运行中的计划
        self.plans: Dict[str, TradingPlanRuntime] = {}

        # 监控线程
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._is_running = False

        # 回调
        self.on_signal_callback: Optional[Callable] = None
        self.on_trade_callback: Optional[Callable] = None
        self.on_status_update_callback: Optional[Callable] = None

        # 线程池
        self._executor = ThreadPoolExecutor(max_workers=5)

        logger.info("[AutoTradeService] 自动交易服务初始化完成")

    def create_plan(self, plan_data: Dict) -> TradingPlanRuntime:
        """创建交易计划"""
        plan_id = str(uuid.uuid4())[:8]

        plan = TradingPlanRuntime(
            plan_id=plan_id,
            strategy_id=plan_data.get("strategy_id", ""),
            strategy_name=plan_data.get("strategy_name", ""),
            strategy_config=plan_data.get("strategy_config", {}),
            stock_code=plan_data.get("stock_code", ""),
            stock_name=plan_data.get("stock_name", ""),
            initial_capital=plan_data.get("initial_capital", 100000),
            max_position_ratio=plan_data.get("max_position_ratio", 0.3),
            entry_mode=plan_data.get("entry_mode", "rule_only"),
            exit_mode=plan_data.get("exit_mode", "rule_only"),
            check_interval=plan_data.get("check_interval", 30),
            stop_loss_pct=plan_data.get("stop_loss_pct", 0.05),
            take_profit_pct=plan_data.get("take_profit_pct", 0.15),
        )

        self.plans[plan_id] = plan
        logger.info(f"[AutoTradeService] 创建交易计划: {plan_id} - {plan.stock_code}")

        return plan

    def start_plan(self, plan_id: str) -> bool:
        """启动交易计划"""
        if plan_id not in self.plans:
            logger.error(f"[AutoTradeService] 计划不存在: {plan_id}")
            return False

        plan = self.plans[plan_id]
        plan.status = "running"
        plan.is_running = True
        plan.started_at = datetime.now()

        # 确保监控服务运行
        if not self._is_running:
            self.start_monitor()

        logger.info(f"[AutoTradeService] 启动计划: {plan_id}")
        return True

    def pause_plan(self, plan_id: str) -> bool:
        """暂停交易计划"""
        if plan_id not in self.plans:
            return False

        plan = self.plans[plan_id]
        plan.status = "paused"
        plan.is_running = False

        logger.info(f"[AutoTradeService] 暂停计划: {plan_id}")
        return True

    def stop_plan(self, plan_id: str) -> bool:
        """停止交易计划"""
        if plan_id not in self.plans:
            return False

        plan = self.plans[plan_id]
        plan.status = "stopped"
        plan.is_running = False

        logger.info(f"[AutoTradeService] 停止计划: {plan_id}")
        return True

    def delete_plan(self, plan_id: str) -> bool:
        """删除交易计划"""
        if plan_id not in self.plans:
            return False

        del self.plans[plan_id]
        logger.info(f"[AutoTradeService] 删除计划: {plan_id}")
        return True

    def get_plan(self, plan_id: str) -> Optional[Dict]:
        """获取计划详情"""
        if plan_id not in self.plans:
            return None
        return self._plan_to_dict(self.plans[plan_id])

    def get_all_plans(self) -> List[Dict]:
        """获取所有计划"""
        return [self._plan_to_dict(p) for p in self.plans.values()]

    def _plan_to_dict(self, plan: TradingPlanRuntime) -> Dict:
        """计划转字典"""
        return {
            "plan_id": plan.plan_id,
            "strategy_id": plan.strategy_id,
            "strategy_name": plan.strategy_name,
            "stock_code": plan.stock_code,
            "stock_name": plan.stock_name,
            "initial_capital": plan.initial_capital,
            "max_position_ratio": plan.max_position_ratio,
            "entry_mode": plan.entry_mode,
            "exit_mode": plan.exit_mode,
            "check_interval": plan.check_interval,
            "stop_loss_pct": plan.stop_loss_pct,
            "take_profit_pct": plan.take_profit_pct,
            "status": plan.status,
            "current_position": plan.current_position,
            "avg_cost": plan.avg_cost,
            "current_price": plan.current_price,
            "stop_loss_price": plan.stop_loss_price,
            "take_profit_price": plan.take_profit_price,
            "signals_generated": plan.signals_generated,
            "trades_executed": plan.trades_executed,
            "total_profit_loss": plan.total_profit_loss,
            "started_at": plan.started_at.isoformat() if plan.started_at else None,
            "last_check_at": plan.last_check_at.isoformat() if plan.last_check_at else None,
            "last_indicators": plan.last_indicators,
            "entry_conditions_status": plan.entry_conditions_status,
            "exit_conditions_status": plan.exit_conditions_status,
        }

    def start_monitor(self):
        """启动监控服务"""
        if self._is_running:
            return

        self._is_running = True
        self._stop_event.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("[AutoTradeService] 监控服务已启动")

    def stop_monitor(self):
        """停止监控服务"""
        self._is_running = False
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("[AutoTradeService] 监控服务已停止")

    def _monitor_loop(self):
        """监控主循环"""
        while not self._stop_event.is_set():
            try:
                # 检查是否有运行中的计划
                running_plans = [p for p in self.plans.values() if p.is_running]

                if not running_plans:
                    self._stop_event.wait(5)
                    continue

                # 检查交易时间
                if not TradingTimeChecker.is_trading_time():
                    logger.debug("[AutoTradeService] 非交易时间，等待...")
                    self._stop_event.wait(60)
                    continue

                # 检查每个计划
                for plan in running_plans:
                    try:
                        self._check_plan(plan)
                    except Exception as e:
                        logger.error(f"[AutoTradeService] 检查计划失败 {plan.plan_id}: {e}")

                # 等待最小检查间隔
                min_interval = min(p.check_interval for p in running_plans) if running_plans else 30
                self._stop_event.wait(min_interval)

            except Exception as e:
                logger.error(f"[AutoTradeService] 监控循环异常: {e}")
                self._stop_event.wait(5)

    def _check_plan(self, plan: TradingPlanRuntime):
        """检查单个计划"""
        now = datetime.now()

        # 检查是否需要检查
        if plan.last_check_at:
            elapsed = (now - plan.last_check_at).total_seconds()
            if elapsed < plan.check_interval:
                return

        plan.last_check_at = now

        # 获取K线数据
        kline_data = self._get_kline_data(plan.stock_code)
        if not kline_data:
            logger.warning(f"[AutoTradeService] 获取K线数据失败: {plan.stock_code}")
            return

        # 获取实时行情
        quote = self._get_realtime_quote(plan.stock_code)
        if quote:
            plan.current_price = quote.get("current_price", 0)
            plan.stock_name = quote.get("stock_name", plan.stock_name)

        # 分析当前状态
        analysis = self.rule_engine.analyze_current_state(kline_data, plan.strategy_config)

        # 更新计划状态
        plan.last_indicators = analysis.get("indicators", {})
        plan.entry_conditions_status = analysis.get("entry_analysis", {}).get("condition_status", [])
        plan.exit_conditions_status = analysis.get("exit_analysis", {}).get("condition_status", [])

        # 触发状态更新回调
        if self.on_status_update_callback:
            self.on_status_update_callback(self._plan_to_dict(plan))

        # 判断是否有信号
        if analysis.get("has_signal"):
            signal_type = analysis.get("signal_type")

            if signal_type == "BUY" and plan.current_position == 0:
                # 入场信号
                self._handle_entry_signal(plan, analysis)
            elif signal_type == "SELL" and plan.current_position > 0:
                # 出场信号
                self._handle_exit_signal(plan, analysis)

        # 检查止损止盈
        if plan.current_position > 0:
            self._check_stop_loss_take_profit(plan)

    def _handle_entry_signal(self, plan: TradingPlanRuntime, analysis: Dict):
        """处理入场信号"""
        plan.signals_generated += 1

        suggestion = analysis.get("trade_suggestion", {})
        price = suggestion.get("price", plan.current_price)
        stop_loss = suggestion.get("stop_loss", price * (1 - plan.stop_loss_pct))
        take_profit = suggestion.get("take_profit", price * (1 + plan.take_profit_pct))

        # 计算买入数量
        position_value = plan.initial_capital * plan.max_position_ratio
        quantity = int(position_value / price / 100) * 100  # 整百股

        if quantity < 100:
            logger.warning(f"[AutoTradeService] 资金不足，无法买入: {plan.stock_code}")
            return

        # 根据入场模式决定是否执行
        should_execute = True

        if plan.entry_mode == "rule_llm":
            # 需要LLM确认
            llm_confirm = self._llm_confirm_entry(plan, analysis)
            should_execute = llm_confirm.get("should_buy", False)

        if should_execute:
            # 执行买入
            success, msg, order = self.trading_service.buy(
                stock_code=plan.stock_code,
                stock_name=plan.stock_name,
                quantity=quantity,
                price=price,
                strategy_id=plan.strategy_id
            )

            if success:
                plan.current_position = quantity
                plan.avg_cost = price
                plan.stop_loss_price = stop_loss
                plan.take_profit_price = take_profit
                plan.trades_executed += 1

                logger.info(f"[AutoTradeService] 买入成功: {plan.stock_code} {quantity}股 @ {price}")

                if self.on_trade_callback:
                    self.on_trade_callback({
                        "plan_id": plan.plan_id,
                        "action": "BUY",
                        "stock_code": plan.stock_code,
                        "quantity": quantity,
                        "price": price,
                        "order": order
                    })
            else:
                logger.error(f"[AutoTradeService] 买入失败: {msg}")

    def _handle_exit_signal(self, plan: TradingPlanRuntime, analysis: Dict):
        """处理出场信号"""
        plan.signals_generated += 1

        price = plan.current_price
        quantity = plan.current_position

        # 根据出场模式决定是否执行
        should_execute = True

        if plan.exit_mode == "rule_llm":
            # 需要LLM确认
            llm_confirm = self._llm_confirm_exit(plan, analysis)
            should_execute = llm_confirm.get("should_sell", False)

        if should_execute:
            # 执行卖出
            success, msg, order = self.trading_service.sell(
                stock_code=plan.stock_code,
                quantity=quantity,
                price=price,
                strategy_id=plan.strategy_id
            )

            if success:
                profit = (price - plan.avg_cost) * quantity
                plan.total_profit_loss += profit
                plan.current_position = 0
                plan.avg_cost = 0
                plan.stop_loss_price = 0
                plan.take_profit_price = 0
                plan.trades_executed += 1

                logger.info(f"[AutoTradeService] 卖出成功: {plan.stock_code} {quantity}股 @ {price}, 盈亏: {profit:.2f}")

                if self.on_trade_callback:
                    self.on_trade_callback({
                        "plan_id": plan.plan_id,
                        "action": "SELL",
                        "stock_code": plan.stock_code,
                        "quantity": quantity,
                        "price": price,
                        "profit": profit,
                        "order": order
                    })
            else:
                logger.error(f"[AutoTradeService] 卖出失败: {msg}")

    def _check_stop_loss_take_profit(self, plan: TradingPlanRuntime):
        """检查止损止盈"""
        if plan.current_position <= 0:
            return

        price = plan.current_price

        # 止损
        if plan.stop_loss_price > 0 and price <= plan.stop_loss_price:
            logger.info(f"[AutoTradeService] 触发止损: {plan.stock_code} @ {price}")
            self._execute_stop_loss(plan)
            return

        # 止盈
        if plan.take_profit_price > 0 and price >= plan.take_profit_price:
            logger.info(f"[AutoTradeService] 触发止盈: {plan.stock_code} @ {price}")
            self._execute_take_profit(plan)
            return

    def _execute_stop_loss(self, plan: TradingPlanRuntime):
        """执行止损"""
        success, msg, order = self.trading_service.sell(
            stock_code=plan.stock_code,
            quantity=plan.current_position,
            price=plan.current_price,
            strategy_id=plan.strategy_id
        )

        if success:
            profit = (plan.current_price - plan.avg_cost) * plan.current_position
            plan.total_profit_loss += profit
            plan.current_position = 0
            plan.avg_cost = 0
            plan.trades_executed += 1

            if self.on_trade_callback:
                self.on_trade_callback({
                    "plan_id": plan.plan_id,
                    "action": "STOP_LOSS",
                    "stock_code": plan.stock_code,
                    "price": plan.current_price,
                    "profit": profit
                })

    def _execute_take_profit(self, plan: TradingPlanRuntime):
        """执行止盈"""
        success, msg, order = self.trading_service.sell(
            stock_code=plan.stock_code,
            quantity=plan.current_position,
            price=plan.current_price,
            strategy_id=plan.strategy_id
        )

        if success:
            profit = (plan.current_price - plan.avg_cost) * plan.current_position
            plan.total_profit_loss += profit
            plan.current_position = 0
            plan.avg_cost = 0
            plan.trades_executed += 1

            if self.on_trade_callback:
                self.on_trade_callback({
                    "plan_id": plan.plan_id,
                    "action": "TAKE_PROFIT",
                    "stock_code": plan.stock_code,
                    "price": plan.current_price,
                    "profit": profit
                })

    def _get_kline_data(self, stock_code: str) -> List[Dict]:
        """获取K线数据"""
        try:
            import akshare as ak
            df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", adjust="qfq")

            if df.empty:
                return []

            df = df.tail(120)

            kline_data = []
            for _, row in df.iterrows():
                kline_data.append({
                    "date": str(row["日期"]),
                    "open": float(row["开盘"]),
                    "close": float(row["收盘"]),
                    "high": float(row["最高"]),
                    "low": float(row["最低"]),
                    "volume": float(row["成交量"]),
                    "amount": float(row.get("成交额", 0)),
                    "change_pct": float(row.get("涨跌幅", 0))
                })

            return kline_data
        except Exception as e:
            logger.error(f"获取K线数据失败 {stock_code}: {e}")
            return []

    def _get_realtime_quote(self, stock_code: str) -> Optional[Dict]:
        """获取实时行情"""
        try:
            import akshare as ak
            df = ak.stock_zh_a_spot_em()
            row = df[df["代码"] == stock_code]

            if row.empty:
                return None

            row = row.iloc[0]
            return {
                "stock_code": stock_code,
                "stock_name": row.get("名称", ""),
                "current_price": float(row.get("最新价", 0)),
                "open": float(row.get("今开", 0)),
                "high": float(row.get("最高", 0)),
                "low": float(row.get("最低", 0)),
                "prev_close": float(row.get("昨收", 0)),
                "volume": float(row.get("成交量", 0)),
                "amount": float(row.get("成交额", 0)),
                "change_pct": float(row.get("涨跌幅", 0)),
            }
        except Exception as e:
            logger.error(f"获取实时行情失败 {stock_code}: {e}")
            return None

    def _llm_confirm_entry(self, plan: TradingPlanRuntime, analysis: Dict) -> Dict:
        """LLM确认入场"""
        try:
            import asyncio
            from backend.services.llm.llm_client import LLMClient
            import os

            # 获取LLM配置
            api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("SILICONFLOW_API_KEY")
            if not api_key:
                logger.warning("[AutoTradeService] 未配置LLM API密钥，跳过LLM确认")
                return {"should_buy": True, "confidence": 0.7, "reason": "未配置LLM，使用规则引擎结果"}

            # 构建提示词
            prompt = f"""你是一个专业的量化交易分析师。请分析以下买入信号是否可靠。

股票信息:
- 代码: {plan.stock_code}
- 名称: {plan.stock_name}
- 当前价格: {plan.current_price}

策略信息:
- 策略名称: {plan.strategy_name}
- 入场条件满足情况: {json.dumps(analysis.get('entry_analysis', {}), ensure_ascii=False)}

技术指标:
{json.dumps(analysis.get('indicators', {}), ensure_ascii=False, indent=2)}

请分析并给出建议，以JSON格式返回:
{{
    "should_buy": true/false,
    "confidence": 0.0-1.0,
    "reason": "分析理由",
    "risk_factors": ["风险因素1", "风险因素2"],
    "suggested_position_ratio": 0.0-1.0
}}
"""

            # 使用DeepSeek或SiliconFlow
            provider = "deepseek" if os.getenv("DEEPSEEK_API_KEY") else "siliconflow"
            base_url = None
            model = "deepseek-chat"

            if provider == "siliconflow":
                base_url = "https://api.siliconflow.cn/v1"
                model = "deepseek-ai/DeepSeek-V2.5"

            client = LLMClient(
                provider=provider if provider == "deepseek" else "openai",
                model=model,
                api_key=api_key,
                base_url=base_url
            )

            # 同步调用异步方法
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(
                    client.generate(
                        prompt=prompt,
                        system_prompt="你是一个专业的量化交易分析师，擅长分析股票买入信号的可靠性。请用JSON格式回复。",
                        temperature=0.3,
                        max_tokens=1000,
                        format="json"
                    )
                )
            finally:
                loop.close()

            # 解析响应
            result = json.loads(response)
            logger.info(f"[AutoTradeService] LLM入场确认结果: {result}")
            return result

        except Exception as e:
            logger.error(f"[AutoTradeService] LLM入场确认失败: {e}")
            return {"should_buy": True, "confidence": 0.6, "reason": f"LLM确认失败: {str(e)}，使用规则引擎结果"}

    def _llm_confirm_exit(self, plan: TradingPlanRuntime, analysis: Dict) -> Dict:
        """LLM确认出场"""
        try:
            import asyncio
            from backend.services.llm.llm_client import LLMClient
            import os

            # 获取LLM配置
            api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("SILICONFLOW_API_KEY")
            if not api_key:
                logger.warning("[AutoTradeService] 未配置LLM API密钥，跳过LLM确认")
                return {"should_sell": True, "confidence": 0.7, "reason": "未配置LLM，使用规则引擎结果"}

            # 计算当前盈亏
            unrealized_pnl = (plan.current_price - plan.avg_cost) * plan.current_position
            unrealized_pnl_pct = ((plan.current_price - plan.avg_cost) / plan.avg_cost * 100) if plan.avg_cost > 0 else 0

            # 构建提示词
            prompt = f"""你是一个专业的量化交易分析师。请分析以下卖出信号是否可靠。

股票信息:
- 代码: {plan.stock_code}
- 名称: {plan.stock_name}
- 当前价格: {plan.current_price}

持仓信息:
- 持仓数量: {plan.current_position}股
- 持仓成本: {plan.avg_cost}
- 浮动盈亏: {unrealized_pnl:.2f} ({unrealized_pnl_pct:.2f}%)
- 止损价: {plan.stop_loss_price}
- 止盈价: {plan.take_profit_price}

策略信息:
- 策略名称: {plan.strategy_name}
- 出场条件满足情况: {json.dumps(analysis.get('exit_analysis', {}), ensure_ascii=False)}

技术指标:
{json.dumps(analysis.get('indicators', {}), ensure_ascii=False, indent=2)}

请分析并给出建议，以JSON格式返回:
{{
    "should_sell": true/false,
    "confidence": 0.0-1.0,
    "reason": "分析理由",
    "suggested_action": "全部卖出/部分卖出/继续持有",
    "suggested_sell_ratio": 0.0-1.0
}}
"""

            # 使用DeepSeek或SiliconFlow
            provider = "deepseek" if os.getenv("DEEPSEEK_API_KEY") else "siliconflow"
            base_url = None
            model = "deepseek-chat"

            if provider == "siliconflow":
                base_url = "https://api.siliconflow.cn/v1"
                model = "deepseek-ai/DeepSeek-V2.5"

            client = LLMClient(
                provider=provider if provider == "deepseek" else "openai",
                model=model,
                api_key=api_key,
                base_url=base_url
            )

            # 同步调用异步方法
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(
                    client.generate(
                        prompt=prompt,
                        system_prompt="你是一个专业的量化交易分析师，擅长分析股票卖出信号的可靠性。请用JSON格式回复。",
                        temperature=0.3,
                        max_tokens=1000,
                        format="json"
                    )
                )
            finally:
                loop.close()

            # 解析响应
            result = json.loads(response)
            logger.info(f"[AutoTradeService] LLM出场确认结果: {result}")
            return result

        except Exception as e:
            logger.error(f"[AutoTradeService] LLM出场确认失败: {e}")
            return {"should_sell": True, "confidence": 0.6, "reason": f"LLM确认失败: {str(e)}，使用规则引擎结果"}


# 全局实例
auto_trade_service = AutoTradeService()


def get_auto_trade_service() -> AutoTradeService:
    """获取自动交易服务实例"""
    return auto_trade_service
