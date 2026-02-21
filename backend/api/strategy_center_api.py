"""
策略中心 API
提供策略管理、LLM解析、信号生成、交易计划管理等功能
"""

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import uuid
import os
import logging
import asyncio

from backend.utils.logging_config import get_logger
from backend.api.strategies import PRESET_STRATEGIES, STRATEGY_CATEGORIES
from backend.services.llm_strategy_service import get_llm_strategy_service
from backend.services.auto_trade_service import get_auto_trade_service, TradingTimeChecker

logger = get_logger("api.strategy_center")
router = APIRouter(prefix="/api/strategy-center", tags=["Strategy Center"])


# ==================== 数据模型 ====================

class StrategyIndicator(BaseModel):
    name: str = Field(..., description="指标名称")
    type: str = Field(..., description="指标类型")
    params: Dict[str, Any] = Field(default_factory=dict)
    weight: float = Field(1.0, ge=0, le=1)


class TradingCondition(BaseModel):
    type: str = Field(..., description="条件类型")
    indicator: str = Field(...)
    operator: str = Field(...)
    value: Any = Field(...)
    description: str = Field("")


class StrategyCreateRequest(BaseModel):
    name: str
    description: str = ""
    category: str = "custom"
    indicators: List[StrategyIndicator] = Field(default_factory=list)
    entry_conditions: List[TradingCondition] = Field(default_factory=list)
    exit_conditions: List[TradingCondition] = Field(default_factory=list)
    risk_params: Dict[str, Any] = Field(default_factory=dict)
    source: str = "manual"


class StrategyParseRequest(BaseModel):
    text: str
    strategy_type: str = "auto"


class SignalGenerateRequest(BaseModel):
    stock_code: str
    strategy_id: str
    include_chart: bool = True
    include_news: bool = True
    timeframe: str = "daily"


# ==================== 交易计划数据模型 ====================

class CreateTradingPlanRequest(BaseModel):
    """创建交易计划请求"""
    strategy_id: str
    strategy_name: str
    strategy_config: Dict[str, Any]
    stock_code: str
    stock_name: Optional[str] = ""
    allocated_capital: float = 100000
    max_position_ratio: float = 0.3
    decision_mode: str = "rule_only"  # rule_only | rule_ai | ai_only
    check_interval: int = 30
    stop_loss_pct: float = 0.05
    take_profit_pct: float = 0.15
    trailing_stop: bool = False
    auto_start: bool = False


class UpdateTradingPlanRequest(BaseModel):
    """更新交易计划请求"""
    allocated_capital: Optional[float] = None
    max_position_ratio: Optional[float] = None
    decision_mode: Optional[str] = None
    check_interval: Optional[int] = None
    stop_loss_pct: Optional[float] = None
    take_profit_pct: Optional[float] = None
    trailing_stop: Optional[bool] = None


# ==================== 存储 ====================

custom_strategies: Dict[str, Dict[str, Any]] = {}

# 交易日志存储
trade_logs: List[Dict[str, Any]] = []


# ==================== WebSocket连接管理 ====================

class StrategyWSManager:
    """策略中心WebSocket连接管理器"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"[StrategyWS] 新连接，当前连接数: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"[StrategyWS] 断开连接，当前连接数: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """广播消息到所有连接"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"[StrategyWS] 发送消息失败: {e}")
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn)

    async def send_signal(self, signal_data: dict):
        """发送信号通知"""
        await self.broadcast({
            "type": "signal",
            "timestamp": datetime.now().isoformat(),
            "data": signal_data
        })

    async def send_trade(self, trade_data: dict):
        """发送交易通知"""
        await self.broadcast({
            "type": "trade",
            "timestamp": datetime.now().isoformat(),
            "data": trade_data
        })

    async def send_plan_update(self, plan_data: dict):
        """发送计划状态更新"""
        await self.broadcast({
            "type": "plan_update",
            "timestamp": datetime.now().isoformat(),
            "data": plan_data
        })


ws_manager = StrategyWSManager()


# ==================== 交易日志管理 ====================

def add_trade_log(
    log_type: str,
    source: str,
    stock_code: str,
    stock_name: str,
    action: str,
    message: str,
    plan_id: Optional[str] = None,
    strategy_name: Optional[str] = None,
    direction: Optional[str] = None,
    quantity: Optional[int] = None,
    price: Optional[float] = None,
    amount: Optional[float] = None,
    confidence: Optional[float] = None,
    conditions_met: Optional[List[str]] = None
) -> Dict[str, Any]:
    """添加交易日志"""
    log_entry = {
        "log_id": str(uuid.uuid4())[:8],
        "timestamp": datetime.now().isoformat(),
        "log_type": log_type,  # signal | order | execution | risk | system
        "source": source,  # manual | auto
        "plan_id": plan_id,
        "strategy_name": strategy_name,
        "stock_code": stock_code,
        "stock_name": stock_name,
        "action": action,
        "message": message,
        "direction": direction,
        "quantity": quantity,
        "price": price,
        "amount": amount,
        "confidence": confidence,
        "conditions_met": conditions_met
    }

    trade_logs.insert(0, log_entry)

    # 保持最近1000条日志
    if len(trade_logs) > 1000:
        trade_logs.pop()

    # 异步广播日志
    asyncio.create_task(ws_manager.broadcast({
        "type": "trade_log",
        "timestamp": datetime.now().isoformat(),
        "data": log_entry
    }))

    return log_entry


