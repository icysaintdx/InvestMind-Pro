"""
策略中心API路由
提供策略的CRUD操作、分析执行、信号生成等接口
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timedelta
import json
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/strategy", tags=["策略中心"])


# ==================== 请求/响应模型 ====================

class StrategyCreate(BaseModel):
    """创建策略请求"""
    name: str
    description: str = ""
    category: str = "technical"
    icon: str = "📊"
    indicators: List[Dict[str, Any]] = []
    entry_conditions: List[Dict[str, Any]] = []
    exit_conditions: List[Dict[str, Any]] = []
    risk_params: Dict[str, Any] = {}
    is_active: bool = True


class StrategyUpdate(BaseModel):
    """更新策略请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    icon: Optional[str] = None
    indicators: Optional[List[Dict[str, Any]]] = None
    entry_conditions: Optional[List[Dict[str, Any]]] = None
    exit_conditions: Optional[List[Dict[str, Any]]] = None
    risk_params: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class StrategyParseRequest(BaseModel):
    """策略解析请求"""
    text: str
    model_id: Optional[str] = None


class AnalysisRequest(BaseModel):
    """分析请求"""
    strategy_id: int
    symbol: str
    model_id: Optional[str] = None
    include_news: bool = True
    include_chart: bool = False


class SignalResponse(BaseModel):
    """交易信号响应"""
    strategy_id: int
    symbol: str
    signal: str
    confidence: float
    trade_instruction: Dict[str, Any]
    analysis: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    timestamp: str


# ==================== 策略CRUD接口 ====================

