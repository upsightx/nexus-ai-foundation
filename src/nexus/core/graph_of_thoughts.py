"""
Nexus AI Foundation - Graph of Thoughts (GoT)
思维图架构 - 突破线性推理
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Callable
from enum import Enum
import uuid
import asyncio
import time


class ThoughtState(Enum):
    """思维状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    AGGREGATED = "aggregated"
    REFINED = "refined"
    VALIDATED = "validated"
    REJECTED = "rejected"


class OperationType(Enum):
    """操作类型"""
    GENERATE = "generate"
    REFINE = "refine"
    AGGREGATE = "aggregate"
    BACKTRACK = "backtrack"
    VALIDATE = "validate"
    SELECT = "select"


@dataclass
class Thought:
    """认知单元（节点）"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    state: ThoughtState = ThoughtState.PENDING
    score: float = 0.0  # 质量分数 0-1
    parent_ids: List[str] = field(default_factory=list)
    children_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    operation: Optional[OperationType] = None
    
    def __hash__(self):
        return hash(self.id)


@dataclass
class GoTConfig:
    """GoT配置"""
    max_iterations: int = 10
    max_thoughts: int = 100
    min_score_threshold: float = 0.7
    aggregation_threshold: float = 0.5  # 触发聚合的分数
    enable_backtrack: bool = True
    enable_aggregate: bool = True


class GraphOfThoughts:
    """思维图架构
    
    核心特性：
    - 聚合(Aggregation): 多路径融合
    - 细化(Refining): 自反馈循环
    - 回溯(Backtracking): 历史高分节点恢复
    - 体积指标(Volume): 衡量思维网络覆盖率
    """
    
    def __init__(
        self,
        llm_provider: Optional[Callable] = None,
        config: Optional[GoTConfig] = None
    ):
        self.llm = llm_provider
        self.config = config or GoTConfig()
        
        # 图结构
        self.thoughts: Dict[str, Thought] = {}
        self.edges: Dict[str, Set[str]] = {}  # 邻接表: parent -> children
        
        # 根节点
        self.root_id: Optional[str] = None
        
        # 统计
        self.stats = {
            "iterations": 0,
            "total_thoughts": 0,
            "aggregations": 0,
            "backtracks": 0,
        }
        
        # GoO: 操作图谱
        self.operations_graph = self._build_operations_graph()
    
    def _build_operations_graph(self) -> Dict[str, Dict[str, Any]]:
        """构建操作图谱"""
        return {
            "generate": {
                "next": ["refine", "validate", "aggregate"],
                "description": "生成初始思维"
            },
            "refine": {
                "next": ["refine", "aggregate", "validate"],
                "description": "细化思维"
            },
            "aggregate": {
                "next": ["validate"],
                "description": "聚合多思维"
            },
            "backtrack": {
                "next": ["generate"],
                "description": "回溯重试"
            },
            "validate": {
                "next": ["completed"],
                "description": "验证思维"
            }
        }
    
    def add_thought(
        self,
        content: str,
        operation: OperationType = OperationType.GENERATE,
        parent_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Thought:
        """添加思维节点"""
        # 检查最大数量限制
        if len(self.thoughts) >= self.config.max_thoughts:
            # 移除最旧的低分思维
            self._prune_low_score_thoughts()
        
        thought = Thought(
            content=content,
            state=ThoughtState.PROCESSING,
            operation=operation,
            parent_ids=parent_ids or [],
            metadata=metadata or {}
        )
        
        self.thoughts[thought.id] = thought
        self.edges[thought.id] = set()
        
        # 更新父子关系
        for parent_id in thought.parent_ids:
            if parent_id in self.edges:
                self.edges[parent_id].add(thought.id)
        
        # 设置根节点
        if self.root_id is None:
            self.root_id = thought.id
        
        self.stats["total_thoughts"] += 1
        
        return thought
    
    def _prune_low_score_thoughts(self):
        """修剪低分思维"""
        # 移除分数最低的思维（保留重要节点）
        sorted_thoughts = sorted(
            [(tid, t) for tid, t in self.thoughts.items() if t.state == ThoughtState.COMPLETED],
            key=lambda x: x[1].score
        )
        
        # 移除最低的20%
        remove_count = max(1, len(sorted_thoughts) // 5)
        for tid, _ in sorted_thoughts[:remove_count]:
            self._remove_thought(tid)
    
    def _remove_thought(self, thought_id: str):
        """移除思维节点"""
        if thought_id in self.thoughts:
            # 从父节点的children中移除
            for parent_id in self.thoughts[thought_id].parent_ids:
                if parent_id in self.edges:
                    self.edges[parent_id].discard(thought_id)
            
            del self.thoughts[thought_id]
            if thought_id in self.edges:
                del self.edges[thought_id]
    
    async def solve(
        self,
        problem: str,
        initial_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """解决问题"""
        if not self.llm:
            return self._mock_solve(problem)
        
        # Phase 1: 生成初始思维
        initial_prompt = initial_prompt or f"请解决这个问题: {problem}"
        initial_thought = await self._generate(initial_prompt)
        
        # Phase 2: 思维演进循环
        current_thought = initial_thought
        
        for i in range(self.config.max_iterations):
            self.stats["iterations"] = i + 1
            
            # 评估当前思维
            score = await self._evaluate(current_thought, problem)
            current_thought.score = score
            current_thought.state = ThoughtState.COMPLETED
            
            # 检查是否满足要求
            if score >= self.config.min_score_threshold:
                break
            
            # 选择下一个操作
            operation = self._select_operation(current_thought, score)
            
            # 执行操作
            if operation == OperationType.REFINE:
                current_thought = await self._refine(current_thought, problem)
            elif operation == OperationType.AGGREGATE:
                current_thought = await self._aggregate(problem)
                self.stats["aggregations"] += 1
            elif operation == OperationType.BACKTRACK:
                current_thought = await self._backtrack()
                self.stats["backtracks"] += 1
            elif operation == OperationType.VALIDATE:
                is_valid = await self._validate(current_thought, problem)
                if not is_valid:
                    current_thought.state = ThoughtState.REJECTED
                    current_thought = await self._backtrack()
        
        return {
            "solution": current_thought.content,
            "score": current_thought.score,
            "thought_id": current_thought.id,
            "stats": self.stats.copy(),
            "thoughts_count": len(self.thoughts),
            "volume": self.calculate_volume(current_thought.id)
        }
    
    async def _generate(self, prompt: str) -> Thought:
        """生成思维"""
        response = await self.llm(prompt)
        
        return self.add_thought(
            content=response,
            operation=OperationType.GENERATE
        )
    
    async def _refine(self, thought: Thought, problem: str) -> Thought:
        """细化思维"""
        refined_prompt = f"""