# ==================== API端点 ====================

@router.get("/strategies")
async def get_all_strategies(
    category: Optional[str] = Query(None, description="策略分类"),
    source: Optional[str] = Query(None, description="策略来源: preset/custom/llm_parsed")
):
    """获取所有策略列表"""
    strategies = []
    
    # 添加预设策略
    for s in PRESET_STRATEGIES:
        if category and s.get("category") != category:
            continue
        if source and s.get("source") != source:
            continue
        strategies.append(s)
    
    # 添加自定义策略
    for s in custom_strategies.values():
        if category and s.get("category") != category:
            continue
        if source and s.get("source") != source:
            continue
        strategies.append(s)
    
    return {
        "success": True,
        "data": strategies,
        "total": len(strategies),
        "categories": STRATEGY_CATEGORIES
    }


@router.get("/strategies/{strategy_id}")
async def get_strategy_detail(strategy_id: str):
    """获取策略详情"""
    # 先查预设策略
    for s in PRESET_STRATEGIES:
        if s["id"] == strategy_id:
            return {"success": True, "data": s}
    
    # 再查自定义策略
    if strategy_id in custom_strategies:
        return {"success": True, "data": custom_strategies[strategy_id]}
    
    raise HTTPException(status_code=404, detail="策略不存在")


@router.post("/strategies")
async def create_strategy(request: StrategyCreateRequest):
    """创建自定义策略"""
    strategy_id = f"custom_{uuid.uuid4().hex[:8]}"
    
    strategy = {
        "id": strategy_id,
        "name": request.name,
        "description": request.description,
        "category": request.category,
        "source": request.source,
        "icon": "📝",
        "indicators": [ind.dict() for ind in request.indicators],
        "entry_conditions": [cond.dict() for cond in request.entry_conditions],
        "exit_conditions": [cond.dict() for cond in request.exit_conditions],
        "risk_params": request.risk_params,
        "created_at": datetime.now().isoformat(),
        "avg_win_rate": 0.0
    }
    
    custom_strategies[strategy_id] = strategy
    logger.info(f"创建自定义策略: {strategy_id} - {request.name}")
    
    return {"success": True, "data": strategy, "message": "策略创建成功"}


@router.put("/strategies/{strategy_id}")
async def update_strategy(strategy_id: str, request: StrategyCreateRequest):
    """更新策略"""
    if strategy_id not in custom_strategies:
        # 检查是否是预设策略
        for s in PRESET_STRATEGIES:
            if s["id"] == strategy_id:
                raise HTTPException(status_code=400, detail="预设策略不可修改")
        raise HTTPException(status_code=404, detail="策略不存在")
    
    strategy = custom_strategies[strategy_id]
    strategy.update({
        "name": request.name,
        "description": request.description,
        "category": request.category,
        "indicators": [ind.dict() for ind in request.indicators],
        "entry_conditions": [cond.dict() for cond in request.entry_conditions],
        "exit_conditions": [cond.dict() for cond in request.exit_conditions],
        "risk_params": request.risk_params,
        "updated_at": datetime.now().isoformat()
    })
    
    return {"success": True, "data": strategy, "message": "策略更新成功"}


@router.delete("/strategies/{strategy_id}")
async def delete_strategy(strategy_id: str):
    """删除策略"""
    if strategy_id not in custom_strategies:
        for s in PRESET_STRATEGIES:
            if s["id"] == strategy_id:
                raise HTTPException(status_code=400, detail="预设策略不可删除")
        raise HTTPException(status_code=404, detail="策略不存在")
    
    del custom_strategies[strategy_id]
    logger.info(f"删除策略: {strategy_id}")
    
    return {"success": True, "message": "策略删除成功"}


@router.post("/parse")
async def parse_strategy_text(request: StrategyParseRequest):
    """使用LLM解析策略文本"""
    # TODO: 集成LLM解析
    # 这里返回模拟的解析结果
    
    parsed_strategy = {
        "id": f"parsed_{uuid.uuid4().hex[:8]}",
        "name": "LLM解析策略",
        "description": f"从文本解析: {request.text[:50]}...",
        "category": "custom",
        "source": "llm_parsed",
        "icon": "🤖",
        "indicators": [
            {"name": "MA", "type": "technical", "params": {"period": 20}, "weight": 0.5},
            {"name": "RSI", "type": "technical", "params": {"period": 14}, "weight": 0.5}
        ],
        "entry_conditions": [
            {"type": "entry", "indicator": "price", "operator": ">", "value": "MA20", "description": "价格站上MA20"}
        ],
        "exit_conditions": [
            {"type": "exit", "indicator": "price", "operator": "<", "value": "MA20", "description": "价格跌破MA20"}
        ],
        "risk_params": {"stop_loss": 0.05, "take_profit": 0.15, "max_position": 0.30},
        "original_text": request.text,
        "parsed_at": datetime.now().isoformat()
    }
    
    # 保存解析的策略
    custom_strategies[parsed_strategy["id"]] = parsed_strategy
    
    return {
        "success": True,
        "data": parsed_strategy,
        "message": "策略解析成功，已保存到自定义策略"
    }


