"""Nexus AI - Providers Package

支持多种大模型API:
- MiniMax: 国产大模型
- OpenAI: GPT系列
- Anthropic: Claude系列
- Google: Gemini系列
- OpenRouter: 聚合众多模型
"""

from .minimax import MiniMaxProvider, get_minimax_models
from .openai import OpenAIProvider
from .anthropic import AnthropicProvider
from .gemini import GeminiProvider
from .openrouter import OpenRouterProvider

__all__ = [
    "MiniMaxProvider",
    "get_minimax_models",
    "OpenAIProvider",
    "AnthropicProvider", 
    "GeminiProvider",
    "OpenRouterProvider",
]
