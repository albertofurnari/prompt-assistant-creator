"""Prompt template management for the Prompt Optimizer."""
from __future__ import annotations

import json
from textwrap import dedent

from prompt_optimizer.domain.models import OptimizationStep, PromptSession


class PromptManager:
    """Render templated prompts used throughout the optimization pipeline."""

    analyze_step_template = dedent(
        """
        You are assisting with the prompt optimization process.
        Evaluate and expand the "{step_label}" dimension of the prompt.

        Draft prompt:
        {user_prompt}

        Previously collected parameters:
        {parameters}

        Additional guidance from the operator (optional):
        {feedback}

        Respond with a concise recommendation for the {step_label} and
        include a short justification. Keep the answer plain text.
        """
    ).strip()

    global_harmonize_template = dedent(
        """
        You are the final reviewer for an optimized prompt.
        Given the session state below, harmonize the components into a single,
        coherent prompt ready for execution. Resolve any inconsistencies and
        preserve the user's intent.

        Session state (JSON):
        {session_state}

        Return the harmonized prompt as polished Markdown. Include a brief note
        explaining the key changes you applied to ensure consistency.
        """
    ).strip()

    def render_analyze_step(
        self,
        step: OptimizationStep,
        user_prompt: str,
        session: PromptSession,
        feedback: str | None = None,
    ) -> str:
        """Render the analysis prompt for a specific optimization step."""

        feedback_value = feedback if feedback is not None else "None provided"
        return self.analyze_step_template.format(
            step_label=step.value.replace("_", " ").title(),
            user_prompt=user_prompt,
            parameters=json.dumps(session.parameters),
            feedback=feedback_value,
        )

    def render_global_harmonize(self, session: PromptSession) -> str:
        """Render the harmonization prompt for the full session state."""

        return self.global_harmonize_template.format(
            session_state=json.dumps(session.model_dump(mode="json"))
        )