@router.post("/signal/generate")
async def generate_trading_signal(request: SignalGenerateRequest):
    """生成交易信号 - 使用LLM进行真实分析"""
    import os
    
    # 获取策略
    strategy = None
    for s in PRESET_STRATEGIES:
        if s["id"] == request.strategy_id:
            strategy = s
            break
    
    if not strategy and request.strategy_id in custom_strategies:
        strategy = custom_strategies[request.strategy_id]
    
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")
    
    logger.info(f"开始生成交易信号: 股票={request.stock_code}, 策略={strategy['name']}")
    
    try:
        # 1. 获取市场数据
        market_data = await _get_market_data_for_signal(request.stock_code)
        market_data["strategy"] = strategy
        
        # 2. 获取新闻数据（如果需要）
        news_data = None
        if request.include_news:
            news_data = await _get_news_data_for_signal(request.stock_code)
        
        # 3. 检查是否配置了LLM
        llm_config = _get_llm_config()
        signal = None

        if llm_config:
            try:
                # 使用LLM进行分析
                llm_service = get_llm_strategy_service()
                llm_service.set_model_config(llm_config)

                # 执行LLM分析
                analysis_result = await llm_service.analyze_with_strategy(
                    strategy=strategy,
                    market_data=market_data,
                    news_data=news_data
                )

                # 构建信号响应
                signal = {
                    "stock_code": request.stock_code,
                    "strategy_id": request.strategy_id,
                    "strategy_name": strategy["name"],
                    "signal_type": analysis_result.get("signal", "HOLD"),
                    "confidence": analysis_result.get("confidence", 0.5),
                    "price_target": analysis_result.get("trade_instruction", {}).get("take_profit", market_data.get("current_price", 0) * 1.1),
                    "stop_loss": analysis_result.get("trade_instruction", {}).get("stop_loss", market_data.get("current_price", 0) * 0.95),
                    "take_profit": analysis_result.get("trade_instruction", {}).get("take_profit", market_data.get("current_price", 0) * 1.15),
                    "position_size": analysis_result.get("trade_instruction", {}).get("quantity_pct", 0.20),
                    "reasoning": analysis_result.get("trade_instruction", {}).get("reason", "基于策略分析"),
                    "analysis": analysis_result.get("analysis", {}),
                    "risk_assessment": analysis_result.get("risk_assessment", {}),
                    "key_levels": analysis_result.get("key_levels", {}),
                    "indicators_status": _format_indicators_status(market_data.get("indicators", {})),
                    "market_data_summary": {
                        "current_price": market_data.get("current_price", 0),
                        "change_pct": market_data.get("change_pct", 0),
                        "name": market_data.get("name", ""),
                        "kline_count": len(market_data.get("kline_data", []))
                    },
                    "generated_at": datetime.now().isoformat(),
                    "llm_used": True
                }
            except Exception as llm_error:
                # LLM调用失败，降级到规则引擎
                logger.warning(f"LLM调用失败，降级到规则引擎: {llm_error}")
                signal = None

        if signal is None:
            # 没有配置LLM或LLM调用失败，使用规则引擎进行基础分析
            logger.warning("使用规则引擎进行基础分析")
            signal = _generate_rule_based_signal(
                stock_code=request.stock_code,
                strategy=strategy,
                market_data=market_data
            )

        logger.info(f"信号生成完成: {signal['signal_type']} (置信度: {signal['confidence']})")
        return {"success": True, "data": signal}
        
    except Exception as e:
        logger.error(f"生成交易信号失败: {e}")
        raise HTTPException(status_code=500, detail=f"生成信号失败: {str(e)}")


def _get_llm_config() -> Optional[Dict[str, Any]]:
    """从agent_configs.json获取LLM配置"""
    import os

    # 从agent_configs.json读取用户配置的模型
    config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "agent_configs.json")
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            # 优先使用summarizerModel，其次使用selectedModels中的第一个
            model_name = config_data.get("summarizerModel")
            if not model_name:
                selected_models = config_data.get("selectedModels", [])
                if selected_models:
                    model_name = selected_models[0]

            if model_name:
                # 根据模型名称识别渠道
                api_key = None
                base_url = None
                model_type = "openai"  # 默认使用OpenAI兼容接口

                # Minimax模型 (kirocpa中转)
                if model_name.startswith("minimax"):
                    api_key = os.getenv("MINIMAX_API_KEY", "icysaintdx")
                    base_url = "https://kirocpa.zeabur.app/v1"
                    logger.info(f"使用Minimax模型(kirocpa): {model_name}")
                # SiliconFlow模型（包含/的通常是SiliconFlow格式）
                elif "/" in model_name:
                    api_key = os.getenv("MINIMAX_API_KEY", "icysaintdx") or os.getenv("SILICONFLOW_API_KEY")
                    base_url = "https://kirocpa.zeabur.app/v1"
                    logger.info(f"使用kirocpa中转模型: {model_name}")
                # DeepSeek模型
                elif model_name.startswith("deepseek"):
                    api_key = os.getenv("DEEPSEEK_API_KEY")
                    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
                    model_type = "deepseek"
                    logger.info(f"使用DeepSeek模型: {model_name}")
                # Gemini模型
                elif model_name.startswith("gemini"):
                    api_key = os.getenv("GEMINI_API_KEY")
                    logger.info(f"使用Gemini模型: {model_name}")
                # Qwen模型（阿里云）
                elif model_name.startswith("qwen"):
                    api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")
                    model_type = "dashscope"
                    logger.info(f"使用Qwen模型: {model_name}")
                # 其他模型尝试kirocpa中转
                else:
                    api_key = os.getenv("MINIMAX_API_KEY", "icysaintdx") or os.getenv("SILICONFLOW_API_KEY")
                    base_url = "https://kirocpa.zeabur.app/v1"
                    logger.info(f"使用kirocpa中转(默认): {model_name}")

                if api_key:
                    return {
                        "type": model_type,
                        "model": model_name,
                        "api_key": api_key,
                        "base_url": base_url
                    }
                else:
                    logger.warning(f"未找到模型 {model_name} 对应的API密钥")

    except Exception as e:
        logger.error(f"读取agent_configs.json失败: {e}")

    # 降级：优先使用kirocpa中转
    minimax_key = os.getenv("MINIMAX_API_KEY", "icysaintdx")
    if minimax_key:
        return {
            "type": "openai",
            "model": "minimax-m2.1",
            "api_key": minimax_key,
            "base_url": "https://kirocpa.zeabur.app/v1"
        }

    siliconflow_key = os.getenv("SILICONFLOW_API_KEY")
    if siliconflow_key:
        return {
            "type": "openai",
            "model": "Qwen/Qwen3-8B",
            "api_key": siliconflow_key,
            "base_url": "https://api.siliconflow.cn/v1"
        }

    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    if deepseek_key:
        return {
            "type": "deepseek",
            "model": "deepseek-chat",
            "api_key": deepseek_key,
            "base_url": "https://api.deepseek.com"
        }

    return None


