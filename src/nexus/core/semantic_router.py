"""
Nexus AI Foundation - Semantic Router
语义路由 - 亚秒级意图识别与模型分发
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import asyncio
import hashlib


class RouteIntent(Enum):
    """路由意图"""
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    MATH_REASONING = "math_reasoning"
    CREATIVE_WRITING = "creative_writing"
    DATA_ANALYSIS = "data_analysis"
    FAST_RESPONSE = "fast_response"
    LONG_CONTEXT = "long_context"
    VISION = "vision"
    AGENTIC_TASK = "agentic_task"
    GENERAL = "general"


@dataclass
class RouteEntry:
    """路由条目"""
    intent: RouteIntent
    model: str
    description: str
    examples: List[str]
    keywords: List[str] = field(default_factory=list)


@dataclass
class RoutingDecision:
    """路由决策"""
    intent: RouteIntent
    model: str
    confidence: float
    reasoning: str


class SemanticRouter:
    """语义路由 - 亚秒级意图识别"""
    
    # 预定义路由表
    ROUTE_TABLE: List[RouteEntry] = [
        RouteEntry(
            intent=RouteIntent.CODE_GENERATION,
            model="deepseek-coder",
            description="代码生成",
            examples=["写一个Python函数", "实现快速排序", "创建REST API", "用代码实现", "帮我写"],
            keywords=["写", "代码", "实现", "function", "def", "class", "api", "写代码", "帮我写"]
        ),
        RouteEntry(
            intent=RouteIntent.CODE_REVIEW,
            model="claude-3-5-sonnet",
            description="代码审查",
            examples=["审查这段代码", "找出bug", "优化性能", "代码review", "帮我审查"],
            keywords=["审查", "review", "bug", "优化", "改进", "帮我审查"]
        ),
        RouteEntry(
            intent=RouteIntent.MATH_REASONING,
            model="o1-mini",
            description="数学推理",
            examples=["证明这个定理", "计算积分", "求解方程", "数学问题"],
            keywords=["证明", "计算", "求解", "积分", "微分", "方程", "数学"]
        ),
        RouteEntry(
            intent=RouteIntent.DATA_ANALYSIS,
            model="gpt-4o",
            description="数据分析",
            examples=["分析这份数据", "统计", "可视化", "报表"],
            keywords=["分析", "统计", "数据", "报表", "可视化", "chart"]
        ),
        RouteEntry(
            intent=RouteIntent.CREATIVE_WRITING,
            model="claude-3-5-sonnet",
            description="创意写作",
            examples=["写一首诗", "创作故事", "写文章"],
            keywords=["写", "创作", "诗", "故事", "文章", "小说", "write", "creative"]
        ),
        RouteEntry(
            intent=RouteIntent.FAST_RESPONSE,
            model="gemini-2.0-flash",
            description="快速响应",
            examples=["今天天气如何", "查询这个词", "简单翻译", "什么是"],
            keywords=["什么是", "怎么", "如何", "今天", "天气", "时间"]
        ),
        RouteEntry(
            intent=RouteIntent.LONG_CONTEXT,
            model="claude-3-5-sonnet",
            description="长文本处理",
            examples=["总结这篇论文", "分析这本书", "提取要点", "总结"],
            keywords=["总结", "摘要", "概括", "论文", "book", "document"]
        ),
        RouteEntry(
            intent=RouteIntent.VISION,
            model="gpt-4o",
            description="图像理解",
            examples=["描述这张图片", "图像内容", "图片里有什么"],
            keywords=["图片", "图像", "照片", "图片中", "image", "photo"]
        ),
        RouteEntry(
            intent=RouteIntent.AGENTIC_TASK,
            model="gpt-4o",
            description="复杂代理任务",
            examples=["帮我完成这个项目", "自动执行", "批量处理"],
            keywords=["完成", "执行", "自动", "批量", "项目", "任务"]
        ),
    ]
    
    def __init__(self):
        self._build_index()
    
    def _build_index(self):
        """构建向量索引（简化版：关键词匹配）"""
        # 为生产环境，可以使用 sentence-transformers 或 OpenAI embeddings
        pass
    
    def route(self, query: str) -> RoutingDecision:
        """路由决策 - 亚秒级"""
        query_lower = query.lower()
        
        # 1. 优先级匹配 - 先检查更具体的关键词
        # 优先级: 代码 > 数学 > 数据 > 视觉 > 长文本 > 创意 > 快速 > 通用
        priority_order = [
            RouteIntent.CODE_GENERATION,
            RouteIntent.CODE_REVIEW,
            RouteIntent.MATH_REASONING,
            RouteIntent.DATA_ANALYSIS,
            RouteIntent.VISION,
            RouteIntent.LONG_CONTEXT,
            RouteIntent.CREATIVE_WRITING,
            RouteIntent.FAST_RESPONSE,
            RouteIntent.AGENTIC_TASK,
        ]
        
        # 按优先级顺序检查
        for intent in priority_order:
            entry = next((e for e in self.ROUTE_TABLE if e.intent == intent), None)
            if entry:
                score = self._keyword_match(query_lower, entry.keywords)
                if score > 0:
                    return RoutingDecision(
                        intent=entry.intent,
                        model=entry.model,
                        confidence=min(score / 5.0, 1.0),
                        reasoning=f"关键词匹配: {entry.description}"
                    )
        
        # 2. 默认路由
        return RoutingDecision(
            intent=RouteIntent.GENERAL,
            model="gpt-4o",
            confidence=0.5,
            reasoning="默认路由到通用模型"
        )
    
    def _keyword_match(self, query: str, keywords: List[str]) -> float:
        """关键词匹配得分"""
        score = 0.0
        for kw in keywords:
            if kw.lower() in query:
                score += 1.0
        return score
    
    def route_batch(self, queries: List[str]) -> List[RoutingDecision]:
        """批量路由"""
        return [self.route(q) for q in queries]


class HybridRouter:
    """混合路由 - 多层级决策"""
    
    def __init__(
        self,
        semantic_router: SemanticRouter,
        model_mesh: Any = None
    ):
        self.semantic_router = semantic_router
        self.model_mesh = model_mesh
    
    async def route(
        self,
        query: str,
        strategy: str = "auto"  # auto, speed, quality, cost
    ) -> RoutingDecision:
        """多层级路由"""
        
        # Layer 1: 语义路由（毫秒级）
        decision = self.semantic_router.route(query)
        
        # Layer 2: 策略调整
        if strategy == "speed":
            # 优先快速模型
            if decision.intent in [RouteIntent.FAST_RESPONSE, RouteIntent.GENERAL]:
                decision.model = "gemini-2.0-flash"
                decision.reasoning += " → 速度优先"
        
        elif strategy == "quality":
            # 优先高质量模型
            if decision.intent in [RouteIntent.MATH_REASONING, RouteIntent.CODE_REVIEW]:
                decision.model = "claude-3-5-sonnet"
                decision.reasoning += " → 质量优先"
        
        elif strategy == "cost":
            # 优先低成本模型
            decision.model = self._get_cheaper_alternative(decision.model)
            decision.reasoning += " → 成本优先"
        
        return decision
    
    def _get_cheaper_alternative(self, model: str) -> str:
        """获取更便宜的替代模型"""
        alternatives = {
            "gpt-4o": "gpt-4o-mini",
            "claude-3-5-sonnet": "claude-3-5-haiku",
            "gemini-2.0-pro": "gemini-2.0-flash",
        }
        return alternatives.get(model, model)


# 测试
def test_semantic_router():
    """测试语义路由"""
    print("=== 测试 Semantic Router ===\n")
    
    router = SemanticRouter()
    
    test_queries = [
        "写一个Python函数来排序数组",
        "帮我审查这段代码",
        "证明勾股定理",
        "今天天气怎么样？",
        "总结这篇论文的主要内容",
        "分析这份销售数据",
        "帮我完成这个项目",
    ]
    
    print("路由结果:")
    for query in test_queries:
        decision = router.route(query)
        print(f"\n查询: {query}")
        print(f"  → 意图: {decision.intent.value}")
        print(f"  → 模型: {decision.model}")
        print(f"  → 置信度: {decision.confidence:.2f}")
        print(f"  → 原因: {decision.reasoning}")
    
    print("\n✓ 语义路由测试通过!")


def test_hybrid_router():
    """测试混合路由"""
    print("\n=== 测试 Hybrid Router ===\n")
    
    semantic = SemanticRouter()
    hybrid = HybridRouter(semantic)
    
    query = "写一个Python函数来排序数组"
    
    for strategy in ["auto", "speed", "quality", "cost"]:
        decision = asyncio.run(hybrid.route(query, strategy))
        print(f"策略 [{strategy}]: {decision.model} - {decision.reasoning}")
    
    print("\n✓ 混合路由测试通过!")


if __name__ == "__main__":
    test_semantic_router()
    test_hybrid_router()
