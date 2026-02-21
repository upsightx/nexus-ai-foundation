# 🧠⚡ Nexus AI Foundation

> AI-Native Cloud Platform with 100B+ Tokens/Month Capacity

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 概述

Nexus AI Foundation 是一个完整的AI-Native系统框架，专为每月100亿Token预算的场景设计。基于[架构指南](./docs/ARCHITECTURE_GUIDE.md)构建，提供从基础设施到应用层的全套解决方案。

## ✨ 特性

| 模块 | 描述 |
|------|------|
| **Token Budget** | 85%法则预算管理，多维限流 |
| **Model Mesh** | 13+模型统一抽象，支持多Provider |
| **Semantic Router** | 亚秒级意图识别与智能路由 |
| **Graph of Thoughts** | 思维图架构，突破线性推理 |
| **Agent Swarm** | 多智能体协作框架 |
| **Tool Registry** | 8+内置工具，支持自定义扩展 |
| **MCP Protocol** | 模型上下文协议实现 |
| **Bi-Temporal Memory** | 双时态记忆，支持时间旅行查询 |
| **Evaluation** | 循环锦标赛式LLM评估器 |

## 📦 安装

```bash
pip install -e .
```

## 🚀 快速开始

```python
from nexus import NexusAI
import asyncio

async def main():
    # 创建实例
    nexus = NexusAI(monthly_budget=100_000_000_000)
    
    # 简单对话
    response = await nexus.chat("你好，请介绍一下Python")
    print(response["content"])
    
    # 使用工具
    result = await nexus.use_tool("calculator", expression="2**10")
    print(f"Result: {result['result']}")
    
    # 查看状态
    print(nexus.status())

asyncio.run(main())
```

## 📁 项目结构

```
nexus-ai-foundation/
├── src/nexus/
│   ├── core/           # 核心模块
│   │   ├── token_budget.py
│   │   ├── model_mesh.py
│   │   ├── semantic_router.py
│   │   └── graph_of_thoughts.py
│   ├── agents/          # 智能体
│   ├── tools/           # 工具系统
│   ├── storage/         # 存储系统
│   ├── utils/          # 工具类
│   ├── api/            # API层
│   └── __init__.py     # 统一入口
├── examples/           # 示例
├── docker/             # Docker配置
├── docs/               # 文档
└── README.md
```

## 🔧 核心模块

### Token Budget (85%法则)

```python
from src.nexus.core import TokenBudget, BudgetStrategy

budget = TokenBudget(max_context_window=128000, strategy=BudgetStrategy.BALANCED)
print(f"有效预算: {budget.effective_limit:,} tokens")  # 108,800
```

### Model Mesh

```python
from src.nexus.core import ModelMesh, ModelCapability

mesh = ModelMesh()
fast_model = mesh.select_model([ModelCapability.FAST], prefer_speed=True)
```

### Semantic Router

```python
from src.nexus.core import SemanticRouter

router = SemanticRouter()
decision = router.route("写一个Python函数")
print(decision.model)  # deepseek-coder
```

### Graph of Thoughts

```python
from src.nexus.core import GraphOfThoughts

got = GraphOfThoughts(llm_provider=my_llm)
result = await got.solve("如何实现快速排序?")
```

### Agent Swarm

```python
from src.nexus.agents import AgentSwarm, AgentRole

swarm = AgentSwarm()
swarm.create_agent(AgentRole.PLANNER, "main", "gpt-4o", "planner prompt")
```

## 🐳 Docker部署

```bash
cd docker
docker-compose up -d
```

API: http://localhost:8000

## 📊 测试

```bash
python -c "from src.nexus import NexusAI; import asyncio; asyncio.run(NexusAI().chat('test'))"
```

## 📄 文档

- [架构设计指南](./docs/ARCHITECTURE_GUIDE.md) - 完整架构文档
- [示例代码](./examples/basic_usage.py) - 使用示例

## 📈 统计

- **代码行数**: ~4000+
- **模块数**: 12+
- **模型支持**: 13+
- **内置工具**: 8+

## License

MIT License