@router.get("/list")
async def get_strategies(
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    page: int = 1,
    page_size: int = 20
):
    """获取策略列表"""
    try:
        from backend.services.strategy_service import get_strategy_service
        service = get_strategy_service()
        
        strategies = service.get_strategies(
            category=category,
            is_active=is_active,
            page=page,
            page_size=page_size
        )
        
        return {
            "success": True,
            "data": strategies,
            "total": len(strategies),
            "page": page,
            "page_size": page_size
        }
    except Exception as e:
        logger.error(f"获取策略列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def get_categories():
    """获取策略分类"""
    from backend.services.preset_strategies import STRATEGY_CATEGORIES
    return {
        "success": True,
        "data": STRATEGY_CATEGORIES
    }


@router.get("/{strategy_id}")
async def get_strategy(strategy_id: int):
    """获取单个策略详情"""
    try:
        from backend.services.strategy_service import get_strategy_service
        service = get_strategy_service()
        
        strategy = service.get_strategy_by_id(strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="策略不存在")
            
        return {
            "success": True,
            "data": strategy
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取策略详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create")
async def create_strategy(strategy: StrategyCreate):
    """创建新策略"""
    try:
        from backend.services.strategy_service import get_strategy_service
        service = get_strategy_service()
        
        new_strategy = service.create_strategy(strategy.model_dump())
        
        return {
            "success": True,
            "data": new_strategy,
            "message": "策略创建成功"
        }
    except Exception as e:
        logger.error(f"创建策略失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{strategy_id}")
async def update_strategy(strategy_id: int, strategy: StrategyUpdate):
    """更新策略"""
    try:
        from backend.services.strategy_service import get_strategy_service
        service = get_strategy_service()
        
        # 过滤掉None值
        update_data = {k: v for k, v in strategy.model_dump().items() if v is not None}
        
        updated_strategy = service.update_strategy(strategy_id, update_data)
        if not updated_strategy:
            raise HTTPException(status_code=404, detail="策略不存在")
            
        return {
            "success": True,
            "data": updated_strategy,
            "message": "策略更新成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新策略失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{strategy_id}")
async def delete_strategy(strategy_id: int):
    """删除策略"""
    try:
        from backend.services.strategy_service import get_strategy_service
        service = get_strategy_service()
        
        success = service.delete_strategy(strategy_id)
        if not success:
            raise HTTPException(status_code=404, detail="策略不存在")
            
        return {
            "success": True,
            "message": "策略删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除策略失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 策略解析接口 ====================

@router.post("/parse")
async def parse_strategy_text(request: StrategyParseRequest):
    """
    解析用户输入的策略文本，转换为标准格式
    用于将民间策略、看线方法等转换为系统可用的策略
    """
    try:
        from backend.services.llm_strategy_service import get_llm_strategy_service
        
        llm_service = get_llm_strategy_service()
        
        # 如果指定了模型ID，需要从模型管理获取配置
        if request.model_id:
            model_config = await get_model_config(request.model_id)
            llm_service.set_model_config(model_config)
        else:
            # 使用默认配置
            model_config = get_default_model_config()
            if model_config:
                llm_service.set_model_config(model_config)
        
        # 解析策略文本
        parsed_strategy = await llm_service.parse_strategy_text(request.text)
        
        return {
            "success": True,
            "data": parsed_strategy,
            "message": "策略解析成功"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"解析策略失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parse-and-save")
async def parse_and_save_strategy(request: StrategyParseRequest):
    """解析策略文本并保存到数据库"""
    try:
        from backend.services.llm_strategy_service import get_llm_strategy_service
        from backend.services.strategy_service import get_strategy_service
        
        llm_service = get_llm_strategy_service()
        strategy_service = get_strategy_service()
        
        # 如果指定了模型ID，需要从模型管理获取配置
        if request.model_id:
            model_config = await get_model_config(request.model_id)
            llm_service.set_model_config(model_config)
        else:
            # 使用默认配置
            model_config = get_default_model_config()
            if model_config:
                llm_service.set_model_config(model_config)
        
        # 解析策略文本
        parsed_strategy = await llm_service.parse_strategy_text(request.text)
        
        # 保存到数据库
        saved_strategy = strategy_service.create_strategy(parsed_strategy)
        
        return {
            "success": True,
            "data": saved_strategy,
            "message": "策略解析并保存成功"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"解析并保存策略失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 策略分析接口 ====================

@router.post("/analyze")
async def analyze_stock(request: AnalysisRequest):
    """
    使用策略分析股票，生成交易信号
    """
    try:
        from backend.services.llm_strategy_service import get_llm_strategy_service
        from backend.services.strategy_service import get_strategy_service
        
        llm_service = get_llm_strategy_service()
        strategy_service = get_strategy_service()
        
        # 获取策略
        strategy = strategy_service.get_strategy_by_id(request.strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="策略不存在")
        
        # 如果指定了模型ID，需要从模型管理获取配置
        if request.model_id:
            model_config = await get_model_config(request.model_id)
            llm_service.set_model_config(model_config)
        else:
            # 使用默认配置
            model_config = get_default_model_config()
            if model_config:
                llm_service.set_model_config(model_config)
        
        # 获取市场数据
        market_data = await get_market_data(request.symbol)
        market_data["strategy"] = strategy
        
        # 获取新闻数据（如果需要）
        news_data = None
        if request.include_news:
            news_data = await get_news_data(request.symbol)
        
        # 获取K线图截图（如果需要）
        chart_image = None
        if request.include_chart:
            chart_image = await capture_chart_image(request.symbol)
        
        # 执行分析
        signal = await llm_service.generate_trade_signal(
            strategy_id=request.strategy_id,
            symbol=request.symbol,
            market_data=market_data,
            news_data=news_data,
            chart_image=chart_image
        )
        
        # 保存信号到数据库
        strategy_service.save_trade_signal(signal)
        
        return {
            "success": True,
            "data": signal,
            "message": "分析完成"
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"策略分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-with-image")
async def analyze_with_image(
    strategy_id: int = Form(...),
    symbol: str = Form(...),
    model_id: Optional[str] = Form(None),
    image: UploadFile = File(...)
):
    """
    使用K线图截图进行分析
    支持用户上传K线图进行多模态分析
    """
    try:
        from backend.services.llm_strategy_service import get_llm_strategy_service
        from backend.services.strategy_service import get_strategy_service
        
        llm_service = get_llm_strategy_service()
        strategy_service = get_strategy_service()
        
        # 获取策略
        strategy = strategy_service.get_strategy_by_id(strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="策略不存在")
        
        # 如果指定了模型ID，需要从模型管理获取配置
        if model_id:
            model_config = await get_model_config(model_id)
            llm_service.set_model_config(model_config)
        else:
            # 使用默认配置
            model_config = get_default_model_config()
            if model_config:
                llm_service.set_model_config(model_config)
        
        # 读取上传的图片
        image_data = await image.read()
        
        # 获取市场数据
        market_data = await get_market_data(symbol)
        market_data["strategy"] = strategy
        
        # 执行分析
        signal = await llm_service.generate_trade_signal(
            strategy_id=strategy_id,
            symbol=symbol,
            market_data=market_data,
            chart_image=image_data
        )
        
        return {
            "success": True,
            "data": signal,
            "message": "图像分析完成"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"图像分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 信号历史接口 ====================

@router.get("/signals/{strategy_id}")
async def get_strategy_signals(
    strategy_id: int,
    symbol: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
):
    """获取策略的历史信号"""
    try:
        from backend.services.strategy_service import get_strategy_service
        service = get_strategy_service()
        
        signals = service.get_trade_signals(
            strategy_id=strategy_id,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size
        )
        
        return {
            "success": True,
            "data": signals,
            "total": len(signals),
            "page": page,
            "page_size": page_size
        }
    except Exception as e:
        logger.error(f"获取信号历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 预设策略接口 ====================

@router.get("/preset/list")
async def get_preset_strategies(category: Optional[str] = None):
    """获取预设策略列表"""
    from backend.services.preset_strategies import (
        get_preset_strategies,
        get_strategies_by_category
    )
    
    if category:
        strategies = get_strategies_by_category(category)
    else:
        strategies = get_preset_strategies()
    
    return {
        "success": True,
        "data": strategies,
        "total": len(strategies)
    }


@router.post("/preset/import/{name}")
async def import_preset_strategy(name: str):
    """导入预设策略到数据库"""
    try:
        from backend.services.preset_strategies import get_strategy_by_name
        from backend.services.strategy_service import get_strategy_service
        
        preset = get_strategy_by_name(name)
        if not preset:
            raise HTTPException(status_code=404, detail="预设策略不存在")
        
        service = get_strategy_service()
        saved_strategy = service.create_strategy(preset)
        
        return {
            "success": True,
            "data": saved_strategy,
            "message": f"预设策略 '{name}' 导入成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导入预设策略失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preset/import-all")
async def import_all_preset_strategies():
    """导入所有预设策略到数据库"""
    try:
        from backend.services.preset_strategies import get_preset_strategies
        from backend.services.strategy_service import get_strategy_service
        
        presets = get_preset_strategies()
        service = get_strategy_service()
        
        imported = []
        for preset in presets:
            try:
                saved = service.create_strategy(preset)
                imported.append(saved["name"])
            except Exception as e:
                logger.warning(f"导入策略 '{preset.get('name')}' 失败: {e}")
        
        return {
            "success": True,
            "data": imported,
            "message": f"成功导入 {len(imported)} 个预设策略"
        }
    except Exception as e:
        logger.error(f"批量导入预设策略失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 辅助函数 ====================

def get_default_model_config() -> Optional[Dict[str, Any]]:
    """从环境变量获取默认模型配置"""
    # 优先使用DeepSeek
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    if deepseek_key:
        return {
            "type": "deepseek",
            "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            "api_key": deepseek_key,
            "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        }
    
    # 其次使用OpenAI
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        return {
            "type": "openai",
            "model": os.getenv("OPENAI_MODEL", "gpt-4"),
            "api_key": openai_key,
            "base_url": os.getenv("OPENAI_BASE_URL")
        }
    
    # 使用DashScope（阿里云）
    dashscope_key = os.getenv("DASHSCOPE_API_KEY")
    if dashscope_key:
        return {
            "type": "dashscope",
            "model": os.getenv("DASHSCOPE_MODEL", "qwen-max"),
            "api_key": dashscope_key
        }
    
    logger.warning("未配置任何LLM API密钥，策略分析功能不可用")
    return None


async def get_model_config(model_id: str) -> Dict[str, Any]:
    """从模型管理模块获取模型配置"""
    # TODO: 实现从模型管理模块获取配置
    # 这里需要调用模型管理模块的API
    # 暂时返回默认配置
    config = get_default_model_config()
    if config:
        return config
    return {
        "type": "openai",
        "model": "gpt-4",
        "api_key": "",
        "base_url": ""
    }


async def get_market_data(symbol: str) -> Dict[str, Any]:
    """
    获取市场数据
    包括K线数据、技术指标、基本面数据等
    """
    logger.info(f"获取 {symbol} 的市场数据...")
    
    result = {
        "symbol": symbol,
        "name": "",
        "current_price": 0,
        "change_pct": 0,
        "kline_data": [],
        "indicators": {},
        "fundamentals": {}
    }
    
    # 清理股票代码
    clean_symbol = symbol.replace('.SH', '').replace('.SZ', '')
    
    # 1. 获取实时行情
    try:
        from backend.dataflows.akshare.stock_data import get_stock_data
        stock_data = get_stock_data()
        
        quote = stock_data.get_stock_quote(clean_symbol)
        if quote:
            result["name"] = quote.get("名称", "")
            result["current_price"] = float(quote.get("最新价", 0) or 0)
            result["change_pct"] = float(quote.get("涨跌幅", 0) or 0)
            logger.info(f"获取实时行情成功: {result['name']} 价格={result['current_price']}")
    except Exception as e:
        logger.warning(f"获取实时行情失败: {e}")
    
    # 2. 获取K线数据（最近60日）
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
            adjust="qfq"  # 前复权
        )
        
        if hist_data:
            result["kline_data"] = hist_data[-60:]  # 最近60条
            logger.info(f"获取K线数据成功: {len(result['kline_data'])}条")
    except Exception as e:
        logger.warning(f"获取K线数据失败: {e}")
    
    # 3. 计算技术指标
    try:
        if result["kline_data"]:
            indicators = calculate_technical_indicators(result["kline_data"])
            result["indicators"] = indicators
            logger.info(f"计算技术指标成功: {list(indicators.keys())}")
    except Exception as e:
        logger.warning(f"计算技术指标失败: {e}")
    
    # 4. 获取基本面数据
    try:
        from backend.dataflows.comprehensive_stock_data import get_comprehensive_service
        
        # 构建ts_code格式
        if clean_symbol.startswith('6'):
            ts_code = f"{clean_symbol}.SH"
        else:
            ts_code = f"{clean_symbol}.SZ"
        
        service = get_comprehensive_service()
        
        # 获取财务数据
        financial = service._get_financial_data(ts_code)
        if financial.get('status') == 'success':
            result["fundamentals"]["financial"] = financial
        
        # 获取公司信息
        company_info = service._get_company_info(ts_code)
        if company_info.get('status') == 'success':
            result["fundamentals"]["company_info"] = company_info.get('data', {})
        
        logger.info(f"获取基本面数据成功")
    except Exception as e:
        logger.warning(f"获取基本面数据失败: {e}")
    
    return result


def calculate_technical_indicators(kline_data: List[Dict]) -> Dict[str, Any]:
    """
    计算技术指标
    """
    import pandas as pd
    
    if not kline_data:
        return {}
    
    # 转换为DataFrame
    df = pd.DataFrame(kline_data)
    
    # 确保有必要的列
    # AKShare返回的列名可能是中文
    column_mapping = {
        '日期': 'date',
        '开盘': 'open',
        '收盘': 'close',
        '最高': 'high',
        '最低': 'low',
        '成交量': 'volume',
        '成交额': 'amount'
    }
    
    for cn, en in column_mapping.items():
        if cn in df.columns:
            df[en] = df[cn]
    
    # 确保数值类型
    for col in ['open', 'close', 'high', 'low', 'volume']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    indicators = {}
    
    try:
        # MA均线
        if 'close' in df.columns:
            df['MA5'] = df['close'].rolling(window=5).mean()
            df['MA10'] = df['close'].rolling(window=10).mean()
            df['MA20'] = df['close'].rolling(window=20).mean()
            df['MA60'] = df['close'].rolling(window=60).mean()
            
            indicators['MA'] = {
                'MA5': round(df['MA5'].iloc[-1], 2) if not pd.isna(df['MA5'].iloc[-1]) else None,
                'MA10': round(df['MA10'].iloc[-1], 2) if not pd.isna(df['MA10'].iloc[-1]) else None,
                'MA20': round(df['MA20'].iloc[-1], 2) if not pd.isna(df['MA20'].iloc[-1]) else None,
                'MA60': round(df['MA60'].iloc[-1], 2) if len(df) >= 60 and not pd.isna(df['MA60'].iloc[-1]) else None
            }
        
        # RSI
        if 'close' in df.columns and len(df) >= 14:
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            indicators['RSI'] = {
                'RSI14': round(rsi.iloc[-1], 2) if not pd.isna(rsi.iloc[-1]) else None
            }
        
        # MACD
        if 'close' in df.columns and len(df) >= 26:
            exp1 = df['close'].ewm(span=12, adjust=False).mean()
            exp2 = df['close'].ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, adjust=False).mean()
            hist = macd - signal
            
            indicators['MACD'] = {
                'MACD': round(macd.iloc[-1], 4) if not pd.isna(macd.iloc[-1]) else None,
                'Signal': round(signal.iloc[-1], 4) if not pd.isna(signal.iloc[-1]) else None,
                'Histogram': round(hist.iloc[-1], 4) if not pd.isna(hist.iloc[-1]) else None
            }
        
        # 布林带
        if 'close' in df.columns and len(df) >= 20:
            ma20 = df['close'].rolling(window=20).mean()
            std20 = df['close'].rolling(window=20).std()
            upper = ma20 + (std20 * 2)
            lower = ma20 - (std20 * 2)
            
            indicators['BOLL'] = {
                'Upper': round(upper.iloc[-1], 2) if not pd.isna(upper.iloc[-1]) else None,
                'Middle': round(ma20.iloc[-1], 2) if not pd.isna(ma20.iloc[-1]) else None,
                'Lower': round(lower.iloc[-1], 2) if not pd.isna(lower.iloc[-1]) else None
            }
        
        # KDJ
        if all(col in df.columns for col in ['high', 'low', 'close']) and len(df) >= 9:
            low_min = df['low'].rolling(window=9).min()
            high_max = df['high'].rolling(window=9).max()
            rsv = (df['close'] - low_min) / (high_max - low_min) * 100
            
            k = rsv.ewm(com=2, adjust=False).mean()
            d = k.ewm(com=2, adjust=False).mean()
            j = 3 * k - 2 * d
            
            indicators['KDJ'] = {
                'K': round(k.iloc[-1], 2) if not pd.isna(k.iloc[-1]) else None,
                'D': round(d.iloc[-1], 2) if not pd.isna(d.iloc[-1]) else None,
                'J': round(j.iloc[-1], 2) if not pd.isna(j.iloc[-1]) else None
            }
        
        # 成交量均线
        if 'volume' in df.columns:
            df['VOL_MA5'] = df['volume'].rolling(window=5).mean()
            df['VOL_MA10'] = df['volume'].rolling(window=10).mean()
            
            indicators['Volume'] = {
                'current': int(df['volume'].iloc[-1]) if not pd.isna(df['volume'].iloc[-1]) else None,
                'MA5': int(df['VOL_MA5'].iloc[-1]) if not pd.isna(df['VOL_MA5'].iloc[-1]) else None,
                'MA10': int(df['VOL_MA10'].iloc[-1]) if not pd.isna(df['VOL_MA10'].iloc[-1]) else None
            }
        
        # ATR (真实波幅)
        if all(col in df.columns for col in ['high', 'low', 'close']) and len(df) >= 14:
            high_low = df['high'] - df['low']
            high_close = abs(df['high'] - df['close'].shift())
            low_close = abs(df['low'] - df['close'].shift())
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = tr.rolling(window=14).mean()
            
            indicators['ATR'] = {
                'ATR14': round(atr.iloc[-1], 4) if not pd.isna(atr.iloc[-1]) else None
            }
    
    except Exception as e:
        logger.warning(f"计算技术指标时出错: {e}")
    
    return indicators


async def get_news_data(symbol: str) -> List[Dict[str, Any]]:
    """
    获取新闻数据
    """
    logger.info(f"获取 {symbol} 的新闻数据...")
    
    news_list = []
    
    # 清理股票代码
    clean_symbol = symbol.replace('.SH', '').replace('.SZ', '')
    
    try:
        from backend.dataflows.news.multi_source_news_aggregator import get_news_aggregator
        
        # 构建ts_code格式
        if clean_symbol.startswith('6'):
            ts_code = f"{clean_symbol}.SH"
        else:
            ts_code = f"{clean_symbol}.SZ"
        
        aggregator = get_news_aggregator()
        result = aggregator.aggregate_news(
            ts_code=ts_code,
            limit_per_source=10,
            include_tushare=False,
            include_akshare=True,
            include_market_news=True
        )
        
        news_list = result.get('merged_news', [])[:20]  # 最多20条
        logger.info(f"获取新闻数据成功: {len(news_list)}条")
        
    except Exception as e:
        logger.warning(f"获取新闻数据失败: {e}")
    
    return news_list


async def capture_chart_image(symbol: str) -> bytes:
    """
    截取K线图
    TODO: 实现K线图截图功能
    可以使用 mplfinance 或 pyecharts 生成图表，然后转换为图片
    """
    logger.info(f"截取 {symbol} 的K线图...")
    
    # 暂时返回空，后续可以实现
    # 可以使用以下方式实现：
    # 1. 使用 mplfinance 生成K线图
    # 2. 使用 pyecharts 生成图表
    # 3. 使用 selenium 截取网页K线图
    
    return b""