"""Prompt template management for the Prompt Optimizer."""
from __future__ import annotations

import json

from jinja2 import Environment, StrictUndefined

from prompt_optimizer.domain.models import OptimizationStep, PromptSession


class PromptManager:
    """Render Jinja2 templates used throughout the optimization pipeline."""

    analyze_step_template = (
        """
        You are assisting with the prompt optimization process.
        Evaluate and expand the "{{ step_label }}" dimension of the prompt.

        Draft prompt:
        {{ user_prompt }}

        Previously collected parameters:
        {{ parameters | tojson }}

        Additional guidance from the operator (optional):
        {{ feedback | default("None provided", true) }}

        Respond with a concise recommendation for the {{ step_label }} and
        include a short justification. Keep the answer plain text.
        """
    ).strip()

    global_harmonize_template = (
        """
        You are the final reviewer for an optimized prompt.
        Given the session state below, harmonize the components into a single,
        coherent prompt ready for execution. Resolve any inconsistencies and
        preserve the user's intent.

        Session state (JSON):
        {{ session_state | tojson }}

        Return the harmonized prompt as polished Markdown. Include a brief note
        explaining the key changes you applied to ensure consistency.
        """
    ).strip()

    def __init__(self) -> None:
        self._environment = Environment(undefined=StrictUndefined)
        self._environment.filters["tojson"] = json.dumps

    def render_analyze_step(
        self,
        step: OptimizationStep,
        user_prompt: str,
        session: PromptSession,
        feedback: str | None = None,
    ) -> str:
        """Render the analysis prompt for a specific optimization step."""

        template = self._environment.from_string(self.analyze_step_template)
        return template.render(
            step_label=step.value.replace("_", " ").title(),
            user_prompt=user_prompt,
            parameters=session.parameters,
            feedback=feedback,
        )

    def render_global_harmonize(self, session: PromptSession) -> str:
        """Render the harmonization prompt for the full session state."""

        template = self._environment.from_string(self.global_harmonize_template)
        return template.render(session_state=session.model_dump())
