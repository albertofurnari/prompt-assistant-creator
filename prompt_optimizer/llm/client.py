from __future__ import annotations

import abc

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
        return (f"{prefix} Response for {step_label}: "
            "synthesized output based on prompt."
        )

    def get_token_usage(self) -> TokenUsage:
        return TokenUsage(
            prompt_tokens=self._prompt_tokens,
            completion_tokens=self._completion_tokens,
            cached_tokens=self._cached_tokens,
            cost_usd=0.0,
        )

