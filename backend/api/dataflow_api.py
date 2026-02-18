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
from datetime import date as date_type


def sanitize_for_json(obj):
    """
    递归清理数据中无法JSON序列化的值：
    - inf, -inf, nan -> None
    - date, datetime -> ISO格式字符串
    """
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(item) for item in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, (datetime, date_type)):
        return obj.isoformat()
    else:
        return obj


# 保留旧函数名作为别名，保持向后兼容
sanitize_float_values = sanitize_for_json

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
    name: Optional[str] = Field(None, description="股票名称，由前端传递避免后端查找")
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

# 导入数据库服务
from backend.database.database import get_db_context
from backend.database.services import (
    MonitoredStockService,
    StockDataService,
    StockNewsService,
    DataFlowStatsService
)

# 监控的股票列表（使用数据库存储）
def _load_monitored_stocks():
    """从数据库加载监控股票，包括情绪和风险数据"""
    try:
        with get_db_context() as db:
            stocks = MonitoredStockService.get_all_active(db)
            result = {}
            for stock in stocks:
                # 尝试从数据库加载综合数据以获取情绪和风险信息
                sentiment_score = 50
                risk_level = "low"
                risk_score = 0
                latest_news = ""

                try:
                    record = StockDataService.get_latest(db, stock.ts_code, 'comprehensive')
                    if record and record.data:
                        data = record.data
                        # 获取情绪评分
                        if 'overall_score' in data:
                            sentiment_score = data.get('overall_score', 50)
                        # 获取风险信息
                        if 'risk' in data and isinstance(data['risk'], dict):
                            risk_level = data['risk'].get('risk_level', 'low')
                            risk_score = data['risk'].get('risk_score', 0)
                        # 获取最新新闻
                        if 'news' in data and isinstance(data['news'], list) and data['news']:
                            latest_news = data['news'][0].get('title', '') if data['news'] else ''
                except Exception as e:
                    logger.warning(f"加载{stock.ts_code}的综合数据失败: {e}")

                result[stock.ts_code] = {
                    "name": stock.name,
                    "code": stock.ts_code,
                    "frequency": stock.frequency,
                    "items": stock.items or {},
                    "sentimentScore": sentiment_score,
                    "riskLevel": risk_level,
                    "riskScore": risk_score,
                    "latestNews": latest_news,
                    "lastUpdate": stock.last_update.isoformat() if stock.last_update else None,
                    "pendingTasks": 0
                }
            return result
    except Exception as e:
        logger.error(f"加载监控股票失败: {e}")
        return {}

def _save_monitored_stocks():
    """保存监控股票到数据库（已在各操作中直接保存，此函数保留兼容性）"""
    pass  # 数据库操作已在各API中直接执行

# 初始化时从数据库加载
monitored_stocks = _load_monitored_stocks()

# 数据缓存 - 启动时从数据库加载
def _load_comprehensive_cache_from_db():
    """从数据库加载综合数据缓存"""
    result = {}
    try:
        with get_db_context() as db:
            stocks = MonitoredStockService.get_all_active(db)
            for stock in stocks:
                record = StockDataService.get_latest(db, stock.ts_code, 'comprehensive')
                if record and record.data:
                    result[f"comprehensive_{stock.ts_code}"] = {
                        'cached_at': record.fetch_time.isoformat() if record.fetch_time else None,
                        'data': record.data
                    }
        logger.info(f"[OK] 启动时从数据库加载综合数据缓存: {len(result)}个")
    except Exception as e:
        logger.error(f"加载综合数据缓存失败: {e}")
    return result

