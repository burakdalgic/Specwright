# Quickstart

Get a spec-validated function running in under 2 minutes.

## 1. Install

```bash
pip install specwright
```

## 2. Decorate a Function

```python
from specwright import spec

@spec
def add(x: int, y: int) -> int:
    """Add two integers."""
    return x + y
```

That's the minimum: a function with **type annotations** on every parameter and the return value, plus a **docstring**.

## 3. See It Work

```python
>>> add(2, 3)
5

>>> add("two", 3)
# InputValidationError: Input validation failed for 'add':
#   - Parameter 'x': expected <class 'int'>, got str ('two')
```

The `@spec` decorator validated the input types at runtime and raised a clear, actionable error.

## 4. Inspect Metadata

Every `@spec`-decorated function carries machine-readable metadata:

```python
>>> add.__spec__.name
'add'
>>> add.__spec__.parameters
{'x': <class 'int'>, 'y': <class 'int'>}
>>> add.__spec__.return_type
<class 'int'>
>>> add.__spec__.docstring
'Add two integers.'
```

This metadata powers the `specwright docs` command and makes functions self-describing for LLMs.

## What's Next?

- [Your First Spec](your-first-spec.md) — a guided walkthrough building a real function
- [@spec Decorator Guide](../guide/spec-decorator.md) — all options and patterns
- [CLI Usage](../guide/cli-usage.md) — scaffold projects and generate code from the terminal

!!! tip "Why this matters for LLM-assisted development"
    When an LLM generates a function, the `@spec` decorator acts as a contract enforcer. The LLM reads the spec (type hints + docstring), writes the implementation, and the framework validates that the implementation actually satisfies the spec — at decoration time and every time the function runs.
