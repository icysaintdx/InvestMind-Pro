#!/usr/bin/env python3
"""
统一新闻API端点
供前端调用

功能说明：
1. /stock - 智能分析使用，调用 unified_news_api 获取个股新闻
2. /list, /statistics, /sources - 新闻中心使用，并行获取多数据源新闻
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import concurrent.futures
import threading

from backend.dataflows.news.unified_news_api import get_unified_news_api
from backend.dataflows.news.hot_search_api import get_hot_search_api
from backend.utils.logging_config import get_logger
from backend.utils.log_stream_handler import attach_log_stream, detach_log_stream
from backend.api.agent_logs_api import end_agent_log_stream

logger = get_logger("unified_news_endpoint")

router = APIRouter(prefix="/api/unified-news", tags=["Unified News"])

# ==================== 新闻中心缓存 ====================
_news_center_cache: List[Dict[str, Any]] = []
_news_center_last_sync: Optional[datetime] = None
_news_center_cache_duration = 300  # 5分钟缓存
_news_center_lock = threading.Lock()
_news_center_source_stats: Dict[str, int] = {}


class StockNewsRequest(BaseModel):
    """股票新闻请求"""
    ticker: str
    agent_id: Optional[str] = "news_analyst"  # 智能体ID，用于日志流
    use_cache: Optional[bool] = True  # 是否使用缓存，默认True
    

class StockNewsResponse(BaseModel):
    """股票新闻响应"""
    success: bool
    ticker: str
    timestamp: str
    data: dict
    message: Optional[str] = None
    from_cache: Optional[bool] = False  # 是否来自缓存


@router.post("/stock", response_model=StockNewsResponse)
async def get_stock_comprehensive_news(request: StockNewsRequest):
    """
    获取股票综合新闻（带实时日志流和缓存）
    
    整合多个数据源：
    - 实时新闻聚合器
    - AKShare个股新闻
    - 财联社快讯
    - 微博热议
    - 情绪分析
    
    缓存机制：
    - 默认启用5分钟缓存
    - 同一股票在5分钟内的重复请求会直接返回缓存数据
    - 可通过 use_cache=false 强制刷新
    
    日志会实时推送到前端，显示在智能体卡片中
    """
    agent_id = request.agent_id
    use_cache = request.use_cache if request.use_cache is not None else True
    
    # 附加日志流处理器到多个 logger
    handler1 = attach_log_stream("unified_news_endpoint", agent_id)
    handler2 = attach_log_stream("unified_news", agent_id)  # 也附加到 unified_news logger
    handler3 = attach_log_stream("agents", agent_id)  # 附加到 agents logger
    handler4 = attach_log_stream("akshare_news", agent_id)  # 附加到 akshare_news logger
    
    try:
        logger.info(f"收到股票新闻请求: {request.ticker}")
        logger.info(f"开始获取{request.ticker}的综合新闻数据... (缓存: {'启用' if use_cache else '禁用'})")
        
        api = get_unified_news_api()
        result = api.get_stock_news_comprehensive(request.ticker, use_cache=use_cache)
        
        from_cache = result.get('from_cache', False)
        if from_cache:
            logger.info("✅ 从缓存返回数据")
        else:
            logger.info("✅ 综合新闻数据获取完成")
        
        # 结束日志流
        end_agent_log_stream(agent_id)
        
        return StockNewsResponse(
            success=True,
            ticker=request.ticker,
            timestamp=datetime.now().isoformat(),
            data=result,
            from_cache=from_cache
        )
        
    except Exception as e:
        logger.error(f"❌ 获取股票新闻失败: {e}")
        end_agent_log_stream(agent_id)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # 移除所有日志流处理器
        detach_log_stream("unified_news_endpoint", handler1)
        detach_log_stream("unified_news", handler2)
        detach_log_stream("agents", handler3)
        detach_log_stream("akshare_news", handler4)


@router.get("/market")
async def get_market_news():
    """
    获取市场新闻
    
    包含：
    - 财经早餐
    - 全球财经新闻
    """
    try:
        logger.info("收到市场新闻请求")
        
        api = get_unified_news_api()
        result = api.get_market_news()
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "data": result
        }
        
    except Exception as e:
        logger.error(f"获取市场新闻失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hot-search")
async def get_hot_search():
    """
    获取热搜数据
    
    包含：
    - 微博热搜
    - 百度热搜
    - 股票相关话题过滤
    """
    try:
        logger.info("收到热搜请求")
        
        api = get_hot_search_api()
        result = api.get_all_stock_hot_topics()
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "data": result
        }
        
    except Exception as e:
        logger.error(f"获取热搜失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/stats")
async def get_cache_stats():
    """
    获取新闻缓存统计信息
    
    返回：
    - total_entries: 缓存条目总数
    - valid_entries: 有效缓存数
    - expired_entries: 已过期缓存数
    - ttl_seconds: 缓存有效期（秒）
    """
    try:
        api = get_unified_news_api()
        stats = api.get_cache_stats()
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"获取缓存统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cache/{ticker}")
async def clear_ticker_cache(ticker: str):
    """
    清除指定股票的新闻缓存
    
    Args:
        ticker: 股票代码
    """
    try:
        logger.info(f"清除缓存请求: {ticker}")
        
        api = get_unified_news_api()
        result = api.clear_cache(ticker)
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "message": result.get('message')
        }
        
    except Exception as e:
        logger.error(f"清除缓存失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cache")
async def clear_all_cache():
    """
    清除所有新闻缓存
    """
    try:
        logger.info("清除所有缓存请求")
        
        api = get_unified_news_api()
        result = api.clear_cache()
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "message": result.get('message')
        }
        
    except Exception as e:
        logger.error(f"清除所有缓存失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """健康检查"""
    api = get_unified_news_api()
    cache_stats = api.get_cache_stats()

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "cache": cache_stats,
        "endpoints": [
            "/api/unified-news/stock",
            "/api/unified-news/market",
            "/api/unified-news/hot-search",
            "/api/unified-news/list",
            "/api/unified-news/statistics",
            "/api/unified-news/sources",
            "/api/unified-news/cache/stats",
            "/api/unified-news/cache/{ticker}",
            "/api/unified-news/cache"
        ]
    }


# ==================== 新闻中心专用端点 ====================

def _analyze_sentiment(text: str) -> str:
    """简单的情绪分析"""
    positive_words = ["涨", "上涨", "增长", "利好", "突破", "新高", "反弹", "上升", "盈利", "增加", "提升", "扩大", "超预期", "强势", "大涨", "暴涨", "飙升"]
    negative_words = ["跌", "下跌", "下降", "利空", "跌破", "新低", "回落", "下滑", "亏损", "减少", "下调", "收缩", "不及预期", "弱势", "风险", "大跌", "暴跌", "崩盘"]

    positive_count = sum(1 for word in positive_words if word in text)
    negative_count = sum(1 for word in negative_words if word in text)

    if positive_count > negative_count:
        return "positive"
    elif negative_count > positive_count:
        return "negative"
    else:
        return "neutral"


def _fetch_global_em() -> List[Dict[str, Any]]:
    """获取东方财富全球资讯"""
    news_list = []
    try:
        import akshare as ak
        df = ak.stock_info_global_em()
        if df is not None and not df.empty:
            for idx, row in df.head(100).iterrows():  # 增加到100条
                title = str(row.get("标题", row.get("title", "")))
                if title:
                    news_list.append({
                        "id": f"em_global_{idx}_{datetime.now().timestamp()}",
                        "title": title,
                        "summary": str(row.get("内容", row.get("content", "")))[:300],
                        "source": "akshare_eastmoney",
                        "source_name": "东方财富",
                        "publish_time": str(row.get("发布时间", row.get("datetime", datetime.now().isoformat()))),
                        "market": "全球",
                        "news_type": "全球财经",
                        "sentiment": _analyze_sentiment(title),
                        "sentiment_score": 0.5,
                        "related_stocks": [],
                        "url": str(row.get("链接", row.get("url", "")))
                    })
    except Exception as e:
        logger.warning(f"[数据源] 东方财富全球资讯获取失败: {e}")
    return news_list


def _fetch_futu_global() -> List[Dict[str, Any]]:
    """获取富途全球资讯"""
    news_list = []
    try:
        import akshare as ak
        df = ak.stock_info_global_futu()
        if df is not None and not df.empty:
            for idx, row in df.head(100).iterrows():  # 增加到100条
                title = str(row.get("标题", ""))
                if title:
                    news_list.append({
                        "id": f"futu_{idx}_{datetime.now().timestamp()}",
                        "title": title,
                        "summary": str(row.get("内容", ""))[:300],
                        "source": "akshare_futu",
                        "source_name": "富途",
                        "publish_time": str(row.get("发布时间", datetime.now().isoformat())),
                        "market": "全球",
                        "news_type": "全球财经",
                        "sentiment": _analyze_sentiment(title),
                        "sentiment_score": 0.5,
                        "related_stocks": [],
                        "url": str(row.get("链接", ""))
                    })
    except Exception as e:
        logger.warning(f"[数据源] 富途全球资讯获取失败: {e}")
    return news_list


def _fetch_sina_global() -> List[Dict[str, Any]]:
    """获取新浪全球资讯"""
    news_list = []
    try:
        import akshare as ak
        df = ak.stock_info_global_sina()
        if df is not None and not df.empty:
            for idx, row in df.head(100).iterrows():  # 增加到100条
                content = str(row.get("内容", ""))
                title = content
                if "【" in content and "】" in content:
                    title = content[content.find("【")+1:content.find("】")]
                news_list.append({
                    "id": f"sina_{idx}_{datetime.now().timestamp()}",
                    "title": title[:100],
                    "summary": content[:300],
                    "source": "akshare_sina",
                    "source_name": "新浪财经",
                    "publish_time": str(row.get("时间", datetime.now().isoformat())),
                    "market": "A股",
                    "news_type": "财经快讯",
                    "sentiment": _analyze_sentiment(content),
                    "sentiment_score": 0.5,
                    "related_stocks": [],
                    "url": ""
                })
    except Exception as e:
        logger.warning(f"[数据源] 新浪全球资讯获取失败: {e}")
    return news_list


def _fetch_ths_global() -> List[Dict[str, Any]]:
    """获取同花顺全球资讯"""
    news_list = []
    try:
        import akshare as ak
        df = ak.stock_info_global_ths()
        if df is not None and not df.empty:
            for idx, row in df.head(100).iterrows():  # 增加到100条
                title = str(row.get("标题", ""))
                if title:
                    news_list.append({
                        "id": f"ths_{idx}_{datetime.now().timestamp()}",
                        "title": title,
                        "summary": str(row.get("内容", ""))[:300],
                        "source": "akshare_ths",
                        "source_name": "同花顺",
                        "publish_time": str(row.get("发布时间", datetime.now().isoformat())),
                        "market": "全球",
                        "news_type": "全球财经",
                        "sentiment": _analyze_sentiment(title),
                        "sentiment_score": 0.5,
                        "related_stocks": [],
                        "url": str(row.get("链接", ""))
                    })
    except Exception as e:
        logger.warning(f"[数据源] 同花顺全球资讯获取失败: {e}")
    return news_list


def _fetch_cls_global() -> List[Dict[str, Any]]:
    """获取财联社全球资讯"""
    news_list = []
    try:
        import akshare as ak
        import socket
        original_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(15)
        try:
            df = ak.stock_info_global_cls()
            if df is not None and not df.empty:
                for idx, row in df.head(100).iterrows():  # 增加到100条
                    title = str(row.get("标题", row.get("title", "")))
                    if title:
                        news_list.append({
                            "id": f"cls_global_{idx}_{datetime.now().timestamp()}",
                            "title": title,
                            "summary": str(row.get("内容", row.get("content", "")))[:300],
                            "source": "akshare_cls",
                            "source_name": "财联社",
                            "publish_time": str(row.get("发布日期", "")) + " " + str(row.get("发布时间", "")),
                            "market": "全球",
                            "news_type": "快讯",
                            "sentiment": _analyze_sentiment(title),
                            "sentiment_score": 0.5,
                            "related_stocks": [],
                            "url": ""
                        })
        finally:
            socket.setdefaulttimeout(original_timeout)
    except Exception as e:
        logger.warning(f"[数据源] 财联社全球资讯获取失败: {e}")
    return news_list


def _fetch_weibo_hot() -> List[Dict[str, Any]]:
    """获取微博股票热议"""
    news_list = []
    try:
        import akshare as ak
        df = ak.stock_js_weibo_report()
        if df is not None and not df.empty:
            for idx, row in df.head(80).iterrows():  # 增加到80条
                # 微博热议数据格式：name(股票名称), rate(涨跌幅)
                stock_name = str(row.get("name", ""))
                rate = row.get("rate", 0)

                # 格式化涨跌幅
                try:
                    rate_val = float(rate) if rate else 0
                    rate_str = f"{rate_val:+.2f}%" if rate_val != 0 else "0.00%"
                except:
                    rate_str = "0.00%"

                if stock_name and stock_name != "nan":
                    title = f"【微博热议】{stock_name} 涨跌幅: {rate_str}"
                    news_list.append({
                        "id": f"weibo_{idx}_{datetime.now().timestamp()}",
                        "title": title,
                        "summary": f"{stock_name} 在微博上引发热议，当前涨跌幅: {rate_str}",
                        "source": "akshare_weibo",
                        "source_name": "微博热议",
                        "publish_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "market": "A股",
                        "news_type": "社交热议",
                        "sentiment": "positive" if rate_val > 0 else ("negative" if rate_val < 0 else "neutral"),
                        "sentiment_score": 0.5 + rate_val / 20,  # 根据涨跌幅调整情绪分数
                        "related_stocks": [],
                        "url": ""
                    })
    except Exception as e:
        logger.warning(f"[数据源] 微博热议获取失败: {e}")
    return news_list


def _fetch_morning_news() -> List[Dict[str, Any]]:
    """获取财经早餐"""
    news_list = []
    try:
        import akshare as ak
        df = ak.stock_info_cjzc_em()
        if df is not None and not df.empty:
            for idx, row in df.head(100).iterrows():  # 增加到100条
                title = str(row.get("标题", ""))
                content = str(row.get("内容", ""))
                if title:
                    news_list.append({
                        "id": f"morning_{idx}_{datetime.now().timestamp()}",
                        "title": title,
                        "summary": content[:300] if content else title,
                        "source": "akshare_morning",
                        "source_name": "财经早餐",
                        "publish_time": str(row.get("发布时间", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))),
                        "market": "A股",
                        "news_type": "财经早餐",
                        "sentiment": _analyze_sentiment(title + content),
                        "sentiment_score": 0.5,
                        "related_stocks": [],
                        "url": ""
                    })
    except Exception as e:
        logger.warning(f"[数据源] 财经早餐获取失败: {e}")
    return news_list


def _fetch_cninfo_announcement() -> List[Dict[str, Any]]:
    """获取巨潮资讯公告（权威公告源）- 使用东方财富公告作为替代"""
    news_list = []
    try:
        import akshare as ak

        # 获取最近几天的公告
        for days_ago in range(3):
            try:
                date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y%m%d")
                df = ak.stock_notice_report(symbol="全部", date=date)
                if df is not None and not df.empty:
                    for idx, row in df.head(50).iterrows():
                        # 列名：代码, 名称, 公告标题, 公告类型, 公告日期, 地址
                        title = str(row.iloc[2]) if len(row) > 2 else ""  # 公告标题
                        if title and title != "nan":
                            stock_code = str(row.iloc[0]) if len(row) > 0 else ""  # 代码
                            stock_name = str(row.iloc[1]) if len(row) > 1 else ""  # 名称
                            notice_type = str(row.iloc[3]) if len(row) > 3 else ""  # 公告类型
                            ann_date = str(row.iloc[4]) if len(row) > 4 else ""  # 公告日期
                            url = str(row.iloc[5]) if len(row) > 5 else ""  # 地址

                            news_list.append({
                                "id": f"cninfo_{date}_{idx}_{datetime.now().timestamp()}",
                                "title": f"【公告】{stock_name}({stock_code}): {title}",
                                "summary": f"{notice_type}: {title}",
                                "source": "akshare_cninfo",
                                "source_name": "巨潮资讯",
                                "publish_time": ann_date if ann_date else f"{date[:4]}-{date[4:6]}-{date[6:8]}",
                                "market": "A股",
                                "news_type": "公告",
                                "sentiment": "neutral",
                                "sentiment_score": 0.5,
                                "related_stocks": [stock_code] if stock_code else [],
                                "url": url
                            })
            except Exception as e:
                logger.debug(f"巨潮资讯{date}获取失败: {e}")

    except Exception as e:
        logger.warning(f"[数据源] 巨潮资讯公告获取失败: {e}")
    return news_list


def _fetch_eastmoney_notice() -> List[Dict[str, Any]]:
    """获取东方财富分类公告（重大事项、财务报告、融资公告）"""
    news_list = []
    try:
        import akshare as ak

        today = datetime.now().strftime("%Y%m%d")

        # 获取分类公告
        categories = ["重大事项", "财务报告", "融资公告", "风险提示"]
        for category in categories:
            try:
                df = ak.stock_notice_report(symbol=category, date=today)
                if df is not None and not df.empty:
                    for idx, row in df.head(30).iterrows():
                        # 列名：代码, 名称, 公告标题, 公告类型, 公告日期, 地址
                        title = str(row.iloc[2]) if len(row) > 2 else ""  # 公告标题
                        if title and title != "nan":
                            stock_code = str(row.iloc[0]) if len(row) > 0 else ""  # 代码
                            stock_name = str(row.iloc[1]) if len(row) > 1 else ""  # 名称
                            ann_date = str(row.iloc[4]) if len(row) > 4 else ""  # 公告日期
                            url = str(row.iloc[5]) if len(row) > 5 else ""  # 地址

                            news_list.append({
                                "id": f"em_notice_{category}_{idx}_{datetime.now().timestamp()}",
                                "title": f"【{category}】{stock_name}({stock_code}): {title}",
                                "summary": title,
                                "source": "akshare_em_notice",
                                "source_name": "东方财富公告",
                                "publish_time": ann_date if ann_date else today,
                                "market": "A股",
                                "news_type": category,
                                "sentiment": "neutral",
                                "sentiment_score": 0.5,
                                "related_stocks": [stock_code] if stock_code else [],
                                "url": url
                            })
            except Exception as e:
                logger.debug(f"东方财富{category}公告获取失败: {e}")

    except Exception as e:
        logger.warning(f"[数据源] 东方财富公告获取失败: {e}")
    return news_list


def _fetch_cctv_news() -> List[Dict[str, Any]]:
    """获取新闻联播文字稿"""
    news_list = []
    try:
        import akshare as ak

        # 获取最近几天的新闻联播
        for days_ago in range(3):
            try:
                date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y%m%d")
                df = ak.news_cctv(date=date)
                if df is not None and not df.empty:
                    for idx, row in df.head(10).iterrows():
                        title = str(row.get("title", row.get("标题", "")))
                        content = str(row.get("content", row.get("内容", "")))
                        if title:
                            news_list.append({
                                "id": f"cctv_{date}_{idx}_{datetime.now().timestamp()}",
                                "title": f"【新闻联播】{title}",
                                "summary": content[:300] if content else title,
                                "source": "akshare_cctv",
                                "source_name": "新闻联播",
                                "publish_time": f"{date[:4]}-{date[4:6]}-{date[6:8]} 19:00:00",
                                "market": "政策",
                                "news_type": "政策新闻",
                                "sentiment": _analyze_sentiment(title + content),
                                "sentiment_score": 0.5,
                                "related_stocks": [],
                                "url": ""
                            })
            except Exception as e:
                logger.debug(f"新闻联播{date}获取失败: {e}")

    except Exception as e:
        logger.warning(f"[数据源] 新闻联播获取失败: {e}")
    return news_list


def _fetch_baidu_economic() -> List[Dict[str, Any]]:
    """获取百度经济新闻（财经日历）"""
    news_list = []
    try:
        import akshare as ak

        # 获取最近几天的财经日历数据
        for days_ago in range(3):
            try:
                date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y%m%d")
                df = ak.news_economic_baidu(date=date)
                if df is not None and not df.empty:
                    for idx, row in df.head(20).iterrows():
                        # 百度财经日历的列名：日期, 时间, 地区, 事件, 公布, 预期, 前值, 重要性
                        event = str(row.get("事件", ""))
                        region = str(row.get("地区", row.get("国家", "")))
                        time_str = str(row.get("时间", ""))
                        actual = str(row.get("公布", row.get("今值", "")))
                        forecast = str(row.get("预期", ""))
                        previous = str(row.get("前值", ""))

                        if event and event != "nan":
                            # 构建标题，如果有地区则显示，否则不显示括号
                            if region and region != "nan":
                                title = f"【{region}】{event}"
                            else:
                                title = event

                            # 构建摘要
                            summary_parts = []
                            if region and region != "nan":
                                summary_parts.append(region)
                            summary_parts.append(event)
                            if actual and actual != "nan" and actual != "NaN":
                                summary_parts.append(f"公布:{actual}")
                            if forecast and forecast != "nan" and forecast != "NaN":
                                summary_parts.append(f"预期:{forecast}")
                            if previous and previous != "nan" and previous != "NaN":
                                summary_parts.append(f"前值:{previous}")
                            summary = " ".join(summary_parts)

                            news_list.append({
                                "id": f"baidu_eco_{date}_{idx}_{datetime.now().timestamp()}",
                                "title": title,
                                "summary": summary,
                                "source": "akshare_baidu",
                                "source_name": "百度财经",
                                "publish_time": f"{date[:4]}-{date[4:6]}-{date[6:8]} {time_str}" if time_str and time_str != "nan" else f"{date[:4]}-{date[4:6]}-{date[6:8]}",
                                "market": "全球",
                                "news_type": "财经日历",
                                "sentiment": "neutral",
                                "sentiment_score": 0.5,
                                "related_stocks": [],
                                "url": ""
                            })
            except Exception as e:
                logger.debug(f"百度财经{date}获取失败: {e}")

    except Exception as e:
        logger.warning(f"[数据源] 百度经济新闻获取失败: {e}")
    return news_list


def _fetch_tushare_news() -> List[Dict[str, Any]]:
    """获取Tushare新闻（条件性启用，需要权限）"""
    news_list = []
    try:
        from backend.dataflows.providers.china.tushare import get_tushare_provider
        import asyncio

        provider = get_tushare_provider()
        if not provider.is_available():
            logger.debug("[数据源] Tushare不可用，跳过")
            return []

        # 尝试获取新闻
        try:
            # 使用同步方式调用
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                news_data = loop.run_until_complete(provider.get_stock_news(limit=20, hours_back=24))
            finally:
                loop.close()

            if news_data:
                for idx, item in enumerate(news_data):
                    title = item.get("title", "")
                    if title:
                        news_list.append({
                            "id": f"tushare_{idx}_{datetime.now().timestamp()}",
                            "title": title,
                            "summary": item.get("summary", item.get("content", ""))[:300],
                            "source": "tushare",
                            "source_name": f"Tushare-{item.get('source', '综合')}",
                            "publish_time": item.get("publish_time", datetime.now()).strftime("%Y-%m-%d %H:%M:%S") if hasattr(item.get("publish_time"), "strftime") else str(item.get("publish_time", "")),
                            "market": "A股",
                            "news_type": item.get("category", "综合新闻"),
                            "sentiment": item.get("sentiment", "neutral"),
                            "sentiment_score": 0.5,
                            "related_stocks": [],
                            "url": item.get("url", "")
                        })
                logger.info(f"[数据源] Tushare新闻获取成功: {len(news_list)} 条")

        except Exception as e:
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in ['权限', 'permission', 'unauthorized', '积分', 'point']):
                logger.debug(f"[数据源] Tushare新闻需要付费权限，跳过: {e}")
            else:
                logger.warning(f"[数据源] Tushare新闻获取失败: {e}")

    except ImportError:
        logger.debug("[数据源] Tushare未安装，跳过")
    except Exception as e:
        logger.warning(f"[数据源] Tushare新闻获取失败: {e}")

    return news_list


def _fetch_all_news_center_parallel() -> List[Dict[str, Any]]:
    """并行获取新闻中心所有数据源（已整合智能分析页面的数据源 + 公告 + 政策）"""
    global _news_center_source_stats
    all_news = []
    source_stats = {}

    logger.info("=" * 60)
    logger.info("开始并行获取新闻中心数据（12个数据源）...")
    logger.info("=" * 60)

    start_time = datetime.now()

    with concurrent.futures.ThreadPoolExecutor(max_workers=14) as executor:
        futures = {
            # 原有数据源（7个）
            executor.submit(_fetch_global_em): "东方财富",
            executor.submit(_fetch_futu_global): "富途",
            executor.submit(_fetch_sina_global): "新浪财经",
            executor.submit(_fetch_ths_global): "同花顺",
            executor.submit(_fetch_cls_global): "财联社",
            executor.submit(_fetch_weibo_hot): "微博热议",
            executor.submit(_fetch_morning_news): "财经早餐",
            # 新增数据源（5个）
            executor.submit(_fetch_cninfo_announcement): "巨潮资讯",
            executor.submit(_fetch_eastmoney_notice): "东方财富公告",
            executor.submit(_fetch_cctv_news): "新闻联播",
            executor.submit(_fetch_baidu_economic): "百度财经",
            executor.submit(_fetch_tushare_news): "Tushare",
        }

        for future in concurrent.futures.as_completed(futures, timeout=30):
            source_name = futures[future]
            try:
                news = future.result(timeout=20)
                all_news.extend(news)
                source_stats[source_name] = len(news)
                logger.info(f"[数据源] {source_name}获取成功: {len(news)} 条")
            except Exception as e:
                logger.warning(f"[数据源] {source_name}获取失败: {e}")
                source_stats[source_name] = 0

    elapsed = (datetime.now() - start_time).total_seconds()

    # 去重
    seen_titles = set()
    unique_news = []
    for news in all_news:
        title = news.get("title", "")
        if title and title not in seen_titles:
            seen_titles.add(title)
            unique_news.append(news)

    _news_center_source_stats = source_stats

    logger.info("=" * 60)
    logger.info(f"新闻中心数据获取完成: 耗时 {elapsed:.2f}秒, 共 {len(unique_news)} 条")
    logger.info("=" * 60)

    unique_news.sort(key=lambda x: x.get("publish_time", ""), reverse=True)
    return unique_news


def _get_news_center_cached() -> List[Dict[str, Any]]:
    """获取新闻中心缓存数据"""
    global _news_center_cache, _news_center_last_sync

    with _news_center_lock:
        now = datetime.now()
        if _news_center_last_sync is None or (now - _news_center_last_sync).total_seconds() > _news_center_cache_duration:
            logger.info("新闻中心缓存已过期，正在刷新...")
            _news_center_cache = _fetch_all_news_center_parallel()
            _news_center_last_sync = now

        return _news_center_cache


def _calculate_news_statistics(news_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """计算新闻统计数据"""
    total = len(news_list)
    positive = sum(1 for n in news_list if n.get("sentiment") == "positive")
    negative = sum(1 for n in news_list if n.get("sentiment") == "negative")
    neutral = total - positive - negative

    source_counts = {}
    for n in news_list:
        source = n.get("source_name", n.get("source", "unknown"))
        source_counts[source] = source_counts.get(source, 0) + 1

    market_counts = {}
    for n in news_list:
        market = n.get("market", "未知")
        market_counts[market] = market_counts.get(market, 0) + 1

    type_counts = {}
    for n in news_list:
        news_type = n.get("news_type", "未知")
        type_counts[news_type] = type_counts.get(news_type, 0) + 1

    return {
        "total_count": total,
        "positive_count": positive,
        "negative_count": negative,
        "neutral_count": neutral,
        "source_counts": source_counts,
        "market_counts": market_counts,
        "type_counts": type_counts,
        "last_update": datetime.now().isoformat()
    }


@router.get("/list")
async def get_news_list(
    market: Optional[str] = Query(None, description="市场筛选"),
    news_type: Optional[str] = Query(None, description="新闻类型"),
    sentiment: Optional[str] = Query(None, description="情绪筛选"),
    source: Optional[str] = Query(None, description="数据源筛选"),
    limit: int = Query(500, description="返回数量限制")  # 增加默认限制到500
):
    """获取新闻列表（新闻中心使用）"""
    try:
        news_data = _get_news_center_cached()

        # 先计算全部数据的统计（用于显示总数）
        full_statistics = _calculate_news_statistics(news_data)

        # 然后进行筛选
        result = news_data.copy()

        if market:
            result = [n for n in result if n.get("market") == market]
        if news_type:
            result = [n for n in result if n.get("news_type") == news_type]
        if sentiment:
            result = [n for n in result if n.get("sentiment") == sentiment]
        if source:
            result = [n for n in result if n.get("source") == source or n.get("source_name") == source]

        # 筛选后的统计
        filtered_statistics = _calculate_news_statistics(result)

        # 限制返回数量
        result = result[:limit]

        return {
            "success": True,
            "data": result,
            "statistics": full_statistics,  # 返回全部数据的统计
            "filtered_statistics": filtered_statistics,  # 返回筛选后的统计
            "total": len(result),
            "full_total": len(news_data),  # 全部数据总数
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"获取新闻列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_news_statistics():
    """获取新闻统计数据（新闻中心使用）"""
    try:
        news_data = _get_news_center_cached()
        statistics = _calculate_news_statistics(news_data)

        return {
            "success": True,
            "data": statistics,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"获取统计数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sources")
async def get_news_sources():
    """获取数据源状态（新闻中心使用）"""
    try:
        global _news_center_source_stats

        # 确保有数据
        _get_news_center_cached()

        source_configs = [
            # 原有数据源（7个）
            {"id": "akshare_eastmoney", "name": "东方财富", "description": "东方财富全球资讯", "priority": 1},
            {"id": "akshare_futu", "name": "富途", "description": "富途全球资讯", "priority": 2},
            {"id": "akshare_ths", "name": "同花顺", "description": "同花顺全球资讯", "priority": 3},
            {"id": "akshare_sina", "name": "新浪财经", "description": "新浪财经快讯", "priority": 4},
            {"id": "akshare_cls", "name": "财联社", "description": "财联社全球资讯", "priority": 5},
            {"id": "akshare_weibo", "name": "微博热议", "description": "微博股票热议榜", "priority": 6},
            {"id": "akshare_morning", "name": "财经早餐", "description": "东方财富财经早餐", "priority": 7},
            # 新增数据源（5个）
            {"id": "akshare_cninfo", "name": "巨潮资讯", "description": "巨潮资讯公告（权威）", "priority": 8},
            {"id": "akshare_em_notice", "name": "东方财富公告", "description": "东方财富公告信息", "priority": 9},
            {"id": "akshare_cctv", "name": "新闻联播", "description": "央视新闻联播文字稿", "priority": 10},
            {"id": "akshare_baidu", "name": "百度财经", "description": "百度经济新闻", "priority": 11},
            {"id": "tushare", "name": "Tushare", "description": "Tushare新闻（需权限）", "priority": 12},
        ]

        sources = {}
        for config in source_configs:
            source_name = config["name"]
            news_count = _news_center_source_stats.get(source_name, 0)

            sources[config["id"]] = {
                "id": config["id"],
                "name": source_name,
                "status": "healthy" if news_count > 0 else "offline",
                "priority": config["priority"],
                "description": config["description"],
                "news_count": news_count,
                "last_check": datetime.now().isoformat()
            }

        return {
            "success": True,
            "data": sources,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"获取数据源状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh")
async def refresh_news_center():
    """强制刷新新闻中心缓存"""
    global _news_center_cache, _news_center_last_sync

    try:
        logger.info("强制刷新新闻中心缓存...")

        with _news_center_lock:
            _news_center_cache = []
            _news_center_last_sync = None

        news_data = _get_news_center_cached()
        statistics = _calculate_news_statistics(news_data)

        return {
            "success": True,
            "message": "新闻中心缓存已刷新",
            "total": len(news_data),
            "statistics": statistics,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"刷新新闻中心缓存失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync")
async def sync_news_center():
    """同步新闻中心（与refresh相同）"""
    return await refresh_news_center()


@router.get("/search")
async def search_news(keyword: str = Query(..., description="搜索关键词"), limit: int = Query(100, description="返回数量限制")):
    """搜索新闻"""
    try:
        news_data = _get_news_center_cached()
        keyword_lower = keyword.lower()

        result = []
        for news in news_data:
            title = news.get("title", "").lower()
            summary = news.get("summary", "").lower()
            if keyword_lower in title or keyword_lower in summary:
                result.append(news)

        result.sort(key=lambda x: x.get("publish_time", ""), reverse=True)

        return {
            "success": True,
            "keyword": keyword,
            "total": len(result),
            "data": result[:limit],
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"搜索新闻失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