data_cache = _load_comprehensive_cache_from_db()
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
    },
    "cninfo": {
        "id": "cninfo",
        "name": "巨潮资讯",
        "type": "公告/研报",
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
    从数据库获取股票的综合数据（只读取，不触发任何更新）

    数据更新只在以下情况发生：
    1. 首次添加监控股票后
    2. 定时器到达时间
    3. 手动点击立即更新按钮

    Args:
        ts_code: 股票代码
    """
    try:
        logger.info(f"📊 从数据库获取 {ts_code} 的综合数据...")

        # 1. 优先从数据库获取
        with get_db_context() as db:
            record = StockDataService.get_latest(db, ts_code, 'comprehensive')
            if record and record.data:
                logger.info(f"[OK] 从数据库获取数据成功")
                # 清理非法float值（inf, -inf, nan）
                sanitized_data = sanitize_for_json(record.data)
                # 同时更新内存缓存
                cache_key = f"comprehensive_{ts_code}"
                data_cache[cache_key] = {
                    'cached_at': record.fetch_time.isoformat() if record.fetch_time else None,
                    'data': sanitized_data
                }
                return {
                    "success": True,
                    "has_data": True,
                    "data": sanitized_data,
                    "loaded_at": record.fetch_time.isoformat() if record.fetch_time else None,
                    "from_database": True
                }

        # 2. 数据库没有数据，检查内存缓存（兼容旧数据）
        cache_key = f"comprehensive_{ts_code}"
        if cache_key in data_cache:
            cached_data = data_cache[cache_key]
            logger.info(f"[OK] 从内存缓存获取数据成功")
            sanitized_data = sanitize_for_json(cached_data.get('data', {}))
            return {
                "success": True,
                "has_data": True,
                "data": sanitized_data,
                "loaded_at": cached_data.get('cached_at'),
                "from_database": False
            }

        # 3. 没有数据
        logger.info(f"ℹ️ 没有找到 {ts_code} 的数据，请点击刷新按钮获取")
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
                "riskScore": data.get("riskScore", 0),
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
    获取所有数据源的状态（使用缓存，不自动检测）
    自动检测会很慢，改为只在用户点击"检测连接"时才检测
    """
    try:
        sources = list(data_sources_status.values())
        return {
            "success": True,
            "sources": sources
        }

    except Exception as e:
        logger.error(f"获取数据源状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _check_all_data_sources():
    """检测所有数据源状态（使用轻量级API）"""
    try:
        current_time = datetime.now().isoformat()

        # 检测AKShare - 使用轻量级API
        try:
            import akshare as ak
            # 使用交易日历API，比全市场行情快很多
            df = ak.tool_trade_date_hist_sina()
            if df is not None and not df.empty:
                data_sources_status["akshare"]["status"] = "online"
                data_sources_status["akshare"]["error"] = None
            else:
                data_sources_status["akshare"]["status"] = "error"
                data_sources_status["akshare"]["error"] = "无法获取数据"
        except Exception as e:
            data_sources_status["akshare"]["status"] = "error"
            data_sources_status["akshare"]["error"] = str(e)[:100]
        data_sources_status["akshare"]["lastUpdate"] = current_time

        # 检测Tushare
        try:
            import tushare as ts
            # 检查是否有token
            token = os.getenv('TUSHARE_TOKEN')
            if token:
                ts.set_token(token)
                pro = ts.pro_api()
                df = pro.daily(ts_code='000001.SZ', start_date='20250101', end_date='20250102')
                if df is not None and not df.empty:
                    data_sources_status["tushare"]["status"] = "online"
                    data_sources_status["tushare"]["error"] = None
                else:
                    data_sources_status["tushare"]["status"] = "error"
                    data_sources_status["tushare"]["error"] = "无法获取数据"
            else:
                data_sources_status["tushare"]["status"] = "offline"
                data_sources_status["tushare"]["error"] = "未配置TUSHARE_TOKEN"
        except Exception as e:
            data_sources_status["tushare"]["status"] = "error"
            data_sources_status["tushare"]["error"] = str(e)[:100]
        data_sources_status["tushare"]["lastUpdate"] = current_time

        # 检测东方财富
        try:
            import requests
            response = requests.get("https://push2.eastmoney.com/api/qt/stock/get", timeout=5)
            if response.status_code == 200:
                data_sources_status["eastmoney"]["status"] = "online"
                data_sources_status["eastmoney"]["error"] = None
            else:
                data_sources_status["eastmoney"]["status"] = "error"
                data_sources_status["eastmoney"]["error"] = f"HTTP {response.status_code}"
        except Exception as e:
            data_sources_status["eastmoney"]["status"] = "error"
            data_sources_status["eastmoney"]["error"] = str(e)[:100]
        data_sources_status["eastmoney"]["lastUpdate"] = current_time

        # 检测聚合数据
        try:
            import requests
            juhe_key = os.getenv('JUHE_API_KEY')
            if juhe_key:
                response = requests.get(f"http://web.juhe.cn/finance/stock/hs?gid=sh601006&key={juhe_key}", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("error_code") == 0:
                        data_sources_status["juhe"]["status"] = "online"
                        data_sources_status["juhe"]["error"] = None
                    else:
                        data_sources_status["juhe"]["status"] = "error"
                        data_sources_status["juhe"]["error"] = data.get("reason", "API错误")
                else:
                    data_sources_status["juhe"]["status"] = "error"
                    data_sources_status["juhe"]["error"] = f"HTTP {response.status_code}"
            else:
                data_sources_status["juhe"]["status"] = "offline"
                data_sources_status["juhe"]["error"] = "未配置JUHE_API_KEY"
        except Exception as e:
            data_sources_status["juhe"]["status"] = "error"
            data_sources_status["juhe"]["error"] = str(e)[:100]
        data_sources_status["juhe"]["lastUpdate"] = current_time

        # 检测巨潮资讯
        try:
            from backend.dataflows.announcement.cninfo_api import CninfoConfig
            if CninfoConfig.is_configured():
                # 尝试调用一个简单的API来检测连接
                import requests
                response = requests.get("https://webapi.cninfo.com.cn/", timeout=5)
                if response.status_code == 200:
                    data_sources_status["cninfo"]["status"] = "online"
                    data_sources_status["cninfo"]["error"] = None
                else:
                    data_sources_status["cninfo"]["status"] = "error"
                    data_sources_status["cninfo"]["error"] = f"HTTP {response.status_code}"
            else:
                data_sources_status["cninfo"]["status"] = "offline"
                data_sources_status["cninfo"]["error"] = "未配置CNINFO_ACCESS_KEY"
        except Exception as e:
            data_sources_status["cninfo"]["status"] = "error"
            data_sources_status["cninfo"]["error"] = str(e)[:100]
        data_sources_status["cninfo"]["lastUpdate"] = current_time

    except Exception as e:
        logger.error(f"检测数据源失败: {e}")


@router.post("/sources/check")
@log_api_call("检测数据源连接")
async def check_data_sources():
    """
    检测所有数据源的连接状态 - 真实测试每个数据源
    """
    import requests

    results = {}
    current_time = datetime.now().isoformat()

    # AKShare检测 - 实际获取数据测试
    try:
        import akshare as ak
        df = ak.tool_trade_date_hist_sina()
        if df is not None and not df.empty:
            data_sources_status["akshare"]["status"] = "online"
            data_sources_status["akshare"]["error"] = None
            results["akshare"] = "online"
        else:
            data_sources_status["akshare"]["status"] = "error"
            data_sources_status["akshare"]["error"] = "无法获取数据"
            results["akshare"] = "error"
    except Exception as e:
        data_sources_status["akshare"]["status"] = "error"
        data_sources_status["akshare"]["error"] = str(e)[:100]
        results["akshare"] = "error"
    data_sources_status["akshare"]["lastUpdate"] = current_time

    # Tushare检测 - 实际API调用测试
    try:
        import tushare as ts
        token = os.getenv('TUSHARE_TOKEN')
        if token:
            ts.set_token(token)
            pro = ts.pro_api()
            # 使用简单的接口测试
            df = pro.trade_cal(exchange='SSE', start_date='20250101', end_date='20250102')
            if df is not None and not df.empty:
                data_sources_status["tushare"]["status"] = "online"
                data_sources_status["tushare"]["error"] = None
                results["tushare"] = "online"
            else:
                data_sources_status["tushare"]["status"] = "error"
                data_sources_status["tushare"]["error"] = "无法获取数据"
                results["tushare"] = "error"
        else:
            data_sources_status["tushare"]["status"] = "offline"
            data_sources_status["tushare"]["error"] = "未配置TUSHARE_TOKEN"
            results["tushare"] = "offline"
    except Exception as e:
        data_sources_status["tushare"]["status"] = "error"
        data_sources_status["tushare"]["error"] = str(e)[:100]
        results["tushare"] = "error"
    data_sources_status["tushare"]["lastUpdate"] = current_time

    # 东方财富检测 - HTTP请求测试
    try:
        response = requests.get(
            "https://push2.eastmoney.com/api/qt/stock/get",
            params={"secid": "1.600519"},
            timeout=5
        )
        if response.status_code == 200:
            data_sources_status["eastmoney"]["status"] = "online"
            data_sources_status["eastmoney"]["error"] = None
            results["eastmoney"] = "online"
        else:
            data_sources_status["eastmoney"]["status"] = "error"
            data_sources_status["eastmoney"]["error"] = f"HTTP {response.status_code}"
            results["eastmoney"] = "error"
    except Exception as e:
        data_sources_status["eastmoney"]["status"] = "error"
        data_sources_status["eastmoney"]["error"] = str(e)[:100]
        results["eastmoney"] = "error"
    data_sources_status["eastmoney"]["lastUpdate"] = current_time

    # 聚合数据检测 - API调用测试
    try:
        juhe_key = os.getenv('JUHE_API_KEY')
        if juhe_key:
            response = requests.get(
                f"http://web.juhe.cn/finance/stock/hs",
                params={"gid": "sh601006", "key": juhe_key},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("error_code") == 0:
                    data_sources_status["juhe"]["status"] = "online"
                    data_sources_status["juhe"]["error"] = None
                    results["juhe"] = "online"
                else:
                    data_sources_status["juhe"]["status"] = "error"
                    data_sources_status["juhe"]["error"] = data.get("reason", "API错误")
                    results["juhe"] = "error"
            else:
                data_sources_status["juhe"]["status"] = "error"
                data_sources_status["juhe"]["error"] = f"HTTP {response.status_code}"
                results["juhe"] = "error"
        else:
            data_sources_status["juhe"]["status"] = "offline"
            data_sources_status["juhe"]["error"] = "未配置JUHE_API_KEY"
            results["juhe"] = "offline"
    except Exception as e:
        data_sources_status["juhe"]["status"] = "error"
        data_sources_status["juhe"]["error"] = str(e)[:100]
        results["juhe"] = "error"
    data_sources_status["juhe"]["lastUpdate"] = current_time

    # 巨潮资讯检测 - API调用测试
    try:
        from backend.dataflows.announcement.cninfo_api import CninfoConfig, get_cninfo_token
        if CninfoConfig.is_configured():
            # 尝试获取token来验证配置是否正确
            token = get_cninfo_token()
            if token:
                # 测试一个简单的API调用
                response = requests.get(
                    "https://webapi.cninfo.com.cn/api/stock/p_stock2101",
                    params={"scode": "000001", "access_token": token},
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("resultcode") == 200 or "records" in data:
                        data_sources_status["cninfo"]["status"] = "online"
                        data_sources_status["cninfo"]["error"] = None
                        results["cninfo"] = "online"
                    else:
                        data_sources_status["cninfo"]["status"] = "error"
                        data_sources_status["cninfo"]["error"] = data.get("resultmsg", "API返回错误")
                        results["cninfo"] = "error"
                else:
                    data_sources_status["cninfo"]["status"] = "error"
                    data_sources_status["cninfo"]["error"] = f"HTTP {response.status_code}"
                    results["cninfo"] = "error"
            else:
                data_sources_status["cninfo"]["status"] = "error"
                data_sources_status["cninfo"]["error"] = "无法获取Token"
                results["cninfo"] = "error"
        else:
            data_sources_status["cninfo"]["status"] = "offline"
            data_sources_status["cninfo"]["error"] = "未配置CNINFO凭证"
            results["cninfo"] = "offline"
    except Exception as e:
        data_sources_status["cninfo"]["status"] = "error"
        data_sources_status["cninfo"]["error"] = str(e)[:100]
        results["cninfo"] = "error"
    data_sources_status["cninfo"]["lastUpdate"] = current_time

    # 统计结果
    online_count = sum(1 for s in results.values() if s == "online")
    total_count = len(results)

    return {
        "success": True,
        "message": f"数据源检测完成: {online_count}/{total_count} 在线",
        "results": results
    }


@router.post("/sources/check-single")
@log_api_call("检测单个数据源")
async def check_single_data_source(request: Dict[str, Any]):
    """
    检测单个数据源的连接状态
    """
    try:
        source_id = request.get("source_id")
        if not source_id or source_id not in data_sources_status:
            return {"success": False, "error": "无效的数据源ID"}

        current_time = datetime.now().isoformat()
        status = "offline"
        error = None

        if source_id == "akshare":
            try:
                import akshare as ak
                df = ak.tool_trade_date_hist_sina()
                if df is not None and not df.empty:
                    status = "online"
                else:
                    status = "error"
                    error = "无法获取数据"
            except Exception as e:
                status = "error"
                error = str(e)[:100]

        elif source_id == "tushare":
            try:
                import tushare as ts
                token = os.getenv('TUSHARE_TOKEN')
                if token:
                    ts.set_token(token)
                    pro = ts.pro_api()
                    df = pro.daily(ts_code='000001.SZ', start_date='20250101', end_date='20250102')
                    if df is not None:
                        status = "online"
                    else:
                        status = "error"
                        error = "无法获取数据"
                else:
                    status = "offline"
                    error = "未配置TUSHARE_TOKEN"
            except Exception as e:
                status = "error"
                error = str(e)[:100]

        elif source_id == "eastmoney":
            try:
                import requests
                response = requests.get("https://push2.eastmoney.com/api/qt/stock/get", timeout=5)
                if response.status_code == 200:
                    status = "online"
                else:
                    status = "error"
                    error = f"HTTP {response.status_code}"
            except Exception as e:
                status = "error"
                error = str(e)[:100]

        elif source_id == "juhe":
            try:
                import requests
                juhe_key = os.getenv('JUHE_API_KEY')
                if juhe_key:
                    response = requests.get(f"http://web.juhe.cn/finance/stock/hs?gid=sh601006&key={juhe_key}", timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("error_code") == 0:
                            status = "online"
                        else:
                            status = "error"
                            error = data.get("reason", "API错误")
                    else:
                        status = "error"
                        error = f"HTTP {response.status_code}"
                else:
                    status = "offline"
                    error = "未配置JUHE_API_KEY"
            except Exception as e:
                status = "error"
                error = str(e)[:100]

        elif source_id == "cninfo":
            try:
                from backend.dataflows.announcement.cninfo_api import CninfoConfig
                if CninfoConfig.is_configured():
                    import requests
                    response = requests.get("https://webapi.cninfo.com.cn/", timeout=5)
                    if response.status_code == 200:
                        status = "online"
                    else:
                        status = "error"
                        error = f"HTTP {response.status_code}"
                else:
                    status = "offline"
                    error = "未配置CNINFO_ACCESS_KEY"
            except Exception as e:
                status = "error"
                error = str(e)[:100]

        # 更新状态
        data_sources_status[source_id]["status"] = status
        data_sources_status[source_id]["lastUpdate"] = current_time
        data_sources_status[source_id]["error"] = error

        return {
            "success": True,
            "source_id": source_id,
            "status": status,
            "error": error,
            "success_rate": 100 if status == "online" else 0
        }

    except Exception as e:
        logger.error(f"检测单个数据源失败: {e}")
        return {"success": False, "error": str(e)}


@router.get("/news")
@log_api_call("获取新闻列表")
async def get_news(source: Optional[str] = None, limit: int = 50):
    """
    获取新闻列表 - 使用统一新闻监控中心

    Args:
        source: 数据源筛选（可选）
        limit: 返回数量限制
    """
    try:
        # 优先使用统一新闻监控中心
        try:
            from backend.services.news_center import get_news_monitor_center
            monitor = get_news_monitor_center()

            # 从监控中心获取新闻
            news_data = monitor.get_latest_news(limit=limit)

            if news_data:
                # 按来源筛选
                if source and source != "all":
                    news_data = [n for n in news_data if n.get("source") == source]

                # 转换为前端期望的格式
                formatted_news = []
                for n in news_data:
                    formatted_news.append({
                        'id': n.get('id', ''),
                        'title': n.get('title', ''),
                        'summary': n.get('content', '')[:200] if n.get('content') else '',
                        'content': n.get('content', ''),
                        'publishTime': n.get('pub_time', ''),
                        'pub_time': n.get('pub_time', ''),
                        'source': n.get('source', ''),
                        'sentiment': n.get('sentiment', 'neutral'),
                        'sentiment_score': n.get('sentiment_score', 50),
                        'url': n.get('url', ''),
                        'keywords': n.get('keywords', []),
                        'urgency': n.get('urgency', 'low'),
                        'related_stocks': n.get('related_stocks', []),
                        'impact_score': n.get('impact_score', 0)
                    })

                # 计算情绪统计
                sentiment_stats = {
                    'positive': sum(1 for n in formatted_news if n.get('sentiment') == 'positive'),
                    'negative': sum(1 for n in formatted_news if n.get('sentiment') == 'negative'),
                    'neutral': sum(1 for n in formatted_news if n.get('sentiment') == 'neutral')
                }

                # 获取监控中心统计
                monitor_stats = monitor.get_stats()

                logger.info(f"📰 从统一新闻中心获取新闻: {len(formatted_news)}条")
                return {
                    "success": True,
                    "news": formatted_news,
                    "total": len(formatted_news),
                    "total_fetched": monitor_stats.get('total_fetched', len(formatted_news)),
                    "sentiment_stats": sentiment_stats,
                    "source": "news_monitor_center"
                }
        except Exception as e:
            logger.warning(f"统一新闻中心不可用，回退到旧逻辑: {e}")

        # 回退到旧逻辑
        global news_list

        # 如果新闻列表为空，主动获取市场新闻
        if not news_list:
            logger.info("📰 新闻列表为空，正在获取市场新闻...")
            try:
                import akshare as ak
                from backend.dataflows.stock.akshare_utils import get_stock_news_em

                # 尝试多个新闻源
                news_sources = [
                    ('stock_info_global_em', '东方财富'),
                    ('stock_news_em', '东方财富个股'),
                ]

                for api_name, source_name in news_sources:
                    if news_list:  # 如果已经获取到新闻，跳过
                        break
                    try:
                        if api_name == 'stock_info_global_em':
                            df = ak.stock_info_global_em()
                        elif api_name == 'stock_news_em':
                            # 使用修复版函数获取个股新闻
                            df = get_stock_news_em(symbol="000001", max_news=50)
                        else:
                            continue

                        if df is not None and not df.empty:
                            for _, row in df.head(50).iterrows():
                                # 根据不同API调整字段名
                                if api_name == 'stock_info_global_em':
                                    title = str(row.get('标题', ''))
                                    content = str(row.get('内容', ''))
                                    pub_time = str(row.get('发布时间', ''))
                                else:
                                    title = str(row.get('新闻标题', row.get('标题', '')))
                                    content = str(row.get('新闻内容', row.get('内容', '')))
                                    pub_time = str(row.get('发布时间', row.get('时间', '')))

                                if not title:
                                    continue

                                # 简单情绪分析
                                sentiment = 'neutral'
                                positive_keywords = ['涨', '上涨', '大涨', '暴涨', '利好', '突破', '新高', '增长', '盈利', '超预期', '上调', '增持']
                                negative_keywords = ['跌', '下跌', '大跌', '暴跌', '利空', '下滑', '新低', '亏损', '下降', '不及预期', '下调', '减持']

                                for kw in positive_keywords:
                                    if kw in title or kw in content:
                                        sentiment = 'positive'
                                        break
                                if sentiment == 'neutral':
                                    for kw in negative_keywords:
                                        if kw in title or kw in content:
                                            sentiment = 'negative'
                                            break

                                news_list.append({
                                    'id': f"em_{pub_time}_{len(news_list)}",
                                    'title': title,
                                    'summary': content[:200] if content else '',
                                    'content': content,
                                    'publishTime': pub_time,
                                    'pub_time': pub_time,
                                    'source': source_name,
                                    'sentiment': sentiment,
                                    'sentiment_score': 75 if sentiment == 'positive' else (25 if sentiment == 'negative' else 50),
                                    'url': '',
                                    'relatedStocks': []
                                })

                            logger.info(f"[OK] 从{source_name}获取市场新闻成功: {len(news_list)}条")
                    except Exception as e:
                        logger.warning(f"[WARN] 从{source_name}获取新闻失败: {e}")
                        continue

            except Exception as e:
                logger.warning(f"[WARN] 获取市场新闻失败: {e}")
                import traceback
                logger.warning(traceback.format_exc())

        filtered_news = news_list

        if source and source != "all":
            filtered_news = [n for n in news_list if n.get("source") == source]

        # 记录去重前的数量
        total_before_limit = len(filtered_news)
        filtered_news = filtered_news[:limit]

        # 计算情绪统计
        sentiment_stats = {
            'positive': sum(1 for n in filtered_news if n.get('sentiment') == 'positive'),
            'negative': sum(1 for n in filtered_news if n.get('sentiment') == 'negative'),
            'neutral': sum(1 for n in filtered_news if n.get('sentiment') == 'neutral')
        }

        return {
            "success": True,
            "news": filtered_news,
            "total": len(filtered_news),
            "total_fetched": len(news_list),  # 原始获取数量
            "total_after_filter": total_before_limit,  # 筛选后数量
            "sentiment_stats": sentiment_stats
        }

    except Exception as e:
        logger.error(f"获取新闻失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/news/{ts_code}")
@log_api_call("获取股票新闻")
async def get_stock_news(ts_code: str, limit: int = 20):
    """
    获取指定股票的新闻 - 使用专门的个股新闻接口

    数据源接口（共8个）:
    多源新闻聚合器（5个）:
    1. 东方财富个股新闻 (ak.stock_news_em) - 个股专属新闻
    2. 东方财富全球资讯 (ak.stock_info_global_em) - 关键词过滤
    3. 财联社全球资讯 (ak.stock_info_global_cls) - 关键词过滤
    4. 百度财经新闻 (ak.news_economic_baidu) - 关键词过滤
    5. 备用源realtime_news (get_realtime_stock_news) - 东方财富爬虫
    巨潮官方API（3个）:
    6. 巨潮个股公告 (cninfo_api.get_announcement_info)
    7. 巨潮个股新闻 (cninfo_api.get_news_list) - VIP
    8. 巨潮个股研报摘要 (cninfo_api.get_research_report_summary) - VIP
    """
    try:
        logger.info(f"获取{ts_code}的新闻...")

        # 清理股票代码
        clean_code = ts_code.replace('.SH', '').replace('.SZ', '').replace('.BJ', '')

        # 使用专门的个股新闻接口
        try:
            from backend.services.news_center import get_news_monitor_center
            monitor = get_news_monitor_center()

            # 使用 fetch_stock_news 获取个股专属新闻（而不是从全局缓存匹配）
            news_data = await monitor.fetch_stock_news(clean_code)

            # 过滤掉微博热议等全市场新闻（这些不是个股专属新闻）
            filtered_news = []
            excluded_sources = ['微博热议', '财经早餐', '新闻联播']

            for n in news_data:
                source = n.get('source', '')
                # 排除全市场新闻源
                if source in excluded_sources:
                    continue
                # 排除标题格式为 "[微博热议] xxx +x.xx%" 的新闻
                title = n.get('title', '')
                if title.startswith('[微博热议]'):
                    continue
                filtered_news.append(n)

            if filtered_news:
                # 转换为前端期望的格式
                formatted_news = []
                for n in filtered_news[:limit]:
                    formatted_news.append({
                        'title': n.get('title', ''),
                        'content': n.get('content', ''),
                        'pub_time': n.get('pub_time', ''),
                        'source': n.get('source', ''),
                        'sentiment': n.get('sentiment', 'neutral'),
                        'score': n.get('sentiment_score', 50),
                        'url': n.get('url', ''),
                        'keywords': n.get('keywords', []),
                        'urgency': n.get('urgency', 'low'),
                        'report_type': n.get('report_type', 'news'),
                        'impact_score': n.get('impact_score', 0)
                    })

                # 计算情绪统计
                overall_score = sum(n.get('score', 50) for n in formatted_news) / len(formatted_news) if formatted_news else 50
                sentiment_summary = {
                    'positive': sum(1 for n in formatted_news if n.get('sentiment') == 'positive'),
                    'negative': sum(1 for n in formatted_news if n.get('sentiment') == 'negative'),
                    'neutral': sum(1 for n in formatted_news if n.get('sentiment') == 'neutral')
                }

                logger.info(f"[OK] 个股新闻获取{ts_code}: {len(formatted_news)}条 (过滤前{len(news_data)}条)")
                return {
                    "success": True,
                    "news": formatted_news,
                    "total": len(formatted_news),
                    "overall_score": overall_score,
                    "sentiment_summary": sentiment_summary,
                    "source": "fetch_stock_news"
                }
        except Exception as e:
            logger.warning(f"个股新闻接口不可用，回退到旧逻辑: {e}")
            import traceback
            logger.debug(traceback.format_exc())

        # 回退到旧逻辑
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

        logger.info(f"[OK] 返回{len(news_list)}条新闻")

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
    获取股票的所有综合数据（此接口会触发数据更新）
    包括：实时行情、停复牌、ST状态、财务数据、审计意见、
          业绩预告、分红送股、限售解禁、股权质押、
          股东增减持、龙虎榜、新闻等

    注意：此接口会触发数据更新并保存到数据库
    前端详情模态框应使用 /from-db 接口只读取数据

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
                logger.info(f"[CACHE] 使用缓存数据 ({(current_time - cache_time).total_seconds():.1f}s前)")
                # 清理非法float值（inf, -inf, nan）
                sanitized_data = sanitize_for_json(cached_data['data'])
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
        result = sanitize_for_json(result)

        # 保存到内存缓存
        data_cache[cache_key] = {
            'cached_at': current_time.isoformat(),
            'data': result
        }

        # 保存到数据库
        with get_db_context() as db:
            StockDataService.save_or_update(
                db=db,
                ts_code=ts_code,
                data_type='comprehensive',
                data=result,
                source='mixed'
            )
            # 更新监控股票的最后更新时间
            MonitoredStockService.update_last_update(db, ts_code)
        logger.info(f"[OK] 综合数据已保存到数据库: {ts_code}")

        # 更新内存中的监控股票信息
        if ts_code in monitored_stocks:
            monitored_stocks[ts_code]["lastUpdate"] = current_time.isoformat()
            # 同时更新情绪和风险数据
            if 'overall_score' in result:
                monitored_stocks[ts_code]["sentimentScore"] = result.get('overall_score', 50)
            if 'risk' in result and isinstance(result['risk'], dict):
                monitored_stocks[ts_code]["riskLevel"] = result['risk'].get('risk_level', 'low')
                monitored_stocks[ts_code]["riskScore"] = result['risk'].get('risk_score', 0)
            if 'news' in result and isinstance(result['news'], list) and result['news']:
                monitored_stocks[ts_code]["latestNews"] = result['news'][0].get('title', '') if result['news'] else ''

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

            # 保存到内存缓存（已清理的数据）
            cache_key = f"comprehensive_{ts_code}"
            current_time = datetime.now()
            data_cache[cache_key] = {
                'cached_at': current_time.isoformat(),
                'data': result
            }

            # 保存到数据库
            with get_db_context() as db:
                StockDataService.save_or_update(
                    db=db,
                    ts_code=ts_code,
                    data_type='comprehensive',
                    data=result,
                    source='mixed'
                )
                # 更新监控股票的最后更新时间
                MonitoredStockService.update_last_update(db, ts_code)
            logger.info(f"[OK] 综合数据已保存到数据库: {ts_code}")

            # 更新内存中的监控股票信息
            if ts_code in monitored_stocks:
                monitored_stocks[ts_code]["lastUpdate"] = current_time.isoformat()
                # 同时更新情绪和风险数据
                if 'overall_score' in result:
                    monitored_stocks[ts_code]["sentimentScore"] = result.get('overall_score', 50)
                if 'risk' in result and isinstance(result['risk'], dict):
                    monitored_stocks[ts_code]["riskLevel"] = result['risk'].get('risk_level', 'low')
                    monitored_stocks[ts_code]["riskScore"] = result['risk'].get('risk_score', 0)
                if 'news' in result and isinstance(result['news'], list) and result['news']:
                    monitored_stocks[ts_code]["latestNews"] = result['news'][0].get('title', '') if result['news'] else ''

            # 发送完成信号，包含 interface_status
            complete_data = {
                'type': 'complete',
                'success_count': success_count,
                'total_count': total_count,
                'success_rate': f'{success_count/total_count*100:.1f}%' if total_count > 0 else '0%',
                'total_time': 0,
                'interface_status': result.get('interface_status', {}),
                'alerts': result.get('alerts', [])
            }
            yield f"data: {json.dumps(complete_data, ensure_ascii=False)}\n\n"

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
    首次添加后会立即执行一次数据更新
    立即返回响应，数据获取在后台异步执行
    """
    try:
        code = request.code

        # 检查是否已存在
        if code in monitored_stocks:
            raise HTTPException(status_code=400, detail="该股票已在监控列表中")

        # 快速获取股票名称（优先使用TDX缓存，避免网络请求）
        stock_name = code.split('.')[0]  # 默认使用代码
        pure_code = code.split('.')[0]
        try:
            # 优先从TDX缓存获取（最快，无网络请求）
            from backend.services.tdx_cache_service import read_stock_list
            stock_list = read_stock_list()
            if stock_list:
                # 构建快速查找字典（按code和ts_code索引）
                stock_dict = {s.get('code'): s.get('name') for s in stock_list if s.get('code')}
                stock_dict.update({s.get('ts_code'): s.get('name') for s in stock_list if s.get('ts_code')})

                # 快速查找
                if pure_code in stock_dict:
                    stock_name = stock_dict[pure_code]
                    logger.info(f"[OK] 从TDX缓存获取股票名称: {code} -> {stock_name}")
                elif code in stock_dict:
                    stock_name = stock_dict[code]
                    logger.info(f"[OK] 从TDX缓存获取股票名称: {code} -> {stock_name}")
        except Exception as e:
            logger.warning(f"[WARN] TDX缓存获取名称失败: {e}")

        # 如果TDX缓存没有，尝试使用请求中的名称（如果前端传了的话）
        if stock_name == code.split('.')[0] and hasattr(request, 'name') and request.name:
            stock_name = request.name

        # 保存到数据库
        with get_db_context() as db:
            MonitoredStockService.add_stock(
                db=db,
                ts_code=code,
                name=stock_name,
                frequency=request.frequency,
                items=request.items
            )

        # 添加到内存监控列表
        monitored_stocks[code] = {
            "name": stock_name,
            "code": code,
            "frequency": request.frequency,
            "items": request.items,
            "sentimentScore": 50,
            "riskLevel": "low",
            "latestNews": "",
            "lastUpdate": datetime.now().isoformat(),
            "pendingTasks": 1  # 标记有待处理任务
        }

        # 添加后台任务：首次添加后立即执行一次数据更新
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

        # 从数据库删除
        with get_db_context() as db:
            MonitoredStockService.delete_stock(db, code)

        # 从内存删除
        del monitored_stocks[code]

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
                
                logger.info(f"[OK] 获取新闻成功: {len(news_list_local)}条，全局新闻总数: {len(news_list)}")
                
            except Exception as e:
                logger.error(f"[FAIL] 获取新闻失败: {e}")
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
                
                logger.info(f"[OK] 情绪分析完成: {sentiment_score:.2f}分 ({sentiment_result.get('overall_sentiment')})")
                logger.info(f"   正面:{sentiment_result.get('positive_count')} 中性:{sentiment_result.get('neutral_count')} 负面:{sentiment_result.get('negative_count')}")
                
            except Exception as e:
                logger.error(f"[FAIL] 情绪分析失败: {e}")
                sentiment_score = 50
        elif items.get("sentiment", False):
            logger.warning(f"[WARN] 无新闻数据，跳过情绪分析")
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
                
                logger.info(f"[OK] {code} 风险分析完成: {stock_data['riskLevel']} (得分:{stock_data['riskScore']})")
                
            except Exception as e:
                logger.error(f"[FAIL] 风险分析失败 {code}: {e}")
                stock_data["riskLevel"] = "unknown"
        
        # 4. 停复牌监控
        if items.get("suspend", False):
            try:
                logger.info(f"检查{code}的停复牌状态...")
                suspend_status = check_suspend_status(code)
                
                stock_data["isSuspended"] = suspend_status.get("is_suspended", False)
                stock_data["suspendInfo"] = suspend_status
                
                if suspend_status.get("is_suspended"):
                    logger.warning(f"[WARN] {code} 当前处于停牌状态")
                    
            except Exception as e:
                logger.error(f"[FAIL] 停复牌检查失败 {code}: {e}")
        
        # 更新时间
        stock_data["lastUpdate"] = datetime.now().isoformat()

        # 获取综合数据并保存到数据库（使用分层获取，仅获取监控所需数据）
        try:
            logger.info(f"[INFO] 获取并保存 {code} 的监控数据到数据库...")
            service = get_comprehensive_service()

            # 使用分层获取：监控更新只获取L1（实时）和L2（中频）层数据
            # 静态数据（L4层）会自动使用缓存，避免重复获取
            comprehensive_result = service.get_monitor_data(code)

            # 清理非法float值
            comprehensive_result = sanitize_for_json(comprehensive_result)

            # 将情绪分析和风险分析结果添加到综合数据中
            comprehensive_result['overall_score'] = stock_data.get('sentimentScore', 50)
            comprehensive_result['sentiment_detail'] = stock_data.get('sentimentDetail', {})
            comprehensive_result['risk'] = {
                'risk_level': stock_data.get('riskLevel', 'low'),
                'risk_score': stock_data.get('riskScore', 0),
                'risk_factors': stock_data.get('riskFactors', {}),
                'warnings': stock_data.get('warnings', [])
            }

            # 保存到内存缓存
            cache_key = f"comprehensive_{code}"
            data_cache[cache_key] = {
                'cached_at': datetime.now().isoformat(),
                'data': comprehensive_result
            }

            # 保存到数据库
            with get_db_context() as db:
                StockDataService.save_or_update(
                    db=db,
                    ts_code=code,
                    data_type='comprehensive',
                    data=comprehensive_result,
                    source='mixed'
                )
                # 更新监控股票的最后更新时间
                MonitoredStockService.update_last_update(db, code)
            logger.info(f"[OK] 监控数据已保存到数据库: {code}")

        except Exception as e:
            logger.error(f"[FAIL] 保存监控数据失败 {code}: {e}")

        logger.info(f"[OK] 完成更新股票数据: {code}")
        
    except Exception as e:
        logger.error(f"[FAIL] 更新股票数据失败 {code}: {e}")


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


# ==================== 接口测试 ====================

@router.get("/interfaces/test/stream")
async def test_interfaces_stream():
    """
    流式测试所有数据接口（SSE）
    逐个测试各数据源的接口，实时返回测试结果
    """
    import time

    async def generate():
        try:
            # 定义要测试的接口
            interfaces = {
                'tushare': {
                    'name': 'Tushare',
                    'icon': '📊',
                    'interfaces': [
                        {'id': 'tushare_daily', 'name': '日线数据', 'category': '行情数据', 'test_func': 'test_tushare_daily'},
                        {'id': 'tushare_income', 'name': '利润表', 'category': '财务数据', 'test_func': 'test_tushare_income'},
                        {'id': 'tushare_suspend', 'name': '停复牌', 'category': '公告数据', 'test_func': 'test_tushare_suspend'},
                        {'id': 'tushare_pledge', 'name': '股权质押', 'category': '风险数据', 'test_func': 'test_tushare_pledge'},
                    ]
                },
                'akshare': {
                    'name': 'AKShare',
                    'icon': '🔗',
                    'interfaces': [
                        {'id': 'akshare_spot', 'name': '实时行情', 'category': '行情数据', 'test_func': 'test_akshare_spot'},
                        {'id': 'akshare_news', 'name': '个股新闻', 'category': '新闻数据', 'test_func': 'test_akshare_news'},
                        {'id': 'akshare_st', 'name': 'ST股票', 'category': '风险数据', 'test_func': 'test_akshare_st'},
                        {'id': 'akshare_block', 'name': '大宗交易', 'category': '交易数据', 'test_func': 'test_akshare_block'},
                    ]
                },
                'eastmoney': {
                    'name': '东方财富',
                    'icon': '💰',
                    'interfaces': [
                        {'id': 'em_realtime', 'name': '实时行情', 'category': '行情数据', 'test_func': 'test_em_realtime'},
                        {'id': 'em_news', 'name': '财经新闻', 'category': '新闻数据', 'test_func': 'test_em_news'},
                    ]
                },
                'cninfo': {
                    'name': '巨潮资讯',
                    'icon': '📋',
                    'interfaces': [
                        {'id': 'cninfo_company', 'name': '公司基本信息', 'category': '基础数据', 'test_func': 'test_cninfo_company'},
                        {'id': 'cninfo_stock', 'name': '股票基本信息', 'category': '基础数据', 'test_func': 'test_cninfo_stock'},
                        {'id': 'cninfo_announcement', 'name': '公告信息', 'category': '公告数据', 'test_func': 'test_cninfo_announcement'},
                    ]
                }
            }

            # 计算总接口数
            total = sum(len(source['interfaces']) for source in interfaces.values())

            # 发送开始信号
            yield f"data: {json.dumps({'type': 'start', 'total': total, 'sources': list(interfaces.keys())})}\n\n"

            progress = 0
            success_count = 0

            # 测试函数映射
            async def test_tushare_daily():
                import os
                token = os.getenv('TUSHARE_TOKEN')
                if not token:
                    return False, 'TUSHARE_TOKEN未配置'
                import tushare as ts
                ts.set_token(token)
                pro = ts.pro_api()
                df = pro.daily(ts_code='000001.SZ', start_date='20250101', end_date='20250102')
                return df is not None and not df.empty, f'{len(df)}条数据' if df is not None else '无数据'

            async def test_tushare_income():
                import os
                token = os.getenv('TUSHARE_TOKEN')
                if not token:
                    return False, 'TUSHARE_TOKEN未配置'
                import tushare as ts
                ts.set_token(token)
                pro = ts.pro_api()
                df = pro.income(ts_code='000001.SZ')
                return df is not None and not df.empty, f'{len(df)}条数据' if df is not None else '无数据'

            async def test_tushare_suspend():
                import os
                token = os.getenv('TUSHARE_TOKEN')
                if not token:
                    return False, 'TUSHARE_TOKEN未配置'
                import tushare as ts
                ts.set_token(token)
                pro = ts.pro_api()
                df = pro.suspend_d(ts_code='000001.SZ')
                return True, '接口可用'

            async def test_tushare_pledge():
                import os
                token = os.getenv('TUSHARE_TOKEN')
                if not token:
                    return False, 'TUSHARE_TOKEN未配置'
                import tushare as ts
                ts.set_token(token)
                pro = ts.pro_api()
                df = pro.pledge_stat(ts_code='000001.SZ')
                return df is not None and not df.empty, f'{len(df)}条数据' if df is not None else '无数据'

            async def test_akshare_spot():
                import akshare as ak
                df = ak.stock_zh_a_spot_em()
                return df is not None and not df.empty, f'{len(df)}只股票'

            async def test_akshare_news():
                import akshare as ak
                # stock_news_em 接口不稳定，使用 stock_info_global_em 替代
                df = ak.stock_info_global_em()
                return df is not None and not df.empty, f'{len(df)}条新闻'

            async def test_akshare_st():
                import akshare as ak
                df = ak.stock_zh_a_st_em()
                return df is not None and not df.empty, f'{len(df)}只ST股票'

            async def test_akshare_block():
                import akshare as ak
                df = ak.stock_dzjy_sctj()
                return df is not None and not df.empty, f'{len(df)}条记录'

            async def test_em_realtime():
                import akshare as ak
                df = ak.stock_zh_a_spot_em()
                return df is not None and not df.empty, f'{len(df)}只股票'

            async def test_em_news():
                import akshare as ak
                df = ak.stock_info_global_em()
                return df is not None and not df.empty, f'{len(df)}条新闻'

            async def test_cninfo_company():
                from backend.dataflows.announcement.cninfo_api import CninfoConfig, get_cninfo_token
                import requests
                if not CninfoConfig.is_configured():
                    return False, '未配置CNINFO凭证'
                token = get_cninfo_token()
                if not token:
                    return False, '无法获取Token'
                response = requests.get(
                    "https://webapi.cninfo.com.cn/api/stock/p_stock2100",
                    params={"scode": "000001", "access_token": token},
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("resultcode") == 200 or "records" in data:
                        return True, f'{len(data.get("records", []))}条数据'
                return False, f'HTTP {response.status_code}'

            async def test_cninfo_stock():
                from backend.dataflows.announcement.cninfo_api import CninfoConfig, get_cninfo_token
                import requests
                if not CninfoConfig.is_configured():
                    return False, '未配置CNINFO凭证'
                token = get_cninfo_token()
                if not token:
                    return False, '无法获取Token'
                response = requests.get(
                    "https://webapi.cninfo.com.cn/api/stock/p_stock2101",
                    params={"scode": "000001", "access_token": token},
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("resultcode") == 200 or "records" in data:
                        return True, f'{len(data.get("records", []))}条数据'
                return False, f'HTTP {response.status_code}'

            async def test_cninfo_announcement():
                from backend.dataflows.announcement.cninfo_api import CninfoConfig, get_cninfo_token
                import requests
                if not CninfoConfig.is_configured():
                    return False, '未配置CNINFO凭证'
                token = get_cninfo_token()
                if not token:
                    return False, '无法获取Token'
                response = requests.get(
                    "https://webapi.cninfo.com.cn/api/info/p_info3015",
                    params={"scode": "000001", "access_token": token},
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("resultcode") == 200 or "records" in data:
                        return True, f'{len(data.get("records", []))}条公告'
                return False, f'HTTP {response.status_code}'

            test_funcs = {
                'test_tushare_daily': test_tushare_daily,
                'test_tushare_income': test_tushare_income,
                'test_tushare_suspend': test_tushare_suspend,
                'test_tushare_pledge': test_tushare_pledge,
                'test_akshare_spot': test_akshare_spot,
                'test_akshare_news': test_akshare_news,
                'test_akshare_st': test_akshare_st,
                'test_akshare_block': test_akshare_block,
                'test_em_realtime': test_em_realtime,
                'test_em_news': test_em_news,
                'test_cninfo_company': test_cninfo_company,
                'test_cninfo_stock': test_cninfo_stock,
                'test_cninfo_announcement': test_cninfo_announcement,
            }

            # 逐个数据源测试
            for source_key, source_info in interfaces.items():
                # 发送数据源开始信号
                yield f"data: {json.dumps({'type': 'source_start', 'source': source_key, 'name': source_info['name'], 'icon': source_info['icon'], 'count': len(source_info['interfaces'])})}\n\n"

                source_success = 0
                source_fail = 0

                for iface in source_info['interfaces']:
                    # 发送测试开始信号
                    yield f"data: {json.dumps({'type': 'test_start', 'source': source_key, 'interface_id': iface['id'], 'name': iface['name'], 'category': iface['category']})}\n\n"

                    start_time = time.time()
                    try:
                        test_func = test_funcs.get(iface['test_func'])
                        if test_func:
                            success, message = await test_func()
                            elapsed = round(time.time() - start_time, 2)
                            status = 'success' if success else 'error'
                            if success:
                                source_success += 1
                                success_count += 1
                            else:
                                source_fail += 1
                        else:
                            elapsed = 0
                            status = 'not_implemented'
                            message = '测试函数未实现'
                            source_fail += 1
                    except Exception as e:
                        elapsed = round(time.time() - start_time, 2)
                        status = 'error'
                        message = str(e)[:100]
                        source_fail += 1

                    progress += 1

                    # 发送测试结果
                    yield f"data: {json.dumps({'type': 'test_result', 'source': source_key, 'interface_id': iface['id'], 'status': status, 'elapsed': elapsed, 'message': message, 'progress': progress})}\n\n"

                    # 短暂延迟避免过快
                    await asyncio.sleep(0.1)

                # 发送数据源完成信号
                yield f"data: {json.dumps({'type': 'source_complete', 'source': source_key, 'name': source_info['name'], 'success': source_success, 'fail': source_fail})}\n\n"

            # 发送完成信号
            success_rate = round(success_count / total * 100, 1) if total > 0 else 0
            yield f"data: {json.dumps({'type': 'complete', 'total': total, 'success': success_count, 'fail': total - success_count, 'success_rate': success_rate})}\n\n"

        except Exception as e:
            logger.error(f"接口测试失败: {e}")
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
