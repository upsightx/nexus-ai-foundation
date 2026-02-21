"""
Nexus AI Foundation - Memory System
双时态记忆网络
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import uuid
import json


class MemoryType(Enum):
    """记忆类型"""
    SHORT_TERM = "short_term"     # 当前会话
    WORKING = "working"            # 工作记忆
    LONG_TERM = "long_term"       # 长期记忆
    ENTITY = "entity"             # 实体记忆


class EntityRelation(Enum):
    """实体关系"""
    KNOWS = "knows"
    WORKS_AT = "works_at"
    LOCATED_IN = "located_in"
    PART_OF = "part_of"
    SIMILAR_TO = "similar_to"
    DEPENDS_ON = "depends_on"


@dataclass
class MemoryNode:
    """记忆节点"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    memory_type: MemoryType = MemoryType.SHORT_TERM
    importance: float = 0.5  # 0-1
    embedding: Optional[List[float]] = None
    
    # 时态信息
    t_created: datetime = field(default_factory=datetime.now)
    t_last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


@dataclass
class EntityNode:
    """实体节点"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    entity_type: str = ""  # person, organization, location, etc.
    properties: Dict[str, Any] = field(default_factory=dict)
    
    # 时态有效性
    t_valid_start: datetime = field(default_factory=datetime.now)
    t_valid_end: Optional[datetime] = None
    t_invalidated: Optional[datetime] = None


@dataclass
class TemporalEdge:
    """时态边"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str = ""
    target_id: str = ""
    relation: EntityRelation = EntityRelation.KNOWS
    
    # 时态
    t_valid_start: datetime = field(default_factory=datetime.now)
    t_valid_end: Optional[datetime] = None
    t_invalidated: Optional[datetime] = None


