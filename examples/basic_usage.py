"""
Nexus AI Foundation - Examples
使用示例
"""

# ========== Example 1: 简单对话 ==========
"""
from src.nexus import NexusAI
import asyncio

async def chat_example():
    nexus = NexusAI()
    
    # 简单对话
    response = await nexus.chat("你好，请介绍一下Python")
    print(response["content"])
    
    # 使用指定模型
    response = await nexus.chat(
        "解释什么是机器学习",
        model="claude-3-5-sonnet"
    )
    print(response["content"])

asyncio.run(chat_example())
"""


# ========== Example 2: 智能路由 ==========
"""
from src.nexus import NexusAI
import asyncio

async def router_example():
    nexus = NexusAI()
    
    # 自动路由到合适的模型
    responses = await asyncio.gather(
        nexus.chat("今天天气怎么样？"),  # -> 快速模型
        nexus.chat("写一个Python函数"),  # -> 代码模型
        nexus.chat("证明勾股定理"),      # -> 推理模型
    )
    
    for r in responses:
        print(f"Model: {r['model']}, Response: {r['content'][:50]}...")

asyncio.run(router_example())
"""


# ========== Example 3: 思维图问题求解 ==========
"""
from src.nexus import NexusAI
import asyncio

async def got_example():
    nexus = NexusAI()
    
    # 使用思维图解决复杂问题
    result = await nexus.solve(
        "如何设计一个高可用的分布式系统?",
        model="gpt-4o"
    )
    
    print(f"Solution: {result['solution']}")
    print(f"Score: {result['score']}")
    print(f"Iterations: {result['stats']['iterations']}")
    print(f"Volume: {result['volume']}")

asyncio.run(got_example())
"""


# ========== Example 4: 工具使用 ==========
"""
from src.nexus import NexusAI
import asyncio

async def tool_example():
    nexus = NexusAI()
    
    # 计算器
    result = await nexus.use_tool("calculator", expression="2**10")
    print(f"2**10 = {result['result']}")
    
    # 获取时间
    result = await nexus.use_tool("get_current_time")
    print(f"Current time: {result['datetime']}")
    
    # 搜索
    result = await nexus.use_tool("web_search", query="AI news", num_results=3)
    for r in result['results']:
        print(f"- {r['title']}")

asyncio.run(tool_example())
"""


# ========== Example 5: 记忆系统 ==========
"""
from src.nexus import NexusAI
import asyncio

async def memory_example():
    nexus = NexusAI()
    
    # 记住重要信息
    await nexus.remember("用户喜欢简洁的技术文档", importance=0.9)
    await nexus.remember("用户是Python开发者", importance=0.8)
    await nexus.remember("今天天气很好", importance=0.3)
    
    # 检索记忆
    memories = await nexus.recall("Python")
    for m in memories:
        print(f"- {m.content}")

asyncio.run(memory_example())
"""


# ========== Example 6: 多智能体协作 ==========
"""
from src.nexus import NexusAI
from src.nexus.agents import AgentSwarm, AgentRole
import asyncio

async def agent_example():
    nexus = NexusAI()
    
    # 创建智能体群
    swarm = nexus.create_swarm("research")
    
    # 添加智能体
    swarm.create_agent(
        role=AgentRole.RESEARCHER,
        name="main",
        model="gemini-2.0-flash",
        system_prompt="你是一个研究专家，擅长收集信息"
    )
    
    swarm.create_agent(
        role=AgentRole.SYNTHESIZER,
        name="main",
        model="claude-3-5-sonnet",
        system_prompt="你是一个综合专家，擅长整合信息"
    )
    
    # 并行执行
    results = await swarm.run_parallel(
        task="AI的发展历史",
        roles=[AgentRole.RESEARCHER]
    )
    
    print(results)

asyncio.run(agent_example())
"""


# ========== Example 7: MCP协议 ==========
"""
from src.nexus.tools.mcp import MCPClient
import asyncio

async def mcp_example():
    client = MCPClient()
    
    # 列出资源
    resources = await client.list_resources()
    print("Resources:", [r["name"] for r in resources])
    
    # 调用工具
    result = await client.call_tool("get_time")
    print("datetime"])
    
   Time:", result[" # 获取提示模板
    prompt = await client.get_prompt("summarize", {"content": "测试文本"})
    print("Prompt:", prompt)

asyncio.run(mcp_example())
"""


# ========== Example 8: Token预算管理 ==========
"""
from src.nexus.core import TokenBudget, QuotaManager, BudgetStrategy

# 创建预算
budget = TokenBudget(
    max_context_window=128000,
    strategy=BudgetStrategy.BALANCED  # 85%法则
)

print(f"有效预算: {budget.effective_limit:,}")
print(f"安全缓冲区: {budget.safety_buffer:,}")

# 配额管理
quota = QuotaManager(monthly_budget=100_000_000_000)  # 100B
quota.consume(10_000_000_000)  # 已使用100亿

print(f"已使用: {quota.used:,}")
print(f"剩余: {quota.remaining():,}")
print(f"使用率: {quota.usage_ratio():.2%}")
print(f"告警: {quota.should_alert(0.9)}")
"""


# ========== Example 9: 模型选择 ==========
"""
from src.nexus.core import ModelMesh, ModelCapability, MockProvider

mesh = ModelMesh()

# 注册provider
for provider in ["openai", "anthropic", "google", "deepseek"]:
    mesh.register_provider(provider, MockProvider())

# 按能力选择
fast_model = mesh.select_model(
    required_capabilities=[ModelCapability.FAST],
    prefer_speed=True
)
print(f"快速模型: {fast_model.name}")

reasoning_model = mesh.select_model(
    required_capabilities=[ModelCapability.REASONING],
    prefer_quality=True
)
print(f"推理模型: {reasoning_model.name}")

# 按成本选择
cheap_code = mesh.select_model(
    required_capabilities=[ModelCapability.CODE],
    max_cost=0.3
)
print(f"低成本代码模型: {cheap_code.name}")
"""


# ========== Example 10: 完整工作流 ==========
"""
from src.nexus import NexusAI
import asyncio

async def full_workflow():
    nexus = NexusAI()
    
    # 1. 用户输入问题
    user_query = "帮我研究最新的AI编程助手发展趋势"
    
    # 2. 智能路由
    chat_response = await nexus.chat(user_query)
    print(f"Response: {chat_response['content'][:100]}...")
    print(f"Used model: {chat_response['model']}")
    
    # 3. 使用工具获取更多信息
    search_results = await nexus.use_tool(
        "web_search",
        query="AI programming assistant 2024",
        num_results=5
    )
    print(f"\nFound {len(search_results['results'])} results")
    
    # 4. 记住用户偏好
    await nexus.remember(
        f"用户询问了: {user_query}",
        importance=0.7
    )
    
    # 5. 检查状态
    status = nexus.status()
    print(f"\nToken使用率: {status['quota']['usage_ratio']:.2%}")

asyncio.run(full_workflow())
"""
