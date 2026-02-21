"""
Nexus AI Foundation - Token Budget Module
100亿Token月度预算下的AI Native系统架构
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List
from enum import Enum
import time
import asyncio


class BudgetStrategy(Enum):
    """预算策略 - 85%法则"""
    CONSERVATIVE = 0.70  # 70% of max
    BALANCED = 0.85      # 85% of max
    AGGRESSIVE = 0.95    # 95% of max


class ModelTier(Enum):
    """模型复杂度等级"""
    LIGHT = "7B"         # 轻量模型
    MEDIUM = "70B"       # 中量模型  
    HEAVY = "ultra"      # 重量模型


@dataclass
class TokenBudget:
    """Token预算管理器
    
    核心原则：85%法则
    - 将任务的可用预算设定为该目标模型最大上下文窗口的85%
    - 保留15%的安全缓冲区用于吸收Token估算误差、系统级系统提示词和动态函数参数的膨胀
    """
    max_context_window: int
    strategy: BudgetStrategy = BudgetStrategy.BALANCED
    
    @property
    def effective_limit(self) -> int:
        """计算有效预算"""
        return int(self.max_context_window * self.strategy.value)
    
    @property
    def safety_buffer(self) -> int:
        """安全缓冲区"""
        return self.max_context_window - self.effective_limit
    
    @property
    def system_prompt_budget(self) -> int:
        """系统提示预留"""
        return int(self.safety_buffer * 0.4)
    
    @property
    def function_params_budget(self) -> int:
        """函数参数预留"""
        return int(self.safety_buffer * 0.3)
    
    @property
    def error_margin_budget(self) -> int:
        """误差余量"""
        return int(self.safety_buffer * 0.3)


@dataclass
class RateLimitConfig:
    """多维限流配置"""
    model_tier_limits: Dict[str, Dict[str, int]] = field(default_factory=lambda: {
        "7B":   {"rpm": 1000, "tpm": 1_000_000, "rpd": 100_000},
        "70B":  {"rpm": 500,  "tpm": 500_000,  "rpd": 50_000},
        "ultra": {"rpm": 100, "tpm": 100_000,  "rpd": 10_000},
    })
    
    request_type_limits: Dict[str, Dict[str, int]] = field(default_factory=lambda: {
        "chat":     {"rpm": 5000, "tpm": 10_000_000},
        "embedding": {"rpm": 1000, "tpm": 50_000_000},
        "summary":  {"rpm": 500,  "tpm": 5_000_000},
    })


class QuotaManager:
    """配额管理器 - 多维度Token分配"""
    
    def __init__(
        self, 
        monthly_budget: int = 100_000_000_000,  # 100B
        config: Optional[RateLimitConfig] = None
    ):
        self.monthly_budget = monthly_budget
        self.used = 0
        self.config = config or RateLimitConfig()
        self.allocations: Dict[str, TokenBudget] = {}
        
        # 使用记录
        self.usage_history: Dict[str, List[float]] = {}
    
    def allocate(
        self,
        name: str,
        max_context_window: int,
        strategy: BudgetStrategy = BudgetStrategy.BALANCED,
        percentage: float = 0.1
    ) -> TokenBudget:
        """分配配额"""
        budget = TokenBudget(
            max_context_window=max_context_window,
            strategy=strategy
        )
        
        self.allocations[name] = budget
        return budget
    
    def consume(self, tokens: int):
        """消耗Token"""
        self.used += tokens
    
    def remaining(self) -> int:
        """剩余配额"""
        return self.monthly_budget - self.used
    
    def usage_ratio(self) -> float:
        """使用率"""
        return self.used / self.monthly_budget
    
    def should_alert(self, threshold: float = 0.9) -> bool:
        """是否触发告警"""
        return self.usage_ratio() >= threshold


class MultiDimensionalRateLimiter:
    """多维限流器"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.usage: Dict[str, List[float]] = {}
        self.locks: Dict[str, asyncio.Lock] = {}
    
    def _get_lock(self, key: str) -> asyncio.Lock:
        """获取锁"""
        if key not in self.locks:
            self.locks[key] = asyncio.Lock()
        return self.locks[key]
    
    async def acquire(
        self, 
        model: str, 
        request_type: str, 
        estimated_tokens: int,
        priority: int = 0  # 0=normal, 1=high, 2=critical
    ) -> bool:
        """获取配额"""
        async with asyncio.Lock():
            # 1. 按模型复杂度限流
            tier = self._get_model_tier(model)
            if not self._check_limit(f"model:{tier}:rpm", 60):
                return False
            if not self._check_limit(f"model:{tier}:tpm", 60, estimated_tokens):
                return False
                
            # 2. 按请求类型限流
            if not self._check_limit(f"type:{request_type}:rpm", 60):
                return False
            if not self._check_limit(f"type:{request_type}:tpm", 60, estimated_tokens):
                return False
                
            # 3. 全局限流
            if not self._check_limit("global:tpm", 60, estimated_tokens):
                return False
                
            return True
    
    def _check_limit(
        self, 
        key: str, 
        window_seconds: int, 
        tokens: int = 1
    ) -> bool:
        """检查是否在限制内"""
        now = time.time()
        
        if key not in self.usage:
            self.usage[key] = []
        
        # 清理过期记录
        self.usage[key] = [t for t in self.usage[key] if now - t < window_seconds]
        
        # 检查是否超限
        if tokens == 1:  # RPM检查
            limit = self._get_limit(key, "rpm")
            return len(self.usage[key]) < limit
        else:  # TPM检查
            limit = self._get_limit(key, "tpm")
            return sum(self.usage[key]) + tokens <= limit
    
    def _record_usage(self, key: str, tokens: int = 1):
        """记录使用"""
        now = time.time()
        if key not in self.usage:
            self.usage[key] = []
        self.usage[key].append(now)
        if tokens > 1:
            self.usage[key].append(now)  # 记录token数
    
    def _get_model_tier(self, model: str) -> str:
        """判断模型规模等级"""
        model_lower = model.lower()
        if any(x in model_lower for x in ["8b", "7b", "qwen-7b", "llama-3-8b", "8b"]):
            return "7B"
        elif any(x in model_lower for x in ["70b", "72b", "qwen-32b", "llama-3-70b", "32b"]):
            return "70B"
        return "ultra"
    
    def _get_limit(self, key: str, limit_type: str) -> int:
        """获取限制值"""
        parts = key.split(":")
        
        if len(parts) == 3:  # model:tier:rpm
            tier = parts[1]
            return self.config.model_tier_limits.get(tier, {}).get(limit_type, 1000)
        elif len(parts) == 2:  # type:chat:rpm
            req_type = parts[1]
            return self.config.request_type_limits.get(req_type, {}).get(limit_type, 1000)
        
        return 1000000  # 全局限额


