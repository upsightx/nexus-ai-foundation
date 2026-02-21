"""
Anthropic (Claude) Provider for Nexus AI
"""
import os
import httpx
from typing import List, Dict, Any

from ..core.model_mesh import ModelResponse

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_BASE_URL = "https://api.anthropic.com/v1"


class AnthropicProvider:
    """Anthropic Claude API Provider
    
    支持的模型:
    - claude-3-5-sonnet
    - claude-3-5-haiku
    - claude-3-opus
    - claude-3-sonnet
    """
    
    MODELS = {
        "claude-3-5-sonnet-20241022": {
            "name": "claude-3-5-sonnet-20241022",
            "context": 200000,
            "description": "最新 Sonnet 模型"
        },
        "claude-3-5-haiku": {
            "name": "claude-3-5-haiku-20241022",
            "context": 200000,
            "description": "快速响应模型"
        },
        "claude-3-opus": {
            "name": "claude-3-opus-20240229",
            "context": 200000,
            "description": "最强推理模型"
        },
        "claude-3-sonnet": {
            "name": "claude-3-sonnet-20240229",
            "context": 200000,
            "description": "平衡模型"
        },
    }
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or ANTHROPIC_API_KEY
        self.base_url = ANTHROPIC_BASE_URL
    
    async def invoke(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> ModelResponse:
        
        url = f"{self.base_url}/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        # 转换消息格式
        system = ""
        claude_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                claude_messages.append(msg)
        
        data = {
            "model": model,
            "messages": claude_messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        if system:
            data["system"] = system
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data, headers=headers, timeout=60)
            response.raise_for_status()
            result = response.json()
            
            return ModelResponse(
                content=result["content"][0]["text"],
                model=model,
                usage={
                    "input_tokens": result.get("usage", {}).get("input_tokens", 0),
                    "output_tokens": result.get("usage", {}).get("output_tokens", 0)
                },
                finish_reason=result.get("stop_reason", "stop"),
                latency_ms=0
            )
