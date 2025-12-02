from __future__ import annotations

import abc

import google.generativeai as genai
from openai import OpenAI

from prompt_optimizer.domain.models import OptimizationStep, TokenUsage


class LLMClient(abc.ABC):
    """Abstract base class describing the minimum LLM client contract."""

    mode: str

    @abc.abstractmethod
    def generate(self, prompt: str, step: OptimizationStep | None = None) -> str:
        """Produce a response for the provided prompt."""

    @abc.abstractmethod
    def get_token_usage(self) -> TokenUsage:
        """Return the accumulated token usage for the client."""


class MockLLMClient(LLMClient):
    """Deterministic, offline implementation for dry-run and testing flows."""

    def __init__(self, mode: str = "dry-run") -> None:
        self.mode = mode
        self._prompt_tokens = 0
        self._completion_tokens = 0
        self._cached_tokens = 0

    def generate(self, prompt: str, step: OptimizationStep | None = None) -> str:
        prompt_tokens = len(prompt.split())
        completion_tokens = max(1, prompt_tokens // 2)

        self._prompt_tokens += prompt_tokens
        self._completion_tokens += completion_tokens

        prefix = "[MOCK]"
        step_label = step.value if step else "general"
        return (
            f"{prefix} Response for {step_label}: "
            "synthesized output based on prompt."
        )

    def get_token_usage(self) -> TokenUsage:
        return TokenUsage(
            prompt_tokens=self._prompt_tokens,
            completion_tokens=self._completion_tokens,
            cached_tokens=self._cached_tokens,
            cost_usd=0.0,
        )


class OpenAILLMClient(LLMClient):
    """OpenAI-powered client for live GPT-style generations."""

    def __init__(self, model: str, api_key: str) -> None:
        self.mode = model
        self._model = model
        self._client = OpenAI(api_key=api_key)
        self._usage = TokenUsage()

    def generate(self, prompt: str, step: OptimizationStep | None = None) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
        )

        message = response.choices[0].message.content or ""
        usage = response.usage

        prompt_tokens = usage.prompt_tokens if usage else 0
        completion_tokens = usage.completion_tokens if usage else 0

        self._usage = TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cached_tokens=0,
            cost_usd=0.0,
        )

        return message

    def get_token_usage(self) -> TokenUsage:
        return self._usage


class GeminiLLMClient(LLMClient):
    """Gemini-powered client for Google Generative AI models."""

    def __init__(self, model: str, api_key: str) -> None:
        self.mode = model
        self._model = model
        self._usage = TokenUsage()
        genai.configure(api_key=api_key)
        self._client = genai.GenerativeModel(model)

    def generate(self, prompt: str, step: OptimizationStep | None = None) -> str:
        response = self._client.generate_content(prompt)
        usage_metadata = response.usage_metadata
        if usage_metadata is None:
            self._usage = TokenUsage()
            return response.text
        prompt_tokens = usage_metadata.prompt_token_count or 0
        completion_tokens = usage_metadata.candidates_token_count or 0
        total_tokens = usage_metadata.total_token_count or 0
        cached_tokens = max(total_tokens - (prompt_tokens + completion_tokens), 0)

        self._usage = TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cached_tokens=cached_tokens,
            cost_usd=0.0,
        )

        return response.text

    def get_token_usage(self) -> TokenUsage:
        return self._usage

