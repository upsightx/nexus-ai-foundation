"""
OpenRouter Provider - One API for all major LLMs
"""
import os
import httpx
from typing import List, Dict, Any

from ..core.model_mesh import ModelResponse

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterProvider:
    """OpenRouter API Provider - 聚合众多模型
    
    支持数百种模型，包括:
    - OpenAI: gpt-4o, gpt-4o-mini, o1
    - Anthropic: claude-3.5-sonnet, claude-3-opus
    - Google: gemini-1.5-pro, gemini-flash
    - Meta: llama-3.1-70b, llama-3.1-8b
    - Mistral: mistral-large, mistral-small
    - 以及更多...
    """
    
    # 热门模型列表
    MODELS = {
        # OpenAI
        "openai/gpt-4o": {"context": 128000},
        "openai/gpt-4o-mini": {"context": 128000},
        "openai/o1-preview": {"context": 128000},
        "openai/o1-mini": {"context": 128000},
        
        # Anthropic
        "anthropic/claude-3.5-sonnet": {"context": 200000},
        "anthropic/claude-3-opus": {"context": 200000},
        "anthropic/claude-3-haiku": {"context": 200000},
        
        # Google
        "google/gemini-1.5-pro": {"context": 200000},
        "google/gemini-1.5-flash": {"context": 1000000},
        "google/gemini-2.0-flash": {"context": 1000000},
        
        # Meta
        "meta-llama/llama-3.1-70b-instruct": {"context": 128000},
        "meta-llama/llama-3.1-8b-instruct": {"context": 128000},
        
        # Mistral
        "mistralai/mistral-large": {"context": 128000},
        "mistralai/mistral-small": {"context": 128000},
        
        # DeepSeek
        "deepseek/deepseek-chat": {"context": 64000},
        
        # Qwen
        "qwen/qwen-2.5-72b-instruct": {"context": 32768},
        "qwen/qwen-2.5-7b-instruct": {"context": 32768},
        
        # MiniMax
        "minimax/minimax-text-01": {"context": 32000},
        
        # Nous
        "nousresearch/hermes-3-llama-3.1-70b": {"context": 128000},
        
        # Cognitive
        "cognitivecomputations/dolphin-mixtral-8x7b": {"context": 32000},
    }
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or OPENROUTER_API_KEY
        self.base_url = OPENROUTER_BASE_URL
    
    async def invoke(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> ModelResponse:
        
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/nexus-ai",
            "X-Title": "Nexus AI Foundation"
        }
        
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data, headers=headers, timeout=120)
            response.raise_for_status()
            result = response.json()
            
            return ModelResponse(
                content=result["choices"][0]["message"]["content"],
                model=model,
                usage={
                    "input_tokens": result.get("usage", {}).get("prompt_tokens", 0),
                    "output_tokens": result.get("usage", {}).get("completion_tokens", 0)
                },
                finish_reason=result["choices"][0].get("finish_reason", "stop"),
                latency_ms=0
            )
    
    def list_models(self) -> Dict[str, Dict]:
        """获取OpenRouter支持的模型列表"""
        return self.MODELS.copy()
