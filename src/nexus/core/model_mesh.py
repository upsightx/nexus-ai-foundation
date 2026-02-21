"""
Nexus AI Foundation - Model Mesh Module
智能模型网格 - 支持多模型调用
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import asyncio
import hashlib


class ModelCapability(Enum):
    """模型能力"""
    REASONING = "reasoning"          # 复杂推理
    CREATIVE = "creative"             # 创意写作
    FAST = "fast"                    # 快速响应
    VISION = "vision"                # 图像理解
    FUNCTION = "function"            # 函数调用
    LONG_CONTEXT = "long_context"    # 长文本
    CODE = "code"                    # 代码


class ModelProvider(Enum):
    """模型提供商"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    DEEPSEEK = "deepseek"
    TOGETHER = "together"
    LOCAL = "local"


@dataclass
class ModelSpec:
    """模型规格"""
    name: str
    provider: ModelProvider
    capabilities: List[ModelCapability]
    max_tokens: int
    context_window: int
    speed_tier: str  # instant, fast, balanced, thorough
    cost_per_1m_input: float
    cost_per_1m_output: float
    enabled: bool = True


@dataclass
class ModelResponse:
    """模型响应"""
    content: str
    model: str
    usage: Dict[str, int]  # input_tokens, output_tokens
    finish_reason: str
    latency_ms: float


