"""
Nexus AI Foundation - API Routes
FastAPI Routes
"""

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

from ..core import (
    TokenBudget,
    BudgetStrategy,
    SemanticRouter,
    GraphOfThoughts,
    ModelMesh,
    ModelCapability,
)
from ..agents import AgentSwarm, AgentRole
from ..tools import get_registry
from ..storage import BiTemporalMemory


# ========== Models ==========

class ChatRequest(BaseModel):
    message: str
    model: Optional[str] = None
    use_router: bool = True
    temperature: float = 0.7


class ChatResponse(BaseModel):
    content: str
    model: str
    usage: Dict[str, int]
    latency_ms: float


class SolveRequest(BaseModel):
    problem: str
    model: str = "gpt-4o"
    max_iterations: int = 10


class ToolCallRequest(BaseModel):
    tool_name: str
    params: Dict[str, Any] = {}


class MemoryRequest(BaseModel):
    content: str
    importance: float = 0.5
    memory_type: str = "short_term"


class MemoryRecallRequest(BaseModel):
    query: str
    limit: int = 5


class AgentTaskRequest(BaseModel):
    task: str
    role: str = "planner"
    model: Optional[str] = None


# ========== App ==========

app = FastAPI(
    title="Nexus AI Foundation",
    description="AI-Native Cloud Platform API",
    version="1.0.0"
)

# 全局实例
model_mesh = ModelMesh()
semantic_router = SemanticRouter()
memory = BiTemporalMemory()
tools = get_registry()


# ========== Dependencies ==========

async def get_model_mesh():
    return model_mesh


async def get_memory():
    return memory


async def get_tools():
    return tools


# ========== Routes ==========

@app.get("/")
async def root():
    return {
        "name": "Nexus AI Foundation",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


# ========== Model Routes ==========

@app.get("/api/v1/models")
async def list_models(
    capability: Optional[str] = None,
    mesh: ModelMesh = Depends(get_model_mesh)
):
    """列出可用模型"""
    models = mesh.list_models()
    
    if capability:
        try:
            cap = ModelCapability(capability)
            models = [m for m in models if cap in m.capabilities]
        except:
            pass
    
    return {
        "models": [
            {
                "name": m.name,
                "provider": m.provider.value,
                "capabilities": [c.value for c in m.capabilities],
                "max_tokens": m.max_tokens,
                "context_window": m.context_window,
                "speed_tier": m.speed_tier,
                "cost_per_1m_input": m.cost_per_1m_input,
                "cost_per_1m_output": m.cost_per_1m_output,
            }
            for m in models
        ]
    }


@app.post("/api/v1/chat/completions")
async def chat_completions(
    request: ChatRequest,
    mesh: ModelMesh = Depends(get_model_mesh)
):
    """对话完成"""
    import asyncio
    
    # 路由
    if request.use_router:
        decision = semantic_router.route(request.message)
        model = request.model or decision.model
    else:
        model = request.model or "gpt-4o"
    
    # 调用模型
    response = await mesh.invoke(
        model=model,
        messages=[{"role": "user", "content": request.message}],
        temperature=request.temperature
    )
    
    return ChatResponse(
        content=response.content,
        model=response.model,
        usage=response.usage,
        latency_ms=response.latency_ms
    )


# ========== Task Routes ==========

@app.post("/api/v1/tasks/solve")
async def solve_task(request: SolveRequest):
    """使用思维图解决问题"""
    
    async def llm_provider(prompt: str) -> str:
        result = await model_mesh.invoke(
            model=request.model,
            messages=[{"role": "user", "content": prompt}]
        )
        return result.content
    
    got = GraphOfThoughts(llm_provider=llm_provider)
    result = await got.solve(request.problem)
    
    return result


# ========== Tool Routes ==========

@app.get("/api/v1/tools")
async def list_tools(tools_registry = Depends(get_tools)):
    """列出可用工具"""
    all_tools = tools_registry.list_tools()
    
    return {
        "tools": [
            {
                "name": t.name,
                "description": t.description,
                "category": t.category.value,
                "parameters": [
                    {
                        "name": p.name,
                        "type": p.type,
                        "description": p.description,
                        "required": p.required
                    }
                    for p in t.parameters
                ]
            }
            for t in all_tools
        ]
    }


@app.post("/api/v1/tools/call")
async def call_tool(
    request: ToolCallRequest,
    tools_registry = Depends(get_tools)
):
    """调用工具"""
    try:
        result = await tools_registry.execute(
            request.tool_name,
            request.params
        )
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ========== Memory Routes ==========

@app.post("/api/v1/memory")
async def add_memory(
    request: MemoryRequest,
    memory_db = Depends(get_memory)
):
    """添加记忆"""
    from ..storage import MemoryType
    
    node = await memory_db.add_memory(
        content=request.content,
        memory_type=MemoryType(request.memory_type),
        importance=request.importance
    )
    
    return {
        "id": node.id,
        "content": node.content,
        "importance": node.importance
    }


@app.post("/api/v1/memory/recall")
async def recall_memory(
    request: MemoryRecallRequest,
    memory_db = Depends(get_memory)
):
    """检索记忆"""
    results = await memory_db.retrieve(
        query=request.query,
        limit=request.limit
    )
    
    return {
        "memories": [
            {
                "id": m.id,
                "content": m.content,
                "importance": m.importance,
                "memory_type": m.memory_type.value
            }
            for m in results
        ]
    }


@app.get("/api/v1/memory/stats")
async def memory_stats(memory_db = Depends(get_memory)):
    """记忆统计"""
    return memory_db.get_stats()


# ========== Agent Routes ==========

@app.post("/api/v1/agents/run")
async def run_agent(request: AgentTaskRequest):
    """运行智能体"""
    try:
        role = AgentRole(request.role)
    except:
        raise HTTPException(status_code=400, detail=f"Invalid role: {request.role}")
    
    swarm = AgentSwarm()
    model = request.model or "gpt-4o"
    
    agent = swarm.create_agent(
        role=role,
        name="temp",
        model=model,
        system_prompt=f"You are a {role.value} agent."
    )
    
    result = await agent.run(request.task)
    
    return {
        "task": request.task,
        "role": request.role,
        "result": result
    }


# ========== Router Routes ==========

@app.post("/api/v1/router/route")
async def route_query(query: Dict[str, str]):
    """路由查询"""
    decision = semantic_router.route(query.get("query", ""))
    
    return {
        "intent": decision.intent.value,
        "model": decision.model,
        "confidence": decision.confidence,
        "reasoning": decision.reasoning
    }


# ========== Server ==========

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
