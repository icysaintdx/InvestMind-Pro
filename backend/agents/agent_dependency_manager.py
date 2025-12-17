"""
智能体依赖管理器
处理智能体之间的依赖关系、启用/禁用逻辑、降级方案
"""

from typing import Dict, List, Set, Optional, Tuple
from backend.agents.agent_registry import get_registry, AgentConfig, AgentPriority
from backend.utils.logging_config import get_logger

logger = get_logger("agent_dependency")


class DependencyCheckResult:
    """依赖检查结果"""
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.can_enable = True
        self.can_disable = True
        self.missing_deps: List[str] = []
        self.optional_deps: List[str] = []
        self.affected_agents: List[str] = []
        self.warnings: List[str] = []
        self.degradation_message: Optional[str] = None
        
    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "can_enable": self.can_enable,
            "can_disable": self.can_disable,
            "missing_deps": self.missing_deps,
            "optional_deps": self.optional_deps,
            "affected_agents": self.affected_agents,
            "warnings": self.warnings,
            "degradation_message": self.degradation_message
        }


class AgentDependencyManager:
    """智能体依赖管理器"""
    
    def __init__(self):
        self.registry = get_registry()
        
        # 降级方案配置
        self.degradation_strategies = {
            'china_market_analyst': {
                'fallback': None,
                'message': 'macro将使用通用市场分析代替中国市场专项分析'
            },
            'social_media_analyst': {
                'fallback': 'news_analyst',
                'message': 'industry将仅依赖新闻分析，不含社交媒体情绪'
            },
            'manager_momentum': {
                'fallback': None,
                'message': '风险评估将缺少动能分析维度'
            },
            'risk_system': {
                'fallback': 'risk_portfolio',
                'message': '系统性风险将由组合风险分析覆盖'
            },
            'risk_portfolio': {
                'fallback': 'risk_system',
                'message': '组合风险将由系统性风险分析覆盖'
            },
            'interpreter': {
                'fallback': None,
                'message': '将不生成白话解读，仅保留专业分析报告'
            }
        }
    
    def get_full_dependencies(self, agent_id: str, visited: Optional[Set[str]] = None) -> Set[str]:
        """
        获取智能体的完整依赖链（递归）
        
        Args:
            agent_id: 智能体ID
            visited: 已访问的智能体集合（避免循环依赖）
            
        Returns:
            所有依赖的智能体ID集合
        """
        if visited is None:
            visited = set()
            
        if agent_id in visited:
            return set()
            
        visited.add(agent_id)
        deps = set()
        
        agent = self.registry.get_agent(agent_id)
        if not agent or not agent.dependencies:
            return deps
            
        for dep_id in agent.dependencies:
            deps.add(dep_id)
            # 递归获取依赖的依赖
            sub_deps = self.get_full_dependencies(dep_id, visited)
            deps.update(sub_deps)
            
        return deps
    
    def find_dependents(self, agent_id: str) -> List[str]:
        """
        查找依赖于指定智能体的其他智能体
        
        Args:
            agent_id: 智能体ID
            
        Returns:
            依赖此智能体的智能体ID列表
        """
        dependents = []
        for agent in self.registry.get_all_agents().values():
            if agent.dependencies and agent_id in agent.dependencies:
                dependents.append(agent.id)
        return dependents
    
    def check_enable(self, agent_id: str, current_config: Dict[str, bool]) -> DependencyCheckResult:
        """
        检查是否可以启用智能体
        
        Args:
            agent_id: 要启用的智能体ID
            current_config: 当前配置状态
            
        Returns:
            检查结果
        """
        result = DependencyCheckResult(agent_id)
        agent = self.registry.get_agent(agent_id)
        
        if not agent:
            result.can_enable = False
            result.warnings.append(f"智能体 {agent_id} 不存在")
            return result
        
        # 检查依赖
        if agent.dependencies:
            for dep_id in agent.dependencies:
                dep_agent = self.registry.get_agent(dep_id)
                if not dep_agent:
                    continue
                    
                # 检查依赖是否启用
                if not current_config.get(dep_id, False):
                    if dep_agent.priority == AgentPriority.CORE:
                        result.missing_deps.append(dep_id)
                        result.can_enable = False
                        result.warnings.append(
                            f"核心依赖 {dep_agent.name} 未启用，必须先启用"
                        )
                    else:
                        result.optional_deps.append(dep_id)
                        result.warnings.append(
                            f"建议启用 {dep_agent.name} 以获得最佳效果"
                        )
        
        return result
    
    def check_disable(self, agent_id: str, current_config: Dict[str, bool]) -> DependencyCheckResult:
        """
        检查是否可以禁用智能体
        
        Args:
            agent_id: 要禁用的智能体ID
            current_config: 当前配置状态
            
        Returns:
            检查结果
        """
        result = DependencyCheckResult(agent_id)
        agent = self.registry.get_agent(agent_id)
        
        if not agent:
            result.can_disable = False
            result.warnings.append(f"智能体 {agent_id} 不存在")
            return result
        
        # 核心智能体不允许禁用
        if agent.priority == AgentPriority.CORE:
            result.can_disable = False
            result.warnings.append(f"{agent.name} 是核心智能体，不允许禁用")
            return result
        
        # 检查是否有启用的智能体依赖此智能体
        dependents = self.find_dependents(agent_id)
        active_dependents = [d for d in dependents if current_config.get(d, False)]
        
        if active_dependents:
            result.affected_agents = active_dependents
            
            # 检查是否有降级方案
            if agent_id in self.degradation_strategies:
                strategy = self.degradation_strategies[agent_id]
                result.degradation_message = strategy['message']
                
                # 如果有fallback且fallback已启用，则可以禁用
                if strategy['fallback'] and current_config.get(strategy['fallback'], False):
                    result.warnings.append(
                        f"禁用后将影响 {', '.join(active_dependents)}，"
                        f"但可由 {strategy['fallback']} 提供替代功能"
                    )
                else:
                    result.warnings.append(
                        f"禁用后将影响 {', '.join(active_dependents)}。{strategy['message']}"
                    )
            else:
                result.warnings.append(
                    f"禁用 {agent.name} 可能影响 {', '.join(active_dependents)} 的分析质量"
                )
        
        return result
    
    def auto_enable_dependencies(self, agent_id: str, current_config: Dict[str, bool]) -> Dict[str, bool]:
        """
        自动启用必需的依赖
        
        Args:
            agent_id: 智能体ID
            current_config: 当前配置
            
        Returns:
            更新后的配置
        """
        new_config = current_config.copy()
        new_config[agent_id] = True
        
        # 获取所有依赖
        deps = self.get_full_dependencies(agent_id)
        
        # 自动启用核心依赖
        for dep_id in deps:
            dep_agent = self.registry.get_agent(dep_id)
            if dep_agent and dep_agent.priority == AgentPriority.CORE:
                new_config[dep_id] = True
                logger.info(f"自动启用核心依赖: {dep_agent.name}")
        
        return new_config
    
    def get_config_impact(self, config: Dict[str, bool]) -> Dict:
        """
        计算配置的影响
        
        Args:
            config: 智能体配置
            
        Returns:
            影响分析结果
        """
        # 基础时间成本（秒）
        time_costs = {
            AgentPriority.CORE: 5,
            AgentPriority.IMPORTANT: 3,
            AgentPriority.OPTIONAL: 2
        }
        
        total_time = 0
        total_cost = 0
        quality_score = 100
        enabled_count = 0
        
        for agent_id, is_enabled in config.items():
            agent = self.registry.get_agent(agent_id)
            if not agent:
                continue
                
            if is_enabled:
                enabled_count += 1
                total_time += time_costs.get(agent.priority, 3)
                total_cost += 1
            else:
                # 禁用智能体的质量影响
                if agent.priority == AgentPriority.IMPORTANT:
                    quality_score -= 5
                elif agent.priority == AgentPriority.OPTIONAL:
                    quality_score -= 2
        
        return {
            "enabled_count": enabled_count,
            "total_agents": len(config),
            "estimated_time": total_time,
            "estimated_cost": total_cost,
            "quality_score": max(0, quality_score),
            "efficiency_ratio": round(quality_score / max(total_time, 1), 2)
        }
    
    def validate_config(self, config: Dict[str, bool]) -> Tuple[bool, List[DependencyCheckResult]]:
        """
        验证配置的合法性
        
        Args:
            config: 智能体配置
            
        Returns:
            (是否合法, 检查结果列表)
        """
        results = []
        all_valid = True
        
        for agent_id, is_enabled in config.items():
            if not is_enabled:
                continue
                
            check_result = self.check_enable(agent_id, config)
            results.append(check_result)
            
            if not check_result.can_enable:
                all_valid = False
        
        return all_valid, results


# 全局单例
_dependency_manager = None

def get_dependency_manager() -> AgentDependencyManager:
    """获取依赖管理器单例"""
    global _dependency_manager
    if _dependency_manager is None:
        _dependency_manager = AgentDependencyManager()
    return _dependency_manager
