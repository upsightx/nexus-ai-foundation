"""
Nexus AI Foundation - Agent Framework
多智能体系统
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import asyncio
import uuid


class AgentRole(Enum):
    """智能体角色"""
    PLANNER = "planner"           # 任务规划
    RESEARCHER = "researcher"     # 信息收集
    ANALYST = "analyst"           # 分析推理
    EXECUTOR = "executor"         # 执行操作
    REVIEWER = "reviewer"         # 结果审查
    SYNTHESIZER = "synthesizer"   # 综合总结
    CRITIC = "critic"             # 批评建议
    GENERATOR = "generator"       # 内容生成


class AgentState(Enum):
    """智能体状态"""
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    WAITING = "waiting"
    DONE = "done"
    ERROR = "error"


@dataclass
class Message:
    """智能体消息"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender: str = ""
    receiver: str = ""
    content: Any = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=lambda: asyncio.get_event_loop().time())


@dataclass
class AgentConfig:
    """智能体配置"""
    role: AgentRole
    name: str
    model: str
    system_prompt: str
    tools: List[str] = field(default_factory=list)
    max_iterations: int = 5
    temperature: float = 0.7


@dataclass
class Agent:
    """基础智能体"""
    config: AgentConfig
    state: AgentState = AgentState.IDLE
    memory: List[Message] = field(default_factory=list)
    tools_registry: Optional[Any] = None
    
    @property
    def id(self) -> str:
        return f"{self.config.role.value}_{self.config.name}"
    
    async def think(self, input_data: Any) -> Any:
        """思考/推理"""
        self.state = AgentState.THINKING
        # 实际实现调用LLM
        await asyncio.sleep(0.1)  # 模拟
        return input_data
    
    async def act(self, plan: Any) -> Any:
        """执行"""
        self.state = AgentState.ACTING
        # 执行计划
        await asyncio.sleep(0.1)
        return plan
    
    async def run(self, task: Any) -> Any:
        """运行智能体"""
        # 思考
        thought = await self.think(task)
        
        # 行动
        result = await self.act(thought)
        
        self.state = AgentState.DONE
        return result


class AgentSwarm:
    """多智能体协作群"""
    
    def __init__(self, name: str = "swarm"):
        self.name = name
        self.agents: Dict[str, Agent] = {}
        self.message_board: List[Message] = []
        self.blackboard: Dict[str, Any] = {}  # 共享知识
        
        # 事件
        self.event_queue: asyncio.Queue = asyncio.Queue()
    
    def register_agent(self, agent: Agent):
        """注册智能体"""
        self.agents[agent.id] = agent
    
    def create_agent(
        self,
        role: AgentRole,
        name: str,
        model: str,
        system_prompt: str,
        tools: Optional[List[str]] = None
    ) -> Agent:
        """创建智能体"""
        config = AgentConfig(
            role=role,
            name=name,
            model=model,
            system_prompt=system_prompt,
            tools=tools or []
        )
        agent = Agent(config=config)
        self.register_agent(agent)
        return agent
    
    async def send_message(
        self,
        from_agent: str,
        to_agent: str,
        content: Any,
        metadata: Optional[Dict] = None
    ):
        """发送消息"""
        message = Message(
            sender=from_agent,
            receiver=to_agent,
            content=content,
            metadata=metadata or {}
        )
        self.message_board.append(message)
        
        # 投递到目标智能体
        if to_agent in self.agents:
            self.agents[to_agent].memory.append(message)
        
        # 触发事件
        await self.event_queue.put(message)
    
    async def broadcast(
        self,
        from_agent: str,
        content: Any,
        metadata: Optional[Dict] = None
    ):
        """广播消息"""
        for agent_id in self.agents:
            if agent_id != from_agent:
                await self.send_message(from_agent, agent_id, content, metadata)
    
    def write_blackboard(self, key: str, value: Any):
        """写入黑板"""
        self.blackboard[key] = value
    
    def read_blackboard(self, key: str) -> Optional[Any]:
        """读取黑板"""
        return self.blackboard.get(key)
    
    async def orchestrate(self, task: str) -> Dict[str, Any]:
        """编排多智能体协作 - 通用工作流"""
        
        results = {}
        
        # 获取相关智能体
        planner = self.agents.get(f"planner_main")
        researcher = self.agents.get(f"researcher_main")
        analyst = self.agents.get(f"analyst_main")
        synthesizer = self.agents.get(f"synthesizer_main")
        
        # Stage 1: 规划
        if planner:
            plan = await planner.run(task)
            results["plan"] = plan
            self.write_blackboard("plan", plan)
        
        # Stage 2: 研究
        if researcher:
            research_result = await researcher.run(results.get("plan", task))
            results["research"] = research_result
            self.write_blackboard("research", research_result)
        
        # Stage 3: 分析
        if analyst:
            analysis = await analyst.run(results.get("research", task))
            results["analysis"] = analysis
            self.write_blackboard("analysis", analysis)
        
        # Stage 4: 综合
        if synthesizer:
            final = await synthesizer.run(results)
            results["final"] = final
        
        return results
    
    async def run_parallel(
        self,
        task: str,
        roles: List[AgentRole]
    ) -> Dict[str, Any]:
        """并行运行多个智能体"""
        tasks = []
        
        for role in roles:
            agent = self._get_agent_by_role(role)
            if agent:
                tasks.append(agent.run(task))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            role.value: result 
            for role, result in zip(roles, results)
        }
    
    def _get_agent_by_role(self, role: AgentRole) -> Optional[Agent]:
        """按角色获取智能体"""
        for agent in self.agents.values():
            if agent.config.role == role:
                return agent
        return None


