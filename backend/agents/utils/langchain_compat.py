"""
LangChain兼容层
提供LangChain组件的简化替代实现
"""

from typing import List, Dict, Any, Optional, Callable
import functools

# 导入日志
from backend.utils.logging_config import get_logger
logger = get_logger('langchain_compat')

# ============= 消息类 =============
class BaseMessage:
    """基础消息类"""
    def __init__(self, content: str, **kwargs):
        self.content = content
        self.id = kwargs.get('id', None)
        self.metadata = kwargs
        self.tool_calls = kwargs.get('tool_calls', [])
        
class HumanMessage(BaseMessage):
    """用户消息"""
    role = "user"
    
class AIMessage(BaseMessage):
    """AI消息"""
    role = "assistant"
    
class ToolMessage(BaseMessage):
    """工具消息"""
    role = "tool"
    def __init__(self, content: str, tool_call_id: str = None, **kwargs):
        super().__init__(content, **kwargs)
        self.tool_call_id = tool_call_id
        
class SystemMessage(BaseMessage):
    """系统消息"""
    role = "system"

class RemoveMessage:
    """删除消息操作"""
    def __init__(self, id: str):
        self.id = id

# ============= Prompt模板 =============
class ChatPromptTemplate:
    """聊天提示模板"""
    def __init__(self, messages: List[Any]):
        self.messages = messages
    
    @classmethod
    def from_messages(cls, messages: List[Any]):
        """从消息列表创建模板"""
        return cls(messages)
    
    def format_messages(self, **kwargs) -> List[BaseMessage]:
        """格式化消息"""
        formatted = []
        for msg in self.messages:
            if isinstance(msg, tuple):
                role, content = msg
                if role == "system":
                    formatted.append(SystemMessage(content=content.format(**kwargs)))
                elif role == "human":
                    formatted.append(HumanMessage(content=content.format(**kwargs)))
                elif role == "assistant":
                    formatted.append(AIMessage(content=content.format(**kwargs)))
            elif isinstance(msg, BaseMessage):
                formatted.append(msg)
            elif isinstance(msg, MessagesPlaceholder):
                # 处理占位符
                if msg.variable_name in kwargs:
                    formatted.extend(kwargs[msg.variable_name])
        return formatted

class MessagesPlaceholder:
    """消息占位符"""
    def __init__(self, variable_name: str):
        self.variable_name = variable_name

# ============= 工具 =============
class BaseTool:
    """基础工具类"""
    name: str = "base_tool"
    description: str = "Base tool"
    
    def run(self, *args, **kwargs):
        """运行工具"""
        raise NotImplementedError
        
    def _run(self, *args, **kwargs):
        """运行工具（内部）"""
        return self.run(*args, **kwargs)

def tool(func=None, *, name: Optional[str] = None, description: Optional[str] = None):
    """工具装饰器"""
    def decorator(f):
        f.is_tool = True
        f.tool_name = name or f.__name__
        f.tool_description = description or f.__doc__
        
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        
        return wrapper
    
    if func is None:
        return decorator
    else:
        return decorator(func)

# ============= Agent相关 =============
class AgentExecutor:
    """Agent执行器（简化版）"""
    def __init__(self, agent: Any, tools: List[Any], **kwargs):
        self.agent = agent
        self.tools = tools
        self.kwargs = kwargs
        
    def invoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """执行Agent"""
        # 简化实现，实际应该调用agent和tools
        return {"output": "Agent execution simulated"}

def create_react_agent(llm: Any, tools: List[Any], prompt: Any) -> Any:
    """创建ReAct Agent（简化版）"""
    class ReactAgent:
        def __init__(self):
            self.llm = llm
            self.tools = tools
            self.prompt = prompt
    
    return ReactAgent()

# ============= LLM相关 =============  
class ChatOpenAI:
    """ChatOpenAI的简化替代"""
    def __init__(self, model: str = "gpt-3.5-turbo", temperature: float = 0.7, **kwargs):
        self.model = model
        self.temperature = temperature
        self.kwargs = kwargs
        
        # 使用我们的LLM客户端
        from backend.utils.llm_client import create_llm_client
        
        # 根据模型名称选择provider
        if "gpt" in model or "openai" in model:
            provider = "siliconflow"  # 使用siliconflow作为OpenAI的替代
            model = "Qwen/Qwen2.5-7B-Instruct"
        elif "deepseek" in model:
            provider = "deepseek"
        else:
            provider = "deepseek"  # 默认
            model = "deepseek-chat"
            
        self.client = create_llm_client(provider=provider, model=model, temperature=temperature)
        
    def bind_tools(self, tools: List[Any]) -> "ChatOpenAI":
        """绑定工具"""
        self.tools = tools
        return self
        
    async def ainvoke(self, messages: List[BaseMessage]) -> AIMessage:
        """异步调用"""
        # 转换消息格式
        prompt = ""
        system_prompt = ""
        
        for msg in messages:
            if hasattr(msg, 'role'):
                if msg.role == "system":
                    system_prompt = msg.content
                elif msg.role == "user":
                    prompt = msg.content
                    
        # 调用LLM
        response = await self.client.generate(prompt, system_prompt, self.temperature)
        
        return AIMessage(content=response)
        
    def invoke(self, messages: List[BaseMessage]) -> AIMessage:
        """同步调用"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        return loop.run_until_complete(self.ainvoke(messages))

# ============= LangGraph相关 =============
class StateGraph:
    """状态图（简化版）"""
    def __init__(self, state_class):
        self.state_class = state_class
        self.nodes = {}
        self.edges = {}
        
    def add_node(self, name: str, func: Callable):
        """添加节点"""
        self.nodes[name] = func
        
    def add_edge(self, from_node: str, to_node: str):
        """添加边"""
        if from_node not in self.edges:
            self.edges[from_node] = []
        self.edges[from_node].append(to_node)
        
    def compile(self):
        """编译图"""
        return self

class MessagesState:
    """消息状态（简化版）"""
    messages: List[BaseMessage] = []

class ToolNode:
    """工具节点（简化版）"""
    def __init__(self, tools: List[Any]):
        self.tools = tools

# 常量
START = "__start__"
END = "__end__"

# ============= Hub相关 =============
class Hub:
    """LangChain Hub的简化版"""
    @staticmethod
    def pull(template_name: str) -> ChatPromptTemplate:
        """获取模板（返回默认模板）"""
        return ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant."),
            ("human", "{input}")
        ])

hub = Hub()

# 导出所有组件
__all__ = [
    'BaseMessage',
    'HumanMessage',
    'AIMessage',
    'ToolMessage',
    'SystemMessage',
    'RemoveMessage',
    'ChatPromptTemplate',
    'MessagesPlaceholder',
    'BaseTool',
    'tool',
    'AgentExecutor',
    'create_react_agent',
    'ChatOpenAI',
    'StateGraph',
    'MessagesState',
    'ToolNode',
    'START',
    'END',
    'hub'
]
