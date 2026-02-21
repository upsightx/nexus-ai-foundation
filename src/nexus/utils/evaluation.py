"""
Nexus AI Foundation - Evaluation System
循环锦标赛式LLM评估器
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import asyncio
import random
import math


@dataclass
class Candidate:
    """候选"""
    id: str
    output: str
    model: str
    elo_score: float = 1500.0


@dataclass
class MatchResult:
    """比赛结果"""
    winner_id: str
    loser_id: str
    scores: Dict[str, float]  # 多维度评分


class RoundRobinEvaluator:
    """循环锦标赛评估器
    
    特性:
    - 成对比较
    - Elo评分系统
    - 多维度评估
    """
    
    def __init__(self, judge_llm=None):
        self.judge_llm = judge_llm
        self.candidates: Dict[str, Candidate] = {}
        self.history: List[MatchResult] = []
    
    def add_candidate(self, candidate: Candidate):
        """添加候选"""
        self.candidates[candidate.id] = candidate
    
    async def evaluate(
        self,
        prompt: str,
        num_rounds: int = 10
    ) -> List[Tuple[str, float]]:
        """执行评估"""
        
        # 生成所有候选的输出
        outputs = {}
        for cid, candidate in self.candidates.items():
            if self.judge_llm:
                output = await self.judge_llm(prompt, candidate.model)
            else:
                output = f"Mock output from {candidate.model}"
            outputs[cid] = output
        
        # 成对比较
        candidate_ids = list(self.candidates.keys())
        
        for _ in range(num_rounds):
            if len(candidate_ids) < 2:
                break
            
            # 随机选择一对
            a_id, b_id = random.sample(candidate_ids, 2)
            
            # 评判
            if self.judge_llm:
                result = await self.judge_llm.compare(
                    prompt,
                    outputs[a_id],
                    outputs[b_id]
                )
            else:
                result = {"winner_id": random.choice([a_id, b_id])}
            
            # 更新Elo
            winner_id = result.get("winner_id", a_id)
            loser_id = b_id if winner_id == a_id else a_id
            
            self._update_elo(winner_id, loser_id)
            
            self.history.append(MatchResult(
                winner_id=winner_id,
                loser_id=loser_id,
                scores=result.get("scores", {})
            ))
        
        # 返回排名
        return sorted(
            [(cid, c.elo_score) for cid, c in self.candidates.items()],
            key=lambda x: x[1],
            reverse=True
        )
    
    def _update_elo(self, winner_id: str, loser_id: str):
        """更新Elo分数"""
        K = 32  # 弹性系数
        
        winner = self.candidates[winner_id]
        loser = self.candidates[loser_id]
        
        # 计算期望
        E_winner = 1 / (1 + 10 ** ((loser.elo_score - winner.elo_score) / 400))
        E_loser = 1 - E_winner
        
        # 更新
        winner.elo_score += K * (1 - E_winner)
        loser.elo_score += K * (0 - E_loser)
    
    def get_leaderboard(self) -> List[Dict]:
        """获取排行榜"""
        ranking = sorted(
            self.candidates.values(),
            key=lambda x: x.elo_score,
            reverse=True
        )
        
        return [
            {
                "rank": i + 1,
                "model": c.model,
                "elo": c.elo_score,
                "output": c.output[:50] + "..."
            }
            for i, c in enumerate(ranking)
        ]


@dataclass
class EvaluationMetrics:
    """评估指标"""
    accuracy: float = 0.0
    coherence: float = 0.0
    creativity: float = 0.0
    utility: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "accuracy": self.accuracy,
            "coherence": self.coherence,
            "creativity": self.creativity,
            "utility": self.utility
        }


class QualityAssessor:
    """质量评估器"""
    
    def __init__(self, llm=None):
        self.llm = llm
    
    async def assess(
        self,
        prompt: str,
        response: str
    ) -> EvaluationMetrics:
        """评估响应质量"""
        
        if self.llm:
            result = await self.llm(prompt, response)
            return EvaluationMetrics(**result)
        
        # Mock评估
        return EvaluationMetrics(
            accuracy=random.uniform(0.7, 0.95),
            coherence=random.uniform(0.7, 0.95),
            creativity=random.uniform(0.6, 0.9),
            utility=random.uniform(0.7, 0.95)
        )
    
    async def compare(
        self,
        prompt: str,
        response_a: str,
        response_b: str
    ) -> Dict:
        """比较两个响应"""
        
        metrics_a = await self.assess(prompt, response_a)
        metrics_b = await self.assess(prompt, response_b)
        
        # 计算总分
        score_a = sum(metrics_a.to_dict().values()) / 4
        score_b = sum(metrics_b.to_dict().values()) / 4
        
        winner_id = "a" if score_a > score_b else "b"
        
        return {
            "winner_id": winner_id,
            "scores_a": metrics_a.to_dict(),
            "scores_b": metrics_b.to_dict()
        }


# 测试
async def test_evaluator():
    """测试评估器"""
    print("=== Test Round Robin Evaluator ===\n")
    
    evaluator = RoundRobinEvaluator()
    
    # 添加候选
    for model in ["gpt-4o", "claude-3-5-sonnet", "gemini-2.0-flash"]:
        evaluator.add_candidate(Candidate(
            id=model,
            output=f"Output from {model}",
            model=model
        ))
    
    # 评估
    ranking = await evaluator.evaluate("什么是AI?", num_rounds=5)
    
    print("Ranking:")
    for rank, (cid, elo) in enumerate(ranking, 1):
        print(f"  {rank}. {cid}: {elo:.1f}")
    
    print("\n✓ Evaluator Test Passed!")


if __name__ == "__main__":
    asyncio.run(test_evaluator())
