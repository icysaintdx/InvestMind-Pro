# -*- coding: utf-8 -*-
"""
巨潮资讯网API管理接口
提供配置管理、数据查询、测试等功能
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from backend.utils.logging_config import get_logger
from backend.utils.tool_logging import log_api_call

logger = get_logger("cninfo_api_route")

router = APIRouter(prefix="/api/cninfo", tags=["巨潮资讯"])


class CninfoConfigRequest(BaseModel):
    """巨潮配置请求"""
    access_key: Optional[str] = None
    access_secret: Optional[str] = None
    access_token: Optional[str] = None


class StockQueryRequest(BaseModel):
    """股票查询请求"""
    stock_codes: List[str]
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    report_date: Optional[str] = None


@router.get("/status")
@log_api_call("获取巨潮API状态")
async def get_cninfo_status():
    """获取巨潮API配置状态"""
    try:
        from backend.dataflows.announcement.cninfo_api import CninfoConfig
        return {
            "success": True,
            "config": CninfoConfig.get_all_config(),
            "message": "已配置" if CninfoConfig.is_configured() else "未配置"
        }
    except Exception as e:
        logger.error(f"获取巨潮状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config")
@log_api_call("保存巨潮API配置")
async def save_cninfo_config(request: CninfoConfigRequest):
    """保存巨潮API配置"""
    try:
        from backend.dataflows.announcement.cninfo_api import CninfoConfig

        config = {}
        if request.access_key:
            config['CNINFO_ACCESS_KEY'] = request.access_key
        if request.access_secret:
            config['CNINFO_ACCESS_SECRET'] = request.access_secret
        if request.access_token:
            config['CNINFO_ACCESS_TOKEN'] = request.access_token

        if not config:
            return {"success": False, "message": "未提供任何配置"}

        success = CninfoConfig.save_config(config)
        if success:
            return {"success": True, "message": "配置保存成功"}
        else:
            return {"success": False, "message": "配置保存失败"}
    except Exception as e:
        logger.error(f"保存巨潮配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test")
@log_api_call("测试巨潮API连接")
async def test_cninfo_connection():
    """测试巨潮API连接"""
    try:
        from backend.dataflows.announcement.cninfo_api import get_cninfo_api_client, CninfoConfig

        if not CninfoConfig.is_configured():
            return {
                "success": False,
                "message": "巨潮API未配置，请先配置 Access Token",
                "configured": False
            }

        client = get_cninfo_api_client()

        # 测试获取贵州茅台信息
        result = await client.get_stock_info(['600519'])

        if result['success']:
            return {
                "success": True,
                "message": "连接成功",
                "test_result": {
                    "api": "get_stock_info",
                    "stock": "600519",
                    "records": result['total'],
                    "sample": result['data'][0] if result['data'] else None
                }
            }
        else:
            return {
                "success": False,
                "message": f"API调用失败: {result.get('error')}",
                "error_code": result.get('code')
            }
    except Exception as e:
        logger.error(f"测试巨潮连接失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 股票数据接口 ====================

@router.get("/stock/info")
@log_api_call("获取股票信息")
async def get_stock_info(codes: str, market: str = ''):
    """
    获取股票背景资料

    Args:
        codes: 股票代码，多个用逗号分隔
        market: 市场 SZ/SH
    """
    try:
        from backend.dataflows.announcement.cninfo_api import get_cninfo_api_client

        client = get_cninfo_api_client()
        stock_codes = [c.strip() for c in codes.split(',') if c.strip()]

        result = await client.get_stock_info(stock_codes, market)
        return result
    except Exception as e:
        logger.error(f"获取股票信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/company")
@log_api_call("获取公司信息")
async def get_company_info(codes: str):
    """
    获取公司基本信息

    Args:
        codes: 股票代码，多个用逗号分隔
    """
    try:
        from backend.dataflows.announcement.cninfo_api import get_cninfo_api_client

        client = get_cninfo_api_client()
        stock_codes = [c.strip() for c in codes.split(',') if c.strip()]

        result = await client.get_company_info(stock_codes)
        return result
    except Exception as e:
        logger.error(f"获取公司信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/sector")
@log_api_call("获取股票板块")
async def get_stock_sector(codes: str, type_code: str = '137004'):
    """
    获取股票所属板块

    Args:
        codes: 股票代码，多个用逗号分隔
        type_code: 分类标准 137002中上协/137004申万/137005新财富
    """
    try:
        from backend.dataflows.announcement.cninfo_api import get_cninfo_api_client

        client = get_cninfo_api_client()
        stock_codes = [c.strip() for c in codes.split(',') if c.strip()]

        result = await client.get_stock_sector(stock_codes, type_code)
        return result
    except Exception as e:
        logger.error(f"获取股票板块失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 财务数据接口 ====================

@router.get("/finance/forecast")
@log_api_call("获取业绩预告")
async def get_performance_forecast(codes: str = '', report_date: str = ''):
    """
    获取业绩预告

    Args:
        codes: 股票代码，多个用逗号分隔
        report_date: 报告期 YYYY-MM-DD
    """
    try:
        from backend.dataflows.announcement.cninfo_api import get_cninfo_api_client

        client = get_cninfo_api_client()
        stock_codes = [c.strip() for c in codes.split(',') if c.strip()] if codes else None

        result = await client.get_performance_forecast(stock_codes, report_date)
        return result
    except Exception as e:
        logger.error(f"获取业绩预告失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/finance/express")
@log_api_call("获取业绩快报")
async def get_performance_express(codes: str = '', report_date: str = ''):
    """
    获取业绩快报

    Args:
        codes: 股票代码，多个用逗号分隔
        report_date: 报告期 YYYY-MM-DD
    """
    try:
        from backend.dataflows.announcement.cninfo_api import get_cninfo_api_client

        client = get_cninfo_api_client()
        stock_codes = [c.strip() for c in codes.split(',') if c.strip()] if codes else None

        result = await client.get_performance_express(stock_codes, report_date)
        return result
    except Exception as e:
        logger.error(f"获取业绩快报失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/finance/balance")
@log_api_call("获取资产负债表")
async def get_balance_sheet(codes: str, start_date: str = '', end_date: str = ''):
    """
    获取资产负债表

    Args:
        codes: 股票代码，多个用逗号分隔（最多50只）
        start_date: 开始日期
        end_date: 结束日期
    """
    try:
        from backend.dataflows.announcement.cninfo_api import get_cninfo_api_client

        client = get_cninfo_api_client()
        stock_codes = [c.strip() for c in codes.split(',') if c.strip()]

        result = await client.get_balance_sheet(stock_codes, start_date, end_date)
        return result
    except Exception as e:
        logger.error(f"获取资产负债表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/finance/income")
@log_api_call("获取利润表")
async def get_income_statement(codes: str, start_date: str = '', end_date: str = ''):
    """
    获取利润表

    Args:
        codes: 股票代码，多个用逗号分隔（最多50只）
        start_date: 开始日期
        end_date: 结束日期
    """
    try:
        from backend.dataflows.announcement.cninfo_api import get_cninfo_api_client

        client = get_cninfo_api_client()
        stock_codes = [c.strip() for c in codes.split(',') if c.strip()]

        result = await client.get_income_statement(stock_codes, start_date, end_date)
        return result
    except Exception as e:
        logger.error(f"获取利润表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/finance/cashflow")
@log_api_call("获取现金流量表")
async def get_cash_flow(codes: str, start_date: str = '', end_date: str = ''):
    """
    获取现金流量表

    Args:
        codes: 股票代码，多个用逗号分隔（最多50只）
        start_date: 开始日期
        end_date: 结束日期
    """
    try:
        from backend.dataflows.announcement.cninfo_api import get_cninfo_api_client

        client = get_cninfo_api_client()
        stock_codes = [c.strip() for c in codes.split(',') if c.strip()]

        result = await client.get_cash_flow(stock_codes, start_date, end_date)
        return result
    except Exception as e:
        logger.error(f"获取现金流量表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/finance/indicators")
@log_api_call("获取财务指标")
async def get_financial_indicators(codes: str, start_date: str = '', end_date: str = ''):
    """
    获取财务指标

    Args:
        codes: 股票代码，多个用逗号分隔（最多50只）
        start_date: 开始日期
        end_date: 结束日期
    """
    try:
        from backend.dataflows.announcement.cninfo_api import get_cninfo_api_client

        client = get_cninfo_api_client()
        stock_codes = [c.strip() for c in codes.split(',') if c.strip()]

        result = await client.get_financial_indicators(stock_codes, start_date, end_date)
        return result
    except Exception as e:
        logger.error(f"获取财务指标失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/finance/quick")
@log_api_call("获取快速指标")
async def get_quick_indicators(codes: str, report_date: str = ''):
    """
    获取个股指标快速版

    Args:
        codes: 股票代码，多个用逗号分隔（最多300只）
        report_date: 报告期
    """
    try:
        from backend.dataflows.announcement.cninfo_api import get_cninfo_api_client

        client = get_cninfo_api_client()
        stock_codes = [c.strip() for c in codes.split(',') if c.strip()]

        result = await client.get_quick_indicators(stock_codes, report_date)
        return result
    except Exception as e:
        logger.error(f"获取快速指标失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 交易数据接口 ====================

@router.get("/trade/daily")
@log_api_call("获取日行情")
async def get_daily_quote(codes: str, start_date: str = '', end_date: str = ''):
    """
    获取日行情数据

    Args:
        codes: 股票代码，多个用逗号分隔（最多50只）
        start_date: 开始日期
        end_date: 结束日期
    """
    try:
        from backend.dataflows.announcement.cninfo_api import get_cninfo_api_client

        client = get_cninfo_api_client()
        stock_codes = [c.strip() for c in codes.split(',') if c.strip()]

        # 默认获取最近30天
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        result = await client.get_daily_quote(stock_codes, start_date, end_date)
        return result
    except Exception as e:
        logger.error(f"获取日行情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trade/suspend")
@log_api_call("获取停复牌信息")
async def get_suspend_resume(codes: str = '', start_date: str = '', end_date: str = ''):
    """
    获取停复牌信息

    Args:
        codes: 股票代码，多个用逗号分隔
        start_date: 开始日期
        end_date: 结束日期
    """
    try:
        from backend.dataflows.announcement.cninfo_api import get_cninfo_api_client

        client = get_cninfo_api_client()
        stock_codes = [c.strip() for c in codes.split(',') if c.strip()] if codes else None

        result = await client.get_suspend_resume(stock_codes, start_date, end_date)
        return result
    except Exception as e:
        logger.error(f"获取停复牌信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trade/limit")
@log_api_call("获取涨跌停统计")
async def get_limit_stats(codes: str = '', start_date: str = '', end_date: str = ''):
    """
    获取涨跌停统计

    Args:
        codes: 股票代码，多个用逗号分隔
        start_date: 开始日期
        end_date: 结束日期
    """
    try:
        from backend.dataflows.announcement.cninfo_api import get_cninfo_api_client

        client = get_cninfo_api_client()
        stock_codes = [c.strip() for c in codes.split(',') if c.strip()] if codes else None

        result = await client.get_limit_stats(stock_codes, start_date, end_date)
        return result
    except Exception as e:
        logger.error(f"获取涨跌停统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trade/block")
@log_api_call("获取大宗交易")
async def get_block_trade(codes: str = '', start_date: str = '', end_date: str = ''):
    """
    获取大宗交易数据

    Args:
        codes: 股票代码，多个用逗号分隔
        start_date: 开始日期
        end_date: 结束日期
    """
    try:
        from backend.dataflows.announcement.cninfo_api import get_cninfo_api_client

        client = get_cninfo_api_client()
        stock_codes = [c.strip() for c in codes.split(',') if c.strip()] if codes else None

        result = await client.get_block_trade(stock_codes, start_date, end_date)
        return result
    except Exception as e:
        logger.error(f"获取大宗交易失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trade/margin")
@log_api_call("获取融资融券")
async def get_margin_trading(codes: str = '', start_date: str = '', end_date: str = ''):
    """
    获取融资融券数据

    Args:
        codes: 股票代码，多个用逗号分隔
        start_date: 开始日期
        end_date: 结束日期
    """
    try:
        from backend.dataflows.announcement.cninfo_api import get_cninfo_api_client

        client = get_cninfo_api_client()
        stock_codes = [c.strip() for c in codes.split(',') if c.strip()] if codes else None

        result = await client.get_margin_trading(stock_codes, start_date, end_date)
        return result
    except Exception as e:
        logger.error(f"获取融资融券失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 股东数据接口 ====================

@router.get("/shareholder/count")
@log_api_call("获取股东户数")
async def get_shareholder_count(codes: str, report_date: str = ''):
    """
    获取股东户数

    Args:
        codes: 股票代码，多个用逗号分隔
        report_date: 报告期
    """
    try:
        from backend.dataflows.announcement.cninfo_api import get_cninfo_api_client

        client = get_cninfo_api_client()
        stock_codes = [c.strip() for c in codes.split(',') if c.strip()]

        result = await client.get_shareholder_count(stock_codes, report_date)
        return result
    except Exception as e:
        logger.error(f"获取股东户数失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shareholder/top")
@log_api_call("获取十大股东")
async def get_top_shareholders(codes: str, report_date: str = ''):
    """
    获取十大股东

    Args:
        codes: 股票代码，多个用逗号分隔
        report_date: 报告期
    """
    try:
        from backend.dataflows.announcement.cninfo_api import get_cninfo_api_client

        client = get_cninfo_api_client()
        stock_codes = [c.strip() for c in codes.split(',') if c.strip()]

        result = await client.get_top_shareholders(stock_codes, report_date)
        return result
    except Exception as e:
        logger.error(f"获取十大股东失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 分红数据接口 ====================

@router.get("/dividend")
@log_api_call("获取分红数据")
async def get_dividend(codes: str = '', start_date: str = '', end_date: str = ''):
    """
    获取分红数据

    Args:
        codes: 股票代码，多个用逗号分隔
        start_date: 开始日期
        end_date: 结束日期
    """
    try:
        from backend.dataflows.announcement.cninfo_api import get_cninfo_api_client

        client = get_cninfo_api_client()
        stock_codes = [c.strip() for c in codes.split(',') if c.strip()] if codes else None

        result = await client.get_dividend(stock_codes, start_date, end_date)
        return result
    except Exception as e:
        logger.error(f"获取分红数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 公共数据接口 ====================

@router.get("/public/calendar")
@log_api_call("获取交易日历")
async def get_trade_calendar(start_date: str, end_date: str, market: str = 'SZ'):
    """
    获取交易日历

    Args:
        start_date: 开始日期 YYYY-MM-DD
        end_date: 结束日期 YYYY-MM-DD
        market: 市场 SZ/SH
    """
    try:
        from backend.dataflows.announcement.cninfo_api import get_cninfo_api_client

        client = get_cninfo_api_client()
        result = await client.get_trade_calendar(start_date, end_date, market)
        return result
    except Exception as e:
        logger.error(f"获取交易日历失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/public/industry")
@log_api_call("获取行业分类")
async def get_industry_classification(ind_code: str = '', ind_type: str = '137004'):
    """
    获取行业分类

    Args:
        ind_code: 行业代码
        ind_type: 分类标准 137002中上协/137004申万/137005新财富
    """
    try:
        from backend.dataflows.announcement.cninfo_api import get_cninfo_api_client

        client = get_cninfo_api_client()
        result = await client.get_industry_classification(ind_code, ind_type)
        return result
    except Exception as e:
        logger.error(f"获取行业分类失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
