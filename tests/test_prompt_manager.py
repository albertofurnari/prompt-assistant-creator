from __future__ import annotations

from prompt_optimizer.domain.models import PromptSession
from prompt_optimizer.prompts.manager import PromptManager


def test_render_global_harmonize_serializes_non_json_primitives() -> None:
    manager = PromptManager()
    session = PromptSession()

    rendered = manager.render_global_harmonize(session)

    assert str(session.session_id) in rendered
    assert session.created_at.isoformat() in rendered


def test_render_global_harmonize_includes_json_session_payload() -> None:
    manager = PromptManager()
    session = PromptSession(parameters={"goal": "improve clarity"})

    rendered = manager.render_global_harmonize(session)

    assert '"parameters": {"goal": "improve clarity"}' in rendered
