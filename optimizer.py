from __future__ import annotations

from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from pydantic_settings import BaseSettings, SettingsConfigDict
from rich.console import Console
from rich.panel import Panel

from prompt_optimizer.domain.models import OptimizationStep
from prompt_optimizer.llm.client import MockLLMClient


class AppSettings(BaseSettings):
    """Application settings sourced from the environment or .env file."""

    model_config = SettingsConfigDict(
        env_prefix="PROMPT_OPT_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    default_step: OptimizationStep = OptimizationStep.USER_INTENT


console = Console()


def run_cli(settings: AppSettings, client: MockLLMClient) -> None:
    console.print(
        Panel.fit(
            "Prompt Optimizer CLI\n"
            "State Machine: User Intent → Parameters → Harmonization → Final Output",
            title="Welcome",
        )
    )
    console.print(f"Using backend mode: [bold]{client.mode}[/bold]\n")

    prompt_session: PromptSession[str] = PromptSession()
    with patch_stdout():
        user_prompt: str | None = prompt_session.prompt(
            "Enter a draft prompt (or 'exit'): "
        )

    if user_prompt and user_prompt.strip().lower() != "exit":
        response = client.generate(user_prompt, step=settings.default_step)
        console.print("\n[bold green]Mock LLM Response[/bold green]")
        console.print(response)

    console.print("\n[dim]Session complete. Goodbye![/dim]")


def main() -> None:
    settings = AppSettings()
    client = MockLLMClient(mode="dry-run")
    run_cli(settings, client)


if __name__ == "__main__":
    main()
