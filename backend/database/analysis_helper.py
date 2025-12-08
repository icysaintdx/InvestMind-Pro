"""
分析流程数据库集成辅助函数
在分析过程中调用这些函数保存进度到数据库
"""

from typing import Optional, List, Dict, Any
from backend.database.database import get_db_context
from backend.database.services import (
    SessionService,
    AgentResultService,
    StockHistoryService
)


def save_agent_result(
    session_id: str,
    agent_id: str,
    agent_name: str,
    status: str,
    output: Optional[str] = None,
    tokens: Optional[int] = None,
    thoughts: Optional[List[Dict]] = None,
    data_sources: Optional[List[Dict]] = None,
    error_message: Optional[str] = None
):
    """
    保存智能体结果到数据库
    
    在每个智能体完成时调用此函数
    
    Args:
        session_id: 会话ID
        agent_id: 智能体ID（如 'news_analyst'）
        agent_name: 智能体名称（如 '新闻舆情分析师'）
        status: 状态（'running', 'completed', 'error'）
        output: 输出结果
        tokens: Token数量
        thoughts: 思维链
        data_sources: 数据源
        error_message: 错误信息
    """
    try:
        with get_db_context() as db:
            # 保存智能体结果
            AgentResultService.create_or_update_result(
                db=db,
                session_id=session_id,
                agent_id=agent_id,
                agent_name=agent_name,
                status=status,
                output=output,
                tokens=tokens,
                thoughts=thoughts,
                data_sources=data_sources,
                error_message=error_message
            )
            
            # 如果完成，更新会话进度
            if status == 'completed':
                completed_agents = AgentResultService.get_completed_agents(db, session_id)
                progress = int(len(completed_agents) / 21 * 100)
                
                # 计算当前阶段（简单估算）
                if len(completed_agents) <= 8:
                    current_stage = 1
                elif len(completed_agents) <= 13:
                    current_stage = 2
                elif len(completed_agents) <= 19:
                    current_stage = 3
                else:
                    current_stage = 4
                
                SessionService.update_session_status(
                    db=db,
                    session_id=session_id,
                    status="running",
                    progress=progress,
                    current_stage=current_stage
                )
                
                print(f"[数据库] 保存进度: {agent_id} 完成, 总进度 {progress}%")
    
    except Exception as e:
        print(f"[数据库] 保存智能体结果失败: {e}")


def complete_analysis(
    session_id: str,
    success: bool = True,
    error_message: Optional[str] = None
):
    """
    标记分析完成
    
    在整个分析流程结束时调用
    
    Args:
        session_id: 会话ID
        success: 是否成功
        error_message: 错误信息（如果失败）
    """
    try:
        with get_db_context() as db:
            SessionService.update_session_status(
                db=db,
                session_id=session_id,
                status="completed" if success else "error",
                progress=100 if success else None,
                error_message=error_message
            )
            
            print(f"[数据库] 分析{'成功' if success else '失败'}: {session_id}")
    
    except Exception as e:
        print(f"[数据库] 标记完成失败: {e}")


def get_agent_name_map():
    """获取智能体ID到名称的映射"""
    return {
        'news_analyst': '新闻舆情分析师',
        'social_analyst': '社交媒体分析师',
        'china_market': '中国市场专家',
        'industry': '行业轮动分析师',
        'macro': '宏观经济学家',
        'technical': '技术分析师',
        'funds': '资金流向分析师',
        'fundamental': '基本面分析师',
        'bull_researcher': '看涨研究员',
        'bear_researcher': '看跌研究员',
        'manager_fundamental': '基本面总监',
        'manager_momentum': '市场动能总监',
        'research_manager': '研究部经理',
        'risk_aggressive': '激进风控师',
        'risk_conservative': '保守风控师',
        'risk_neutral': '中立风控师',
        'risk_system': '系统性风险总监',
        'risk_portfolio': '组合风险总监',
        'risk_manager': '风控部经理',
        'gm': '投资决策总经理',
        'trader': '量化交易员',
        'interpreter': '白话解读员'
    }


# 使用示例
"""
在分析流程中使用：

# 1. 智能体开始运行
save_agent_result(
    session_id=session_id,
    agent_id='news_analyst',
    agent_name='新闻舆情分析师',
    status='running'
)

# 2. 智能体完成
save_agent_result(
    session_id=session_id,
    agent_id='news_analyst',
    agent_name='新闻舆情分析师',
    status='completed',
    output=result_text,
    tokens=1500,
    thoughts=[
        {'step': 1, 'content': '搜索相关新闻'},
        {'step': 2, 'content': '分析情绪倾向'}
    ],
    data_sources=[
        {'source': '东方财富', 'count': 5}
    ]
)

# 3. 分析完成
complete_analysis(session_id=session_id, success=True)
"""
