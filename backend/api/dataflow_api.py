"""
数据流监控API
提供股票数据流监控、新闻舆情分析、风险预警等功能
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
import os

from backend.utils.logging_config import get_logger
from backend.utils.tool_logging import log_api_call
import math


def sanitize_float_values(obj):
    """
    递归清理数据中的非法float值（inf, -inf, nan）
    将它们转换为None，以便JSON序列化
    """
    if isinstance(obj, dict):
        return {k: sanitize_float_values(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_float_values(item) for item in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    else:
        return obj

# 导入风险监控模块
from backend.dataflows.risk import (
    check_suspend_status,
    is_st_stock,
    get_stock_realtime_quote,
    analyze_stock_risk
)

# 导入新闻和情绪分析模块
from backend.dataflows.news.multi_source_news_aggregator import get_news_aggregator
from backend.dataflows.news.sentiment_engine import get_sentiment_engine

# 导入综合数据服务
from backend.dataflows.comprehensive_stock_data import get_comprehensive_service

logger = get_logger("api.dataflow")
router = APIRouter(prefix="/api/dataflow", tags=["Data Flow"])


# ==================== 数据模型 ====================

class MonitorStockRequest(BaseModel):
    """添加监控股票请求"""
    code: str = Field(..., description="股票代码，如600519.SH")
    frequency: str = Field("1h", description="更新频率：5m/15m/30m/1h/1d")
    items: Dict[str, bool] = Field(
        default_factory=lambda: {
            "news": True,
            "risk": True,
            "sentiment": True,
            "suspend": False
        },
        description="监控项目"
    )


class RemoveMonitorRequest(BaseModel):
    """移除监控请求"""
    code: str = Field(..., description="股票代码")


class UpdateMonitorRequest(BaseModel):
    """立即更新请求"""
    code: str = Field(..., description="股票代码")


# ==================== 全局状态 ====================

# 导入持久化存储
from backend.dataflows.persistence.monitor_storage import get_monitor_storage

# 监控的股票列表（使用持久化存储）
def _load_monitored_stocks():
    """从持久化存储加载监控股票"""
    try:
        storage = get_monitor_storage()
        return storage.get_monitored_stocks()
    except Exception as e:
        logger.error(f"加载监控股票失败: {e}")
        return {}

def _save_monitored_stocks():
    """保存监控股票到持久化存储"""
    try:
        storage = get_monitor_storage()
        storage.save_monitor_config({'stocks': monitored_stocks})
    except Exception as e:
        logger.error(f"保存监控股票失败: {e}")

# 初始化时从文件加载
monitored_stocks = _load_monitored_stocks()

# 数据缓存 - 避免重复请求
data_cache = {}
data_sources_status = {
    "tushare": {
        "id": "tushare",
        "name": "Tushare",
        "type": "股票数据/新闻",
        "status": "offline",
        "todayCalls": 0,
        "lastUpdate": None,
        "error": None
    },
    "akshare": {
        "id": "akshare",
        "name": "AKShare",
        "type": "股票数据/资讯",
        "status": "offline",
        "todayCalls": 0,
        "lastUpdate": None,
        "error": None
    },
    "eastmoney": {
        "id": "eastmoney",
        "name": "东方财富",
        "type": "新闻/资讯",
        "status": "offline",
        "todayCalls": 0,
        "lastUpdate": None,
        "error": None
    },
    "juhe": {
        "id": "juhe",
        "name": "聚合数据",
        "type": "新闻/舆情",
        "status": "offline",
        "todayCalls": 0,
        "lastUpdate": None,
        "error": None
    }
}

# 新闻列表
news_list = []


# ==================== API接口 ====================

@router.get("/daily-stats")
@log_api_call("获取每日统计数据")
async def get_daily_stats():
    """
    获取每日统计数据
    包括：监控股票数、今日新闻数、风险预警数、分析任务数
    """
    try:
        # 统计监控股票数
        monitored_count = len(monitored_stocks)

        # 统计今日新闻数
        today = datetime.now().date()
        today_news_count = 0
        for news in news_list:
            try:
                news_time = news.get('publishTime') or news.get('pub_time', '')
                if news_time:
                    news_date = datetime.fromisoformat(news_time.replace('Z', '+00:00')).date()
                    if news_date == today:
                        today_news_count += 1
            except:
                pass

        # 统计风险预警数（高风险股票数）
        risk_alert_count = sum(
            1 for stock in monitored_stocks.values()
            if stock.get('riskLevel') in ['high', 'medium']
        )

        # 统计分析任务数（待处理任务）
        analysis_task_count = sum(
            stock.get('pendingTasks', 0)
            for stock in monitored_stocks.values()
        )

        # API调用统计
        api_calls = {}
        for source_id, source_data in data_sources_status.items():
            api_calls[source_id] = source_data.get('todayCalls', 0)

        return {
            "success": True,
            "stats": {
                "monitoredStocks": monitored_count,
                "todayNews": today_news_count or len(news_list),  # 如果今日新闻为0，返回总新闻数
                "riskAlerts": risk_alert_count,
                "analysisTasks": analysis_task_count,
                "apiCalls": api_calls
            }
        }

    except Exception as e:
        logger.error(f"获取每日统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/comprehensive/{ts_code}/from-db")
@log_api_call("从数据库获取股票综合数据")
async def get_stock_comprehensive_from_db(ts_code: str):
    """
    从数据库/缓存获取股票的综合数据（不触发新的API请求）
    优先从缓存获取，如果没有则返回空数据

    Args:
        ts_code: 股票代码
    """
    try:
        logger.info(f"📊 从数据库获取 {ts_code} 的综合数据...")

        # 检查缓存
        cache_key = f"comprehensive_{ts_code}"

        if cache_key in data_cache:
            cached_data = data_cache[cache_key]
            logger.info(f"✅ 从缓存获取数据成功")
            # 清理非法float值（inf, -inf, nan）
            sanitized_data = sanitize_float_values(cached_data.get('data', {}))
            return {
                "success": True,
                "has_data": True,
                "data": sanitized_data,
                "loaded_at": cached_data.get('cached_at'),
                "from_database": True
            }

        # 检查监控股票中是否有数据
        if ts_code in monitored_stocks:
            stock_data = monitored_stocks[ts_code]
            # 构建综合数据
            comprehensive = {
                "ts_code": ts_code,
                "name": stock_data.get("name", ts_code.split('.')[0]),
                "sentimentScore": stock_data.get("sentimentScore", 50),
                "riskLevel": stock_data.get("riskLevel", "low"),
                "riskScore": stock_data.get("riskScore", 0),
                "news": [],
                "risk": {
                    "risk_level": stock_data.get("riskLevel", "low"),
                    "risk_score": stock_data.get("riskScore", 0),
                    "risk_factors": stock_data.get("riskFactors", {}),
                    "warnings": stock_data.get("warnings", [])
                },
                "overall_score": stock_data.get("sentimentScore", 50),
                "sentiment_summary": stock_data.get("sentimentDetail", {})
            }

            logger.info(f"✅ 从监控数据获取成功")
            return {
                "success": True,
                "has_data": True,
                "data": comprehensive,
                "loaded_at": stock_data.get("lastUpdate"),
                "from_database": False
            }

        # 没有数据
        logger.info(f"ℹ️ 没有找到 {ts_code} 的缓存数据")
        return {
            "success": True,
            "has_data": False,
            "data": None,
            "message": "暂无数据，请点击刷新按钮获取"
        }

    except Exception as e:
        logger.error(f"从数据库获取综合数据失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/cached/{ts_code}")
@log_api_call("获取股票缓存数据")
async def get_stock_cached(ts_code: str):
    """
    获取股票的缓存数据（用于前端快速加载）

    Args:
        ts_code: 股票代码
    """
    try:
        cache_key = f"comprehensive_{ts_code}"

        if cache_key in data_cache:
            cached_data = data_cache[cache_key]
            return {
                "success": True,
                "has_data": True,
                "comprehensive": cached_data.get('data', {}),
                "news": cached_data.get('data', {}).get('news', []),
                "cached_at": cached_data.get('cached_at')
            }

        return {
            "success": True,
            "has_data": False,
            "message": "无缓存数据"
        }

    except Exception as e:
        logger.error(f"获取缓存数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitored-stocks")
@log_api_call("获取监控股票列表")
async def get_monitored_stocks():
    """
    获取当前监控的股票列表
    """
    try:
        stocks = []
        for code, data in monitored_stocks.items():
            stocks.append({
                "code": code,
                "name": data.get("name", "未知"),
                "sentimentScore": data.get("sentimentScore", 50),
                "riskLevel": data.get("riskLevel", "low"),
                "latestNews": data.get("latestNews", ""),
                "updateFrequency": data.get("frequency", "1h"),
                "lastUpdate": data.get("lastUpdate"),
                "pendingTasks": data.get("pendingTasks", 0)
            })
        
        return {
            "success": True,
            "stocks": stocks
        }
        
    except Exception as e:
        logger.error(f"获取监控股票失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sources/status")
@log_api_call("获取数据源状态")
async def get_data_sources_status():
    """
    获取所有数据源的状态（自动检测）
    """
    try:
        # 自动检测数据源状态
        await _check_all_data_sources()

        sources = list(data_sources_status.values())
        return {
            "success": True,
            "sources": sources
        }

    except Exception as e:
        logger.error(f"获取数据源状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _check_all_data_sources():
    """检测所有数据源状态"""
    try:
        # 检测AKShare
        try:
            import akshare as ak
            # 尝试获取一个简单的数据
            df = ak.stock_zh_a_spot_em()
            if df is not None and not df.empty:
                data_sources_status["akshare"]["status"] = "online"
                data_sources_status["akshare"]["lastUpdate"] = datetime.now().isoformat()
                data_sources_status["akshare"]["error"] = None
            else:
                data_sources_status["akshare"]["status"] = "error"
                data_sources_status["akshare"]["error"] = "无法获取数据"
        except Exception as e:
            data_sources_status["akshare"]["status"] = "error"
            data_sources_status["akshare"]["error"] = str(e)

        # 检测Tushare
        try:
            import tushare as ts
            # 检查是否有token
            token = os.getenv('TUSHARE_TOKEN')
            if token:
                ts.set_token(token)
                df = ts.daily(ts_code='000001.SZ', start_date='20240101', end_date='20240102')
                if df is not None and not df.empty:
                    data_sources_status["tushare"]["status"] = "online"
                    data_sources_status["tushare"]["lastUpdate"] = datetime.now().isoformat()
                    data_sources_status["tushare"]["error"] = None
                else:
                    data_sources_status["tushare"]["status"] = "error"
                    data_sources_status["tushare"]["error"] = "无法获取数据"
            else:
                data_sources_status["tushare"]["status"] = "offline"
                data_sources_status["tushare"]["error"] = "未配置TUSHARE_TOKEN"
        except Exception as e:
            data_sources_status["tushare"]["status"] = "error"
            data_sources_status["tushare"]["error"] = str(e)

        # 检测其他数据源
        for source in ["eastmoney", "juhe"]:
            if data_sources_status[source]["status"] == "offline":
                try:
                    # 简单的网络测试
                    import requests
                    if source == "eastmoney":
                        response = requests.get("https://push2.eastmoney.com/api/qt/stock/get", timeout=5)
                    else:  # juhe
                        response = requests.get("https://apis.juhe.cn/1.0/api/v1/stock/news", timeout=5)

                    if response.status_code == 200:
                        data_sources_status[source]["status"] = "online"
                        data_sources_status[source]["lastUpdate"] = datetime.now().isoformat()
                        data_sources_status[source]["error"] = None
                except Exception as e:
                    data_sources_status[source]["status"] = "error"
                    data_sources_status[source]["error"] = str(e)

    except Exception as e:
        logger.error(f"检测数据源失败: {e}")


@router.post("/sources/check")
@log_api_call("检测数据源连接")
async def check_data_sources():
    """
    检测所有数据源的连接状态
    """
    try:
        # TODO: 实现真实的数据源连接检测
        # 这里先用模拟数据
        
        # Tushare检测
        try:
            import tushare as ts
            data_sources_status["tushare"]["status"] = "online"
            data_sources_status["tushare"]["lastUpdate"] = datetime.now().isoformat()
            data_sources_status["tushare"]["error"] = None
        except Exception as e:
            data_sources_status["tushare"]["status"] = "error"
            data_sources_status["tushare"]["error"] = str(e)
        
        # AKShare检测
        try:
            import akshare as ak
            data_sources_status["akshare"]["status"] = "online"
            data_sources_status["akshare"]["lastUpdate"] = datetime.now().isoformat()
            data_sources_status["akshare"]["error"] = None
        except Exception as e:
            data_sources_status["akshare"]["status"] = "error"
            data_sources_status["akshare"]["error"] = str(e)
        
        # 其他数据源设置为在线（简化）
        for source_id in ["eastmoney", "juhe"]:
            data_sources_status[source_id]["status"] = "online"
            data_sources_status[source_id]["lastUpdate"] = datetime.now().isoformat()
        
        return {
            "success": True,
            "message": "数据源检测完成"
        }
        
    except Exception as e:
        logger.error(f"检测数据源失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/news")
@log_api_call("获取新闻列表")
async def get_news(source: Optional[str] = None, limit: int = 50):
    """
    获取新闻列表
    
    Args:
        source: 数据源筛选（可选）
        limit: 返回数量限制
    """
    try:
        filtered_news = news_list
        
        if source and source != "all":
            filtered_news = [n for n in news_list if n.get("source") == source]
        
        filtered_news = filtered_news[:limit]
        
        return {
            "success": True,
            "news": filtered_news,
            "total": len(filtered_news)
        }
        
    except Exception as e:
        logger.error(f"获取新闻失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/news/{ts_code}")
@log_api_call("获取股票新闻")
async def get_stock_news(ts_code: str, limit: int = 20):
    """
    获取指定股票的新闻
    """
    try:
        logger.info(f"获取{ts_code}的新闻...")
        aggregator = get_news_aggregator()
        
        # 修复：使用正确的参数名 limit_per_source
        result = aggregator.aggregate_news(
            ts_code=ts_code,
            limit_per_source=limit,  # 修复参数名
            include_tushare=False,  # Tushare需要5000积分，默认不开启
            include_akshare=True,
            include_market_news=False
        )
        
        # 修复：使用正确的字段名 merged_news
        news_list = result.get('merged_news', [])
        
        logger.info(f"✅ 返回{len(news_list)}条新闻")
        
        return {
            "success": True,
            "news": news_list,
            "total": result.get('total_count', 0),
            "sources": result.get('sources', {})
        }
        
    except Exception as e:
        logger.error(f"获取股票新闻失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/sentiment/{ts_code}")
@log_api_call("获取股票情绪分析")
async def get_stock_sentiment(ts_code: str, limit: int = 20):
    """
    获取指定股票的情绪分析
    """
    try:
        logger.info(f"获取{ts_code}的情绪分析...")
        
        # 先获取新闻
        aggregator = get_news_aggregator()
        news_result = aggregator.aggregate_news(
            ts_code=ts_code,
            limit_per_source=limit,  # 修复参数名
            include_tushare=False,
            include_akshare=True,
            include_market_news=False
        )
        
        news_list = news_result.get('merged_news', [])  # 修复字段名
        
        # 情绪分析
        engine = get_sentiment_engine()
        sentiment_result = engine.analyze_news_list(news_list)
        
        return {
            "success": True,
            **sentiment_result
        }
        
    except Exception as e:
        logger.error(f"情绪分析失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/risk/{ts_code}")
@log_api_call("获取股票风险分析")
async def get_stock_risk(ts_code: str):
    """
    获取指定股票的风险分析
    """
    try:
        logger.info(f"获取{ts_code}的风险分析...")
        
        # 调用风险分析函数
        risk_result = analyze_stock_risk(ts_code)
        
        return {
            "success": True,
            **risk_result
        }
        
    except Exception as e:
        logger.error(f"风险分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/comprehensive/{ts_code}")
@log_api_call("获取股票综合数据")
async def get_stock_comprehensive(ts_code: str, force_update: bool = False):
    """
    获取股票的所有综合数据
    包括：实时行情、停复牌、ST状态、财务数据、审计意见、
          业绩预告、分红送股、限售解禁、股权质押、
          股东增减持、龙虎榜、新闻等

    Args:
        ts_code: 股票代码
        force_update: 是否强制更新（忽略缓存）
    """
    try:
        logger.info(f"📊 开始获取 {ts_code} 的综合数据...")

        # 检查缓存
        cache_key = f"comprehensive_{ts_code}"
        current_time = datetime.now()

        # 如果缓存存在且不超过5分钟，直接返回
        if not force_update and cache_key in data_cache:
            cached_data = data_cache[cache_key]
            cache_time = datetime.fromisoformat(cached_data.get('cached_at', '1970-01-01'))
            if (current_time - cache_time).total_seconds() < 300:  # 5分钟缓存
                logger.info(f"📦 使用缓存数据 ({(current_time - cache_time).total_seconds():.1f}s前)")
                # 清理非法float值（inf, -inf, nan）
                sanitized_data = sanitize_float_values(cached_data['data'])
                return {
                    "success": True,
                    "cached": True,
                    **sanitized_data
                }

        # 获取新数据
        logger.info(f"🔄 获取新数据...")
        service = get_comprehensive_service()
        result = service.get_all_stock_data(ts_code)

        # 清理非法float值（inf, -inf, nan）
        result = sanitize_float_values(result)

        # 保存到缓存
        data_cache[cache_key] = {
            'cached_at': current_time.isoformat(),
            'data': result
        }

        return {
            "success": True,
            "cached": False,
            **result
        }

    except Exception as e:
        logger.error(f"综合数据获取失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


from fastapi.responses import StreamingResponse
import json

@router.get("/stock/comprehensive/{ts_code}/stream")
async def get_stock_comprehensive_stream(ts_code: str):
    """
    流式获取股票综合数据（SSE）
    前端可以边获取边渲染，提升用户体验
    """
    async def generate():
        try:
            # 发送开始信号
            yield f"data: {json.dumps({'type': 'start', 'ts_code': ts_code})}\n\n"

            # 获取综合数据服务
            service = get_comprehensive_service()

            # 定义数据分类
            categories = {
                'basic': {'name': '基础信息', 'fields': ['realtime', 'st_status', 'suspend']},
                'financial': {'name': '财务数据', 'fields': ['financial', 'forecast', 'dividend', 'audit']},
                'risk': {'name': '风险数据', 'fields': ['pledge', 'restricted', 'holder_trade']},
                'market': {'name': '市场数据', 'fields': ['dragon_tiger', 'block_trade', 'margin']},
                'news': {'name': '新闻舆情', 'fields': ['news_sina', 'announcements', 'news']},
                'company': {'name': '公司信息', 'fields': ['company_info', 'managers', 'main_business']},
            }

            # 获取完整数据
            logger.info(f"📊 开始流式获取 {ts_code} 的综合数据...")
            result = service.get_all_stock_data(ts_code)

            # 清理非法float值（inf, -inf, nan）
            result = sanitize_float_values(result)

            # 按分类发送数据
            success_count = 0
            total_count = 0

            for category_key, category_info in categories.items():
                category_data = {}
                category_success = 0
                category_total = 0

                for field in category_info['fields']:
                    if field in result:
                        category_data[field] = result[field]
                        category_total += 1
                        if isinstance(result[field], dict) and result[field].get('status') in ['success', 'has_suspend', 'normal']:
                            category_success += 1

                total_count += category_total
                success_count += category_success

                # 发送分类数据（数据已经被sanitize过）
                yield f"data: {json.dumps({'type': 'category', 'category': category_key, 'data': {'name': category_info['name'], 'data': category_data, 'success_count': category_success, 'total_count': category_total}}, ensure_ascii=False)}\n\n"

                # 短暂延迟，让前端有时间处理
                await asyncio.sleep(0.1)

            # 保存到缓存（已清理的数据）
            cache_key = f"comprehensive_{ts_code}"
            data_cache[cache_key] = {
                'cached_at': datetime.now().isoformat(),
                'data': result
            }

            # 发送完成信号
            yield f"data: {json.dumps({'type': 'complete', 'success_count': success_count, 'total_count': total_count, 'success_rate': f'{success_count/total_count*100:.1f}%' if total_count > 0 else '0%', 'total_time': 0}, ensure_ascii=False)}\n\n"

        except Exception as e:
            logger.error(f"流式获取数据失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )


@router.post("/monitor/add")
@log_api_call("添加监控股票")
async def add_monitor(request: MonitorStockRequest, background_tasks: BackgroundTasks):
    """
    添加股票监控
    """
    try:
        code = request.code

        # 检查是否已存在
        if code in monitored_stocks:
            raise HTTPException(status_code=400, detail="该股票已在监控列表中")

        # 获取股票名称（使用数据源管理器获取真实名称）
        stock_name = code.split('.')[0]  # 默认使用代码
        try:
            from backend.dataflows.data_source_manager import get_data_source_manager
            manager = get_data_source_manager()
            stock_info = manager.get_stock_info(code)
            if stock_info and stock_info.get('name'):
                stock_name = stock_info['name']
                logger.info(f"✅ 获取股票名称成功: {code} -> {stock_name}")
        except Exception as e:
            logger.warning(f"⚠️ 获取股票名称失败，使用代码作为名称: {e}")

        # 添加到监控列表
        monitored_stocks[code] = {
            "name": stock_name,
            "code": code,
            "frequency": request.frequency,
            "items": request.items,
            "sentimentScore": 50,
            "riskLevel": "low",
            "latestNews": "",
            "lastUpdate": datetime.now().isoformat(),
            "pendingTasks": 0
        }

        # 保存到持久化存储
        _save_monitored_stocks()

        # 添加后台任务：立即执行一次数据更新
        background_tasks.add_task(update_stock_data, code)

        logger.info(f"添加监控股票: {code} ({stock_name})")

        return {
            "success": True,
            "message": f"已添加监控: {stock_name}({code})",
            "code": code,
            "name": stock_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加监控失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitor/remove")
@log_api_call("移除监控股票")
async def remove_monitor(request: RemoveMonitorRequest):
    """
    移除股票监控
    """
    try:
        code = request.code
        
        if code not in monitored_stocks:
            raise HTTPException(status_code=404, detail="该股票不在监控列表中")

        del monitored_stocks[code]

        # 保存到持久化存储
        _save_monitored_stocks()

        logger.info(f"移除监控股票: {code}")
        
        return {
            "success": True,
            "message": f"已移除监控: {code}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"移除监控失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitor/update")
@log_api_call("立即更新股票数据")
async def update_monitor(request: UpdateMonitorRequest, background_tasks: BackgroundTasks):
    """
    立即更新指定股票的数据
    """
    try:
        code = request.code
        
        if code not in monitored_stocks:
            raise HTTPException(status_code=404, detail="该股票不在监控列表中")
        
        # 添加后台任务
        background_tasks.add_task(update_stock_data, code)
        
        return {
            "success": True,
            "message": f"更新任务已提交: {code}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/realtime/{ts_code}")
@log_api_call("获取股票实时数据")
async def get_stock_realtime(ts_code: str):
    """
    获取股票实时数据
    """
    try:
        realtime_data = get_stock_realtime_quote(ts_code)

        if realtime_data:
            return {
                "success": True,
                "data": realtime_data
            }
        else:
            return {
                "success": False,
                "error": "未能获取实时数据"
            }

    except Exception as e:
        logger.error(f"获取实时数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/suspend/{ts_code}")
@log_api_call("检查股票停复牌状态")
async def get_stock_suspend(ts_code: str):
    """
    检查股票停复牌状态
    """
    try:
        suspend_status = check_suspend_status(ts_code)

        return {
            "success": True,
            "data": suspend_status
        }

    except Exception as e:
        logger.error(f"检查停复牌失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 后台任务 ====================

async def update_stock_data(code: str):
    """
    更新股票数据（后台任务）
    
    包括：
    1. 获取最新新闻
    2. 进行情绪分析
    3. 进行风险评估
    4. 更新监控状态
    """
    try:
        logger.info(f"开始更新股票数据: {code}")
        
        if code not in monitored_stocks:
            return
        
        stock_data = monitored_stocks[code]
        items = stock_data.get("items", {})
        
        # 1. 获取新闻（使用真实的多源新闻聚合器）
        news_list_local = []
        if items.get("news", False):
            try:
                logger.info(f"📰 获取{code}的新闻...")
                news_aggregator = get_news_aggregator()
                news_data = news_aggregator.aggregate_news(
                    code,
                    include_tushare=False,  # Tushare新闻需要5000积分
                    include_akshare=True,
                    limit_per_source=10
                )
                
                news_list_local = news_data.get('merged_news', [])
                stock_data["newsCount"] = news_data.get('total_count', 0)
                stock_data["latestNews"] = news_list_local[0]['title'] if news_list_local else ""
                
                # 关键修复：将新闻添加到全局news_list中
                global news_list
                for news_item in news_list_local:
                    # 添加相关股票信息
                    news_with_stock = {
                        'id': f"{code}_{news_item.get('pub_time', '')}",
                        'title': news_item.get('title', ''),
                        'summary': news_item.get('content', '')[:200] if news_item.get('content') else '',
                        'publishTime': news_item.get('pub_time', ''),
                        'source': news_item.get('source', ''),
                        'relatedStocks': [code],
                        'sentiment': 0  # 将在情绪分析后更新
                    }
                    # 检查是否已存在（避免重复）
                    if not any(n.get('id') == news_with_stock['id'] for n in news_list):
                        news_list.append(news_with_stock)
                
                # 保持最近100条新闻
                if len(news_list) > 100:
                    news_list = news_list[-100:]
                
                logger.info(f"✅ 获取新闻成功: {len(news_list_local)}条，全局新闻总数: {len(news_list)}")
                
            except Exception as e:
                logger.error(f"❌ 获取新闻失败: {e}")
                await asyncio.sleep(0.1)  # 保持异步
        
        # 2. 情绪分析（使用真实的情绪分析引擎）
        sentiment_score = 50  # 默认中性
        if items.get("sentiment", False) and news_list_local:
            try:
                logger.info(f"💭 分析{code}的情绪...")
                sentiment_engine = get_sentiment_engine()
                sentiment_result = sentiment_engine.analyze_news_list(news_list_local)
                
                sentiment_score = sentiment_result.get('overall_score', 50)
                stock_data["sentimentScore"] = sentiment_score
                stock_data["sentimentDetail"] = {
                    'overall': sentiment_result.get('overall_sentiment', 'neutral'),
                    'positive': sentiment_result.get('positive_count', 0),
                    'negative': sentiment_result.get('negative_count', 0),
                    'neutral': sentiment_result.get('neutral_count', 0)
                }
                
                # 更新全局news_list中的情绪分数
                news_sentiments = sentiment_result.get('news_sentiments', [])
                for i, news_sentiment in enumerate(news_sentiments):
                    news_id = f"{code}_{news_list_local[i].get('pub_time', '')}"
                    for news_item in news_list:
                        if news_item.get('id') == news_id:
                            news_item['sentiment'] = news_sentiment.get('score', 50)
                            break
                
                logger.info(f"✅ 情绪分析完成: {sentiment_score:.2f}分 ({sentiment_result.get('overall_sentiment')})")
                logger.info(f"   正面:{sentiment_result.get('positive_count')} 中性:{sentiment_result.get('neutral_count')} 负面:{sentiment_result.get('negative_count')}")
                
            except Exception as e:
                logger.error(f"❌ 情绪分析失败: {e}")
                sentiment_score = 50
        elif items.get("sentiment", False):
            logger.warning(f"⚠️ 无新闻数据，跳过情绪分析")
            stock_data["sentimentScore"] = sentiment_score
        
        # 3. 风险分析（使用真实的风险分析引擎）
        if items.get("risk", False):
            try:
                logger.info(f"🔍 开始分析{code}的风险...")
                risk_result = analyze_stock_risk(
                    code, 
                    sentiment_score=sentiment_score
                )
                
                stock_data["riskLevel"] = risk_result.get("risk_level", "low")
                stock_data["riskScore"] = risk_result.get("risk_score", 0)
                stock_data["riskFactors"] = risk_result.get("risk_factors", {})
                stock_data["warnings"] = risk_result.get("warnings", [])
                
                logger.info(f"✅ {code} 风险分析完成: {stock_data['riskLevel']} (得分:{stock_data['riskScore']})")
                
            except Exception as e:
                logger.error(f"❌ 风险分析失败 {code}: {e}")
                stock_data["riskLevel"] = "unknown"
        
        # 4. 停复牌监控
        if items.get("suspend", False):
            try:
                logger.info(f"检查{code}的停复牌状态...")
                suspend_status = check_suspend_status(code)
                
                stock_data["isSuspended"] = suspend_status.get("is_suspended", False)
                stock_data["suspendInfo"] = suspend_status
                
                if suspend_status.get("is_suspended"):
                    logger.warning(f"⚠️ {code} 当前处于停牌状态")
                    
            except Exception as e:
                logger.error(f"❌ 停复牌检查失败 {code}: {e}")
        
        # 更新时间
        stock_data["lastUpdate"] = datetime.now().isoformat()
        
        logger.info(f"✅ 完成更新股票数据: {code}")
        
    except Exception as e:
        logger.error(f"❌ 更新股票数据失败 {code}: {e}")


# ==================== 定时任务（简化示例） ====================

async def scheduled_update_task():
    """
    定时更新任务（应该在后台运行）
    """
    while True:
        try:
            current_time = datetime.now()
            
            for code, data in monitored_stocks.items():
                frequency = data.get("frequency", "1h")
                last_update = data.get("lastUpdate")
                
                if not last_update:
                    continue
                
                last_time = datetime.fromisoformat(last_update)
                
                # 根据频率计算是否需要更新
                intervals = {
                    "5m": 5,
                    "15m": 15,
                    "30m": 30,
                    "1h": 60,
                    "1d": 1440
                }
                
                interval_minutes = intervals.get(frequency, 60)
                
                if (current_time - last_time).total_seconds() >= interval_minutes * 60:
                    await update_stock_data(code)
            
            # 每分钟检查一次
            await asyncio.sleep(60)
            
        except Exception as e:
            logger.error(f"定时任务出错: {e}")
            await asyncio.sleep(60)
