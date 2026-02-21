"""
Google Gemini Provider for Nexus AI
"""
import os
import httpx
from typing import List, Dict, Any

from ..core.model_mesh import ModelResponse

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


class GeminiProvider:
    """Google Gemini API Provider
    
    支持的模型:
    - gemini-2.0-flash
    - gemini-2.0-pro
    - gemini-1.5-flash
    - gemini-1.5-pro
    """
    
    MODELS = {
        "gemini-2.0-flash": {
            "context": 1000000,
            "description": "最新高速模型"
        },
        "gemini-2.0-pro": {
            "context": 2000000,
            "description": "最强推理模型"
        },
        "gemini-1.5-flash": {
            "context": 1000000,
            "description": "快速响应"
        },
        "gemini-1.5-pro": {
            "context": 2000000,
            "description": "高级推理"
        },
    }
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or GOOGLE_API_KEY
    
    async def invoke(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> ModelResponse:
        
        url = f"{GEMINI_BASE_URL}/models/{model}:generateContent?key={self.api_key}"
        
        # 转换消息格式
        contents = []
        for msg in messages:
            if msg["role"] == "user":
                contents.append({
                    "role": "user",
                    "parts": [{"text": msg["content"]}]
                })
            elif msg["role"] == "model":
                contents.append({
                    "role": "model",
                    "parts": [{"text": msg["content"]}]
                })
        
        data = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()
            
            content = result["candidates"][0]["content"]["parts"][0]["text"]
            
            return ModelResponse(
                content=content,
                model=model,
                usage={
                    "input_tokens": result.get("usageMetadata", {}).get("promptTokenCount", 0),
                    "output_tokens": result.get("usageMetadata", {}).get("candidatesTokenCount", 0)
                },
                finish_reason="stop",
                latency_ms=0
            )
