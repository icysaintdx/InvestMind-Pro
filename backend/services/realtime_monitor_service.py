"""
实时盯盘监控服务
参考 aiagents-stock 的 SmartMonitorEngine 实现
支持实时循环监控、AI 决策、自动交易执行
"""

import asyncio
from datetime import datetime, time
from typing import Dict, List, Optional, Any, Callable
import json
from pathlib import Path
from enum import Enum

from backend.utils.logging_config import get_logger

logger = get_logger("services.realtime_monitor")


class MonitorMode(str, Enum):
    """监控模式"""
    REALTIME = "realtime"  # 实时循环模式
    SCHEDULED = "scheduled"  # 固定时间点模式


class MonitorStatus(str, Enum):
    """监控状态"""
    IDLE = "idle"  # 空闲
    RUNNING = "running"  # 运行中
    PAUSED = "paused"  # 暂停（非交易时段）
    STOPPED = "stopped"  # 已停止
    ERROR = "error"  # 错误


class RealTimeMonitorService:
    """
    实时盯盘监控服务
    
    功能：
    - 实时循环监控（可配置间隔，默认5分钟）
    - 交易时段检查（9:30-11:30, 13:00-15:00）
    - AI 决策分析
    - 自动执行交易
    - 止盈止损自动触发
    - WebSocket 实时推送
    """
    
    def __init__(self):
        self.status: MonitorStatus = MonitorStatus.IDLE
        self.mode: MonitorMode = MonitorMode.REALTIME
        
        # 监控配置
        self.monitor_interval: int = 300  # 默认5分钟（秒）
        self.enable_ai_decision: bool = True  # 启用AI决策
        self.enable_auto_trade: bool = True  # 启用自动交易
        self.trading_hours_only: bool = True  # 仅在交易时段运行
        
        # 监控的股票列表
        self.monitored_stocks: Dict[str, Dict] = {}  # {stock_code: {stop_loss, take_profit, ...}}
        
        # 运行状态
        self._monitor_task: Optional[asyncio.Task] = None
        self._stop_event: asyncio.Event = asyncio.Event()
        
        # 统计信息
        self.stats = {
            "total_checks": 0,
            "total_decisions": 0,
            "total_trades": 0,
            "last_check_time": None,
            "last_decision_time": None,
            "last_trade_time": None,
            "errors": []
        }
        
        # 事件回调
        self._event_callbacks: List[Callable] = []
        
        # 配置文件路径
        self.config_file = Path("backend/data/realtime_monitor_config.json")
        
        # 加载配置
        self._load_config()
        
        logger.info("实时盯盘监控服务初始化完成")
    
    def _load_config(self):
        """加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.monitor_interval = config.get("monitor_interval", 300)
                    self.enable_ai_decision = config.get("enable_ai_decision", True)
                    self.enable_auto_trade = config.get("enable_auto_trade", True)
                    self.trading_hours_only = config.get("trading_hours_only", True)
                    self.monitored_stocks = config.get("monitored_stocks", {})
                    self.mode = MonitorMode(config.get("mode", "realtime"))
                    logger.info(f"已加载监控配置: 间隔={self.monitor_interval}秒, 股票数={len(self.monitored_stocks)}")
            except Exception as e:
                logger.warning(f"加载配置失败: {e}")
    
    def _save_config(self):
        """保存配置"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            config = {
                "monitor_interval": self.monitor_interval,
                "enable_ai_decision": self.enable_ai_decision,
                "enable_auto_trade": self.enable_auto_trade,
                "trading_hours_only": self.trading_hours_only,
                "monitored_stocks": self.monitored_stocks,
                "mode": self.mode.value,
                "last_update": datetime.now().isoformat()
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            logger.debug("监控配置已保存")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
    
    def is_trading_time(self) -> bool:
        """
        检查当前是否在交易时段
        
        A股交易时段：
        - 上午：9:30 - 11:30
        - 下午：13:00 - 15:00
        
        Returns:
            bool: 是否在交易时段
        """
        now = datetime.now()
        current_time = now.time()
        
        # 检查是否是工作日（周一到周五）
        if now.weekday() >= 5:  # 周六=5, 周日=6
            return False
        
        # 上午交易时段
        morning_start = time(9, 30)
        morning_end = time(11, 30)
        
        # 下午交易时段
        afternoon_start = time(13, 0)
        afternoon_end = time(15, 0)
        
        is_morning = morning_start <= current_time <= morning_end
        is_afternoon = afternoon_start <= current_time <= afternoon_end
        
        return is_morning or is_afternoon
    
    def get_next_trading_time(self) -> Optional[datetime]:
        """获取下一个交易时段开始时间"""
        now = datetime.now()
        current_time = now.time()
        
        # 如果是工作日
        if now.weekday() < 5:
            # 如果在上午开盘前
            if current_time < time(9, 30):
                return now.replace(hour=9, minute=30, second=0, microsecond=0)
            # 如果在午休时间
            elif time(11, 30) < current_time < time(13, 0):
                return now.replace(hour=13, minute=0, second=0, microsecond=0)
            # 如果在收盘后
            elif current_time >= time(15, 0):
                # 下一个工作日
                next_day = now.replace(hour=9, minute=30, second=0, microsecond=0)
                days_ahead = 1
                if now.weekday() == 4:  # 周五
                    days_ahead = 3
                from datetime import timedelta
                return next_day + timedelta(days=days_ahead)
        else:
            # 周末，找下周一
            from datetime import timedelta
            days_ahead = 7 - now.weekday()
            next_monday = now + timedelta(days=days_ahead)
            return next_monday.replace(hour=9, minute=30, second=0, microsecond=0)
        
        return None
    
    async def start_monitor(self) -> Dict[str, Any]:
        """
        启动实时监控
        
        Returns:
            启动结果
        """
        if self.status == MonitorStatus.RUNNING:
            return {
                "success": False,
                "error": "监控已在运行中",
                "status": self.status.value
            }
        
        if not self.monitored_stocks:
            return {
                "success": False,
                "error": "没有监控的股票，请先添加股票",
                "status": self.status.value
            }
        
        try:
            self._stop_event.clear()
            self.status = MonitorStatus.RUNNING
            
            # 创建监控任务
            self._monitor_task = asyncio.create_task(self._monitor_loop())
            
            logger.info(f"实时监控已启动: 间隔={self.monitor_interval}秒, 股票数={len(self.monitored_stocks)}")
            
            # 发送事件通知
            await self._emit_event("monitor_started", {
                "interval": self.monitor_interval,
                "stocks": list(self.monitored_stocks.keys()),
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "success": True,
                "message": "监控已启动",
                "status": self.status.value,
                "interval": self.monitor_interval,
                "stocks_count": len(self.monitored_stocks)
            }
            
        except Exception as e:
            self.status = MonitorStatus.ERROR
            logger.error(f"启动监控失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "status": self.status.value
            }
    
    async def stop_monitor(self) -> Dict[str, Any]:
        """
        停止实时监控
        
        Returns:
            停止结果
        """
        if self.status not in [MonitorStatus.RUNNING, MonitorStatus.PAUSED]:
            return {
                "success": False,
                "error": "监控未在运行",
                "status": self.status.value
            }
        
        try:
            self._stop_event.set()
            
            if self._monitor_task:
                self._monitor_task.cancel()
                try:
                    await self._monitor_task
                except asyncio.CancelledError:
                    pass
                self._monitor_task = None
            
            self.status = MonitorStatus.STOPPED
            
            logger.info("实时监控已停止")
            
            # 发送事件通知
            await self._emit_event("monitor_stopped", {
                "timestamp": datetime.now().isoformat(),
                "stats": self.stats
            })
            
            return {
                "success": True,
                "message": "监控已停止",
                "status": self.status.value,
                "stats": self.stats
            }
            
        except Exception as e:
            logger.error(f"停止监控失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "status": self.status.value
            }
    
    async def _monitor_loop(self):
        """
        监控主循环
        """
        logger.info("监控循环开始运行")
        
        while not self._stop_event.is_set():
            try:
                # 检查交易时段
                if self.trading_hours_only and not self.is_trading_time():
                    if self.status != MonitorStatus.PAUSED:
                        self.status = MonitorStatus.PAUSED
                        next_time = self.get_next_trading_time()
                        logger.info(f"非交易时段，监控暂停。下一交易时段: {next_time}")
                        await self._emit_event("monitor_paused", {
                            "reason": "非交易时段",
                            "next_trading_time": next_time.isoformat() if next_time else None
                        })
                    
                    # 非交易时段，等待较长时间再检查
                    await asyncio.sleep(60)  # 每分钟检查一次是否进入交易时段
                    continue
                
                # 恢复运行状态
                if self.status == MonitorStatus.PAUSED:
                    self.status = MonitorStatus.RUNNING
                    logger.info("进入交易时段，监控恢复运行")
                    await self._emit_event("monitor_resumed", {
                        "timestamp": datetime.now().isoformat()
                    })
                
                # 执行监控检查
                await self._execute_monitor_check()
                
                # 等待下一次检查
                await asyncio.sleep(self.monitor_interval)
                
            except asyncio.CancelledError:
                logger.info("监控循环被取消")
                break
            except Exception as e:
                logger.error(f"监控循环错误: {e}", exc_info=True)
                self.stats["errors"].append({
                    "time": datetime.now().isoformat(),
                    "error": str(e)
                })
                # 保留最近10条错误
                self.stats["errors"] = self.stats["errors"][-10:]
                
                # 发送错误事件
                await self._emit_event("monitor_error", {
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
                
                # 出错后等待一段时间再继续
                await asyncio.sleep(30)
        
        logger.info("监控循环结束")
    
    async def _execute_monitor_check(self):
        """
        执行一次监控检查
        """
        self.stats["total_checks"] += 1
        self.stats["last_check_time"] = datetime.now().isoformat()
        
        logger.debug(f"执行监控检查 #{self.stats['total_checks']}")
        
        for stock_code, config in self.monitored_stocks.items():
            try:
                await self._check_single_stock(stock_code, config)
            except Exception as e:
                logger.error(f"检查股票 {stock_code} 失败: {e}")
    
    async def _check_single_stock(self, stock_code: str, config: Dict):
        """
        检查单只股票
        
        Args:
            stock_code: 股票代码
            config: 股票配置（止盈止损等）
        """
        # 获取实时行情
        market_data = await self._get_market_data(stock_code)
        if not market_data:
            logger.warning(f"获取 {stock_code} 行情失败")
            return
        
        current_price = market_data.get("current_price", 0)
        if current_price <= 0:
            return
        
        # 获取当前持仓
        position = await self._get_position(stock_code)
        
        # 1. 检查止盈止损（如果有持仓）
        if position and position.get("quantity", 0) > 0:
            sl_tp_action = await self._check_stop_loss_take_profit(
                stock_code, current_price, position, config
            )
            if sl_tp_action:
                # 触发止盈止损，执行卖出
                await self._execute_decision(stock_code, sl_tp_action, market_data)
                return
        
        # 2. AI 决策分析
        if self.enable_ai_decision:
            decision = await self._make_ai_decision(stock_code, market_data, position)
            
            if decision and decision.get("action") != "hold":
                self.stats["total_decisions"] += 1
                self.stats["last_decision_time"] = datetime.now().isoformat()
                
                # 发送决策事件
                await self._emit_event("decision_made", {
                    "stock_code": stock_code,
                    "decision": decision,
                    "market_data": market_data,
                    "timestamp": datetime.now().isoformat()
                })
                
                # 3. 自动执行交易
                if self.enable_auto_trade:
                    await self._execute_decision(stock_code, decision, market_data)
    
    async def _get_market_data(self, stock_code: str) -> Optional[Dict]:
        """获取实时行情数据"""
        try:
            from backend.services.market_data_service import get_realtime_quote
            quote = get_realtime_quote(stock_code)
            return quote
        except Exception as e:
            logger.error(f"获取行情失败 {stock_code}: {e}")
            return None
    
    async def _get_position(self, stock_code: str) -> Optional[Dict]:
        """获取当前持仓"""
        try:
            from backend.api.trading_api import simulator
            return simulator.positions.get(stock_code)
        except Exception as e:
            logger.error(f"获取持仓失败 {stock_code}: {e}")
            return None
    
    async def _check_stop_loss_take_profit(
        self, 
        stock_code: str, 
        current_price: float, 
        position: Dict,
        config: Dict
    ) -> Optional[Dict]:
        """
        检查止盈止损条件
        
        Args:
            stock_code: 股票代码
            current_price: 当前价格
            position: 持仓信息
            config: 止盈止损配置
            
        Returns:
            如果触发，返回卖出决策；否则返回 None
        """
        avg_cost = position.get("avg_cost", 0)
        quantity = position.get("quantity", 0)
        
        if avg_cost <= 0 or quantity <= 0:
            return None
        
        # 计算收益率
        profit_rate = (current_price - avg_cost) / avg_cost
        
        # 检查止损
        stop_loss_rate = config.get("stop_loss_rate")
        if stop_loss_rate and profit_rate <= -stop_loss_rate:
            logger.warning(f"触发止损: {stock_code} 收益率={profit_rate:.2%} <= -{stop_loss_rate:.2%}")
            return {
                "action": "sell",
                "quantity": quantity,
                "reason": f"触发止损: 收益率 {profit_rate:.2%}",
                "trigger_type": "stop_loss",
                "confidence": 1.0,
                "risk_level": "high"
            }
        
        # 检查止盈
        take_profit_rate = config.get("take_profit_rate")
        if take_profit_rate and profit_rate >= take_profit_rate:
            logger.info(f"触发止盈: {stock_code} 收益率={profit_rate:.2%} >= {take_profit_rate:.2%}")
            return {
                "action": "sell",
                "quantity": quantity,
                "reason": f"触发止盈: 收益率 {profit_rate:.2%}",
                "trigger_type": "take_profit",
                "confidence": 1.0,
                "risk_level": "low"
            }
        
        return None
    
    async def _make_ai_decision(
        self, 
        stock_code: str, 
        market_data: Dict,
        position: Optional[Dict]
    ) -> Optional[Dict]:
        """
        调用 AI 进行交易决策
        
        Args:
            stock_code: 股票代码
            market_data: 市场数据
            position: 当前持仓
            
        Returns:
            决策结果
        """
        try:
            from backend.api.auto_trading_api import call_trading_decision_llm, MarketData
            
            # 构建市场数据对象
            md = MarketData(
                stock_code=stock_code,
                current_price=market_data.get("current_price", 0),
                change_rate=market_data.get("change_rate", 0),
                volume=market_data.get("volume", 0),
                news_summary=None  # 可以后续添加新闻摘要
            )
            
            # 获取股票配置中的策略ID
            stock_config = self.monitored_stocks.get(stock_code, {})
            strategy_id = stock_config.get("strategy_id")
            
            # 调用 LLM 决策
            decision = await call_trading_decision_llm(
                stock_code=stock_code,
                market_data=md,
                analysis_result=None,
                current_position=position,
                strategy_id=strategy_id
            )
            
            return {
                "action": decision.action,
                "quantity": decision.quantity,
                "reason": decision.reason,
                "confidence": decision.confidence,
                "risk_level": decision.risk_level,
                "stop_loss": decision.stop_loss,
                "take_profit": decision.take_profit,
                "trigger_type": "ai_decision"
            }
            
        except Exception as e:
            logger.error(f"AI 决策失败 {stock_code}: {e}")
            return None
    
    async def _execute_decision(
        self, 
        stock_code: str, 
        decision: Dict,
        market_data: Dict
    ) -> Dict[str, Any]:
        """
        执行交易决策
        
        Args:
            stock_code: 股票代码
            decision: 决策结果
            market_data: 市场数据
            
        Returns:
            执行结果
        """
        action = decision.get("action", "hold")
        
        if action == "hold":
            return {"success": True, "action": "hold", "message": "持有观望"}
        
        try:
            from backend.api.trading_api import simulator, TradeOrder
            
            # 构建交易订单
            order = TradeOrder(
                stock_code=stock_code,
                action=action.upper(),
                quantity=decision.get("quantity", 100),
                price=market_data.get("current_price", 0),
                order_type="MARKET",
                stop_loss=decision.get("stop_loss"),
                take_profit=decision.get("take_profit")
            )
            
            # 执行交易
            result = await simulator.execute_trade(order)
            
            if result.get("success"):
                self.stats["total_trades"] += 1
                self.stats["last_trade_time"] = datetime.now().isoformat()
                
                logger.info(f"交易执行成功: {stock_code} {action} {decision.get('quantity')}股")
                
                # 发送交易事件
                await self._emit_event("trade_executed", {
                    "stock_code": stock_code,
                    "action": action,
                    "quantity": decision.get("quantity"),
                    "price": market_data.get("current_price"),
                    "reason": decision.get("reason"),
                    "trigger_type": decision.get("trigger_type"),
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                logger.warning(f"交易执行失败: {stock_code} - {result.get('error')}")
                
                await self._emit_event("trade_failed", {
                    "stock_code": stock_code,
                    "action": action,
                    "error": result.get("error"),
                    "timestamp": datetime.now().isoformat()
                })
            
            return result
            
        except Exception as e:
            logger.error(f"执行交易失败 {stock_code}: {e}")
            return {"success": False, "error": str(e)}
    
    # ==================== 股票管理 ====================
    
    def add_stock(
        self, 
        stock_code: str, 
        stop_loss_rate: Optional[float] = None,
        take_profit_rate: Optional[float] = None,
        strategy_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        添加监控股票
        
        Args:
            stock_code: 股票代码
            stop_loss_rate: 止损比例（如 0.05 表示 5%）
            take_profit_rate: 止盈比例
            strategy_id: 策略ID
            
        Returns:
            添加结果
        """
        self.monitored_stocks[stock_code] = {
            "stop_loss_rate": stop_loss_rate,
            "take_profit_rate": take_profit_rate,
            "strategy_id": strategy_id,
            "added_at": datetime.now().isoformat()
        }
        
        self._save_config()
        
        logger.info(f"添加监控股票: {stock_code}, 止损={stop_loss_rate}, 止盈={take_profit_rate}")
        
        return {
            "success": True,
            "message": f"已添加 {stock_code}",
            "config": self.monitored_stocks[stock_code]
        }
    
    def remove_stock(self, stock_code: str) -> Dict[str, Any]:
        """
        移除监控股票
        
        Args:
            stock_code: 股票代码
            
        Returns:
            移除结果
        """
        if stock_code not in self.monitored_stocks:
            return {
                "success": False,
                "error": f"股票 {stock_code} 不在监控列表中"
            }
        
        del self.monitored_stocks[stock_code]
        self._save_config()
        
        logger.info(f"移除监控股票: {stock_code}")
        
        return {
            "success": True,
            "message": f"已移除 {stock_code}"
        }
    
    def update_stock_config(
        self, 
        stock_code: str,
        stop_loss_rate: Optional[float] = None,
        take_profit_rate: Optional[float] = None,
        strategy_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        更新股票配置
        """
        if stock_code not in self.monitored_stocks:
            return {
                "success": False,
                "error": f"股票 {stock_code} 不在监控列表中"
            }
        
        config = self.monitored_stocks[stock_code]
        if stop_loss_rate is not None:
            config["stop_loss_rate"] = stop_loss_rate
        if take_profit_rate is not None:
            config["take_profit_rate"] = take_profit_rate
        if strategy_id is not None:
            config["strategy_id"] = strategy_id
        
        config["updated_at"] = datetime.now().isoformat()
        
        self._save_config()
        
        return {
            "success": True,
            "message": f"已更新 {stock_code} 配置",
            "config": config
        }
    
    # ==================== 配置管理 ====================
    
    def update_config(
        self,
        monitor_interval: Optional[int] = None,
        enable_ai_decision: Optional[bool] = None,
        enable_auto_trade: Optional[bool] = None,
        trading_hours_only: Optional[bool] = None,
        mode: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        更新监控配置
        """
        if monitor_interval is not None:
            self.monitor_interval = max(60, min(3600, monitor_interval))
        if enable_ai_decision is not None:
            self.enable_ai_decision = enable_ai_decision
        if enable_auto_trade is not None:
            self.enable_auto_trade = enable_auto_trade
        if trading_hours_only is not None:
            self.trading_hours_only = trading_hours_only
        if mode is not None:
            self.mode = MonitorMode(mode)
        
        self._save_config()
        
        return {
            "success": True,
            "config": self.get_config()
        }
    
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return {
            "monitor_interval": self.monitor_interval,
            "enable_ai_decision": self.enable_ai_decision,
            "enable_auto_trade": self.enable_auto_trade,
            "trading_hours_only": self.trading_hours_only,
            "mode": self.mode.value,
            "monitored_stocks": self.monitored_stocks
        }
    
    def get_status(self) -> Dict[str, Any]:
        """获取监控状态"""
        return {
            "status": self.status.value,
            "mode": self.mode.value,
            "is_trading_time": self.is_trading_time(),
            "next_trading_time": self.get_next_trading_time().isoformat() if self.get_next_trading_time() else None,
            "config": self.get_config(),
            "stats": self.stats,
            "stocks_count": len(self.monitored_stocks)
        }
    
    # ==================== 事件系统 ====================
    
    def register_event_callback(self, callback: Callable):
        """注册事件回调"""
        self._event_callbacks.append(callback)
    
    def unregister_event_callback(self, callback: Callable):
        """取消注册事件回调"""
        if callback in self._event_callbacks:
            self._event_callbacks.remove(callback)
    
    async def _emit_event(self, event_type: str, data: Dict):
        """发送事件"""
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        for callback in self._event_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"事件回调执行失败: {e}")


# 全局实例
_monitor_service: Optional[RealTimeMonitorService] = None


def get_monitor_service() -> RealTimeMonitorService:
    """获取监控服务实例"""
    global _monitor_service
    if _monitor_service is None:
        _monitor_service = RealTimeMonitorService()
    return _monitor_service