async def _get_market_data_for_signal(stock_code: str) -> Dict[str, Any]:
    """获取用于信号生成的市场数据"""
    from datetime import timedelta
    
    result = {
        "symbol": stock_code,
        "name": "",
        "current_price": 0,
        "change_pct": 0,
        "kline_data": [],
        "indicators": {},
        "fundamentals": {}
    }
    
    # 清理股票代码
    clean_symbol = stock_code.replace('.SH', '').replace('.SZ', '')
    
    # 1. 获取实时行情
    try:
        from backend.dataflows.akshare.stock_data import get_stock_data
        stock_data = get_stock_data()
        
        quote = stock_data.get_stock_quote(clean_symbol)
        if quote:
            result["name"] = quote.get("名称", "")
            result["current_price"] = float(quote.get("最新价", 0) or 0)
            result["change_pct"] = float(quote.get("涨跌幅", 0) or 0)
    except Exception as e:
        logger.warning(f"获取实时行情失败: {e}")
    
    # 2. 获取K线数据
    try:
        from backend.dataflows.akshare.stock_data import get_stock_data
        stock_data = get_stock_data()
        
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=90)).strftime('%Y%m%d')
        
        hist_data = stock_data.get_stock_hist(
            symbol=clean_symbol,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq"
        )
        
        if hist_data:
            result["kline_data"] = hist_data[-60:]
    except Exception as e:
        logger.warning(f"获取K线数据失败: {e}")
    
    # 3. 计算技术指标
    try:
        if result["kline_data"]:
            result["indicators"] = _calculate_indicators(result["kline_data"])
    except Exception as e:
        logger.warning(f"计算技术指标失败: {e}")
    
    return result


def _calculate_indicators(kline_data: List[Dict]) -> Dict[str, Any]:
    """计算技术指标"""
    import pandas as pd
    
    if not kline_data:
        return {}
    
    df = pd.DataFrame(kline_data)
    
    # 列名映射
    column_mapping = {
        '日期': 'date', '开盘': 'open', '收盘': 'close',
        '最高': 'high', '最低': 'low', '成交量': 'volume'
    }
    for cn, en in column_mapping.items():
        if cn in df.columns:
            df[en] = df[cn]
    
    for col in ['open', 'close', 'high', 'low', 'volume']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    indicators = {}
    
    try:
        if 'close' in df.columns:
            # MA
            for period in [5, 10, 20, 60]:
                ma = df['close'].rolling(window=period).mean()
                if len(df) >= period and not pd.isna(ma.iloc[-1]):
                    indicators[f'MA{period}'] = round(ma.iloc[-1], 2)
            
            # RSI
            if len(df) >= 14:
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                if not pd.isna(rsi.iloc[-1]):
                    indicators['RSI14'] = round(rsi.iloc[-1], 2)
            
            # MACD
            if len(df) >= 26:
                exp1 = df['close'].ewm(span=12, adjust=False).mean()
                exp2 = df['close'].ewm(span=26, adjust=False).mean()
                macd = exp1 - exp2
                signal = macd.ewm(span=9, adjust=False).mean()
                if not pd.isna(macd.iloc[-1]):
                    indicators['MACD'] = round(macd.iloc[-1], 4)
                    indicators['MACD_Signal'] = round(signal.iloc[-1], 4)
    except Exception as e:
        logger.warning(f"计算指标出错: {e}")
    
    return indicators


async def _get_news_data_for_signal(stock_code: str) -> List[Dict[str, Any]]:
    """获取用于信号生成的新闻数据"""
    clean_symbol = stock_code.replace('.SH', '').replace('.SZ', '')
    
    try:
        from backend.dataflows.news.multi_source_news_aggregator import get_news_aggregator
        
        if clean_symbol.startswith('6'):
            ts_code = f"{clean_symbol}.SH"
        else:
            ts_code = f"{clean_symbol}.SZ"
        
        aggregator = get_news_aggregator()
        result = aggregator.aggregate_news(
            ts_code=ts_code,
            limit_per_source=5,
            include_tushare=False,
            include_akshare=True,
            include_market_news=True
        )
        
        return result.get('merged_news', [])[:10]
    except Exception as e:
        logger.warning(f"获取新闻数据失败: {e}")
        return []


