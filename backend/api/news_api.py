"""
新闻分析API接口
集成新闻采集、情绪分析和舆情监控功能
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import asyncio

# 导入日志系统
from backend.utils.logging_config import get_logger
from backend.utils.tool_logging import log_api_call

# 导入新闻分析师
from backend.agents.analysts.news_analyst import create_news_analyst

# 导入数据流工具
from backend.dataflows.news.unified_news_tool import create_unified_news_tool
from backend.dataflows.news.realtime_news import get_realtime_news
from backend.dataflows.news.chinese_finance import get_chinese_finance_news

logger = get_logger("api.news")

# 创建路由器
router = APIRouter(prefix="/api/news", tags=["News Analysis"])


class NewsAnalysisRequest(BaseModel):
    """新闻分析请求模型"""
    stock_code: str = Field(..., description="股票代码")
    date: Optional[str] = Field(None, description="分析日期 (YYYY-MM-DD)")
    days_back: int = Field(3, description="向前查看的天数", ge=1, le=30)
    
class NewsAnalysisResponse(BaseModel):
    """新闻分析响应模型"""
    success: bool
    stock_code: str
    analysis_date: str
    sentiment_score: float = Field(..., description="情绪分数 (-1到1)")
    sentiment_label: str = Field(..., description="情绪标签")
    news_summary: str
    key_events: List[Dict[str, Any]]
    risk_factors: List[str]
    recommendations: str
    news_count: int
    
class NewsListRequest(BaseModel):
    """新闻列表请求模型"""
    stock_code: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    limit: int = Field(20, ge=1, le=100)
    source: Optional[str] = Field(None, description="新闻源筛选")
    
class NewsItem(BaseModel):
    """新闻条目模型"""
    title: str
    source: str
    publish_time: str
    summary: str
    sentiment: Optional[float] = None
    url: Optional[str] = None
    relevance: float = Field(..., description="相关度分数")
    
class NewsListResponse(BaseModel):
    """新闻列表响应模型"""
    success: bool
    stock_code: str
    total_count: int
    news_items: List[NewsItem]
    

@router.post("/analyze", response_model=NewsAnalysisResponse)
@log_api_call("新闻情绪分析")
async def analyze_news_sentiment(request: NewsAnalysisRequest):
    """
    分析股票相关新闻的情绪
    
    包括:
    - 新闻情绪打分
    - 关键事件提取
    - 风险因素识别
    - 投资建议生成
    """
    try:
        logger.info(f"开始分析 {request.stock_code} 的新闻情绪")
        
        # 准备分析日期
        if request.date:
            analysis_date = request.date
        else:
            analysis_date = datetime.now().strftime("%Y-%m-%d")
            
        # 创建状态对象（模拟LangGraph状态）
        state = {
            "company_of_interest": request.stock_code,
            "trade_date": analysis_date,
            "session_id": f"news-{request.stock_code}-{datetime.now().timestamp()}",
            "days_back": request.days_back
        }
        
        # 创建新闻分析师（这里需要配置LLM）
        # 注意：实际使用时需要传入正确的LLM和toolkit
        news_analyst = create_news_analyst(llm=None, toolkit=None)
        
        # 执行分析
        analysis_result = await asyncio.to_thread(news_analyst, state)
        
        # 解析情绪分数
        sentiment_score = analysis_result.get("sentiment", 0)
        sentiment_label = _get_sentiment_label(sentiment_score)
        
        # 构建响应
        response = NewsAnalysisResponse(
            success=True,
            stock_code=request.stock_code,
            analysis_date=analysis_date,
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label,
            news_summary=analysis_result.get("summary", "暂无新闻摘要"),
            key_events=analysis_result.get("key_events", []),
            risk_factors=analysis_result.get("risk_factors", []),
            recommendations=analysis_result.get("recommendation", "持有观望"),
            news_count=analysis_result.get("news_count", 0)
        )
        
        logger.success(f"{request.stock_code} 新闻分析完成，情绪得分: {sentiment_score}")
        return response
        
    except Exception as e:
        logger.error(f"新闻分析失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"新闻分析失败: {str(e)}")


@router.post("/list", response_model=NewsListResponse)
@log_api_call("获取新闻列表")
async def get_news_list(request: NewsListRequest):
    """
    获取股票相关新闻列表
    
    支持:
    - 时间范围筛选
    - 新闻源筛选
    - 相关度排序
    """
    try:
        logger.info(f"获取 {request.stock_code} 的新闻列表")
        
        # 准备日期范围
        end_date = request.end_date or datetime.now().strftime("%Y-%m-%d")
        start_date = request.start_date or (
            datetime.now() - timedelta(days=7)
        ).strftime("%Y-%m-%d")
        
        # 获取新闻数据
        news_data = await _fetch_news_data(
            stock_code=request.stock_code,
            start_date=start_date,
            end_date=end_date,
            source=request.source
        )
        
        # 转换为响应格式
        news_items = []
        for item in news_data[:request.limit]:
            news_items.append(NewsItem(
                title=item.get("title", ""),
                source=item.get("source", "未知"),
                publish_time=item.get("publish_time", ""),
                summary=item.get("summary", ""),
                sentiment=item.get("sentiment"),
                url=item.get("url"),
                relevance=item.get("relevance", 0.5)
            ))
            
        response = NewsListResponse(
            success=True,
            stock_code=request.stock_code,
            total_count=len(news_data),
            news_items=news_items
        )
        
        logger.success(f"获取到 {len(news_items)} 条新闻")
        return response
        
    except Exception as e:
        logger.error(f"获取新闻列表失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取新闻失败: {str(e)}")


@router.get("/sources")
async def get_news_sources():
    """获取可用的新闻源列表"""
    try:
        sources = [
            {"id": "eastmoney", "name": "东方财富", "type": "financial"},
            {"id": "sina", "name": "新浪财经", "type": "financial"},
            {"id": "xueqiu", "name": "雪球", "type": "social"},
            {"id": "cls", "name": "财联社", "type": "news"},
            {"id": "tushare", "name": "Tushare", "type": "data"},
            {"id": "juhe", "name": "聚合数据", "type": "api"}
        ]
        
        return {
            "success": True,
            "sources": sources,
            "total": len(sources)
        }
        
    except Exception as e:
        logger.error(f"获取新闻源失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sentiment/history")
async def get_sentiment_history(
    stock_code: str = Query(..., description="股票代码"),
    days: int = Query(30, description="历史天数", ge=7, le=90)
):
    """
    获取历史情绪趋势
    
    返回指定天数内的每日情绪分数
    """
    try:
        logger.info(f"获取 {stock_code} 过去 {days} 天的情绪历史")
        
        # TODO: 实现历史情绪数据获取
        # 这里需要从数据库或缓存中读取历史分析结果
        
        # 模拟数据
        history = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            history.append({
                "date": date,
                "sentiment": 0.1 + (i % 5) * 0.1 - 0.2,  # 模拟波动
                "news_count": 10 + (i % 3) * 5
            })
            
        return {
            "success": True,
            "stock_code": stock_code,
            "days": days,
            "history": history
        }
        
    except Exception as e:
        logger.error(f"获取情绪历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# 辅助函数
def _get_sentiment_label(score: float) -> str:
    """根据情绪分数返回标签"""
    if score >= 0.5:
        return "非常积极"
    elif score >= 0.2:
        return "积极"
    elif score >= -0.2:
        return "中性"
    elif score >= -0.5:
        return "消极"
    else:
        return "非常消极"


async def _fetch_news_data(
    stock_code: str,
    start_date: str,
    end_date: str,
    source: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    从多个数据源获取新闻数据
    
    Args:
        stock_code: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        source: 指定数据源
        
    Returns:
        新闻数据列表
    """
    try:
        # 这里实现实际的新闻数据获取
        # 可以调用 backend.dataflows.news 中的各种工具
        
        # 暂时返回模拟数据
        mock_news = [
            {
                "title": f"{stock_code} 发布最新财报，业绩超预期",
                "source": "东方财富",
                "publish_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "summary": "公司第三季度营收同比增长20%，净利润增长15%",
                "sentiment": 0.6,
                "relevance": 0.9,
                "url": "http://example.com/news1"
            },
            {
                "title": f"机构调研 {stock_code}，关注未来发展",
                "source": "新浪财经",
                "publish_time": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
                "summary": "多家机构集中调研，看好公司长期发展",
                "sentiment": 0.3,
                "relevance": 0.8,
                "url": "http://example.com/news2"
            }
        ]
        
        return mock_news
        
    except Exception as e:
        logger.error(f"获取新闻数据失败: {str(e)}")
        return []