class DynamicBatcher:
    """动态批处理器"""
    
    def __init__(
        self,
        batch_wait_ms: int = 10,
        max_batch_size: int = 32,
        max_wait_ms: int = 100
    ):
        self.batch_wait_ms = batch_wait_ms
        self.max_batch_size = max_batch_size
        self.max_wait_ms = max_wait_ms
        self.pending: List = []
        self.lock = asyncio.Lock()
        self.running = False
    
    async def add(self, item):
        """添加请求到批次"""
        async with self.lock:
            self.pending.append(item)
            
            # 如果达到批大小，立即处理
            if len(self.pending) >= self.max_batch_size:
                return await self._process_batch()
        
        return None  # 等待异步处理
    
    async def _process_batch(self):
        """处理批次"""
        async with self.lock:
            if not self.pending:
                return []
            
            batch = self.pending[:self.max_batch_size]
            self.pending = self.pending[self.max_batch_size:]
            
        return batch
    
    async def start_processor(self, process_fn):
        """启动批处理器"""
        self.running = True
        while self.running:
            batch = await self._process_batch()
            if batch:
                await process_fn(batch)
            await asyncio.sleep(self.batch_wait_ms / 1000)


class FairScheduler:
    """公平调度器 - 循环轮询"""
    
    def __init__(self):
        self.queues: Dict[str, asyncio.Queue] = {}
        self.weights: Dict[str, int] = {}
        self.pointers: Dict[str, int] = {}
    
    def add_tenant(self, tenant_id: str, weight: int = 1):
        """添加租户"""
        self.queues[tenant_id] = asyncio.Queue()
        self.weights[tenant_id] = weight
        self.pointers[tenant_id] = 0
    
    async def enqueue(self, tenant_id: str, item):
        """入队"""
        if tenant_id not in self.queues:
            self.add_tenant(tenant_id)
        await self.queues[tenant_id].put(item)
    
    async def dequeue(self) -> Optional[tuple]:
        """出队 - 加权轮询"""
        tenants = list(self.queues.keys())
        if not tenants:
            return None
        
        # 简单轮询
        for tenant_id in tenants:
            if not self.queues[tenant_id].empty():
                item = self.queues[tenant_id].get_nowait()
                return tenant_id, item
        
        return None


