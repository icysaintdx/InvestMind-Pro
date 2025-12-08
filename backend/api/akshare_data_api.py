#!/usr/bin/env python3
"""
AKShare数据API
为前端和分析师提供统一的数据接口
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
from backend.dataflows.akshare.fund_flow_data import get_fund_flow_data
from backend.dataflows.akshare.financial_data import get_financial_data
from backend.dataflows.akshare.social_media_data import get_social_media_data
from backend.dataflows.akshare.hot_rank_data import get_hot_rank_data
from backend.dataflows.akshare.stock_search import get_stock_search

router = APIRouter(prefix="/api/akshare", tags=["AKShare Data"])


# ========== 资金流向API ==========
# 注意：主要的 /fund-flow/{stock_code} 路由在文件末尾（第369行）

@router.get("/fund-flow/industry/realtime")
async def get_industry_fund_flow():
    """
    获取行业资金流向（实时）
    
    Returns:
        行业资金流向数据
    """
    try:
        fund_flow = get_fund_flow_data()
        data = fund_flow.get_industry_fund_flow("即时")
        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fund-flow/concept/realtime")
async def get_concept_fund_flow():
    """
    获取概念资金流向（实时）
    
    Returns:
        概念资金流向数据
    """
    try:
        fund_flow = get_fund_flow_data()
        data = fund_flow.get_concept_fund_flow("即时")
        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fund-flow/north-bound/realtime")
async def get_north_bound_realtime():
    """
    获取北向资金实时数据
    
    Returns:
        北向资金实时数据
    """
    try:
        fund_flow = get_fund_flow_data()
        data = fund_flow.get_hsgt_realtime("北向资金")
        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 财务数据API ==========

@router.get("/financial/{symbol}")
async def get_financial(symbol: str, period: str = "report"):
    """
    获取财务数据
    
    Args:
        symbol: 股票代码（如：600519）
        period: 报告期类型（report/yearly/quarterly）
    
    Returns:
        财务数据（三大报表）
    """
    try:
        financial = get_financial_data()
        data = financial.get_comprehensive_financial_data(symbol, period)
        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/financial/{symbol}/summary")
async def get_financial_summary(symbol: str):
    """
    获取最新财务摘要
    
    Args:
        symbol: 股票代码（如：600519）
    
    Returns:
        最新财务摘要
    """
    try:
        financial = get_financial_data()
        data = financial.get_latest_financial_summary(symbol)
        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 社交媒体API ==========

@router.get("/social-media/all")
async def get_social_media_all():
    """
    获取综合社交媒体数据
    
    Returns:
        微博热搜、微博股票热议、百度热搜
    """
    try:
        social = get_social_media_data()
        data = social.get_comprehensive_social_media()
        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/social-media/weibo/hot-search")
async def get_weibo_hot_search():
    """
    获取微博热搜
    
    Returns:
        微博热搜列表
    """
    try:
        social = get_social_media_data()
        data = social.get_weibo_hot_search()
        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/social-media/weibo/stock-hot")
async def get_weibo_stock_hot():
    """
    获取微博股票热议
    
    Returns:
        微博股票热议列表
    """
    try:
        social = get_social_media_data()
        data = social.get_weibo_stock_hot()
        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 热榜API ==========

@router.get("/hot-rank/all")
async def get_all_hot_ranks():
    """
    获取所有热榜数据
    
    Returns:
        所有热榜数据
    """
    try:
        hot_rank = get_hot_rank_data()
        data = hot_rank.get_all_hot_ranks()
        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hot-rank/eastmoney")
async def get_eastmoney_hot():
    """
    获取东财热门股票
    
    Returns:
        东财热门股票列表
    """
    try:
        hot_rank = get_hot_rank_data()
        data = hot_rank.get_eastmoney_hot_rank()
        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hot-rank/keywords")
async def get_hot_keywords():
    """
    获取热门关键词
    
    Returns:
        热门关键词列表
    """
    try:
        hot_rank = get_hot_rank_data()
        data = hot_rank.get_hot_keywords()
        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hot-rank/popularity")
async def get_popularity_rank():
    """
    获取个股人气榜
    
    Returns:
        个股人气榜列表
    """
    try:
        hot_rank = get_hot_rank_data()
        data = hot_rank.get_stock_popularity_rank()
        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hot-rank/xueqiu")
async def get_xueqiu_hot():
    """
    获取雪球热度榜
    
    Returns:
        雪球热度榜列表
    """
    try:
        hot_rank = get_hot_rank_data()
        data = hot_rank.get_xueqiu_hot()
        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 股票搜索API ==========

@router.get("/stock/search")
async def search_stock(keyword: str, limit: int = 10):
    """
    搜索股票（本地数据库）
    
    Args:
        keyword: 搜索关键词（代码或名称）
        limit: 返回数量限制
    
    Returns:
        匹配的股票列表
    """
    try:
        stock_search = get_stock_search()
        data = stock_search.search_stock(keyword, limit)
        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stock/list/status")
async def get_stock_list_status():
    """
    获取股票列表状态
    
    Returns:
        股票总数、最后更新时间
    """
    try:
        stock_search = get_stock_search()
        return {
            "success": True,
            "data": {
                "count": stock_search.get_stock_count(),
                "last_update": stock_search.get_last_update_time()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stock/list/update")
async def update_stock_list():
    """
    手动更新股票列表
    
    Returns:
        更新结果
    """
    try:
        stock_search = get_stock_search()
        success = stock_search.force_update()
        return {
            "success": success,
            "message": "更新成功" if success else "更新失败"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 资金流向API ==========

from backend.dataflows.akshare.fund_flow_data import get_fund_flow_data

@router.get("/fund-flow/{stock_code}")
async def get_fund_flow(stock_code: str):
    """
    获取资金流向数据
    
    Args:
        stock_code: 股票代码
        
    Returns:
        资金流向数据
    """
    try:
        fund_flow = get_fund_flow_data()
        data = fund_flow.get_comprehensive_fund_flow(stock_code)
        
        # 统计数据源数量
        sources = {
            'north_bound': len(data.get('north_bound_realtime', [])),
            'industry_flow': len(data.get('industry_flow', [])),
            'concept_flow': len(data.get('concept_flow', [])),
            'individual_flow': len(data.get('individual_flow_top', [])),
            'margin_summary': len(data.get('margin_summary', []))
        }
        
        return {
            "success": True,
            "data": data,
            "sources": sources
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fund-flow/north-bound/realtime")
async def get_north_bound_realtime():
    """获取北向资金实时数据"""
    try:
        fund_flow = get_fund_flow_data()
        data = fund_flow.get_hsgt_realtime("北向资金")
        return {
            "success": True,
            "data": data,
            "count": len(data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fund-flow/industry")
async def get_industry_fund_flow():
    """获取行业资金流向"""
    try:
        fund_flow = get_fund_flow_data()
        data = fund_flow.get_industry_fund_flow("即时")
        return {
            "success": True,
            "data": data,
            "count": len(data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 行业板块API ==========

from backend.dataflows.akshare.sector_data import get_sector_data

@router.get("/sector/comprehensive")
async def get_comprehensive_sector():
    """
    获取综合板块数据
    
    Returns:
        板块数据
    """
    try:
        sector = get_sector_data()
        data = sector.get_comprehensive_sector_data()
        
        # 统计数据源数量
        sources = {
            'industry_list': len(data.get('industry_list', [])),
            'industry_flow': len(data.get('industry_flow', []))
        }
        
        return {
            "success": True,
            "data": data,
            "sources": sources
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sector/industry-list")
async def get_industry_list():
    """获取行业板块列表"""
    try:
        sector = get_sector_data()
        data = sector.get_industry_list()
        return {
            "success": True,
            "data": data,
            "count": len(data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 宏观经济API ==========

from backend.dataflows.akshare.macro_data import get_macro_data

@router.get("/macro/comprehensive")
async def get_comprehensive_macro():
    """
    获取综合宏观数据
    
    Returns:
        宏观数据
    """
    try:
        macro = get_macro_data()
        data = macro.get_comprehensive_macro_data()
        
        # 统计数据源数量
        sources = {
            'gdp': len(data.get('gdp', [])),
            'cpi': len(data.get('cpi', [])),
            'pmi': len(data.get('pmi', [])),
            'money_supply': len(data.get('money_supply', []))
        }
        
        return {
            "success": True,
            "data": data,
            "sources": sources
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/macro/gdp")
async def get_gdp():
    """获取GDP数据"""
    try:
        macro = get_macro_data()
        data = macro.get_gdp_data()
        return {
            "success": True,
            "data": data[:12],  # 最近12个月
            "count": len(data[:12])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/macro/cpi")
async def get_cpi():
    """获取CPI数据"""
    try:
        macro = get_macro_data()
        data = macro.get_cpi_data()
        return {
            "success": True,
            "data": data[:12],
            "count": len(data[:12])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/macro/pmi")
async def get_pmi():
    """获取PMI数据"""
    try:
        macro = get_macro_data()
        data = macro.get_pmi_data()
        return {
            "success": True,
            "data": data[:12],
            "count": len(data[:12])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
