"""
PDF报告生成API
提供股票分析报告的PDF导出功能
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime

from backend.utils.logging_config import get_logger
from backend.services.report.pdf_generator import pdf_generator

logger = get_logger("api.report")
router = APIRouter(prefix="/api/report", tags=["Report Generation"])


# ==================== 数据模型 ====================

class StockInfo(BaseModel):
    """股票信息"""
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    current_price: Optional[float] = None
    change_percent: Optional[float] = None
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    market_cap: Optional[float] = None
    industry: Optional[str] = None


class AgentAnalysis(BaseModel):
    """智能体分析结果"""
    agent_name: str
    agent_role: Optional[str] = None
    analysis: str


class DebateResult(BaseModel):
    """辩论结果"""
    bull_view: Optional[str] = None
    bear_view: Optional[str] = None
    conclusion: Optional[str] = None


class FinalDecision(BaseModel):
    """最终决策"""
    rating: str = Field(..., description="投资评级")
    operation_advice: Optional[str] = None
    target_price: Optional[float] = None
    entry_range: Optional[str] = None
    take_profit: Optional[float] = None
    stop_loss: Optional[float] = None
    holding_period: Optional[str] = None
    position_size: Optional[str] = None
    confidence_level: Optional[int] = None
    reason: Optional[str] = None
    risk_warning: Optional[str] = None


class GenerateReportRequest(BaseModel):
    """生成报告请求"""
    stock_info: Dict[str, Any]
    analysis_result: Optional[Dict[str, Any]] = None
    agents_analysis: Optional[List[Dict[str, Any]]] = None
    debate_result: Optional[Dict[str, Any]] = None
    final_decision: Optional[Dict[str, Any]] = None


class ReportResponse(BaseModel):
    """报告响应"""
    success: bool
    filename: str
    content_base64: str
    message: str


# ==================== API端点 ====================

@router.post("/generate-pdf", response_model=ReportResponse)
async def generate_pdf_report(request: GenerateReportRequest):
    """
    生成PDF分析报告

    Args:
        request: 包含股票信息和分析结果的请求

    Returns:
        Base64编码的PDF内容
    """
    try:
        logger.info(f"开始生成PDF报告: {request.stock_info.get('code', 'unknown')}")

        # 生成PDF
        pdf_base64 = pdf_generator.generate_base64(
            stock_info=request.stock_info,
            analysis_result=request.analysis_result or {},
            agents_analysis=request.agents_analysis,
            debate_result=request.debate_result,
            final_decision=request.final_decision
        )

        # 生成文件名
        stock_code = request.stock_info.get('code', request.stock_info.get('stock_code', 'unknown'))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"分析报告_{stock_code}_{timestamp}.pdf"

        logger.info(f"PDF报告生成成功: {filename}")

        return ReportResponse(
            success=True,
            filename=filename,
            content_base64=pdf_base64,
            message="PDF报告生成成功"
        )

    except Exception as e:
        logger.error(f"生成PDF报告失败: {e}")
        raise HTTPException(status_code=500, detail=f"生成PDF报告失败: {str(e)}")


@router.post("/download-pdf")
async def download_pdf_report(request: GenerateReportRequest):
    """
    直接下载PDF报告

    Args:
        request: 包含股票信息和分析结果的请求

    Returns:
        PDF文件流
    """
    try:
        logger.info(f"开始生成PDF下载: {request.stock_info.get('code', 'unknown')}")

        # 生成PDF
        pdf_content = pdf_generator.generate_analysis_report(
            stock_info=request.stock_info,
            analysis_result=request.analysis_result or {},
            agents_analysis=request.agents_analysis,
            debate_result=request.debate_result,
            final_decision=request.final_decision
        )

        # 生成文件名
        stock_code = request.stock_info.get('code', request.stock_info.get('stock_code', 'unknown'))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"分析报告_{stock_code}_{timestamp}.pdf"

        logger.info(f"PDF下载准备完成: {filename}")

        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{filename}"
            }
        )

    except Exception as e:
        logger.error(f"下载PDF报告失败: {e}")
        raise HTTPException(status_code=500, detail=f"下载PDF报告失败: {str(e)}")


@router.get("/test")
async def test_pdf_generation():
    """测试PDF生成功能"""
    try:
        # 测试数据
        test_stock_info = {
            "code": "600519",
            "name": "贵州茅台",
            "current_price": 1688.88,
            "change_percent": 2.35,
            "pe_ratio": 28.5,
            "pb_ratio": 8.2,
            "market_cap": 2120000000000,
            "industry": "白酒"
        }

        test_agents = [
            {
                "agent_name": "technical_analyst",
                "agent_role": "技术分析",
                "analysis": "从技术面来看，该股票处于上升趋势中，MACD金叉，KDJ指标显示超买..."
            },
            {
                "agent_name": "fundamental_analyst",
                "agent_role": "基本面分析",
                "analysis": "公司基本面良好，营收稳定增长，毛利率保持在90%以上..."
            }
        ]

        test_decision = {
            "rating": "买入",
            "operation_advice": "建议逢低买入",
            "target_price": 1800,
            "entry_range": "1650-1700",
            "take_profit": 1850,
            "stop_loss": 1600,
            "holding_period": "中长期(3-6个月)",
            "position_size": "20%",
            "confidence_level": 8,
            "reason": "公司基本面优秀，技术面向好，估值合理",
            "risk_warning": "注意市场系统性风险"
        }

        # 生成PDF
        pdf_base64 = pdf_generator.generate_base64(
            stock_info=test_stock_info,
            analysis_result={},
            agents_analysis=test_agents,
            debate_result=None,
            final_decision=test_decision
        )

        return {
            "success": True,
            "message": "PDF生成测试成功",
            "filename": "test_report.pdf",
            "content_length": len(pdf_base64)
        }

    except Exception as e:
        logger.error(f"PDF生成测试失败: {e}")
        raise HTTPException(status_code=500, detail=f"PDF生成测试失败: {str(e)}")