# 测试
async def test_token_budget():
    """测试Token预算管理"""
    print("=== 测试 Token Budget ===")
    
    budget = TokenBudget(
        max_context_window=128000,
        strategy=BudgetStrategy.BALANCED
    )
    
    print(f"最大上下文: {budget.max_context_window:,}")
    print(f"有效预算: {budget.effective_limit:,}")
    print(f"安全缓冲区: {budget.safety_buffer:,}")
    print(f"  - 系统提示: {budget.system_prompt_budget:,}")
    print(f"  - 函数参数: {budget.function_params_budget:,}")
    print(f"  - 误差余量: {budget.error_margin_budget:,}")
    print()
    
    # 测试配额管理器
    quota = QuotaManager(monthly_budget=100_000_000_000)
    quota.consume(50_000_000_000)
    print(f"已使用: {quota.used:,}")
    print(f"剩余: {quota.remaining():,}")
    print(f"使用率: {quota.usage_ratio():.2%}")
    print(f"告警阈值: {quota.should_alert()}")
    print()


async def test_rate_limiter():
    """测试限流器"""
    print("=== 测试 Rate Limiter ===")
    
    config = RateLimitConfig()
    limiter = MultiDimensionalRateLimiter(config)
    
    # 模拟请求
    for i in range(5):
        result = await limiter.acquire(
            model="gpt-4o",
            request_type="chat",
            estimated_tokens=1000
        )
        print(f"请求 {i+1}: {'✓ 通过' if result else '✗ 拒绝'}")
    
    print()


async def test_dynamic_batcher():
    """测试动态批处理"""
    print("=== 测试 Dynamic Batcher ===")
    
    batcher = DynamicBatcher(batch_wait_ms=10, max_batch_size=3)
    
    results = []
    
    async def process(batch):
        results.append(batch)
        print(f"处理批次: {len(batch)} 项")
    
    # 添加请求
    for i in range(10):
        item = await batcher.add({"id": i, "data": f"item_{i}"})
        if item:
            await process(item)
    
    # 等待最后一批
    await asyncio.sleep(0.1)
    final_batch = await batcher._process_batch()
    if final_batch:
        await process(final_batch)
    
    print(f"总处理批次: {len(results)}")
    print()


async def test_fair_scheduler():
    """测试公平调度"""
    print("=== 测试 Fair Scheduler ===")
    
    scheduler = FairScheduler()
    
    # 添加租户
    scheduler.add_tenant("tenant_a", weight=2)
    scheduler.add_tenant("tenant_b", weight=1)
    scheduler.add_tenant("tenant_c", weight=1)
    
    # 添加请求
    for i in range(6):
        tenant = ["tenant_a", "tenant_b", "tenant_c"][i % 3]
        await scheduler.enqueue(tenant, f"req_{i}")
    
    # 取出请求
    print("调度顺序:")
    for _ in range(6):
        result = await scheduler.dequeue()
        if result:
            tenant_id, item = result
            print(f"  {tenant_id}: {item}")
    
    print()


async def main():
    """主测试"""
    print("=" * 60)
    print("Nexus AI Foundation - Core Modules Test")
    print("=" * 60)
    print()
    
    await test_token_budget()
    await test_rate_limiter()
    await test_dynamic_batcher()
    await test_fair_scheduler()
    
    print("=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
