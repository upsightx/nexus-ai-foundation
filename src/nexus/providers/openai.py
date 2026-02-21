"""
OpenAI Compatible Provider for Nexus AI
"""
import os
import httpx
from typing import List, Dict, Any

from ..core.model_mesh import ModelResponse

class OpenAIProvider:
    """OpenAI API Provider
    
    支持的模型:
    - gpt-4o
    - gpt-4o-mini
    - o1-preview
    - o1-mini
    """
    
    MODELS = {
        "gpt-4o": {"context": 128000, "max_output": 16384},
        "gpt-4o-mini": {"context": 128000, "max_output": 16384},
        "o1-preview": {"context": 128000, "max_output": 32768},
        "o1-mini": {"context": 128000, "max_output": 65536},
        "gpt-4-turbo": {"context": 128000, "max_output": 4096},
    }
    
    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.base_url = base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    
    async def invoke(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> ModelResponse:
        
        url = f"{self.base_url}/chat/completions"
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
            response = await client.post(url, json=data, headers=headers, timeout=60)
            response.raise_for_status()
            result = response.json()
            
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