# 测试端点
@router.get("/test")
async def test_news_api():
    """测试新闻API是否正常工作"""
    return {
        "status": "ok",
        "message": "News API is working",
        "timestamp": datetime.now().isoformat()
    }


# 实时新闻API端点
class RealtimeNewsRequest(BaseModel):
    """实时新闻请求模型"""
    ticker: str = Field(..., description="股票代码")
    curr_date: Optional[str] = Field(None, description="当前日期 (YYYY-MM-DD)")
    hours_back: int = Field(6, description="回溯小时数", ge=1, le=24)


class RealtimeNewsResponse(BaseModel):
    """实时新闻响应模型"""
    success: bool
    ticker: str
    date: str
    report: str = Field(..., description="格式化的新闻报告")
    source: str = Field(..., description="数据源")
    news_count: int = Field(0, description="新闻数量")
    fetch_time: float = Field(0.0, description="获取耗时(秒)")


@router.post("/realtime", response_model=RealtimeNewsResponse)
@log_api_call(api_name="get_realtime_news")
async def get_realtime_news_api(request: RealtimeNewsRequest):
    """
    获取实时新闻数据
    
    这个接口调用后端的实时新闻获取功能，
    优先使用东方财富（AKShare）数据源。
    
    Args:
        request: 实时新闻请求参数
        
    Returns:
        实时新闻响应，包含格式化的 Markdown 报告
    """
    import time
    start_time = time.time()
    
    try:
        # 设置默认日期
        curr_date = request.curr_date or datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"开始获取 {request.ticker} 的实时新闻，日期: {curr_date}")
        
        # 调用后端实时新闻获取功能
        from backend.dataflows.realtime_news_utils import get_realtime_stock_news
        
        news_report = get_realtime_stock_news(
            ticker=request.ticker,
            curr_date=curr_date,
            hours_back=request.hours_back
        )
        
        # 计算耗时
        fetch_time = time.time() - start_time
        
        # 统计新闻数量（简单统计，通过标题数量）
        news_count = news_report.count('###') if news_report else 0
        
        logger.info(f"✅ 成功获取 {request.ticker} 的新闻，耗时: {fetch_time:.2f}秒")
        
        return RealtimeNewsResponse(
            success=True,
            ticker=request.ticker,
            date=curr_date,
            report=news_report,
            source="东方财富 (AKShare)",
            news_count=news_count,
            fetch_time=round(fetch_time, 2)
        )
        
    except Exception as e:
        logger.error(f"❌ 获取实时新闻失败: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # 返回错误响应
        return RealtimeNewsResponse(
            success=False,
            ticker=request.ticker,
            date=request.curr_date or datetime.now().strftime('%Y-%m-%d'),
            report=f"新闻获取失败: {str(e)}",
            source="错误",
            news_count=0,
            fetch_time=0.0
        )
