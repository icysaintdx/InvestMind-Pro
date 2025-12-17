"""
统一智能体注册表
管理所有智能体的注册、配置和调用
"""

from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field
from backend.utils.logging_config import get_logger

logger = get_logger("agent_registry")

class AgentType(Enum):
    """智能体类型"""
    ANALYST = "analyst"          # 分析师
    MANAGER = "manager"          # 管理者
    RISK = "risk"               # 风控
    RESEARCHER = "researcher"    # 研究员
    DEBATOR = "debator"         # 辩论者
    TRADER = "trader"           # 交易员
    EXECUTIVE = "executive"     # 高管

class AgentStage(Enum):
    """智能体阶段"""
    STAGE_1 = 1  # 第一阶段：数据分析
    STAGE_2 = 2  # 第二阶段：研究整合
    STAGE_3 = 3  # 第三阶段：风险评估
    STAGE_4 = 4  # 第四阶段：决策执行

class AgentPriority(Enum):
    """智能体优先级"""
    CORE = "core"              # 核心必需（不可禁用）
    IMPORTANT = "important"    # 重要增强（默认启用，可选禁用）
    OPTIONAL = "optional"      # 可选补充（默认禁用，可选启用）

@dataclass
class AgentConfig:
    """智能体配置"""
    id: str                     # 唯一标识
    name: str                   # 中文名称
    english_name: str           # 英文名称
    type: AgentType            # 类型
    stage: AgentStage          # 所属阶段
    icon: str                  # 图标
    color: str                 # 颜色主题
    description: str           # 描述
    module_path: Optional[str] = None  # Python模块路径
    api_endpoint: Optional[str] = None # API端点
    dependencies: Optional[List[str]] = field(default=None)  # 依赖的其他智能体
    priority: AgentPriority = AgentPriority.IMPORTANT  # 优先级
    is_active: bool = True            # 是否激活
    is_legacy: bool = False          # 是否为旧系统智能体