def _format_indicators_status(indicators: Dict[str, Any]) -> List[Dict[str, Any]]:
    """格式化指标状态"""
    status_list = []

    # MA状态
    if 'MA' in indicators:
        ma_data = indicators['MA']
        if isinstance(ma_data, dict):
            for name, value in ma_data.items():
                if value is not None:
                    status_list.append({
                        "name": name,
                        "value": float(value) if value is not None else None,
                        "status": "neutral"
                    })
        elif isinstance(ma_data, (int, float)):
            status_list.append({
                "name": "MA",
                "value": float(ma_data),
                "status": "neutral"
            })

    # RSI状态
    if 'RSI' in indicators:
        rsi_data = indicators['RSI']
        rsi_value = None
        if isinstance(rsi_data, dict):
            rsi_value = rsi_data.get('RSI14') or rsi_data.get('RSI')
        elif isinstance(rsi_data, (int, float)):
            rsi_value = rsi_data

        if rsi_value is not None:
            rsi_value = float(rsi_value)
            status = "oversold" if rsi_value < 30 else ("overbought" if rsi_value > 70 else "neutral")
            status_list.append({
                "name": "RSI14",
                "value": rsi_value,
                "status": status
            })

    # MACD状态
    if 'MACD' in indicators:
        macd_data = indicators['MACD']
        macd_value = None
        if isinstance(macd_data, dict):
            macd_value = macd_data.get('MACD') or macd_data.get('DIF')
        elif isinstance(macd_data, (int, float)):
            macd_value = macd_data

        if macd_value is not None:
            macd_value = float(macd_value)
            status = "bullish" if macd_value > 0 else "bearish"
            status_list.append({
                "name": "MACD",
                "value": macd_value,
                "status": status
            })

    # 处理扁平化的指标
    import numpy as np
    for key, value in indicators.items():
        if key in ['MA', 'RSI', 'MACD', 'BOLL', 'KDJ', 'Volume', 'ATR']:
            continue
        if isinstance(value, (int, float, np.floating, np.integer)):
            status_list.append({
                "name": key,
                "value": float(value),
                "status": "neutral"
            })
    
    return status_list


def _generate_rule_based_signal(
    stock_code: str,
    strategy: Dict[str, Any],
    market_data: Dict[str, Any]
) -> Dict[str, Any]:
    """使用规则引擎生成基础信号（当LLM不可用时）"""
    import numpy as np

    indicators = market_data.get("indicators", {})
    current_price = market_data.get("current_price", 0)

    # 简单的规则判断
    signal_type = "HOLD"
    confidence = 0.5
    reasoning = "基于规则引擎分析"

    # 辅助函数：安全获取数值
    def safe_get_value(data, key=None):
        """安全获取数值，处理dict和numpy类型"""
        if data is None:
            return None
        if isinstance(data, dict):
            if key:
                val = data.get(key)
                if val is not None:
                    return float(val)
            return None
        if isinstance(data, (int, float, np.floating, np.integer)):
            return float(data)
        return None

    # 检查MA趋势
    ma_data = indicators.get("MA")
    ma5 = safe_get_value(indicators, "MA5") or safe_get_value(ma_data, "MA5")
    ma20 = safe_get_value(indicators, "MA20") or safe_get_value(ma_data, "MA20")

    if ma5 and ma20:
        if ma5 > ma20:
            signal_type = "BUY"
            confidence = 0.6
            reasoning = "短期均线在长期均线上方，趋势向上"
        elif ma5 < ma20:
            signal_type = "SELL"
            confidence = 0.6
            reasoning = "短期均线在长期均线下方，趋势向下"

    # 检查RSI
    rsi_data = indicators.get("RSI")
    rsi = safe_get_value(indicators, "RSI14") or safe_get_value(rsi_data, "RSI14") or safe_get_value(rsi_data, "RSI")
    if rsi is None and isinstance(rsi_data, (int, float, np.floating, np.integer)):
        rsi = float(rsi_data)

    if rsi:
        if rsi < 30:
            signal_type = "BUY"
            confidence = max(confidence, 0.65)
            reasoning = f"RSI={rsi:.2f}，处于超卖区域"
        elif rsi > 70:
            signal_type = "SELL"
            confidence = max(confidence, 0.65)
            reasoning = f"RSI={rsi:.2f}，处于超买区域"

    return {
        "stock_code": stock_code,
        "strategy_id": strategy.get("id", ""),
        "strategy_name": strategy.get("name", ""),
        "signal_type": signal_type,
        "confidence": confidence,
        "price_target": current_price * 1.1 if signal_type == "BUY" else current_price * 0.9,
        "stop_loss": current_price * 0.95 if signal_type == "BUY" else current_price * 1.05,
        "take_profit": current_price * 1.15 if signal_type == "BUY" else current_price * 0.85,
        "position_size": 0.20,
        "reasoning": reasoning,
        "analysis": {
            "technical": reasoning,
            "note": "此分析由规则引擎生成，建议配置LLM以获得更详细的分析"
        },
        "risk_assessment": {
            "level": "MEDIUM",
            "factors": ["规则引擎分析，准确度有限"],
            "suggestions": ["建议配置LLM API以获得更准确的分析"]
        },
        "indicators_status": _format_indicators_status(indicators),
        "market_data_summary": {
            "current_price": current_price,
            "change_pct": market_data.get("change_pct", 0),
            "name": market_data.get("name", ""),
            "kline_count": len(market_data.get("kline_data", []))
        },
        "generated_at": datetime.now().isoformat(),
        "llm_used": False
    }


