# Test Requirements

The `@requires_tests` decorator declares what tests a function needs. The companion pytest plugin verifies those tests exist at collection time — before any test runs.

## Basic Usage

```python
from specwright import requires_tests

@requires_tests(
    happy_path=True,
    edge_cases=["empty_input", "max_boundaries"],
    error_cases=["invalid_email", "negative_age"],
)
def create_user(email: str, age: int) -> dict:
    """Create a new user account."""
    ...
```

This tells Specwright: "This function requires five test functions to exist."

## Expected Test Names

The naming convention is:

```
test_{function_name}_{case_name}
```

Check what's expected:

```python
reqs = create_user.__test_requirements__
reqs.expected_test_names
# ['test_create_user_happy_path',
#  'test_create_user_empty_input',
#  'test_create_user_max_boundaries',
#  'test_create_user_invalid_email',
#  'test_create_user_negative_age']
```

## Writing the Tests

Create test functions that match the expected names:

```python
# tests/test_create_user.py

from myapp import create_user

def test_create_user_happy_path():
    result = create_user("alice@example.com", 30)
    assert result["email"] == "alice@example.com"
    assert result["age"] == 30

def test_create_user_empty_input():
    # Test with empty string email
    ...

def test_create_user_max_boundaries():
    # Test with extreme age values
    ...

def test_create_user_invalid_email():
    # Test with malformed email
    ...

def test_create_user_negative_age():
    # Test with negative age
    ...
```

## Decorator Options

```python
@requires_tests(
    happy_path=True,                           # Require a _happy_path test (default: True)
    edge_cases=["empty", "boundary"],          # Edge case scenario names
    error_cases=["invalid_input", "overflow"], # Error case scenario names
)
```

### Happy Path Only

```python
@requires_tests()
def simple_function(x: int) -> int:
    ...
# Expects: test_simple_function_happy_path
```

### No Happy Path

```python
@requires_tests(happy_path=False, edge_cases=["empty", "full"])
def edge_only(items: list) -> list:
    ...
# Expects: test_edge_only_empty, test_edge_only_full
```

## Pytest Plugin

Specwright includes a pytest plugin that automatically checks test requirements at collection time. It's registered via the `pytest11` entry point and activates when Specwright is installed.

### Configuration

Set the enforcement level in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
specwright_test_enforcement = "strict"   # "strict" | "warn" | "off"
```

| Mode | Behavior |
|------|----------|
| `strict` | **Fail the session** if any required tests are missing |
| `warn` | Emit warnings but let the session continue |
| `off` | Skip the check entirely |

### Strict Mode (Default)

If any required test is missing, the session fails immediately:

```
ERRORS
MissingTestsError: Missing required tests:
  create_user:
    - test_create_user_empty_input
    - test_create_user_negative_age
```

### Warn Mode

Missing tests produce warnings but don't block the session:

```
warnings.warn: Missing required tests:
  create_user:
    - test_create_user_empty_input
```

### Off Mode

No checking at all. Useful when running a subset of tests during development:

```toml
specwright_test_enforcement = "off"
```

## Combining with @spec

`@requires_tests` composes naturally with `@spec`:

```python
from specwright import requires_tests, spec

@requires_tests(
    happy_path=True,
    edge_cases=["empty_list", "single_item"],
    error_cases=["non_numeric"],
)
@spec
def average(values: list[float]) -> float:
    """Calculate the arithmetic mean of a list of numbers."""
    return sum(values) / len(values)
```

Both decorators store their metadata independently:

```python
average.__spec__                # SpecMetadata(...)
average.__test_requirements__   # TestRequirements(...)
```

## TestRequirements Dataclass

The metadata stored on decorated functions:

```python
@dataclass(frozen=True)
class TestRequirements:
    function_name: str          # Simple function name
    qualname: str               # Qualified name (includes class if nested)
    module: str | None          # Module where the function is defined
    happy_path: bool            # Whether a happy-path test is required
    edge_cases: tuple[str, ...] # Edge case scenario names
    error_cases: tuple[str, ...] # Error case scenario names
```

The `expected_test_names` property computes the full list of required test function names.

## Global Registry

All `@requires_tests`-decorated functions are tracked in a global registry. The pytest plugin reads this registry to know what to check:

```python
from specwright.testing import get_registry

registry = get_registry()  # Returns a copy of all registered TestRequirements
```

!!! tip "Why this matters for LLM-assisted development"
    This enforces a **test-driven LLM workflow**: the human declares *what* must be tested (happy path, edge cases, error cases), the LLM writes both the implementation and the tests, and the framework verifies nothing is forgotten. You can't ship code with missing tests — the pytest plugin catches it before any test runs.

## Common Pitfalls

!!! warning "Test names must match exactly"
    The plugin checks for **exact function name matches**. A test named `test_create_user_happy` won't satisfy a requirement for `test_create_user_happy_path`.

!!! warning "Test enforcement affects all tests in the session"
    If any `@requires_tests`-decorated function in your codebase has missing tests, `strict` mode will fail the entire session. Use `"off"` mode during early development.

!!! warning "Registry is global and cumulative"
    Every import of a module containing `@requires_tests` adds to the global registry. In tests, you may need to clear the registry between test cases if you're dynamically creating decorated functions.
