"""Global harmonization stage for prompt optimization."""
from __future__ import annotations

from prompt_optimizer.domain.models import AnalysisResult, OptimizationStep, PromptSession
from prompt_optimizer.llm.client import LLMClient
from prompt_optimizer.prompts.manager import PromptManager


class GlobalHarmonizer:
    """Perform a consistency sweep across all collected prompt parameters."""

    def __init__(self, prompt_manager: PromptManager, client: LLMClient) -> None:
        self._prompt_manager = prompt_manager
        self._client = client

    def harmonize(self, session: PromptSession) -> PromptSession:
        """Run the harmonization prompt and update the session with the result."""

        harmonize_prompt = self._prompt_manager.render_global_harmonize(session)
        response = self._client.generate(
            harmonize_prompt, step=OptimizationStep.HARMONIZATION
        )

        harmonization_result = AnalysisResult(
            step=OptimizationStep.HARMONIZATION,
            summary="Harmonized the prompt based on the full session state.",
            details={"harmonized_prompt": response},
        )
        session.record_analysis(harmonization_result)

        final_output_result = AnalysisResult(
            step=OptimizationStep.FINAL_OUTPUT,
            summary="Final optimized prompt ready for use.",
            details={"final_prompt": response},
        )
        session.parameters[OptimizationStep.FINAL_OUTPUT.value] = response
        session.record_analysis(final_output_result)

        return session
