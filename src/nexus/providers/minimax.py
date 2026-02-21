"""
MiniMax Provider for Nexus AI Foundation
"""
import os
import sys
import httpx
from typing import List, Dict, Any

from ..core.model_mesh import ModelResponse

MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "")
MINIMAX_BASE_URL = "https://api.minimax.chat/v1"


class MiniMaxProvider:
    """MiniMax API Provider
    
    支持的模型 (2024):
    - MiniMax-M2.5 (最新旗舰模型) ⭐
    - MiniMax-M2.5-highspeed
    - MiniMax-M2.1
    - MiniMax-M2.1-highspeed
    - MiniMax-M2
    - abab6.5s-chat
    - abab6.5g-chat
    """
    
    MODELS = {
        # M2.5 系列 (最新旗舰)
        "MiniMax-M2.5": {
            "name": "MiniMax-M2.5", 
            "context": 200000,
            "description": "最新旗舰模型，代码生成和推理能力最强"
        },
        "MiniMax-M2.5-highspeed": {
            "name": "MiniMax-M2.5-highspeed", 
            "context": 200000,
            "description": "M2.5高速版本"
        },
        # M2.1 系列
        "MiniMax-M2.1": {
            "name": "MiniMax-M2.1", 
            "context": 100000,
            "description": "多语言编程专家"
        },
        "MiniMax-M2.1-highspeed": {
            "name": "MiniMax-M2.1-highspeed", 
            "context": 100000,
            "description": "M2.1高速版本"
        },
        # M2
        "MiniMax-M2": {
            "name": "MiniMax-M2", 
            "context": 200000,
            "description": "Agent能力，函数调用，高级推理"
        },
        # abab 系列
        "abab6.5s-chat": {"name": "abab6.5s-chat", "context": 245760},
        "abab6.5g-chat": {"name": "abab6.5g-chat", "context": 245760},
    }
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or MINIMAX_API_KEY
        self.base_url = MINIMAX_BASE_URL
    
    async def invoke(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> ModelResponse:
        """调用MiniMax API"""
        
        url = f"{self.base_url}/text/chatcompletion_v2"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, 
                json=data, 
                headers=headers, 
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("choices") is None:
                raise Exception(f"API Error: {result.get('base_resp', result)}")
            
            return ModelResponse(
                content=result["choices"][0]["message"]["content"],
                model=model,
                usage={
                    "input_tokens": result.get("usage", {}).get("prompt_tokens", 0),
                    "output_tokens": result.get("usage", {}).get("completion_tokens", 0)
                },
                finish_reason=result["choices"][0]["finish_reason"],
                latency_ms=0
            )


def get_minimax_models() -> Dict[str, Dict]:
    """获取支持的MiniMax模型列表"""
    return MiniMaxProvider.MODELS.copy()
