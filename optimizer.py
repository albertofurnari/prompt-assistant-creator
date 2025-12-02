from __future__ import annotations

from prompt_toolkit import PromptSession as PromptToolkitSession
from prompt_toolkit.patch_stdout import patch_stdout
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.theme import Theme

from prompt_optimizer.domain.models import OptimizationStep, PromptSession
from prompt_optimizer.llm.client import (
    GeminiLLMClient,
    LLMClient,
    MockLLMClient,
    OpenAILLMClient,
)
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
    primary_color: str = "#7FB3D5"
    accent_color: str = "#82E0AA"
    muted_color: str = "#ABB2B9"
    border_color: str = "#A9CCE3"
    warning_color: str = "#F7DC6F"
    error_color: str = "#E6B0AA"


def build_console(settings: AppSettings) -> Console:
    """Create a themed Rich console using a relaxing palette."""

    theme = Theme(
        {
            "primary": settings.primary_color,
            "accent": settings.accent_color,
            "muted": settings.muted_color,
            "warning": settings.warning_color,
            "error": settings.error_color,
            "success": settings.accent_color,
        }
    )

    return Console(theme=theme)

def build_client(model_choice: str, settings: AppSettings) -> LLMClient:
    """Instantiate an LLM client based on the user's selection."""

    if model_choice == "gemini-2.5-flash":
        if not settings.gemini_api_key:
            raise ValueError("Gemini API key not configured.")
        return GeminiLLMClient(model_choice, api_key=settings.gemini_api_key)

    if model_choice == "gpt-5":
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured.")
        return OpenAILLMClient(model_choice, api_key=settings.openai_api_key)

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

    if normalized in {"mock", "dry-run", "dryrun"}:
        return "mock"

    return None


def prompt_for_input(session: PromptToolkitSession, message: str) -> str:
    """Prompt the user for input while keeping stdout patched for Rich."""

    with patch_stdout():
        return session.prompt(message)


def prompt_for_multiline(session: PromptToolkitSession, message: str) -> str:
    """Prompt the user for multi-line input."""

    lines: list[str] = []

    with patch_stdout():
        while True:
            try:
                prompt_message = message if not lines else "... "
                line = session.prompt(prompt_message)
            except EOFError:
                # Finish input on Ctrl-D even when the buffer is empty.
                break

            if line == "":
                # An empty line ends the multi-line capture.
                break

            lines.append(line)

    return "\n".join(lines)


def run_cli(settings: AppSettings, console: Console) -> None:
    """Run the interactive Prompt Optimizer CLI workflow."""

    welcome_message = (
        "Prompt Optimizer CLI\n"
        "State Machine: User Intent → Parameters → Harmonization → Final Output"
    )
    console.print(
        Panel.fit(
            welcome_message,
            title="[accent]Welcome[/accent]",
            border_style=settings.border_color,
            style="primary",
        )
    )

    prompt_manager = PromptManager()
    prompt_session: PromptToolkitSession[str] = PromptToolkitSession()

    while True:
        console.print(
            Panel.fit(
                "[1] Gemini (gemini-2.5-flash)\n[2] ChatGPT (gpt-5)",
                title="[accent]Select Model[/accent]",
                border_style=settings.border_color,
                style="primary",
            )
        )

        model_choice: str | None = None
        while model_choice is None:
            raw_choice = prompt_for_input(
                prompt_session, "Choose a model [1/2]: "
            ).strip()

            normalized_choice = _normalize_model_choice(raw_choice)
            default_choice = _normalize_model_choice(settings.default_model)

            model_choice = normalized_choice or default_choice

            if model_choice is None:
                console.print(
                    "[error]Invalid selection. Please choose '1' for Gemini or '2' for ChatGPT.[/error]"
                )

        try:
            client = build_client(model_choice, settings)
        except ValueError as error:
            console.print(
                f"[error]{error} Please set the required API key and retry.[/error]\n"
            )
            continue
        engine = PromptOptimizerEngine(prompt_manager=prompt_manager, client=client)
        harmonizer = GlobalHarmonizer(prompt_manager=prompt_manager, client=client)

        console.print(
            f"Using backend mode: [accent]{model_choice}[/accent]\n"
        )
        console.print(
            "[muted]Enter a draft prompt. Finish input with Ctrl-D or an empty line on a new prompt.[/muted]"
        )
        raw_prompt = prompt_for_multiline(
            prompt_session, "Draft Prompt (multi-line supported): "
        ).strip()

        if not raw_prompt or raw_prompt.strip().lower() == "exit":
            console.print("\n[muted]Session aborted by user.[/muted]")
            return

        session_state = PromptSession(parameters={"draft_prompt": raw_prompt})

        steps_to_run = [
            OptimizationStep.USER_INTENT,
            OptimizationStep.ROLE,
            OptimizationStep.OBJECTIVE,
            OptimizationStep.CONTEXT,
            OptimizationStep.AUDIENCE,
            OptimizationStep.KEY_POINTS,
            OptimizationStep.CONSTRAINTS,
            OptimizationStep.OUTPUT,
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
                    progress.add_task(
                        f"Generating {step.name.replace('_', ' ').title()}...",
                        total=None,
                    )
                    analysis_result = engine.process_step(
                        session=session_state,
                        step=step,
                        user_prompt=raw_prompt,
                        feedback=feedback,
                    )

                console.print(
                    Panel(
                        analysis_result.summary,
                        title=f"[accent]{step.name.replace('_', ' ').title()}[/accent]",
                        subtitle="Accept this suggestion?",
                        border_style=settings.border_color,
                        style="primary",
                    )
                )

                confirmation = prompt_for_input(prompt_session, "Accept? [Y/n]: ")
                if confirmation.strip().lower().startswith("n"):
                    feedback = prompt_for_input(
                        prompt_session, "Provide feedback for refinement: "
                    )
                    continue

                session_state.parameters[step.value] = analysis_result.summary
                session_state.record_analysis(analysis_result)
                confirmed = True

        with Progress(
            SpinnerColumn(),
            TextColumn("{task.description}"),
            transient=True,
            console=console,
        ) as progress:
            progress.add_task("Harmonizing final prompt...", total=None)
            session_state = harmonizer.harmonize(session_state)

        final_prompt = session_state.parameters.get(
            OptimizationStep.FINAL_OUTPUT.value, ""
        )
        console.print(
            Panel(
                Markdown(final_prompt),
                title="[accent]Optimized Prompt[/accent]",
                border_style=settings.border_color,
                style="primary",
            )
        )

        restart = prompt_for_input(prompt_session, "Restart session? [y/N]: ").strip().lower()
        if restart not in {"y", "yes"}:
            console.print("\n[muted]Session complete. Goodbye![/muted]")
            return


def main() -> None:
    settings = AppSettings()
    console = build_console(settings)

    try:
        run_cli(settings=settings, console=console)
    except KeyboardInterrupt:
        console.print("\n[red]Interrupted by user. Exiting...[/red]")


if __name__ == "__main__":
    main()
