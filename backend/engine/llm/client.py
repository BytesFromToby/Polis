"""
engine/llm/client.py — LLM provider abstraction.

Providers:
  "anthropic"     — Anthropic Python SDK
  "openai_compat" — OpenAI SDK with base_url override (covers Ollama, LM Studio, OpenAI, etc.)

Config loading priority:
  1. LLM profile (from SimRun.llm_profile_id) — decrypts stored API key
  2. city.llm_config_json — per-city override (backward compat)
  3. Environment variables (LLM_PROVIDER, LLM_MODEL, LLM_API_KEY, LLM_BASE_URL, ...)
  4. Stub fallback — no real LLM call made
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any


# ── Exceptions ────────────────────────────────────────────────────────────────

class LLMError(Exception):
    """Base exception for LLM call failures."""


class LLMTimeoutError(LLMError):
    """Request exceeded configured timeout."""


# ── Config ────────────────────────────────────────────────────────────────────

@dataclass
class LLMConfig:
    provider: str = "stub"       # "anthropic" | "openai_compat" | "stub" | "override"
    model: str = ""
    api_key: str = ""
    base_url: str = ""           # required for openai_compat; ignored for anthropic
    temperature: float = 0.7
    max_tokens: int = 500
    timeout: int = 30            # seconds
    # Transient operator-supplied audience outcome for provider "override" (override-llm_spec).
    # Not serialized (to_json/from_env omit it) — set programmatically per audience/test.
    override: Any = None

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Load config from environment variables. Returns stub config if none set."""
        provider = os.environ.get("LLM_PROVIDER", "stub")
        return cls(
            provider=provider,
            model=os.environ.get("LLM_MODEL", ""),
            api_key=os.environ.get("LLM_API_KEY", ""),
            base_url=os.environ.get("LLM_BASE_URL", ""),
            temperature=float(os.environ.get("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.environ.get("LLM_MAX_TOKENS", "500")),
            timeout=int(os.environ.get("LLM_TIMEOUT", "30")),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "LLMConfig":
        """Deserialise from city.llm_config_json."""
        data = json.loads(json_str)
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def to_json(self) -> str:
        return json.dumps({
            "provider": self.provider,
            "model": self.model,
            "api_key": self.api_key,
            "base_url": self.base_url,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
        })

    @classmethod
    def from_profile(cls, profile: "Any") -> "LLMConfig":
        """Build LLMConfig from an LLMProfile ORM row, decrypting the API key."""
        from engine.llm.crypto import decrypt_api_key
        try:
            api_key = decrypt_api_key(profile.encrypted_api_key) if profile.encrypted_api_key else ""
        except ValueError:
            api_key = ""
        return cls(
            provider=profile.provider,
            model=profile.model,
            api_key=api_key,
            base_url=profile.base_url,
            temperature=profile.temperature,
            max_tokens=profile.max_tokens,
            timeout=profile.timeout,
        )

    @classmethod
    def resolve(
        cls,
        profile: "Any | None" = None,
        city_llm_json: str | None = None,
    ) -> "LLMConfig":
        """Return config from profile, city setting, env vars, or stub — in that order."""
        if profile is not None:
            try:
                return cls.from_profile(profile)
            except Exception:
                pass
        if city_llm_json:
            try:
                return cls.from_json(city_llm_json)
            except Exception:
                pass
        return cls.from_env()


# ── Client ────────────────────────────────────────────────────────────────────

class LLMClient:
    """Routes to Anthropic or OpenAI-compatible provider based on config."""

    def __init__(self, config: LLMConfig):
        self.config = config
        self._client = None
        if config.provider == "stub":
            return
        if config.provider == "override":
            self._client = OverrideLLMClient(config.override)
            return
        if config.provider == "anthropic":
            try:
                import anthropic as _anthropic
                self._client = _anthropic.Anthropic(
                    api_key=config.api_key,
                    timeout=float(config.timeout),
                )
            except ImportError:
                raise LLMError("anthropic package not installed. Run: pip install anthropic")
        elif config.provider == "openai_compat":
            try:
                import openai as _openai
            except ImportError:
                raise LLMError("openai package not installed. Run: pip install openai")
            try:
                kwargs: dict = {"api_key": config.api_key or "ollama", "timeout": float(config.timeout)}
                if config.base_url:
                    kwargs["base_url"] = config.base_url
                self._client = _openai.OpenAI(**kwargs)
            except Exception as exc:
                raise LLMError(f"Failed to initialise OpenAI client: {exc}") from exc
        else:
            raise LLMError(f"Unknown LLM provider: {config.provider!r}")

    def complete(self, system: str, messages: list[dict]) -> str:
        """
        Send a conversation and return the assistant's text response.
        messages: [{"role": "user"|"assistant", "content": str}, ...]
        Raises LLMError on failure.
        """
        if self.config.provider == "stub":
            return StubLLMClient().complete(system, messages)
        if self.config.provider == "override":
            return self._client.complete(system, messages)

        try:
            if self.config.provider == "anthropic":
                return self._complete_anthropic(system, messages)
            else:
                return self._complete_openai(system, messages)
        except LLMTimeoutError:
            raise
        except LLMError:
            raise
        except Exception as exc:
            raise LLMError(f"LLM call failed: {exc}") from exc

    def _complete_anthropic(self, system: str, messages: list[dict]) -> str:
        import anthropic
        try:
            response = self._client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=system,
                messages=messages,
            )
            return response.content[0].text
        except anthropic.APITimeoutError as exc:
            raise LLMTimeoutError("Anthropic request timed out") from exc
        except Exception as exc:
            raise LLMError(f"Anthropic error: {exc}") from exc

    def _complete_openai(self, system: str, messages: list[dict]) -> str:
        import openai
        all_messages = [{"role": "system", "content": system}] + messages
        try:
            response = self._client.chat.completions.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                messages=all_messages,
            )
            return response.choices[0].message.content
        except openai.APITimeoutError as exc:
            raise LLMTimeoutError("OpenAI-compat request timed out") from exc
        except Exception as exc:
            raise LLMError(f"OpenAI-compat error: {exc}") from exc


# ── Stub ──────────────────────────────────────────────────────────────────────

class StubLLMClient:
    """
    Returns valid canned responses at each audience step.
    Used in tests and when no LLM provider is configured.
    """

    def complete(self, system: str, messages: list[dict]) -> str:
        turn = len([m for m in messages if m.get("role") == "assistant"])

        if turn == 0:
            # Step 1 — opening
            return (
                "I appreciate you making time, Mayor. "
                "We have matters to discuss, though I make no promises today."
            )
        if turn == 1:
            # Step 3 — response/counter
            return (
                "An interesting proposal. I will need to consider what you are offering "
                "against what you are asking of us."
            )
        # Step 5 — conclusion (no deal)
        return (
            "I'm afraid we cannot reach an agreement at this time. "
            "Perhaps the terms will be more favourable in future.\n\n"
            "<deal>\n"
            "{\n"
            '  "accepted": false,\n'
            '  "mayor_terms": [],\n'
            '  "faction_terms": [],\n'
            '  "rep_cost_if_broken_by_mayor": 0,\n'
            '  "memory_note": "mayor audience held, no deal reached",\n'
            '  "reasoning": "Stub client always rejects."\n'
            "}\n"
            "</deal>"
        )


# ── Override ────────────────────────────────────────────────────────────────────

class OverrideLLMClient:
    """
    Deterministic "choose the outcome" provider (override-llm_spec). Never calls a model or the
    network — it synthesises the audience output an operator supplies, so the audience flow and
    ResponseParser are unchanged. The conclude turn emits narrative + a well-formed <deal> built
    from the supplied outcome.

    outcome (all optional):
        accepted: bool                       — deal verdict (default False)
        faction_terms / mayor_terms: list[dict]  — deal-term objects (audience_spec schema)
        rep_cost_if_broken_by_mayor: int     — default 20
        memory_note / reasoning: str
        narratives: {"open", "counter", "conclude"}  — per-step text (placeholders if omitted)
    On a reject, both term arrays are emitted empty (the convention the prompt asks the model for).
    """

    def __init__(self, outcome: Any = None):
        self.outcome = dict(outcome) if outcome else {}

    def complete(self, system: str, messages: list[dict]) -> str:
        turn = len([m for m in messages if m.get("role") == "assistant"])
        nar = self.outcome.get("narratives", {}) or {}

        if turn == 0:
            return nar.get("open", "The leader hears the Mayor out, giving nothing away.")
        if turn == 1:
            return nar.get("counter", "The leader weighs the offer in silence, then waits for more.")

        accepted = bool(self.outcome.get("accepted", False))
        deal = {
            "accepted": accepted,
            "mayor_terms": self.outcome.get("mayor_terms", []) if accepted else [],
            "faction_terms": self.outcome.get("faction_terms", []) if accepted else [],
            "rep_cost_if_broken_by_mayor": int(self.outcome.get("rep_cost_if_broken_by_mayor", 20)),
            "memory_note": self.outcome.get("memory_note", "operator-set audience outcome"),
            "reasoning": self.outcome.get("reasoning", "override: operator-supplied outcome"),
        }
        narrative = nar.get("conclude",
                            "The leader gives their answer." if accepted
                            else "The leader declines, for now.")
        return f"{narrative}\n<deal>\n{json.dumps(deal, indent=2)}\n</deal>"