基于以下问题，细化这个答案：

问题: {problem}

当前答案:
{thought.content}

请提供更精确、更完整的答案。
"""
        refined = await self.llm(refined_prompt)
        
        new_thought = self.add_thought(
            content=refined,
            operation=OperationType.REFINE,
            parent_ids=[thought.id]
        )
        
        return new_thought
    
    async def _aggregate(self, problem: str) -> Thought:
        """聚合思维 - 关键创新！"""
        # 获取所有高质量候选思维
        candidates = self._get_candidate_thoughts()
        
        if len(candidates) < 2:
            # 只有一个候选，返回它
            return candidates[0] if candidates else list(self.thoughts.values())[0]
        
        aggregation_prompt = f"""
将以下多个解答方案融合为一个最优答案：

问题: {problem}

{"=".join([f"方案{i+1} (分数: {c.score:.2f}):\n{c.content}" for i, c in enumerate(candidates)])}

综合各方案优点，给出最终答案。要求：
1. 吸收各方案的最佳部分
2. 解决方案之间的矛盾
3. 提供一个完整且准确的答案
"""
        
        aggregated = await self.llm(aggregation_prompt)
        
        new_thought = self.add_thought(
            content=aggregated,
            operation=OperationType.AGGREGATE,
            parent_ids=[c.id for c in candidates]
        )
        new_thought.state = ThoughtState.AGGREGATED
        
        return new_thought
    
    async def _backtrack(self) -> Thought:
        """回溯到高质量节点"""
        if not self.config.enable_backtrack:
            # 如果不允许回溯，生成新的思维
            return await self._generate("重新思考这个问题")
        
        # 找到历史最高分节点
        best_thought = self._find_best_ancestor()
        
        if best_thought and best_thought.score > 0.3:
            # 从最佳节点重新生成
            return await self._generate(f"基于以下思路重新思考: {best_thought.content}")
        
        # 否则生成新思维
        return await self._generate("重新思考这个问题")
    
    async def _evaluate(self, thought: Thought, problem: str) -> float:
        """评估思维质量"""
        eval_prompt = f"""
评估以下答案对问题的解决程度（0-1分）：

问题: {problem}

答案: {thought.content}

