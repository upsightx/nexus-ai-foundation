"""
Nexus AI Foundation - Token Budget Module
100亿Token月度预算下的AI Native系统架构设计与实现
"""

from dataclasses import dataclass
from typing import Dict, Optional
from enum import Enum


class BudgetStrategy(Enum):
    """预算策略"""
    CONSERVATIVE = 0.70  # 70% of max
    BALANCED = 0.85      # 85% of max
    AGGRESSIVE = 0.95    # 95% of max


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


class QuotaManager:
    """配额管理器 - 多维度Token分配"""
    
    def __init__(self, monthly_budget: int = 100_000_000_000):  # 100B
        self.monthly_budget = monthly_budget
        self.used = 0
        self.allocations: Dict[str, TokenBudget] = {}
    
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


# 使用示例
if __name__ == "__main__":
    # 100亿Token月度预算
    quota = QuotaManager(monthly_budget=100_000_000_000)
    
    # 为不同任务分配预算
    research_budget = quota.allocate(
        name="research",
        max_context_window=128000,
        strategy=BudgetStrategy.BALANCED,
        percentage=0.3
    )
    
    print(f"研究任务有效预算: {research_budget.effective_limit:,} tokens")
    print(f"安全缓冲区: {research_budget.safety_buffer:,} tokens")
    print(f"当前使用率: {quota.usage_ratio():.2%}")
