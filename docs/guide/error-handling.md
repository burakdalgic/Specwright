# Error Handling

The `@handle_errors` decorator provides declarative error handling — you map exception types to strategies, and Specwright applies them automatically.

## Basic Usage

```python
from specwright import handle_errors

@handle_errors({
    ValueError: "ignore",
    KeyError: lambda e: f"missing: {e}",
    RuntimeError: "log",
    ConnectionError: {"error": "offline"},
})
def process(data: dict) -> str:
    ...
```

Instead of scattering `try/except` blocks through your code, you declare the error policy once, right where the function is defined.

## Strategies

### `"ignore"` — Suppress and Return None

```python
@handle_errors({ValueError: "ignore"})
def parse_int(s: str) -> int | None:
    """Parse a string to int, returning None on failure."""
    return int(s)

parse_int("42")     # 42
parse_int("abc")    # None (ValueError suppressed)
```

### `"log"` — Log with Traceback, Then Re-raise

```python
@handle_errors({RuntimeError: "log"})
def risky_operation() -> str:
    """Operation that might fail."""
    raise RuntimeError("something broke")

risky_operation()
# Logs: ERROR - Error in 'risky_operation': something broke
# Then re-raises the RuntimeError
```

The log includes the full traceback and uses the standard `logging` module with the function's module name as the logger.

### Callable — Custom Handler

```python
def handle_not_found(exc: BaseException) -> dict:
    return {"error": "not found", "detail": str(exc)}

@handle_errors({KeyError: handle_not_found})
def lookup(key: str) -> dict:
    """Look up a value."""
    return DATA[key]

lookup("missing")  # {"error": "not found", "detail": "'missing'"}
```

The callable receives the exception instance and its return value becomes the function's return value. You can use lambdas for simple cases:

```python
@handle_errors({
    KeyError: lambda e: None,
    ValueError: lambda e: {"error": str(e)},
})
def process(key: str) -> dict | None:
    ...
```

### Any Other Value — Return Directly

```python
@handle_errors({
    ConnectionError: {"status": "offline"},
    TimeoutError: {"status": "timeout"},
})
def fetch_data() -> dict:
    """Fetch data from a remote service."""
    ...

# If ConnectionError is raised, returns {"status": "offline"}
```

## Strategy Reference

| Strategy | Behavior |
|----------|----------|
| `"ignore"` | Suppress the exception, return `None` |
| `"log"` | Log with full traceback, then re-raise |
| callable | Call `handler(exception)`, return its result |
| any other value | Return that value directly |

## Handler Matching

Handlers are checked in order. The **first matching handler** wins:

```python
@handle_errors({
    ValueError: "ignore",           # Checked first
    Exception: lambda e: "fallback" # Checked second
})
def example() -> str:
    ...
```

**Subclasses match parent handlers.** If you raise a `FileNotFoundError`, it matches an `OSError` handler (since `FileNotFoundError` is a subclass of `OSError`):

```python
@handle_errors({OSError: "ignore"})
def read_file(path: str) -> str:
    """Read a file."""
    return open(path).read()

read_file("/nonexistent")  # None (FileNotFoundError matches OSError)
```

**Unhandled exceptions propagate normally** — if no handler matches, the exception is raised as usual.

## Combining with @spec

The two decorators compose naturally. The order matters:

### @handle_errors Outside @spec

The most common pattern. `@spec` validates types, then `@handle_errors` catches any exceptions that escape:

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
get_user("bad")    # InputValidationError (not in handlers — propagates)
```

!!! note
    `InputValidationError` is raised by `@spec` before `@handle_errors` sees it (unless you explicitly handle `InputValidationError`).

### @spec Outside @handle_errors

Use this when you want `@spec` to validate the fallback return values too:

```python
@spec
@handle_errors({ValueError: 0})
def parse_int(s: str) -> int:
    """Parse a string to int, defaulting to 0."""
    return int(s)

parse_int("abc")   # 0 (fallback passes int type check)
```

If the fallback value doesn't match the return type, `@spec` will catch it:

```python
@spec
@handle_errors({ValueError: "not a number"})  # str, not int!
def parse_int(s: str) -> int:
    """Parse a string to int."""
    return int(s)

parse_int("abc")   # OutputValidationError — "not a number" is str, not int
```

## Validation

Handler keys are validated at decoration time. Non-exception types are rejected:

```python
@handle_errors({"not_a_type": "ignore"})  # (1)!
def bad():
    ...
```

1. Raises `HandlingStrategyError`

```
HandlingStrategyError: Handler key must be an exception type, got str: 'not_a_type'
```

## Preserves Function Metadata

`@handle_errors` preserves `__name__`, `__doc__`, and `__module__` via `functools.wraps`:

```python
@handle_errors({ValueError: "ignore"})
def my_func():
    """My docstring."""
    ...

my_func.__name__  # "my_func"
my_func.__doc__   # "My docstring."
```

!!! tip "Why this matters for LLM-assisted development"
    Error handling policy is often the hardest thing to get right in generated code. With `@handle_errors`, the human declares the policy (what exceptions to catch, what to do with them), and the LLM only needs to write the core logic. The error handling is visible, declarative, and impossible to forget.

## Common Pitfalls

!!! warning "Handler order matters"
    Put specific exception types before general ones:
    ```python
    # Wrong — Exception matches everything, ValueError never reached
    @handle_errors({
        Exception: "ignore",
        ValueError: lambda e: "validation error",
    })

    # Correct — specific first, general last
    @handle_errors({
        ValueError: lambda e: "validation error",
        Exception: "ignore",
    })
    ```

!!! warning "Return types must match"
    When using `@spec` outside `@handle_errors`, the fallback value must match the declared return type.
