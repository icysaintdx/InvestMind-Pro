"""
动态API提供商管理 - FastAPI路由
提供提供商的增删改查、模型检测、连通性测试接口
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

from backend.utils.logging_config import get_logger

logger = get_logger("api.api_provider")
router = APIRouter(prefix="/api/api-providers", tags=["API Provider Management"])


# ==================== 请求模型 ====================


class ProviderCreate(BaseModel):
    """创建提供商请求"""
    name: str = Field(..., description="提供商名称")
    base_url: str = Field(..., description="API基础URL")
    api_key: str = Field(..., description="API密钥")
    sdk_type: str = Field("openai", description="SDK类型: openai/anthropic/google")
    models: List[str] = Field(default_factory=list, description="可用模型列表")
    enabled: bool = Field(True, description="是否启用")
    priority: int = Field(0, description="优先级（越大越优先）")


class ProviderUpdate(BaseModel):
    """更新提供商请求"""
    name: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    sdk_type: Optional[str] = None
    models: Optional[List[str]] = None
    enabled: Optional[bool] = None
    priority: Optional[int] = None


# ==================== CRUD 端点 ====================


@router.get("")
async def get_providers():
    """列出所有已配置的API提供商"""
    try:
        from backend.services.api_provider_service import list_providers
        providers = list_providers()
        return {
            "success": True,
            "count": len(providers),
            "providers": providers,
        }
    except Exception as e:
        logger.error(f"获取提供商列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
async def create_provider(body: ProviderCreate):
    """添加新的API提供商"""
    try:
        from backend.services.api_provider_service import add_provider
        provider = add_provider(body.model_dump())
        return {"success": True, "provider": provider}
    except Exception as e:
        logger.error(f"添加提供商失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{provider_id}")
async def get_provider_detail(provider_id: int):
    """获取单个提供商详情"""
    try:
        from backend.services.api_provider_service import get_provider
        provider = get_provider(provider_id)
        if not provider:
            raise HTTPException(status_code=404, detail="提供商不存在")
        return {"success": True, "provider": provider}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取提供商详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{provider_id}")
async def update_provider_endpoint(provider_id: int, body: ProviderUpdate):
    """修改提供商配置"""
    try:
        from backend.services.api_provider_service import update_provider
        update_data = {k: v for k, v in body.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="没有提供要更新的字段")
        provider = update_provider(provider_id, update_data)
        if not provider:
            raise HTTPException(status_code=404, detail="提供商不存在")
        return {"success": True, "provider": provider}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新提供商失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{provider_id}")
async def delete_provider_endpoint(provider_id: int):
    """删除提供商"""
    try:
        from backend.services.api_provider_service import delete_provider
        deleted = delete_provider(provider_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="提供商不存在")
        return {"success": True, "message": "提供商已删除"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除提供商失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 功能端点 ====================


@router.post("/{provider_id}/detect-models")
async def detect_models_endpoint(provider_id: int):
    """自动检测提供商可用模型（调用 /v1/models 端点）"""
    try:
        from backend.services.api_provider_service import detect_models
        result = await detect_models(provider_id)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"检测模型失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{provider_id}/test")
async def test_connection_endpoint(provider_id: int):
    """测试提供商连通性"""
    try:
        from backend.services.api_provider_service import test_connection
        result = await test_connection(provider_id)
        return result
    except Exception as e:
        logger.error(f"测试连通性失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
