from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class OptimizationStep(str, Enum):
    """Enumerates the ordered stages of the optimization pipeline."""

    USER_INTENT = "user_intent"
    ROLE = "role"
    OBJECTIVE = "objective"
    CONTEXT = "context"
    AUDIENCE = "audience"
    KEY_POINTS = "key_points"
    CONSTRAINTS = "constraints"
    OUTPUT = "output"
    HARMONIZATION = "harmonization"
    FINAL_OUTPUT = "final_output"


class TokenUsage(BaseModel):
    """Tracks LLM token usage and the associated telemetry data."""

    model_config = ConfigDict(frozen=True)

    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    cached_tokens: int = Field(default=0, ge=0)
    cost_usd: float = Field(default=0.0, ge=0.0)

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens + self.cached_tokens


class AnalysisResult(BaseModel):
    """Represents the structured output produced by each optimization stage."""

    step: OptimizationStep
    summary: str
    details: dict[str, str] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PromptSession(BaseModel):
    """Captures the ongoing state and history of a user's optimization session."""

    session_id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    current_step: OptimizationStep = OptimizationStep.USER_INTENT
    completed_steps: list[OptimizationStep] = Field(default_factory=list)
    parameters: dict[str, str] = Field(default_factory=dict)
    analysis_history: list[AnalysisResult] = Field(default_factory=list)
    token_usage: TokenUsage | None = None

    @property
    def is_complete(self) -> bool:
        return self.current_step == OptimizationStep.FINAL_OUTPUT

    def record_analysis(self, result: AnalysisResult) -> None:
        """Append an analysis result and advance tracking metadata."""
        self.analysis_history.append(result)
        if result.step not in self.completed_steps:
            self.completed_steps.append(result.step)
        self.current_step = result.step