@router.get("/categories")
async def get_strategy_categories():
    """获取策略分类"""
    return {
        "success": True,
        "data": STRATEGY_CATEGORIES
    }


@router.get("/indicators")
async def get_available_indicators():
    """获取可用指标列表"""
    indicators = {
        "technical": [
            {"name": "MA", "display": "移动平均线", "params": ["period"]},
            {"name": "EMA", "display": "指数移动平均", "params": ["period"]},
            {"name": "MACD", "display": "MACD", "params": ["fast", "slow", "signal"]},
            {"name": "RSI", "display": "相对强弱指数", "params": ["period"]},
            {"name": "BOLL", "display": "布林带", "params": ["period", "std"]},
            {"name": "KDJ", "display": "KDJ", "params": ["k_period", "d_period"]},
            {"name": "ADX", "display": "平均趋向指数", "params": ["period"]},
            {"name": "ATR", "display": "真实波幅", "params": ["period"]},
            {"name": "Volume", "display": "成交量", "params": ["ma_period"]},
            {"name": "Donchian", "display": "唐奇安通道", "params": ["period"]},
        ],
        "fundamental": [
            {"name": "PE", "display": "市盈率", "params": ["max", "min"]},
            {"name": "PB", "display": "市净率", "params": ["max", "min"]},
            {"name": "ROE", "display": "净资产收益率", "params": ["min"]},
            {"name": "PEG", "display": "市盈增长比", "params": ["max"]},
            {"name": "Debt_Ratio", "display": "资产负债率", "params": ["max"]},
            {"name": "Revenue_Growth", "display": "营收增长率", "params": ["min"]},
            {"name": "EPS_Growth", "display": "EPS增长率", "params": ["min"]},
            {"name": "Dividend_Yield", "display": "股息率", "params": ["min"]},
            {"name": "Current_Ratio", "display": "流动比率", "params": ["min"]},
        ],
        "sentiment": [
            {"name": "News_Sentiment", "display": "新闻情绪", "params": []},
            {"name": "Social_Sentiment", "display": "社交媒体情绪", "params": []},
        ],
        "flow": [
            {"name": "Money_Flow", "display": "资金流向", "params": []},
            {"name": "Northbound_Flow", "display": "北向资金", "params": []},
        ],
        "institutional": [
            {"name": "KIA_Holding", "display": "科威特投资局持仓", "params": []},
            {"name": "GWD_Holding", "display": "葛卫东持仓", "params": []},
            {"name": "SSF_Holding", "display": "社保基金持仓", "params": []},
            {"name": "QFII_Holding", "display": "QFII持仓", "params": []},
            {"name": "Northbound_Holding", "display": "北向资金持仓", "params": []},
        ],
    }
    
    return {"success": True, "data": indicators}


@router.get("/stats")
async def get_strategy_stats():
    """获取策略统计信息"""
    preset_count = len(PRESET_STRATEGIES)
    custom_count = len(custom_strategies)

    category_stats = {}
    for s in PRESET_STRATEGIES + list(custom_strategies.values()):
        cat = s.get("category", "other")
        category_stats[cat] = category_stats.get(cat, 0) + 1

    return {
        "success": True,
        "data": {
            "total": preset_count + custom_count,
            "preset": preset_count,
            "custom": custom_count,
            "by_category": category_stats
        }
    }


# ==================== 交易计划管理API ====================

@router.post("/plans")
async def create_trading_plan(request: CreateTradingPlanRequest):
    """创建交易计划"""
    try:
        service = get_auto_trade_service()

        plan_data = {
            "strategy_id": request.strategy_id,
            "strategy_name": request.strategy_name,
            "strategy_config": request.strategy_config,
            "stock_code": request.stock_code,
            "stock_name": request.stock_name,
            "initial_capital": request.allocated_capital,
            "max_position_ratio": request.max_position_ratio,
            "entry_mode": request.decision_mode,
            "exit_mode": request.decision_mode,
            "check_interval": request.check_interval,
            "stop_loss_pct": request.stop_loss_pct,
            "take_profit_pct": request.take_profit_pct,
        }

        plan = service.create_plan(plan_data)

        # 添加日志
        add_trade_log(
            log_type="system",
            source="auto",
            stock_code=request.stock_code,
            stock_name=request.stock_name or "",
            action="plan_created",
            message=f"创建交易计划: {request.strategy_name}",
            plan_id=plan.plan_id,
            strategy_name=request.strategy_name
        )

        # 如果需要自动启动
        if request.auto_start:
            service.start_plan(plan.plan_id)
            add_trade_log(
                log_type="system",
                source="auto",
                stock_code=request.stock_code,
                stock_name=request.stock_name or "",
                action="plan_started",
                message=f"交易计划已启动: {request.strategy_name}",
                plan_id=plan.plan_id,
                strategy_name=request.strategy_name
            )

        return {
            "success": True,
            "message": "交易计划创建成功",
            "data": service.get_plan(plan.plan_id)
        }

    except Exception as e:
        logger.error(f"创建交易计划失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plans")