请只返回一个数字分数，不要其他文字。分数标准：
- 0.0-0.3: 完全不正确或不相关
- 0.3-0.5: 部分正确，但不完整
- 0.5-0.7: 基本正确，但有改进空间
- 0.7-0.9: 正确且完整
- 0.9-1.0: 完美答案
"""
        
        response = await self.llm(eval_prompt)
        
        try:
            # 提取数字
            import re
            match = re.search(r'0?\.?\d+', response)
            if match:
                return float(match.group())
        except:
            pass
        
        return 0.5  # 默认分数
    
    async def _validate(self, thought: Thought, problem: str) -> bool:
        """验证思维正确性"""
        # 简化验证
        return thought.score >= 0.5
    
    def _select_operation(
        self,
        thought: Thought,
        score: float
    ) -> OperationType:
        """选择下一个操作"""
        if score < 0.3:
            return OperationType.BACKTRACK
        elif score < 0.5:
            return OperationType.REFINE
        elif score < self.config.aggregation_threshold and self.config.enable_aggregate:
            # 检查是否有足够的候选
            candidates = self._get_candidate_thoughts()
            if len(candidates) >= 2:
                return OperationType.AGGREGATE
            return OperationType.REFINE
        elif score < self.config.min_score_threshold:
            return OperationType.REFINE
        else:
            return OperationType.VALIDATE
    
    def _get_candidate_thoughts(self) -> List[Thought]:
        """获取候选思维（用于聚合）"""
        # 获取已完成且分数较高的思维
        candidates = [
            t for t in self.thoughts.values()
            if t.state in [ThoughtState.COMPLETED, ThoughtState.AGGREGATED]
            and t.score >= self.config.aggregation_threshold
        ]
        
        # 按分数排序，取前5个
        candidates.sort(key=lambda x: x.score, reverse=True)
        return candidates[:5]
    
    def _find_best_ancestor(self) -> Optional[Thought]:
        """找到最佳祖先节点"""
        if not self.thoughts:
            return None
        
        completed = [
            t for t in self.thoughts.values()
            if t.state == ThoughtState.COMPLETED
        ]
        
        if not completed:
            return None
        
        return max(completed, key=lambda x: x.score)
    
    def calculate_volume(self, thought_id: str) -> int:
        """计算体积指标 - GoT核心指标
        
        体积 = 通过依赖路径可触达的认知节点总数
        """
        if thought_id not in self.thoughts:
            return 0
        
        visited = set()
        
        def dfs(node_id: str):
            if node_id in visited:
                return
            visited.add(node_id)
            for child_id in self.edges.get(node_id, []):
                dfs(child_id)
        
        dfs(thought_id)
        return len(visited)
    
    def get_thought_tree(self, thought_id: str) -> Dict[str, Any]:
        """获取思维树"""
        if thought_id not in self.thoughts:
            return {}
        
        thought = self.thoughts[thought_id]
        
        return {
            "id": thought.id,
            "content": thought.content[:100] + "...",
            "score": thought.score,
            "state": thought.state.value,
            "operation": thought.operation.value if thought.operation else None,
            "children": [
                self.get_thought_tree(child_id)
                for child_id in self.edges.get(thought_id, [])
            ]
        }
    
    def _mock_solve(self, problem: str) -> Dict[str, Any]:
        """模拟解决（无LLM时）"""
        solution = f"Mock solution for: {problem}"
        
        thought = self.add_thought(
            content=solution,
            operation=OperationType.GENERATE
        )
        thought.score = 0.8
        thought.state = ThoughtState.COMPLETED
        
        return {
            "solution": solution,
            "score": 0.8,
            "thought_id": thought.id,
            "stats": self.stats,
            "thoughts_count": len(self.thoughts),
            "volume": 1
        }


# 测试
async def mock_llm(prompt: str) -> str:
    """Mock LLM for testing"""
    await asyncio.sleep(0.1)
    
    if "评估" in prompt or "分数" in prompt or "score" in prompt.lower():
        return "0.75"
    
    if "融合" in prompt or "聚合" in prompt:
        return "这是聚合后的答案，综合了多个方案的优点。"
    
    if "细化" in prompt:
        return "这是细化后的答案，更完整准确。"
    
    return f"这是一个测试答案: {prompt[:50]}..."


async def test_graph_of_thoughts():
    """测试思维图"""
    print("=== 测试 Graph of Thoughts ===\n")
    
    got = GraphOfThoughts(llm_provider=mock_llm)
    
    problem = "如何用Python实现快速排序？"
    
    print(f"问题: {problem}\n")
    
    result = await got.solve(problem)
    
    print(f"解答: {result['solution'][:80]}...")
    print(f"分数: {result['score']:.2f}")
    print(f"迭代次数: {result['stats']['iterations']}")
    print(f"总思维数: {result['thoughts_count']}")
    print(f"聚合次数: {result['stats']['aggregations']}")
    print(f"回溯次数: {result['stats']['backtracks']}")
    print(f"体积指标: {result['volume']}")
    
    # 打印思维树
    print("\n思维树结构:")
    tree = got.get_thought_tree(result['thought_id'])
    print(f"  根节点: {tree.get('id', 'N/A')[:8]}... (score: {tree.get('score', 0):.2f})")
    
    print("\n✓ Graph of Thoughts 测试通过!")


if __name__ == "__main__":
    asyncio.run(test_graph_of_thoughts())
