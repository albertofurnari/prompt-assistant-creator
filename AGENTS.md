# Repository Guidelines

## 1. Architecture Overview

The project adopts a **modular, deterministic, and test-centric architecture**. The CLI is strictly a thin orchestration layer; all core logic resides in dedicated modules to ensure clarity, auditability, and reusability.

### Core Layers

1. **Domain Models (`prompt_optimizer/domain/`)**  
   Single source of truth. Pydantic models defining `PromptSession`, `OptimizationStep`, `TokenUsage`, and `AnalysisResult`. No raw dictionaries passed between layers.

2. **State Machine (`prompt_optimizer/state_machine/`)**  
   Defines transitions, guards, rollback logic, and recovery paths. Must remain deterministic, pure, and fully unit-testable.  
   *Constraint:* State persistence must be serializable (JSON/Pickle) to allow session resumption.

3. **Harmonization Pipelines (`prompt_optimizer/pipelines/`)**  
   Multi-stage transformations: parse → validate → normalize → optimize → render.  
   *Contract:* Every stage **must** accept and return Pydantic Models. Raw dicts are strictly forbidden.

4. **LLM Client Abstraction (`prompt_optimizer/llm/`)**  
   Unified interface for GPT, Gemini, and others.  
   **Operational Modes:**

      - `dry-run`: No network calls (mocks).
      - `record`: Real calls, creating VCR cassettes.
      - `replay`: Deterministic execution from cassettes.
      - `live`: Production mode.  
        **Telemetry:** Tracks token usage, latency, retry counts, model version, and total session cost.

5. **Internal Prompt Registry (`prompt_optimizer/prompts/`)**  
   Repository of the meta-prompts used by the system (e.g., `analyzer_system_prompt.jinja2`). Separation of code and prompt logic.

6. **Tracing & Observability (`prompt_optimizer/tracing/`)**  
   Generates an internal graph of the pipeline execution. Captures snapshots of state transitions, intermediate transforms, and LLM reasoning steps for deep debugging and auditing.

7. **UI Layer (`prompt_optimizer/ui/`)**  
   Rich-based interactive components and CLI renderers. Fully presentation-only—no state manipulation.

-----

## 2. Project Structure & Files

- `optimizer.py`: CLI entry point.
- `prompt_optimizer/`:
    - `domain/`: Pydantic schemas and types.
    - `state_machine/`: FSM logic.
    - `pipelines/`: Processing logic.
    - `llm/`: API wrappers and telemetry agents.
    - `tracing/`: Execution graph and snapshotting.
    - `prompts/`: Jinja2 templates for internal system prompts.
    - `adapters/`: IO handling (YAML/JSON).
    - `utils/`: Generic helpers.
- `assets/`: User-facing templates, examples.
- `tests/`:
    - `unit/`: Fast, isolated tests.
    - `integration/`: VCR-backed API tests.
    - `snapshots/`: UI rendering verification.
- `.env.example`: Template for secrets.
- `Makefile`: Build automation.

-----

## 3. Coding Standards

### Language & Tools

- Target **Python 3.10+**.
- **Black** for formatting (line length 88).
- **Ruff** for linting (strict ruleset).
- **mypy --strict** for static typing (No `Any` allowed in core logic).
- **Pydantic V2** for data validation.

### Naming Conventions

- Modules: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE`
- CLI flags: `--kebab-case`
- Pydantic Models: Suffix `Schema` or `Model` (e.g., `PromptRequestSchema`).

### Design Principles

- **Functional Core, Imperative Shell:** Core logic must be pure functions where possible.
- **Fail Fast:** Validation occurs at the boundaries (UI input or API response).
- **Structured Logging:** Use `structlog`. Log events must include `correlation_id`, `model_name`, `latency_ms`, and `token_cost`.
- **Dependency Injection:** Components (LLM Client, Console) must be injected to facilitate testing.

### Error Handling Strategy

Implement a strict error taxonomy to ensure distinct handling strategies:

- `PromptOptimizerError` (Base)
    - `PipelineStageError` (Transform failures)
    - `StateTransitionError` (Invalid FSM moves)
    - `PromptTemplateError` (Jinja2 rendering issues)
    - `LLMClientError` (Network/API failures)
        - `LLMRateLimitError`
        - `InvalidResponseError` (Schema validation failure)

-----

## 4. Configuration & Secrets

- **Zero Trust:** Never commit secrets.
- Configuration via `pydantic-settings`. Priority:
  1. CLI Flags
  2. Environment Variables (`PROMPT_OPT_*`)
  3. `.env` file
  4. `config/settings.yaml`

-----

## 5. Testing Guidelines

### General Rules

- **Coverage Floor:** Strict 90%.
- **Mutation Testing:** Recommended for critical State Machine logic.

### Specific Strategies

- **LLM Interactions:** Do NOT just mock return values. Use **VCR.py** to record real API interactions and replay them in CI. This ensures parsing logic handles real-world LLM variability.
- **Snapshot Testing:** Use `pytest-snapshot` or `syrupy` to verify CLI output rendering (Rich tables/markdown) and generated prompt templates.
- **Property-based Testing:** Use `hypothesis` to fuzz the State Machine inputs.

### Useful Commands

```bash
# Run tests with VCR replay (fast)
pytest

# Run tests forcing real API calls (to update cassettes)
pytest --record-mode=rewrite

# Full audit
make audit  # runs mypy, ruff, black check, safety
```

-----

## 6. Build, Test & Development

### Setup

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pre-commit install  # Enforce hooks before commit
```

### Development Cycle

1. Define the Pydantic Model in `domain/`.
2. Write the Test (TDD).
3. Implement the logic.
4. Run `make lint` & `make test`.

-----

## 7. Commit, PR & Review Process

### Commit Format (Conventional Commits)

`type(scope): imperative description`

- `feat(fsm): add backtracking support`
- `chore(deps): update openai sdk`
- `docs(arch): update sequence diagram`

### PR Requirements

- **Type Check:** `mypy` must pass without ignores.
- **Docs:** Docstrings (Google Style) for all public methods.
- **Reasoning:** Explain *why* a prompt template was changed (if applicable).

### Definition of Done

- [ ] Logic covered by tests (Unit + VCR).
- [ ] Type hints complete (`Strict`).
- [ ] No hardcoded prompts (moved to `prompts/`).
- [ ] Telemetry added for new LLM calls.

-----

## 8. Release Management

- Semantic Versioning: **MAJOR.MINOR.PATCH**.
- **Changelog:** Automated generation via `cz` (Commitizen) preferred.
- **Artifacts:** Code is packaged as a standard Python wheel/sdist.
