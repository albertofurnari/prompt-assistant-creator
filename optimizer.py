from __future__ import annotations

from prompt_toolkit import PromptSession as PromptToolkitSession
from prompt_toolkit.patch_stdout import patch_stdout
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from prompt_optimizer.domain.models import OptimizationStep, PromptSession
from prompt_optimizer.llm.client import LLMClient, MockLLMClient
from prompt_optimizer.pipelines.harmonizer import GlobalHarmonizer
from prompt_optimizer.prompts.manager import PromptManager
from prompt_optimizer.state_machine.engine import PromptOptimizerEngine


class AppSettings(BaseSettings):
    """Application settings sourced from the environment or .env file."""

    model_config = SettingsConfigDict(
        env_prefix="PROMPT_OPT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
    )

    default_model: str = "mock"
    openai_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "openai_api_key", "OPENAI_API_KEY", "PROMPT_OPT_OPENAI_API_KEY"
        ),
    )
    gemini_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "gemini_api_key", "GEMINI_API_KEY", "PROMPT_OPT_GEMINI_API_KEY"
        ),
    )


def build_client(model_choice: str) -> LLMClient:
    """Instantiate an LLM client based on the user's selection."""

    return MockLLMClient(mode=model_choice)


def _normalize_model_choice(choice: str) -> str | None:
    """Normalize user input into a supported model identifier."""

    normalized = choice.strip().lower()

    if not normalized:
        return None

    if normalized in {"1", "gemini", "gemini-2.5-flash", "gemini 2.5 flash"}:
        return "gemini-2.5-flash"

    if normalized in {"2", "chatgpt", "gpt-5", "gpt5"}:
        return "gpt-5"

    return None


def prompt_for_input(session: PromptToolkitSession, message: str) -> str:
    """Prompt the user for input while keeping stdout patched for Rich."""

    with patch_stdout():
        return session.prompt(message)


def run_cli(settings: AppSettings, console: Console) -> None:
    """Run the interactive Prompt Optimizer CLI workflow."""

    console.print(
        Panel.fit(
            "Prompt Optimizer CLI\n"
            "State Machine: User Intent → Parameters → Harmonization → Final Output",
            title="Welcome",
        )
    )

    prompt_manager = PromptManager()
    prompt_session: PromptToolkitSession[str] = PromptToolkitSession()

    console.print(
        Panel(
            "[1] Gemini (gemini-2.5-flash)\n[2] ChatGPT (gpt-5)",
            title="Select Model",
        )
    )

    model_choice: str | None = None
    while model_choice is None:
        raw_choice = prompt_for_input(
            prompt_session, "Choose a model [1/2]: "
        ).strip()
        model_choice = _normalize_model_choice(raw_choice) or _normalize_model_choice(
            settings.default_model
        )

        if model_choice is None:
            console.print(
                "[red]Invalid selection. Please choose '1' for Gemini or '2' for ChatGPT.[/red]"
            )

    client = build_client(model_choice)
    engine = PromptOptimizerEngine(prompt_manager=prompt_manager, client=client)
    harmonizer = GlobalHarmonizer(prompt_manager=prompt_manager, client=client)

    console.print(f"Using backend mode: [bold]{model_choice}[/bold]\n")

    raw_prompt = prompt_for_input(prompt_session, "Enter a draft prompt (or 'exit'): ")

    if not raw_prompt or raw_prompt.strip().lower() == "exit":
        console.print("\n[dim]Session aborted by user.[/dim]")
        return

    session_state = PromptSession(parameters={"user_intent": raw_prompt})

    steps_to_run = [
        OptimizationStep.USER_INTENT,
        OptimizationStep.ROLE,
        OptimizationStep.OBJECTIVE,
        OptimizationStep.AUDIENCE,
        OptimizationStep.TONE,
        OptimizationStep.CONSTRAINTS,
        OptimizationStep.CONTEXT,
    ]

    for step in steps_to_run:
        confirmed = False
        feedback: str | None = None

        while not confirmed:
            with Progress(
                SpinnerColumn(),
                TextColumn("{task.description}"),
                transient=True,
                console=console,
            ) as progress:
                progress.add_task(f"Generating {step.name.title()}...", total=None)
                session_state = engine.process_step(
                    session=session_state,
                    step=step,
                    user_prompt=raw_prompt,
                    feedback=feedback,
                )

            latest_result = session_state.analysis_history[-1]
            console.print(
                Panel(
                    latest_result.summary,
                    title=f"{step.name.replace('_', ' ').title()}",
                    subtitle="Accept this suggestion?",
                )
            )

            confirmation = prompt_for_input(prompt_session, "Accept? [Y/n]: ")
            if confirmation.strip().lower().startswith("n"):
                feedback = prompt_for_input(
                    prompt_session, "Provide feedback for refinement: "
                )
                continue

            confirmed = True

    with Progress(
        SpinnerColumn(), TextColumn("{task.description}"), transient=True, console=console
    ) as progress:
        progress.add_task("Harmonizing final prompt...", total=None)
        session_state = harmonizer.harmonize(session_state)

    final_prompt = session_state.parameters.get(OptimizationStep.FINAL_OUTPUT.value, "")
    console.print(Panel(Markdown(final_prompt), title="Optimized Prompt"))
    console.print("\n[dim]Session complete. Goodbye![/dim]")


def main() -> None:
    console = Console()
    settings = AppSettings()

    try:
        run_cli(settings=settings, console=console)
    except KeyboardInterrupt:
        console.print("\n[red]Interrupted by user. Exiting...[/red]")


if __name__ == "__main__":
    main()
