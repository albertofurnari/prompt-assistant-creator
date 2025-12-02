"""State machine orchestration for the prompt optimizer."""
from __future__ import annotations

from prompt_optimizer.domain.models import AnalysisResult, OptimizationStep, PromptSession
from prompt_optimizer.llm.client import LLMClient
from prompt_optimizer.prompts.manager import PromptManager


class PromptOptimizerEngine:
    """Drive each optimization step using the configured LLM client."""

    def __init__(self, prompt_manager: PromptManager, client: LLMClient) -> None:
        self._prompt_manager = prompt_manager
        self._client = client

    def process_step(
        self,
        session: PromptSession,
        step: OptimizationStep,
        user_prompt: str,
        feedback: str | None = None,
    ) -> PromptSession:
        """Process a single optimization step and update the session state."""

        prompt = self._prompt_manager.render_analyze_step(
            step=step, user_prompt=user_prompt, session=session, feedback=feedback
        )
        response = self._client.generate(prompt, step=step)

        analysis_result = AnalysisResult(
            step=step,
            summary=response,
            details={"suggestion": response, "prompt": prompt},
        )

        session.parameters[step.value] = response
        session.record_analysis(analysis_result)
        return session
