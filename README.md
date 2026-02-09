# Specwright

[![Documentation](https://img.shields.io/badge/docs-specwright.org-blue)](https://specwright.org)
[![PyPI](https://img.shields.io/pypi/v/specwright)](https://pypi.org/project/specwright/)
[![Python](https://img.shields.io/pypi/pyversions/specwright)](https://pypi.org/project/specwright/)
[![Tests](https://github.com/burakdalgic/Specwright/actions/workflows/test.yml/badge.svg)](https://github.com/burakdalgic/Specwright/actions/workflows/test.yml)
[![Lint](https://github.com/burakdalgic/Specwright/actions/workflows/lint.yml/badge.svg)](https://github.com/burakdalgic/Specwright/actions/workflows/lint.yml)
[![codecov](https://codecov.io/gh/burakdalgic/Specwright/branch/main/graph/badge.svg)](https://codecov.io/gh/burakdalgic/Specwright)
[![License](https://img.shields.io/github/license/burakdalgic/Specwright)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**A specification-first framework for LLM-assisted development.**

Humans write specifications and constraints. LLMs write implementations. Specwright enforces that implementations satisfy specifications — at decoration time and at runtime.

> **[Read the full documentation at specwright.org](https://specwright.org)**

## Quick Start

```python
from specwright import spec

@spec
def add(x: int, y: int) -> int:
    """Add two integers."""
    return x + y

add(1, 2)        # 3
add("one", 2)    # raises InputValidationError
```

Every `@spec`-decorated function must have:
- **Complete type annotations** on all parameters and the return type
- **A docstring** describing its behavior

Specwright validates these at decoration time. At runtime, it checks that actual arguments and return values match the declared types.

## Installation

```bash
pip install specwright
```

Or with [Poetry](https://python-poetry.org/):

```bash
poetry add specwright
```

> Requires Python 3.11+

## Features

### Runtime Type Validation

```python
@spec
def divide(a: float, b: float) -> float:
    """Divide a by b."""
    return a / b

divide(10, 3)        # 3.333...
divide("ten", 3)     # InputValidationError with clear message
```

### Complex Type Support

Works with generics, unions, and Pydantic models:

```python
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int

@spec
def find_adults(users: list[User]) -> list[str]:
    """Return names of users aged 18+."""
    return [u.name for u in users if u.age >= 18]
```

### Spec Metadata for Doc Generation

Every decorated function carries machine-readable metadata:

```python
@spec
def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}!"

meta = greet.__spec__
meta.name          # "greet"
meta.parameters    # {"name": <class 'str'>}
meta.return_type   # <class 'str'>
meta.docstring     # "Greet someone by name."
```

### Configurable Enforcement

Turn off specific checks when you need to:

```python
@spec(validate_output=False)
def flexible_return(x: int) -> str:
    """May not return a string during development."""
    return x  # no error raised
```

### Declarative Error Handling

The `@handle_errors` decorator maps exception types to handling strategies:

```python
from specwright import handle_errors

@handle_errors({
    ValueError: "ignore",                      # suppress, return None
    KeyError: lambda e: f"missing: {e}",       # custom handler
    RuntimeError: "log",                       # log with traceback, re-raise
    ConnectionError: {"error": "offline"},      # return a fallback value
})
def process(data: dict) -> str:
    ...
```

**Strategies:**

| Strategy | Behaviour |
|---|---|
| `"ignore"` | Suppress the exception, return `None` |
| `"log"` | Log with full traceback, then re-raise |
| callable | Call `handler(exception)`, return its result |
| any other value | Return that value directly |

### Combining `@spec` and `@handle_errors`

The two decorators compose naturally. Place `@handle_errors` on the outside to catch exceptions that escape the spec-validated function:

```python
from specwright import spec, handle_errors

@handle_errors({
    ValueError: lambda e: {"error": str(e)},
    KeyError: "ignore",
})
@spec
def get_user(user_id: int) -> dict:
    """Look up a user by ID."""
    if user_id < 0:
        raise ValueError("user_id must be non-negative")
    return USERS[user_id]

get_user(1)        # {"name": "Alice", ...}
get_user(-1)       # {"error": "user_id must be non-negative"}
get_user(999)      # None (KeyError ignored)
get_user("bad")    # raises InputValidationError (not in handlers)
```

Or place `@spec` on the outside to validate the fallback return values too:

```python
@spec
@handle_errors({ValueError: 0})
def parse_int(s: str) -> int:
    """Parse a string to int, defaulting to 0."""
    return int(s)

parse_int("abc")   # 0 (fallback passes int type check)
```

### State Machine

The `StateMachine` base class enforces valid state transitions at runtime:

```python
from specwright import StateMachine, transition

class OrderProcessor(StateMachine):
    states = ["pending", "paid", "shipped", "delivered", "cancelled"]
    initial_state = "pending"

    @transition(from_state="pending", to_state="paid")
    def pay(self, amount: float) -> str:
        return f"Paid ${amount:.2f}"

    @transition(from_state="paid", to_state="shipped")
    def ship(self, tracking: str) -> str:
        return f"Shipped ({tracking})"

    @transition(from_state=["pending", "paid"], to_state="cancelled")
    def cancel(self, reason: str) -> str:
        return f"Cancelled: {reason}"

order = OrderProcessor()
order.pay(99.99)         # state -> "paid"
order.ship("TRACK-123")  # state -> "shipped"
order.cancel("reason")   # raises InvalidTransitionError (can't cancel after shipping)
```

**State history** tracks every state visited:

```python
class Tracked(StateMachine):
    states = ["a", "b", "c"]
    initial_state = "a"
    track_history = True  # opt-in

    @transition(from_state="a", to_state="b")
    def go_b(self): ...

    @transition(from_state="b", to_state="c")
    def go_c(self): ...

sm = Tracked()
sm.go_b()
sm.go_c()
sm.state_history  # ["a", "b", "c"]
```

**Lifecycle hooks** run automatically on state changes:

```python
class WithHooks(StateMachine):
    states = ["active", "suspended"]
    initial_state = "active"

    @transition(from_state="active", to_state="suspended")
    def suspend(self): ...

    def on_exit_active(self):
        print("Leaving active state")

    def on_enter_suspended(self):
        print("Entering suspended state")
```

**Combines with `@spec`** for full validation:

```python
class Machine(StateMachine):
    states = ["idle", "done"]
    initial_state = "idle"

    @transition(from_state="idle", to_state="done")
    @spec
    def finish(self, result: str) -> str:
        """Complete the task."""
        return f"done: {result}"
```

State machines help LLMs by making valid transitions explicit and machine-readable. An LLM can see exactly which states exist, which transitions are allowed, and what the current state is — eliminating an entire class of bugs where code attempts an impossible operation.

### Test Requirements (`@requires_tests`)

Declare what tests a function needs — the pytest plugin enforces it:

```python
from specwright import requires_tests, spec

@requires_tests(
    happy_path=True,
    edge_cases=["empty_input", "max_boundaries"],
    error_cases=["invalid_email", "negative_age"],
)
@spec
def create_user(email: str, age: int) -> dict:
    """Create a new user account."""
    ...
```

The decorator stores a `TestRequirements` object on the function:

```python
reqs = create_user.__test_requirements__
reqs.expected_test_names
# ['test_create_user_happy_path',
#  'test_create_user_empty_input',
#  'test_create_user_max_boundaries',
#  'test_create_user_invalid_email',
#  'test_create_user_negative_age']
```

**Naming convention:** `test_{function_name}_{case_name}`

**Pytest plugin** verifies at collection time that all required test functions exist:

```toml
# pyproject.toml
[tool.pytest.ini_options]
specwright_test_enforcement = "strict"   # "strict" | "warn" | "off"
```

| Mode | Behaviour |
|---|---|
| `strict` | Fail the session if any required tests are missing |
| `warn` | Emit warnings but let the session continue |
| `off` | Skip the check entirely |

This enforces a **test-driven LLM workflow**: humans declare *what* must be tested, LLMs write the implementations *and* the tests, and the framework ensures nothing is forgotten.

### Clear Error Messages

```
InputValidationError: Input validation failed for 'add':
  - Parameter 'x': expected <class 'int'>, got str ('one')
```

```
InvalidTransitionError: Cannot transition from 'shipped' to 'cancelled'
via 'cancel'. Valid source state(s): paid, pending
```

## Why Specwright?

Modern development increasingly involves LLMs generating code. This creates a new problem: **how do you trust LLM-generated implementations?**

The traditional answer — code review — doesn't scale. Specwright takes a different approach:

1. **Humans write specs** — type signatures, docstrings, constraints, and state machines that define *what* a function should do
2. **LLMs write implementations** — the code that fulfills the spec
3. **Specwright enforces correctness** — runtime validation ensures implementations actually satisfy their specifications

This creates a workflow where humans stay in control of *what* the software does, while delegating *how* it does it. The framework is the bridge that ensures the two stay in sync.

## CLI

Specwright includes a CLI for scaffolding projects, generating boilerplate, validating coverage, and producing docs.

### `specwright init`

Scaffold a new project:

```bash
specwright init my_project
```

Creates `my_project/` with `pyproject.toml`, a sample `@spec` function, `tests/`, and a `.specwright.toml` config file.

### `specwright new function`

Generate a `@spec`-decorated function and its test file:

```bash
specwright new function calculate_score \
    --params "base: int, multiplier: float" \
    --returns float
```

Omit `--params` / `--returns` to be prompted interactively.

### `specwright new statemachine`

Generate a `StateMachine` subclass with sequential transitions:

```bash
specwright new statemachine order_processor \
    --states pending,paid,shipped,delivered
```

### `specwright validate`

Check that all `@spec`-decorated functions have tests and state machines are well-formed:

```bash
specwright validate --path .
```

Exits with code 1 if issues are found.

### `specwright docs`

Generate API documentation from `@spec` metadata:

```bash
specwright docs --path .                # to stdout
specwright docs --path . --output API.md   # to file
specwright docs --path . --diagram         # include DOT state diagrams
```

### Workflow

```bash
specwright init my_project
cd my_project
specwright new function my_func
specwright new statemachine my_workflow
# ... fill in implementations ...
specwright validate
specwright docs --output API.md
```

## Project Structure

```
specwright/
  __init__.py        # Public API
  cli.py             # CLI entry point (init, new, validate, docs)
  decorators.py      # @spec and @handle_errors decorators
  state_machine.py   # StateMachine base class and @transition
  testing.py         # @requires_tests decorator and TestRequirements
  pytest_plugin.py   # Pytest plugin for test enforcement
  validation.py      # Runtime type checking engine
  exceptions.py      # Clear, typed error hierarchy
  templates/         # Jinja2 templates for code generation
tests/               # Comprehensive test suite
examples/            # Runnable usage examples
```

## Development

```bash
# Install dependencies
poetry install

# Run tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=specwright --cov-report=term-missing

# Lint
poetry run ruff check .

# Format
poetry run black .

# Type check
poetry run mypy specwright
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, code style, and PR guidelines.

## License

MIT — see [LICENSE](LICENSE) for details.

## Links

- **Documentation:** [specwright.org](https://specwright.org)
- **Source:** [GitHub](https://github.com/burakdalgic/Specwright)
- **Issues:** [Bug Tracker](https://github.com/burakdalgic/Specwright/issues)
- **Changelog:** [CHANGELOG.md](CHANGELOG.md)
