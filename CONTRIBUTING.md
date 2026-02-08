# Contributing to Specwright

Thanks for your interest in contributing! This guide will help you get started.

## Development Setup

```bash
git clone https://github.com/specwright/specwright.git
cd specwright
poetry install
```

This installs all runtime and development dependencies.

## Running Tests

```bash
# All tests
poetry run pytest

# Verbose output
poetry run pytest -v

# With coverage report
poetry run pytest --cov=specwright --cov-report=term-missing

# Single test file
poetry run pytest tests/test_decorators.py -v
```

The test suite must pass before submitting a PR. Currently at 187 tests.

## Code Quality

All three checks must pass:

```bash
# Format
poetry run black .

# Lint
poetry run ruff check .

# Type check
poetry run mypy specwright
```

CI runs all three on every push and PR.

## Code Style

- **Formatter**: Black (line length 88)
- **Linter**: Ruff (Python 3.11 target)
- **Type checker**: mypy (strict mode)
- Follow existing patterns in the codebase
- Use `from __future__ import annotations` in all modules
- Use frozen dataclasses for metadata objects
- Use `functools.wraps` on all wrapper functions

## Making Changes

1. **Fork and clone** the repository
2. **Create a branch** from `main`: `git checkout -b my-feature`
3. **Make your changes** with tests
4. **Run the checks**: `poetry run pytest && poetry run black . && poetry run ruff check . && poetry run mypy specwright`
5. **Commit** with a clear message
6. **Push** and open a pull request

## Pull Request Guidelines

- Keep PRs focused on a single change
- Include tests for new features and bug fixes
- Update documentation if the public API changes
- Add a CHANGELOG.md entry under `[Unreleased]`
- Ensure CI passes (tests, lint, type check)

## Adding a New Decorator

If you're adding a new decorator to Specwright:

1. Create the module in `specwright/` (or add to an existing one)
2. Use a frozen dataclass for any metadata
3. Store metadata via a dunder attribute (e.g., `__my_meta__`)
4. Export from `specwright/__init__.py` and add to `__all__`
5. Write tests in `tests/`
6. Add an example in `examples/`
7. Document in `docs/guide/` and `docs/api-reference/`

## Adding Examples

Examples live in `examples/` and should be:

- Self-contained (runnable with `python examples/my_example.py`)
- Well-commented explaining what's happening
- Using `if __name__ == "__main__":` for the demo code

## Documentation

Docs are built with MkDocs Material. To preview locally:

```bash
poetry install --with docs
poetry run mkdocs serve
```

Then open http://localhost:8000.

## Reporting Bugs

File issues at [github.com/specwright/specwright/issues](https://github.com/specwright/specwright/issues) with:

- Python version and OS
- Specwright version (`specwright --version`)
- Minimal reproduction case
- Expected vs actual behavior

## Questions?

Open a [discussion](https://github.com/specwright/specwright/discussions) for questions that aren't bug reports or feature requests.
