# Contributing

Specwright welcomes contributions. Here's how to get started.

## Development Setup

```bash
git clone https://github.com/burakdalgic/Specwright.git
cd specwright
poetry install
```

## Running Tests

```bash
# All tests
poetry run pytest

# With verbose output
poetry run pytest -v

# With coverage
poetry run pytest --cov=specwright --cov-report=term-missing

# Specific test file
poetry run pytest tests/test_decorators.py
```

## Code Quality

```bash
# Lint
poetry run ruff check .

# Format
poetry run black .

# Type check
poetry run mypy specwright
```

## Project Structure

```
specwright/
  __init__.py          # Public API and exports
  cli.py               # CLI commands (Click)
  decorators.py        # @spec and @handle_errors
  state_machine.py     # StateMachine and @transition
  testing.py           # @requires_tests and TestRequirements
  pytest_plugin.py     # Pytest plugin for test enforcement
  validation.py        # Runtime type checking (Pydantic)
  exceptions.py        # Exception hierarchy
  templates/           # Jinja2 templates for code generation
tests/
  test_cli.py          # CLI tests
  test_decorators.py   # @spec and @handle_errors tests
  test_state_machine.py # StateMachine tests
  test_requires_tests.py # @requires_tests tests
  test_validation.py   # Validation engine tests
  test_exceptions.py   # Exception hierarchy tests
  test_handle_errors.py # @handle_errors tests
examples/              # Runnable usage examples
docs/                  # MkDocs documentation
```

## Making Changes

1. Create a branch from `main`
2. Make your changes
3. Write or update tests
4. Run the full test suite: `poetry run pytest`
5. Run linting: `poetry run ruff check .`
6. Submit a pull request

## Documentation

Documentation is built with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/). To preview locally:

```bash
poetry install --with docs
poetry run mkdocs serve
```

Then open `http://localhost:8000`.

## Guidelines

- **Tests are required.** Every new feature or bugfix should include tests. The test suite currently has 187 tests — keep it growing.
- **Maintain backwards compatibility.** Public API changes require discussion.
- **Follow existing patterns.** Look at how existing decorators and modules are structured.
- **Keep it simple.** Specwright values clarity over cleverness.

## Reporting Issues

File issues at [github.com/burakdalgic/Specwright/issues](https://github.com/burakdalgic/Specwright/issues).

Include:

- Python version (`python --version`)
- Specwright version (`specwright --version`)
- Minimal reproduction case
- Expected vs actual behavior
