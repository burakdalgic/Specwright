# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-02-07

### Added

- **`@spec` decorator** — Enforces type annotations, docstrings, and runtime type validation on functions using Pydantic's `TypeAdapter` with strict mode.
- **`@handle_errors` decorator** — Declarative error handling with four strategies: `"ignore"`, `"log"`, callable handlers, and direct return values.
- **`StateMachine` base class** — Finite state machines with validated transitions, lifecycle hooks (`on_enter_*`/`on_exit_*`), state history tracking, and class-level validation at definition time.
- **`@transition` decorator** — Marks methods as state transitions with source/target state enforcement.
- **`@requires_tests` decorator** — Declares required test scenarios (happy path, edge cases, error cases) with automatic naming convention.
- **Pytest plugin** — Validates at collection time that all `@requires_tests` functions have matching test functions. Supports `strict`, `warn`, and `off` enforcement modes via `pyproject.toml`.
- **CLI tool** with five commands:
  - `specwright init` — Scaffold a new project with pyproject.toml, sample code, tests, and config.
  - `specwright new function` — Generate a `@spec`-decorated function stub with test file.
  - `specwright new statemachine` — Generate a `StateMachine` subclass with sequential transitions and test file.
  - `specwright validate` — Scan a project for spec coverage, test completeness, and state machine reachability.
  - `specwright docs` — Generate Markdown API documentation from `@spec` metadata with optional Graphviz state diagrams.
- **Exception hierarchy** rooted at `SpecwrightError` with specific subtypes: `InputValidationError`, `OutputValidationError`, `MissingDocstringError`, `MissingTypeHintError`, `HandlingStrategyError`, `InvalidTransitionError`, `InvalidStateError`, `MissingTestsError`, `InvalidTestNameError`.
- **Jinja2 templates** for code generation (`function.py.j2`, `statemachine.py.j2`, etc.).
- **MkDocs documentation site** with Material theme, Mermaid state diagrams, and GitHub Pages deployment.
- **187 tests** covering all modules.

[0.1.0]: https://github.com/specwright/specwright/releases/tag/v0.1.0