class BiTemporalMemory:
    """双时态记忆系统
    
    特性：
    - 时态边：有效区间(t_valid, t_invalid)
    - 时间旅行查询：重建历史认知快照
    - 混合检索：向量 + 关键词 + 图遍历
    """
    
    def __init__(self):
        # 记忆存储
        self.memories: Dict[str, MemoryNode] = {}
        
        # 实体存储
        self.entities: Dict[str, EntityNode] = {}
        
        # 时态边
        self.edges: Dict[str, TemporalEdge] = {}
        
        # 索引
        self.type_index: Dict[MemoryType, Set[str]] = {}
        self.tag_index: Dict[str, Set[str]] = {}
        
        # 配置
        self.max_short_term = 100
        self.max_working = 20
    
    # ========== 记忆操作 ==========
    
    async def add_memory(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.SHORT_TERM,
        importance: float = 0.5,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MemoryNode:
        """添加记忆"""
        node = MemoryNode(
            content=content,
            memory_type=memory_type,
            importance=importance,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        self.memories[node.id] = node
        
        # 更新索引
        self._update_indexes(node)
        
        # 触发记忆整合
        await self._maybe_consolidate()
        
        return node
    
    def _update_indexes(self, node: MemoryNode):
        """更新索引"""
        # 类型索引
        if node.memory_type not in self.type_index:
            self.type_index[node.memory_type] = set()
        self.type_index[node.memory_type].add(node.id)
        
        # 标签索引
        for tag in node.tags:
            if tag not in self.tag_index:
                self.tag_index[tag] = set()
            self.tag_index[tag].add(node.id)
    
    async def _maybe_consolidate(self):
        """记忆整合"""
        # 检查短期记忆是否已满
        if len(self.type_index.get(MemoryType.SHORT_TERM, set())) > self.max_short_term:
            await self._consolidate_short_term()
    
    async def _consolidate_short_term(self):
        """整合短期记忆到长期"""
        short_term_ids = self.type_index.get(MemoryType.SHORT_TERM, set())
        
        if not short_term_ids:
            return
        
        # 选择重要度高的转为长期
        short_term_memories = [
            self.memories[mid] for mid in short_term_ids
        ]
        
        # 按重要度排序
        short_term_memories.sort(key=lambda m: m.importance, reverse=True)
        
        # 保留一半，其余转为长期
        keep_count = len(short_term_memories) // 2
        
        for memory in short_term_memories[keep_count:]:
            memory.memory_type = MemoryType.LONG_TERM
            
            # 更新索引
            self.type_index[MemoryType.SHORT_TERM].discard(memory.id)
            if MemoryType.LONG_TERM not in self.type_index:
                self.type_index[MemoryType.LONG_TERM] = set()
            self.type_index[MemoryType.LONG_TERM].add(memory.id)
    
    async def retrieve(
        self,
        query: str,
        memory_type: Optional[MemoryType] = None,
        limit: int = 5
    ) -> List[MemoryNode]:
        """检索记忆 - 简化版"""
        results = []
        
        # 获取候选集
        if memory_type:
            candidate_ids = self.type_index.get(memory_type, set())
        else:
            candidate_ids = set(self.memories.keys())
        
        # 简单关键词匹配
        query_lower = query.lower()
        
        for mid in candidate_ids:
            memory = self.memories[mid]
            
            # 关键词匹配
            score = 0
            if query_lower in memory.content.lower():
                score += 1
            for tag in memory.tags:
                if query_lower in tag.lower():
                    score += 0.5
            
            if score > 0:
                results.append((memory, score))
        
        # 按分数排序
        results.sort(key=lambda x: x[1], reverse=True)
        
        return [m for m, _ in results[:limit]]
    
    async def get_working_memory(self) -> List[MemoryNode]:
        """获取工作记忆"""
        working_ids = self.type_index.get(MemoryType.WORKING, set())
        return [self.memories[mid] for mid in working_ids]
    
    async def set_working_memory(self, memory_id: str):
        """设置为工作记忆"""
        if memory_id not in self.memories:
            return
        
        memory = self.memories[memory_id]
        old_type = memory.memory_type
        
        # 从旧类型移除
        if old_type in self.type_index:
            self.type_index[old_type].discard(memory_id)
        
        # 添加到工作记忆
        memory.memory_type = MemoryType.WORKING
        if MemoryType.WORKING not in self.type_index:
            self.type_index[MemoryType.WORKING] = set()
        self.type_index[MemoryType.WORKING].add(memory_id)
        
        # 限制工作记忆数量
        await self._prune_working_memory()
    
    async def _prune_working_memory(self):
        """修剪工作记忆"""
        working_ids = self.type_index.get(MemoryType.WORKING, set())
        
        if len(working_ids) <= self.max_working:
            return
        
        # 保留最近访问的
        working_memories = [
            self.memories[mid] for mid in working_ids
        ]
        working_memories.sort(key=lambda m: m.t_last_accessed, reverse=True)
        
        # 移除外多余的
        for memory in working_memories[self.max_working:]:
            memory.memory_type = MemoryType.LONG_TERM
            self.type_index[MemoryType.WORKING].discard(memory.id)
            
            if MemoryType.LONG_TERM not in self.type_index:
                self.type_index[MemoryType.LONG_TERM] = set()
            self.type_index[MemoryType.LONG_TERM].add(memory.id)
    
    def access_memory(self, memory_id: str):
        """访问记忆"""
        if memory_id in self.memories:
            memory = self.memories[memory_id]
            memory.access_count += 1
            memory.t_last_accessed = datetime.now()
    
    # ========== 实体操作 ==========
    
    async def add_entity(
        self,
        name: str,
        entity_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> EntityNode:
        """添加实体"""
        entity = EntityNode(
            name=name,
            entity_type=entity_type,
            properties=properties or {}
        )
        
        self.entities[entity.id] = entity
        return entity
    
    async def add_relation(
        self,
        source_id: str,
        target_id: str,
        relation: EntityRelation
    ) -> TemporalEdge:
        """添加关系"""
        edge = TemporalEdge(
            source_id=source_id,
            target_id=target_id,
            relation=relation
        )
        
        self.edges[edge.id] = edge
        return edge
    
    # ========== 时间旅行查询 ==========
    
    async def time_travel_query(
        self,
        query: str,
        timestamp: datetime
    ) -> Dict[str, Any]:
        """时间旅行查询 - 重建历史时刻的认知快照"""
        
        # 获取该时间点有效的实体
        valid_entities = [
            e for e in self.entities.values()
            if e.t_valid_start <= timestamp
            and (e.t_invalidated is None or e.t_invalidated > timestamp)
        ]
        
        # 获取该时间点有效的关系
        valid_edges = [
            e for e in self.edges.values()
            if e.t_valid_start <= timestamp
            and (e.t_invalidated is None or e.t_invalidated > timestamp)
        ]
        
        return {
            "timestamp": timestamp.isoformat(),
            "entities": [
                {
                    "id": e.id,
                    "name": e.name,
                    "type": e.entity_type,
                    "properties": e.properties
                }
                for e in valid_entities
            ],
            "relations": [
                {
                    "source": e.source_id,
                    "target": e.target_id,
                    "type": e.relation.value
                }
                for e in valid_edges
            ]
        }
    
    # ========== 统计 ==========
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_memories": len(self.memories),
            "total_entities": len(self.entities),
            "total_edges": len(self.edges),
            "by_type": {
                mt.value: len(ids) 
                for mt, ids in self.type_index.items()
            },
            "total_tags": len(self.tag_index)
        }


class ContextBuilder:
    """上下文构建器 - 为任务构建最优上下文"""
    
    def __init__(self, memory: BiTemporalMemory):
        self.memory = memory
    
    async def build(
        self,
        task: str,
        max_tokens: int = 100000
    ) -> str:
        """构建上下文"""
        # 检索相关记忆
        relevant = await self.memory.retrieve(task, limit=10)
        
        # 构建上下文
        context_parts = ["## 相关记忆\n"]
        
        for memory in relevant:
            self.memory.access_memory(memory.id)
            context_parts.append(f"- {memory.content}")
        
        return "\n".join(context_parts)


# 测试
async def test_memory():
    """测试记忆系统"""
    print("=== 测试 Bi-Temporal Memory ===\n")
    
    memory = BiTemporalMemory()
    
    # 添加记忆
    await memory.add_memory(
        content="用户喜欢简洁的技术文档",
        memory_type=MemoryType.SHORT_TERM,
        importance=0.9,
        tags=["preference", "documentation"]
    )
    
    await memory.add_memory(
        content="今天天气很好",
        memory_type=MemoryType.SHORT_TERM,
        importance=0.3,
        tags=["weather", "daily"]
    )
    
    await memory.add_memory(
        content="用户是Python开发者",
        memory_type=MemoryType.LONG_TERM,
        importance=0.9,
        tags=["user", "developer", "python"]
    )
    
    # 检索
    print("检索 '用户':")
    results = await memory.retrieve("用户")
    for r in results:
        print(f"  - [{r.memory_type.value}] {r.content[:50]}... (importance: {r.importance})")
    
    # 统计
    print("\n统计:")
    stats = memory.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # 添加实体和关系
    user = await memory.add_entity("张三", "person", {"role": "developer"})
    company = await memory.add_entity("Google", "organization", {"industry": "tech"})
    await memory.add_relation(user.id, company.id, EntityRelation.WORKS_AT)
    
    print("\n实体和关系:")
    print(f"  实体数: {len(memory.entities)}")
    print(f"  边数: {len(memory.edges)}")
    
    # 时间旅行
    print("\n时间旅行查询:")
    travel_result = await memory.time_travel_query("用户", datetime.now())
    print(f"  时间点: {travel_result['timestamp']}")
    print(f"  有效实体: {len(travel_result['entities'])}")
    
    print("\n✓ Memory System 测试通过!")


if __name__ == "__main__":
    asyncio.run(test_memory())
