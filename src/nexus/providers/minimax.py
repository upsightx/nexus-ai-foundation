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
    
    支持的模型:
    - abab6.5s-chat (推荐)
    - abab6.5g-chat
    - abab6-chat
    """
    
    MODELS = {
        "abab6.5s-chat": {"name": "abab6.5s-chat", "context": 245760},
        "abab6.5g-chat": {"name": "abab6.5g-chat", "context": 245760},
        "abab6-chat": {"name": "abab6-chat", "context": 245760},
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