class ModelMesh:
    """模型网格 - 统一模型调用接口"""
    
    # 内置模型注册表
    MODELS: Dict[str, ModelSpec] = {
        # OpenAI
        "gpt-4o": ModelSpec(
            name="gpt-4o",
            provider=ModelProvider.OPENAI,
            capabilities=[ModelCapability.REASONING, ModelCapability.VISION, ModelCapability.FUNCTION],
            max_tokens=16384,
            context_window=128000,
            speed_tier="balanced",
            cost_per_1m_input=2.50,
            cost_per_1m_output=10.00
        ),
        "gpt-4o-mini": ModelSpec(
            name="gpt-4o-mini",
            provider=ModelProvider.OPENAI,
            capabilities=[ModelCapability.FAST, ModelCapability.FUNCTION],
            max_tokens=16384,
            context_window=128000,
            speed_tier="fast",
            cost_per_1m_input=0.15,
            cost_per_1m_output=0.60
        ),
        "o1-preview": ModelSpec(
            name="o1-preview",
            provider=ModelProvider.OPENAI,
            capabilities=[ModelCapability.REASONING],
            max_tokens=32768,
            context_window=128000,
            speed_tier="thorough",
            cost_per_1m_input=15.00,
            cost_per_1m_output=60.00
        ),
        "o1-mini": ModelSpec(
            name="o1-mini",
            provider=ModelProvider.OPENAI,
            capabilities=[ModelCapability.REASONING, ModelCapability.CODE],
            max_tokens=65536,
            context_window=128000,
            speed_tier="fast",
            cost_per_1m_input=3.00,
            cost_per_1m_output=12.00
        ),
        
        # Anthropic
        "claude-3-5-sonnet": ModelSpec(
            name="claude-3-5-sonnet",
            provider=ModelProvider.ANTHROPIC,
            capabilities=[ModelCapability.REASONING, ModelCapability.CREATIVE, ModelCapability.LONG_CONTEXT],
            max_tokens=8192,
            context_window=200000,
            speed_tier="balanced",
            cost_per_1m_input=3.00,
            cost_per_1m_output=15.00
        ),
        "claude-3-5-haiku": ModelSpec(
            name="claude-3-5-haiku",
            provider=ModelProvider.ANTHROPIC,
            capabilities=[ModelCapability.FAST, ModelCapability.FUNCTION],
            max_tokens=8192,
            context_window=200000,
            speed_tier="instant",
            cost_per_1m_input=0.80,
            cost_per_1m_output=4.00
        ),
        
        # Google
        "gemini-2.0-flash": ModelSpec(
            name="gemini-2.0-flash",
            provider=ModelProvider.GOOGLE,
            capabilities=[ModelCapability.FAST, ModelCapability.VISION, ModelCapability.FUNCTION],
            max_tokens=8192,
            context_window=1000000,
            speed_tier="instant",
            cost_per_1m_input=0.10,
            cost_per_1m_output=0.10
        ),
        "gemini-2.0-pro": ModelSpec(
            name="gemini-2.0-pro",
            provider=ModelProvider.GOOGLE,
            capabilities=[ModelCapability.REASONING, ModelCapability.VISION, ModelCapability.LONG_CONTEXT],
            max_tokens=8192,
            context_window=2000000,
            speed_tier="balanced",
            cost_per_1m_input=1.25,
            cost_per_1m_output=5.00
        ),
        
        # DeepSeek
        "deepseek-chat": ModelSpec(
            name="deepseek-chat",
            provider=ModelProvider.DEEPSEEK,
            capabilities=[ModelCapability.CODE, ModelCapability.REASONING],
            max_tokens=4096,
            context_window=64000,
            speed_tier="fast",
            cost_per_1m_input=0.14,
            cost_per_1m_output=0.28
        ),
        "deepseek-coder": ModelSpec(
            name="deepseek-coder",
            provider=ModelProvider.DEEPSEEK,
            capabilities=[ModelCapability.CODE],
            max_tokens=4096,
            context_window=64000,
            speed_tier="fast",
            cost_per_1m_input=0.14,
            cost_per_1m_output=0.28
        ),
        
        # Together AI (Llama, etc)
        "llama-3.1-8b-instruct": ModelSpec(
            name="llama-3.1-8b-instruct",
            provider=ModelProvider.TOGETHER,
            capabilities=[ModelCapability.CODE, ModelCapability.FAST],
            max_tokens=4096,
            context_window=128000,
            speed_tier="fast",
            cost_per_1m_input=0.20,
            cost_per_1m_output=0.20
        ),
        "llama-3.1-70b-instruct": ModelSpec(
            name="llama-3.1-70b-instruct",
            provider=ModelProvider.TOGETHER,
            capabilities=[ModelCapability.CODE, ModelCapability.REASONING],
            max_tokens=4096,
            context_window=128000,
            speed_tier="balanced",
            cost_per_1m_input=0.35,
            cost_per_1m_output=0.35
        ),
        "qwen-2.5-72b-instruct": ModelSpec(
            name="qwen-2.5-72b-instruct",
            provider=ModelProvider.TOGETHER,
            capabilities=[ModelCapability.CODE, ModelCapability.REASONING],
            max_tokens=4096,
            context_window=32768,
            speed_tier="balanced",
            cost_per_1m_input=0.90,
            cost_per_1m_output=0.90
        ),
    }
    
    def __init__(self):
        self.custom_models: Dict[str, ModelSpec] = {}
        self.providers: Dict[ModelProvider, Any] = {}
        self.default_provider: Optional[Callable] = None
    
    def register_model(self, model: ModelSpec):
        """注册自定义模型"""
        self.custom_models[model.name] = model
    
    def register_provider(self, provider: ModelProvider, handler: Any):
        """注册模型提供商"""
        self.providers[provider] = handler
    
    def get_model(self, name: str) -> Optional[ModelSpec]:
        """获取模型规格"""
        return self.MODELS.get(name) or self.custom_models.get(name)
    
    def list_models(
        self,
        capability: Optional[ModelCapability] = None,
        provider: Optional[ModelProvider] = None,
        max_cost: Optional[float] = None
    ) -> List[ModelSpec]:
        """列出模型"""
        models = list(self.MODELS.values()) + list(self.custom_models.values())
        
        if capability:
            models = [m for m in models if capability in m.capabilities]
        
        if provider:
            models = [m for m in models if m.provider == provider]
        
        if max_cost is not None:
            models = [m for m in models if m.cost_per_1m_input <= max_cost]
        
        return [m for m in models if m.enabled]
    
    def select_model(
        self,
        required_capabilities: List[ModelCapability],
        prefer_speed: bool = False,
        prefer_quality: bool = False,
        max_cost: Optional[float] = None
    ) -> Optional[ModelSpec]:
        """智能选择模型"""
        candidates = self.list_models(
            capability=None,  # 过滤在后面处理
            max_cost=max_cost
        )
        
        # 按能力过滤
        if required_capabilities:
            candidates = [
                m for m in candidates 
                if all(cap in m.capabilities for cap in required_capabilities)
            ]
        
        if not candidates:
            return None
        
        # 排序选择
        if prefer_speed:
            candidates.sort(key=lambda m: (
                {"instant": 0, "fast": 1, "balanced": 2, "thorough": 3}.get(m.speed_tier, 2),
                m.cost_per_1m_input
            ))
        elif prefer_quality:
            candidates.sort(key=lambda m: (
                -m.context_window,
                -m.max_tokens
            ))
        else:
            # 成本优先
            candidates.sort(key=lambda m: m.cost_per_1m_input)
        
        return candidates[0]
    
    async def invoke(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ModelResponse:
        """调用模型"""
        model_spec = self.get_model(model)
        if not model_spec:
            raise ValueError(f"Unknown model: {model}")
        
        # 获取provider handler
        handler = self.providers.get(model_spec.provider)
        
        if handler:
            return await handler.invoke(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens or model_spec.max_tokens,
                **kwargs
            )
        
        # Mock响应（测试用）
        return await self._mock_invoke(model, messages)


class MockProvider:
    """Mock provider for testing"""
    
    def __init__(self, latency_ms: float = 100):
        self.latency_ms = latency_ms
    
    async def invoke(
        self,
        model: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> ModelResponse:
        import time
        start = time.time()
        
        # 模拟延迟
        await asyncio.sleep(self.latency_ms / 1000)
        
        # 生成mock响应
        last_msg = messages[-1]["content"] if messages else ""
        response = f"[{model}] Mock response to: {last_msg[:50]}..."
        
        latency = (time.time() - start) * 1000
        
        return ModelResponse(
            content=response,
            model=model,
            usage={
                "input_tokens": len(str(messages)) // 4,
                "output_tokens": len(response) // 4
            },
            finish_reason="stop",
            latency_ms=latency
        )


# 测试
async def test_model_mesh():
    """测试模型网格"""
    print("=== 测试 Model Mesh ===")
    
    mesh = ModelMesh()
    
    # 注册mock provider
    for provider in ModelProvider:
        mesh.register_provider(provider, MockProvider(latency_ms=50))
    
    # 列出所有模型
    print(f"\n1. 总模型数: {len(mesh.list_models())}")
    
    # 按能力筛选
    code_models = mesh.list_models(capability=ModelCapability.CODE)
    print(f"   代码模型: {[m.name for m in code_models]}")
    
    reasoning_models = mesh.list_models(capability=ModelCapability.REASONING)
    print(f"   推理模型: {[m.name for m in reasoning_models]}")
    
    # 智能选择
    print("\n2. 智能模型选择:")
    
    fast_model = mesh.select_model(
        required_capabilities=[ModelCapability.FAST],
        prefer_speed=True
    )
    print(f"   快速任务: {fast_model.name if fast_model else 'None'}")
    
    reasoning_model = mesh.select_model(
        required_capabilities=[ModelCapability.REASONING],
        prefer_quality=True
    )
    print(f"   推理任务: {reasoning_model.name if reasoning_model else 'None'}")
    
    cheap_model = mesh.select_model(
        required_capabilities=[ModelCapability.CODE],
        max_cost=0.3
    )
    print(f"   低成本: {cheap_model.name if cheap_model else 'None'}")
    
    # 调用模型
    print("\n3. 模型调用:")
    response = await mesh.invoke(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Hello, how are you?"}]
    )
    print(f"   模型: {response.model}")
    print(f"   响应: {response.content[:60]}...")
    print(f"   延迟: {response.latency_ms:.1f}ms")
    print(f"   Token使用: {response.usage}")
    
    print("\n✓ Model Mesh 测试通过!")


if __name__ == "__main__":
    asyncio.run(test_model_mesh())