# 预定义智能体工厂
class AgentFactory:
    """智能体工厂"""
    
    @staticmethod
    def create_planner(name: str = "main", model: str = "gpt-4o") -> Agent:
        """创建规划智能体"""
        return Agent(
            config=AgentConfig(
                role=AgentRole.PLANNER,
                name=name,
                model=model,
                system_prompt="""你是一个任务规划专家。你的职责是：
1. 分析用户请求，理解目标
2. 将复杂任务分解为可执行的子任务
3. 确定任务的执行顺序和依赖关系
4. 为每个子任务指定合适的执行智能体

请以结构化的方式输出任务计划。"""
            )
        )
    
    @staticmethod
    def create_researcher(name: str = "main", model: str = "gemini-2.0-flash") -> Agent:
        """创建研究智能体"""
        return Agent(
            config=AgentConfig(
                role=AgentRole.RESEARCHER,
                name=name,
                model=model,
                system_prompt="""你是一个研究专家。你的职责是：
1. 根据任务要求收集相关信息
2. 搜索和筛选高质量的信息源
3. 整理和总结研究发现
4. 识别知识空白和不确定性

请提供全面、准确的研究结果。"""
            )
        )
    
    @staticmethod
    def create_analyst(name: str = "main", model: str = "gpt-4o") -> Agent:
        """创建分析智能体"""
        return Agent(
            config=AgentConfig(
                role=AgentRole.ANALYST,
                name=name,
                model=model,
                system_prompt="""你是一个分析专家。你的职责是：
1. 分析研究数据和结果
2. 识别模式、趋势和异常
3. 提供深入洞察和见解
4. 基于证据得出结论

请提供清晰、逻辑严密的分析。"""
            )
        )
    
    @staticmethod
    def create_synthesizer(name: str = "main", model: str = "claude-3-5-sonnet") -> Agent:
        """创建综合智能体"""
        return Agent(
            config=AgentConfig(
                role=AgentRole.SYNTHESIZER,
                name=name,
                model=model,
                system_prompt="""你是一个综合专家。你的职责是：
1. 整合多个来源的信息
2. 综合不同角度的观点
3. 生成连贯、全面的最终输出
4. 确保结论清晰可行

请提供高质量的综合报告。"""
            )
        )
    
    @staticmethod
    def create_standard_swarm() -> AgentSwarm:
        """创建标准智能体群"""
        swarm = AgentSwarm("standard")
        
        # 添加标准智能体
        swarm.register_agent(AgentFactory.create_planner())
        swarm.register_agent(AgentFactory.create_researcher())
        swarm.register_agent(AgentFactory.create_analyst())
        swarm.register_agent(AgentFactory.create_synthesizer())
        
        return swarm


# 测试
async def test_agent_swarm():
    """测试智能体群"""
    print("=== 测试 Agent Swarm ===\n")
    
    # 创建智能体群
    swarm = AgentSwarm("test_swarm")
    
    # 创建智能体
    planner = swarm.create_agent(
        role=AgentRole.PLANNER,
        name="main",
        model="gpt-4o",
        system_prompt="你是一个任务规划专家"
    )
    
    researcher = swarm.create_agent(
        role=AgentRole.RESEARCHER,
        name="main", 
        model="gemini-2.0-flash",
        system_prompt="你是一个研究专家"
    )
    
    # 测试消息发送
    await swarm.send_message(
        from_agent=planner.id,
        to_agent=researcher.id,
        content="请研究AI的发展历史"
    )
    
    print(f"已注册智能体: {list(swarm.agents.keys())}")
    print(f"消息板消息数: {len(swarm.message_board)}")
    
    # 写入黑板
    swarm.write_blackboard("task", "研究AI")
    print(f"黑板内容: {swarm.blackboard}")
    
    # 测试并行运行
    print("\n并行运行测试:")
    results = await swarm.run_parallel(
        task="简单任务",
        roles=[AgentRole.PLANNER, AgentRole.RESEARCHER]
    )
    print(f"结果: {results.keys()}")
    
    print("\n✓ Agent Swarm 测试通过!")


if __name__ == "__main__":
    asyncio.run(test_agent_swarm())