class AgentRegistry:
    """智能体注册表"""
    
    def __init__(self):
        self._agents: Dict[str, AgentConfig] = {}
        self._initialize_agents()
        
    def _initialize_agents(self):
        """初始化所有智能体配置"""
        
        # ============ 原InvestMind Pro 10个智能体 ============
        # 第一阶段：5个专业分析师
        self.register(AgentConfig(
            id="macro",
            name="宏观政策分析师",
            english_name="Macro Policy Analyst",
            type=AgentType.ANALYST,
            stage=AgentStage.STAGE_1,
            icon="🌍",
            color="slate",
            description="分析宏观经济政策、货币政策、财政政策对市场的影响",
            api_endpoint="/api/analyze",
            priority=AgentPriority.IMPORTANT,
            is_legacy=True
        ))
        
        self.register(AgentConfig(
            id="industry",
            name="行业轮动分析师",
            english_name="Industry Rotation Analyst",
            type=AgentType.ANALYST,
            stage=AgentStage.STAGE_1,
            icon="🏭",
            color="cyan",
            description="研究行业周期、板块轮动、产业链上下游关系",
            api_endpoint="/api/analyze",
            priority=AgentPriority.IMPORTANT,
            is_legacy=True
        ))
        
        self.register(AgentConfig(
            id="technical",
            name="技术分析专家",
            english_name="Technical Analysis Expert",
            type=AgentType.ANALYST,
            stage=AgentStage.STAGE_1,
            icon="📈",
            color="violet",
            description="运用技术指标、K线形态、趋势分析等方法预测价格走势",
            api_endpoint="/api/analyze",
            priority=AgentPriority.CORE,
            is_legacy=True
        ))
        
        self.register(AgentConfig(
            id="funds",
            name="资金流向分析师",
            english_name="Fund Flow Analyst",
            type=AgentType.ANALYST,
            stage=AgentStage.STAGE_1,
            icon="💰",
            color="emerald",
            description="追踪主力资金动向、北向资金、机构持仓变化",
            api_endpoint="/api/analyze",
            priority=AgentPriority.IMPORTANT,
            is_legacy=True
        ))
        
        self.register(AgentConfig(
            id="fundamental",
            name="基本面估值分析师",
            english_name="Fundamental Valuation Analyst",
            type=AgentType.ANALYST,
            stage=AgentStage.STAGE_1,
            icon="💼",
            color="blue",
            description="分析财务报表、估值模型、公司基本面",
            api_endpoint="/api/analyze",
            priority=AgentPriority.CORE,
            is_legacy=True
        ))
        
        # 第二阶段：2个经理
        self.register(AgentConfig(
            id="manager_fundamental",
            name="基本面研究总监",
            english_name="Fundamental Research Manager",
            type=AgentType.MANAGER,
            stage=AgentStage.STAGE_2,
            icon="👔",
            color="indigo",
            description="整合基本面相关分析，形成价值投资观点",
            api_endpoint="/api/analyze",
            dependencies=["fundamental", "macro", "industry"],
            priority=AgentPriority.IMPORTANT,
            is_legacy=True
        ))
        
        self.register(AgentConfig(
            id="manager_momentum",
            name="市场动能总监",
            english_name="Market Momentum Manager",
            type=AgentType.MANAGER,
            stage=AgentStage.STAGE_2,
            icon="🎯",
            color="amber",
            description="整合技术面和资金面分析，判断市场动能",
            api_endpoint="/api/analyze",
            dependencies=["technical", "funds"],
            priority=AgentPriority.OPTIONAL,
            is_legacy=True
        ))
        
        # 第三阶段：2个风控
        self.register(AgentConfig(
            id="risk_system",
            name="系统性风险总监",
            english_name="Systematic Risk Director",
            type=AgentType.RISK,
            stage=AgentStage.STAGE_3,
            icon="🛡️",
            color="red",
            description="评估系统性风险、市场风险、政策风险",
            api_endpoint="/api/analyze",
            dependencies=["manager_fundamental", "manager_momentum"],
            priority=AgentPriority.OPTIONAL,
            is_legacy=True
        ))
        
        self.register(AgentConfig(
            id="risk_portfolio",
            name="组合风险总监",
            english_name="Portfolio Risk Director",
            type=AgentType.RISK,
            stage=AgentStage.STAGE_3,
            icon="⚖️",
            color="orange",
            description="管理组合风险、仓位配置、风险敞口",
            api_endpoint="/api/analyze",
            dependencies=["manager_fundamental", "manager_momentum"],
            priority=AgentPriority.OPTIONAL,
            is_legacy=True
        ))
        
        # 第四阶段：1个总经理
        self.register(AgentConfig(
            id="gm",
            name="投资决策总经理",
            english_name="Investment Decision GM",
            type=AgentType.EXECUTIVE,
            stage=AgentStage.STAGE_4,
            icon="👨‍💼",
            color="purple",
            description="综合所有分析，做出最终投资决策",
            api_endpoint="/api/analyze",
            dependencies=["risk_system", "risk_portfolio"],
            priority=AgentPriority.CORE,
            is_legacy=True
        ))
        
        # ============ 新增TradingAgents-CN智能体 ============
        # 新增分析师
        self.register(AgentConfig(
            id="news_analyst",
            name="新闻舆情分析师",
            english_name="News Sentiment Analyst",
            type=AgentType.ANALYST,
            stage=AgentStage.STAGE_1,
            icon="📰",
            color="teal",
            description="分析新闻舆情、市场情绪、热点事件影响",
            module_path="backend.agents.analysts.news_analyst",
            api_endpoint="/api/news/analyze",
            priority=AgentPriority.CORE
        ))
        
        self.register(AgentConfig(
            id="social_analyst",
            name="社交媒体分析师",
            english_name="Social Media Analyst",
            type=AgentType.ANALYST,
            stage=AgentStage.STAGE_1,
            icon="🗣️",
            color="cyan",
            description="监控社交媒体动态、投资者情绪、市场热度",
            module_path="backend.agents.analysts.social_media_analyst",
            api_endpoint="/api/social/analyze",
            priority=AgentPriority.OPTIONAL
        ))

        self.register(AgentConfig(
            id="china_market",
            name="中国市场专家",
            english_name="China Market Specialist",
            type=AgentType.ANALYST,
            stage=AgentStage.STAGE_1,
            icon="🇨🇳",
            color="red",
            description="专注A股市场特性、政策解读、中国特色分析",
            module_path="backend.agents.analysts.china_market_analyst",
            api_endpoint="/api/china/analyze",
            priority=AgentPriority.OPTIONAL
        ))
        
        # 研究员（辩论层）
        self.register(AgentConfig(
            id="bull_researcher",
            name="看涨研究员",
            english_name="Bull Researcher",
            type=AgentType.RESEARCHER,
            stage=AgentStage.STAGE_2,
            icon="🐂",
            color="green",
            description="从乐观角度分析，寻找上涨理由和机会",
            module_path="backend.agents.researchers.bull_researcher",
            api_endpoint="/api/debate/research",
            dependencies=["news_analyst", "fundamental", "technical"],
            priority=AgentPriority.CORE
        ))
        
        self.register(AgentConfig(
            id="bear_researcher",
            name="看跌研究员",
            english_name="Bear Researcher",
            type=AgentType.RESEARCHER,
            stage=AgentStage.STAGE_2,
            icon="🐻",
            color="red",
            description="从谨慎角度分析，识别下跌风险和问题",
            module_path="backend.agents.researchers.bear_researcher",
            api_endpoint="/api/debate/research",
            dependencies=["news_analyst", "fundamental", "technical"],
            priority=AgentPriority.CORE
        ))
        
        # 风控辩论员
        self.register(AgentConfig(
            id="risk_aggressive",
            name="激进风控师",
            english_name="Aggressive Risk Debator",
            type=AgentType.DEBATOR,
            stage=AgentStage.STAGE_3,
            icon="⚔️",
            color="orange",
            description="倾向高风险高收益策略，追求超额收益",
            module_path="backend.agents.risk_mgmt.aggresive_debator",
            api_endpoint="/api/debate/risk",
            priority=AgentPriority.IMPORTANT
        ))

        self.register(AgentConfig(
            id="risk_conservative",
            name="保守风控师",
            english_name="Conservative Risk Debator",
            type=AgentType.DEBATOR,
            stage=AgentStage.STAGE_3,
            icon="🛡️",
            color="slate",
            description="注重风险控制，追求稳健收益",
            module_path="backend.agents.risk_mgmt.conservative_debator",
            api_endpoint="/api/debate/risk",
            priority=AgentPriority.IMPORTANT
        ))

        self.register(AgentConfig(
            id="risk_neutral",
            name="中立风控师",
            english_name="Neutral Risk Debator",
            type=AgentType.DEBATOR,
            stage=AgentStage.STAGE_3,
            icon="⚖️",
            color="blue",
            description="平衡风险与收益，寻求最优配置",
            module_path="backend.agents.risk_mgmt.neutral_debator",
            api_endpoint="/api/debate/risk",
            priority=AgentPriority.IMPORTANT
        ))
        
        # 新增管理者
        self.register(AgentConfig(
            id="research_manager",
            name="研究经理",
            english_name="Research Manager",
            type=AgentType.MANAGER,
            stage=AgentStage.STAGE_2,
            icon="📊",
            color="indigo",
            description="整合多空观点，形成研究结论",
            module_path="backend.agents.managers.research_manager",
            api_endpoint="/api/debate/research",
            dependencies=["bull_researcher", "bear_researcher"],
            priority=AgentPriority.CORE
        ))
        
        self.register(AgentConfig(
            id="risk_manager",
            name="风控部经理",
            english_name="Risk Manager",
            type=AgentType.MANAGER,
            stage=AgentStage.STAGE_3,
            icon="👮",
            color="indigo",
            description="综合风险评估，制定风控策略",
            module_path="backend.agents.managers.risk_manager",
            api_endpoint="/api/debate/risk",
            dependencies=["risk_aggressive", "risk_conservative", "risk_neutral"],
            priority=AgentPriority.CORE
        ))

        # 交易员
        self.register(AgentConfig(
            id="trader",
            name="量化交易员",
            english_name="Quantitative Trader",
            type=AgentType.TRADER,
            stage=AgentStage.STAGE_4,
            icon="🤖",
            color="cyan",
            description="执行交易策略，生成交易信号和订单",
            module_path="backend.agents.trader.trader",
            api_endpoint="/api/trading/execute",
            dependencies=["gm", "risk_manager"],
            priority=AgentPriority.CORE
        ))

        # 注意：interpreter（白话解读员）不在此注册
        # 它是嵌入在 GM（投资决策总经理）卡片中的功能，不作为独立智能体配置
        
    def register(self, config: AgentConfig):
        """注册智能体"""
        self._agents[config.id] = config
        logger.info(f"注册智能体: {config.name} ({config.id})")
        
    def get_agent(self, agent_id: str) -> Optional[AgentConfig]:
        """获取智能体配置"""
        return self._agents.get(agent_id)
        
    def get_agents_by_type(self, agent_type: AgentType) -> List[AgentConfig]:
        """按类型获取智能体列表"""
        return [a for a in self._agents.values() if a.type == agent_type]
        
    def get_agents_by_stage(self, stage: AgentStage) -> List[AgentConfig]:
        """按阶段获取智能体列表"""
        return [a for a in self._agents.values() if a.stage == stage]
        
    def get_all_agents(self) -> Dict[str, AgentConfig]:
        """获取所有智能体"""
        return self._agents.copy()
        
    def get_active_agents(self) -> List[AgentConfig]:
        """获取激活的智能体"""
        return [a for a in self._agents.values() if a.is_active]
        
    def get_legacy_agents(self) -> List[AgentConfig]:
        """获取旧系统智能体"""
        return [a for a in self._agents.values() if a.is_legacy]
        
    def get_new_agents(self) -> List[AgentConfig]:
        """获取新系统智能体"""
        return [a for a in self._agents.values() if not a.is_legacy]
        
    def get_agent_dependencies(self, agent_id: str) -> List[AgentConfig]:
        """获取智能体依赖"""
        agent = self.get_agent(agent_id)
        if not agent or not agent.dependencies:
            return []
        return [self.get_agent(dep_id) for dep_id in agent.dependencies if self.get_agent(dep_id)]
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（用于API返回）"""
        result = {
            "total": len(self._agents),
            "legacy_count": len(self.get_legacy_agents()),
            "new_count": len(self.get_new_agents()),
            "by_stage": {},
            "by_type": {},
            "agents": {}
        }
        
        # 按阶段分组
        for stage in AgentStage:
            agents = self.get_agents_by_stage(stage)
            result["by_stage"][stage.value] = [a.id for a in agents]
            
        # 按类型分组
        for agent_type in AgentType:
            agents = self.get_agents_by_type(agent_type)
            result["by_type"][agent_type.value] = [a.id for a in agents]
            
        # 所有智能体详情
        for agent_id, agent in self._agents.items():
            result["agents"][agent_id] = {
                "name": agent.name,
                "english_name": agent.english_name,
                "type": agent.type.value,
                "stage": agent.stage.value,
                "icon": agent.icon,
                "color": agent.color,
                "description": agent.description,
                "is_active": agent.is_active,
                "is_legacy": agent.is_legacy,
                "api_endpoint": agent.api_endpoint,
                "dependencies": agent.dependencies or []
            }
            
        return result


# 全局注册表实例
agent_registry = AgentRegistry()

def get_registry() -> AgentRegistry:
    """获取全局注册表"""
    return agent_registry
