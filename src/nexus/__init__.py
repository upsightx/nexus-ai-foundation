"""
Nexus AI Foundation - Main Entry Point
统一入口
"""

import asyncio
from typing import Optional, Dict, Any, List

from .core import (
    TokenBudget,
    QuotaManager,
    BudgetStrategy,
    MultiDimensionalRateLimiter,
    ModelMesh,
    ModelCapability,
    SemanticRouter,
    HybridRouter,
    GraphOfThoughts,
    GoTConfig,
)

from .agents import AgentSwarm, AgentFactory, AgentRole
from .tools import ToolRegistry, get_registry
from .tools.mcp import MCPServer, MCPClient
from .storage import BiTemporalMemory, ContextBuilder
from .utils.evaluation import RoundRobinEvaluator, QualityAssessor


class NexusAI:
    """Nexus AI Foundation - 统一入口类
    
    示例:
        nexus = NexusAI()
        
        # 简单对话
        response = await nexus.chat("写一首诗")
        
        # 使用思维图解决问题
        result = await nexus.solve("如何实现快速排序?")
        
        # 多智能体协作
        result = await nexus.run_agent("研究AI历史", role=AgentRole.RESEARCHER)
    """
    
    def __init__(
        self,
        monthly_budget: int = 100_000_000_000,
        default_model: str = "gpt-4o"
    ):
        # 核心组件
        self.quota = QuotaManager(monthly_budget=monthly_budget)
        self.model_mesh = ModelMesh()
        self.router = SemanticRouter()
        self.hybrid_router = HybridRouter(self.router, self.model_mesh)
        
        # 工具
        self.tools = get_registry()
        
        # 记忆
        self.memory = BiTemporalMemory()
        self.context_builder = ContextBuilder(self.memory)
        
        # MCP
        self.mcp = MCPClient()
        
        # 配置
        self.default_model = default_model
    
    # ========== 基础对话 ==========
    
    async def chat(
        self,
        message: str,
        model: Optional[str] = None,
        use_router: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """聊天"""
        
        # 路由选择模型
        if use_router:
            decision = self.router.route(message)
            model = model or decision.model
        else:
            model = model or self.default_model
        
        # 调用模型
        response = await self.model_mesh.invoke(
            model=model,
            messages=[{"role": "user", "content": message}],
            **kwargs
        )
        
        # 记录到记忆
        await self.memory.add_memory(
            content=f"User: {message}\nAssistant: {response.content}",
            importance=0.5
        )
        
        return {
            "content": response.content,
            "model": response.model,
            "usage": response.usage,
            "latency_ms": response.latency_ms
        }
    
    # ========== 思维图问题求解 ==========
    
    async def solve(
        self,
        problem: str,
        model: str = "gpt-4o",
        config: Optional[GoTConfig] = None
    ) -> Dict[str, Any]:
        """使用思维图解决问题"""
        
        # 创建LLM提供者
        async def llm_provider(prompt: str) -> str:
            result = await self.chat(prompt, model=model)
            return result["content"]
        
        got = GraphOfThoughts(llm_provider=llm_provider, config=config)
        result = await got.solve(problem)
        
        return result
    
    # ========== 工具调用 ==========
    
    async def use_tool(
        self,
        tool_name: str,
        **params
    ) -> Any:
        """使用工具"""
        return await self.tools.execute(tool_name, params)
    
    def list_tools(self) -> List[Dict]:
        """列出可用工具"""
        return [
            {"name": t.name, "description": t.description}
            for t in self.tools.list_tools()
        ]
    
    # ========== 智能体 ==========
    
    def create_swarm(self, name: str = "default") -> AgentSwarm:
        """创建智能体群"""
        return AgentSwarm(name)
    
    async def run_agent(
        self,
        task: str,
        role: AgentRole = AgentRole.PLANNER,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """运行单个智能体"""
        
        # 创建临时智能体
        swarm = self.create_swarm()
        model = model or self.default_model
        
        agent = swarm.create_agent(
            role=role,
            name="temp",
            model=model,
            system_prompt=f"You are a {role.value} agent."
        )
        
        result = await agent.run(task)
        
        return {
            "task": task,
            "role": role.value,
            "result": result
        }
    
    # ========== MCP ==========
    
    async def mcp_list_resources(self) -> List[Dict]:
        """MCP列出资源"""
        return await self.mcp.list_resources()
    
    async def mcp_call_tool(self, name: str, params: Dict = None) -> Any:
        """MCP调用工具"""
        return await self.mcp.call_tool(name, params)
    
    # ========== 记忆 ==========
    
    async def remember(
        self,
        content: str,
        importance: float = 0.5
    ):
        """存储记忆"""
        return await self.memory.add_memory(
            content=content,
            importance=importance
        )
    
    async def recall(self, query: str, limit: int = 5):
        """检索记忆"""
        return await self.memory.retrieve(query, limit=limit)
    
    # ========== 统计 ==========
    
    def status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            "quota": {
                "monthly_budget": self.quota.monthly_budget,
                "used": self.quota.used,
                "remaining": self.quota.remaining(),
                "usage_ratio": self.quota.usage_ratio()
            },
            "models": len(self.model_mesh.list_models()),
            "tools": len(self.tools.tools),
            "memory": self.memory.get_stats()
        }


# ========== 便捷函数 ==========

_nexus_instance: Optional[NexusAI] = None


def get_nexus(
    monthly_budget: int = 100_000_000_000,
    default_model: str = "gpt-4o"
) -> NexusAI:
    """获取全局NexusAI实例"""
    global _nexus_instance
    if _nexus_instance is None:
        _nexus_instance = NexusAI(
            monthly_budget=monthly_budget,
            default_model=default_model
        )
    return _nexus_instance


async def chat(message: str, **kwargs) -> Dict[str, Any]:
    """便捷聊天函数"""
    nexus = get_nexus()
    return await nexus.chat(message, **kwargs)


async def solve(problem: str, **kwargs) -> Dict[str, Any]:
    """便捷求解函数"""
    nexus = get_nexus()
    return await nexus.solve(problem, **kwargs)


# ========== 测试 ==========

async def test_nexus():
    """测试Nexus AI"""
    print("=== Test Nexus AI Foundation ===\n")
    
    # 创建实例
    nexus = NexusAI(monthly_budget=100_000_000_000)
    
    # 状态
    status = nexus.status()
    print(f"Models: {status['models']}")
    print(f"Tools: {status['tools']}")
    print(f"Quota: {status['quota']['monthly_budget']:,}")
    
    # 简单对话
    print("\n--- Chat Test ---")
    response = await nexus.chat("你好，请介绍一下自己")
    print(f"Response: {response['content'][:80]}...")
    print(f"Model: {response['model']}")
    
    # 工具
    print("\n--- Tool Test ---")
    tools = nexus.list_tools()
    print(f"Available tools: {[t['name'] for t in tools[:5]]}")
    
    # 记忆
    print("\n--- Memory Test ---")
    await nexus.remember("用户喜欢Python", importance=0.9)
    memories = await nexus.recall("Python")
    print(f"Found {len(memories)} memories")
    
    print("\n✓ All tests passed!")


if __name__ == "__main__":
    asyncio.run(test_nexus())
