"""配置API路由"""

from fastapi import APIRouter
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

router = APIRouter(prefix="/api", tags=["Config"])

@router.get("/config")
async def get_config():
    """获取系统配置"""
    
    # 检查环境变量中的API密钥
    config = {
        "api_keys": {},
        "model_configs": [],
        "backend_status": "running"
    }
    
    # 检查各个API密钥
    if os.getenv("GEMINI_API_KEY"):
        config["api_keys"]["gemini"] = "configured"
        config["GEMINI_API_KEY"] = "configured"
    
    if os.getenv("DEEPSEEK_API_KEY"):
        config["api_keys"]["deepseek"] = "configured"
        config["DEEPSEEK_API_KEY"] = "configured"
    
    if os.getenv("DASHSCOPE_API_KEY"):
        config["api_keys"]["qwen"] = "configured"
        config["DASHSCOPE_API_KEY"] = "configured"
        
    if os.getenv("SILICONFLOW_API_KEY"):
        config["api_keys"]["siliconflow"] = "configured"
        config["SILICONFLOW_API_KEY"] = "configured"
        
    if os.getenv("JUHE_API_KEY"):
        config["api_keys"]["juhe"] = "configured"
        config["JUHE_API_KEY"] = "configured"
    
    # 默认模型配置
    config["model_configs"] = [
        {"id": "macro", "model_name": "gemini-2.0-flash-exp", "temperature": 0.3},
        {"id": "industry", "model_name": "deepseek-chat", "temperature": 0.3},
        {"id": "technical", "model_name": "qwen-plus", "temperature": 0.2},
        {"id": "funds", "model_name": "Qwen/Qwen2.5-7B-Instruct", "temperature": 0.2},
        {"id": "fundamental", "model_name": "deepseek-chat", "temperature": 0.3},
        {"id": "manager_fundamental", "model_name": "gemini-2.0-flash-exp", "temperature": 0.4},
        {"id": "manager_momentum", "model_name": "deepseek-chat", "temperature": 0.4},
        {"id": "risk_system", "model_name": "qwen-plus", "temperature": 0.2},
        {"id": "risk_portfolio", "model_name": "Qwen/Qwen2.5-7B-Instruct", "temperature": 0.2},
        {"id": "gm", "model_name": "gemini-2.0-flash-exp", "temperature": 0.5}
    ]
    
    return config
