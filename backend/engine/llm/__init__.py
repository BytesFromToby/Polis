"""
engine/llm — LLM integration layer.

Modules:
  client.py         — LLMConfig, LLMClient, StubLLMClient
  prompt_builder.py — data → natural-language prompt
  response_parser.py — LLM response → structured ParsedAudienceResponse
  memory.py         — faction memory note creation and compression
  audiences.py      — full audience flow (wires all layers)
"""
from .client import LLMConfig, LLMClient, StubLLMClient, LLMError, LLMTimeoutError
from .response_parser import ResponseParser, ParsedAudienceResponse
from .prompt_builder import PromptBuilder
from .memory import MemoryWriter

__all__ = [
    "LLMConfig", "LLMClient", "StubLLMClient", "LLMError", "LLMTimeoutError",
    "ResponseParser", "ParsedAudienceResponse",
    "PromptBuilder",
    "MemoryWriter",
]
