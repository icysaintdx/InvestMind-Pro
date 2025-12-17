"""
模拟交易 API
提供模拟账户管理、下单、持仓查询等功能
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

# 创建路由
router = APIRouter(prefix="/api/paper-trading", tags=["paper_trading"])


# ==================== 数据模型 ====================

class CreateAccountRequest(BaseModel):
    """创建模拟账户请求"""
    initial_capital: float = Field(100000, description="初始资金")
    account_name: str = Field("我的模拟账户", description="账户名称")


class PlaceOrderRequest(BaseModel):
    """下单请求"""
    account_id: str
    stock_code: str
    side: str = Field(..., description="买卖方向: buy/sell")
    quantity: int = Field(..., description="数量")
    price: Optional[float] = Field(None, description="价格（None为市价）")
    order_type: str = Field("market", description="订单类型: market/limit")


class Account(BaseModel):
    """模拟账户"""
    account_id: str
    account_name: str
    initial_capital: float
    available_cash: float
    total_assets: float
    total_profit: float
    profit_rate: float
    created_at: str
    updated_at: str


class Position(BaseModel):
    """持仓"""
    stock_code: str
    stock_name: str
    quantity: int
    avg_cost: float
    current_price: float
    market_value: float
    profit: float
    profit_rate: float


class Order(BaseModel):
    """订单"""
    order_id: str
    account_id: str
    stock_code: str
    side: str
    order_type: str
    quantity: int
    price: Optional[float]
    status: str  # pending, filled, cancelled
    filled_quantity: int
    filled_price: Optional[float]
    commission: float
    created_at: str
    filled_at: Optional[str]


# ==================== 内存存储（实际应用应使用数据库） ====================

# 存储账户
accounts: Dict[str, Dict] = {}

# 存储持仓
positions: Dict[str, List[Dict]] = {}  # account_id -> [position]

# 存储订单
orders: Dict[str, List[Dict]] = {}  # account_id -> [order]

# 存储交易记录
trades: Dict[str, List[Dict]] = {}  # account_id -> [trade]


# ==================== API端点 ====================

@router.post("/account/create")
async def create_account(request: CreateAccountRequest):
    """
    创建模拟账户
    
    Args:
        request: 创建账户请求
        
    Returns:
        账户信息
    """
    try:
        account_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        account = {
            "account_id": account_id,
            "account_name": request.account_name,
            "initial_capital": request.initial_capital,
            "available_cash": request.initial_capital,
            "total_assets": request.initial_capital,
            "total_profit": 0,
            "profit_rate": 0,
            "created_at": now,
            "updated_at": now
        }
        
        accounts[account_id] = account
        positions[account_id] = []
        orders[account_id] = []
        trades[account_id] = []
        
        logger.info(f"创建模拟账户: {account_id}")
        
        return {
            "success": True,
            "account": account
        }
        
    except Exception as e:
        logger.error(f"创建账户失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accounts")
async def list_accounts():
    """
    获取所有模拟账户列表
    
    Returns:
        账户列表
    """
    try:
        return {
            "success": True,
            "accounts": list(accounts.values()),
            "total": len(accounts)
        }
    except Exception as e:
        logger.error(f"获取账户列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/account/{account_id}")
async def get_account(account_id: str):
    """
    获取账户详情
    
    Args:
        account_id: 账户ID
        
    Returns:
        账户详细信息
    """
    try:
        if account_id not in accounts:
            raise HTTPException(status_code=404, detail="账户不存在")
        
        account = accounts[account_id]
        account_positions = positions.get(account_id, [])
        
        # 更新账户总资产
        total_market_value = sum(p["market_value"] for p in account_positions)
        account["total_assets"] = account["available_cash"] + total_market_value
        account["total_profit"] = account["total_assets"] - account["initial_capital"]
        account["profit_rate"] = account["total_profit"] / account["initial_capital"]
        account["updated_at"] = datetime.now().isoformat()
        
        return {
            "success": True,
            "account": account,
            "positions": account_positions,
            "position_count": len(account_positions)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取账户详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/account/{account_id}/positions")
async def get_positions(account_id: str):
    """
    获取持仓列表
    
    Args:
        account_id: 账户ID
        
    Returns:
        持仓列表
    """
    try:
        if account_id not in accounts:
            raise HTTPException(status_code=404, detail="账户不存在")
        
        account_positions = positions.get(account_id, [])
        
        return {
            "success": True,
            "positions": account_positions,
            "total": len(account_positions)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取持仓失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/order/place")
async def place_order(request: PlaceOrderRequest):
    """
    下单
    
    Args:
        request: 下单请求
        
    Returns:
        订单信息
    """
    try:
        if request.account_id not in accounts:
            raise HTTPException(status_code=404, detail="账户不存在")
        
        account = accounts[request.account_id]
        
        # 模拟获取当前价格（实际应该调用行情API）
        current_price = request.price if request.price else 100.0
        
        # 计算订单金额
        order_amount = current_price * request.quantity
        commission = order_amount * 0.0003  # 0.03%手续费
        
        # 检查资金
        if request.side == "buy":
            required_cash = order_amount + commission
            if account["available_cash"] < required_cash:
                raise HTTPException(status_code=400, detail="可用资金不足")
        
        # 创建订单
        order_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        order = {
            "order_id": order_id,
            "account_id": request.account_id,
            "stock_code": request.stock_code,
            "side": request.side,
            "order_type": request.order_type,
            "quantity": request.quantity,
            "price": request.price,
            "status": "filled",  # 模拟立即成交
            "filled_quantity": request.quantity,
            "filled_price": current_price,
            "commission": commission,
            "created_at": now,
            "filled_at": now
        }
        
        # 保存订单
        if request.account_id not in orders:
            orders[request.account_id] = []
        orders[request.account_id].append(order)
        
        # 更新账户和持仓
        if request.side == "buy":
            # 买入
            account["available_cash"] -= (order_amount + commission)
            
            # 更新持仓
            account_positions = positions.get(request.account_id, [])
            existing_position = next((p for p in account_positions if p["stock_code"] == request.stock_code), None)
            
            if existing_position:
                # 更新现有持仓
                total_cost = existing_position["avg_cost"] * existing_position["quantity"] + order_amount
                total_quantity = existing_position["quantity"] + request.quantity
                existing_position["quantity"] = total_quantity
                existing_position["avg_cost"] = total_cost / total_quantity
                existing_position["market_value"] = current_price * total_quantity
                existing_position["profit"] = existing_position["market_value"] - total_cost
                existing_position["profit_rate"] = existing_position["profit"] / total_cost
            else:
                # 新建持仓
                new_position = {
                    "stock_code": request.stock_code,
                    "stock_name": request.stock_code,  # 实际应该查询股票名称
                    "quantity": request.quantity,
                    "avg_cost": current_price,
                    "current_price": current_price,
                    "market_value": order_amount,
                    "profit": 0,
                    "profit_rate": 0
                }
                account_positions.append(new_position)
                positions[request.account_id] = account_positions
        
        else:
            # 卖出
            account["available_cash"] += (order_amount - commission)
            
            # 更新持仓
            account_positions = positions.get(request.account_id, [])
            existing_position = next((p for p in account_positions if p["stock_code"] == request.stock_code), None)
            
            if existing_position:
                existing_position["quantity"] -= request.quantity
                if existing_position["quantity"] <= 0:
                    account_positions.remove(existing_position)
                else:
                    existing_position["market_value"] = current_price * existing_position["quantity"]
                    existing_position["profit"] = existing_position["market_value"] - (existing_position["avg_cost"] * existing_position["quantity"])
                    existing_position["profit_rate"] = existing_position["profit"] / (existing_position["avg_cost"] * existing_position["quantity"])
        
        # 记录交易
        trade = {
            "trade_id": str(uuid.uuid4()),
            "order_id": order_id,
            "account_id": request.account_id,
            "stock_code": request.stock_code,
            "side": request.side,
            "quantity": request.quantity,
            "price": current_price,
            "amount": order_amount,
            "commission": commission,
            "timestamp": now
        }
        
        if request.account_id not in trades:
            trades[request.account_id] = []
        trades[request.account_id].append(trade)
        
        logger.info(f"下单成功: {order_id}")
        
        return {
            "success": True,
            "order": order,
            "trade": trade
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下单失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/account/{account_id}/orders")
async def get_orders(account_id: str, limit: int = 50):
    """
    获取订单列表
    
    Args:
        account_id: 账户ID
        limit: 返回数量限制
        
    Returns:
        订单列表
    """
    try:
        if account_id not in accounts:
            raise HTTPException(status_code=404, detail="账户不存在")
        
        account_orders = orders.get(account_id, [])
        
        return {
            "success": True,
            "orders": account_orders[-limit:],
            "total": len(account_orders)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取订单列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/account/{account_id}/trades")
async def get_trades(account_id: str, limit: int = 50):
    """
    获取交易记录
    
    Args:
        account_id: 账户ID
        limit: 返回数量限制
        
    Returns:
        交易记录列表
    """
    try:
        if account_id not in accounts:
            raise HTTPException(status_code=404, detail="账户不存在")
        
        account_trades = trades.get(account_id, [])
        
        return {
            "success": True,
            "trades": account_trades[-limit:],
            "total": len(account_trades)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取交易记录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/account/{account_id}")
async def delete_account(account_id: str):
    """
    删除模拟账户
    
    Args:
        account_id: 账户ID
        
    Returns:
        删除结果
    """
    try:
        if account_id not in accounts:
            raise HTTPException(status_code=404, detail="账户不存在")
        
        del accounts[account_id]
        if account_id in positions:
            del positions[account_id]
        if account_id in orders:
            del orders[account_id]
        if account_id in trades:
            del trades[account_id]
        
        logger.info(f"删除模拟账户: {account_id}")
        
        return {
            "success": True,
            "message": "账户已删除"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除账户失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