async def get_all_trading_plans(
    status: Optional[str] = Query(None, description="计划状态: running/paused/stopped/pending")
):
    """获取所有交易计划"""
    try:
        service = get_auto_trade_service()
        plans = service.get_all_plans()

        # 按状态筛选
        if status:
            plans = [p for p in plans if p.get("status") == status]

        return {
            "success": True,
            "data": plans,
            "total": len(plans)
        }

    except Exception as e:
        logger.error(f"获取交易计划列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plans/{plan_id}")
async def get_trading_plan(plan_id: str):
    """获取交易计划详情"""
    try:
        service = get_auto_trade_service()
        plan = service.get_plan(plan_id)

        if not plan:
            raise HTTPException(status_code=404, detail="计划不存在")

        return {
            "success": True,
            "data": plan
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取交易计划详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/plans/{plan_id}")
async def update_trading_plan(plan_id: str, request: UpdateTradingPlanRequest):
    """更新交易计划"""
    try:
        service = get_auto_trade_service()

        if plan_id not in service.plans:
            raise HTTPException(status_code=404, detail="计划不存在")

        plan = service.plans[plan_id]

        # 更新字段
        if request.allocated_capital is not None:
            plan.initial_capital = request.allocated_capital
        if request.max_position_ratio is not None:
            plan.max_position_ratio = request.max_position_ratio
        if request.decision_mode is not None:
            plan.entry_mode = request.decision_mode
            plan.exit_mode = request.decision_mode
        if request.check_interval is not None:
            plan.check_interval = request.check_interval
        if request.stop_loss_pct is not None:
            plan.stop_loss_pct = request.stop_loss_pct
        if request.take_profit_pct is not None:
            plan.take_profit_pct = request.take_profit_pct

        return {
            "success": True,
            "message": "交易计划更新成功",
            "data": service.get_plan(plan_id)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新交易计划失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/plans/{plan_id}")
async def delete_trading_plan(plan_id: str):
    """删除交易计划"""
    try:
        service = get_auto_trade_service()

        plan = service.get_plan(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="计划不存在")

        # 添加日志
        add_trade_log(
            log_type="system",
            source="auto",
            stock_code=plan.get("stock_code", ""),
            stock_name=plan.get("stock_name", ""),
            action="plan_deleted",
            message=f"删除交易计划: {plan.get('strategy_name', '')}",
            plan_id=plan_id,
            strategy_name=plan.get("strategy_name")
        )

        if not service.delete_plan(plan_id):
            raise HTTPException(status_code=404, detail="计划不存在")

        return {
            "success": True,
            "message": "交易计划删除成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除交易计划失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plans/{plan_id}/start")
async def start_trading_plan(plan_id: str):
    """启动交易计划"""
    try:
        service = get_auto_trade_service()

        plan = service.get_plan(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="计划不存在")

        if not service.start_plan(plan_id):
            raise HTTPException(status_code=400, detail="启动失败")

        # 添加日志
        add_trade_log(
            log_type="system",
            source="auto",
            stock_code=plan.get("stock_code", ""),
            stock_name=plan.get("stock_name", ""),
            action="plan_started",
            message=f"启动交易计划: {plan.get('strategy_name', '')}",
            plan_id=plan_id,
            strategy_name=plan.get("strategy_name")
        )

        # 广播状态更新
        await ws_manager.send_plan_update(service.get_plan(plan_id))

        return {
            "success": True,
            "message": "交易计划已启动",
            "data": service.get_plan(plan_id)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动交易计划失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plans/{plan_id}/pause")
async def pause_trading_plan(plan_id: str):
    """暂停交易计划"""
    try:
        service = get_auto_trade_service()

        plan = service.get_plan(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="计划不存在")

        if not service.pause_plan(plan_id):
            raise HTTPException(status_code=400, detail="暂停失败")

        # 添加日志
        add_trade_log(
            log_type="system",
            source="auto",
            stock_code=plan.get("stock_code", ""),
            stock_name=plan.get("stock_name", ""),
            action="plan_paused",
            message=f"暂停交易计划: {plan.get('strategy_name', '')}",
            plan_id=plan_id,
            strategy_name=plan.get("strategy_name")
        )

        # 广播状态更新
        await ws_manager.send_plan_update(service.get_plan(plan_id))

        return {
            "success": True,
            "message": "交易计划已暂停",
            "data": service.get_plan(plan_id)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"暂停交易计划失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plans/{plan_id}/stop")
async def stop_trading_plan(plan_id: str):
    """停止交易计划"""
    try:
        service = get_auto_trade_service()

        plan = service.get_plan(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="计划不存在")

        if not service.stop_plan(plan_id):
            raise HTTPException(status_code=400, detail="停止失败")

        # 添加日志
        add_trade_log(
            log_type="system",
            source="auto",
            stock_code=plan.get("stock_code", ""),
            stock_name=plan.get("stock_name", ""),
            action="plan_stopped",
            message=f"停止交易计划: {plan.get('strategy_name', '')}",
            plan_id=plan_id,
            strategy_name=plan.get("strategy_name")
        )

        # 广播状态更新
        await ws_manager.send_plan_update(service.get_plan(plan_id))

        return {
            "success": True,
            "message": "交易计划已停止",
            "data": service.get_plan(plan_id)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"停止交易计划失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plans/{plan_id}/signals")
async def get_plan_signals(
    plan_id: str,
    limit: int = Query(50, ge=1, le=200)
):
    """获取计划的信号历史"""
    try:
        # 从交易日志中筛选该计划的信号
        plan_signals = [
            log for log in trade_logs
            if log.get("plan_id") == plan_id and log.get("log_type") == "signal"
        ][:limit]

        return {
            "success": True,
            "data": plan_signals,
            "total": len(plan_signals)
        }

    except Exception as e:
        logger.error(f"获取计划信号历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 交易日志API ====================

@router.get("/logs")
async def get_trade_logs(
    log_type: Optional[str] = Query(None, description="日志类型: signal/order/execution/risk/system"),
    source: Optional[str] = Query(None, description="来源: manual/auto"),
    stock_code: Optional[str] = Query(None, description="股票代码"),
    plan_id: Optional[str] = Query(None, description="计划ID"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """获取交易日志"""
    try:
        filtered_logs = trade_logs

        if log_type:
            filtered_logs = [l for l in filtered_logs if l.get("log_type") == log_type]
        if source:
            filtered_logs = [l for l in filtered_logs if l.get("source") == source]
        if stock_code:
            filtered_logs = [l for l in filtered_logs if l.get("stock_code") == stock_code]
        if plan_id:
            filtered_logs = [l for l in filtered_logs if l.get("plan_id") == plan_id]

        total = len(filtered_logs)
        paginated_logs = filtered_logs[offset:offset + limit]

        return {
            "success": True,
            "data": paginated_logs,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logger.error(f"获取交易日志失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 交易时间API ====================

@router.get("/trading-time")
async def get_trading_time_status():
    """获取交易时间状态"""
    is_trading = TradingTimeChecker.is_trading_time()
    next_trading = TradingTimeChecker.get_next_trading_time()

    return {
        "success": True,
        "data": {
            "is_trading_time": is_trading,
            "next_trading_time": next_trading.isoformat(),
            "current_time": datetime.now().isoformat(),
            "trading_hours": {
                "morning": "09:30 - 11:30",
                "afternoon": "13:00 - 15:00"
            }
        }
    }


# ==================== 监控服务API ====================

@router.get("/monitor/status")
async def get_monitor_status():
    """获取监控服务状态"""
    try:
        service = get_auto_trade_service()

        running_plans = [p for p in service.plans.values() if p.is_running]

        return {
            "success": True,
            "data": {
                "is_running": service._is_running,
                "total_plans": len(service.plans),
                "running_plans": len(running_plans),
                "plans": service.get_all_plans()
            }
        }

    except Exception as e:
        logger.error(f"获取监控状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitor/start")
async def start_monitor_service():
    """启动监控服务"""
    try:
        service = get_auto_trade_service()
        service.start_monitor()

        add_trade_log(
            log_type="system",
            source="auto",
            stock_code="",
            stock_name="",
            action="monitor_started",
            message="监控服务已启动"
        )

        return {
            "success": True,
            "message": "监控服务已启动"
        }

    except Exception as e:
        logger.error(f"启动监控服务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitor/stop")
async def stop_monitor_service():
    """停止监控服务"""
    try:
        service = get_auto_trade_service()
        service.stop_monitor()

        add_trade_log(
            log_type="system",
            source="auto",
            stock_code="",
            stock_name="",
            action="monitor_stopped",
            message="监控服务已停止"
        )

        return {
            "success": True,
            "message": "监控服务已停止"
        }

    except Exception as e:
        logger.error(f"停止监控服务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== WebSocket端点 ====================

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket实时推送"""
    await ws_manager.connect(websocket)

    service = get_auto_trade_service()

    # 设置回调函数
    def sync_status_callback(plan_data):
        asyncio.create_task(ws_manager.send_plan_update(plan_data))

    def sync_trade_callback(trade_data):
        # 添加交易日志
        add_trade_log(
            log_type="execution",
            source="auto",
            stock_code=trade_data.get("stock_code", ""),
            stock_name=trade_data.get("stock_name", ""),
            action=trade_data.get("action", "trade"),
            message=f"{trade_data.get('action', '')} {trade_data.get('quantity', 0)}股 @ {trade_data.get('price', 0)}",
            plan_id=trade_data.get("plan_id"),
            direction=trade_data.get("action"),
            quantity=trade_data.get("quantity"),
            price=trade_data.get("price")
        )
        asyncio.create_task(ws_manager.send_trade(trade_data))

    service.on_status_update_callback = sync_status_callback
    service.on_trade_callback = sync_trade_callback

    try:
        # 发送初始状态
        await websocket.send_json({
            "type": "connected",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "is_running": service._is_running,
                "plans": service.get_all_plans(),
                "recent_logs": trade_logs[:20]
            }
        })

        # 保持连接
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)

                if message.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    })
                elif message.get("type") == "get_status":
                    await websocket.send_json({
                        "type": "status",
                        "timestamp": datetime.now().isoformat(),
                        "data": {
                            "is_running": service._is_running,
                            "plans": service.get_all_plans()
                        }
                    })
                elif message.get("type") == "get_logs":
                    limit = message.get("limit", 50)
                    await websocket.send_json({
                        "type": "logs",
                        "timestamp": datetime.now().isoformat(),
                        "data": trade_logs[:limit]
                    })

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"[StrategyWS] 处理消息失败: {e}")

    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.disconnect(websocket)